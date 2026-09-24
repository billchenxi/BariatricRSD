"""
brsd_lib.smoothing
==================

Adam-inspired inference-time smoothing for per-clip RSD trajectories.

Motivation
----------
A trained RSD model produces one remaining-time estimate per clip. Raw
per-clip predictions are noisy: a stapler going out of frame, a brief
out-of-body segment, or a phase-transition frame can spike the prediction
up or down by several minutes. Existing inference-time fixes (isotonic
regression, moving average) are useful but blunt: isotonic enforces strict
monotonicity without regard to local noise level, and a fixed-window moving
average treats all past predictions equally.

This module implements an Adam-optimizer-inspired smoother:

  m_t = β1 * m_{t-1} + (1 - β1) * ŷ_t               # first-moment EMA
  v_t = β2 * v_{t-1} + (1 - β2) * (ŷ_t - m̂_t)²       # second-moment (variance)
  α_t = τ² / (τ² + v̂_t)                               # adaptive trust factor
  ỹ_t = α_t * ŷ_t + (1 - α_t) * m̂_t                   # variance-adaptive blend
  y*_t = min(ỹ_t, y*_{t-1}) if monotone else ỹ_t     # clock-never-goes-back

Intuition:
- When raw predictions are locally consistent (low v̂_t), α_t → 1 and we
  trust the new prediction — responsive to real workflow changes.
- When raw predictions are locally noisy (high v̂_t), α_t → 0 and we lean
  on the moving average — ignore outliers.
- Bias correction (Adam's m̂_t, v̂_t) handles the cold-start window so
  early-clip predictions don't collapse to the first observation.
- The monotonicity cap enforces the physical constraint that remaining
  surgery time cannot increase.

This is a drop-in alternative/complement to the per-video
``IsotonicRegression(increasing=False)`` path in ``brsd_lib.ensemble``.
Written fresh for the NeurIPS 2026 submission. No GPU required.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Core smoother
# ---------------------------------------------------------------------------

@dataclass
class AdamSmootherConfig:
    beta1: float = 0.9
    beta2: float = 0.999
    tau: float = 0.02
    eps: float = 1e-8
    monotone: bool = True
    bias_correct: bool = True


def adam_smooth(
    preds: Sequence[float],
    cfg: AdamSmootherConfig = AdamSmootherConfig(),
) -> np.ndarray:
    """Smooth a single per-video trajectory of raw RSD predictions.

    Arguments:
        preds: List/1D-array of raw predictions, ordered by time, values in
            roughly [0, 1] (normalized remaining fraction).
        cfg: AdamSmootherConfig — momentum / variance / trust / monotonicity.

    Returns:
        np.ndarray of smoothed predictions, same length as ``preds``.
    """
    preds = np.asarray(preds, dtype=np.float64)
    N = preds.shape[0]
    out = np.empty(N, dtype=np.float64)
    m = 0.0
    v = 0.0
    last_smoothed = np.inf
    for t in range(N):
        p = float(preds[t])
        # First moment (EMA of predictions)
        m = cfg.beta1 * m + (1.0 - cfg.beta1) * p
        m_hat = m / (1.0 - cfg.beta1 ** (t + 1)) if cfg.bias_correct else m
        # Second moment (EMA of squared residual from m_hat)
        resid = p - m_hat
        v = cfg.beta2 * v + (1.0 - cfg.beta2) * (resid * resid)
        v_hat = v / (1.0 - cfg.beta2 ** (t + 1)) if cfg.bias_correct else v
        # Adaptive trust factor: close to 1 when local variance is small
        # (raw trusted), close to 0 when variance is large (lean on EMA).
        alpha = (cfg.tau * cfg.tau) / (cfg.tau * cfg.tau + v_hat + cfg.eps)
        blended = alpha * p + (1.0 - alpha) * m_hat
        if cfg.monotone and blended > last_smoothed:
            blended = last_smoothed
        out[t] = blended
        last_smoothed = blended
    return out


# ---------------------------------------------------------------------------
# Per-video application + evaluation
# ---------------------------------------------------------------------------

def apply_per_video(
    df,
    pred_col: str = "prediction",
    video_col: str = "video_id",
    order_col: Optional[str] = None,
    cfg: AdamSmootherConfig = AdamSmootherConfig(),
) -> np.ndarray:
    """Apply adam_smooth independently per video, returning a column aligned
    with the input DataFrame order.

    If ``order_col`` is given it is used to sort *within* each video (e.g.
    frame_idx). Otherwise, rows are assumed to already be in temporal order
    within each video (as produced by ``brsd_lib.compute_residuals``).
    """
    import pandas as pd
    out = np.empty(len(df), dtype=np.float64)
    for vid, grp in df.groupby(video_col, sort=False):
        if order_col is not None:
            grp = grp.sort_values(order_col)
        preds = grp[pred_col].to_numpy()
        smoothed = adam_smooth(preds, cfg=cfg)
        out[grp.index.to_numpy()] = smoothed
    return out


def per_video_mae_minutes(
    df,
    pred_col: str,
    target_col: str = "target",
    total_minutes_col: Optional[str] = None,
    video_col: str = "video_id",
    default_total_min: float = 90.0,
) -> Dict[str, float]:
    """Compute per-video mean absolute error in *minutes*.

    If ``total_minutes_col`` is present in the DataFrame it is used to
    denormalize fractional RSD back to minutes; otherwise a dataset-level
    default is used (not ideal, but enough for ranking smoothing configs
    against each other on the same dataset).
    """
    import pandas as pd
    per_video: Dict[str, float] = {}
    for vid, grp in df.groupby(video_col, sort=False):
        if total_minutes_col and total_minutes_col in grp.columns:
            total = float(grp[total_minutes_col].iloc[0])
        else:
            total = default_total_min
        err_min = np.abs(grp[pred_col].to_numpy() - grp[target_col].to_numpy()) * total
        per_video[str(vid)] = float(err_min.mean())
    return per_video


# ---------------------------------------------------------------------------
# Sweep helper
# ---------------------------------------------------------------------------

def sweep_configs(
    df,
    pred_col: str = "prediction",
    target_col: str = "target",
    total_minutes_col: Optional[str] = None,
    video_col: str = "video_id",
    grid: Optional[List[AdamSmootherConfig]] = None,
) -> List[Tuple[AdamSmootherConfig, float, float]]:
    """Evaluate a grid of smoother configs; return (cfg, mean, median) tuples
    ordered by mean per-video MAE in minutes."""
    import pandas as pd
    if grid is None:
        grid = []
        for beta1 in (0.80, 0.90, 0.95, 0.99):
            for beta2 in (0.99, 0.999):
                for tau in (0.005, 0.02, 0.05, 0.1):
                    for mono in (True, False):
                        grid.append(AdamSmootherConfig(
                            beta1=beta1, beta2=beta2, tau=tau, monotone=mono,
                        ))
    # Baseline (no smoothing)
    results: List[Tuple[AdamSmootherConfig, float, float]] = []
    baseline = per_video_mae_minutes(df, pred_col, target_col, total_minutes_col, video_col)
    bmean = float(np.mean(list(baseline.values())))
    bmed = float(np.median(list(baseline.values())))
    results.append((AdamSmootherConfig(beta1=-1, beta2=-1, tau=-1, monotone=False), bmean, bmed))
    # Smoothed
    for cfg in grid:
        smoothed = apply_per_video(df, pred_col=pred_col, video_col=video_col, cfg=cfg)
        df = df.assign(_smooth=smoothed)
        per_vid = per_video_mae_minutes(
            df, "_smooth", target_col, total_minutes_col, video_col
        )
        mean = float(np.mean(list(per_vid.values())))
        med = float(np.median(list(per_vid.values())))
        results.append((cfg, mean, med))
    results.sort(key=lambda r: r[1])
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.smoothing",
        description="Apply Adam-inspired smoothing to a per-clip predictions "
                    "CSV (from brsd_lib.compute_residuals) and report MAE.",
    )
    ap.add_argument("--input_csv", required=True,
                    help="CSV with at least columns: video_id, prediction, target.")
    ap.add_argument("--output_csv", default=None,
                    help="If set, write smoothed predictions here.")
    ap.add_argument("--output_json", default=None,
                    help="If set, write per-video MAE and best-config sweep here.")
    ap.add_argument("--total_minutes_col", default=None,
                    help="Optional column giving per-video total duration in minutes.")
    ap.add_argument("--default_total_min", type=float, default=90.0,
                    help="Fallback total duration used to denormalize fractional RSD "
                         "(MB140 median ≈ 83 min; Cholec80 ≈ 39 min).")
    ap.add_argument("--sweep", action="store_true", default=False,
                    help="Run a configuration sweep and print top-10 configs.")
    ap.add_argument("--beta1", type=float, default=0.9)
    ap.add_argument("--beta2", type=float, default=0.999)
    ap.add_argument("--tau", type=float, default=0.02)
    ap.add_argument("--no_monotone", action="store_true", default=False)
    args = ap.parse_args()

    import pandas as pd
    df = pd.read_csv(args.input_csv)
    print(f"loaded {len(df):,} rows, {df['video_id'].nunique()} videos")

    if args.sweep:
        results = sweep_configs(
            df,
            pred_col="prediction",
            target_col="target",
            total_minutes_col=args.total_minutes_col,
            video_col="video_id",
        )
        print("\n=== Top-10 configs by mean per-video MAE (minutes) ===")
        for cfg, mean, med in results[:10]:
            if cfg.beta1 < 0:
                label = "<<no smoothing (baseline)>>"
            else:
                label = (f"beta1={cfg.beta1} beta2={cfg.beta2} tau={cfg.tau} "
                         f"mono={cfg.monotone}")
            print(f"  mean={mean:7.3f}  median={med:7.3f}  {label}")
        best_cfg, best_mean, best_med = results[0]
        print(f"\nBest: mean={best_mean:.3f} min, median={best_med:.3f} min")
        if args.output_json:
            out = {
                "results": [
                    {
                        "beta1": c.beta1, "beta2": c.beta2,
                        "tau": c.tau, "monotone": c.monotone,
                        "mean_mae_min": m, "median_mae_min": md,
                    }
                    for (c, m, md) in results
                ],
                "best": {
                    "beta1": best_cfg.beta1, "beta2": best_cfg.beta2,
                    "tau": best_cfg.tau, "monotone": best_cfg.monotone,
                    "mean_mae_min": best_mean, "median_mae_min": best_med,
                },
            }
            Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output_json, "w") as f:
                json.dump(out, f, indent=2)
            print(f"wrote sweep results to {args.output_json}")
    else:
        cfg = AdamSmootherConfig(
            beta1=args.beta1, beta2=args.beta2, tau=args.tau,
            monotone=not args.no_monotone,
        )
        smoothed = apply_per_video(df, pred_col="prediction", video_col="video_id", cfg=cfg)
        df = df.assign(prediction_smoothed=smoothed)
        per_vid_raw = per_video_mae_minutes(
            df, "prediction", "target", args.total_minutes_col, "video_id",
            default_total_min=args.default_total_min,
        )
        per_vid_s = per_video_mae_minutes(
            df, "prediction_smoothed", "target", args.total_minutes_col, "video_id",
            default_total_min=args.default_total_min,
        )
        raw_mean = float(np.mean(list(per_vid_raw.values())))
        s_mean = float(np.mean(list(per_vid_s.values())))
        print(f"\nraw       mean per-video MAE: {raw_mean:.3f} min")
        print(f"smoothed  mean per-video MAE: {s_mean:.3f} min   (Δ = {s_mean - raw_mean:+.3f})")
        if args.output_csv:
            df.to_csv(args.output_csv, index=False)
            print(f"wrote {args.output_csv}")


if __name__ == "__main__":
    _cli()

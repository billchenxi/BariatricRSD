"""
brsd_lib.ensemble
=================

Test-time ensemble + TTA + isotonic post-processing for RSD prediction.

Given N trained checkpoints (seeds of the same configuration), produces
predictions on a held-out split by:

  1. Running each checkpoint forward on the test clips.
  2. Optionally running each checkpoint a second time on horizontally-flipped
     frames (TTA).
  3. Averaging the predicted normalized-RSD across all (checkpoint, view) pairs.
  4. Optionally post-processing each video's per-frame predictions through
     sklearn IsotonicRegression(increasing=False) to enforce monotonic
     non-increase (surgery duration can only decrease with time).

Then computes per-video MAE in minutes (same convention as brsd_lib.evaluate)
and returns a structured summary.

Written fresh for the NeurIPS 2026 submission. No code borrowed from any
prior project.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch


# ---------------------------------------------------------------------------
# Project import helper
# ---------------------------------------------------------------------------

def _import_project(project_src: str):
    if project_src not in sys.path:
        sys.path.insert(0, project_src)
    from models.bariatric_rsd import BariatricRSD           # type: ignore
    from data.dataset import BariatricFrameDataset          # type: ignore
    from torch.utils.data import DataLoader                  # type: ignore
    return BariatricRSD, BariatricFrameDataset, DataLoader


def _load_checkpoint(model: torch.nn.Module, ckpt_path: str, device: torch.device) -> None:
    state = torch.load(ckpt_path, map_location=device, weights_only=False)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    model.load_state_dict(state)
    model.eval()


# ---------------------------------------------------------------------------
# Inference over a split, optionally with horizontal-flip TTA
# ---------------------------------------------------------------------------

@torch.no_grad()
def _infer_split(
    model: torch.nn.Module,
    loader,
    device: torch.device,
    use_hflip: bool = False,
) -> Dict[Tuple[str, int], float]:
    """
    Run inference on every clip in `loader`, return a dict keyed by
    (video_id, timestamp_sec_int) → predicted normalized RSD (float).

    If `use_hflip` is True, horizontally flips each clip's frames before forward.
    """
    preds: Dict[Tuple[str, int], float] = {}
    for batch in loader:
        frames = batch["frames"].to(device, non_blocking=True)
        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)
        timestamps = batch["timestamp_sec"].float().cpu().numpy()
        vids = batch["video_id"]

        if use_hflip:
            # Flip spatial W dimension of every frame in the clip.
            # BariatricFrameDataset returns [B, T, C, H, W]
            frames = torch.flip(frames, dims=[-1])

        out = model(frames, cluster)
        rsd_pred = out["rsd"].detach().float().cpu().numpy()
        for v, ts, p in zip(vids, timestamps, rsd_pred):
            key = (v, int(round(float(ts))))
            # If duplicate key (multiple sequences landing on same mid-frame), keep the last — they're equivalent.
            preds[key] = float(p)
    return preds


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _group_by_video(
    preds: Dict[Tuple[str, int], float],
) -> Dict[str, List[Tuple[int, float]]]:
    """Group {(vid, ts) -> pred} into {vid -> [(ts, pred), ...]} sorted by ts."""
    by_vid: Dict[str, List[Tuple[int, float]]] = {}
    for (vid, ts), p in preds.items():
        by_vid.setdefault(vid, []).append((ts, p))
    for vid in by_vid:
        by_vid[vid].sort(key=lambda x: x[0])
    return by_vid


def _apply_isotonic(
    timestamps: Sequence[int],
    values: Sequence[float],
) -> np.ndarray:
    """
    Enforce non-increasing RSD trajectory over time by isotonic regression.
    Returns an array aligned with `values` (same length, same order as input).
    """
    try:
        from sklearn.isotonic import IsotonicRegression
    except ImportError:
        # Degrade gracefully — return input unchanged
        return np.asarray(values, dtype=np.float64)
    ir = IsotonicRegression(increasing=False, out_of_bounds="clip")
    x = np.asarray(timestamps, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if len(y) < 2:
        return y
    smoothed = ir.fit_transform(x, y)
    # Clamp to [0, 1]
    return np.clip(smoothed, 0.0, 1.0)


def _per_video_mae_min(
    preds_by_vid: Dict[str, List[Tuple[int, float]]],
    truths_by_vid: Dict[str, List[Tuple[int, float]]],
    durations_sec: Dict[str, float],
    use_isotonic: bool,
) -> Dict[str, float]:
    """
    Compute per-video MAE in minutes. If use_isotonic, smooth predictions first.
    """
    out: Dict[str, float] = {}
    for vid, pred_list in preds_by_vid.items():
        if vid not in truths_by_vid:
            continue
        true_list = truths_by_vid[vid]
        # Align by timestamp
        true_by_ts = dict(true_list)
        ts_sorted, pred_sorted = zip(*pred_list)
        ts_sorted = list(ts_sorted)
        pred_arr = np.asarray(pred_sorted, dtype=np.float64)
        truth_arr = np.asarray([true_by_ts.get(ts, 0.0) for ts in ts_sorted], dtype=np.float64)

        if use_isotonic:
            pred_arr = _apply_isotonic(ts_sorted, pred_arr)

        total = durations_sec.get(vid, 0.0)
        if total <= 0:
            continue
        err_sec = np.abs(pred_arr - truth_arr) * total
        out[vid] = float(np.mean(err_sec) / 60.0)
    return out


def _summarize(per_vid: Dict[str, float]) -> Dict[str, float]:
    vals = list(per_vid.values())
    if not vals:
        return {"n_videos": 0, "mean": 0.0, "median": 0.0, "std": 0.0,
                "min": 0.0, "max": 0.0}
    return {
        "n_videos": len(vals),
        "mean": float(mean(vals)),
        "median": float(median(vals)),
        "std": float(stdev(vals)) if len(vals) >= 2 else 0.0,
        "min": float(min(vals)),
        "max": float(max(vals)),
    }


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def run_ensemble_eval(
    checkpoints: List[str],
    label_json: str,
    data_root: str,
    split: str = "test",
    sequence_len: int = 8,
    frame_stride: int = 5,
    img_size: int = 224,
    batch_size: int = 64,
    num_workers: int = 16,
    num_phases: int = 7,
    project_src: str = "/lambda/nfs/bariatric-rsd/src",
    use_tta_hflip: bool = False,
    use_isotonic: bool = False,
    device: str = "cuda",
) -> Dict:
    """
    Ensemble N checkpoints on `split`. Returns a summary dict.
    """
    BariatricRSD, BariatricFrameDataset, DataLoader = _import_project(project_src)
    dev = torch.device(device if torch.cuda.is_available() else "cpu")

    ds = BariatricFrameDataset(
        label_json, data_root, split=split,
        sequence_len=sequence_len, frame_stride=frame_stride,
        img_size=img_size, augment=False,
    )
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False,
                        num_workers=num_workers, pin_memory=True)

    # Load labels.json to get per-video total duration and the ground-truth RSD per clip
    with open(label_json) as f:
        videos_meta = json.load(f)
    durations = {v["video_id"]: float(v["total_duration_sec"]) for v in videos_meta}

    # Build truth_by_vid from the first pass by simply calling _infer_split on a dummy model?
    # Simpler: iterate once through the loader to get truths keyed by (vid, ts)
    truths: Dict[Tuple[str, int], float] = {}
    for batch in loader:
        ts = batch["timestamp_sec"].float().cpu().numpy()
        vids = batch["video_id"]
        y = batch["rsd_normalized"].float().cpu().numpy()
        for v, t, yi in zip(vids, ts, y):
            truths[(v, int(round(float(t))))] = float(yi)
    truths_by_vid = _group_by_video(truths)

    # Accumulate predictions across checkpoints and optional hflip view
    acc: Dict[Tuple[str, int], List[float]] = {}
    view_names: List[str] = []

    for ckpt_path in checkpoints:
        print(f"[ensemble] loading {ckpt_path}")
        model = BariatricRSD(
            encoder_checkpoint=None,
            encoder_freeze_layers=6,
            embed_dim=768,
            temporal_layers=6,
            num_phases=num_phases,
        ).to(dev)
        _load_checkpoint(model, ckpt_path, dev)

        for view_hflip in ([False, True] if use_tta_hflip else [False]):
            view_tag = "hflip" if view_hflip else "orig"
            view_names.append(f"{Path(ckpt_path).parent.name}:{view_tag}")
            preds = _infer_split(model, loader, dev, use_hflip=view_hflip)
            for k, v in preds.items():
                acc.setdefault(k, []).append(v)

    # Average predictions across views
    avg_preds: Dict[Tuple[str, int], float] = {k: float(np.mean(vs)) for k, vs in acc.items()}
    preds_by_vid = _group_by_video(avg_preds)

    # Per-video MAE (optionally with isotonic smoothing)
    per_vid = _per_video_mae_min(preds_by_vid, truths_by_vid, durations, use_isotonic=use_isotonic)
    summary = _summarize(per_vid)
    summary["per_video"] = per_vid
    summary["n_checkpoints"] = len(checkpoints)
    summary["n_views_total"] = len(view_names)
    summary["view_names"] = view_names
    summary["use_tta_hflip"] = use_tta_hflip
    summary["use_isotonic"] = use_isotonic
    summary["split"] = split
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.ensemble",
        description="Ensemble + optional TTA + optional isotonic post-processing for RSD test eval."
    )
    ap.add_argument("--checkpoints", nargs="+", required=True,
                    help="Paths to multiple best_model.pth files (one per seed).")
    ap.add_argument("--label_json", required=True)
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--sequence_len", type=int, default=8)
    ap.add_argument("--frame_stride", type=int, default=5)
    ap.add_argument("--img_size", type=int, default=224)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--num_workers", type=int, default=16)
    ap.add_argument("--num_phases", type=int, default=7)
    ap.add_argument("--tta_hflip", action="store_true", help="Apply horizontal-flip TTA.")
    ap.add_argument("--isotonic", action="store_true", help="Apply per-video isotonic smoothing.")
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    ap.add_argument("--out_json", default=None)
    args = ap.parse_args()

    summary = run_ensemble_eval(
        checkpoints=args.checkpoints,
        label_json=args.label_json,
        data_root=args.data_root,
        split=args.split,
        sequence_len=args.sequence_len,
        frame_stride=args.frame_stride,
        img_size=args.img_size,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        num_phases=args.num_phases,
        use_tta_hflip=args.tta_hflip,
        use_isotonic=args.isotonic,
        project_src=args.project_src,
    )

    tag = []
    tag.append(f"ensemble(n={summary['n_checkpoints']})")
    if summary["use_tta_hflip"]: tag.append("TTA-hflip")
    if summary["use_isotonic"]:   tag.append("isotonic")
    tag_str = " + ".join(tag)

    print(f"\n=== Test-set results: {tag_str} ===")
    print(f"Split: {summary['split']} ({summary['n_videos']} videos)")
    print(f"Views total (checkpoints × TTA views): {summary['n_views_total']}")
    print(f"Mean per-video MAE:   {summary['mean']:.3f} min")
    print(f"Median per-video MAE: {summary['median']:.3f} min")
    print(f"Std across videos:    {summary['std']:.3f} min")
    print(f"Min / Max:            {summary['min']:.3f} / {summary['max']:.3f} min")

    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_json, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nWrote full summary → {args.out_json}")


if __name__ == "__main__":
    _cli()

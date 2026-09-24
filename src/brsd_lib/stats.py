"""
brsd_lib.stats
==============

Bootstrap CIs and paired Wilcoxon tests for per-video MAE comparisons.

The paper compares no-token vs oracle vs causal across many configurations.
For every reported MAE delta we want:

  1. A 95% bootstrap CI on the per-video MAE distribution (so the paper
     can say "12.59 ± 0.33 (95% CI: 11.94 – 13.24)" instead of just std).
  2. A paired Wilcoxon signed-rank p-value when comparing two configurations
     evaluated on the same set of videos (so the paper can claim significance
     of e.g. causal < no-token at p < 0.05).

This module is CPU-only and operates on per-video MAE dictionaries — the
same shape produced by `brsd_lib.evaluate.per_video_mae_minutes` and
`brsd_lib.smoothing.per_video_mae_minutes`. It does not require predictions
or PyTorch.

Written fresh for the NeurIPS 2026 submission.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Bootstrap CI on per-video MAE distribution
# ---------------------------------------------------------------------------

def bootstrap_ci(
    per_video_mae: Dict[str, float],
    n_resamples: int = 10_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> Tuple[float, float, float]:
    """Return (mean, lower, upper) bootstrap CI on the per-video MAE.

    Resamples videos with replacement; for each resample, computes the mean
    per-video MAE; reports the empirical 100*α/2 and 100*(1-α/2) quantiles.
    """
    rng = np.random.default_rng(seed)
    values = np.asarray(list(per_video_mae.values()), dtype=np.float64)
    n = values.shape[0]
    if n == 0:
        raise ValueError("per_video_mae is empty")
    means = np.empty(n_resamples, dtype=np.float64)
    for b in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        means[b] = values[idx].mean()
    lo = float(np.quantile(means, (1 - confidence) / 2))
    hi = float(np.quantile(means, 1 - (1 - confidence) / 2))
    return float(values.mean()), lo, hi


# ---------------------------------------------------------------------------
# Paired Wilcoxon signed-rank test
# ---------------------------------------------------------------------------

def paired_wilcoxon(
    a: Dict[str, float],
    b: Dict[str, float],
    alternative: str = "two-sided",
) -> Dict[str, float]:
    """Paired Wilcoxon signed-rank on per-video MAE dicts.

    `a` and `b` must share their video-id keys (the paired-comparison
    contract). Returns dict with statistic, p-value, n, mean diff, median
    diff, sign (positive means a > b, i.e. b is the better config).

    Alternative: 'two-sided' (default), 'less' (a < b), or 'greater' (a > b).
    """
    from scipy.stats import wilcoxon
    keys = sorted(set(a.keys()) & set(b.keys()))
    if len(keys) < 5:
        raise ValueError(f"Too few paired videos ({len(keys)}) for Wilcoxon")
    aa = np.asarray([a[k] for k in keys], dtype=np.float64)
    bb = np.asarray([b[k] for k in keys], dtype=np.float64)
    diffs = aa - bb
    res = wilcoxon(aa, bb, alternative=alternative, zero_method="wilcox")
    return {
        "n_paired": len(keys),
        "statistic": float(res.statistic),
        "p_value": float(res.pvalue),
        "alternative": alternative,
        "mean_diff_a_minus_b": float(diffs.mean()),
        "median_diff_a_minus_b": float(np.median(diffs)),
        "n_a_higher": int((diffs > 0).sum()),
        "n_b_higher": int((diffs < 0).sum()),
        "n_tied": int((diffs == 0).sum()),
    }


# ---------------------------------------------------------------------------
# Convenience: 3-way comparison summary
# ---------------------------------------------------------------------------

def threeway_summary(
    no_token: Dict[str, float],
    oracle: Dict[str, float],
    causal: Dict[str, float],
    n_resamples: int = 10_000,
    seed: int = 0,
) -> Dict:
    """Compute bootstrap CIs for each config and pairwise Wilcoxon tests for
    the three configurations the paper reports."""
    summary = {
        "no_token": {},
        "oracle": {},
        "causal": {},
        "wilcoxon": {},
    }
    for name, d in (("no_token", no_token), ("oracle", oracle), ("causal", causal)):
        m, lo, hi = bootstrap_ci(d, n_resamples=n_resamples, seed=seed)
        summary[name] = {
            "mean": m, "ci_low": lo, "ci_high": hi, "n_videos": len(d),
        }
    # Paired tests: oracle better than no_token? causal better than no_token? causal vs oracle?
    # For each pair, "alternative='less'" tests whether the first is *smaller* (better) than the second.
    summary["wilcoxon"]["oracle_vs_no_token"] = paired_wilcoxon(oracle, no_token, alternative="less")
    summary["wilcoxon"]["causal_vs_no_token"] = paired_wilcoxon(causal, no_token, alternative="less")
    summary["wilcoxon"]["causal_vs_oracle"] = paired_wilcoxon(causal, oracle, alternative="two-sided")
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.stats",
        description="Bootstrap CIs + paired Wilcoxon tests on per-video MAE dicts.",
    )
    ap.add_argument("--no_token_json", required=True,
                    help="JSON file mapping video_id -> per-video MAE in minutes (no-token).")
    ap.add_argument("--oracle_json", required=True,
                    help="JSON file mapping video_id -> per-video MAE in minutes (oracle).")
    ap.add_argument("--causal_json", required=True,
                    help="JSON file mapping video_id -> per-video MAE in minutes (causal).")
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--n_resamples", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    def _load(path):
        with open(path) as f:
            return json.load(f)

    nt = _load(args.no_token_json)
    orc = _load(args.oracle_json)
    cau = _load(args.causal_json)
    out = threeway_summary(nt, orc, cau,
                           n_resamples=args.n_resamples, seed=args.seed)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    _cli()

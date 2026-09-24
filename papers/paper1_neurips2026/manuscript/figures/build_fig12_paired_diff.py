"""
Figure 12 (per FIGURE_ROADMAP.md): paired per-video difference plot.

For each video in the validation set, computes
  Δ_v = MAE_no_token(v) − MAE_strict_causal(v)
and visualizes the per-video distribution. Annotates with median
difference, paired Wilcoxon p-value, and 95% bootstrap CI on the median
(via `brsd_lib.stats`).

Required inputs:
  outputs/run031_per_video_metric/run026_fold0_seed*.json    (no-token, per-video)
  outputs/run035_strict_pixel_only/run033_decoupled_seed*.json  OR
  outputs/run035_strict_pixel_only/run033_oracle_seed*.json   (strict causal, per-video)

Output:
  paper/figures/fig12_paired_per_video_diff.{png,pdf}

Falls back to a placeholder if the inputs aren't yet present.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path
from collections import defaultdict
from statistics import mean, median

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent

NO_TOKEN_GLOB = [
    "outputs/run031_per_video_metric/run026_fold0_seed*.json",
    "lambda_mirror/outputs/run031_per_video_metric/run026_fold0_seed*.json",
]
CAUSAL_GLOB = [
    "outputs/run035_strict_pixel_only/run033_decoupled_seed*.json",
    "outputs/run035_strict_pixel_only/run033_oracle_seed*.json",
    "lambda_mirror/outputs/run035_strict_pixel_only/run033_decoupled_seed*.json",
    "lambda_mirror/outputs/run035_strict_pixel_only/run033_oracle_seed*.json",
]


def _glob_first_nonempty(patterns):
    found = []
    for patt in patterns:
        found.extend(glob.glob(str(ROOT / patt)))
        if found:
            return found
    return []


def _load_per_video_mae(paths):
    """Average per-video MAE across the supplied seeds. Returns dict {video_id: mae_min}."""
    if not paths:
        return {}
    by_vid = defaultdict(list)
    for p in paths:
        try:
            d = json.load(open(p))
        except Exception:
            continue
        pv = d.get("per_video", {})
        for vid, info in pv.items():
            mae = info.get("mae_minutes") if isinstance(info, dict) else None
            if mae is None and isinstance(info, dict):
                mae = info.get("mae_norm")
            if mae is not None:
                by_vid[str(vid)].append(float(mae))
    return {vid: mean(vals) for vid, vals in by_vid.items() if vals}


def main():
    plt.rcParams.update({"figure.dpi": 140, "savefig.bbox": "tight"})

    nt_paths = _glob_first_nonempty(NO_TOKEN_GLOB)
    cs_paths = _glob_first_nonempty(CAUSAL_GLOB)
    nt = _load_per_video_mae(nt_paths)
    cs = _load_per_video_mae(cs_paths)

    fig, ax = plt.subplots(figsize=(6.5, 4.0))

    keys = sorted(set(nt) & set(cs))
    if not keys:
        ax.text(0.5, 0.5,
                "Pending per-video JSONs from\n"
                "  outputs/run031_per_video_metric/run026_fold0_seed*.json (no-token)\n"
                "  outputs/run035_strict_pixel_only/run033_*_seed*.json     (strict causal)\n"
                "Re-run after Run 031 + Run 035 land.",
                ha="center", va="center", fontsize=9, color="#777",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#fffbe5", edgecolor="#aaa"))
        ax.axis("off")
    else:
        diffs = np.array([nt[k] - cs[k] for k in keys], dtype=float)

        # Stats via brsd_lib.stats if importable; otherwise compute inline.
        wilcox_p = float("nan"); ci = (None, None)
        try:
            import sys
            sys.path.insert(0, str(ROOT))
            from brsd_lib.stats import bootstrap_ci, paired_wilcoxon
            mean_, lo, hi = bootstrap_ci({k: nt[k] - cs[k] for k in keys})
            ci = (lo, hi)
            ww = paired_wilcoxon(nt, cs, alternative="greater")
            wilcox_p = ww["p_value"]
        except Exception as e:
            print(f"  (brsd_lib.stats unavailable: {e}; using descriptive stats only)")

        ax.violinplot(diffs, positions=[0], widths=0.7, showmeans=False,
                      showmedians=True, showextrema=True)
        ax.scatter(np.zeros_like(diffs) + (np.random.RandomState(0).rand(len(diffs)) - 0.5) * 0.15,
                   diffs, s=14, color="#444", alpha=0.7, zorder=3)
        ax.axhline(0, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
        ax.set_xticks([0])
        ax.set_xticklabels(["per-video Δ\n(no-token − strict causal)"])
        ax.set_ylabel("Δ MAE (min, > 0 = causal helps)")
        title = (f"Figure 12.  Paired per-video improvement (n={len(keys)} videos)\n"
                 f"median Δ = {median(diffs.tolist()):+.2f} min")
        if not np.isnan(wilcox_p):
            title += f", paired Wilcoxon p = {wilcox_p:.3f}"
        if ci != (None, None):
            title += f"\nbootstrap 95% CI on mean Δ: [{ci[0]:+.2f}, {ci[1]:+.2f}] min"
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", alpha=0.3)

    out_png = HERE / "fig12_paired_per_video_diff.png"
    out_pdf = HERE / "fig12_paired_per_video_diff.pdf"
    fig.savefig(out_png); fig.savefig(out_pdf)
    print(f"wrote {out_png}, {out_pdf}")


if __name__ == "__main__":
    main()

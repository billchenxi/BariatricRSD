"""
Figure 9 (per FIGURE_ROADMAP.md): error vs surgery progress on MB140
strict-protocol checkpoints.

Per-clip predictions are binned by (clip_middle_frame_idx /
video_length) into [10, 25, 50, 75, 90] % progress quantiles. We compute
mean per-video MAE within each bin and plot one line per condition.

Required inputs (per-clip predictions CSVs from compute_residuals on
strict-trained checkpoints with --target_position last):

  outputs/run035_strict_pixel_only/per_clip_*.csv
  OR strict per-clip residuals from a follow-up `compute_residuals` pass

Output:
  paper/figures/fig9_error_vs_progress.{png,pdf}

If no inputs are present, emits a placeholder figure naming the missing
files so the manuscript build doesn't break.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from collections import defaultdict
from statistics import mean

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent.parent

# Search paths for per-clip prediction CSVs. Codex's run035 evaluator
# writes one summary JSON per checkpoint; for progress curves we need
# per-clip rows (video_id, frame_path, prediction, target). The
# `brsd_lib.compute_residuals` CLI produces those CSVs. We accept any
# of the following layouts:
SEARCH_PATTERNS = [
    "outputs/run030_pixel_only_causal/*.csv",
    "outputs/run035_strict_pixel_only/*.csv",
    "outputs/run020/*train*residuals*.csv",      # fallback example
    "lambda_mirror/outputs/run030_pixel_only_causal/*.csv",
    "lambda_mirror/outputs/run035_strict_pixel_only/*.csv",
]

LABEL_JSONS = [
    ROOT / "lambda_mirror" / "labels" / "mb140_fold0_labels_kmeans.json",
    ROOT / "outputs" / "labels" / "mb140_fold0_labels_kmeans.json",
]


def _load_video_lengths():
    """Return {video_id: total_frame_count} from whichever labels file is local."""
    for p in LABEL_JSONS:
        if p.exists():
            data = json.load(open(p))
            return {v["video_id"]: len(v.get("frames", [])) for v in data}
    return {}


def _find_csvs():
    found = []
    for patt in SEARCH_PATTERNS:
        for p in (ROOT.glob(patt)):
            found.append(p)
    return found


def _bin_by_progress(rows, video_lengths, bins=(0.10, 0.25, 0.50, 0.75, 0.90)):
    """rows: list of {video_id, frame_path or frame_idx, prediction, target}.
    Returns {bin_center_pct: list of (pred, target) within tolerance ±0.075}."""
    out = defaultdict(list)
    for r in rows:
        vid = str(r["video_id"])
        n = video_lengths.get(vid, 0)
        if n <= 0: continue
        # frame index inferred from filename suffix if available
        idx = None
        if "frame_idx" in r:
            try: idx = int(r["frame_idx"])
            except: pass
        if idx is None:
            fp = str(r.get("frame_path", ""))
            try:
                # Filenames look like "BBP03_00000040.jpg" or
                # "video12_001234.jpg"; the frame index is the trailing
                # digit run before the extension, after the last "_".
                stem = fp.split("/")[-1].rsplit(".", 1)[0]
                idx = int(stem.rsplit("_", 1)[-1])
            except: pass
        if idx is None: continue
        prog = idx / n
        for b in bins:
            if abs(prog - b) <= 0.075:
                err = abs(float(r["prediction"]) - float(r["target"]))
                out[b].append((vid, err))
                break
    return out


def main():
    plt.rcParams.update({"figure.dpi": 140, "savefig.bbox": "tight"})

    csvs = _find_csvs()
    video_lengths = _load_video_lengths()
    fig, ax = plt.subplots(figsize=(6.5, 4.0))

    if not csvs or not video_lengths:
        ax.text(0.5, 0.5,
                "Pending: per-clip prediction CSVs from\n"
                "  outputs/run030_pixel_only_causal/*.csv  (legacy protocol)\n"
                "  outputs/run035_strict_pixel_only/*.csv  (strict protocol)\n"
                "and labels file at lambda_mirror/labels/mb140_fold0_labels_kmeans.json.\n"
                "Re-run after Run 030 / Run 035 land.",
                ha="center", va="center", fontsize=9, color="#777",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#fffbe5", edgecolor="#aaa"))
        ax.axis("off")
    else:
        # Group CSVs by inferred condition from filename. Note that the
        # CSVs come from `brsd_lib.compute_residuals` (Run 036), which
        # evaluates each trained checkpoint with the cluster ID it was
        # trained on — so the "decoupled" CSVs are decoupled-oracle's
        # per-clip predictions, NOT pixel-only causal predictions. The
        # pixel-only causal numbers come separately from Run 035 (per-
        # checkpoint *.json) and are not represented as a curve here.
        by_cond = defaultdict(list)
        for p in csvs:
            name = p.stem.lower()
            if "no_token" in name or "notok" in name:
                cond = "no-token"
            elif "decoupl" in name:
                cond = "decoupled-oracle"
            elif "oracle" in name:
                cond = "oracle"
            else:
                cond = "other"
            by_cond[cond].append(p)

        bins = [0.10, 0.25, 0.50, 0.75, 0.90]
        colors = {"no-token": "#d84a4a", "oracle": "#3b7dd8",
                  "decoupled-oracle": "#a64a9c", "other": "#888"}
        for cond, paths in by_cond.items():
            all_rows = []
            for p in paths:
                with open(p) as f:
                    for r in csv.DictReader(f):
                        all_rows.append(r)
            binned = _bin_by_progress(all_rows, video_lengths, bins=bins)
            xs, ys = [], []
            for b in bins:
                if b in binned and binned[b]:
                    # per-video MAE within bin: mean over (vid, err) tuples
                    per_vid = defaultdict(list)
                    for vid, err in binned[b]:
                        per_vid[vid].append(err)
                    vid_means = [mean(es) for es in per_vid.values()]
                    # convert normalized error to minutes assuming ~90 min mean
                    ys.append(mean(vid_means) * 90.0)
                    xs.append(int(b * 100))
            if xs:
                ax.plot(xs, ys, marker="o", linewidth=2, label=cond,
                        color=colors.get(cond, "#444"))
        ax.set_xlabel("Surgery progress (%)")
        ax.set_ylabel("Per-video MAE (min, ↓)")
        ax.set_title("Figure 9.  Error vs surgery progress (MB140 fold 0 val)")
        ax.legend()
        ax.grid(alpha=0.3)

    out_png = HERE / "fig9_error_vs_progress.png"
    out_pdf = HERE / "fig9_error_vs_progress.pdf"
    fig.savefig(out_png); fig.savefig(out_pdf)
    print(f"wrote {out_png}, {out_pdf}")


if __name__ == "__main__":
    main()

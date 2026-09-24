"""
Regenerate every figure used in paper/draft.md.

Usage:
    python paper/figures/generate_figures.py

All figures are saved as both .png (for quick viewing) and .pdf (for LaTeX).
Numbers are hardcoded from the repository's SESSION_LOG.md and the results
saved in lambda_mirror/outputs/run*.json. Every figure is reproducible.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

HERE = Path(__file__).parent
plt.rcParams.update({
    "figure.dpi": 140,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
})

# Consistent colour palette across figures
C_WITH  = "#3b7dd8"   # workflow-token configs
C_WO    = "#d84a4a"   # ablation / no-token
C_MB140 = "#3b7dd8"
C_CHOL  = "#f2b134"
C_BERN  = "#4a90a4"
C_STRAS = "#a64a9c"
C_HIGHLIGHT = "#2ea44f"


def save(fig, name):
    for ext in ("png", "pdf"):
        out = HERE / f"{name}.{ext}"
        fig.savefig(out)
    print(f"  -> {name}.{{png,pdf}}")


# ---------------------------------------------------------------------------
# Figure 1 - phase-order diversity contrast (MB140 vs Cholec80)
# ---------------------------------------------------------------------------
def fig_cluster_diversity():
    mb140 = [38, 27, 25, 23, 17, 10]     # from SESSION_LOG run001 note
    cholec = [51, 12, 6, 3]              # from SESSION_LOG Cholec80 clusters

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    for ax, sizes, tag, color, total in [
        (axes[0], mb140,  "MultiBypass140",   C_MB140, 140),
        (axes[1], cholec, "Cholec80 (72 public)", C_CHOL, 72),
    ]:
        bars = ax.bar(range(len(sizes)), sizes, color=color, edgecolor="k", linewidth=0.6)
        for i, b in enumerate(bars):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.5,
                    f"{sizes[i]}\n({100*sizes[i]/total:.0f}%)",
                    ha="center", va="bottom", fontsize=8)
        ax.set_title(f"{tag}: k-means workflow clusters")
        ax.set_xlabel("Cluster ID (sorted by size)")
        ax.set_ylabel("Videos")
        ax.set_ylim(0, max(sizes) * 1.25)
        ax.set_xticks(range(len(sizes)))
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "Figure 1.  Phase-order diversity differs sharply between benchmarks.",
        y=1.02, fontsize=11,
    )
    fig.tight_layout()
    save(fig, "fig1_cluster_diversity")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 - video duration distributions (MB140 Bern vs Stras vs Cholec80)
# ---------------------------------------------------------------------------
def fig_duration_distributions():
    # Use medians from SESSION_LOG (draft §4.1 / §4.2). Simulate a plausible
    # duration distribution if raw durations aren't available on disk.
    mirror = HERE.parent.parent / "lambda_mirror" / "labels"
    mb140_path = mirror / "mb140_fold0_labels_kmeans.json"
    chol_path  = mirror / "cholec80_labels_kmeans.json"

    bern, stras, chol = [], [], []
    if mb140_path.exists():
        for v in json.load(open(mb140_path)):
            dur_min = v["total_duration_sec"] / 60.0
            (bern if v["video_id"].startswith("BBP") else stras).append(dur_min)
    if chol_path.exists():
        for v in json.load(open(chol_path)):
            chol.append(v["total_duration_sec"] / 60.0)

    fig, ax = plt.subplots(figsize=(9, 3.5))
    bins = np.arange(0, 200, 10)
    if bern:
        ax.hist(bern,  bins=bins, alpha=0.55, color=C_BERN,  label=f"MB140 Bern (n={len(bern)}, med={np.median(bern):.0f})")
    if stras:
        ax.hist(stras, bins=bins, alpha=0.55, color=C_STRAS, label=f"MB140 Strasbourg (n={len(stras)}, med={np.median(stras):.0f})")
    if chol:
        ax.hist(chol,  bins=bins, alpha=0.55, color=C_CHOL,  label=f"Cholec80 (n={len(chol)}, med={np.median(chol):.0f})")
    ax.set_xlabel("Video duration (min)")
    ax.set_ylabel("# videos")
    ax.set_title("Figure 2.  Duration distributions: Cholec80 is ~40 min; MB140 is 70-120 min with a center gap.")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    save(fig, "fig2_duration_distributions")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 - architecture diagram (retrospective workflow-conditioned model)
# ---------------------------------------------------------------------------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis("off")
    ax.set_title(
        "Figure 3.  Retrospective workflow-conditioned RSD predictor (this paper's diagnostic model).",
        y=1.04, fontsize=11,
    )

    def box(x, y, w, h, text, color, fontsize=9):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.12",
            linewidth=1.2, edgecolor="#333", facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize)

    def arr(x1, y1, x2, y2):
        ax.add_patch(mpatches.FancyArrowPatch((x1, y1), (x2, y2),
                                              arrowstyle="->", mutation_scale=14,
                                              linewidth=1.1, color="#333"))

    # Frames (8-frame clip)
    for i in range(8):
        box(0.4 + i*0.45, 3.6, 0.4, 0.6, f"t{i}", "#d9e8f6", fontsize=8)
    ax.text(0.4 + 4*0.45, 4.5, "Clip of 8 frames", ha="center", fontsize=9, style="italic")

    # Retrospective phase-order cluster (oracle)
    box(0.2, 2.3, 1.6, 0.6, "Retrospective\nworkflow cluster ID\n(full-video oracle)", "#c7aff1", fontsize=8)

    # ViT + HTA block
    box(2.1, 2.3, 4.5, 0.6, "ViT-B encoder + Hierarchical Temporal Attention", "#a0d8a0", fontsize=9)
    for i in range(8):
        arr(0.4 + i*0.45 + 0.2, 3.6, 0.4 + i*0.45 + 0.2, 2.9)

    # Token sequence with workflow prefix
    box(2.1, 1.3, 0.6, 0.5, "wf", "#c7aff1", fontsize=8)
    for i in range(8):
        box(2.8 + i*0.5, 1.3, 0.4, 0.5, f"f{i}", "#d9e8f6", fontsize=8)
    arr(1.0, 2.3, 2.4, 1.8)
    for i in range(8):
        arr(2.1 + (i+0.5)*0.5 + 0.3, 2.3, 2.8 + i*0.5 + 0.2, 1.8)

    # Heads on the right
    box(8.2, 3.3, 2.4, 0.6, "RSD regression", "#f4b6c2", fontsize=9)
    box(8.2, 2.3, 2.4, 0.6, "Phase classification", "#f4b6c2", fontsize=9)
    box(8.2, 1.3, 2.4, 0.6, "Deviation head\n(IAE, Cholec80 has none)", "#f4b6c2", fontsize=8)

    # Arrows: workflow feat -> heads
    box(6.9, 0.5, 1.0, 0.5, "out[0]\n(wf slot)", "#c7aff1", fontsize=7)
    arr(5.0, 1.3, 7.4, 1.0)
    for head_y in (3.6, 2.6, 1.6):
        arr(7.9, 0.75, 8.2, head_y)

    # Retrospective badge
    box(6.9, 4.1, 4.9, 0.55, "DIAGNOSTIC / OFFLINE: workflow cluster uses full-video phase order",
        "#fff1f2", fontsize=9)

    fig.tight_layout()
    save(fig, "fig3_architecture")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3b - why the current token is a retrospective upper bound
# ---------------------------------------------------------------------------
def fig_retrospective_vs_causal():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    fig.suptitle(
        "Figure 3b.  Why the current workflow token is a retrospective upper bound, not a deployable online input.",
        y=1.02, fontsize=11,
    )

    def setup(ax, title):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis("off")
        ax.set_title(title, fontsize=10, pad=8)

    def box(ax, x, y, w, h, text, color, fontsize=8.5, edge="#333", rounded=0.12):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0.04,rounding_size={rounded}",
            linewidth=1.1, edgecolor=edge, facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)

    def arrow(ax, x1, y1, x2, y2, color="#333", style="->", lw=1.2):
        ax.add_patch(mpatches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle=style, mutation_scale=14, linewidth=lw, color=color,
        ))

    def frame_strip(ax, x0, y, n_past, n_future):
        width = 0.42
        gap = 0.08
        for i in range(n_past):
            box(ax, x0 + i * (width + gap), y, width, 0.55, f"t{i}", "#d9e8f6", fontsize=7.5)
        start = x0 + n_past * (width + gap)
        for i in range(n_future):
            box(ax, start + i * (width + gap), y, width, 0.55, f"f{i+1}", "#f8d7da", fontsize=7.5)
        ax.text(x0 + (n_past - 1) * (width + gap) + width / 2, y + 0.82, "observed by time t", ha="center", fontsize=8, color="#22577a")
        ax.text(start + (n_future - 1) * (width + gap) / 2 + 0.2, y + 0.82, "future after t", ha="center", fontsize=8, color="#9b2226")
        ax.plot([start - gap / 2, start - gap / 2], [y - 0.15, y + 0.72], color="#9b2226", linestyle="--", linewidth=1.2)
        return x0, start + n_future * (width + gap) - gap

    # Left: current retrospective system
    ax = axes[0]
    setup(ax, "Current system: retrospective workflow token")
    frame_strip(ax, 0.5, 5.0, n_past=5, n_future=4)
    box(ax, 0.4, 3.75, 3.0, 0.75, "Full surgery phase sequence", "#fff3cd")
    box(ax, 0.7, 2.55, 2.4, 0.7, "Offline phase-order\nclustering", "#ffe8a1")
    box(ax, 3.9, 2.55, 2.2, 0.7, "Workflow token\nfrom full case", "#c7aff1")
    box(ax, 6.8, 3.75, 2.5, 0.75, "Predict RSD at time t", "#cfe8cf")
    arrow(ax, 1.9, 3.75, 1.9, 3.25)
    arrow(ax, 3.1, 2.9, 3.9, 2.9)
    arrow(ax, 6.1, 2.9, 7.7, 3.75)
    box(ax, 0.5, 1.05, 8.8, 0.95,
        "Problem: at time t, the model is given a token computed from phases that occur after t.\nThat uses future information, so it is not a valid online input.",
        "#fff1f2", fontsize=8.3, edge="#a61b1b")
    ax.text(5.0, 0.35, "Interpretation: useful diagnostic and offline upper bound", ha="center",
            fontsize=8.5, color="#7a1f1f", fontweight="bold")

    # Right: future causal system
    ax = axes[1]
    setup(ax, "Desired next system: causal workflow inference")
    frame_strip(ax, 0.5, 5.0, n_past=5, n_future=4)
    box(ax, 0.5, 3.75, 3.0, 0.75, "Observed prefix only\n(frames up to time t)", "#d9e8f6")
    box(ax, 0.8, 2.55, 2.5, 0.7, "Infer workflow posterior\nq(z | x<=t)", "#bde0fe")
    box(ax, 4.0, 2.55, 2.2, 0.7, "Soft workflow token\nfrom prefix", "#c7aff1")
    box(ax, 6.8, 3.75, 2.5, 0.75, "Predict RSD at time t", "#cfe8cf")
    arrow(ax, 2.0, 3.75, 2.0, 3.25)
    arrow(ax, 3.3, 2.9, 4.0, 2.9)
    arrow(ax, 6.2, 2.9, 7.7, 3.75)
    box(ax, 0.5, 1.05, 8.8, 0.95,
        "Correct formulation: infer workflow state from information available by time t,\nthen condition the predictor on that estimated state.",
        "#eefbf0", fontsize=8.3, edge="#2b7a0b")
    ax.text(5.0, 0.35, "Interpretation: deployable causal workflow-conditioned model", ha="center",
            fontsize=8.5, color="#1f5c1f", fontweight="bold")

    fig.tight_layout()
    save(fig, "fig3b_retrospective_vs_causal")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3c - what future-frame leakage means in the centered-window setup
# ---------------------------------------------------------------------------
def fig_centered_window_leakage():
    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    ax.set_title(
        "Figure 3c.  What future-frame leakage means in the current centered-window clip formulation.",
        fontsize=11, pad=10,
    )

    def box(x, y, w, h, text, color, fontsize=8.5, edge="#333", rounded=0.12):
        rect = mpatches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0.04,rounding_size={rounded}",
            linewidth=1.1, edgecolor=edge, facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)

    def arrow(x1, y1, x2, y2, color="#333", lw=1.2):
        ax.add_patch(mpatches.FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle="->", mutation_scale=14, linewidth=lw, color=color,
        ))

    def timeline(y, title, leak=False):
        ax.text(0.6, y + 0.95, title, fontsize=10, fontweight="bold")
        x0, w, gap = 1.1, 0.72, 0.12
        labels = ["t-3", "t-2", "t-1", "t", "t+1", "t+2", "t+3"]
        colors = []
        for i, lab in enumerate(labels):
            if i <= 3:
                colors.append("#d9e8f6")
            else:
                colors.append("#f8d7da" if leak else "#eeeeee")
        for i, (lab, color) in enumerate(zip(labels, colors)):
            edge = "#a61b1b" if (leak and i >= 4) else "#333"
            box(x0 + i * (w + gap), y, w, 0.62, lab, color, fontsize=8, edge=edge)

        mid_x = x0 + 3 * (w + gap) + w / 2
        ax.plot([mid_x, mid_x], [y - 0.18, y + 0.92], linestyle="--", color="#555", linewidth=1.2)
        ax.text(mid_x, y - 0.34, "target timestamp", ha="center", fontsize=8, color="#444")
        ax.text(x0 + 1.6, y + 0.78, "available at time t", ha="center", fontsize=8, color="#22577a")
        if leak:
            ax.text(x0 + 5.55, y + 0.78, "future relative to t", ha="center", fontsize=8, color="#9b2226")
        else:
            ax.text(x0 + 5.55, y + 0.78, "not yet observable", ha="center", fontsize=8, color="#666")

    timeline(3.35, "Correct online prediction")
    box(8.45, 3.28, 2.8, 0.8,
        "Use frames up to t only,\npredict remaining time at t",
        "#eefbf0", edge="#2b7a0b")
    arrow(7.15, 3.66, 8.45, 3.66, color="#2b7a0b")

    timeline(1.7, "Current paper's centered-window sample", leak=True)
    box(8.45, 1.63, 2.8, 0.8,
        "Predict label at t,\nbut clip still includes t+1..t+3",
        "#fff1f2", edge="#a61b1b")
    arrow(7.15, 2.01, 8.45, 2.01, color="#a61b1b")

    box(0.7, 0.25, 10.55, 0.9,
        "Example: if t is minute 40, the current sample may include frames from minutes 40.5 and 41. "
        "Those frames contain future information, so the result is useful for retrospective analysis "
        "but not a strict real-time deployment claim.",
        "#fff8e6", edge="#b58900", fontsize=8.6)

    fig.tight_layout()
    save(fig, "fig3c_centered_window_leakage")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 - MB140 within-center: token vs no-token (main positive result)
# ---------------------------------------------------------------------------
def fig_mb140_main_result():
    configs = ["No token\n(3 seeds)", "Oracle\n(3 seeds)", "Decoupled\n(3 seeds)"]
    vals    = [13.03, 12.26, 12.18]
    errs    = [0.18,  0.09,  0.14]
    colors  = ["#9ca3af", C_WITH, "#4caa9b"]

    fig, ax = plt.subplots(figsize=(6, 3.6))
    bars = ax.bar(configs, vals, yerr=errs, color=colors, edgecolor="k", capsize=6, linewidth=0.6)
    for b, v, e in zip(bars, vals, errs):
        tag = f"{v:.2f}" + (f" ± {e:.2f}" if e > 0 else "")
        ax.text(b.get_x() + b.get_width()/2, v + e + 0.2,
                tag, ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, 16)
    ax.set_ylabel("Val MAE (min)")
    ax.set_title("MB140 fold-0 strict prefix-only result")
    ax.grid(axis="y", alpha=0.3)
    # Annotate improvement
    ax.annotate("", xy=(2, 12.18 + 0.55), xytext=(0, 13.03 + 0.45),
                arrowprops=dict(arrowstyle="->", color=C_HIGHLIGHT, linewidth=2))
    ax.text(1.0, 14.4, "-0.85 min\n(vs no token)", ha="center",
            color=C_HIGHLIGHT, fontweight="bold", fontsize=9)
    fig.tight_layout()
    save(fig, "fig4_mb140_main_result")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 5 - Cholec80 within-center: token vs no-token (neutral / null result)
# ---------------------------------------------------------------------------
def fig_cholec_null():
    configs = ["With kmeans\ntoken\n(Run 014+016)", "No token\n(Run 015+017)"]
    vals    = [4.49, 4.61]
    errs    = [0.14, 0.19]
    colors  = [C_WITH, C_WO]

    fig, ax = plt.subplots(figsize=(6, 3.6))
    bars = ax.bar(configs, vals, yerr=errs, color=colors, edgecolor="k", capsize=6, linewidth=0.6)
    for b, v, e in zip(bars, vals, errs):
        ax.text(b.get_x() + b.get_width()/2, v + e + 0.1,
                f"{v:.2f} ± {e:.2f}", ha="center", va="bottom", fontsize=10)
    ax.set_ylim(0, 6)
    ax.set_ylabel("Val MAE (min)")
    ax.set_title("Figure 5.  Workflow token is neutral on Cholec80 (low variability).")
    ax.grid(axis="y", alpha=0.3)
    ax.text(0.5, 5.6, "$\\Delta$ inside cross-seed std\n(null result)", ha="center",
            color="#666", fontstyle="italic", fontsize=9)
    fig.tight_layout()
    save(fig, "fig5_cholec80_null_result")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6 - cross-center MAE gap on MB140
# ---------------------------------------------------------------------------
def fig_cross_center():
    labels = ["Within-center\n3-seed mean\n(Run 010)",
              "Cross-center\nBern -> Stras\n(Run 008)"]
    vals = [13.15, 18.94]      # 3-seed within-center mean, cross-center mean
    colors = [C_WITH, C_STRAS]
    fig, ax = plt.subplots(figsize=(6, 3.8))
    bars = ax.bar(labels, vals, color=colors, edgecolor="k", linewidth=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.2, f"{v:.2f} min",
                ha="center", va="bottom", fontsize=10)
    # Annotate the gap
    ax.annotate("", xy=(1, 18.94 - 0.3), xytext=(0, 13.15 + 0.3),
                arrowprops=dict(arrowstyle="->", color="#a00", linewidth=2))
    ax.text(0.5, 16.7, "+5.79 min\ncross-center gap", ha="center",
            color="#a00", fontweight="bold", fontsize=10)
    ax.set_ylabel("Val MAE (min)")
    ax.set_ylim(0, 22)
    ax.set_title("Figure 6.  Workflow heterogeneity dominates cross-center shift.")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    save(fig, "fig6_cross_center_gap")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 7 - Cholec80 inference-time ablation (ensemble + TTA + isotonic)
# ---------------------------------------------------------------------------
def fig_cholec_inference_ablation():
    configs = [
        "3-seed mean\n(Run 018)",
        "+ ensemble\n(019-A)",
        "+ ensemble\n+ TTA (019-B)",
        "Single seed\n+ isotonic\n(019-D)",
        "Full stack\n(019-C) ★",
    ]
    vals = [4.337, 4.099, 4.117, 3.694, 3.563]
    colors = ["#bbb", "#8ea7e9", "#8ea7e9", "#e39e7e", C_HIGHLIGHT]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    bars = ax.bar(configs, vals, color=colors, edgecolor="k", linewidth=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.05, f"{v:.2f}",
                ha="center", va="bottom", fontsize=10)
    ax.axhline(7.10, color="#a00", linestyle="--", linewidth=1,
               label="TransLocal published SOTA (7.10 min)")
    ax.set_ylim(0, 8)
    ax.set_ylabel("Test MAE (min, 30 videos)")
    ax.set_title("Figure 7.  Cholec80 inference-time ablation (appendix; not the paper's main claim).")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    save(fig, "fig7_cholec_inference_ablation")
    plt.close(fig)


# ---------------------------------------------------------------------------
# New figures (Codex round 4 manuscript, post-rewrite)
# ---------------------------------------------------------------------------

def fig8_three_tier_mb140_fold0():
    """Headline: no-token / oracle / teacher-forced prefix on MB140 fold 0,
    3-seed mean ± std. Replaces the older two-bar fig4 with the actual
    three-tier framing the manuscript now uses."""
    conds = ["No token", "Oracle\n(full-video)", "Teacher-forced\nprefix"]
    means = [12.88, 12.59, 12.56]
    stds  = [0.09,  0.33,  0.04]
    colors = [C_WO, C_WITH, C_HIGHLIGHT]
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    bars = ax.bar(conds, means, yerr=stds, capsize=6, color=colors,
                  edgecolor="black", linewidth=0.5)
    for b, m, s in zip(bars, means, stds):
        ax.text(b.get_x() + b.get_width() / 2, m + s + 0.05,
                f"{m:.2f} ± {s:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Validation MAE (min, ↓)")
    ax.set_title("MB140 fold 0 — three-tier comparison (3 seeds)")
    ax.set_ylim(11.5, 13.6)
    ax.axhline(12.88, color=C_WO, linestyle=":", alpha=0.4, linewidth=0.8)
    ax.grid(axis="y", alpha=0.3)
    save(fig, "fig_pre08_mb140_three_tier_legacy")
    plt.close(fig)


def fig9_cholec_three_tier():
    """Cholec80 three-tier: oracle null + teacher-forced negative."""
    conds = ["No token", "Oracle\n(full-video)", "Teacher-forced\nprefix"]
    means = [4.61, 4.49, 5.03]
    stds  = [0.19, 0.14, 0.07]
    colors = [C_WO, C_WITH, "#b03030"]   # last bar red to flag the negative
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    bars = ax.bar(conds, means, yerr=stds, capsize=6, color=colors,
                  edgecolor="black", linewidth=0.5)
    for b, m, s in zip(bars, means, stds):
        ax.text(b.get_x() + b.get_width() / 2, m + s + 0.03,
                f"{m:.2f} ± {s:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Validation MAE (min, ↓)")
    ax.set_title("Cholec80 — oracle null, teacher-forced prefix negative (3 seeds)")
    ax.axhline(4.61, color=C_WO, linestyle=":", alpha=0.4, linewidth=0.8)
    ax.set_ylim(4.0, 5.4)
    ax.grid(axis="y", alpha=0.3)
    save(fig, "fig_supp_cholec_three_tier")
    plt.close(fig)


def fig10_cross_center_collapse():
    """Cross-center: oracle / no-token / teacher-forced (the negative).
    Visualizes that the deployable variant is *worse* under domain shift."""
    conds = ["No token", "Oracle\n(full-video)", "Teacher-forced\nprefix"]
    means = [18.26, 18.05, 20.19]
    stds  = [0.0,   0.0,   0.02]
    colors = [C_WO, C_WITH, "#b03030"]
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    bars = ax.bar(conds, means, yerr=stds, capsize=6, color=colors,
                  edgecolor="black", linewidth=0.5)
    for b, m, s in zip(bars, means, stds):
        ax.text(b.get_x() + b.get_width() / 2, m + s + 0.1,
                f"{m:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Bern → Strasbourg val MAE (min, ↓)")
    ax.set_title("Cross-center: teacher-forced prefix fails under domain shift")
    ax.set_ylim(17.0, 21.5)
    ax.axhline(18.26, color=C_WO, linestyle=":", alpha=0.4, linewidth=0.8,
               label="no-token baseline")
    ax.grid(axis="y", alpha=0.3)
    save(fig, "fig_supp_cross_center_legacy")
    plt.close(fig)


def fig11_variability_scaling():
    """The paper's central claim made visual: token-effect-size scales with
    workflow-variability of the dataset. Plots the token effect (MAE
    reduction) against a variability score (1 − fraction of videos in the
    largest cluster)."""
    # Variability = 1 - (largest cluster fraction)
    # MB140: largest cluster = 38 / 140 = 27%, variability = 73%
    # Cholec80: largest cluster = 51 / 72 = 71%, variability = 29%
    points = [
        ("Cholec80",        0.29, -0.12,  C_CHOL,  False),  # null effect
        ("Cholec80\n(teacher-forced)", 0.29, +0.42, "#b03030", True),  # negative
        ("MB140 within-center", 0.73, -0.29, C_MB140, False),
        ("MB140 cross-center\n(teacher-forced)", 0.73, +1.93, "#b03030", True),
    ]
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    label_offsets = {
        "Cholec80": (8, 6),
        "Cholec80\n(teacher-forced)": (8, 6),
        "MB140 within-center": (8, 6),
        "MB140 cross-center\n(teacher-forced)": (-8, -10),
    }
    label_align = {
        "MB140 cross-center\n(teacher-forced)": ("right", "top"),
    }
    for name, var, eff, color, neg in points:
        ax.scatter(var, eff, s=140, color=color,
                   edgecolor="black", linewidth=0.6,
                   marker="X" if neg else "o")
        ax.annotate(name, (var, eff), textcoords="offset points",
                    xytext=label_offsets[name], fontsize=8.5,
                    ha=label_align.get(name, ("left", "bottom"))[0],
                    va=label_align.get(name, ("left", "bottom"))[1])
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_xlabel("Workflow variability  (1 − largest-cluster fraction)")
    ax.set_ylabel("Token effect on val MAE  (min; negative = helps, positive = hurts)")
    ax.set_title("Workflow-conditioning effect scales with workflow variability")
    ax.grid(alpha=0.3)
    ax.set_xlim(0.2, 0.85)
    save(fig, "fig_variability_scaling")
    plt.close(fig)


def fig12_protocol_audit_ladder():
    """Stacks the four canonical conditioning regimes on MB140 fold 0,
    annotating each with what's consulted at training and inference. This
    is the figure that explains the manuscript's three-tier scoping."""
    rows = [
        ("Pixel-only causal\n(deployable)", "pending Run 035",
         "model frames only", "model frames only"),
        ("Teacher-forced prefix",            "12.56 ± 0.04",
         "GT prefix phases",  "GT prefix phases"),
        ("Oracle (full-video)",              "12.59 ± 0.33",
         "full GT phases",    "full GT phases"),
        ("No token (baseline)",              "12.88 ± 0.09",
         "no signal",         "no signal"),
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    y = np.arange(len(rows))
    labels    = [r[0] for r in rows]
    vals      = [r[1] for r in rows]
    train_use = [r[2] for r in rows]
    infer_use = [r[3] for r in rows]
    for i, (label, val, tu, iu) in enumerate(rows):
        ax.text(0.02, y[i], label, va="center", fontsize=10, fontweight="bold")
        ax.text(0.36, y[i], "train: " + tu, va="center", fontsize=9, color="#555")
        ax.text(0.64, y[i], "infer: " + iu, va="center", fontsize=9, color="#555")
        ax.text(0.99, y[i], val, va="center", ha="right", fontsize=10,
                fontweight="bold",
                color=("#888" if "pending" in val else "black"))
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlim(0, 1.05)
    ax.axis("off")
    ax.set_title("Four signal regimes on MB140 fold 0 — what each row consults",
                 fontsize=11, pad=12)
    save(fig, "fig_protocol_ladder")
    plt.close(fig)


def main():
    print(f"Generating figures into {HERE}/")
    fig_cluster_diversity()
    fig_duration_distributions()
    fig_architecture()
    fig_retrospective_vs_causal()
    fig_centered_window_leakage()
    fig_mb140_main_result()
    fig_cholec_null()
    fig_cross_center()
    fig_cholec_inference_ablation()
    fig8_three_tier_mb140_fold0()
    fig9_cholec_three_tier()
    fig10_cross_center_collapse()
    fig11_variability_scaling()
    fig12_protocol_audit_ladder()
    print("Done.")


if __name__ == "__main__":
    main()

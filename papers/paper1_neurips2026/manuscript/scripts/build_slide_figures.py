"""
Build slide-ready figures from the paper's results data.

Output: paper/figures_slides/  (separate from paper/figures/ which is the
                                paper-PDF-bound figures).

Figures produced (all .png + .pdf at 300 DPI):
  fig_main_mb140_within         MB140 fold-0 within-center 3-condition bars
  fig_main_mb140_cross_center   MB140 cross-center 3-condition bars
  fig_phase_e_5fold             Per-fold Phase E results (5×3 grouped bars)
  fig_longer_context            Run 042 seq_len 8 vs 16 (2-condition × 2-seq bars)
  fig_cholec80_strict_vs_legacy Cholec80 strict vs centered protocol comparison
  fig_variability_scaling       The headline cross-dataset variability curve
  fig_cluster_sizes             MB140 (K=6) vs Cholec80 (K=4) cluster size bars
  fig_protocol_compare_summary  Strict vs centered comparison summary across regimes
  fig_summary_at_a_glance       Single-figure "headline" summary
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "figures_slides"
OUTDIR.mkdir(parents=True, exist_ok=True)

# --- consistent slide-friendly style ---
plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.titlesize": 18,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Brand-consistent palette (no-token / oracle / decoupled / shuffled / negative)
COLORS = {
    "no_token":   "#9CA3AF",   # gray
    "oracle":     "#60A5FA",   # blue
    "decoupled":  "#1E40AF",   # deep blue (winner)
    "shuffled":   "#A78BFA",   # purple (control)
    "negative":   "#EF4444",   # red (negative effect)
    "ensemble":   "#10B981",   # green (Cholec80 inference stack)
}


def save(fig, name):
    p = OUTDIR / name
    fig.savefig(str(p) + ".png")
    fig.savefig(str(p) + ".pdf")
    plt.close(fig)
    print(f"  wrote {p}.png + .pdf")


# =====================================================================
# 1. MB140 fold-0 within-center (the headline)
# =====================================================================
def fig_main_mb140_within():
    conditions = ["no-token", "oracle", "decoupled\noracle"]
    means      = [13.03, 12.26, 12.18]
    stds       = [0.18, 0.09, 0.11]
    colors     = [COLORS["no_token"], COLORS["oracle"], COLORS["decoupled"]]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(conditions, means, yerr=stds, capsize=8,
                  color=colors, edgecolor="black", linewidth=0.7)
    for bar, m, s in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width()/2, m + s + 0.15,
                f"{m:.2f}\n± {s:.2f}", ha="center", va="bottom",
                fontsize=11, fontweight="bold")

    ax.set_ylabel("Validation MAE (min) ↓")
    ax.set_title("MB140 fold-0, strict prefix-only protocol\n(3 seeds, 20 val videos)")
    ax.set_ylim(0, max(means) * 1.18)
    ax.annotate("", xy=(2, 12.18), xytext=(0, 13.03),
                arrowprops=dict(arrowstyle="<->", color="darkred", lw=2))
    ax.text(1.0, 12.6, "−0.85 min\n(6.5%)",
            ha="center", color="darkred", fontsize=12, fontweight="bold")

    save(fig, "fig_main_mb140_within")


# =====================================================================
# 2. MB140 cross-center (Bern → Strasbourg)
# =====================================================================
def fig_main_mb140_cross_center():
    conditions = ["no-token", "oracle", "decoupled\noracle"]
    means      = [17.80, 17.71, 17.33]
    stds       = [0.55, 0.23, 0.15]
    colors     = [COLORS["no_token"], COLORS["oracle"], COLORS["decoupled"]]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(conditions, means, yerr=stds, capsize=8,
                  color=colors, edgecolor="black", linewidth=0.7)
    for bar, m, s in zip(bars, means, stds):
        ax.text(bar.get_x() + bar.get_width()/2, m + s + 0.2,
                f"{m:.2f}\n± {s:.2f}", ha="center", va="bottom",
                fontsize=11, fontweight="bold")

    ax.set_ylabel("Cross-center val MAE (min) ↓")
    ax.set_title("MB140 cross-center: Bern → Strasbourg\n(3 seeds, 70 val videos)")
    ax.set_ylim(0, max(means) * 1.15)
    ax.annotate("", xy=(2, 17.33), xytext=(0, 17.80),
                arrowprops=dict(arrowstyle="<->", color="darkred", lw=2))
    ax.text(1.0, 17.55, "−0.47 min",
            ha="center", color="darkred", fontsize=12, fontweight="bold")

    save(fig, "fig_main_mb140_cross_center")


# =====================================================================
# 3. Phase E 5-fold extension — grouped bars
# =====================================================================
def fig_phase_e_5fold():
    summary = json.loads((ROOT / "phase_e_summary.json").read_text())
    folds = list(range(5))
    no_t = [summary["per_fold"]["no_token"][str(f)]["mean"] for f in folds]
    or_  = [summary["per_fold"]["oracle"][str(f)]["mean"] for f in folds]
    dec  = [summary["per_fold"]["decoupled"][str(f)]["mean"] for f in folds]
    no_t_std = [summary["per_fold"]["no_token"][str(f)]["std"] for f in folds]
    or_std   = [summary["per_fold"]["oracle"][str(f)]["std"] for f in folds]
    dec_std  = [summary["per_fold"]["decoupled"][str(f)]["std"] for f in folds]

    x = np.arange(len(folds))
    width = 0.27
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(x - width, no_t, width, yerr=no_t_std, capsize=4,
           color=COLORS["no_token"], label="no-token", edgecolor="black", lw=0.5)
    ax.bar(x, or_, width, yerr=or_std, capsize=4,
           color=COLORS["oracle"], label="oracle", edgecolor="black", lw=0.5)
    ax.bar(x + width, dec, width, yerr=dec_std, capsize=4,
           color=COLORS["decoupled"], label="decoupled-oracle", edgecolor="black", lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Fold {f}{' (dev)' if f == 0 else ''}" for f in folds])
    ax.set_ylabel("Validation MAE (min) ↓")
    ax.set_title("MB140 Phase E: 5-fold × 3-seed × 3-condition\n"
                 "(3 seeds per fold; fold 0 is development fold)")
    ax.legend(loc="upper right", framealpha=0.9)

    overall = summary["overall"]
    txt = (f"5-fold mean Δ (decoupled − no-token): "
           f"{summary['deltas']['overall']['decoupled_minus_no_token']:+.2f} min\n"
           f"Fold-0 Δ: {summary['deltas']['0']['decoupled_minus_no_token']:+.2f} min "
           f"(largest)")
    ax.text(0.02, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=11, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

    save(fig, "fig_phase_e_5fold")


# =====================================================================
# 4. Run 042 longer-context: seq_len 8 vs 16
# =====================================================================
def fig_longer_context():
    conditions = ["no-token", "decoupled-oracle"]
    seq8 = [13.03, 12.18]
    seq16 = [12.46, 11.02]
    seq8_std = [0.18, 0.11]

    x = np.arange(len(conditions))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars1 = ax.bar(x - width/2, seq8, width, yerr=seq8_std, capsize=5,
                   color=COLORS["no_token"], label="seq_len = 8 (3-seed)",
                   edgecolor="black", lw=0.5)
    bars2 = ax.bar(x + width/2, seq16, width,
                   color=COLORS["decoupled"], label="seq_len = 16 (1 seed, Run 042)",
                   edgecolor="black", lw=0.5)

    for bars, vals in [(bars1, seq8), (bars2, seq16)]:
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, v + 0.15,
                    f"{v:.2f}", ha="center", va="bottom", fontsize=11,
                    fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel("MB140 fold-0 val MAE (min) ↓")
    ax.set_title("Longer-context ablation (Run 042)\n"
                 "Wider conditioning gain with more temporal context")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.set_ylim(0, 14.5)

    txt = ("Conditioning gain widens:\n"
           "  seq_len 8:  −0.85 min\n"
           "  seq_len 16: −1.44 min")
    ax.text(0.02, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=11, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

    save(fig, "fig_longer_context")


# =====================================================================
# 5. Cholec80 strict vs centered (the null result)
# =====================================================================
def fig_cholec80_strict_vs_legacy():
    conditions = ["no-token", "oracle", "teacher-forced\nprefix"]
    centered = [4.61, 4.49, 5.03]
    cent_std = [0.19, 0.14, 0.07]
    strict   = [4.34, 4.33, 4.26]

    x = np.arange(len(conditions))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.bar(x - width/2, centered, width, yerr=cent_std, capsize=5,
           color=COLORS["oracle"], label="centered-window (legacy, 3-seed)",
           edgecolor="black", lw=0.5)
    bars2 = ax.bar(x + width/2, strict, width,
                   color=COLORS["decoupled"], label="strict prefix-only (1 seed)",
                   edgecolor="black", lw=0.5)
    for b, v in zip(ax.patches[:3], centered):
        ax.text(b.get_x() + b.get_width()/2, v + 0.1,
                f"{v:.2f}", ha="center", va="bottom", fontsize=10)
    for b, v in zip(bars2, strict):
        ax.text(b.get_x() + b.get_width()/2, v + 0.07,
                f"{v:.2f}", ha="center", va="bottom", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(conditions)
    ax.set_ylabel("Cholec80 val MAE (min) ↓")
    ax.set_title("Cholec80: workflow conditioning has no effect\n"
                 "(3-seed centered-window; 1-seed strict)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.set_ylim(0, 5.8)

    txt = ("All three strict conditions collapse to ~4.3.\n"
           "Centered teacher-forced prefix is +0.42 negative\n"
           "(future-frame leakage interaction, vanishes under strict).")
    ax.text(0.50, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

    save(fig, "fig_cholec80_strict_vs_legacy")


# =====================================================================
# 6. Variability-scaling curve — the headline thesis figure
# =====================================================================
def fig_variability_scaling():
    rows = [
        ("Cholec80 oracle\n(centered)",                    1.27, -0.12, "null"),
        ("Cholec80 TF-prefix\n(centered)",                 1.27, +0.42, "neg"),
        ("MB140 within-center\n(centered)",                2.48, -0.29, "pos"),
        ("MB140 within-center\n(strict)",                  2.48, -0.85, "pos"),
        ("MB140 cross-center\n(strict)",                   2.48, -0.47, "pos"),
        ("MB140 cross-center TF-prefix\n(centered)",       2.48, +1.93, "neg"),
    ]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for label, hz, delta, sign in rows:
        c = (COLORS["decoupled"] if sign == "pos" else
             COLORS["negative"]   if sign == "neg" else
             COLORS["no_token"])
        ax.scatter(hz, delta, s=200, c=c, edgecolor="black", lw=1.2, zorder=3)
        ax.annotate(label, (hz, delta), textcoords="offset points",
                    xytext=(8, 8 if delta < 0 else -25), fontsize=10)
    ax.axhline(0, color="black", lw=0.7, ls="-", zorder=1)
    ax.set_xlabel("Cluster entropy H(z) (bits)")
    ax.set_ylabel("Δ val MAE = workflow gain (min, negative = better)")
    ax.set_title("Variability scaling: workflow conditioning helps\n"
                 "where workflow has more entropy")
    ax.set_xticks([1.27, 2.48])
    ax.set_xticklabels(["Cholec80\nH = 1.27 bits", "MB140\nH = 2.48 bits"])
    ax.invert_yaxis()  # so "better" goes up

    handles = [
        plt.scatter([], [], s=120, c=COLORS["decoupled"], edgecolor="black",
                    label="positive (conditioning helps)"),
        plt.scatter([], [], s=120, c=COLORS["no_token"], edgecolor="black",
                    label="null"),
        plt.scatter([], [], s=120, c=COLORS["negative"], edgecolor="black",
                    label="negative (conditioning hurts)"),
    ]
    ax.legend(handles=handles, loc="lower left", framealpha=0.9)
    save(fig, "fig_variability_scaling")


# =====================================================================
# 7. Cluster size distribution: MB140 vs Cholec80
# =====================================================================
def fig_cluster_sizes():
    mb140_sizes = [38, 27, 25, 23, 17, 10]   # K=6
    chol_sizes  = [51, 12, 6, 3]             # K=4

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, sizes, name, hz in [
        (axes[0], mb140_sizes, "MultiBypass140 (K=6)", 2.48),
        (axes[1], chol_sizes, "Cholec80 (K=4)",       1.27),
    ]:
        bars = ax.bar(range(1, len(sizes)+1), sizes,
                      color=COLORS["decoupled"], edgecolor="black", lw=0.7)
        for b, s in zip(bars, sizes):
            ax.text(b.get_x() + b.get_width()/2, s + 0.7,
                    str(s), ha="center", va="bottom", fontsize=12,
                    fontweight="bold")
        ax.set_title(f"{name}\nH(z) = {hz} bits")
        ax.set_xlabel("Cluster ID")
        ax.set_ylabel("Number of videos")
        total = sum(sizes)
        max_frac = max(sizes) / total
        ax.text(0.97, 0.95,
                f"largest = {max_frac*100:.0f}% of corpus",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=10, family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray"))

    fig.suptitle("Workflow-cluster diversity drives the conditioning gain", y=1.02)
    save(fig, "fig_cluster_sizes")


# =====================================================================
# 8. Protocol comparison summary — strict vs centered, three regimes
# =====================================================================
def fig_protocol_compare_summary():
    regimes = ["MB140\nwithin-center", "MB140\ncross-center",
               "Cholec80\noracle", "Cholec80\nTF-prefix"]
    centered = [-0.29, +1.93, -0.12, +0.42]
    strict   = [-0.85, -0.47, -0.05, -0.08]

    x = np.arange(len(regimes))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x - width/2, centered, width,
           color=COLORS["oracle"], label="centered-window",
           edgecolor="black", lw=0.5)
    ax.bar(x + width/2, strict, width,
           color=COLORS["decoupled"], label="strict prefix-only",
           edgecolor="black", lw=0.5)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(regimes)
    ax.set_ylabel("Δ val MAE = workflow gain (min)\nnegative = conditioning helps")
    ax.set_title("Strict prefix-only protocol gives larger and more consistent gains\n"
                 "(reverses the cross-center 'negative' result of centered-window)")
    ax.legend(loc="upper right", framealpha=0.9)

    for i, (c, s) in enumerate(zip(centered, strict)):
        ax.text(i - width/2, c + (0.1 if c > 0 else -0.15),
                f"{c:+.2f}", ha="center", fontsize=10)
        ax.text(i + width/2, s + (0.1 if s > 0 else -0.15),
                f"{s:+.2f}", ha="center", fontsize=10)

    save(fig, "fig_protocol_compare_summary")


# =====================================================================
# 9. Single-figure "headline" summary
# =====================================================================
def fig_summary_at_a_glance():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # (a) MB140 within-center
    ax = axes[0]
    cond = ["no-token", "decoupled"]
    vals, errs = [13.03, 12.18], [0.18, 0.11]
    ax.bar(cond, vals, yerr=errs, capsize=6,
           color=[COLORS["no_token"], COLORS["decoupled"]],
           edgecolor="black", lw=0.6)
    for i, (v, e) in enumerate(zip(vals, errs)):
        ax.text(i, v + e + 0.15, f"{v:.2f}", ha="center", fontweight="bold",
                fontsize=12)
    ax.set_ylabel("Val MAE (min)")
    ax.set_title("MB140 within-center\n−0.85 min (3 seeds)")
    ax.set_ylim(0, 14.5)

    # (b) MB140 cross-center
    ax = axes[1]
    vals, errs = [17.80, 17.33], [0.55, 0.15]
    ax.bar(cond, vals, yerr=errs, capsize=6,
           color=[COLORS["no_token"], COLORS["decoupled"]],
           edgecolor="black", lw=0.6)
    for i, (v, e) in enumerate(zip(vals, errs)):
        ax.text(i, v + e + 0.15, f"{v:.2f}", ha="center", fontweight="bold",
                fontsize=12)
    ax.set_ylabel("Val MAE (min)")
    ax.set_title("MB140 cross-center\n−0.47 min (3 seeds)")
    ax.set_ylim(0, 19.5)

    # (c) Cholec80 strict
    ax = axes[2]
    vals = [4.34, 4.33]
    ax.bar(cond, vals, color=[COLORS["no_token"], COLORS["decoupled"]],
           edgecolor="black", lw=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.07, f"{v:.2f}", ha="center", fontweight="bold",
                fontsize=12)
    ax.set_ylabel("Val MAE (min)")
    ax.set_title("Cholec80 strict\n−0.01 min (null)")
    ax.set_ylim(0, 5.2)

    fig.suptitle("Workflow conditioning helps where workflow varies — "
                 "and not where it doesn't", y=1.02, fontsize=18)
    save(fig, "fig_summary_at_a_glance")


# =====================================================================
# 10. Literature comparison — Cholec80 RSD across published methods
# =====================================================================
def fig_literature_comparison():
    methods = ["RSDNet\n2019", "TransLocal\n2024", "Kostopoulos\n2025\n(annotations)",
               "Ours\nsingle-seed", "Ours\nensemble + isotonic"]
    maes    = [8.0, 7.10, 5.89, 4.46, 3.56]
    splits  = ["40-video\ncanonical", "40-video\ncanonical", "their split\n(annotations)",
               "30-video\npublic", "30-video\npublic"]
    inputs  = ["raw video", "raw video", "phase + tool labels", "raw video", "raw video"]
    colors  = ["#9CA3AF", "#9CA3AF", "#A78BFA", "#1E40AF", "#10B981"]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(range(len(methods)), maes, color=colors,
                  edgecolor="black", linewidth=0.7)
    for i, (b, m, s, inp) in enumerate(zip(bars, maes, splits, inputs)):
        ax.text(b.get_x() + b.get_width()/2, m + 0.15, f"{m:.2f}",
                ha="center", va="bottom", fontweight="bold", fontsize=12)
        ax.text(b.get_x() + b.get_width()/2, -0.6, s,
                ha="center", va="top", fontsize=9, style="italic")
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, fontsize=11)
    ax.set_ylabel("Cholec80 test MAE (min) ↓")
    ax.set_title("Cholec80 RSD literature comparison\n"
                 "(non-canonical splits & input modalities — informative not benchmark-clean)")
    ax.set_ylim(-1.2, 9)
    ax.axhline(0, color="black", lw=0.4)

    txt = ("Our 3.56 is the lowest absolute number known to us\n"
           "but on a different (30-video) test split. Kostopoulos\n"
           "uses already-annotated phase + tool labels as input,\n"
           "not raw video — different problem.")
    ax.text(0.50, 0.96, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))
    save(fig, "fig_literature_comparison")


# =====================================================================
# 11. Parameter breakdown — frozen vs trainable
# =====================================================================
def fig_parameter_breakdown():
    parts = ["ViT-B/16\nfrozen blocks 1-6\n(~43M)",
             "ViT-B/16\ntrainable blocks 7-12\n(~43M)",
             "HTA temporal head\n6 blocks, 768-dim\n(~57M)",
             "Task heads\nRSD + phase + dev\n(~7M)",
             "Workflow embedding\nE ∈ R^(K×768)\n(<1M)"]
    sizes  = [43, 43, 57, 7, 1]
    colors = ["#9CA3AF", "#1E40AF", "#3B82F6", "#10B981", "#A78BFA"]

    fig, ax = plt.subplots(figsize=(10, 5))
    wedges, texts = ax.pie(sizes, colors=colors, startangle=90,
                            wedgeprops=dict(width=0.4, edgecolor="white", lw=2))
    ax.set_title("Model parameter breakdown — total ≈ 149.9M, trainable ≈ 106.8M")

    legend_labels = [f"{p} ({s}M, {s/sum(sizes)*100:.0f}%)"
                     for p, s in zip(parts, sizes)]
    ax.legend(wedges, legend_labels, loc="center left",
              bbox_to_anchor=(1.0, 0.5), fontsize=11, frameon=False)
    save(fig, "fig_parameter_breakdown")


# =====================================================================
# 12. Cholec80 inference-time ablation — incremental gains
# =====================================================================
def fig_cholec80_inference_ablation():
    stages = ["single-seed\n(no post-proc)", "+ per-video\nisotonic",
              "+ 3-seed\nensemble", "+ H-flip\nTTA"]
    maes   = [4.46, 3.69, 3.61, 3.56]
    colors = ["#9CA3AF", "#10B981", "#10B981", "#10B981"]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(stages, maes, color=colors, edgecolor="black", lw=0.7)
    for b, m in zip(bars, maes):
        ax.text(b.get_x() + b.get_width()/2, m + 0.05, f"{m:.2f}",
                ha="center", va="bottom", fontweight="bold", fontsize=12)

    deltas = [maes[i] - maes[i-1] for i in range(1, len(maes))]
    for i, d in enumerate(deltas):
        ax.annotate(f"{d:+.2f}", xy=(i + 0.5, max(maes[i], maes[i+1]) + 0.2),
                    ha="center", fontsize=10, color="darkred", fontweight="bold")

    ax.set_ylabel("Cholec80 test MAE (min) ↓")
    ax.set_title("Cholec80 inference-time stack — isotonic dominates\n"
                 "(83% of gain from calibration alone, not from conditioning)")
    ax.set_ylim(0, 5)

    txt = ("Workflow conditioning is null on Cholec80 (§6.3).\n"
           "The 4.46 → 3.56 gain is post-processing, not workflow.")
    ax.text(0.50, 0.97, txt, transform=ax.transAxes, va="top", ha="left",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))
    save(fig, "fig_cholec80_inference_ablation")


# =====================================================================
# 13. Windowed local attention vs HTA-inspired — schematic comparison
# =====================================================================
def fig_attention_compare():
    """Two-panel illustration: how a single block routes attention in
    windowed-local (TransLocal-style) vs HTA-inspired (Surgformer-derived)
    designs, on a 9-token sequence."""
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch

    n = 9                  # 9 tokens (8 frames + 1 workflow token)
    token_y = 1.0
    token_r = 0.34

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # ---------- helper to draw the token row ----------
    def draw_tokens(ax, highlight_global=False):
        for i in range(n):
            color = COLORS["decoupled"] if (i == 0 and highlight_global) else COLORS["no_token"]
            ax.add_patch(plt.Circle((i, token_y), token_r,
                                    facecolor=color, edgecolor="black",
                                    lw=0.9, zorder=4))
            label = "wf" if i == 0 else str(i)   # token 0 is the workflow token
            ax.text(i, token_y, label, ha="center", va="center",
                    fontsize=10, color="white" if color == COLORS["decoupled"]
                    else "black", fontweight="bold", zorder=5)
        # axis labels
        ax.text(-0.9, token_y, "Tokens:", ha="right", va="center", fontsize=11)

    # ---------- LEFT: windowed local attention ----------
    ax = axes[0]
    draw_tokens(ax, highlight_global=False)

    # two windows: tokens [0..3] and [4..8]
    win_color = COLORS["oracle"]
    ax.add_patch(FancyBboxPatch((-0.5, token_y - 0.7), 4.0, 1.4,
                                boxstyle="round,pad=0.05",
                                fc=win_color, alpha=0.18,
                                ec=win_color, lw=2.0, zorder=2))
    ax.add_patch(FancyBboxPatch((3.5, token_y - 0.7), 5.0, 1.4,
                                boxstyle="round,pad=0.05",
                                fc=win_color, alpha=0.18,
                                ec=win_color, lw=2.0, zorder=2))
    ax.text(1.5, token_y + 0.95, "Window 1", ha="center", color=win_color,
            fontweight="bold", fontsize=11)
    ax.text(6.0, token_y + 0.95, "Window 2", ha="center", color=win_color,
            fontweight="bold", fontsize=11)

    # within-window attention edges
    def draw_attn(ax, lo, hi, y_offset, color, alpha=0.4):
        for i in range(lo, hi + 1):
            for j in range(lo, hi + 1):
                if i == j:
                    continue
                # arc connecting i and j
                xa, xb = i, j
                cx = (xa + xb) / 2
                arc_height = 0.18 + 0.05 * abs(xa - xb)
                from matplotlib.patches import FancyArrowPatch
                arrow = FancyArrowPatch(
                    (xa, token_y + y_offset),
                    (xb, token_y + y_offset),
                    connectionstyle=f"arc3,rad=0.{int(arc_height*30)}",
                    color=color, alpha=alpha, lw=0.5,
                    arrowstyle="-")
                ax.add_patch(arrow)

    draw_attn(ax, 0, 3, 0.45, win_color, alpha=0.45)
    draw_attn(ax, 4, 8, 0.45, win_color, alpha=0.45)

    # X mark between windows showing no cross-window attention
    ax.text(3.75, token_y + 1.6, "✗  no cross-window\nattention this layer",
            ha="center", va="center", fontsize=10, color="darkred",
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white",
                      ec="darkred", lw=1))

    ax.set_xlim(-1.8, n)
    ax.set_ylim(-1.2, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Windowed local attention\n(TransLocal-style: one attention per block)",
                 fontsize=13, pad=10)

    # caption box
    txt = ("• Each block: ONE attention computation over a window\n"
           "• Receptive field per block: window size W only\n"
           "• Long-range info propagates across stacked blocks\n"
           "• Compute: O(T · W) per block")
    ax.text(0.5, -0.10, txt, transform=ax.transAxes, ha="center", va="top",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray"))

    # ---------- RIGHT: HTA-inspired ----------
    ax = axes[1]
    draw_tokens(ax, highlight_global=False)

    # local branch box (tokens 0..3)
    local_color = COLORS["oracle"]
    ax.add_patch(FancyBboxPatch((-0.5, token_y - 0.7), 4.0, 1.4,
                                boxstyle="round,pad=0.05",
                                fc=local_color, alpha=0.18,
                                ec=local_color, lw=2.0, zorder=2))
    ax.text(1.5, token_y - 1.1, "Local branch\n(first half)",
            ha="center", color=local_color, fontweight="bold", fontsize=11)
    draw_attn(ax, 0, 3, 0.45, local_color, alpha=0.45)

    # global branch box (all 9 tokens) — drawn above
    global_color = COLORS["decoupled"]
    ax.add_patch(FancyBboxPatch((-0.5, token_y + 1.4), 9.0, 1.0,
                                boxstyle="round,pad=0.05",
                                fc=global_color, alpha=0.20,
                                ec=global_color, lw=2.0, zorder=2))
    ax.text(4, token_y + 1.9, "Global branch (all 9 tokens)",
            ha="center", color="white", fontweight="bold", fontsize=11,
            bbox=dict(boxstyle="round,pad=0.3", fc=global_color, ec="black"))
    # global attention indicated by horizontal "all-to-all" curves on top edge
    for i in range(0, n, 2):
        for j in range(0, n, 2):
            if i == j: continue
            arrow = FancyArrowPatch(
                (i, token_y + 1.5),
                (j, token_y + 1.5),
                connectionstyle=f"arc3,rad=0.15",
                color=global_color, alpha=0.35, lw=0.5,
                arrowstyle="-")
            ax.add_patch(arrow)

    # concat + projection at the bottom
    ax.add_patch(FancyBboxPatch((2.0, token_y - 2.4), 5.0, 0.7,
                                boxstyle="round,pad=0.05",
                                fc="#10B981", ec="black", lw=1.0, zorder=3))
    ax.text(4.5, token_y - 2.05, "concat → linear projection (768-d)",
            ha="center", va="center", fontsize=11, color="white",
            fontweight="bold", zorder=4)

    # arrows from both branches to the concat box
    ax.annotate("", xy=(4.5, token_y - 1.7), xytext=(1.5, token_y - 0.85),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2))
    ax.annotate("", xy=(4.5, token_y - 1.7), xytext=(4, token_y + 1.45),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2))

    ax.set_xlim(-1.8, n)
    ax.set_ylim(-3.5, 3.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Hierarchical Temporal Attention (HTA-inspired)\n"
                 "(Surgformer-derived: local AND global in parallel)",
                 fontsize=13, pad=10)

    # caption box
    txt = ("• Each block: TWO attention computations (local + global)\n"
           "• Receptive field per block: full sequence (via global)\n"
           "• Long-range info available WITHIN each block\n"
           "• Compute: O(T · W) + O(T²) per block")
    ax.text(0.5, -0.10, txt, transform=ax.transAxes, ha="center", va="top",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray"))

    fig.suptitle(
        "Per-block attention pattern: how each design routes information",
        fontsize=15, fontweight="bold", y=1.00)
    save(fig, "fig_attention_compare")


# =====================================================================
# 14. Causal-at-inference Step 1: prefix forward-pass with placeholder
#     cluster — illustrates §4.5 / §4.5.1 of the paper
# =====================================================================
def fig_causal_step1():
    """Step 1 of the causal-at-inference recovery pipeline:
       prefix frames → visual encoder → HTA → phase head, with a
       *placeholder* workflow token. Shows that the phase output does
       not depend on the placeholder because of decoupled-phase-head."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

    fig, ax = plt.subplots(figsize=(15, 6.5))
    ax.set_xlim(0, 16)
    ax.set_ylim(-1.5, 7)
    ax.axis("off")

    # ---------- prefix frames (left) ----------
    n_frames = 8
    frame_w = 0.55
    frame_h = 0.85
    x0 = 0.5
    y_frames = 4.5
    for i in range(n_frames):
        ax.add_patch(Rectangle(
            (x0 + i * (frame_w + 0.08), y_frames),
            frame_w, frame_h,
            fc=plt.cm.Greys(0.25 + 0.06 * i), ec="black", lw=0.8))
        if i in [0, n_frames - 1]:
            ax.text(x0 + i * (frame_w + 0.08) + frame_w / 2,
                    y_frames - 0.32,
                    f"$x_{{{i+1 if i==0 else 't'}}}$",
                    ha="center", fontsize=12)
        elif i == 4:
            ax.text(x0 + i * (frame_w + 0.08) + frame_w / 2,
                    y_frames - 0.32, "...", ha="center", fontsize=14)
    ax.text(x0 + (n_frames * (frame_w + 0.08)) / 2 - 0.04,
            y_frames + frame_h + 0.45,
            "Prefix frames $x_{1:t}$\n(observed up to time $t$)",
            ha="center", fontsize=12, fontweight="bold")

    # arrow from frames to encoder
    ax.annotate("", xy=(6.0, y_frames + frame_h / 2),
                xytext=(x0 + n_frames * (frame_w + 0.08) - 0.05,
                         y_frames + frame_h / 2),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="black"))

    # ---------- ViT-B/16 visual encoder ----------
    enc_x, enc_y, enc_w, enc_h = 6.1, 3.7, 1.7, 2.4
    ax.add_patch(FancyBboxPatch((enc_x, enc_y), enc_w, enc_h,
                                boxstyle="round,pad=0.08",
                                fc=COLORS["oracle"], alpha=0.85,
                                ec="black", lw=1.0))
    ax.text(enc_x + enc_w / 2, enc_y + enc_h / 2 + 0.45,
            "ViT-B/16", ha="center", fontsize=13, fontweight="bold",
            color="white")
    ax.text(enc_x + enc_w / 2, enc_y + enc_h / 2,
            "frame encoder", ha="center", fontsize=10, color="white")
    ax.text(enc_x + enc_w / 2, enc_y + enc_h / 2 - 0.45,
            "(per-frame [CLS])", ha="center", fontsize=9,
            color="white", style="italic")

    # arrow from encoder to HTA
    ax.annotate("", xy=(8.5, y_frames + frame_h / 2),
                xytext=(enc_x + enc_w + 0.05, y_frames + frame_h / 2),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="black"))
    ax.text((enc_x + enc_w + 8.5) / 2, y_frames + frame_h / 2 + 0.35,
            "$8 \\times 768$\nfeatures",
            ha="center", fontsize=9, color="darkblue")

    # ---------- HTA temporal head ----------
    hta_x, hta_y, hta_w, hta_h = 8.6, 2.7, 2.5, 4.4
    ax.add_patch(FancyBboxPatch((hta_x, hta_y), hta_w, hta_h,
                                boxstyle="round,pad=0.08",
                                fc=COLORS["decoupled"], alpha=0.9,
                                ec="black", lw=1.0))
    ax.text(hta_x + hta_w / 2, hta_y + hta_h - 0.4,
            "HTA blocks", ha="center", fontsize=13, fontweight="bold",
            color="white")
    ax.text(hta_x + hta_w / 2, hta_y + hta_h - 0.85,
            "(6 stacked,\nlocal + global)", ha="center", fontsize=9,
            color="white")

    # input tokens to HTA — 8 frame tokens + 1 placeholder workflow token
    tok_y = hta_y + hta_h / 2 - 0.3
    tok_w = 0.18
    for i in range(8):
        ax.add_patch(Rectangle(
            (hta_x + 0.20 + i * (tok_w + 0.04), tok_y),
            tok_w, 0.32,
            fc="#9CA3AF", ec="black", lw=0.4))
    # The placeholder workflow token (shown dashed, indicating arbitrary)
    placeholder_x = hta_x + 0.20 + 8 * (tok_w + 0.04)
    ax.add_patch(Rectangle(
        (placeholder_x, tok_y),
        tok_w + 0.04, 0.32,
        fc="white", ec="darkred", lw=1.4, linestyle=":"))
    ax.text(placeholder_x + (tok_w + 0.04) / 2, tok_y + 0.16,
            "?", ha="center", va="center", fontsize=11,
            color="darkred", fontweight="bold")

    # callout for placeholder
    ax.annotate(
        "Placeholder cluster ID\n(any value — e.g., $z=0$)\nphase head does not depend on this",
        xy=(placeholder_x + (tok_w + 0.04) / 2, tok_y - 0.05),
        xytext=(hta_x + hta_w / 2, hta_y - 1.2),
        ha="center", fontsize=10, color="darkred",
        bbox=dict(boxstyle="round,pad=0.4", fc="#FEE2E2",
                  ec="darkred", lw=1.0),
        arrowprops=dict(arrowstyle="->", color="darkred", lw=1.0))

    # arrow from HTA to phase head
    ax.annotate("", xy=(11.6, y_frames + frame_h / 2),
                xytext=(hta_x + hta_w + 0.05, y_frames + frame_h / 2),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="black"))

    # ---------- Phase head (decoupled) ----------
    ph_x, ph_y, ph_w, ph_h = 11.7, 4.0, 1.8, 1.8
    ax.add_patch(FancyBboxPatch((ph_x, ph_y), ph_w, ph_h,
                                boxstyle="round,pad=0.08",
                                fc=COLORS["ensemble"], alpha=0.9,
                                ec="black", lw=1.0))
    ax.text(ph_x + ph_w / 2, ph_y + ph_h / 2 + 0.30,
            "Phase head", ha="center", fontsize=12, fontweight="bold",
            color="white")
    ax.text(ph_x + ph_w / 2, ph_y + ph_h / 2 - 0.10,
            "(decoupled)", ha="center", fontsize=10,
            color="white", style="italic")
    ax.text(ph_x + ph_w / 2, ph_y + ph_h / 2 - 0.45,
            "$P$-class", ha="center", fontsize=9, color="white")

    # arrow to predicted phases
    ax.annotate("", xy=(14.3, y_frames + frame_h / 2),
                xytext=(ph_x + ph_w + 0.05, y_frames + frame_h / 2),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="black"))

    # ---------- Predicted phases (right) ----------
    pred_x = 14.0
    pred_y = y_frames - 0.05
    for i, (p, c) in enumerate([("$\\hat{p}_1$", "#3B82F6"),
                                  ("$\\hat{p}_2$", "#3B82F6"),
                                  ("$\\hat{p}_3$", "#10B981"),
                                  ("...", "white"),
                                  ("$\\hat{p}_t$", "#F59E0B")]):
        if p == "...":
            ax.text(pred_x + 0.5, pred_y + 0.4 + i * 0.42, "...",
                    ha="center", fontsize=12)
        else:
            ax.add_patch(Rectangle(
                (pred_x, pred_y + i * 0.42), 1.0, 0.34,
                fc=c, ec="black", lw=0.6))
            ax.text(pred_x + 0.5, pred_y + i * 0.42 + 0.17,
                    p, ha="center", va="center", fontsize=10,
                    color="white", fontweight="bold")

    ax.text(pred_x + 0.5, pred_y + 5 * 0.42 + 0.4,
            "Predicted phases\n$\\hat{\\phi}(x_{1:t})$",
            ha="center", fontsize=11, fontweight="bold")

    # ---------- bottom-left: highlight that this is Step 1 ----------
    ax.text(0.3, -0.7,
            "Step 1 of causal-at-inference recovery (§4.5):\n"
            "• Prefix frames go through the visual + temporal stack\n"
            "• A placeholder cluster ID fills the workflow-token slot\n"
            "• The decoupled phase head produces $\\hat{\\phi}(x_{1:t})$ — kept for Step 2\n"
            "• RSD output at this stage is discarded; we only need the phases",
            ha="left", va="top", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.4", fc="#FEF3C7",
                      ec="#92400E", lw=1.0))

    # ---------- title ----------
    ax.set_title(
        "Causal-at-inference Step 1: forward-pass prefix → predicted phases\n"
        "(placeholder cluster has no effect on phase output, by decoupled-phase-head design)",
        fontsize=14, fontweight="bold", pad=15)

    save(fig, "fig_causal_step1")


# =====================================================================
# 15. ViT [CLS] mechanism — explanatory schematic
# =====================================================================
def fig_vit_cls_mechanism():
    """How the ViT [CLS] token aggregates patch information via
    self-attention to produce a per-frame summary vector."""
    from matplotlib.patches import (FancyBboxPatch, Rectangle,
                                      FancyArrowPatch, Circle)

    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.4)

    # ====== TOP ROW: pipeline overview ======
    ax = fig.add_subplot(gs[0, 0])
    ax.set_xlim(0, 18)
    ax.set_ylim(-1.0, 7.5)
    ax.axis("off")

    # 1. Input image
    img_x, img_y, img_w, img_h = 0.3, 1.5, 2.4, 2.4
    ax.add_patch(Rectangle((img_x, img_y), img_w, img_h,
                            fc="#D1D5DB", ec="black", lw=0.8))
    # Sketch some content lines
    for k in range(5):
        ax.plot([img_x + 0.3, img_x + img_w - 0.3],
                [img_y + 0.4 + k*0.4, img_y + 0.4 + k*0.4],
                color="#6B7280", lw=0.5)
    ax.text(img_x + img_w/2, img_y + img_h + 0.35,
            "Input frame\n($224 \\times 224$)", ha="center",
            fontsize=11, fontweight="bold")

    # arrow
    ax.annotate("", xy=(3.4, img_y + img_h/2),
                xytext=(img_x + img_w + 0.05, img_y + img_h/2),
                arrowprops=dict(arrowstyle="->", lw=1.6))
    ax.text(3.05, img_y + img_h/2 + 0.4, "split into\n16×16 patches",
            ha="center", fontsize=9, style="italic")

    # 2. Patch grid (4x4 simplified)
    grid_x, grid_y = 3.5, 1.5
    cell = 0.55
    for i in range(4):
        for j in range(4):
            shade = 0.5 + 0.05*(i+j)
            ax.add_patch(Rectangle(
                (grid_x + j*cell, grid_y + i*cell), cell*0.95, cell*0.95,
                fc=plt.cm.Greys(shade), ec="black", lw=0.5))
    ax.text(grid_x + 2*cell, grid_y + 4*cell + 0.35,
            "16 patches shown\n(actual: 196 = 14×14)",
            ha="center", fontsize=11, fontweight="bold")

    # arrow + label "linear projection + add CLS"
    ax.annotate("", xy=(7.0, img_y + img_h/2),
                xytext=(grid_x + 4*cell + 0.05, img_y + img_h/2),
                arrowprops=dict(arrowstyle="->", lw=1.6))
    ax.text(6.8, img_y + img_h/2 + 0.6,
            "linear project\n→ 768-d each\n+ prepend [CLS]",
            ha="center", fontsize=9, style="italic")

    # 3. Token sequence with CLS highlighted
    tok_x = 7.1
    tok_y = 2.4
    tok_w = 0.45
    tok_h = 0.6
    # CLS token
    ax.add_patch(Rectangle((tok_x, tok_y), tok_w, tok_h,
                            fc=COLORS["decoupled"], ec="black", lw=1.0))
    ax.text(tok_x + tok_w/2, tok_y + tok_h/2, "CLS",
            ha="center", va="center", fontsize=9,
            color="white", fontweight="bold")
    ax.text(tok_x + tok_w/2, tok_y - 0.30, "0",
            ha="center", fontsize=8, color="darkblue")
    # Patch tokens (16 simplified)
    for i in range(16):
        x = tok_x + tok_w + 0.06 + i*(tok_w + 0.02)
        ax.add_patch(Rectangle((x, tok_y), tok_w, tok_h,
                                fc="#9CA3AF", ec="black", lw=0.4))
        ax.text(x + tok_w/2, tok_y + tok_h/2, f"$p_{{{i+1}}}$",
                ha="center", va="center", fontsize=7)
        if i in [0, 15]:
            ax.text(x + tok_w/2, tok_y - 0.30, str(i+1),
                    ha="center", fontsize=8)
        elif i == 7:
            ax.text(x + tok_w/2, tok_y - 0.30, "...",
                    ha="center", fontsize=10)
    ax.text(tok_x + 8.5*tok_w, tok_y + tok_h + 0.45,
            "197 tokens — each $\\in \\mathbb{R}^{768}$",
            ha="center", fontsize=11, fontweight="bold")
    ax.text(tok_x + tok_w/2, tok_y + tok_h + 1.15,
            "learned\nparameter", ha="center", fontsize=8,
            color=COLORS["decoupled"], fontweight="bold")
    # arrow
    ax.annotate("", xy=(tok_x + tok_w/2, tok_y + tok_h + 0.95),
                xytext=(tok_x + tok_w/2, tok_y + tok_h + 0.65),
                arrowprops=dict(arrowstyle="->", color=COLORS["decoupled"],
                                lw=1.0))

    # arrow to transformer stack
    ax.annotate("", xy=(17.0, img_y + img_h/2),
                xytext=(tok_x + 17*(tok_w + 0.02) + 0.25, img_y + img_h/2),
                arrowprops=dict(arrowstyle="->", lw=1.6))

    # 4. Transformer block stack
    stk_x = 16.4
    stk_w = 1.4
    block_h = 0.45
    for i in range(6):  # show 6 of 12 stacked blocks
        y_block = 1.0 + i * (block_h + 0.05)
        c = COLORS["oracle"] if i % 2 == 0 else COLORS["decoupled"]
        ax.add_patch(FancyBboxPatch((stk_x, y_block), stk_w, block_h,
                                     boxstyle="round,pad=0.02",
                                     fc=c, alpha=0.8, ec="black", lw=0.5))
        if i == 5:
            ax.text(stk_x + stk_w/2, y_block + block_h/2,
                    "Block 12", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
        elif i == 0:
            ax.text(stk_x + stk_w/2, y_block + block_h/2,
                    "Block 1", ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
        elif i == 2:
            ax.text(stk_x + stk_w/2, y_block + block_h/2,
                    "...", ha="center", va="center",
                    fontsize=11, color="white")
    ax.text(stk_x + stk_w/2, 1.0 + 6*(block_h + 0.05) + 0.2,
            "12 transformer blocks\n(self-attention + MLP each)",
            ha="center", fontsize=9, fontweight="bold")

    ax.set_title(
        "ViT-B/16 forward pass: image $\\to$ patches $\\to$ CLS-augmented tokens $\\to$ 12 blocks",
        fontsize=13, fontweight="bold", pad=8)

    # ====== BOTTOM ROW: how CLS gathers info via attention ======
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.set_xlim(0, 18)
    ax2.set_ylim(-1.5, 5.0)
    ax2.axis("off")

    # Show one transformer block with attention edges from CLS to all tokens
    n_show = 9  # CLS + 8 patches for clarity
    box_y = 2.5
    box_h = 1.0
    box_w = 0.65
    box_gap = 0.15
    box_x0 = 1.2

    # Input row (entering attention)
    in_y = box_y - 0.15
    for i in range(n_show):
        x = box_x0 + i * (box_w + box_gap)
        c = COLORS["decoupled"] if i == 0 else "#9CA3AF"
        label = "CLS" if i == 0 else (f"$p_{{{i}}}$" if i < 8 else "...")
        ax2.add_patch(Rectangle((x, in_y), box_w, box_h,
                                 fc=c, ec="black", lw=0.6))
        ax2.text(x + box_w/2, in_y + box_h/2, label,
                 ha="center", va="center", fontsize=10,
                 color="white" if i == 0 else "black",
                 fontweight="bold")
    ax2.text(box_x0 + n_show*(box_w + box_gap)/2 - 0.4, in_y + box_h + 0.2,
             "INPUT to attention layer (197 token vectors, $\\mathbb{R}^{768}$ each)",
             ha="center", fontsize=10)

    # Self-attention diagram: CLS attends to all
    arrows_y_top = in_y - 0.4
    cls_x_center = box_x0 + box_w/2
    for i in range(1, n_show):
        x_target = box_x0 + i*(box_w + box_gap) + box_w/2
        weight = [0.3, 0.6, 0.85, 0.4, 0.7, 0.5, 0.2, 0.4][i-1]
        ax2.annotate("", xy=(cls_x_center, arrows_y_top - 0.5),
                     xytext=(x_target, in_y - 0.05),
                     arrowprops=dict(arrowstyle="-|>", color=plt.cm.Reds(weight),
                                     lw=0.5 + 2.0*weight, alpha=0.7))

    ax2.text(cls_x_center, arrows_y_top - 0.85,
             "$\\alpha_{0,j}$  =  attention weights\n"
             "(learned during training)",
             ha="center", fontsize=9, color="darkred", style="italic")

    # The aggregation formula in the middle
    formula_x = 9.0
    formula_y = 1.5
    ax2.add_patch(FancyBboxPatch((formula_x - 0.3, formula_y - 0.2),
                                  4.5, 1.5,
                                  boxstyle="round,pad=0.1",
                                  fc="#FEF3C7", ec="#92400E", lw=1.2))
    ax2.text(formula_x + 1.95, formula_y + 1.0,
             "Self-attention output at position 0:",
             ha="center", fontsize=10, fontweight="bold")
    ax2.text(formula_x + 1.95, formula_y + 0.4,
             "$\\text{out}_{[CLS]} = \\sum_{j=0}^{196}\\, \\alpha_{0,j}\\, V_j$",
             ha="center", fontsize=14)
    ax2.text(formula_x + 1.95, formula_y - 0.05,
             "(weighted sum of patch values)",
             ha="center", fontsize=9, style="italic", color="#92400E")

    # Output box: CLS now contains aggregated patch info
    out_x = 14.0
    out_y = 1.7
    out_w = 1.5
    out_h = 1.5
    ax2.add_patch(FancyBboxPatch((out_x, out_y), out_w, out_h,
                                  boxstyle="round,pad=0.05",
                                  fc=COLORS["ensemble"], ec="black", lw=1.2))
    ax2.text(out_x + out_w/2, out_y + out_h/2 + 0.3,
             "CLS output", ha="center", fontsize=12,
             color="white", fontweight="bold")
    ax2.text(out_x + out_w/2, out_y + out_h/2 - 0.05,
             "$\\in \\mathbb{R}^{768}$",
             ha="center", fontsize=11, color="white")
    ax2.text(out_x + out_w/2, out_y + out_h/2 - 0.4,
             "now mixes\nall patches",
             ha="center", fontsize=8, color="white", style="italic")
    ax2.text(out_x + out_w/2, out_y + out_h + 0.3,
             "After 12 blocks:\nper-frame feature",
             ha="center", fontsize=10, fontweight="bold")

    # arrow from formula to output
    ax2.annotate("", xy=(out_x - 0.05, out_y + out_h/2),
                 xytext=(formula_x + 4.3, formula_y + 0.5),
                 arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))
    ax2.text((formula_x + 4.3 + out_x)/2, out_y + out_h/2 + 0.25,
             "× 12 blocks",
             ha="center", fontsize=9, style="italic")

    ax2.set_title(
        "Inside one block: CLS is a weighted sum of all 197 patch values",
        fontsize=13, fontweight="bold", pad=8)

    # bottom callout — three key takeaways
    ax2.text(0.2, -0.9,
             "Why this works:\n"
             "• [CLS] starts as a \\textbf{learned parameter}, not from the image — a 'blank slate' container\n"
             "• Self-attention lets it weight-and-sum information from \\textbf{all 196 patches} in O(1) layers\n"
             "• Pretraining forces [CLS] to encode whatever is needed for image classification — generalizable per-frame summary",
             ha="left", va="top", fontsize=9.5,
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", lw=0.8))

    save(fig, "fig_vit_cls_mechanism")


# =====================================================================
# 16. Offline workflow-clustering pipeline (§4.3)
#     phase sequence → bigrams → TF-IDF → PCA → k-means → cluster z
# =====================================================================
def fig_workflow_cluster_pipeline():
    """Six-stage left-to-right schematic of the offline workflow-clustering
    pipeline: how a surgery's phase sequence becomes a single cluster ID."""
    from matplotlib.patches import (FancyBboxPatch, Rectangle, Circle,
                                      FancyArrowPatch, Ellipse)

    fig, ax = plt.subplots(figsize=(16, 5.0))
    ax.set_xlim(0, 18)
    ax.set_ylim(-0.5, 5.5)
    ax.axis("off")

    # ---------- outer container ----------
    ax.add_patch(FancyBboxPatch((0.2, 0.2), 17.6, 4.8,
                                 boxstyle="round,pad=0.05",
                                 fc="#F0FDFA", ec="#0F766E", lw=1.5))
    ax.text(9, 4.85, "Build workflow clusters (offline)",
            ha="center", fontsize=15, fontweight="bold", color="#0F766E")

    # ---------- 1. Phase sequence ----------
    x0 = 1.4; y_seq = 2.2
    phase_colors = ["#10B981", "#F59E0B", "#A78BFA", "#EF4444", "#3B82F6"]
    for i, c in enumerate(phase_colors):
        ax.add_patch(Circle((x0 + i*0.35, y_seq), 0.18,
                             fc=c, ec="black", lw=0.6, zorder=3))
        if i < len(phase_colors) - 1:
            ax.plot([x0 + i*0.35 + 0.15, x0 + (i+1)*0.35 - 0.15],
                    [y_seq, y_seq],
                    color="black", lw=0.6, zorder=2)
    ax.text(x0 + 5*0.35 + 0.08, y_seq, "...", fontsize=14, va="center")
    ax.text(x0 + 0.7, 3.65, "Phase\nsequence",
            ha="center", fontsize=11, fontweight="bold")

    # arrow
    ax.annotate("", xy=(3.5, y_seq), xytext=(x0 + 1.95, y_seq),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="black"))

    # ---------- 2. Phase-transition bigrams ----------
    bx = 3.6; by = 2.2
    ax.text(bx + 0.6, by + 0.45, "(A,B)  (B,C)", ha="center", fontsize=10,
            family="monospace")
    ax.text(bx + 0.6, by + 0.05, "(C,D)  (D,E)", ha="center", fontsize=10,
            family="monospace")
    ax.text(bx + 0.6, by - 0.4, "...", ha="center", fontsize=14)
    ax.text(bx + 0.6, 3.65, "Phase-transition\nbigrams",
            ha="center", fontsize=11, fontweight="bold")

    # arrow + (small "document" icon)
    ax.annotate("", xy=(5.7, y_seq), xytext=(bx + 1.25, y_seq),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="black"))
    # document/page icon under the arrow
    ax.add_patch(Rectangle((5.0, by - 0.15), 0.6, 0.7,
                            fc="white", ec="black", lw=0.7))
    for k in range(4):
        ax.plot([5.05, 5.55], [by - 0.05 + k*0.15, by - 0.05 + k*0.15],
                color="#9CA3AF", lw=0.4)
    # arrow up from doc to corpus label
    ax.annotate("", xy=(5.3, 4.4), xytext=(5.3, by + 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#0F766E",
                                ls="--"))
    ax.text(5.3, 4.25, "all videos\n(corpus)", ha="center", fontsize=8,
            color="#0F766E", style="italic")

    # ---------- 3. TF-IDF heatmap ----------
    tx = 5.9; ty = 1.4
    n_rows, n_cols = 6, 6
    cell_w, cell_h = 0.18, 0.18
    np.random.seed(7)
    heat = np.random.rand(n_rows, n_cols) ** 1.4
    for r in range(n_rows):
        for c in range(n_cols):
            ax.add_patch(Rectangle(
                (tx + c*cell_w, ty + r*cell_h),
                cell_w*0.95, cell_h*0.95,
                fc=plt.cm.Blues(0.2 + 0.7 * heat[r, c]),
                ec="#1E40AF", lw=0.3))
    ax.text(tx + (n_cols*cell_w)/2, 3.65, "TF-IDF\nacross corpus",
            ha="center", fontsize=11, fontweight="bold")

    # arrow
    ax.annotate("", xy=(8.6, y_seq), xytext=(tx + n_cols*cell_w + 0.05, y_seq),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="black"))

    # ---------- 4. PCA scatter ----------
    px, py = 8.7, 1.4
    pw, ph = 1.6, 1.6
    # axes
    ax.plot([px, px + pw], [py, py], color="black", lw=0.7)
    ax.plot([px, px], [py, py + ph], color="black", lw=0.7)
    # scatter
    np.random.seed(3)
    pts = np.random.randn(20, 2) * 0.35 + np.array([0.8, 0.8])
    pts = np.clip(pts, 0.1, 1.5)
    for p in pts:
        ax.scatter(px + p[0], py + p[1], s=24, c="#1E40AF",
                   edgecolor="white", lw=0.4, zorder=3)
    ax.text(px + pw/2, 3.65, "PCA",
            ha="center", fontsize=11, fontweight="bold")

    # arrow
    ax.annotate("", xy=(11.0, y_seq), xytext=(px + pw + 0.05, y_seq),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="black"))

    # ---------- 5. k-means ----------
    kx, ky = 11.1, 1.4
    kw, kh = 1.7, 1.6
    ax.plot([kx, kx + kw], [ky, ky], color="black", lw=0.7)
    ax.plot([kx, kx], [ky, ky + kh], color="black", lw=0.7)
    # three clusters of points + dashed-ellipse boundaries
    cluster_centers = [(0.55, 1.25), (0.50, 0.55), (1.25, 0.85)]
    cluster_colors = ["#10B981", "#F59E0B", "#A78BFA"]
    for (ccx, ccy), col in zip(cluster_centers, cluster_colors):
        # ellipse boundary
        ax.add_patch(Ellipse((kx + ccx, ky + ccy), 0.65, 0.55,
                              fc="none", ec=col, lw=1.2, ls=(0, (4, 2))))
        # cluster points
        np.random.seed(int(ccx * 13 + ccy * 7))
        for _ in range(5):
            jitter = np.random.randn(2) * 0.10
            ax.scatter(kx + ccx + jitter[0], ky + ccy + jitter[1],
                       s=24, c=col, edgecolor="white", lw=0.4, zorder=3)
    ax.text(kx + kw/2, 3.65, "k-means\n($K$ clusters)",
            ha="center", fontsize=11, fontweight="bold")

    # arrow
    ax.annotate("", xy=(13.6, y_seq), xytext=(kx + kw + 0.05, y_seq),
                arrowprops=dict(arrowstyle="->", lw=1.4, color="black"))

    # ---------- 6. Workflow cluster z ----------
    zx, zy = 14.0, y_seq
    ax.add_patch(Circle((zx, zy), 0.55,
                         fc="#A78BFA", ec="black", lw=1.0, zorder=3))
    ax.text(zx, zy, "$z$", ha="center", va="center",
            fontsize=20, color="white", fontweight="bold")
    ax.text(zx, 3.65, "Workflow\ncluster",
            ha="center", fontsize=11, fontweight="bold")

    # ---------- output arrow leaving the box (downward, indicating it feeds the model) ----------
    ax.annotate("", xy=(zx, -0.35), xytext=(zx, zy - 0.65),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#7C3AED"))
    ax.text(zx + 0.95, 0.4, "→ to model\n(workflow token $\\mathbf{e}_z$)",
            ha="left", fontsize=10, color="#7C3AED", style="italic")

    # ---------- input arrow entering at the top ----------
    ax.annotate("", xy=(x0 + 0.7, 4.05), xytext=(x0 + 0.7, 5.4),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#0F766E"))
    ax.text(x0 + 0.7, 5.45, "from training corpus",
            ha="center", fontsize=9, color="#0F766E", style="italic")

    # ---------- bottom annotations: K values ----------
    ax.text(9, -0.25,
            "On MultiBypass140: $K=6$  •  On Cholec80: $K=4$  •  Computed once offline; reused at training and inference",
            ha="center", fontsize=10, color="#374151", style="italic")

    save(fig, "fig_workflow_cluster_pipeline")


# =====================================================================
def main():
    print(f"Output dir: {OUTDIR}")
    fig_main_mb140_within()
    fig_main_mb140_cross_center()
    fig_phase_e_5fold()
    fig_longer_context()
    fig_cholec80_strict_vs_legacy()
    fig_variability_scaling()
    fig_cluster_sizes()
    fig_protocol_compare_summary()
    fig_summary_at_a_glance()
    fig_literature_comparison()
    fig_parameter_breakdown()
    fig_cholec80_inference_ablation()
    fig_attention_compare()
    fig_causal_step1()
    fig_vit_cls_mechanism()
    fig_workflow_cluster_pipeline()
    print(f"\nAll figures written to {OUTDIR}/")


if __name__ == "__main__":
    main()

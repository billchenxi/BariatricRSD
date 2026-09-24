"""Alternative main-text result figure: horizontal-bar variant.

Same locked numbers as fig2_result_multipanel but rendered as horizontal
bars with delta annotations, an explicit baseline reference line on each
MB140 panel, and a paired before/after layout for Cholec80.

Numbers verified against:
  - body_main_short.tex (Run 033, 034, 017/016/024, 046/046b, 037)
  - paper/phase_e_summary.json (regenerated 2026-05-03 from log-best values)
  - paper/results_manifest.csv

Output:
  paper/figures/fig2_result_summary_bars.{png,pdf}
  paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig2_result_summary_bars.{png,pdf}
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SUB = ROOT / "paper" / "Formatting_Instructions_For_NeurIPS_2026" / "figures"


COLORS = {
    "none": "#94a3b8",
    "oracle": "#1d4ed8",
    "decoupled": "#0d9488",
    "prefix": "#ea580c",
    "shuffle": "#7c3aed",
}


plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 7.8,
    "axes.labelsize": 8.0,
    "axes.titlesize": 8.6,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.8,
    "legend.fontsize": 7.4,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def hbar_panel(ax, labels, means, stds, colors, baseline_idx, title, xlim, xlabel=None):
    """Horizontal-bar panel with mean±std and a dashed baseline at the no-token row.

    Value labels are placed to the right of the error-bar tip; xlim is extended
    rightward to give them room. The dashed reference line marks the no-token mean.
    """
    y = np.arange(len(labels))
    baseline = means[baseline_idx]

    # Reserve right-side space for the annotation column.
    span = xlim[1] - xlim[0]
    label_x = xlim[1] + 0.01 * span
    ext_xlim = (xlim[0], xlim[1] + 0.78 * span)

    ax.axvline(baseline, linestyle="--", color="#374151", linewidth=0.9, alpha=0.55, zorder=1)

    for i, (m, s, c) in enumerate(zip(means, stds, colors)):
        ax.barh(
            y[i], m - xlim[0], left=xlim[0], height=0.58, color=c, alpha=0.78,
            edgecolor="black", linewidth=0.4, zorder=2,
        )
        if s is not None:
            ax.errorbar(
                m, y[i], xerr=s, fmt="none",
                ecolor="#0f172a", elinewidth=0.9, capsize=2.5, zorder=3,
            )
        delta = m - baseline
        if i == baseline_idx:
            label = f"{m:.2f} ± {s:.2f}" if s is not None else f"{m:.2f}"
        else:
            sign = "+" if delta >= 0 else ""
            label = f"{m:.2f} ± {s:.2f}  ({sign}{delta:.2f})" if s is not None else f"{m:.2f}  ({sign}{delta:.2f})"
        ax.text(
            label_x, y[i], label,
            va="center", ha="left", fontsize=7.2, color="#0f172a", zorder=4,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(*ext_xlim)
    # Only show ticks within the data range, not the annotation column.
    tick_step = 0.5 if span <= 2.5 else 1.0
    first_tick = np.ceil(xlim[0] / tick_step) * tick_step
    last_tick = np.floor(xlim[1] / tick_step) * tick_step
    ax.set_xticks(np.arange(first_tick, last_tick + 1e-9, tick_step))
    ax.set_title(title, loc="left", pad=4, fontweight="bold")
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.7, zorder=0)
    if xlabel:
        ax.set_xlabel(xlabel)


def cholec_paired_panel(ax):
    """Cholec80: centered (with stds) vs strict (single seed) for three conditions."""
    conds = ["oracle", "no token", "teacher-forced prefix"]
    colors = [COLORS["oracle"], COLORS["none"], COLORS["prefix"]]
    centered = [4.49, 4.61, 5.03]
    centered_err = [0.14, 0.19, 0.07]
    strict = [4.33, 4.34, 4.26]

    x_centered = 0.0
    x_strict = 1.0
    offsets = [-0.18, 0.0, 0.18]

    for off, lab, color, c, ce, s in zip(offsets, conds, colors, centered, centered_err, strict):
        ax.errorbar(
            x_centered + off, c, yerr=ce, fmt="o", ms=5.5, capsize=3, color=color,
            markeredgecolor="black", markeredgewidth=0.4, elinewidth=1.0, zorder=3, label=lab,
        )
        ax.scatter(
            x_strict + off, s, s=42, color=color, edgecolor="black", linewidth=0.4,
            zorder=3, marker="s",
        )
        ax.plot([x_centered + off, x_strict + off], [c, s], color=color, alpha=0.30, linewidth=1, zorder=2)
        ax.text(x_centered + off, c + ce + 0.04, f"{c:.2f}", ha="center", va="bottom", fontsize=6.7, color="#0f172a")
        ax.text(x_strict + off, s + 0.06, f"{s:.2f}", ha="center", va="bottom", fontsize=6.7, color="#0f172a")

    ax.set_xticks([x_centered, x_strict])
    ax.set_xticklabels(["centered-window\n(3 seeds)", "strict prefix-only\n(1 seed)"])
    ax.set_xlim(-0.45, 1.45)
    ax.set_ylim(3.85, 5.4)
    ax.set_ylabel("MAE (min)")
    ax.set_title("C. Cholec80: protocol effect", loc="left", pad=4, fontweight="bold")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.7, zorder=0)
    ax.legend(loc="center right", frameon=False, ncol=1, handletextpad=0.4, borderaxespad=0.0,
              bbox_to_anchor=(1.02, 0.78), fontsize=7.0)
    ax.text(
        0.5, -0.46,
        "centered-window:  +0.42 prefix vs no-token (leakage artifact)\n"
        "strict prefix-only:  range = 0.08 min  →  null effect",
        transform=ax.transAxes, ha="center", va="top", fontsize=6.9, color="#0f172a",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=0.7),
    )


def main():
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.0))
    fig.subplots_adjust(wspace=0.55, hspace=0.65, bottom=0.11, top=0.94, left=0.10, right=0.98)

    # A. Within-center MB140 strict
    hbar_panel(
        axes[0, 0],
        labels=["no token", "oracle", "decoupled"],
        means=[13.03, 12.26, 12.18],
        stds=[0.18, 0.09, 0.14],
        colors=[COLORS["none"], COLORS["oracle"], COLORS["decoupled"]],
        baseline_idx=0,
        title="A. MB140 within-center (strict)",
        xlim=(11.7, 13.45),
        xlabel="MAE (min, lower is better)",
    )

    # B. Cross-center MB140 strict
    hbar_panel(
        axes[0, 1],
        labels=["no token", "oracle", "decoupled"],
        means=[17.80, 17.71, 17.33],
        stds=[0.55, 0.23, 0.15],
        colors=[COLORS["none"], COLORS["oracle"], COLORS["decoupled"]],
        baseline_idx=0,
        title="B. MB140 Bern → Strasbourg (strict)",
        xlim=(16.55, 18.85),
        xlabel="MAE (min, lower is better)",
    )

    # C. Cholec80 paired centered-vs-strict
    cholec_paired_panel(axes[1, 0])

    # D. Shuffled-token control (MB140 strict)
    hbar_panel(
        axes[1, 1],
        labels=["no token", "shuffled token", "real (decoupled)"],
        means=[13.03, 13.14, 12.18],
        stds=[0.18, 0.15, 0.14],
        colors=[COLORS["none"], COLORS["shuffle"], COLORS["decoupled"]],
        baseline_idx=0,
        title="D. Shuffled-token semantic control",
        xlim=(11.7, 13.55),
        xlabel="MAE (min, lower is better)",
    )

    fig.text(
        0.5, 0.005,
        "Bars: mean over 3 seeds with std (error bars). Dashed line on each MB140 panel marks the no-token "
        "baseline. Cholec80 strict uses 1 seed. Numbers reflect log-best validation MAE; std for "
        "decoupled is 0.14 (sample std over seeds [12.32, 12.19, 12.04]).",
        ha="center", fontsize=6.7, color="#374151",
    )

    SUB.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        out = HERE / f"fig2_result_summary_bars.{ext}"
        fig.savefig(out)
        shutil.copy2(out, SUB / out.name)
        print(f"wrote {out} and {SUB / out.name}")


if __name__ == "__main__":
    main()

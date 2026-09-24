"""Build a compact main-text multi-panel result figure.

Output:
  paper/figures/fig2_result_multipanel.{png,pdf}
  paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig2_result_multipanel.{png,pdf}

The values are the locked manuscript numbers from body_main_short.tex and
paper/results_manifest.csv. The figure is intentionally compact so it can
replace the single Cholec80-only main-text figure.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SUB = ROOT / "paper" / "Formatting_Instructions_For_NeurIPS_2026" / "figures"


COLORS = {
    "none": "#6b7280",
    "oracle": "#2563eb",
    "decoupled": "#0f766e",
    "prefix": "#d97706",
    "shuffle": "#7c3aed",
}


plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 7.8,
    "axes.labelsize": 8.0,
    "axes.titlesize": 8.4,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def point_panel(
    ax,
    labels,
    means,
    stds,
    colors,
    ylim,
    title,
    delta_text=None,
    ylabel=False,
    delta_pos=(0.98, 0.92),
    delta_ha="right",
    delta_va="top",
):
    x = np.arange(len(labels))
    for i, (m, s, c) in enumerate(zip(means, stds, colors)):
        if s is None:
            ax.scatter(i, m, s=42, color=c, edgecolor="black", linewidth=0.4, zorder=3)
        else:
            ax.errorbar(
                i, m, yerr=s, fmt="o", ms=5.5, capsize=3,
                color=c, markeredgecolor="black", markeredgewidth=0.4,
                elinewidth=1.0, zorder=3,
            )
        text = f"{m:.2f}" if s is None else f"{m:.2f}\n±{s:.2f}"
        ax.text(i, m + (ylim[1] - ylim[0]) * 0.055, text, ha="center", va="bottom", fontsize=7.2)

    ax.plot(x, means, color="#cbd5e1", linewidth=1.0, zorder=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(*ylim)
    ax.set_title(title, loc="left", pad=5, fontweight="bold")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    if ylabel:
        ax.set_ylabel("MAE (min, lower is better)")
    else:
        ax.set_ylabel("")
    if delta_text:
        ax.text(
            delta_pos[0], delta_pos[1], delta_text,
            transform=ax.transAxes,
            ha=delta_ha,
            va=delta_va,
            fontsize=7.5,
            color="#064e3b",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#ecfdf5", edgecolor="#99f6e4", linewidth=0.8),
        )


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.55))
    fig.subplots_adjust(wspace=0.26, hspace=0.58, bottom=0.14)

    # A. Main strict within-center MB140 result.
    ax = axes[0, 0]
    point_panel(
        ax,
        ["no token", "oracle", "decoupled"],
        [13.03, 12.26, 12.18],
        [0.18, 0.09, 0.14],
        [COLORS["none"], COLORS["oracle"], COLORS["decoupled"]],
        (11.95, 13.55),
        "A. MB140 within-center (strict)",
        "decoupled gain: -0.85 min",
        ylabel=True,
    )

    # B. Cross-center MB140 result.
    ax = axes[0, 1]
    point_panel(
        ax,
        ["no token", "oracle", "decoupled"],
        [17.80, 17.71, 17.33],
        [0.55, 0.23, 0.15],
        [COLORS["none"], COLORS["oracle"], COLORS["decoupled"]],
        (16.95, 18.85),
        "B. MB140 Bern -> Strasbourg (strict)",
        "decoupled gain: -0.47 min",
    )

    # C. Cholec80 contrast: centered-window negative vs strict null.
    ax = axes[1, 0]
    xs = np.array([0, 1])
    offsets = [-0.18, 0.0, 0.18]
    labels = ["oracle", "no token", "prefix"]
    colors = [COLORS["oracle"], COLORS["none"], COLORS["prefix"]]
    centered = [4.49, 4.61, 5.03]
    centered_err = [0.14, 0.19, 0.07]
    strict = [4.33, 4.34, 4.26]
    strict_label_offsets = [0.11, 0.06, -0.08]
    for idx, (off, lab, color, y0, e0, y1) in enumerate(zip(offsets, labels, colors, centered, centered_err, strict)):
        ax.errorbar(xs[0] + off, y0, yerr=e0, fmt="o", ms=5, capsize=3, color=color,
                    markeredgecolor="black", markeredgewidth=0.4, elinewidth=1.0, zorder=3)
        ax.scatter(xs[1] + off, y1, s=38, color=color, edgecolor="black", linewidth=0.4, zorder=3, label=lab)
        ax.plot([xs[0] + off, xs[1] + off], [y0, y1], color=color, alpha=0.35, linewidth=1)
        ax.text(
            xs[0] + off,
            y0 + e0 + 0.035,
            f"{y0:.2f}",
            ha="center",
            va="bottom",
            fontsize=6.6,
            zorder=4,
        )
        strict_y = y1 + strict_label_offsets[idx]
        ax.text(
            xs[1] + off,
            strict_y,
            f"{y1:.2f}",
            ha="center",
            va="bottom",
            fontsize=6.6,
            zorder=4,
        )
    ax.set_xticks(xs)
    ax.set_xticklabels(["centered-window\n3 seeds", "strict prefix-only\n1 seed"])
    ax.set_ylim(4.1, 5.2)
    ax.set_title("C. Cholec80 contrast", loc="left", pad=5, fontweight="bold")
    ax.set_ylabel("MAE (min, lower is better)")
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.legend(loc="upper right", frameon=False, ncol=1, bbox_to_anchor=(0.98, 0.99),
              handletextpad=0.3, borderaxespad=0.0)
    ax.text(0.02, 0.08, "strict: 0.08 min range", transform=ax.transAxes, ha="left", va="bottom",
            fontsize=7.5, color="#374151",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=0.8))

    # D. Shuffled-token control.
    ax = axes[1, 1]
    point_panel(
        ax,
        ["no token", "shuffled", "real token"],
        [13.03, 13.14, 12.18],
        [0.18, 0.15, 0.14],
        [COLORS["none"], COLORS["shuffle"], COLORS["decoupled"]],
        (11.95, 13.55),
        "D. Shuffled-token control (MB140 strict)",
        "shuffle does not reproduce gain",
        delta_pos=(0.50, 0.08),
        delta_ha="center",
        delta_va="bottom",
    )

    fig.text(
        0.5, 0.01,
        "Oracle and decoupled-oracle rows use retrospective cluster IDs; strict protocol removes future visual frames. "
        "Panel C strict Cholec80 uses one seed.",
        ha="center",
        fontsize=6.8,
        color="#374151",
    )

    for ext in ("png", "pdf"):
        out = HERE / f"fig2_result_multipanel.{ext}"
        fig.savefig(out)
        SUB.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, SUB / out.name)
        print(f"wrote {out} and {SUB / out.name}")


if __name__ == "__main__":
    main()

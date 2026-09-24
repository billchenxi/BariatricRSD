"""Build the main-text Figure 1 overview.

Output:
  paper/figures/fig1_paper_overview.{png,pdf}
  paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig1_paper_overview.{png,pdf}

The figure summarizes the full paper story: workflow variability, token
construction, protocol scope, and the observed result pattern.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
SUB = ROOT / "paper" / "Formatting_Instructions_For_NeurIPS_2026" / "figures"


COLORS = {
    "ink": "#111827",
    "muted": "#4b5563",
    "grid": "#e5e7eb",
    "blue": "#2563eb",
    "teal": "#0f766e",
    "orange": "#d97706",
    "purple": "#7c3aed",
    "slate": "#64748b",
    "red": "#dc2626",
    "green_bg": "#ecfdf5",
    "blue_bg": "#eff6ff",
    "orange_bg": "#fff7ed",
    "slate_bg": "#f8fafc",
}


plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 7.6,
    "axes.titlesize": 8.6,
    "axes.labelsize": 7.6,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def panel_title(ax, title: str) -> None:
    ax.set_title(title, loc="left", pad=4, fontweight="bold", color=COLORS["ink"])


def rounded_box(ax, xy, w, h, text, fc, ec, fontsize=7.0, weight="normal") -> None:
    patch = FancyBboxPatch(
        xy, w, h,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        facecolor=fc,
        edgecolor=ec,
        linewidth=0.9,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + w / 2,
        xy[1] + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=COLORS["ink"],
        fontweight=weight,
        linespacing=1.15,
    )


def arrow(ax, start, end, color="#64748b", lw=1.0) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, shrinkA=2, shrinkB=2),
    )


def draw_variability_panel(ax) -> None:
    panel_title(ax, "A. Workflow variation is the signal")
    labels = ["MB140", "Cholec80"]
    mb = np.array([0.21, 0.18, 0.17, 0.16, 0.15, 0.13])
    ch = np.array([0.71, 0.12, 0.10, 0.07])
    y = [1.0, 0.0]
    left = 0.0
    palette = ["#2563eb", "#0f766e", "#d97706", "#7c3aed", "#db2777", "#64748b"]
    for v, c in zip(mb, palette):
        ax.barh(y[0], v, left=left, height=0.28, color=c)
        left += v
    left = 0.0
    for v, c in zip(ch, palette[:4]):
        ax.barh(y[1], v, left=left, height=0.28, color=c)
        left += v
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.6, 1.45)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xticklabels(["0", "50%", "100%"])
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.7)
    ax.text(0.03, 1.28, "balanced clusters\nH(z)=2.48 bits", color=COLORS["muted"], fontsize=6.8)
    ax.text(0.54, 0.17, "71% in one cluster\nH(z)=1.27 bits", color=COLORS["muted"], fontsize=6.8)
    ax.set_xlabel("videos assigned to workflow clusters")


def draw_method_panel(ax) -> None:
    panel_title(ax, "B. Prefix-derived workflow token")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    steps = [
        ((0.03, 0.58), 0.17, 0.22, "prefix\nframes", COLORS["blue_bg"], "#93c5fd"),
        ((0.28, 0.58), 0.17, 0.22, "phase\nhead", COLORS["slate_bg"], "#cbd5e1"),
        ((0.52, 0.58), 0.20, 0.22, "TF-IDF\nPCA\ncentroids", COLORS["orange_bg"], "#fdba74"),
        ((0.80, 0.58), 0.16, 0.22, "soft\ncluster q", COLORS["green_bg"], "#5eead4"),
    ]
    for xy, w, h, text, fc, ec in steps:
        rounded_box(ax, xy, w, h, text, fc, ec, fontsize=6.9, weight="bold")
    for x0, x1 in [(0.20, 0.28), (0.45, 0.52), (0.72, 0.80)]:
        arrow(ax, (x0, 0.69), (x1, 0.69))
    rounded_box(
        ax,
        (0.22, 0.18), 0.56, 0.20,
        "workflow token\n$e_z=\\sum_k q_k E[k,:]$",
        COLORS["green_bg"],
        "#5eead4",
        fontsize=6.8,
        weight="bold",
    )
    arrow(ax, (0.88, 0.58), (0.76, 0.39), color=COLORS["teal"])
    ax.text(0.50, 0.08, "inference token is derived from pixels, not labels",
            ha="center", va="bottom", fontsize=6.6, color=COLORS["muted"])


def draw_protocol_panel(ax) -> None:
    panel_title(ax, "C. Protocol determines the real-time claim")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for y, title, target_x, color, note, label_x, label_y in [
        (0.66, "strict prefix-only", 0.82, COLORS["teal"], "clip ends at prediction time", 0.82, 0.12),
        (0.28, "centered-window", 0.50, COLORS["orange"], "clip includes post-target frames", 0.56, 0.07),
    ]:
        ax.plot([0.08, 0.92], [y, y], color="#cbd5e1", lw=4, solid_capstyle="round")
        xs = np.linspace(0.14, 0.86, 8)
        for x in xs:
            fc = "#dbeafe" if x <= target_x else "#fee2e2"
            ec = "#93c5fd" if x <= target_x else "#fca5a5"
            ax.add_patch(Rectangle((x - 0.023, y - 0.045), 0.046, 0.09, facecolor=fc, edgecolor=ec, linewidth=0.7))
        ax.axvline(target_x, y - 0.12, y + 0.12, color=color, lw=1.2)
        ax.text(label_x, y + label_y, "target t", ha="center", color=color, fontsize=6.8, fontweight="bold")
        ax.text(0.08, y + 0.13, title, ha="left", color=COLORS["ink"], fontsize=7.2, fontweight="bold")
        ax.text(0.08, y - 0.15, note, ha="left", color=COLORS["muted"], fontsize=6.8)
    ax.text(0.86, 0.13, "red frames are\nfuture relative to t", ha="center", color=COLORS["red"], fontsize=6.6)


def draw_results_panel(ax) -> None:
    panel_title(ax, "D. Empirical pattern")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    cards = [
        ((0.04, 0.66), 0.42, 0.22, "MB140 fold 0\nstrict gain: -0.85 min", COLORS["green_bg"], "#5eead4"),
        ((0.54, 0.66), 0.42, 0.22, "Bern -> Strasbourg\nstrict gain: -0.47 min", COLORS["green_bg"], "#5eead4"),
        ((0.04, 0.33), 0.42, 0.22, "Cholec80\nstrict range: 0.08 min", COLORS["slate_bg"], "#cbd5e1"),
        ((0.54, 0.33), 0.42, 0.22, "shuffle control\n13.14 vs 13.03 min", "#f5f3ff", "#c4b5fd"),
    ]
    for xy, w, h, text, fc, ec in cards:
        rounded_box(ax, xy, w, h, text, fc, ec, fontsize=7.0, weight="bold")
    ax.text(
        0.50,
        0.11,
        "Workflow conditioning helps when workflow variation exists;\nextra token capacity alone is not enough.",
        ha="center",
        va="center",
        fontsize=7.0,
        color=COLORS["ink"],
        fontweight="bold",
    )


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.25))
    fig.subplots_adjust(wspace=0.28, hspace=0.48)
    draw_variability_panel(axes[0, 0])
    draw_method_panel(axes[0, 1])
    draw_protocol_panel(axes[1, 0])
    draw_results_panel(axes[1, 1])
    fig.suptitle(
        "Workflow conditioning for remaining-surgery-duration prediction",
        x=0.5,
        y=1.02,
        fontsize=9.8,
        fontweight="bold",
        color=COLORS["ink"],
    )

    SUB.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        out = HERE / f"fig1_paper_overview.{ext}"
        fig.savefig(out)
        shutil.copy2(out, SUB / out.name)
        print(f"wrote {out} and {SUB / out.name}")


if __name__ == "__main__":
    main()

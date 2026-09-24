"""
Slide figure for inference step 1:
prefix frames pass through the visual encoder and HTA blocks with a
placeholder cluster identifier; the phase head is decoupled from that
placeholder and reads visual features only.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "paper" / "figures_slides"
FRAME_DIR = (
    ROOT
    / "lambda_mirror"
    / "extern"
    / "MultiBypass140"
    / "datasets"
    / "MultiBypass140"
    / "BernBypass70"
    / "frames"
    / "BBP12"
)

FRAME_NAMES = [
    "BBP12_00003439.jpg",
    "BBP12_00003444.jpg",
    "BBP12_00003449.jpg",
    "BBP12_00003454.jpg",
    "BBP12_00003459.jpg",
]
FRAME_LABELS = [r"$x_{t-20}$", r"$x_{t-15}$", r"$x_{t-10}$", r"$x_{t-5}$", r"$x_t$"]

TEXT = "#111827"
MUTED = "#4b5563"
EDGE = "#1f2937"
BLUE = "#2563eb"
BLUE_LIGHT = "#dbeafe"
GREEN = "#059669"
GREEN_LIGHT = "#d1fae5"
PURPLE = "#7c3aed"
PURPLE_LIGHT = "#ede9fe"
AMBER = "#f59e0b"
AMBER_LIGHT = "#fef3c7"
RED = "#dc2626"
RED_LIGHT = "#fee2e2"
GRAY_LIGHT = "#f9fafb"


def thumb(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    image = ImageOps.exif_transpose(image)
    w, h = image.size
    image = image.crop((55, 18, w - 55, h - 12))
    image = ImageOps.fit(image, (560, 390), method=Image.Resampling.LANCZOS)
    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = ImageEnhance.Sharpness(image).enhance(1.08)
    return np.asarray(image)


def add_text(ax, x, y, text, *, size=11, weight="normal", color=TEXT, ha="center", va="center"):
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        fontweight=weight,
        color=color,
        ha=ha,
        va=va,
        linespacing=1.08,
        zorder=20,
    )


def box(ax, x, y, w, h, text, *, face, edge=EDGE, size=12, weight="bold", color=TEXT):
    patch = patches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.025,rounding_size=0.08",
        linewidth=1.6,
        edgecolor=edge,
        facecolor=face,
        zorder=4,
    )
    ax.add_patch(patch)
    add_text(ax, x + w / 2, y + h / 2, text, size=size, weight=weight, color=color)
    return patch


def arrow(ax, start, end, *, color=EDGE, lw=1.8, style="-|>", rad=0.0, dashed=False):
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=18,
            linewidth=lw,
            linestyle="--" if dashed else "-",
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=4,
            shrinkB=6,
            zorder=12,
        )
    )


def draw_filmstrip(ax):
    x0, y0 = 0.78, 5.18
    w, h, gap = 2.04, 1.34, 0.18
    for i, (name, label) in enumerate(zip(FRAME_NAMES, FRAME_LABELS)):
        x = x0 + i * (w + gap)
        ax.imshow(thumb(FRAME_DIR / name), extent=(x, x + w, y0, y0 + h), aspect="auto", zorder=1)
        edge = AMBER if i == len(FRAME_NAMES) - 1 else BLUE
        lw = 3.0 if i == len(FRAME_NAMES) - 1 else 2.0
        ax.add_patch(patches.Rectangle((x, y0), w, h, fill=False, edgecolor=edge, linewidth=lw, zorder=6))
        ax.add_patch(patches.Rectangle((x, y0 + h - 0.30), 0.78, 0.30, facecolor="black", alpha=0.58, linewidth=0, zorder=7))
        add_text(ax, x + 0.39, y0 + h - 0.15, label, size=10.5, weight="bold", color="white")

    add_text(ax, 0.78, 7.10, r"Observed prefix frames $x_{1:t}$", size=17, weight="bold", ha="left")
    add_text(
        ax,
        0.78,
        6.82,
        "Concrete MB140 / BBP12 frames ending at the current timestamp t; no future thumbnails are used in this first-pass view.",
        size=10.4,
        color=MUTED,
        ha="left",
    )


def draw_phase_distribution(ax):
    x0, y0 = 12.55, 3.10
    labels = ["Prep", "Gastric", "Omentum", "GJ"]
    vals = [0.05, 0.12, 0.24, 0.59]
    colors = [GREEN_LIGHT, GREEN_LIGHT, GREEN_LIGHT, GREEN]
    for i, (lab, val, color) in enumerate(zip(labels, vals, colors)):
        x = x0 + i * 0.48
        ax.add_patch(
            patches.Rectangle(
                (x, y0),
                0.30,
                val * 1.05,
                facecolor=color,
                edgecolor=GREEN,
                linewidth=1.0,
                zorder=8,
            )
        )
        add_text(ax, x + 0.15, y0 - 0.16, lab, size=7.3, color=MUTED)
    ax.add_line(plt.Line2D([x0 - 0.04, x0 + 1.80], [y0, y0], color=MUTED, linewidth=0.8, zorder=8))
    add_text(ax, x0 + 0.90, y0 + 0.82, r"$p(\phi_t \mid x_{1:t})$", size=11, weight="bold", color=GREEN)
    add_text(ax, x0 + 0.90, y0 + 0.58, "argmax phase", size=8.7, color=MUTED)


def draw_pipeline(ax):
    box(ax, 0.95, 3.36, 2.10, 0.92, "prefix\nframes", face=BLUE_LIGHT, edge=BLUE, size=12)
    box(ax, 3.72, 3.36, 2.15, 0.92, "visual encoder\nViT-B/16", face=BLUE_LIGHT, edge=BLUE, size=11.3)
    box(ax, 6.42, 3.36, 1.95, 0.92, "frame\nfeatures", face=GRAY_LIGHT, edge=EDGE, size=11.3)
    box(ax, 8.88, 3.36, 1.96, 0.92, "HTA\nblocks", face=PURPLE_LIGHT, edge=PURPLE, size=11.5)
    box(ax, 11.45, 3.36, 2.08, 0.92, "phase\nhead", face=GREEN_LIGHT, edge=GREEN, size=12)
    box(ax, 13.98, 3.36, 1.38, 0.92, "phase\nlogits", face=GREEN_LIGHT, edge=GREEN, size=11)

    arrow(ax, (3.05, 3.82), (3.72, 3.82))
    arrow(ax, (5.87, 3.82), (6.42, 3.82))
    arrow(ax, (8.37, 3.82), (8.88, 3.82))
    arrow(ax, (10.84, 3.82), (11.45, 3.82), color=GREEN)
    arrow(ax, (13.53, 3.82), (13.98, 3.82), color=GREEN)

    add_text(ax, 6.70, 4.70, "visual-only path used by phase head", size=9.5, color=GREEN, ha="left")
    arrow(ax, (7.40, 4.55), (11.50, 4.10), color=GREEN, lw=1.4, rad=-0.12)

    # Placeholder workflow token branch.
    box(ax, 4.95, 1.76, 2.15, 0.78, "placeholder\ncluster id", face=AMBER_LIGHT, edge=AMBER, size=11.5)
    box(ax, 7.76, 1.76, 2.10, 0.78, "workflow token\nE[z_dummy]", face=AMBER_LIGHT, edge=AMBER, size=11.0)
    arrow(ax, (7.10, 2.15), (7.76, 2.15), color=AMBER)
    arrow(ax, (8.82, 2.54), (9.72, 3.36), color=AMBER, rad=-0.12)
    add_text(ax, 9.92, 2.55, "prepended into temporal sequence", size=9.2, color=AMBER, ha="left")

    # Explicitly show that the phase head ignores the placeholder in this pass.
    arrow(ax, (8.78, 2.15), (12.18, 3.28), color=RED, lw=1.5, dashed=True, rad=-0.10)
    ax.plot([11.55, 11.88], [2.78, 3.11], color=RED, linewidth=3.0, zorder=15)
    ax.plot([11.88, 11.55], [2.78, 3.11], color=RED, linewidth=3.0, zorder=15)
    add_text(ax, 12.18, 2.58, "no influence on\nphase head here", size=9.0, color=RED, weight="bold")

    draw_phase_distribution(ax)

    box(
        ax,
        0.95,
        1.35,
        3.00,
        1.04,
        "first pass uses a\ndummy workflow slot",
        face=GRAY_LIGHT,
        edge=EDGE,
        size=11.3,
    )
    add_text(
        ax,
        1.13,
        0.92,
        "Reason: the soft workflow token has not been computed yet. The phase predictions are the source used to compute it in the next step.",
        size=9.3,
        color=MUTED,
        ha="left",
    )


def main():
    missing = [name for name in FRAME_NAMES if not (FRAME_DIR / name).exists()]
    if missing:
        raise FileNotFoundError("Missing frame files: " + ", ".join(missing))

    OUTDIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "figure.dpi": 170,
            "savefig.dpi": 300,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.set_aspect("auto")
    ax.axis("off")

    add_text(ax, 0.78, 8.46, "Inference step 1: first pass with a placeholder workflow slot", size=19, weight="bold", ha="left")
    add_text(
        ax,
        0.78,
        8.08,
        "Prefix frames are encoded visually; the placeholder cluster token is present for the temporal stack, but phase prediction is decoupled from it.",
        size=11.2,
        color=MUTED,
        ha="left",
    )

    draw_filmstrip(ax)
    draw_pipeline(ax)

    out = OUTDIR / "fig_inference_step1_placeholder_phase_head"
    fig.savefig(out.with_suffix(".png"))
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    print(f"wrote {out.with_suffix('.png')}")
    print(f"wrote {out.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()

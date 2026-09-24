"""
Figure 3: strict online vs. centered-window clip formulation.

The visual style matches the clean transformer/ViT schematic figures:
white canvas, black flow arrows, thin outlines, blue gradient feature blocks,
and a small number of direct labels.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent

BLACK = "#111111"
BLUE = "#1f5bb4"
BLUE_DARK = "#0b3d8f"
BLUE_LIGHT = "#dce9fb"
YELLOW = "#ffd166"
YELLOW_EDGE = "#9a6a0a"
RED = "#d96b63"
RED_DARK = "#9c2f2a"
RED_LIGHT = "#ffe2df"
GRAY = "#f6f6f6"


def gradient_box(ax, x, y, w, h, text, *, fc1, fc2, ec, color=BLACK, fs=14, weight="normal"):
    """Rounded rectangle with a subtle vertical gradient, clipped to the shape."""
    patch = mpatches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor="none",
        edgecolor=ec,
        linewidth=1.15,
        zorder=3,
    )
    ax.add_patch(patch)

    c1 = np.array(mcolors.to_rgb(fc1))
    c2 = np.array(mcolors.to_rgb(fc2))
    grad = np.linspace(0, 1, 128)[:, None]
    rgb = c1 * (1 - grad) + c2 * grad
    img = np.repeat(rgb[:, None, :], 8, axis=1)
    im = ax.imshow(img, extent=(x, x + w, y, y + h), origin="lower", aspect="auto", zorder=2)
    im.set_clip_path(patch)

    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color, weight=weight, zorder=4)
    return patch


def arrow(ax, x1, y1, x2, y2, *, lw=1.7):
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", mutation_scale=18, lw=lw, color=BLACK, shrinkA=0, shrinkB=0),
        zorder=5,
    )


def timeline_axis(ax, x1, y, x2):
    ax.plot([x1, x2], [y, y], color=BLACK, lw=1.4, zorder=1)
    arrow(ax, x2 - 0.02, y, x2 + 0.28, y, lw=1.4)
    ax.text(x2 + 0.43, y, "time", ha="left", va="center", fontsize=11, color=BLACK)


def draw_frame_stack(ax, x, y, labels, kinds):
    frame_w = 0.62
    frame_h = 0.62
    gap = 0.12
    for i, (label, kind) in enumerate(zip(labels, kinds)):
        xx = x + i * (frame_w + gap)
        if kind == "observed":
            gradient_box(
                ax,
                xx,
                y,
                frame_w,
                frame_h,
                label,
                fc1="#f7fbff",
                fc2=BLUE_LIGHT,
                ec=BLUE_DARK,
                color=BLACK,
                fs=11,
            )
        elif kind == "target":
            gradient_box(
                ax,
                xx,
                y,
                frame_w,
                frame_h,
                label,
                fc1="#fff6cf",
                fc2=YELLOW,
                ec=YELLOW_EDGE,
                color=BLACK,
                fs=12,
                weight="bold",
            )
        else:
            gradient_box(
                ax,
                xx,
                y,
                frame_w,
                frame_h,
                label,
                fc1="#fff8f7",
                fc2=RED_LIGHT,
                ec=RED_DARK,
                color=BLACK,
                fs=11,
            )
    return frame_w, frame_h, gap


def draw_protocol(ax, *, y, title, subtitle, labels, kinds, target_idx, verdict, verdict_color, future_span=False):
    x0 = 4.05
    frame_w, frame_h, gap = draw_frame_stack(ax, x0, y, labels, kinds)
    x_end = x0 + len(labels) * frame_w + (len(labels) - 1) * gap
    y_mid = y + frame_h / 2

    ax.text(0.35, y + 0.46, title, ha="left", va="center", fontsize=13.5, weight="bold", color=BLACK)
    ax.text(0.35, y + 0.14, subtitle, ha="left", va="center", fontsize=9.8, color="#333333")

    timeline_axis(ax, x0 - 0.55, y - 0.32, x_end + 0.02)

    target_x = x0 + target_idx * (frame_w + gap) + frame_w / 2
    ax.plot([target_x, target_x], [y - 0.52, y + 1.15], linestyle=(0, (4, 3)), color=BLACK, lw=1.25, zorder=4)
    ax.text(target_x, y + 1.13, "target timestamp t", ha="center", va="bottom", fontsize=9.8, color=BLACK)

    if future_span:
        first_future_x = x0 + (target_idx + 1) * (frame_w + gap) - 0.04
        last_future_x = x0 + (len(labels) - 1) * (frame_w + gap) + frame_w + 0.04
        ax.plot([first_future_x, last_future_x], [y - 0.62, y - 0.62], color=RED_DARK, lw=2.0)
        ax.text(
            (first_future_x + last_future_x) / 2,
            y - 0.82,
            "frames after t inside the same clip",
            ha="center",
            va="top",
            fontsize=9.8,
            color=RED_DARK,
        )

    # Model input arrow and verdict block.
    arrow(ax, x_end + 0.55, y_mid, x_end + 1.25, y_mid)
    gradient_box(
        ax,
        x_end + 1.42,
        y - 0.03,
        1.45,
        0.72,
        "model\ninput",
        fc1="#ffffff",
        fc2=GRAY,
        ec=BLACK,
        fs=12,
        weight="bold",
    )
    arrow(ax, x_end + 3.02, y_mid, x_end + 3.65, y_mid)
    gradient_box(
        ax,
        x_end + 3.82,
        y - 0.03,
        2.05,
        0.72,
        verdict,
        fc1="#ffffff",
        fc2=verdict_color,
        ec=BLACK,
        fs=12,
        weight="bold",
    )


def draw_legend(ax):
    items = [
        ("observed prefix frame", "#f7fbff", BLUE_LIGHT, BLUE_DARK),
        ("target frame", "#fff6cf", YELLOW, YELLOW_EDGE),
        ("future frame", "#fff8f7", RED_LIGHT, RED_DARK),
    ]
    x = 2.65
    y = 0.52
    for label, fc1, fc2, ec in items:
        gradient_box(ax, x, y - 0.12, 0.28, 0.24, "", fc1=fc1, fc2=fc2, ec=ec, fs=1)
        ax.text(x + 0.40, y, label, ha="left", va="center", fontsize=10.2, color=BLACK)
        x += 2.45


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.dpi": 170,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )

    fig, ax = plt.subplots(figsize=(15.2, 5.8))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 16.4)
    ax.set_ylim(0, 6.1)
    ax.axis("off")

    ax.text(
        6.7,
        5.82,
        "Strict Online vs. Centered-Window Clip",
        ha="center",
        va="top",
        fontsize=18,
        weight="bold",
        color=BLACK,
    )

    labels_strict = ["t-7", "t-6", "t-5", "t-4", "t-3", "t-2", "t-1", "t"]
    kinds_strict = ["observed"] * 7 + ["target"]
    draw_protocol(
        ax,
        y=3.95,
        title="Strict online",
        subtitle="causal clip ending at t",
        labels=labels_strict,
        kinds=kinds_strict,
        target_idx=7,
        verdict="real-time\nvalid",
        verdict_color="#dce9fb",
    )

    labels_centered = ["t-3", "t-2", "t-1", "t", "t+1", "t+2", "t+3", "t+4"]
    kinds_centered = ["observed"] * 3 + ["target"] + ["future"] * 4
    draw_protocol(
        ax,
        y=2.20,
        title="Current setup",
        subtitle="centered clip with middle-frame label",
        labels=labels_centered,
        kinds=kinds_centered,
        target_idx=3,
        verdict="post-hoc\ncaveat",
        verdict_color=RED_LIGHT,
        future_span=True,
    )

    ax.text(
        6.7,
        1.05,
        "The inference-time workflow token is prefix-derived, but a centered clip can still expose visual frames after the target timestamp.",
        ha="center",
        va="center",
        fontsize=9.8,
        color=BLACK,
    )
    ax.text(
        6.7,
        0.22,
        "Example: clip length 8 at frame_stride 5 can let a clip labeled at minute 40 include frames up to roughly minute 42.",
        ha="center",
        va="center",
        fontsize=9.3,
        color="#333333",
    )
    draw_legend(ax)

    out_png = HERE / "fig3_protocol_comparison.png"
    fig.savefig(out_png)
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()

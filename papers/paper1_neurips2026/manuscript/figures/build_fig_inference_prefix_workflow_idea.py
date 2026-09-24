"""
New concept figure: inference-time prefix-derived soft workflow token.

This is separate from Figure 3, which explains strict online vs. centered
window sampling. This figure explains the inference algorithm:
predicted prefix phases -> soft posterior over workflow centroids -> soft
workflow token -> re-run temporal/RSD head.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent

BLACK = "#111111"
TEXT = "#202020"
MUTED = "#4a4a4a"
BLUE_DARK = "#0b3d8f"
BLUE_MID = "#1f5bb4"
BLUE_LIGHT = "#dce9fb"
GOLD = "#ffd166"
GOLD_LIGHT = "#fff3c4"
GOLD_EDGE = "#9a6a0a"
PURPLE = "#d8ccff"
PURPLE_LIGHT = "#f1ecff"
PURPLE_EDGE = "#5b3fb4"
GREEN = "#dff0d8"
GREEN_LIGHT = "#f5fbf2"
GREEN_EDGE = "#4f8a43"
RED = "#ffd9d6"
RED_EDGE = "#9c2f2a"
GRAY = "#f4f4f4"
GRAY_EDGE = "#505050"


def _gradient(fc1: str, fc2: str) -> np.ndarray:
    c1 = np.array(mcolors.to_rgb(fc1))
    c2 = np.array(mcolors.to_rgb(fc2))
    grad = np.linspace(0, 1, 128)[:, None]
    rgb = c1 * (1 - grad) + c2 * grad
    return np.repeat(rgb[:, None, :], 8, axis=1)


def box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    fc1: str = "#ffffff",
    fc2: str = BLUE_LIGHT,
    ec: str = BLUE_DARK,
    fs: float = 11,
    weight: str = "normal",
    color: str = TEXT,
    radius: float = 0.07,
    lw: float = 1.25,
):
    patch = mpatches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor="none",
        edgecolor=ec,
        linewidth=lw,
        zorder=3,
    )
    ax.add_patch(patch)
    img = _gradient(fc1, fc2)
    im = ax.imshow(img, extent=(x, x + w, y, y + h), origin="lower", aspect="auto", zorder=2)
    im.set_clip_path(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fs,
        color=color,
        weight=weight,
        linespacing=1.12,
        zorder=4,
    )
    return patch


def arrow(ax, x1, y1, x2, y2, *, color=BLACK, lw=1.6, rad=0.0, style="-|>"):
    ax.add_patch(
        mpatches.FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle=style,
            mutation_scale=17,
            linewidth=lw,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=0,
            shrinkB=0,
            zorder=5,
        )
    )


def step(ax, x, y, n):
    circ = mpatches.Circle((x, y), 0.18, facecolor=BLACK, edgecolor=BLACK, zorder=8)
    ax.add_patch(circ)
    ax.text(x, y, str(n), ha="center", va="center", fontsize=9, color="white", weight="bold", zorder=9)


def frame_strip(ax, x, y):
    labels = [r"$x_1$", r"$x_2$", r"$\cdots$", r"$x_t$"]
    w, h, gap = 0.55, 0.58, 0.10
    for i, label in enumerate(labels):
        box(
            ax,
            x + i * (w + gap),
            y,
            w,
            h,
            label,
            fc1="#ffffff",
            fc2=BLUE_LIGHT,
            ec=BLUE_DARK,
            fs=12,
            radius=0.055,
        )
    ax.text(x + 1.27, y - 0.32, "observed prefix frames", ha="center", va="center", fontsize=9.5, color=MUTED)


def posterior_bars(ax, x, y):
    heights = [0.42, 0.86, 0.30, 0.58]
    labels = [r"$q_1$", r"$q_2$", r"$q_3$", r"$q_K$"]
    for i, (height, label) in enumerate(zip(heights, labels)):
        xx = x + i * 0.38
        ax.add_patch(
            mpatches.Rectangle(
                (xx, y),
                0.22,
                height,
                facecolor=PURPLE,
                edgecolor=PURPLE_EDGE,
                linewidth=1.0,
                zorder=3,
            )
        )
        ax.text(xx + 0.11, y - 0.16, label, ha="center", va="top", fontsize=8.4, color=TEXT)
    ax.text(x + 0.68, y + 1.04, r"$q \in \Delta^{K-1}$", ha="center", va="bottom", fontsize=10.5, color=PURPLE_EDGE)


def embedding_table(ax, x, y):
    w, h = 0.42, 0.34
    colors = [PURPLE_LIGHT, PURPLE, "#c5b7ff", "#b9a6ff"]
    for i in range(4):
        box(
            ax,
            x,
            y + i * (h + 0.05),
            w,
            h,
            "",
            fc1="#ffffff",
            fc2=colors[i],
            ec=PURPLE_EDGE,
            radius=0.035,
            lw=0.9,
        )
    ax.text(x + 0.65, y + 0.72, r"$\mathbf{E}$", ha="center", va="center", fontsize=16, weight="bold", color=PURPLE_EDGE)
    ax.text(x + 0.65, y + 0.40, "workflow\nembeddings", ha="center", va="center", fontsize=8.5, color=MUTED)


def draw_caveat_strip(ax, x, y):
    labels = ["t-3", "t-2", "t-1", "t", "t+1", "t+2"]
    fills = [(BLUE_LIGHT, BLUE_DARK)] * 3 + [(GOLD_LIGHT, GOLD_EDGE)] + [(RED, RED_EDGE)] * 2
    w, h, gap = 0.34, 0.34, 0.04
    for i, (label, (fc, ec)) in enumerate(zip(labels, fills)):
        box(ax, x + i * (w + gap), y, w, h, label, fc1="#ffffff", fc2=fc, ec=ec, fs=6.8, radius=0.025, lw=0.8)


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.dpi": 170,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )

    fig, ax = plt.subplots(figsize=(15.4, 8.4))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(
        8,
        8.65,
        "Inference-Time Prefix-Derived Workflow Token",
        ha="center",
        va="top",
        fontsize=23,
        weight="bold",
        color=BLACK,
    )
    ax.text(
        8,
        8.25,
        "The model estimates workflow style from its own predicted prefix phases, then re-runs the RSD head with a soft workflow token.",
        ha="center",
        va="top",
        fontsize=11.2,
        color=MUTED,
    )

    # Step 1: first pass with placeholder slot.
    step(ax, 0.55, 7.18, 1)
    frame_strip(ax, 0.85, 6.82)
    box(
        ax,
        3.9,
        6.62,
        1.3,
        0.92,
        "placeholder\ncluster slot",
        fc1="#ffffff",
        fc2=GRAY,
        ec=GRAY_EDGE,
        fs=9.4,
        weight="bold",
    )
    box(
        ax,
        5.85,
        6.55,
        2.05,
        1.06,
        "Visual encoder\n+ HTA blocks",
        fc1="#ffffff",
        fc2=BLUE_LIGHT,
        ec=BLUE_DARK,
        fs=12,
        weight="bold",
    )
    box(
        ax,
        8.55,
        6.62,
        1.55,
        0.92,
        "Phase head\n$p(\\phi_i|x)$",
        fc1="#ffffff",
        fc2=GOLD_LIGHT,
        ec=GOLD_EDGE,
        fs=10.5,
        weight="bold",
    )
    box(
        ax,
        10.75,
        6.62,
        1.08,
        0.92,
        "argmax",
        fc1="#ffffff",
        fc2=GOLD_LIGHT,
        ec=GOLD_EDGE,
        fs=10.5,
        weight="bold",
    )
    box(
        ax,
        12.45,
        6.48,
        2.65,
        1.2,
        "predicted prefix\nphase sequence\n$\\hat{\\phi}(x_{1:t})$",
        fc1="#ffffff",
        fc2=GOLD_LIGHT,
        ec=GOLD_EDGE,
        fs=10.0,
        weight="bold",
    )

    arrow(ax, 3.55, 7.11, 3.9, 7.11)
    arrow(ax, 5.2, 7.08, 5.85, 7.08)
    arrow(ax, 7.9, 7.08, 8.55, 7.08)
    arrow(ax, 10.1, 7.08, 10.75, 7.08)
    arrow(ax, 11.83, 7.08, 12.45, 7.08)
    ax.text(6.25, 6.18, "first pass: the phase head uses visual features; the placeholder only fills the workflow slot", ha="center", fontsize=9.2, color=MUTED)

    # Step 2 and 3: phase sequence to posterior.
    step(ax, 0.55, 5.14, 2)
    arrow(ax, 13.75, 6.48, 2.0, 5.46, rad=0.18)
    box(ax, 1.15, 4.78, 1.25, 0.86, "TF-IDF\nvectorizer", fc1="#ffffff", fc2=BLUE_LIGHT, ec=BLUE_DARK, fs=10.0, weight="bold")
    box(ax, 3.05, 4.78, 1.0, 0.86, "PCA", fc1="#ffffff", fc2=BLUE_LIGHT, ec=BLUE_DARK, fs=11, weight="bold")
    box(
        ax,
        4.72,
        4.65,
        2.25,
        1.12,
        "distance to\n$K$ centroids\n$\\|u-c_k\\|^2$",
        fc1="#ffffff",
        fc2=BLUE_LIGHT,
        ec=BLUE_DARK,
        fs=10.0,
        weight="bold",
    )
    step(ax, 7.42, 5.14, 3)
    box(
        ax,
        7.75,
        4.55,
        2.45,
        1.32,
        "softmax over\nnegative squared distance\n$\\tau = 0.01$",
        fc1="#ffffff",
        fc2=PURPLE_LIGHT,
        ec=PURPLE_EDGE,
        fs=9.8,
        weight="bold",
    )
    posterior_bars(ax, 10.75, 4.73)

    arrow(ax, 2.4, 5.21, 3.05, 5.21)
    arrow(ax, 4.05, 5.21, 4.72, 5.21)
    arrow(ax, 6.97, 5.21, 7.75, 5.21)
    arrow(ax, 10.2, 5.21, 10.68, 5.21, color=PURPLE_EDGE)
    ax.text(5.55, 4.27, "same offline pipeline as clustering, but inference keeps the posterior soft instead of taking a hard cluster", ha="center", fontsize=9.2, color=MUTED)

    # Step 4: posterior to soft token and second RSD pass.
    step(ax, 0.55, 2.95, 4)
    embedding_table(ax, 1.15, 2.35)
    box(
        ax,
        3.05,
        2.52,
        2.55,
        1.05,
        "soft workflow token\n$\\mathbf{e}_z = \\sum_k q_k\\mathbf{E}[k,:]$",
        fc1="#ffffff",
        fc2=PURPLE_LIGHT,
        ec=PURPLE_EDGE,
        fs=10.0,
        weight="bold",
    )
    box(ax, 6.28, 2.6, 1.5, 0.9, "replace\nplaceholder", fc1="#ffffff", fc2=GRAY, ec=GRAY_EDGE, fs=10, weight="bold")
    box(ax, 8.42, 2.52, 1.92, 1.05, "re-run\ntemporal head", fc1="#ffffff", fc2=BLUE_LIGHT, ec=BLUE_DARK, fs=11.0, weight="bold")
    box(ax, 10.98, 2.52, 1.38, 1.05, "RSD head\n$\\hat{y}_t$", fc1="#ffffff", fc2=RED, ec=RED_EDGE, fs=11.2, weight="bold")
    box(ax, 13.05, 2.52, 2.05, 1.05, "remaining duration\nprediction", fc1="#ffffff", fc2=GREEN_LIGHT, ec=GREEN_EDGE, fs=10.4, weight="bold")

    arrow(ax, 11.42, 4.73, 4.28, 3.57, color=PURPLE_EDGE, rad=-0.18)
    arrow(ax, 2.05, 2.93, 3.05, 3.05, color=PURPLE_EDGE)
    arrow(ax, 5.6, 3.05, 6.28, 3.05, color=PURPLE_EDGE)
    arrow(ax, 7.78, 3.05, 8.42, 3.05)
    arrow(ax, 10.34, 3.05, 10.98, 3.05)
    arrow(ax, 12.36, 3.05, 13.05, 3.05)
    ax.text(8.4, 2.08, "second pass: RSD uses a workflow token inferred from the observed prefix", ha="center", fontsize=9.4, color=MUTED)

    # Guardrails and caveat.
    box(
        ax,
        0.85,
        0.75,
        4.8,
        0.72,
        "No ground-truth phase labels and no full-video oracle cluster are consulted at inference.",
        fc1="#ffffff",
        fc2=GREEN,
        ec=GREEN_EDGE,
        fs=9.6,
        weight="bold",
    )
    box(
        ax,
        6.15,
        0.72,
        8.95,
        0.78,
        "Caveat: the current dataset still uses centered clips; visual frames after t may be inside the clip itself. Figure 3 isolates that protocol issue.",
        fc1="#ffffff",
        fc2=GOLD_LIGHT,
        ec=GOLD_EDGE,
        fs=9.4,
        weight="bold",
    )
    draw_caveat_strip(ax, 12.7, 0.98)

    out_png = HERE / "fig_inference_prefix_workflow_idea.png"
    fig.savefig(out_png)
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()

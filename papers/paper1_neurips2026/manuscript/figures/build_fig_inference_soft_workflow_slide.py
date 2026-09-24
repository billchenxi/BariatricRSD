"""
Slide figure: inference-time soft workflow token with the centered-window caveat.

This is a presentation-only figure. It uses a concrete MultiBypass140 clip
from BBP12 to make the inference pipeline less abstract, and saves outputs to
paper/figures_slides rather than the paper figure directory.
"""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import fill

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageEnhance, ImageOps


ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "paper" / "figures_slides"
ARTIFACTS = ROOT / "labels" / "mb140_fold0_kmeans_artifacts.json"
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

OUTDIR.mkdir(parents=True, exist_ok=True)

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
GRAY = "#e5e7eb"
GRAY_LIGHT = "#f9fafb"


FRAME_NAMES = [
    "BBP12_00003439.jpg",
    "BBP12_00003444.jpg",
    "BBP12_00003449.jpg",
    "BBP12_00003454.jpg",
    "BBP12_00003459.jpg",
    "BBP12_00003464.jpg",
    "BBP12_00003469.jpg",
    "BBP12_00003474.jpg",
]
FRAME_TIMES = ["t-20", "t-15", "t-10", "t-5", "t", "t+5", "t+10", "t+15"]
FRAME_PHASES = [
    "Omentum division",
    "Omentum division",
    "Omentum division",
    "Omentum division",
    "Gastro-jejunal anastomosis",
    "Gastro-jejunal anastomosis",
    "Gastro-jejunal anastomosis",
    "Gastro-jejunal anastomosis",
]

PREFIX_BIGRAMS = [
    "preparation->gastric_pouch_creation",
    "gastric_pouch_creation->omentum_division",
    "omentum_division->gastro-jejunal_anastomosis",
]
PHASE_SEQUENCE_LABELS = ["Preparation", "Gastric pouch", "Omentum", "Gastro-jejunal"]


def load_artifacts() -> dict:
    with open(ARTIFACTS) as f:
        return json.load(f)


def posterior_from_bigrams(art: dict, bigrams: list[str], temperature: float = 0.01) -> tuple[np.ndarray, np.ndarray]:
    vocabulary = art["vocabulary"]
    idf = np.asarray(art["idf"], dtype=np.float64)
    pca_components = np.asarray(art["pca_components"], dtype=np.float64)
    pca_mean = np.asarray(art["pca_mean"], dtype=np.float64)
    centroids = np.asarray(art["centroids"], dtype=np.float64)
    k = int(art["K"])

    tf = np.zeros(len(vocabulary), dtype=np.float64)
    hits = 0
    for bigram in bigrams:
        j = vocabulary.get(bigram)
        if j is not None:
            tf[j] += 1.0
            hits += 1
    if hits == 0:
        return np.full(k, 1.0 / k, dtype=np.float64), np.full(k, np.nan)

    tf /= tf.sum()
    pca = pca_components @ (tf * idf - pca_mean)
    d2 = np.sum((centroids - pca[None, :]) ** 2, axis=1)
    logits = -d2 / max(temperature, 1e-6)
    logits -= logits.max()
    weights = np.exp(logits)
    weights /= weights.sum()
    return weights, d2


def crop_for_thumb(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    image = ImageOps.exif_transpose(image)
    w, h = image.size
    crop = image.crop((55, 18, w - 55, h - 12))
    crop = ImageOps.fit(crop, (520, 390), method=Image.Resampling.LANCZOS)
    crop = ImageEnhance.Contrast(crop).enhance(1.12)
    crop = ImageEnhance.Sharpness(crop).enhance(1.08)
    return np.asarray(crop)


def rounded_box(
    ax,
    xy: tuple[float, float],
    wh: tuple[float, float],
    *,
    face: str,
    edge: str = EDGE,
    lw: float = 1.3,
    radius: float = 0.06,
    zorder: int = 2,
):
    x, y = xy
    w, h = wh
    box = patches.FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.018,rounding_size={radius}",
        linewidth=lw,
        edgecolor=edge,
        facecolor=face,
        zorder=zorder,
    )
    ax.add_patch(box)
    return box


def add_text(ax, x, y, s, *, size=11, weight="normal", color=TEXT, ha="center", va="center", wrap=None):
    if wrap:
        s = fill(s, width=wrap)
    ax.text(
        x,
        y,
        s,
        ha=ha,
        va=va,
        fontsize=size,
        fontweight=weight,
        color=color,
        linespacing=1.08,
        zorder=10,
    )


def arrow(ax, start, end, *, color=EDGE, lw=1.6, rad=0.0):
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=lw,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=6,
            shrinkB=8,
            zorder=9,
        )
    )


def step_badge(ax, x, y, label, color=EDGE):
    ax.add_patch(patches.Circle((x, y), 0.17, facecolor=color, edgecolor=color, zorder=12))
    add_text(ax, x, y, str(label), size=9.5, weight="bold", color="white")


def draw_filmstrip(ax):
    x0, y0 = 0.78, 6.08
    w, h, gap = 1.70, 0.96, 0.12
    for i, (name, time_label, phase) in enumerate(zip(FRAME_NAMES, FRAME_TIMES, FRAME_PHASES)):
        x = x0 + i * (w + gap)
        img = crop_for_thumb(FRAME_DIR / name)
        ax.imshow(img, extent=(x, x + w, y0, y0 + h), aspect="auto", zorder=1)

        if i == 4:
            edge = AMBER
            lw = 3.0
        elif i > 4:
            edge = RED
            lw = 2.5
            ax.add_patch(patches.Rectangle((x, y0), w, h, facecolor=RED, alpha=0.12, linewidth=0, zorder=2))
        else:
            edge = BLUE
            lw = 1.6

        ax.add_patch(patches.Rectangle((x, y0), w, h, fill=False, edgecolor=edge, linewidth=lw, zorder=4))
        add_text(
            ax,
            x + 0.08,
            y0 + h - 0.10,
            time_label,
            size=9,
            weight="bold",
            color="white",
            ha="left",
            va="top",
        )
        label_face = AMBER_LIGHT if i == 4 else RED_LIGHT if i > 4 else BLUE_LIGHT
        label_edge = AMBER if i == 4 else RED if i > 4 else BLUE
        rounded_box(ax, (x + 0.06, y0 - 0.29), (w - 0.12, 0.22), face=label_face, edge=label_edge, lw=0.8, radius=0.03, zorder=4)
        short_phase = "GJ anastomosis" if "Gastro" in phase else "Omentum"
        add_text(ax, x + w / 2, y0 - 0.18, short_phase, size=7.3, color=TEXT)

    add_text(ax, 0.45, 7.31, "Concrete centered-window clip from MB140 / BBP12", size=14, weight="bold", ha="left")
    add_text(
        ax,
        0.45,
        7.10,
        "Prediction timestamp is the middle-frame label at t = 57:39; red thumbnails are after t but still inside the clip.",
        size=9.6,
        color=MUTED,
        ha="left",
    )


def draw_phase_sequence(ax):
    x0, y = 2.0, 4.74
    widths = [1.35, 1.25, 1.05, 1.55]
    centers = []
    cursor = x0
    for label, width in zip(PHASE_SEQUENCE_LABELS, widths):
        rounded_box(ax, (cursor, y), (width, 0.43), face=GREEN_LIGHT, edge=GREEN, lw=1.1, radius=0.055)
        add_text(ax, cursor + width / 2, y + 0.215, label, size=8.8, color=TEXT)
        centers.append((cursor + width / 2, y + 0.215))
        cursor += width + 0.18
    for (x1, yy), (x2, _) in zip(centers[:-1], centers[1:]):
        arrow(ax, (x1 + 0.48, yy), (x2 - 0.50, yy), color=GREEN, lw=1.1)
    add_text(ax, x0, y + 0.72, "Argmax phase predictions become a prefix sequence", size=10.2, weight="bold", ha="left")


def draw_posterior_bars(ax, q: np.ndarray):
    x0, y0 = 6.82, 3.42
    width = 0.28
    scale = 1.38
    for i, val in enumerate(q):
        x = x0 + i * 0.43
        height = max(0.018, val * scale)
        ax.add_patch(
            patches.Rectangle(
                (x, y0),
                width,
                height,
                facecolor=PURPLE,
                edgecolor=PURPLE,
                linewidth=0.9,
                zorder=6,
            )
        )
        add_text(ax, x + width / 2, y0 - 0.13, f"C{i}", size=7.8, color=MUTED)
        if val > 0.025:
            add_text(ax, x + width / 2, y0 + height + 0.10, f"{val:.2f}", size=7.8, color=PURPLE, weight="bold")
    ax.add_line(plt.Line2D([x0 - 0.06, x0 + 2.76], [y0, y0], color=MUTED, linewidth=0.8, zorder=5))
    add_text(ax, x0 + 1.32, y0 + 1.66, r"$q_k \propto \exp(-\|u-c_k\|^2 / \tau)$", size=11.0, color=PURPLE)
    add_text(ax, x0 + 1.32, y0 + 1.43, r"$K=6,\ \tau=0.01$", size=9.6, color=MUTED)


def draw_token_blend(ax, q: np.ndarray):
    x, y = 10.30, 3.40
    colors = ["#ede9fe", "#ddd6fe", "#c4b5fd", "#a78bfa", "#8b5cf6", "#6d28d9"]
    for i, color in enumerate(colors):
        ax.add_patch(
            patches.Rectangle(
                (x + i * 0.18, y + i * 0.055),
                1.05,
                0.40,
                facecolor=color,
                edgecolor=PURPLE,
                linewidth=0.7,
                alpha=0.88,
                zorder=3 + i,
            )
        )
    add_text(ax, x + 0.78, y + 0.98, r"$\mathbf{E}[k,:]$", size=10.5, weight="bold", color=PURPLE)
    add_text(ax, x + 0.78, y - 0.12, r"$\mathbf{e}_z=\sum_k q_k\mathbf{E}[k,:]$", size=11.0, weight="bold", color=TEXT)
    add_text(ax, x + 0.78, y - 0.39, "soft workflow token", size=9.1, color=MUTED)
    add_text(ax, x + 0.78, y + 0.68, f"dominant C{int(np.argmax(q))}", size=8.4, color=MUTED)


def draw_phase_pills(ax, x0: float, y: float):
    widths = [0.78, 0.86, 0.62, 0.92]
    labels = ["Prep", "Gastric", "Omentum", "GJ"]
    cursor = x0
    centers = []
    for label, width in zip(labels, widths):
        rounded_box(ax, (cursor, y), (width, 0.30), face=GREEN_LIGHT, edge=GREEN, lw=0.9, radius=0.04, zorder=5)
        add_text(ax, cursor + width / 2, y + 0.15, label, size=7.4, color=TEXT)
        centers.append((cursor + width / 2, y + 0.15, width))
        cursor += width + 0.13
    for (x1, yy, w1), (x2, _, w2) in zip(centers[:-1], centers[1:]):
        arrow(ax, (x1 + w1 / 2 - 0.03, yy), (x2 - w2 / 2 + 0.03, yy), color=GREEN, lw=0.8)


def draw_q_bars(ax, x0: float, y0: float, q: np.ndarray):
    width = 0.18
    scale = 0.74
    for i, val in enumerate(q):
        x = x0 + i * 0.31
        height = max(0.018, val * scale)
        ax.add_patch(
            patches.Rectangle(
                (x, y0),
                width,
                height,
                facecolor=PURPLE,
                edgecolor=PURPLE,
                linewidth=0.7,
                zorder=6,
            )
        )
        add_text(ax, x + width / 2, y0 - 0.09, f"C{i}", size=6.6, color=MUTED)
    ax.add_line(plt.Line2D([x0 - 0.03, x0 + 1.70], [y0, y0], color=MUTED, linewidth=0.7, zorder=5))
    add_text(ax, x0 + 1.08, y0 + 0.83, f"C{int(np.argmax(q))} dominates", size=7.2, color=PURPLE, weight="bold")


def draw_pipeline(ax, q: np.ndarray):
    card_y, card_h = 3.42, 1.46
    card_w, gap = 3.42, 0.34
    xs = [0.45 + i * (card_w + gap) for i in range(4)]

    specs = [
        (BLUE_LIGHT, BLUE, "First pass", r"$x_{1:t}$ + placeholder slot" + "\nViT-B/16 + HTA -> phase logits"),
        (GREEN_LIGHT, GREEN, "Predicted prefix phases", "Phase-head argmax per clip\n" + r"forms $\hat\phi(x_{1:t})$"),
        (PURPLE_LIGHT, PURPLE, "Prefix posterior", "Same TF-IDF/PCA/centroids\nsoftmax of -squared distances"),
        (AMBER_LIGHT, AMBER, "Soft token then RSD", r"$\mathbf{e}_z=\sum_k q_k\mathbf{E}[k,:]$" + "\nreplace placeholder and re-run"),
    ]

    for i, (x, (face, edge, title, body)) in enumerate(zip(xs, specs), start=1):
        rounded_box(ax, (x, card_y), (card_w, card_h), face=face, edge=edge, lw=1.4, radius=0.08)
        step_badge(ax, x + 0.18, card_y + card_h - 0.16, i, edge)
        add_text(ax, x + 0.42, card_y + card_h - 0.18, title, size=10.2, weight="bold", color=TEXT, ha="left")
        add_text(ax, x + 0.22, card_y + 0.88, body, size=8.4, color=MUTED, ha="left", va="top")
        if i < len(xs):
            arrow(ax, (x + card_w + 0.03, card_y + card_h / 2), (xs[i] - 0.03, card_y + card_h / 2), color=EDGE, lw=1.2)

    draw_phase_pills(ax, xs[1] + 0.22, card_y + 0.28)
    draw_q_bars(ax, xs[2] + 0.35, card_y + 0.28, q)

    for j, color in enumerate(["#c4b5fd", "#a78bfa", "#8b5cf6"]):
        ax.add_patch(
            patches.Rectangle(
                (xs[3] + 0.33 + j * 0.18, card_y + 0.22 + j * 0.05),
                0.82,
                0.28,
                facecolor=color,
                edgecolor=PURPLE,
                linewidth=0.7,
                alpha=0.88,
                zorder=5 + j,
            )
        )
    add_text(ax, xs[3] + 1.98, card_y + 0.40, "temporal head\nRSD head", size=9.0, weight="bold", color=TEXT)
    arrow(ax, (xs[3] + 1.42, card_y + 0.43), (xs[3] + 2.40, card_y + 0.43), color=AMBER, lw=1.0)

    rounded_box(ax, (0.45, 3.02), (14.70, 0.26), face=GRAY_LIGHT, edge=GRAY, lw=0.6, radius=0.035)
    add_text(
        ax,
        0.63,
        3.15,
        "Inference reads model-predicted phases from the observed prefix only; no ground-truth phase labels or full-case workflow labels are consulted.",
        size=8.3,
        weight="bold",
        color=TEXT,
        ha="left",
    )


def draw_protocol_caveat(ax):
    add_text(ax, 0.45, 2.48, "Centered-window caveat", size=14.0, weight="bold", ha="left")
    add_text(
        ax,
        0.45,
        2.24,
        "The soft token is prefix-derived, but the current clip dataset still labels the middle frame.",
        size=10.0,
        color=MUTED,
        ha="left",
    )

    x0 = 4.50
    y_strict = 1.48
    y_center = 0.68
    w, h, gap = 0.54, 0.34, 0.06

    def row(y, title, labels, target_at_last):
        add_text(ax, x0 - 0.36, y + h / 2, title, size=9.2, weight="bold", ha="right")
        for i, lab in enumerate(labels):
            x = x0 + i * (w + gap)
            if target_at_last:
                if i == len(labels) - 1:
                    fc, ec = AMBER_LIGHT, AMBER
                else:
                    fc, ec = BLUE_LIGHT, BLUE
            else:
                if i < 4:
                    fc, ec = BLUE_LIGHT, BLUE
                elif i == 4:
                    fc, ec = AMBER_LIGHT, AMBER
                else:
                    fc, ec = RED_LIGHT, RED
            rounded_box(ax, (x, y), (w, h), face=fc, edge=ec, lw=1.0, radius=0.035)
            add_text(ax, x + w / 2, y + h / 2, lab, size=8.1, weight="bold", color=TEXT)

    row(y_strict, "strict online", ["t-35", "t-30", "t-25", "t-20", "t-15", "t-10", "t-5", "t"], True)
    row(y_center, "current centered clip", FRAME_TIMES, False)

    add_text(ax, 10.08, y_strict + h / 2, "clip ends at prediction time", size=9.0, color=BLUE, ha="left")
    add_text(ax, 10.08, y_center + h / 2, "post-target frames remain visible", size=9.0, color=RED, ha="left")

    rounded_box(ax, (12.15, 0.61), (3.28, 1.34), face=GRAY_LIGHT, edge=EDGE, lw=1.0, radius=0.07)
    add_text(ax, 12.35, 1.70, "How to say it on the slide", size=9.7, weight="bold", ha="left")
    add_text(
        ax,
        12.35,
        1.28,
        "Workflow token: inferred from observed prefix. Clip protocol: not strictly online because the visual window is centered.",
        size=8.8,
        color=MUTED,
        ha="left",
        va="top",
        wrap=46,
    )


def main():
    missing = [name for name in FRAME_NAMES if not (FRAME_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(
            "Missing BBP12 frame thumbnails. Pull them from Lambda first: " + ", ".join(missing)
        )

    art = load_artifacts()
    q, d2 = posterior_from_bigrams(art, PREFIX_BIGRAMS, temperature=0.01)

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
    ax.axis("off")
    ax.set_aspect("auto")

    add_text(
        ax,
        0.45,
        8.55,
        "Inference-time soft workflow token from the observed prefix",
        size=20,
        weight="bold",
        ha="left",
    )
    add_text(
        ax,
        0.45,
        8.16,
        "First pass predicts prefix phases; the same offline TF-IDF/PCA centroids produce a posterior over workflow styles; the RSD head is then re-run with a soft token.",
        size=10.5,
        color=MUTED,
        ha="left",
    )
    add_text(ax, 15.45, 8.55, "MB140 fold 0, K=6", size=8.8, color=MUTED, ha="right")
    add_text(ax, 15.45, 8.34, "TF-IDF vocab=63, PCA=16", size=8.8, color=MUTED, ha="right")

    draw_filmstrip(ax)
    draw_pipeline(ax, q)
    draw_protocol_caveat(ax)

    add_text(
        ax,
        0.45,
        0.28,
        "Example posterior for the BBP12 prefix: "
        + ", ".join(f"C{i}={val:.3f}" for i, val in enumerate(q))
        + ".",
        size=8.2,
        color=MUTED,
        ha="left",
    )

    out = OUTDIR / "fig_inference_soft_workflow_token_explainer"
    fig.savefig(out.with_suffix(".png"))
    fig.savefig(out.with_suffix(".pdf"))
    plt.close(fig)
    print(f"wrote {out.with_suffix('.png')}")
    print(f"wrote {out.with_suffix('.pdf')}")
    print("posterior:", np.round(q, 6).tolist())
    print("d2:", np.round(d2, 6).tolist())


if __name__ == "__main__":
    main()

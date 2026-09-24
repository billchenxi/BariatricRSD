"""Build a concrete overall project pipeline figure.

Output:
  paper/figures/fig_project_overall_pipeline.{png,pdf}
  paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig_project_overall_pipeline.{png,pdf}
  paper/final_draft/figures/fig_project_overall_pipeline.{png,pdf} when present

The figure uses real MB140/BBP12 frames when the local Lambda mirror is
available, and falls back to the existing explanatory PNG otherwise.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image, ImageOps


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PAPER = ROOT / "paper"
SUB_FIG = PAPER / "Formatting_Instructions_For_NeurIPS_2026" / "figures"
FINAL_FIG = PAPER / "final_draft" / "figures"
FINAL_SCRIPTS = PAPER / "final_draft" / "figure_scripts"

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
    "BBP12_00003464.jpg",
    "BBP12_00003469.jpg",
    "BBP12_00003474.jpg",
]


COLORS = {
    "ink": "#111827",
    "muted": "#4b5563",
    "blue": "#1d4ed8",
    "blue_light": "#eff6ff",
    "teal": "#0f766e",
    "teal_light": "#ecfdf5",
    "orange": "#d97706",
    "orange_light": "#fff7ed",
    "purple": "#7c3aed",
    "purple_light": "#f5f3ff",
    "gray": "#64748b",
    "gray_light": "#f8fafc",
    "red": "#dc2626",
    "red_light": "#fef2f2",
    "edge": "#334155",
}


plt.rcParams.update({
    "figure.dpi": 180,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "font.family": "DejaVu Sans",
    "font.size": 8.2,
})


def load_thumb(path: Path, size: tuple[int, int] = (220, 150)) -> Image.Image:
    if path.exists():
        img = Image.open(path).convert("RGB")
    else:
        fallback = HERE / "clip_to_tensor_pipeline.png"
        img = Image.open(fallback).convert("RGB")
    return ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)


def box(ax, x, y, w, h, text, fc, ec, size=8.0, weight="normal", color=None):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.035,rounding_size=0.055",
        facecolor=fc,
        edgecolor=ec,
        linewidth=1.1,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=size,
        fontweight=weight,
        color=color or COLORS["ink"],
        linespacing=1.12,
    )
    return patch


def arrow(ax, start, end, color=None, lw=1.4, rad=0.0):
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="-|>",
            lw=lw,
            color=color or COLORS["edge"],
            shrinkA=2,
            shrinkB=2,
            connectionstyle=f"arc3,rad={rad}",
        ),
    )


def add_panel_label(ax, x, y, label):
    ax.text(x, y, label, ha="left", va="top", fontsize=10.5,
            fontweight="bold", color=COLORS["ink"])


def draw_filmstrip(ax, x, y, w, h):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="#0b0f19",
                           edgecolor="black", linewidth=1.0))
    hole_h = h / 13.5
    for i in range(11):
        yy = y + 0.10 + i * (h - 0.20) / 10.4
        ax.add_patch(Rectangle((x + 0.05, yy), 0.07, hole_h,
                               facecolor="white", edgecolor="white"))
        ax.add_patch(Rectangle((x + w - 0.12, yy), 0.07, hole_h,
                               facecolor="white", edgecolor="white"))

    thumb_h = (h - 0.34) / 4.6
    for i, name in enumerate(FRAME_NAMES[:4]):
        yy = y + h - 0.17 - (i + 1) * thumb_h - i * 0.035
        img = load_thumb(FRAME_DIR / name)
        ax.imshow(img, extent=(x + 0.16, x + w - 0.16, yy, yy + thumb_h),
                  aspect="auto", zorder=2)
    ax.text(x + w / 2, y - 0.10, "time", ha="center", va="top",
            fontsize=7.0, color=COLORS["muted"])
    arrow(ax, (x + w / 2, y - 0.17), (x + w / 2, y - 0.45),
          color=COLORS["ink"], lw=1.0)


def draw_clip(ax, x, y, w, h):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                                facecolor="white", edgecolor=COLORS["blue"],
                                linewidth=1.1, linestyle="--"))
    thumb_h = (h - 0.30) / 4.4
    for i, name in enumerate(FRAME_NAMES[:4]):
        yy = y + h - 0.16 - (i + 1) * thumb_h - i * 0.035
        img = load_thumb(FRAME_DIR / name)
        ax.imshow(img, extent=(x + 0.12, x + w - 0.12, yy, yy + thumb_h),
                  aspect="auto", zorder=2)
    ax.text(x + w / 2, y + 0.28, "...", ha="center", va="center",
            fontsize=13, color=COLORS["ink"])
    ax.text(x + w / 2, y - 0.12, "8-frame clip", ha="center", va="top",
            fontsize=8.0, color=COLORS["blue"], fontweight="bold")


def draw_feature_matrix(ax, x, y, w, h):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=COLORS["blue_light"],
                           edgecolor=COLORS["blue"], linewidth=1.1))
    rows = 8
    for i in range(1, rows):
        yy = y + i * h / rows
        ax.plot([x, x + w], [yy, yy], color="#bfdbfe", linewidth=0.7)
    for r in range(rows):
        yy = y + (r + 0.5) * h / rows
        for c in range(5):
            xx = x + 0.12 + c * (w - 0.24) / 4
            ax.scatter(xx, yy, s=9, color=COLORS["blue"])
        ax.text(x - 0.09, yy, f"$t_{r+1}$", ha="right", va="center",
                fontsize=6.5, color=COLORS["ink"])
    ax.text(x + w / 2, y + h + 0.12, "$8 \\times 768$ frame tensor",
            ha="center", va="bottom", fontsize=8.0, color=COLORS["blue"],
            fontweight="bold")
    ax.text(x + w / 2, y - 0.12, "768", ha="center", va="top",
            fontsize=7.0, color=COLORS["muted"])


def draw_phase_sequence(ax, x, y, w, h):
    phases = [
        ("P1", "#2563eb"),
        ("P2", "#0f766e"),
        ("P3", "#d97706"),
        ("P2", "#0f766e"),
        ("P4", "#7c3aed"),
        ("P5", "#db2777"),
    ]
    gap = 0.035
    seg_w = (w - gap * (len(phases) - 1)) / len(phases)
    for i, (p, c) in enumerate(phases):
        xx = x + i * (seg_w + gap)
        ax.add_patch(Rectangle((xx, y), seg_w, h, facecolor=c,
                               edgecolor="white", linewidth=0.7))
        ax.text(xx + seg_w / 2, y + h / 2, p, ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")


def main() -> None:
    fig, ax = plt.subplots(figsize=(13.6, 7.0))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.2)
    ax.axis("off")

    ax.text(
        8.0, 9.0,
        "Overall pipeline: workflow-conditioned RSD prediction",
        ha="center", va="top", fontsize=14.2, fontweight="bold",
        color=COLORS["ink"],
    )
    ax.text(
        8.0, 8.58,
        "Concrete visual example from MultiBypass140 / BBP12; the same model/evaluation protocol is also applied to Cholec80.",
        ha="center", va="top", fontsize=8.6, color=COLORS["muted"],
    )

    # Main visual path.
    add_panel_label(ax, 0.25, 8.10, "1. Video -> clip -> frame tensor")
    ax.text(1.05, 7.75, "surgical video", ha="center", va="center",
            fontsize=8.2, fontweight="bold")
    draw_filmstrip(ax, 0.45, 4.70, 1.20, 2.85)
    arrow(ax, (1.70, 6.18), (2.18, 6.18), color=COLORS["blue"], lw=1.1)
    draw_clip(ax, 2.22, 4.90, 1.25, 2.55)
    arrow(ax, (3.55, 6.18), (4.05, 6.18))
    box(ax, 4.12, 5.56, 1.28, 1.25, "ViT-B/16\nper-frame\nencoder",
        COLORS["blue_light"], COLORS["blue"], size=8.0, weight="bold")
    arrow(ax, (5.48, 6.18), (5.92, 6.18))
    draw_feature_matrix(ax, 6.00, 5.05, 1.25, 2.05)

    # Workflow token branch.
    add_panel_label(ax, 0.25, 4.15, "2. Workflow token: oracle during diagnosis, prefix-derived at inference")
    box(ax, 0.42, 3.10, 1.38, 0.74, "full phase\nsequence",
        COLORS["purple_light"], COLORS["purple"], size=7.5, weight="bold")
    draw_phase_sequence(ax, 0.58, 2.72, 1.05, 0.25)
    box(ax, 2.25, 3.10, 1.28, 0.74, "phase\nbigrams",
        COLORS["purple_light"], COLORS["purple"], size=7.5, weight="bold")
    box(ax, 4.02, 3.10, 1.56, 0.74, "TF-IDF\n+ PCA",
        COLORS["orange_light"], COLORS["orange"], size=7.5, weight="bold")
    box(ax, 6.08, 3.10, 1.34, 0.74, "k-means\ncentroids",
        COLORS["orange_light"], COLORS["orange"], size=7.5, weight="bold")
    box(ax, 7.94, 3.10, 1.44, 0.74, "cluster z\nor posterior q",
        COLORS["teal_light"], COLORS["teal"], size=7.2, weight="bold")
    box(ax, 10.00, 3.10, 1.35, 0.74, "workflow\ntoken",
        COLORS["teal_light"], COLORS["teal"], size=7.5, weight="bold")
    ax.text(10.68, 2.72, "$E[z,:]$ or $\\sum_k q_k E[k,:]$",
            ha="center", va="top", fontsize=7.2, color=COLORS["teal"])
    for start, end in [((1.82, 3.47), (2.23, 3.47)), ((3.55, 3.47), (4.00, 3.47)),
                       ((5.60, 3.47), (6.06, 3.47)), ((7.44, 3.47), (7.92, 3.47)),
                       ((9.40, 3.47), (9.98, 3.47))]:
        arrow(ax, start, end, color=COLORS["gray"], lw=1.1)

    ax.text(0.42, 2.18, "oracle diagnostic path", ha="left",
            fontsize=7.2, color=COLORS["purple"], fontweight="bold")
    ax.text(0.42, 1.88, "uses full-case phase sequence", ha="left",
            fontsize=6.8, color=COLORS["muted"])
    box(ax, 4.15, 1.74, 1.45, 0.58, "prefix frames",
        COLORS["blue_light"], COLORS["blue"], size=7.0, weight="bold")
    box(ax, 6.10, 1.74, 1.50, 0.58, "phase head\npredictions",
        COLORS["gray_light"], COLORS["gray"], size=6.8, weight="bold")
    box(ax, 8.10, 1.74, 1.55, 0.58, "same\ncentroid map",
        COLORS["orange_light"], COLORS["orange"], size=6.8, weight="bold")
    ax.text(4.15, 1.36, "causal-at-inference path: no ground-truth phase labels or full-case cluster label",
            ha="left", va="top", fontsize=6.9, color=COLORS["teal"])
    arrow(ax, (5.62, 2.03), (6.08, 2.03), color=COLORS["teal"], lw=1.0)
    arrow(ax, (7.62, 2.03), (8.08, 2.03), color=COLORS["teal"], lw=1.0)
    arrow(ax, (9.66, 2.03), (10.28, 3.06), color=COLORS["teal"], lw=1.0, rad=0.15)

    # Modeling and outputs.
    add_panel_label(ax, 7.70, 8.10, "3. Temporal prediction model")
    box(ax, 7.85, 5.67, 1.45, 0.82, "append\nworkflow token",
        COLORS["teal_light"], COLORS["teal"], size=7.4, weight="bold")
    arrow(ax, (7.28, 6.18), (7.82, 6.18), color=COLORS["teal"], lw=1.1)
    arrow(ax, (10.68, 3.86), (8.58, 5.62), color=COLORS["teal"], lw=1.1, rad=-0.18)
    box(ax, 9.90, 5.36, 1.70, 1.42, "HTA-inspired\n6-block\ntemporal head",
        COLORS["gray_light"], COLORS["edge"], size=7.8, weight="bold")
    arrow(ax, (9.33, 6.18), (9.88, 6.18))
    box(ax, 12.15, 6.38, 1.10, 0.55, "RSD\nhead",
        "#eef2ff", COLORS["blue"], size=7.4, weight="bold")
    box(ax, 12.15, 5.70, 1.10, 0.55, "phase\nhead",
        "#f0fdf4", COLORS["teal"], size=7.4, weight="bold")
    box(ax, 12.15, 5.02, 1.10, 0.55, "deviation\nhead",
        "#fff7ed", COLORS["orange"], size=7.4, weight="bold")
    for yy in [6.66, 5.98, 5.30]:
        arrow(ax, (11.62, 6.07), (12.12, yy), lw=1.0)
    box(ax, 13.78, 6.02, 1.48, 0.74, "remaining\nsurgery duration",
        "#eef2ff", COLORS["blue"], size=7.2, weight="bold")
    arrow(ax, (13.27, 6.66), (13.76, 6.44), color=COLORS["blue"], lw=1.0)

    # Evaluation right/bottom.
    add_panel_label(ax, 11.78, 4.15, "4. Evaluation question")
    box(ax, 11.85, 3.36, 1.28, 0.52, "MB140\nwithin-center",
        COLORS["green_light"] if "green_light" in COLORS else COLORS["teal_light"], COLORS["teal"],
        size=6.8, weight="bold")
    box(ax, 13.32, 3.36, 1.36, 0.52, "MB140\ncross-center",
        COLORS["teal_light"], COLORS["teal"], size=6.8, weight="bold")
    box(ax, 14.88, 3.36, 0.82, 0.52, "Cholec80",
        COLORS["gray_light"], COLORS["gray"], size=6.8, weight="bold")
    box(ax, 12.02, 2.44, 1.62, 0.52, "strict prefix-only\nvs centered-window",
        COLORS["blue_light"], COLORS["blue"], size=6.6, weight="bold")
    box(ax, 13.92, 2.44, 1.52, 0.52, "shuffled-token\ncontrol",
        COLORS["purple_light"], COLORS["purple"], size=6.6, weight="bold")
    ax.text(13.77, 1.80,
            "Main claim: workflow conditioning helps when\nworkflow variation exists and the token is meaningful.",
            ha="center", va="top", fontsize=7.4, color=COLORS["ink"], fontweight="bold")

    # Compact study-scope footer.
    ax.plot([0.40, 15.60], [0.62, 0.62], color="#e5e7eb", lw=1.0)
    footer = (
        "Study scope: MultiBypass140 + Cholec80 | "
        "conditions: no-token, retrospective oracle, causal-at-inference | "
        "metric: validation MAE in minutes"
    )
    ax.text(8.0, 0.34, footer, ha="center", va="center",
            fontsize=7.2, color=COLORS["muted"])

    for ext in ("png", "pdf"):
        out = HERE / f"fig_project_overall_pipeline.{ext}"
        fig.savefig(out)
        for dest in (SUB_FIG, FINAL_FIG):
            if dest.exists():
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(out, dest / out.name)
        print(f"wrote {out}")

    if FINAL_SCRIPTS.exists():
        shutil.copy2(Path(__file__), FINAL_SCRIPTS / Path(__file__).name)


if __name__ == "__main__":
    main()

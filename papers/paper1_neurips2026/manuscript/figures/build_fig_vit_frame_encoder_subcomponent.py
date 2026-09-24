"""Build a compact ViT-B/16 frame-encoder subcomponent figure.

Output:
  paper/figures/fig_vit_frame_encoder_subcomponent.{png,pdf,svg}
  paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig_vit_frame_encoder_subcomponent.{png,pdf,svg}
  paper/final_draft/figures/fig_vit_frame_encoder_subcomponent.{png,pdf,svg} when present

The diagram is intended to be embedded as a detailed replacement for a
single "ViT-B/16 frame encoder" box in overview figures.
"""
from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image, ImageOps


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PAPER = ROOT / "paper"
SUB_FIG = PAPER / "Formatting_Instructions_For_NeurIPS_2026" / "figures"
FINAL_FIG = PAPER / "final_draft" / "figures"

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
SLIDE_ASSET_DIR = PAPER / "figures_slides" / "assets"
FRAME_NAME = "BBP12_00003449.jpg"

COLORS = {
    "ink": "#111827",
    "muted": "#4b5563",
    "edge": "#334155",
    "blue": "#1d4ed8",
    "blue_mid": "#2563eb",
    "blue_light": "#eff6ff",
    "blue_frozen": "#dce6f2",
    "teal": "#0f766e",
    "green_light": "#e8f3dc",
    "gray": "#64748b",
    "gray_light": "#f8fafc",
    "white": "#ffffff",
}


plt.rcParams.update(
    {
        "figure.dpi": 180,
        "savefig.dpi": 320,
        "savefig.bbox": "tight",
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.linewidth": 0.8,
    }
)


def frame_path() -> Path:
    local = FRAME_DIR / FRAME_NAME
    if local.exists():
        return local
    return SLIDE_ASSET_DIR / FRAME_NAME


def load_frame() -> Image.Image:
    path = frame_path()
    if not path.exists():
        raise FileNotFoundError(f"Missing source frame: {path}")
    return Image.open(path).convert("RGB")


def arrow(ax, start: tuple[float, float], end: tuple[float, float], *, color: str | None = None, lw: float = 1.25) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=lw,
            color=color or COLORS["edge"],
            shrinkA=2,
            shrinkB=2,
            zorder=5,
        )
    )


def rounded_box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fc: str,
    ec: str,
    text: str = "",
    text_color: str | None = None,
    size: float = 8.0,
    weight: str = "normal",
    radius: float = 0.06,
    lw: float = 1.0,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=2,
    )
    ax.add_patch(patch)
    if text:
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=size,
            fontweight=weight,
            color=text_color or COLORS["ink"],
            linespacing=1.05,
            zorder=6,
        )
    return patch


def draw_input_frame(ax, img: Image.Image, x: float, y: float, w: float, h: float) -> None:
    thumb = ImageOps.fit(img, (720, 520), method=Image.Resampling.LANCZOS)
    ax.imshow(thumb, extent=(x, x + w, y, y + h), aspect="auto", zorder=3)
    ax.add_patch(Rectangle((x, y), w, h, facecolor="none", edgecolor=COLORS["ink"], linewidth=1.1, zorder=4))
    ax.text(x + w / 2, y + h + 0.24, "Input frame", ha="center", va="bottom", fontsize=9.0, fontweight="bold", color=COLORS["ink"])
    ax.text(x + w / 2, y - 0.14, "one sampled surgical frame", ha="center", va="top", fontsize=6.8, color=COLORS["muted"])


def draw_patch_grid(ax, img: Image.Image, x: float, y: float, tile: float, gap: float, n: int = 4) -> None:
    square = ImageOps.fit(img, (512, 512), method=Image.Resampling.LANCZOS)
    patch_px = square.width // n
    for row in range(n):
        for col in range(n):
            crop = square.crop((col * patch_px, row * patch_px, (col + 1) * patch_px, (row + 1) * patch_px))
            xx = x + col * (tile + gap)
            yy = y + (n - 1 - row) * (tile + gap)
            ax.imshow(crop, extent=(xx, xx + tile, yy, yy + tile), aspect="auto", zorder=3)
            ax.add_patch(Rectangle((xx, yy), tile, tile, facecolor="none", edgecolor=COLORS["white"], linewidth=1.0, zorder=4))

    total = n * tile + (n - 1) * gap
    ax.add_patch(Rectangle((x - 0.03, y - 0.03), total + 0.06, total + 0.06, facecolor="none", edgecolor="#d1d5db", linewidth=0.8, zorder=2))
    ax.text(x + total / 2, y + total + 0.24, "16 x 16 px patches", ha="center", va="bottom", fontsize=9.0, fontweight="bold", color=COLORS["ink"])
    ax.text(x + total + 0.10, y + 0.10, "...", ha="left", va="bottom", fontsize=15, color=COLORS["ink"])


def draw_vit_stack(ax, x: float, y: float, w: float, h: float) -> None:
    rounded_box(ax, x, y, w, h, fc="none", ec=COLORS["edge"], radius=0.08, lw=0.9)
    ax.text(x + w / 2, y + h + 0.36, "ViT-B/16", ha="center", va="bottom", fontsize=11.0, fontweight="bold", color=COLORS["ink"])
    ax.text(x + w / 2, y + h + 0.15, "ImageNet-21k init; 12 transformer blocks", ha="center", va="bottom", fontsize=7.2, color=COLORS["muted"])

    pad_x = 0.35
    block_x = x + pad_x
    block_w = w - 0.78
    block_h = 0.205
    gap = 0.055
    bottom = y + 0.33
    block_y: dict[int, float] = {}

    for idx in range(1, 13):
        yy = bottom + (idx - 1) * (block_h + gap)
        if idx >= 7:
            fc = COLORS["blue"]
            ec = "#143880"
            tc = COLORS["white"]
            weight = "bold"
        else:
            fc = COLORS["blue_frozen"]
            ec = "#9fb6cf"
            tc = COLORS["ink"]
            weight = "normal"
        rounded_box(ax, block_x, yy, block_w, block_h, fc=fc, ec=ec, text=f"Block {idx}", text_color=tc, size=6.6, weight=weight, radius=0.035, lw=0.65)
        ax.text(block_x - 0.12, yy + block_h / 2, str(idx), ha="right", va="center", fontsize=6.4, color=COLORS["ink"])
        block_y[idx] = yy

    sep_y = block_y[7] - gap / 2
    ax.plot([x + 0.18, x + w - 0.18], [sep_y, sep_y], color=COLORS["edge"], linewidth=0.8, linestyle=(0, (4, 3)), zorder=5)

    bracket_x = x + w + 0.10
    def bracket(y0: float, y1: float, color: str, label: str, sublabel: str) -> None:
        ax.plot([bracket_x, bracket_x], [y0, y1], color=color, linewidth=1.15)
        ax.plot([bracket_x - 0.08, bracket_x], [y0, y0], color=color, linewidth=1.15)
        ax.plot([bracket_x - 0.08, bracket_x], [y1, y1], color=color, linewidth=1.15)
        ax.text(bracket_x + 0.12, (y0 + y1) / 2 + 0.08, label, ha="left", va="center", fontsize=7.2, fontweight="bold", color=color)
        ax.text(bracket_x + 0.12, (y0 + y1) / 2 - 0.12, sublabel, ha="left", va="center", fontsize=6.6, color=color)

    bracket(block_y[7], block_y[12] + block_h, COLORS["blue"], "Fine-tuned", "blocks 7-12")
    bracket(block_y[1], block_y[6] + block_h, "#3b6f9c", "Frozen", "blocks 1-6")


def draw_cls_and_feature(ax, x: float, y: float) -> None:
    ax.text(x + 0.36, y + 1.16, "[CLS] output", ha="center", va="bottom", fontsize=8.4, fontweight="bold", color=COLORS["ink"])
    rounded_box(ax, x, y + 0.50, 0.72, 0.52, fc="#f1f5f9", ec=COLORS["gray"], text="CLS", size=8.0, weight="bold")

    feat_x = x + 1.45
    feat_y = y + 0.08
    feat_w = 0.42
    feat_h = 1.55
    rounded_box(ax, feat_x, feat_y, feat_w, feat_h, fc=COLORS["green_light"], ec=COLORS["gray"], radius=0.07, lw=0.9)
    for yy in [feat_y + 1.30, feat_y + 1.06, feat_y + 0.82, feat_y + 0.58, feat_y + 0.23]:
        ax.add_patch(Circle((feat_x + feat_w / 2, yy), 0.065, facecolor="#75a65b", edgecolor="#75a65b", zorder=6))
    ax.text(feat_x + feat_w / 2, feat_y + 0.40, "...", ha="center", va="center", fontsize=8.0, fontweight="bold", color=COLORS["ink"], zorder=7)
    ax.text(feat_x + feat_w / 2, feat_y + feat_h + 0.18, "768-d\nframe feature", ha="center", va="bottom", fontsize=8.0, fontweight="bold", color=COLORS["ink"], linespacing=1.0)
    arrow(ax, (x + 0.74, y + 0.76), (feat_x - 0.08, feat_y + feat_h / 2), color=COLORS["edge"], lw=1.1)


def main() -> None:
    img = load_frame()
    fig, ax = plt.subplots(figsize=(10.8, 3.80))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 4.75)
    ax.axis("off")

    ax.text(0.18, 4.62, "ViT-B/16 frame encoder subcomponent", ha="left", va="top", fontsize=11.2, fontweight="bold", color=COLORS["ink"])
    ax.text(0.18, 4.36, "Each sampled frame is patchified, encoded independently, and represented by its 768-d [CLS] feature.", ha="left", va="top", fontsize=7.4, color=COLORS["muted"])

    draw_input_frame(ax, img, 0.30, 1.26, 2.18, 1.56)
    arrow(ax, (2.58, 2.04), (3.02, 2.04))
    draw_patch_grid(ax, img, 3.16, 1.19, tile=0.36, gap=0.055)
    arrow(ax, (4.78, 2.04), (5.32, 2.04))
    draw_vit_stack(ax, 5.45, 0.38, 2.78, 3.22)
    arrow(ax, (8.92, 2.02), (9.55, 2.02))
    draw_cls_and_feature(ax, 9.72, 1.16)

    ax.text(12.00, 0.55, "Used per frame;\n8 frames -> 8 x 768 tensor", ha="center", va="center", fontsize=7.4, color=COLORS["blue"], fontweight="bold", linespacing=1.15)

    for ext in ("png", "pdf", "svg"):
        out = HERE / f"fig_vit_frame_encoder_subcomponent.{ext}"
        fig.savefig(out)
        for dest in (SUB_FIG, FINAL_FIG):
            if dest.exists():
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(out, dest / out.name)
        print(f"wrote {out}")

    if (PAPER / "final_draft" / "figure_scripts").exists():
        shutil.copy2(Path(__file__), PAPER / "final_draft" / "figure_scripts" / Path(__file__).name)


if __name__ == "__main__":
    main()

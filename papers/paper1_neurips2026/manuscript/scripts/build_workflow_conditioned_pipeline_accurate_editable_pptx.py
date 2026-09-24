"""Build an accurate editable PPTX architecture/pipeline figure.

This revises the older high-level workflow-conditioned RSD schematic so the
ViT and workflow-token operations match the implementation:

  - each 16 x 16 x 3 patch is flattened and linearly projected to a 768-d token
  - the ViT [CLS] token is prepended before the ViT blocks
  - the final ViT [CLS] state is used as each frame feature
  - the workflow token is prepended/concatenated with frame features, not added

Output:
    paper/figures/fig_workflow_conditioned_pipeline_accurate_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/fig_workflow_conditioned_pipeline_accurate_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

SLIDE_W = 13.60
SLIDE_H = 8.15

COLORS = {
    **base.COLORS,
    "blue_light": "EFF6FF",
    "teal": "0F766E",
    "teal_light": "ECFDF5",
    "orange": "D97706",
    "orange_light": "FFF7ED",
    "purple": "7C3AED",
    "purple_light": "F5F3FF",
    "red": "DC2626",
    "red_light": "FEF2F2",
    "yellow_light": "FFFBEB",
}


def set_slide_size() -> None:
    base.SLIDE_W = SLIDE_W
    base.SLIDE_H = SLIDE_H


def block(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    *,
    fill: str = "FFFFFF",
    stroke: str = COLORS["edge"],
    title_color: str = COLORS["ink"],
    title_pt: float = 8.0,
    body: str | None = None,
    body_pt: float = 6.4,
) -> None:
    base.shape("Block", "roundRect", x, y, w, h, fill, stroke, 0.9)
    base.textbox("Block title", x + 0.08, y + 0.10, w - 0.16, 0.18, title, title_pt, title_color, True, "ctr")
    if body:
        base.textbox("Block body", x + 0.10, y + 0.36, w - 0.20, h - 0.42, body, body_pt, COLORS["ink"], False, "ctr")


def tiny_token(x: float, y: float, label: str, *, cls: bool = False, w: float = 0.42) -> None:
    if cls:
        base.shape("CLS token", "roundRect", x, y, w, 0.24, COLORS["orange_light"], COLORS["orange"], 0.65, label, 5.5, COLORS["orange"], True)
    else:
        base.shape("Token", "roundRect", x, y, w, 0.24, COLORS["blue_frozen"], COLORS["blue_frozen_edge"], 0.55, label, 5.2, COLORS["ink"])


def film_icon(x: float, y: float, w: float, h: float) -> None:
    base.shape("Film outer", "roundRect", x, y, w, h, "FFFFFF", COLORS["ink"], 1.0)
    for i in range(4):
        yy = y + 0.08 + i * (h - 0.20) / 3
        base.shape("Film hole L", "rect", x + 0.06, yy, 0.10, 0.10, COLORS["ink"], COLORS["ink"], 0.1)
        base.shape("Film hole R", "rect", x + w - 0.16, yy, 0.10, 0.10, COLORS["ink"], COLORS["ink"], 0.1)
    base.shape("Play triangle", "triangle", x + w * 0.43, y + h * 0.33, w * 0.22, h * 0.34, COLORS["ink"], COLORS["ink"], 0.1)


def frame_strip(x: float, y: float) -> None:
    base.textbox("Video label", x, y - 0.30, 1.72, 0.18, "Observed prefix video", 8.3, COLORS["ink"], True, "ctr")
    film_icon(x + 0.42, y, 0.80, 0.72)
    base.textbox("Video note", x + 0.06, y + 0.82, 1.48, 0.15, "8 frames: x_1:t", 6.3, COLORS["muted"], False, "ctr")
    for i in range(8):
        xx = x + 0.03 + i * 0.19
        fill = "DBEAFE" if i < 7 else COLORS["orange_light"]
        stroke = COLORS["blue"] if i < 7 else COLORS["orange"]
        base.shape("Frame chip", "rect", xx, y + 1.06, 0.14, 0.16, fill, stroke, 0.35)


def vit_encoder_detail(x: float, y: float, w: float, h: float) -> None:
    base.shape("ViT encoder detail", "roundRect", x, y, w, h, COLORS["blue_light"], COLORS["blue"], 0.95)
    base.textbox("ViT title", x + 0.10, y + 0.10, w - 0.20, 0.18, "Shared ViT-B/16 frame encoder", 8.5, COLORS["blue"], True, "ctr")

    # Patch projection lane.
    base.shape("Patch grid", "rect", x + 0.18, y + 0.48, 0.54, 0.54, "FFFFFF", COLORS["edge"], 0.45)
    cell = 0.12
    fills = ["6B2C23", "A64E3F", "3D1F1B", "1B1210", "CF7A6A", "754034", "4A2422", "9C5A50", "E3A093", "884B43", "6C3736", "B05F57", "B96D62", "6D403B", "8A4747", "BF6B62"]
    for r in range(4):
        for c in range(4):
            base.shape("Patch cell", "rect", x + 0.22 + c * cell, y + 0.52 + r * cell, cell - 0.01, cell - 0.01, fills[r * 4 + c], "FFFFFF", 0.25)
    base.textbox("Patch label", x + 0.03, y + 1.07, 0.82, 0.24, "14 x 14 grid\n16 x 16 px each", 4.8, COLORS["muted"], False, "ctr")

    base.arrow(x + 0.78, y + 0.75, x + 1.10, y + 0.75, COLORS["edge"])
    block(
        x + 1.18,
        y + 0.44,
        1.05,
        0.60,
        "flatten + linear",
        fill="FFFFFF",
        stroke=COLORS["blue"],
        title_pt=5.8,
        body="16 x 16 x 3 = 768\n-> token in R^768",
        body_pt=4.8,
    )

    base.arrow(x + 2.28, y + 0.75, x + 2.58, y + 0.75, COLORS["edge"])
    tiny_token(x + 2.64, y + 0.50, "CLS", cls=True, w=0.42)
    tiny_token(x + 3.14, y + 0.50, "p1")
    tiny_token(x + 3.61, y + 0.50, "p2")
    tiny_token(x + 4.08, y + 0.50, "...")
    tiny_token(x + 4.51, y + 0.50, "p196", w=0.48)
    base.textbox("Vstack formula", x + 2.50, y + 0.86, 2.64, 0.16, "X = [x_CLS ; p_1 ; ... ; p_196] + pos", 5.4, COLORS["ink"], False, "ctr")
    base.textbox("Vstack shape", x + 2.94, y + 1.04, 1.76, 0.13, "X in R^(197 x 768)", 5.3, COLORS["muted"], False, "ctr")

    base.arrow(x + 5.20, y + 0.75, x + 5.52, y + 0.75, COLORS["edge"])
    base.shape("ViT blocks mini", "roundRect", x + 5.60, y + 0.39, 0.86, 0.78, "FFFFFF", COLORS["blue"], 0.65)
    for i in range(6):
        fill = COLORS["blue_frozen"] if i < 3 else COLORS["blue"]
        stroke = COLORS["blue_frozen_edge"] if i < 3 else COLORS["blue_dark"]
        base.shape("Mini block", "roundRect", x + 5.72, y + 0.50 + i * 0.095, 0.62, 0.055, fill, stroke, 0.15)
    base.textbox("12 blocks", x + 5.63, y + 1.21, 0.80, 0.12, "12 blocks", 4.7, COLORS["muted"], False, "ctr")

    base.arrow(x + 6.52, y + 0.75, x + 6.82, y + 0.75, COLORS["edge"])
    tiny_token(x + 6.88, y + 0.50, "CLS'", cls=True, w=0.46)
    base.arrow(x + 7.42, y + 0.62, x + 7.80, y + 0.62, COLORS["teal"])
    base.shape("Frame feature", "roundRect", x + 7.88, y + 0.34, 0.50, 0.70, COLORS["green_light"], COLORS["gray"], 0.75)
    for k in range(4):
        base.shape("Feature dot", "ellipse", x + 8.08, y + 0.45 + k * 0.13, 0.08, 0.08, COLORS["green"], COLORS["green"], 0.1)
    base.textbox("Feature label", x + 7.60, y + 1.08, 1.05, 0.13, "f_i in R^768", 5.4, COLORS["teal"], True, "ctr")

    base.textbox("ViT note", x + 0.30, y + 1.38, w - 0.60, 0.16, "The final CLS row is the frame summary; it is not concatenated after the blocks.", 6.0, COLORS["orange"], True, "ctr")


def frame_feature_matrix(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Frame-feature matrix", fill=COLORS["blue_light"], stroke=COLORS["blue"], title_color=COLORS["blue"], title_pt=7.3)
    mx, my, mw, mh = x + 0.20, y + 0.42, w - 0.40, h - 0.72
    base.shape("F matrix", "rect", mx, my, mw, mh, "FFFFFF", COLORS["blue"], 0.7)
    for r in range(1, 8):
        yy = my + r * mh / 8
        base.line("F row", mx, yy, mx + mw, yy, "BFDBFE", 0.35)
    for r in range(8):
        yy = my + (r + 0.5) * mh / 8
        base.textbox("f label", mx - 0.20, yy - 0.045, 0.16, 0.08, f"f_{r+1}", 4.1, COLORS["muted"], False, "r")
        for c in range(4):
            xx = mx + 0.12 + c * (mw - 0.24) / 3
            base.shape("F dot", "ellipse", xx - 0.018, yy - 0.018, 0.036, 0.036, COLORS["blue"], COLORS["blue"], 0.1)
    base.textbox("F shape", x + 0.08, y + h - 0.22, w - 0.16, 0.12, "F in R^(8 x 768)", 5.7, COLORS["blue"], True, "ctr")


def phase_sequence(x: float, y: float, w: float, h: float, title: str, *, prefix: bool = False) -> None:
    fill = COLORS["teal_light"] if prefix else COLORS["purple_light"]
    stroke = COLORS["teal"] if prefix else COLORS["purple"]
    block(x, y, w, h, title, fill=fill, stroke=stroke, title_color=stroke, title_pt=6.7)
    colors = ["2563EB", "0F766E", "D97706", "0F766E", "7C3AED", "DB2777"]
    labels = ["A", "B", "C", "B", "D", "E"]
    seg_w = (w - 0.32) / len(labels)
    for i, (lab, col) in enumerate(zip(labels, colors)):
        base.shape("Phase dot", "ellipse", x + 0.16 + i * seg_w, y + 0.48, 0.16, 0.16, col, col, 0.1, lab, 4.2, "FFFFFF", True)
    base.textbox("Phase caption", x + 0.16, y + 0.78, w - 0.32, 0.12, "ordered labels over time", 4.8, COLORS["muted"], False, "ctr")


def bigrams(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Transition bigrams", fill=COLORS["purple_light"], stroke=COLORS["purple"], title_color=COLORS["purple"], title_pt=6.4)
    for i, txt in enumerate(["(A,B)", "(B,C)", "(C,B)", "(B,D)"]):
        base.shape("Bigram chip", "roundRect", x + 0.18 + (i % 2) * 0.48, y + 0.45 + (i // 2) * 0.20, 0.40, 0.13, "FFFFFF", COLORS["purple"], 0.3, txt, 4.2, COLORS["ink"], True)


def artifact_pipeline(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Fixed offline artifacts", fill=COLORS["orange_light"], stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=6.5)
    # TF-IDF grid.
    gx, gy = x + 0.16, y + 0.44
    for r in range(4):
        for c in range(5):
            fill = "FDBA74" if c == 0 else ("FED7AA" if (r + c) % 2 == 0 else "FFFFFF")
            base.shape("TFIDF cell", "rect", gx + c * 0.10, gy + r * 0.10, 0.09, 0.09, fill, COLORS["border"], 0.15)
    base.textbox("TFIDF", gx - 0.02, gy + 0.45, 0.58, 0.10, "TF-IDF", 4.4, COLORS["muted"], False, "ctr")
    # PCA points and centroids.
    px, py = x + 0.92, y + 0.48
    base.line("PCA x", px - 0.08, py + 0.18, px + 0.58, py + 0.18, COLORS["muted"], 0.3)
    base.line("PCA y", px, py + 0.02, px, py + 0.50, COLORS["muted"], 0.3)
    for dx, dy, col in [(0.10, 0.10, COLORS["blue"]), (0.20, 0.32, COLORS["teal"]), (0.42, 0.18, COLORS["orange"]), (0.36, 0.40, COLORS["purple"]), (0.54, 0.28, COLORS["teal"])]:
        base.shape("PCA point", "ellipse", px + dx, py + dy, 0.055, 0.055, col, col, 0.1)
    base.textbox("PCA label", px + 0.02, gy + 0.45, 0.62, 0.10, "PCA + k-means", 4.2, COLORS["muted"], False, "ctr")


def workflow_token_box(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Workflow token w", fill=COLORS["teal_light"], stroke=COLORS["teal"], title_color=COLORS["teal"], title_pt=6.8)
    base.textbox("w formula 1", x + 0.10, y + 0.43, w - 0.20, 0.13, "oracle: w = E[z_full]", 5.3, COLORS["ink"], False, "ctr")
    base.textbox("w formula 2", x + 0.10, y + 0.64, w - 0.20, 0.13, "causal: w = sum_k q_k E[k]", 5.3, COLORS["ink"], False, "ctr")
    base.shape("Token visual", "rect", x + 0.30, y + 0.90, w - 0.60, 0.14, COLORS["purple"], COLORS["purple"], 0.2)


def sequence_stack(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Temporal input sequence", fill=COLORS["yellow_light"], stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=7.0)
    base.textbox("Seq formula", x + 0.10, y + 0.40, w - 0.20, 0.15, "S = [w ; f_1 ; ... ; f_8]", 6.2, COLORS["ink"], True, "ctr")
    base.textbox("Seq shape", x + 0.10, y + 0.60, w - 0.20, 0.13, "S in R^(9 x 768)", 5.4, COLORS["muted"], False, "ctr")
    # stack visual
    sx, sy = x + 0.44, y + 0.84
    base.shape("w row", "rect", sx, sy, w - 0.88, 0.12, COLORS["purple"], COLORS["purple"], 0.1)
    for i in range(5):
        base.shape("f row", "rect", sx, sy + 0.16 + i * 0.10, w - 0.88, 0.06, "DBEAFE", COLORS["blue"], 0.12)
    base.shape("No plus badge", "roundRect", x + 0.28, y + h - 0.28, w - 0.56, 0.18, COLORS["red_light"], COLORS["red"], 0.45)
    base.textbox("No plus", x + 0.34, y + h - 0.24, w - 0.68, 0.10, "concat/prepend, not +", 4.8, COLORS["red"], True, "ctr")


def hta_and_heads(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "HTA-inspired temporal head", fill=COLORS["gray_light"], stroke=COLORS["edge"], title_pt=7.0)
    for i in range(6):
        base.shape("HTA block", "roundRect", x + 0.24, y + 0.45 + i * 0.11, w - 0.48, 0.075, "E5E7EB", COLORS["edge"], 0.22)
    base.textbox("HTA note", x + 0.14, y + h - 0.25, w - 0.28, 0.12, "6 blocks; row 0 becomes h_t", 5.3, COLORS["muted"], False, "ctr")


def heads(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Task heads on h_t", fill="FFFFFF", stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=7.1)
    items = [
        ("RSD regression", "MSE", "EEF2FF", COLORS["blue"]),
        ("Phase cls.", "CE", "F0FDF4", COLORS["teal"]),
        ("Deviation", "BCE", COLORS["orange_light"], COLORS["orange"]),
    ]
    for i, (name, loss, fill, stroke) in enumerate(items):
        xx = x + 0.18 + i * ((w - 0.42) / 3)
        ww = (w - 0.54) / 3
        base.shape("Head card", "roundRect", xx, y + 0.46, ww, 0.62, fill, stroke, 0.5)
        base.textbox("Head name", xx + 0.04, y + 0.55, ww - 0.08, 0.13, name, 5.3, COLORS["ink"], True, "ctr")
        base.textbox("Head loss", xx + 0.04, y + 0.84, ww - 0.08, 0.12, loss, 5.0, COLORS["muted"], False, "ctr")
    base.textbox("Decoupled note", x + 0.20, y + h - 0.22, w - 0.40, 0.12, "decoupled runs: phase head reads pre-token visual features", 4.8, COLORS["muted"], False, "ctr")


def conditioning_settings(x: float, y: float, w: float, h: float) -> None:
    block(x, y, w, h, "Conditioning settings", fill="FFFFFF", stroke=COLORS["blue"], title_color=COLORS["blue"], title_pt=7.1)
    rows = [
        ("No-token / constant", "video features only baseline", COLORS["blue"]),
        ("Oracle", "full-surgery z_full -> E[z]", COLORS["purple"]),
        ("Causal", "prefix-derived q -> sum qE", COLORS["teal"]),
    ]
    for i, (title, note, color) in enumerate(rows):
        yy = y + 0.42 + i * 0.33
        base.shape("Setting swatch", "rect", x + 0.20, yy + 0.04, 0.16, 0.16, color, color, 0.1)
        base.textbox("Setting title", x + 0.42, yy, w - 0.60, 0.12, title, 5.4, COLORS["ink"], True)
        base.textbox("Setting note", x + 0.42, yy + 0.16, w - 0.60, 0.10, note, 4.6, COLORS["muted"])


def build_slide_xml() -> bytes:
    set_slide_size()
    base.parts.clear()
    base.shape_id = 1

    base.textbox("Title", 0.48, 0.16, 12.50, 0.32, "Workflow-conditioned RSD pipeline, with accurate ViT token flow", 15.5, COLORS["ink"], True, "ctr")
    base.textbox(
        "Subtitle",
        0.72,
        0.56,
        12.00,
        0.20,
        "Key correction: patch tokens and workflow tokens are prepended/concatenated along the token axis; '+' is reserved for positional embeddings.",
        7.4,
        COLORS["muted"],
        False,
        "ctr",
    )

    # A. Visual encoder.
    base.textbox("A label", 0.44, 0.98, 2.10, 0.18, "A. Per-frame visual encoding", 9.0, COLORS["ink"], True)
    frame_strip(0.48, 1.36)
    base.arrow(2.24, 2.15, 2.64, 2.15, COLORS["edge"])
    vit_encoder_detail(2.78, 1.02, 8.72, 1.82)
    base.arrow(11.60, 2.15, 11.92, 2.15, COLORS["teal"])
    frame_feature_matrix(12.00, 1.12, 1.18, 1.62)

    # B. Workflow token construction.
    base.textbox("B label", 0.44, 3.16, 2.65, 0.18, "B. Workflow-token construction", 9.0, COLORS["ink"], True)
    base.shape("Workflow band", "roundRect", 0.44, 3.42, 12.70, 1.62, None, COLORS["teal"], 1.0)
    phase_sequence(0.72, 3.66, 1.22, 1.08, "Full phase sequence", prefix=False)
    base.arrow(1.98, 4.20, 2.28, 4.20, COLORS["purple"])
    bigrams(2.34, 3.66, 1.12, 1.08)
    base.arrow(3.50, 4.20, 3.80, 4.20, COLORS["edge"])
    artifact_pipeline(3.86, 3.66, 1.82, 1.08)
    base.arrow(5.72, 4.20, 6.02, 4.20, COLORS["edge"])
    phase_sequence(6.08, 3.66, 1.12, 1.08, "Prefix phases", prefix=True)
    base.arrow(7.24, 4.20, 7.54, 4.20, COLORS["teal"])
    base.shape("Posterior", "roundRect", 7.60, 3.66, 1.02, 1.08, COLORS["teal_light"], COLORS["teal"], 0.75)
    base.textbox("Posterior title", 7.70, 3.80, 0.82, 0.13, "posterior q", 6.3, COLORS["teal"], True, "ctr")
    for i, bh in enumerate([0.18, 0.36, 0.12, 0.45, 0.22]):
        base.shape("q bar", "rect", 7.82 + i * 0.11, 4.32 - bh, 0.06, bh, COLORS["teal"] if i == 3 else "99F6E4", COLORS["teal"], 0.12)
    base.arrow(8.66, 4.20, 8.96, 4.20, COLORS["teal"])
    workflow_token_box(9.02, 3.66, 1.62, 1.08)
    base.arrow(10.70, 4.20, 11.08, 5.54, COLORS["teal"])
    base.textbox("Artifact note", 3.80, 3.45, 4.18, 0.12, "fit offline on training corpus; reused for oracle and causal paths", 5.3, COLORS["teal"], True, "ctr")
    base.textbox("Causal note", 6.02, 4.84, 2.80, 0.11, "causal path uses predicted prefix phases, not full-case labels", 5.0, COLORS["muted"], False, "ctr")

    # C. Temporal model and heads.
    base.textbox("C label", 0.44, 5.36, 2.72, 0.18, "C. Temporal prediction model", 9.0, COLORS["ink"], True)
    conditioning_settings(0.54, 5.70, 2.35, 1.42)
    base.arrow(3.00, 6.40, 3.34, 6.40, COLORS["edge"])
    frame_feature_matrix(3.40, 5.72, 1.18, 1.38)
    base.arrow(4.64, 6.40, 5.00, 6.40, COLORS["orange"])
    workflow_token_box(5.06, 5.72, 1.48, 1.38)
    base.arrow(6.60, 6.40, 6.94, 6.40, COLORS["orange"])
    sequence_stack(7.00, 5.58, 1.74, 1.66)
    base.arrow(8.80, 6.40, 9.14, 6.40, COLORS["edge"])
    hta_and_heads(9.20, 5.58, 1.62, 1.66)
    base.arrow(10.88, 6.40, 11.22, 6.40, COLORS["edge"])
    heads(11.28, 5.58, 1.86, 1.66)

    base.line("Footer rule", 0.46, 7.78, 13.12, 7.78, "E5E7EB", 0.6)
    base.textbox("Footer", 0.90, 7.91, 11.90, 0.12, "Notation: [a ; b] means vertical stack / token-axis concatenation. Elementwise '+' is used only for positional embeddings.", 6.5, COLORS["muted"], False, "ctr")

    xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<p:cSld>"
        '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>'
        "<p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        "<p:grpSpPr/>"
        f"{''.join(base.parts)}"
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
    )
    return xml.encode("utf-8")


def build_rels_xml() -> bytes:
    return (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout7.xml"/>'
        "</Relationships>"
    ).encode("utf-8")


def main() -> None:
    set_slide_size()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(base.TEMPLATE, "r") as zin, ZipFile(OUT, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in {"ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels"}:
                continue
            data = zin.read(item.filename)
            if item.filename == "ppt/presentation.xml":
                data = base.update_presentation_size(data)
            zout.writestr(item, data)
        zout.writestr("ppt/slides/slide1.xml", build_slide_xml())
        zout.writestr("ppt/slides/_rels/slide1.xml.rels", build_rels_xml())

    for dest in (SUB_FIG, FINAL_FIG):
        if dest.exists():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(OUT, dest / OUT.name)

    print(OUT)


if __name__ == "__main__":
    main()

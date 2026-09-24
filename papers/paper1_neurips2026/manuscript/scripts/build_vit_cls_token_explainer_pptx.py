"""Build an editable PPTX explainer for the ViT [CLS] token.

Output:
    paper/figures/fig_vit_cls_token_explainer.pptx
    paper/figures/fig_vit_cls_token_explainer_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/fig_vit_cls_token_explainer.pptx"
EDITABLE_OUT = ROOT / "figures/fig_vit_cls_token_explainer_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

COLORS = {
    **base.COLORS,
    "orange": "D97706",
    "orange_light": "FFF7ED",
    "purple": "7C3AED",
    "purple_light": "F5F3FF",
    "teal": "0F766E",
    "teal_light": "ECFDF5",
    "red": "DC2626",
    "red_light": "FEF2F2",
}


def token(x: float, y: float, text: str, *, cls: bool = False, w: float = 0.58) -> None:
    if cls:
        base.shape("CLS token", "roundRect", x, y, w, 0.36, COLORS["orange_light"], COLORS["orange"], 1.0, text, 8.4, COLORS["orange"], True)
    else:
        base.shape("Patch token", "roundRect", x, y, w, 0.36, COLORS["blue_frozen"], COLORS["blue_frozen_edge"], 0.8, text, 8.0, COLORS["ink"])


def small_patch_grid(x: float, y: float) -> None:
    colors = ["6B2C23", "A64E3F", "3D1F1B", "1B1210", "CF7A6A", "754034", "4A2422", "9C5A50", "E3A093", "884B43", "6C3736", "B05F57", "B96D62", "6D403B", "8A4747", "BF6B62"]
    size = 0.22
    gap = 0.035
    for row in range(4):
        for col in range(4):
            idx = row * 4 + col
            base.shape("Image patch", "rect", x + col * (size + gap), y + row * (size + gap), size, size, colors[idx], "FFFFFF", 0.5)
    base.shape("Patch grid outline", "rect", x - 0.03, y - 0.03, 4 * size + 3 * gap + 0.06, 4 * size + 3 * gap + 0.06, None, COLORS["edge"], 0.8)
    base.textbox("Patch grid label", x - 0.10, y + 1.05, 1.15, 0.16, "image patches", 7.4, COLORS["muted"], False, "ctr")


def token_row(x: float, y: float, *, include_cls: bool, prime: bool = False) -> None:
    labels = ["p1", "p2", "p3", "...", "p196"]
    if prime:
        labels = ["p1'", "p2'", "p3'", "...", "p196'"]
    cur = x
    if include_cls:
        token(cur, y, "[CLS]'" if prime else "[CLS]", cls=True, w=0.70)
        cur += 0.84
    for label in labels:
        token(cur, y, label, w=0.55 if label != "..." else 0.42)
        cur += 0.68 if label != "..." else 0.55


def compact_token_row(x: float, y: float, *, prime: bool = False) -> None:
    cls_label = "[CLS]'" if prime else "[CLS]"
    patch_labels = ["p1'", "p2'", "...", "p196'"] if prime else ["p1", "p2", "...", "p196"]
    token(x, y, cls_label, cls=True, w=0.58)
    cur = x + 0.78
    for label in patch_labels:
        token(cur, y, label, w=0.46 if label != "..." else 0.38)
        cur += 0.60 if label != "..." else 0.50


def attention_fan(x: float, y: float) -> None:
    # Lines from the CLS token into representative patch tokens inside attention.
    cls_c = (x + 0.29, y + 0.18)
    for end_x in [x + 1.02, x + 1.63, x + 2.15, x + 2.72]:
        base.line("Attention line", cls_c[0], cls_c[1], end_x, y + 0.18, COLORS["orange"], 0.85, False)
    base.shape("Attention halo", "roundRect", x - 0.11, y - 0.16, 3.30, 0.70, None, COLORS["orange"], 0.8, dash="dash")


def matrix_cell(
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    fill: str,
    stroke: str,
    *,
    color: str = COLORS["ink"],
    bold: bool = False,
    size: float = 6.4,
) -> None:
    base.shape("Matrix cell", "rect", x, y, w, h, fill, stroke, 0.45, text, size, color, bold)


def draw_token_matrix(x: float, y: float) -> None:
    base.textbox("Token matrix title", x, y - 0.34, 2.70, 0.18, "Input sequence to ViT block", 9.7, COLORS["ink"], True, "ctr")
    base.textbox("Token matrix subtitle", x, y - 0.12, 2.70, 0.16, "X has 197 rows x 768 features", 6.8, COLORS["muted"], False, "ctr")

    row_h = 0.28
    label_w = 0.54
    cell_w = 0.32
    cols = ["d1", "d2", "...", "d768"]
    rows = [("[CLS]", True), ("p1", False), ("p2", False), ("...", False), ("p196", False)]

    for c, label in enumerate(["token"] + cols):
        w = label_w if c == 0 else cell_w
        xx = x if c == 0 else x + label_w + (c - 1) * cell_w
        matrix_cell(xx, y, w, row_h, label, COLORS["gray_light"], COLORS["border"], size=5.5, bold=True)

    for r, (label, is_cls) in enumerate(rows, start=1):
        yy = y + r * row_h
        fill = COLORS["orange_light"] if is_cls else COLORS["blue_frozen"]
        stroke = COLORS["orange"] if is_cls else COLORS["blue_frozen_edge"]
        text_color = COLORS["orange"] if is_cls else COLORS["ink"]
        matrix_cell(x, yy, label_w, row_h, label, fill, stroke, color=text_color, bold=is_cls, size=6.1)
        for c in range(4):
            txt = "..." if c == 2 else ""
            matrix_cell(x + label_w + c * cell_w, yy, cell_w, row_h, txt, fill, stroke, color=text_color, bold=is_cls, size=5.6)

    base.shape("Row 0 highlight", "roundRect", x - 0.05, y + row_h - 0.03, label_w + 4 * cell_w + 0.10, row_h + 0.06, None, COLORS["orange"], 1.1, dash="dash")
    base.textbox("Row 0 note", x - 0.06, y + 1.84, 2.30, 0.18, "row 0 is the CLS token", 6.9, COLORS["orange"], True, "ctr")


def draw_attention_matrix(x: float, y: float) -> None:
    base.textbox("Attention title", x - 0.10, y - 0.38, 2.95, 0.20, "Inside self-attention", 9.7, COLORS["ink"], True, "ctr")
    base.textbox("Attention formula", x - 0.10, y - 0.14, 2.95, 0.16, "A = softmax(QK^T / sqrt(d))", 6.7, COLORS["muted"], False, "ctr")

    labels = ["CLS", "p1", "p2", "...", "p196"]
    vals = [
        ["0.08", "0.21", "0.04", "...", "0.12"],
        ["", "", "", "", ""],
        ["", "", "", "", ""],
        ["", "", "", "", ""],
        ["", "", "", "", ""],
    ]
    cell = 0.30
    label_w = 0.43
    for c, label in enumerate([""] + labels):
        xx = x if c == 0 else x + label_w + (c - 1) * cell
        w = label_w if c == 0 else cell
        matrix_cell(xx, y, w, cell, label, COLORS["gray_light"], COLORS["border"], size=5.4, bold=True)
    for r, label in enumerate(labels):
        yy = y + (r + 1) * cell
        is_cls = r == 0
        row_fill = COLORS["orange_light"] if is_cls else COLORS["white"]
        matrix_cell(x, yy, label_w, cell, label, row_fill, COLORS["orange"] if is_cls else COLORS["border"], color=COLORS["orange"] if is_cls else COLORS["ink"], bold=is_cls, size=5.5)
        for c in range(5):
            matrix_cell(
                x + label_w + c * cell,
                yy,
                cell,
                cell,
                vals[r][c],
                row_fill,
                COLORS["orange"] if is_cls else COLORS["border"],
                color=COLORS["orange"] if is_cls else COLORS["muted"],
                bold=is_cls,
                size=5.2,
            )

    base.shape("CLS attention row highlight", "roundRect", x - 0.04, y + cell - 0.03, label_w + 5 * cell + 0.08, cell + 0.06, None, COLORS["orange"], 1.2, dash="dash")
    base.textbox("CLS row note", x - 0.06, y + 1.98, 2.35, 0.34, "CLS row = how much row 0\nreads from each token", 6.7, COLORS["orange"], True, "ctr")


def draw_cls_update_formula(x: float, y: float) -> None:
    base.shape("Formula box", "roundRect", x, y, 2.60, 0.96, COLORS["orange_light"], COLORS["orange"], 0.9)
    base.textbox("Formula title", x + 0.14, y + 0.13, 2.32, 0.18, "CLS is updated by attention", 8.4, COLORS["orange"], True, "ctr")
    base.textbox("Formula body", x + 0.12, y + 0.38, 2.36, 0.18, "CLS_next = sum_j A[CLS,j] V_j", 7.3, COLORS["ink"], True, "ctr")
    base.textbox("Formula note", x + 0.12, y + 0.64, 2.36, 0.18, "+ residual + MLP inside each block", 6.6, COLORS["muted"], False, "ctr")


def draw_block_stack(x: float, y: float) -> None:
    base.textbox("Repeat title", x - 0.08, y - 0.36, 2.08, 0.20, "Repeat 12 times", 9.4, COLORS["ink"], True, "ctr")
    for i, label in enumerate(["Block 1", "Block 2", "...", "Block 12"]):
        fill = COLORS["blue"] if i == 3 else COLORS["blue_frozen"]
        stroke = COLORS["blue_dark"] if i == 3 else COLORS["blue_frozen_edge"]
        text_color = COLORS["white"] if i == 3 else COLORS["ink"]
        base.shape("Mini ViT block", "roundRect", x, y + i * 0.34, 1.90, 0.23, fill, stroke, 0.6, label, 6.4, text_color, i == 3)
        if i < 3:
            base.arrow(x + 0.95, y + i * 0.34 + 0.24, x + 0.95, y + (i + 1) * 0.34 - 0.03, COLORS["edge"])
    base.textbox("Repeat note", x - 0.05, y + 1.50, 2.00, 0.32, "The CLS row is refined\nat every layer.", 6.8, COLORS["muted"], False, "ctr")


def draw_output_readout(x: float, y: float) -> None:
    base.textbox("Readout title", x - 0.20, y - 0.38, 2.72, 0.20, "Readout after final block", 9.7, COLORS["ink"], True, "ctr")
    base.shape("Final matrix", "roundRect", x, y, 1.10, 1.46, COLORS["gray_light"], COLORS["edge"], 0.9)
    row_h = 0.24
    rows = [("[CLS]^12", True), ("p1^12", False), ("p2^12", False), ("...", False), ("p196^12", False)]
    for r, (label, is_cls) in enumerate(rows):
        yy = y + 0.12 + r * row_h
        fill = COLORS["orange_light"] if is_cls else COLORS["blue_frozen"]
        stroke = COLORS["orange"] if is_cls else COLORS["blue_frozen_edge"]
        color = COLORS["orange"] if is_cls else COLORS["ink"]
        base.shape("Final token row", "roundRect", x + 0.12, yy, 0.86, 0.18, fill, stroke, 0.45, label, 5.5, color, is_cls)
    base.shape("Final row highlight", "roundRect", x + 0.07, y + 0.08, 0.96, 0.28, None, COLORS["orange"], 1.1, dash="dash")
    base.arrow(x + 1.18, y + 0.22, x + 1.75, y + 0.22, COLORS["teal"])
    base.shape("Feature vector", "roundRect", x + 1.88, y - 0.04, 0.40, 1.28, COLORS["green_light"], COLORS["gray"], 1.0)
    for yy in [y + 0.12, y + 0.36, y + 0.60, y + 0.84, y + 1.08]:
        base.shape("Feature dot", "ellipse", x + 2.03, yy, 0.10, 0.10, COLORS["green"], COLORS["green"], 0.2)
    base.textbox("Feature label", x + 1.50, y + 1.38, 1.25, 0.34, "768-d\nframe feature", 9.3, COLORS["ink"], True, "ctr")
    base.textbox("Patch discard note", x - 0.05, y + 1.82, 2.55, 0.18, "patch rows still exist, but row 0 is used", 6.6, COLORS["muted"], False, "ctr")


def build_slide_xml() -> bytes:
    base.parts.clear()
    base.shape_id = 1

    base.textbox("Title", 0.36, 0.18, 7.80, 0.34, "What does \"ViT blocks -> [CLS] output\" mean?", 16.5, COLORS["ink"], True)
    base.textbox(
        "Subtitle",
        0.36,
        0.56,
        10.60,
        0.22,
        "The [CLS] token is row 0 of the token matrix. It is updated by self-attention in every block, then row 0 is read as the frame feature.",
        9.2,
        COLORS["muted"],
    )

    # Main explanatory flow.
    draw_token_matrix(0.50, 1.36)
    base.arrow(2.94, 2.28, 3.38, 2.28, COLORS["edge"])
    draw_attention_matrix(3.54, 1.38)
    base.arrow(5.76, 2.28, 6.22, 2.28, COLORS["edge"])
    draw_cls_update_formula(6.08, 1.68)
    base.arrow(8.70, 2.28, 8.80, 2.28, COLORS["edge"])
    draw_block_stack(8.82, 1.48)
    base.arrow(10.62, 2.28, 10.74, 2.28, COLORS["edge"])
    draw_output_readout(10.78, 1.44)

    # Clarifying notes.
    base.shape("Input prepend note", "roundRect", 0.52, 3.70, 2.78, 0.58, COLORS["orange_light"], COLORS["orange"], 0.8)
    base.textbox("Input prepend note title", 0.66, 3.82, 2.50, 0.16, "Concatenation happens here only", 8.1, COLORS["orange"], True, "ctr")
    base.textbox("Input prepend note body", 0.66, 4.04, 2.50, 0.14, "[CLS] is prepended to patch tokens before block 1.", 6.3, COLORS["ink"], False, "ctr")

    base.shape("Not output concat", "roundRect", 3.82, 3.70, 2.66, 0.58, COLORS["red_light"], COLORS["red"], 0.8)
    base.textbox("Not output concat title", 3.96, 3.82, 2.38, 0.16, "Not concatenated after ViT", 8.1, COLORS["red"], True, "ctr")
    base.textbox("Not output concat body", 3.96, 4.04, 2.38, 0.14, "The final CLS row already contains mixed information.", 6.3, COLORS["ink"], False, "ctr")

    base.shape("Plain English", "roundRect", 6.94, 3.70, 5.70, 0.58, COLORS["teal_light"], COLORS["teal"], 0.8)
    base.textbox("Plain English title", 7.15, 3.82, 5.28, 0.16, "Plain English", 8.1, COLORS["teal"], True, "ctr")
    base.textbox("Plain English body", 7.15, 4.04, 5.28, 0.14, "The CLS token is a learnable summary slot that repeatedly looks at image patches through attention.", 6.5, COLORS["ink"], False, "ctr")

    base.line("Footer rule", 0.36, 4.58, 13.10, 4.58, "E5E7EB", 0.6)
    base.textbox(
        "Footer",
        0.90,
        4.68,
        11.90,
        0.14,
        "In code, timm's ViT handles the image-level [CLS] internally; your temporal workflow token is a separate CLS-style token later in HTA.",
        6.7,
        COLORS["muted"],
        False,
        "ctr",
    )

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

    shutil.copy2(OUT, EDITABLE_OUT)
    for dest in (SUB_FIG, FINAL_FIG):
        if dest.exists():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(OUT, dest / OUT.name)
            shutil.copy2(EDITABLE_OUT, dest / EDITABLE_OUT.name)

    print(OUT)
    print(EDITABLE_OUT)


if __name__ == "__main__":
    main()

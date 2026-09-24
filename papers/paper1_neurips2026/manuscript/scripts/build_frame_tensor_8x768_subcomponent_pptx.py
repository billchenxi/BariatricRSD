"""Build an editable PPTX subcomponent for the 8 x 768 frame tensor.

The figure is a compact, copyable PowerPoint component that clarifies that the
visual encoder emits one 768-d feature vector per sampled frame. The resulting
clip tensor has 8 temporal rows and 768 feature columns.

Output:
    paper/figures/fig_frame_tensor_8x768_subcomponent_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/fig_frame_tensor_8x768_subcomponent_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

SLIDE_W = 7.20
SLIDE_H = 4.70

COLORS = {
    **base.COLORS,
    "blue_light": "EFF6FF",
    "blue_lighter": "F8FBFF",
    "blue_mid": "93C5FD",
    "green": "0F766E",
    "green_light": "ECFDF5",
    "purple": "7C3AED",
    "purple_light": "F5F3FF",
    "orange": "D97706",
    "orange_light": "FFF7ED",
    "red": "DC2626",
}


def set_slide_size() -> None:
    base.SLIDE_W = SLIDE_W
    base.SLIDE_H = SLIDE_H


def add_column_labels(matrix_x: float, matrix_y: float, matrix_w: float) -> None:
    cols = [0.22, 0.52, 0.82, 1.70, matrix_w - 0.88, matrix_w - 0.58, matrix_w - 0.28]
    labels = ["1", "2", "3", "...", "766", "767", "768"]
    for xx, label in zip(cols, labels):
        base.textbox(
            "Column label",
            matrix_x + xx - 0.11,
            matrix_y - 0.28,
            0.22,
            0.12,
            label,
            6.0,
            COLORS["muted"],
            label in {"1", "768"},
            "ctr",
        )
    base.textbox(
        "Column axis label",
        matrix_x + 0.70,
        matrix_y - 0.53,
        matrix_w - 1.40,
        0.18,
        "feature dimensions",
        8.2,
        COLORS["blue"],
        True,
        "ctr",
    )


def add_row_vector(row_idx: int, x: float, y: float, w: float, h: float) -> None:
    fill = COLORS["blue_lighter"] if row_idx % 2 == 0 else COLORS["blue_light"]
    base.shape("Frame feature row", "rect", x, y, w, h, fill, COLORS["blue_mid"], 0.55)
    base.textbox(
        "Frame row label",
        x - 0.58,
        y + 0.09,
        0.42,
        0.14,
        f"f_{row_idx + 1}",
        7.2,
        COLORS["ink"],
        True,
        "r",
    )
    base.textbox(
        "Frame time label",
        x - 0.16,
        y + 0.09,
        0.13,
        0.14,
        f"t{row_idx + 1}",
        5.6,
        COLORS["muted"],
        False,
        "r",
    )

    left_centers = [x + 0.22, x + 0.52, x + 0.82]
    right_centers = [x + w - 0.88, x + w - 0.58, x + w - 0.28]
    for j, cx in enumerate(left_centers + right_centers):
        color = COLORS["blue"] if j not in {2, 3} else COLORS["green"]
        base.shape("Feature value", "ellipse", cx - 0.045, y + h / 2 - 0.045, 0.09, 0.09, color, color, 0.2)
    base.textbox("Feature ellipsis", x + w / 2 - 0.18, y + 0.07, 0.36, 0.16, "...", 10.5, COLORS["muted"], True, "ctr")


def add_matrix(x: float, y: float, w: float, h: float) -> None:
    row_h = h / 8
    add_column_labels(x, y, w)
    base.shape("Tensor outer border", "rect", x, y, w, h, None, COLORS["blue"], 1.4)
    for i in range(8):
        add_row_vector(i, x, y + i * row_h, w, row_h)
    base.shape("Tensor outer border top", "rect", x, y, w, h, None, COLORS["blue"], 1.55)

    # Left temporal bracket.
    bracket_x = x - 0.82
    base.line("Temporal bracket", bracket_x, y, bracket_x, y + h, COLORS["blue"], 1.25)
    base.line("Temporal bracket cap", bracket_x, y, bracket_x + 0.16, y, COLORS["blue"], 1.25)
    base.line("Temporal bracket cap", bracket_x, y + h, bracket_x + 0.16, y + h, COLORS["blue"], 1.25)
    base.textbox("Temporal label", bracket_x - 0.35, y + h / 2 - 0.18, 0.28, 0.36, "8\nframes", 7.4, COLORS["blue"], True, "ctr")

    # Bottom feature bracket.
    bracket_y = y + h + 0.30
    base.line("Feature bracket", x, bracket_y, x + w, bracket_y, COLORS["blue"], 1.25)
    base.line("Feature bracket cap", x, bracket_y - 0.12, x, bracket_y, COLORS["blue"], 1.25)
    base.line("Feature bracket cap", x + w, bracket_y - 0.12, x + w, bracket_y, COLORS["blue"], 1.25)
    base.textbox("Feature width label", x + 0.92, bracket_y + 0.08, w - 1.84, 0.18, "768 feature channels", 8.2, COLORS["blue"], True, "ctr")


def add_formula_panel(x: float, y: float, w: float, h: float) -> None:
    base.shape("Formula panel", "roundRect", x, y, w, h, COLORS["green_light"], COLORS["green"], 0.85)
    base.textbox("Formula title", x + 0.16, y + 0.16, w - 0.32, 0.18, "What each row means", 8.0, COLORS["green"], True, "ctr")
    base.textbox(
        "Formula one",
        x + 0.18,
        y + 0.55,
        w - 0.36,
        0.20,
        "f_i = ViT [CLS](frame_i)",
        6.5,
        COLORS["ink"],
        True,
        "ctr",
    )
    base.textbox(
        "Formula two",
        x + 0.18,
        y + 0.85,
        w - 0.36,
        0.20,
        "f_i in R^768",
        6.5,
        COLORS["ink"],
        True,
        "ctr",
    )
    base.textbox(
        "Formula three",
        x + 0.18,
        y + 1.15,
        w - 0.36,
        0.28,
        "F = stack(f_1, ..., f_8)\nin R^(8 x 768)",
        6.4,
        COLORS["blue"],
        True,
        "ctr",
    )


def build_slide_xml() -> bytes:
    set_slide_size()
    base.parts.clear()
    base.shape_id = 1

    base.shape("Background", "rect", 0, 0, SLIDE_W, SLIDE_H, "FFFFFF", no_line=True)
    base.textbox("Title", 0.32, 0.22, 6.56, 0.30, "8 x 768 frame tensor F", 15.2, COLORS["blue"], True, "ctr")
    base.textbox(
        "Subtitle",
        0.82,
        0.58,
        5.58,
        0.18,
        "F in R^(8 x 768): 8 sampled frames, each represented by one 768-d ViT [CLS] feature vector",
        7.2,
        COLORS["muted"],
        False,
        "ctr",
    )

    add_matrix(1.32, 1.32, 3.55, 2.28)
    add_formula_panel(5.18, 1.44, 1.48, 1.78)

    base.shape("Clarifier", "roundRect", 0.84, 4.20, 5.52, 0.30, COLORS["orange_light"], COLORS["orange"], 0.7)
    base.textbox(
        "Clarifier text",
        1.00,
        4.28,
        5.20,
        0.10,
        "Not pixels or patches: rows are frame embeddings; columns are learned feature dimensions.",
        5.5,
        COLORS["orange"],
        True,
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

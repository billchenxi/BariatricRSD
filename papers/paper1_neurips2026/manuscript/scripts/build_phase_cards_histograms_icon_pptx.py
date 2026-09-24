"""Build an editable PPTX icon for phase labels with per-step histograms.

This recreates the supplied PNG concept as native PowerPoint objects: four
phase cards (A, B, B, C) and a small editable histogram under each card.

Output:
    paper/figures/icon_phase_cards_histograms_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/icon_phase_cards_histograms_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

SLIDE_W = 3.70
SLIDE_H = 1.78

COLORS = {
    **base.COLORS,
    "pink": "F472B6",
    "pink_light": "FBCFE8",
    "orange": "F59E0B",
    "orange_light": "FED7AA",
    "yellow": "FDE047",
    "yellow_light": "FEF9C3",
    "brown": "B45309",
    "axis": "111827",
    "bar": "6B7280",
    "bar_light": "D1D5DB",
}


def set_slide_size() -> None:
    base.SLIDE_W = SLIDE_W
    base.SLIDE_H = SLIDE_H


def card(x: float, y: float, w: float, h: float, label: str, fill: str, stroke: str) -> None:
    base.shape("Phase card", "roundRect", x + 0.035, y + 0.035, w, h, "000000", "000000", 0.1)
    base.shape("Phase card", "roundRect", x, y, w, h, fill, stroke, 1.05)
    base.textbox("Phase label", x, y + 0.14, w, 0.26, label, 17.0, COLORS["ink"], True, "ctr")


def histogram(x: float, y: float, w: float, h: float, values: list[float]) -> None:
    axis_x = x + 0.12
    axis_y = y + h - 0.14
    base.line("Histogram x-axis", axis_x, axis_y, x + w - 0.08, axis_y, COLORS["axis"], 0.75)
    base.line("Histogram y-axis", axis_x, axis_y, axis_x, y + 0.08, COLORS["axis"], 0.75)

    bar_gap = 0.035
    bar_w = (w - 0.30 - bar_gap * (len(values) - 1)) / len(values)
    for i, value in enumerate(values):
        bh = value * (h - 0.26)
        bx = axis_x + 0.05 + i * (bar_w + bar_gap)
        by = axis_y - bh
        fill = COLORS["bar"] if i in {0, 2} else COLORS["bar_light"]
        base.shape("Histogram bar", "rect", bx, by, bar_w, bh, fill, COLORS["axis"], 0.25)


def build_slide_xml() -> bytes:
    set_slide_size()
    base.parts.clear()
    base.shape_id = 1

    base.shape("Background", "rect", 0, 0, SLIDE_W, SLIDE_H, "FFFFFF", no_line=True)

    labels = ["A", "B", "B", "C"]
    fills = [COLORS["pink_light"], COLORS["orange_light"], COLORS["orange_light"], COLORS["yellow_light"]]
    strokes = [COLORS["pink"], COLORS["orange"], COLORS["brown"], COLORS["yellow"]]
    hists = [
        [0.82, 0.66, 0.54, 0.38, 0.25],
        [0.18, 0.28, 0.34, 0.46, 0.55],
        [0.62, 0.20, 0.15, 0.28, 0.34],
        [0.76, 0.88, 0.48, 0.26, 0.18],
    ]

    card_w = 0.82
    card_h = 0.58
    gap = 0.02
    x0 = 0.20
    card_y = 0.20
    hist_y = 1.05
    for i, label in enumerate(labels):
        x = x0 + i * (card_w + gap)
        card(x, card_y, card_w, card_h, label, fills[i], strokes[i])
        histogram(x + 0.08, hist_y, card_w - 0.16, 0.52, hists[i])

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

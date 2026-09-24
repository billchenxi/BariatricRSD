"""Build a small editable PPTX PCA icon.

The icon is intended for reuse inside workflow-clustering pipeline figures.
Every visible element is a native PowerPoint shape: points, axes, projection
guides, and the highlighted principal-component direction.

Output:
    paper/figures/icon_pca_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/icon_pca_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

SLIDE_W = 2.45
SLIDE_H = 2.20

COLORS = {
    **base.COLORS,
    "blue_light": "EFF6FF",
    "blue_mid": "60A5FA",
    "teal": "0F766E",
    "teal_light": "CCFBF1",
    "orange": "D97706",
    "orange_light": "FFF7ED",
    "purple": "7C3AED",
    "purple_light": "F5F3FF",
}


def set_slide_size() -> None:
    base.SLIDE_W = SLIDE_W
    base.SLIDE_H = SLIDE_H


def point(x: float, y: float, fill: str = COLORS["blue"]) -> None:
    base.shape("PCA point", "ellipse", x - 0.045, y - 0.045, 0.09, 0.09, fill, fill, 0.2)


def build_slide_xml() -> bytes:
    set_slide_size()
    base.parts.clear()
    base.shape_id = 1

    base.shape("Background", "rect", 0, 0, SLIDE_W, SLIDE_H, "FFFFFF", no_line=True)
    base.shape("Icon frame", "roundRect", 0.08, 0.08, 2.29, 2.04, "FFFFFF", COLORS["border"], 0.75)
    base.textbox("PCA label", 0.18, 0.18, 0.68, 0.20, "PCA", 10.8, COLORS["ink"], True, "l")

    # Coordinate axes.
    base.line("x axis", 0.42, 1.66, 2.02, 1.66, COLORS["muted"], 0.65, arrow=True)
    base.line("y axis", 0.42, 1.66, 0.42, 0.48, COLORS["muted"], 0.65, arrow=True)

    # Original data cloud.
    points = [
        (0.62, 1.43, COLORS["blue"]),
        (0.75, 1.24, COLORS["blue"]),
        (0.90, 1.18, COLORS["blue"]),
        (1.05, 0.98, COLORS["teal"]),
        (1.20, 0.89, COLORS["blue"]),
        (1.34, 0.75, COLORS["teal"]),
        (1.51, 0.62, COLORS["blue"]),
        (1.65, 0.82, COLORS["blue"]),
        (1.80, 0.53, COLORS["blue"]),
    ]
    for px, py, fill in points:
        point(px, py, fill)

    # Projection guides toward the first principal component.
    guide_pairs = [
        ((0.75, 1.24), (0.83, 1.31)),
        ((1.05, 0.98), (1.13, 1.05)),
        ((1.34, 0.75), (1.43, 0.84)),
        ((1.65, 0.82), (1.53, 0.69)),
    ]
    for (x1, y1), (x2, y2) in guide_pairs:
        base.line("Projection guide", x1, y1, x2, y2, "CBD5E1", 0.45, dash="dash")

    # Principal component directions.
    base.line("PC2 direction", 1.28, 1.08, 0.92, 0.72, COLORS["teal"], 0.9, arrow=True, dash="dash")
    base.line("PC1 direction", 0.55, 1.50, 1.93, 0.45, COLORS["orange"], 1.85, arrow=True)
    base.textbox("PC1 label", 1.52, 0.29, 0.46, 0.16, "PC1", 6.2, COLORS["orange"], True, "ctr")
    base.textbox("PC2 label", 0.82, 0.56, 0.42, 0.14, "PC2", 5.4, COLORS["teal"], True, "ctr")

    base.shape("Reduced vector chip", "roundRect", 0.64, 1.82, 1.20, 0.18, COLORS["orange_light"], COLORS["orange"], 0.45)
    base.textbox("Reduced vector text", 0.72, 1.87, 1.04, 0.07, "rotate + keep main variance", 4.4, COLORS["orange"], True, "ctr")

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

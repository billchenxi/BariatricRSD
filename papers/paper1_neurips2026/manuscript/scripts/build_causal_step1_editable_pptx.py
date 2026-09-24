"""Build an editable PowerPoint version of the causal inference step-1 figure.

The surgical frame thumbnails remain images, but the diagram structure
(boxes, lanes, arrows, labels, bars, and callouts) is native PowerPoint XML.

Outputs:
    paper/figures_slides/fig_causal_step1_better_editable.pptx
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures/fig_vit_backbone.pptx"
OUT = ROOT / "figures_slides/fig_causal_step1_better_editable.pptx"
ASSETS = [
    ROOT / "figures_slides/assets/BBP12_00003439.jpg",
    ROOT / "figures_slides/assets/BBP12_00003444.jpg",
    ROOT / "figures_slides/assets/BBP12_00003449.jpg",
    ROOT / "figures_slides/assets/BBP12_00003454.jpg",
    ROOT / "figures_slides/assets/BBP12_00003459.jpg",
]

EMU_PER_IN = 914_400
shape_id = 1
parts: list[str] = []


def emu(value_in: float) -> str:
    return str(int(round(value_in * EMU_PER_IN)))


def font_size(pt: float) -> str:
    return str(int(round(pt * 100)))


def next_id() -> int:
    global shape_id
    shape_id += 1
    return shape_id


def fill_xml(color: str | None) -> str:
    if color is None:
        return "<a:noFill/>"
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def line_xml(
    color: str = "1F2937",
    width_pt: float = 1.0,
    dash: str | None = None,
    no_line: bool = False,
    arrow: bool = False,
) -> str:
    if no_line:
        return "<a:ln><a:noFill/></a:ln>"
    dash_xml = f'<a:prstDash val="{dash}"/>' if dash else ""
    arrow_xml = '<a:tailEnd type="triangle" w="med" h="med"/>' if arrow else ""
    width = int(round(width_pt * 12_700))
    return (
        f'<a:ln w="{width}">'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f"{dash_xml}{arrow_xml}</a:ln>"
    )


def text_body(
    text: str | list[str],
    font_pt: float = 14,
    color: str = "111827",
    bold: bool = False,
    align: str = "ctr",
    anchor: str = "ctr",
    margins: bool = True,
) -> str:
    lines = text.split("\n") if isinstance(text, str) else text
    bold_flag = "1" if bold else "0"
    margin_attrs = ' lIns="0" rIns="0" tIns="0" bIns="0"' if margins else ""
    paragraphs = []
    for line in lines:
        paragraphs.append(
            f'<a:p><a:pPr algn="{align}"/>'
            f'<a:r><a:rPr sz="{font_size(font_pt)}" b="{bold_flag}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="Arial"/></a:rPr>'
            f"<a:t>{escape(line)}</a:t></a:r></a:p>"
        )
    return (
        f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}"{margin_attrs}>'
        f"<a:spAutoFit/></a:bodyPr><a:lstStyle/>"
        f"{''.join(paragraphs)}</p:txBody>"
    )


def shape(
    name: str,
    prst: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str | None = None,
    line: str = "1F2937",
    line_pt: float = 1.0,
    text: str | list[str] | None = None,
    font_pt: float = 14,
    text_color: str = "111827",
    bold: bool = False,
    align: str = "ctr",
    anchor: str = "ctr",
    no_line: bool = False,
) -> None:
    sid = next_id()
    body = text_body(text, font_pt, text_color, bold, align, anchor) if text is not None else ""
    if text is None:
        body = '<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p/></p:txBody>'
    parts.append(
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        f"<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>"
        f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>'
        f"{fill_xml(fill)}{line_xml(line, line_pt, no_line=no_line)}</p:spPr>{body}</p:sp>"
    )


def textbox(
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str | list[str],
    font_pt: float = 14,
    color: str = "111827",
    bold: bool = False,
    align: str = "l",
) -> None:
    sid = next_id()
    parts.append(
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
        f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f"{text_body(text, font_pt, color, bold, align, 'ctr')}</p:sp>"
    )


def line(
    name: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = "1F2937",
    width_pt: float = 2.0,
    arrow: bool = False,
    dash: str | None = None,
) -> None:
    sid = next_id()
    flip_h = x2 < x1
    flip_v = y2 < y1
    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    flips = ""
    if flip_h:
        flips += ' flipH="1"'
    if flip_v:
        flips += ' flipV="1"'
    parts.append(
        f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        f"<p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr>"
        f'<a:xfrm{flips}><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
        f"{line_xml(color, width_pt, dash=dash, arrow=arrow)}</p:spPr></p:cxnSp>"
    )


def picture(name: str, rid: str, x: float, y: float, w: float, h: float, crop_tb: int = 14_300) -> None:
    sid = next_id()
    parts.append(
        f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
        f'<p:blipFill><a:blip r:embed="{rid}"/>'
        f'<a:srcRect t="{crop_tb}" b="{crop_tb}"/>'
        f"<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>"
        f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
    )


def add_arrow(x1: float, y1: float, x2: float, y2: float, color: str = "1F2937", dashed: bool = False) -> None:
    line("Arrow", x1, y1, x2, y2, color=color, width_pt=2.1, arrow=True, dash="dash" if dashed else None)


def add_block(x: float, y: float, w: float, h: float, fill: str, stroke: str, text: str, font_pt: float = 14) -> None:
    shape("Block", "roundRect", x, y, w, h, fill, stroke, 1.35, text, font_pt, "111827", True)


def build_slide_xml() -> str:
    # Background
    shape("Background", "rect", 0, 0, 13.333, 7.5, "FFFFFF", no_line=True)

    # Header
    textbox(
        "Title",
        0.48,
        0.25,
        12.0,
        0.35,
        "Causal inference step 1: get phase predictions without using workflow identity",
        20,
        "111827",
        True,
    )
    textbox(
        "Subtitle",
        0.48,
        0.62,
        11.6,
        0.28,
        "First pass uses a dummy workflow slot. The phase head reads visual-prefix features before workflow-token mixing.",
        11.5,
        "4B5563",
    )

    # Prefix frames
    textbox("Prefix label", 0.48, 0.96, 2.5, 0.24, "Observed prefix frames", 13, "111827", True)
    frame_x, frame_y, frame_w, frame_h, gap = 0.48, 1.24, 1.92, 1.10, 0.18
    for idx in range(5):
        x = frame_x + idx * (frame_w + gap)
        picture(f"BBP12 frame {idx + 1}", f"rId{idx + 2}", x, frame_y, frame_w, frame_h)
        shape("Frame outline", "rect", x, frame_y, frame_w, frame_h, None, "D1D5DB", 0.7)
    xt_x = frame_x + 4 * (frame_w + gap)
    shape("Current timestamp border", "rect", xt_x, frame_y, frame_w, frame_h, None, "F59E0B", 2.4)
    shape("xt badge", "rect", xt_x, frame_y, 0.46, 0.24, "000000", no_line=True)
    textbox("xt text", xt_x + 0.06, frame_y + 0.03, 0.35, 0.16, "x_t", 9.5, "FFFFFF", True, "ctr")
    textbox(
        "Prefix note",
        0.48,
        2.40,
        6.1,
        0.22,
        "Concrete MB140 / BBP12 prefix ending at the current timestamp.",
        9.2,
        "4B5563",
    )

    # Lanes
    shape("Phase lane", "roundRect", 0.48, 2.78, 12.05, 1.46, "ECFDF5", "A7F3D0", 0.8)
    textbox("Phase lane title", 0.70, 2.95, 4.0, 0.24, "A. Phase branch: visual features only", 10.8, "111827", True)
    shape("Temporal lane", "roundRect", 0.48, 4.52, 12.05, 1.92, "FAF5FF", "DDD6FE", 0.8)
    textbox(
        "Temporal lane title",
        0.70,
        4.69,
        6.5,
        0.24,
        "B. Temporal branch: dummy workflow token fills the slot for this first pass",
        10.8,
        "111827",
        True,
    )

    # Phase branch blocks
    y = 3.28
    h = 0.62
    add_block(0.72, y, 1.25, h, "DBEAFE", "2563EB", "prefix\nframes", 11.2)
    add_arrow(1.98, y + h / 2, 2.38, y + h / 2)
    add_block(2.46, y, 1.62, h, "DBEAFE", "2563EB", "visual encoder\nViT-B/16", 10.6)
    add_arrow(4.10, y + h / 2, 4.55, y + h / 2)
    add_block(4.64, y, 1.36, h, "F9FAFB", "1F2937", "frame\nfeatures", 11.2)
    add_arrow(6.03, y + h / 2, 6.47, y + h / 2, "059669")
    add_block(6.56, y, 1.30, h, "D1FAE5", "059669", "phase\nhead", 11.2)
    add_arrow(7.89, y + h / 2, 8.32, y + h / 2, "059669")
    add_block(8.41, y, 1.55, h, "D1FAE5", "059669", "phase\nprobabilities", 10.2)
    # Small bar chart
    line("Bar baseline", 10.22, 3.88, 11.15, 3.88, "4B5563", 1.0)
    for i, bh in enumerate([0.14, 0.28, 0.46, 0.70]):
        fill = "059669" if i == 3 else "D1FAE5"
        x = 10.28 + i * 0.24
        shape("Probability bar", "rect", x, 3.88 - bh, 0.14, bh, fill, "059669", 0.7)
    textbox("Argmax note", 10.08, 3.94, 1.35, 0.20, "argmax gives phase label", 7.8, "4B5563", False, "ctr")

    # Temporal branch blocks
    y2 = 5.16
    add_block(0.72, y2, 1.90, 0.64, "FEF3C7", "F59E0B", "placeholder cluster id\nz_dummy, e.g. 0", 9.5)
    add_arrow(2.65, y2 + 0.32, 3.09, y2 + 0.32, "F59E0B")
    add_block(3.18, y2, 1.55, 0.64, "FEF3C7", "F59E0B", "workflow token\nE[z_dummy]", 9.8)
    add_arrow(4.76, y2 + 0.32, 5.90, y2 + 0.32, "F59E0B")
    add_block(5.99, y2, 1.50, 0.64, "EDE9FE", "7C3AED", "HTA blocks\n[E[z_dummy], f_1:t]", 9.5)
    add_arrow(7.52, y2 + 0.32, 7.96, y2 + 0.32)
    add_block(8.05, y2, 1.48, 0.64, "F9FAFB", "1F2937", "temporal\nfeatures", 10.8)
    textbox("Temporal note", 7.82, 5.86, 2.0, 0.18, "used later after soft-token re-run", 7.4, "4B5563", False, "ctr")

    # Cross-lane annotation
    add_arrow(5.32, 3.90, 6.28, 5.16, "1F2937")
    textbox("Same features", 5.28, 4.42, 1.35, 0.20, "same frame features", 8.8, "4B5563", False, "ctr")
    line("Red dashed influence", 4.05, 5.14, 7.08, 3.92, "DC2626", 1.7, True, "dash")
    line("Red cross 1", 6.98, 4.10, 7.32, 4.44, "DC2626", 3.0)
    line("Red cross 2", 7.32, 4.10, 6.98, 4.44, "DC2626", 3.0)
    add_block(10.02, y2, 1.72, 0.64, "FEE2E2", "DC2626", "placeholder token\ndoes not affect phase", 9.2)

    # Footer
    textbox(
        "Footer",
        0.48,
        6.88,
        11.7,
        0.28,
        "Result of step 1: keep the phase probabilities from branch A; use them next to build the prefix phase sequence and infer the soft workflow token.",
        9.5,
        "4B5563",
    )

    return (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        "<p:grpSpPr/>"
        f"{''.join(parts)}"
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
    )


def build_rels() -> str:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout7.xml"/>'
    ]
    for idx in range(5):
        rels.append(
            f'<Relationship Id="rId{idx + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/causal_step1_frame{idx + 1}.jpeg"/>'
        )
    return (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels)}</Relationships>"
    )


def main() -> None:
    slide_xml = build_slide_xml().encode("utf-8")
    rels_xml = build_rels().encode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(TEMPLATE, "r") as zin, ZipFile(OUT, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in {"ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels"}:
                continue
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("ppt/slides/slide1.xml", slide_xml)
        zout.writestr("ppt/slides/_rels/slide1.xml.rels", rels_xml)
        for idx, asset in enumerate(ASSETS, start=1):
            zout.writestr(f"ppt/media/causal_step1_frame{idx}.jpeg", asset.read_bytes())

    print(OUT)


if __name__ == "__main__":
    main()

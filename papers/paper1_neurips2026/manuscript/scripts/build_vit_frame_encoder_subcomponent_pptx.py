"""Build a fully editable PowerPoint ViT frame-encoder subcomponent.

Every visible element is a native PowerPoint object. The surgical frame and
patch tiles are represented as vector mosaics of editable rectangle shapes,
so the output contains no full-slide image and no embedded picture objects.

Output:
    paper/figures/fig_vit_frame_encoder_subcomponent.pptx
    paper/figures/fig_vit_frame_encoder_subcomponent_editable.pptx
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
TEMPLATE = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures/fig_vit_backbone.pptx"
OUT = ROOT / "figures/fig_vit_frame_encoder_subcomponent.pptx"
EDITABLE_OUT = ROOT / "figures/fig_vit_frame_encoder_subcomponent_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

FRAME_DIR = (
    REPO
    / "lambda_mirror/extern/MultiBypass140/datasets/MultiBypass140"
    / "BernBypass70/frames/BBP12"
)
SLIDE_ASSET_DIR = ROOT / "figures_slides/assets"
FRAME_NAME = "BBP12_00003449.jpg"

EMU_PER_IN = 914_400
SLIDE_W = 13.60
SLIDE_H = 4.96

COLORS = {
    "ink": "111827",
    "muted": "4B5563",
    "edge": "334155",
    "blue": "1D4ED8",
    "blue_dark": "143880",
    "blue_frozen": "DCE6F2",
    "blue_frozen_edge": "9FB6CF",
    "blue_frozen_text": "3B6F9C",
    "green_light": "E8F3DC",
    "green": "75A65B",
    "gray": "64748B",
    "gray_light": "F1F5F9",
    "border": "D1D5DB",
    "white": "FFFFFF",
}

parts: list[str] = []
shape_id = 1


def frame_path() -> Path:
    local = FRAME_DIR / FRAME_NAME
    if local.exists():
        return local
    return SLIDE_ASSET_DIR / FRAME_NAME


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
    color: str = COLORS["edge"],
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
    font_pt: float = 10,
    color: str = COLORS["ink"],
    bold: bool = False,
    align: str = "ctr",
    anchor: str = "ctr",
) -> str:
    lines = text.split("\n") if isinstance(text, str) else text
    bold_flag = "1" if bold else "0"
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
        f'<p:txBody><a:bodyPr wrap="square" anchor="{anchor}" '
        'lIns="0" rIns="0" tIns="0" bIns="0"><a:spAutoFit/></a:bodyPr>'
        f"<a:lstStyle/>{''.join(paragraphs)}</p:txBody>"
    )


def shape(
    name: str,
    prst: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str | None = None,
    stroke: str = COLORS["edge"],
    stroke_pt: float = 0.9,
    text: str | list[str] | None = None,
    font_pt: float = 10,
    text_color: str = COLORS["ink"],
    bold: bool = False,
    align: str = "ctr",
    anchor: str = "ctr",
    no_line: bool = False,
    dash: str | None = None,
) -> None:
    sid = next_id()
    body = (
        text_body(text, font_pt, text_color, bold, align, anchor)
        if text is not None
        else '<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p/></p:txBody>'
    )
    parts.append(
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        f"<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>"
        f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/>'
        f'<a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>'
        f"{fill_xml(fill)}{line_xml(stroke, stroke_pt, dash=dash, no_line=no_line)}"
        f"</p:spPr>{body}</p:sp>"
    )


def textbox(
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str | list[str],
    font_pt: float = 10,
    color: str = COLORS["ink"],
    bold: bool = False,
    align: str = "l",
    anchor: str = "ctr",
) -> None:
    sid = next_id()
    parts.append(
        f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
        f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/>'
        f'<a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f"{text_body(text, font_pt, color, bold, align, anchor)}</p:sp>"
    )


def line(
    name: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = COLORS["edge"],
    width_pt: float = 1.15,
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
        f'<a:xfrm{flips}><a:off x="{emu(x)}" y="{emu(y)}"/>'
        f'<a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        '<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
        f"{line_xml(color, width_pt, dash=dash, arrow=arrow)}</p:spPr></p:cxnSp>"
    )


def arrow(x1: float, y1: float, x2: float, y2: float, color: str = COLORS["edge"]) -> None:
    line("Arrow", x1, y1, x2, y2, color, 1.35, True)


def picture(name: str, rid: str, x: float, y: float, w: float, h: float) -> None:
    sid = next_id()
    parts.append(
        f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{escape(name)}"/>'
        '<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
        f'<p:blipFill><a:blip r:embed="{rid}"/>'
        '<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>'
        f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/>'
        f'<a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
    )


def load_source_frame() -> Image.Image:
    path = frame_path()
    if not path.exists():
        raise FileNotFoundError(f"Missing source frame: {path}")
    return Image.open(path).convert("RGB")


def rgb_hex(pixel: tuple[int, int, int]) -> str:
    return f"{pixel[0]:02X}{pixel[1]:02X}{pixel[2]:02X}"


def draw_image_mosaic(
    img: Image.Image,
    x: float,
    y: float,
    w: float,
    h: float,
    cols: int,
    rows: int,
    *,
    name: str,
) -> None:
    thumb = ImageOps.fit(img, (cols, rows), method=Image.Resampling.BILINEAR)
    cell_w = w / cols
    cell_h = h / rows
    overlap = 0.005
    pixels = thumb.load()
    for row in range(rows):
        for col in range(cols):
            fill = rgb_hex(pixels[col, row])
            shape(
                name,
                "rect",
                x + col * cell_w,
                y + row * cell_h,
                cell_w + overlap,
                cell_h + overlap,
                fill,
                fill,
                0.1,
                no_line=True,
            )


def add_block(x: float, y: float, w: float, h: float, text: str, *, trainable: bool) -> None:
    if trainable:
        shape("ViT trainable block", "roundRect", x, y, w, h, COLORS["blue"], COLORS["blue_dark"], 0.65, text, 7.2, COLORS["white"], True)
    else:
        shape("ViT frozen block", "roundRect", x, y, w, h, COLORS["blue_frozen"], COLORS["blue_frozen_edge"], 0.65, text, 7.2, COLORS["ink"])


def draw_patch_grid(img: Image.Image, x: float, y: float, tile: float, gap: float) -> None:
    textbox("Patch label", x - 0.20, y - 0.50, 2.05, 0.28, "16 x 16 px patches", 14.0, COLORS["ink"], True, "ctr")
    square = ImageOps.fit(img, (512, 512), method=Image.Resampling.LANCZOS)
    patch_px = square.width // 4
    for row in range(4):
        for col in range(4):
            xx = x + col * (tile + gap)
            yy = y + row * (tile + gap)
            crop = square.crop((col * patch_px, row * patch_px, (col + 1) * patch_px, (row + 1) * patch_px))
            draw_image_mosaic(crop, xx, yy, tile, tile, 4, 4, name=f"Patch {row},{col} mosaic cell")
            shape("Patch tile border", "rect", xx, yy, tile, tile, None, COLORS["white"], 0.8)
    total = 4 * tile + 3 * gap
    shape("Patch grid border", "rect", x - 0.03, y - 0.03, total + 0.06, total + 0.06, None, COLORS["border"], 0.8)
    textbox("Patch ellipsis", x + total + 0.10, y + total - 0.42, 0.45, 0.25, "...", 20.0, COLORS["ink"], True, "ctr")


def draw_vit_stack(x: float, y: float, w: float, h: float) -> None:
    textbox("ViT title", x + 0.48, 0.76, 1.90, 0.30, "ViT-B/16", 19.0, COLORS["ink"], True, "ctr")
    textbox(
        "ViT subtitle",
        x - 0.12,
        1.10,
        3.10,
        0.20,
        "ImageNet-21k init; 12 transformer blocks",
        9.2,
        COLORS["muted"],
        False,
        "ctr",
    )
    shape("ViT stack container", "roundRect", x, y, w, h, None, COLORS["edge"], 1.0)

    block_x = x + 0.42
    block_w = w - 0.82
    block_h = 0.20
    gap = 0.052
    top = y + 0.34
    block_pos: dict[int, float] = {}
    for idx in range(12, 0, -1):
        yy = top + (12 - idx) * (block_h + gap)
        block_pos[idx] = yy
        textbox("Block index", block_x - 0.30, yy + 0.02, 0.22, 0.12, str(idx), 7.0, COLORS["ink"], False, "r")
        add_block(block_x, yy, block_w, block_h, f"Block {idx}", trainable=idx >= 7)

    sep_y = block_pos[7] + block_h + gap / 2
    line("Frozen separator", x + 0.18, sep_y, x + w - 0.18, sep_y, COLORS["edge"], 0.9, False, "dash")

    bracket_x = x + w + 0.10
    fine_top = block_pos[12]
    fine_bot = block_pos[7] + block_h
    frozen_top = block_pos[6]
    frozen_bot = block_pos[1] + block_h
    for y0, y1, color, label, sublabel in [
        (fine_top, fine_bot, COLORS["blue"], "Fine-tuned", "blocks 7-12"),
        (frozen_top, frozen_bot, COLORS["blue_frozen_text"], "Frozen", "blocks 1-6"),
    ]:
        line("Group bracket", bracket_x, y0, bracket_x, y1, color, 1.25)
        line("Group bracket cap", bracket_x - 0.08, y0, bracket_x, y0, color, 1.25)
        line("Group bracket cap", bracket_x - 0.08, y1, bracket_x, y1, color, 1.25)
        textbox("Group label", bracket_x + 0.12, (y0 + y1) / 2 - 0.16, 1.12, 0.18, label, 10.2, color, True)
        textbox("Group sublabel", bracket_x + 0.12, (y0 + y1) / 2 + 0.11, 1.10, 0.18, sublabel, 8.3, color)


def draw_cls_and_feature(x: float, y: float) -> None:
    textbox("CLS label", x + 0.08, y - 0.58, 1.40, 0.25, "[CLS] output", 13.6, COLORS["ink"], True, "ctr")
    shape("CLS box", "roundRect", x + 0.28, y, 0.78, 0.58, COLORS["gray_light"], COLORS["gray"], 1.2, "CLS", 12.2, COLORS["ink"], True)
    arrow(x + 1.13, y + 0.29, x + 1.85, y + 0.15)

    feat_x = x + 2.08
    feat_y = y - 0.21
    feat_w = 0.42
    feat_h = 1.58
    textbox("Feature label", feat_x - 0.50, feat_y - 0.58, 1.45, 0.36, "768-d\nframe feature", 12.4, COLORS["ink"], True, "ctr")
    shape("Feature vector", "roundRect", feat_x, feat_y, feat_w, feat_h, COLORS["green_light"], COLORS["gray"], 1.0)
    for yy in [feat_y + 0.22, feat_y + 0.48, feat_y + 0.74, feat_y + 1.00, feat_y + 1.30]:
        shape("Feature dot", "ellipse", feat_x + 0.16, yy, 0.11, 0.11, COLORS["green"], COLORS["green"], 0.2)
    textbox("Feature ellipsis", feat_x + 0.08, feat_y + 1.08, 0.25, 0.12, "...", 10.0, COLORS["ink"], True, "ctr")
    textbox("Frame tensor note", feat_x - 0.38, 4.37, 2.10, 0.32, "Used per frame;\n8 frames -> 8 x 768 tensor", 10.2, COLORS["blue"], True, "ctr")


def build_slide_xml(img: Image.Image) -> bytes:
    global parts, shape_id
    parts = []
    shape_id = 1

    textbox("Title", 0.34, 0.26, 5.80, 0.34, "ViT-B/16 frame encoder subcomponent", 18.5, COLORS["ink"], True)
    textbox(
        "Subtitle",
        0.34,
        0.66,
        6.35,
        0.22,
        "Each sampled frame is patchified, encoded independently, and represented by its 768-d [CLS] feature.",
        9.7,
        COLORS["muted"],
    )

    textbox("Input label", 0.88, 1.66, 1.65, 0.28, "Input frame", 15.0, COLORS["ink"], True, "ctr")
    draw_image_mosaic(img, 0.47, 2.18, 2.18, 1.55, 40, 28, name="Input frame mosaic cell")
    shape("Input frame border", "rect", 0.47, 2.18, 2.18, 1.55, None, COLORS["ink"], 1.0)
    textbox("Input caption", 0.52, 3.84, 2.05, 0.20, "one sampled surgical frame", 10.0, COLORS["muted"], False, "ctr")
    arrow(2.82, 2.96, 3.18, 2.96)

    draw_patch_grid(img, 3.36, 2.19, 0.34, 0.055)
    arrow(5.05, 2.96, 5.55, 2.96)

    draw_vit_stack(5.70, 1.42, 2.85, 3.18)
    arrow(8.92, 2.99, 9.55, 2.99)
    draw_cls_and_feature(9.72, 2.68)

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
        f"{''.join(parts)}"
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
    )
    return xml.encode("utf-8")


def build_rels_xml() -> bytes:
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout7.xml"/>'
    ]
    return (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels)}</Relationships>"
    ).encode("utf-8")


def update_content_types(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    if 'Extension="png"' not in text:
        text = text.replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>')
    return text.encode("utf-8")


def update_presentation_size(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    text = re.sub(
        r'<p:sldSz [^>]*/>',
        f'<p:sldSz cx="{emu(SLIDE_W)}" cy="{emu(SLIDE_H)}" type="custom"/>',
        text,
        count=1,
    )
    return text.encode("utf-8")


def main() -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Missing PPTX template: {TEMPLATE}")

    img = load_source_frame()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(TEMPLATE, "r") as zin, ZipFile(OUT, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in {"ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels"}:
                continue
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = update_content_types(data)
            elif item.filename == "ppt/presentation.xml":
                data = update_presentation_size(data)
            zout.writestr(item, data)

        zout.writestr("ppt/slides/slide1.xml", build_slide_xml(img))
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

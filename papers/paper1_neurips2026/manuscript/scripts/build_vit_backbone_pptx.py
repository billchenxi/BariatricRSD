"""
Build an editable PowerPoint version of the ViT-B/16 backbone diagram.

Every element (block, brace label, arrow, text) is a native PowerPoint shape,
so opening the .pptx in PowerPoint / Keynote / Google Slides lets you move,
recolor, or retext anything by clicking on it.

Run:
    python3 scripts/build_vit_backbone_pptx.py
Outputs:
    paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig_vit_backbone.pptx
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
LATEX_DIR = ROOT / "Formatting_Instructions_For_NeurIPS_2026"
OUT = LATEX_DIR / "figures" / "fig_vit_backbone.pptx"
INPUT_FRAME = LATEX_DIR / "figures" / "laparoscopic_frame.png"

# --- editable colors ---
FROZEN_FILL    = RGBColor(0xDC, 0xE6, 0xF2)   # light blue
FROZEN_TEXT    = RGBColor(0x1F, 0x4E, 0x79)   # darker blue
TRAINABLE_FILL = RGBColor(0x1E, 0x50, 0xAA)   # deep blue
TRAINABLE_TEXT = RGBColor(0xFF, 0xFF, 0xFF)   # white
GRAY_FILL      = RGBColor(0xF2, 0xF2, 0xF2)
GREEN_FILL     = RGBColor(0xD0, 0xE8, 0xC8)
LINE_COLOR     = RGBColor(0x40, 0x40, 0x40)


def add_text_box(slide, x, y, w, h, text, *, size=12, bold=False,
                 color=RGBColor(0, 0, 0), align=PP_ALIGN.CENTER):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_block(slide, x, y, w, h, label, *, fill, text_color, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line_color or fill
    shape.line.width = Pt(0.5)
    tf = shape.text_frame
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label
    run.font.size = Pt(11)
    run.font.color.rgb = text_color
    return shape


def add_arrow(slide, x1, y1, x2, y2):
    conn = slide.shapes.add_connector(2, x1, y1, x2, y2)  # 2 = STRAIGHT
    conn.line.color.rgb = LINE_COLOR
    conn.line.width = Pt(1.0)
    # Add arrow head via XML (python-pptx lacks a direct API)
    line_elem = conn.line._get_or_add_ln()
    from pptx.oxml.ns import qn
    from lxml import etree
    tail_arrow = etree.SubElement(line_elem, qn("a:tailEnd"))
    tail_arrow.set("type", "triangle")
    tail_arrow.set("w", "med")
    tail_arrow.set("h", "med")
    return conn


def add_brace(slide, x, y_top, y_bot, label, sublabel, color):
    # Right-pointing brace shape; PowerPoint MSO_SHAPE has RIGHT_BRACE=87
    h = y_bot - y_top
    brace = slide.shapes.add_shape(MSO_SHAPE.RIGHT_BRACE, x, y_top, Inches(0.18), h)
    brace.fill.background()
    brace.line.color.rgb = LINE_COLOR
    brace.line.width = Pt(0.7)
    add_text_box(slide, x + Inches(0.22), y_top + h/2 - Inches(0.18),
                 Inches(1.6), Inches(0.22),
                 label, size=11, bold=True, color=color, align=PP_ALIGN.LEFT)
    add_text_box(slide, x + Inches(0.22), y_top + h/2 + Inches(0.04),
                 Inches(1.6), Inches(0.20),
                 sublabel, size=9, color=color, align=PP_ALIGN.LEFT)


def main():
    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

    # ===== Input frame =====
    fx, fy, fw, fh = Inches(0.4), Inches(2.5), Inches(2.0), Inches(1.7)
    if INPUT_FRAME.exists():
        slide.shapes.add_picture(str(INPUT_FRAME), fx, fy, fw, fh)
    else:
        ph = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, fx, fy, fw, fh)
        ph.fill.solid(); ph.fill.fore_color.rgb = GRAY_FILL
        ph.line.color.rgb = LINE_COLOR
        ph.text_frame.text = "[ replace with\nlaparoscopic frame ]"
    add_text_box(slide, fx, fy + fh + Inches(0.04), fw, Inches(0.3),
                 "Input frame", size=12, bold=True)

    # ===== 16x16 patches grid =====
    px, py = Inches(2.9), Inches(2.6)
    psize = Inches(0.30)
    for i in range(4):
        for j in range(4):
            cell = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                px + j * psize, py + i * psize, psize, psize)
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
            cell.line.color.rgb = RGBColor(0x99, 0x99, 0x99)
            cell.line.width = Pt(0.3)
    add_text_box(slide, px, py + 4*psize + Inches(0.06), 4*psize, Inches(0.3),
                 "16×16 patches", size=12, bold=True)

    # ===== ViT-B/16 stack =====
    stack_x = Inches(5.4)
    stack_y_bottom = Inches(6.6)
    block_w, block_h = Inches(2.6), Inches(0.36)
    block_gap = Inches(0.05)
    frozen_trainable_gap = Inches(0.10)

    # Frozen blocks 1..6 (drawn from bottom up at y_bottom downward...)
    # Actually we'll go top-down with block 12 at top.
    # Layout: block 12 at top, block 1 at bottom.
    block_shapes = {}
    cur_y = stack_y_bottom - block_h
    for i in range(1, 7):  # 1..6 frozen
        s = add_block(slide, stack_x, cur_y, block_w, block_h,
                      f"Block {i}",
                      fill=FROZEN_FILL, text_color=FROZEN_TEXT,
                      line_color=RGBColor(0xA0, 0xB8, 0xD0))
        block_shapes[i] = s
        # number on left
        add_text_box(slide, stack_x - Inches(0.30), cur_y, Inches(0.25), block_h,
                     str(i), size=9, align=PP_ALIGN.RIGHT)
        cur_y -= (block_h + block_gap)

    cur_y -= frozen_trainable_gap  # visual gap between groups
    for i in range(7, 13):  # 7..12 trainable
        s = add_block(slide, stack_x, cur_y, block_w, block_h,
                      f"Block {i}",
                      fill=TRAINABLE_FILL, text_color=TRAINABLE_TEXT,
                      line_color=RGBColor(0x14, 0x38, 0x80))
        block_shapes[i] = s
        add_text_box(slide, stack_x - Inches(0.30), cur_y, Inches(0.25), block_h,
                     str(i), size=9, align=PP_ALIGN.RIGHT)
        cur_y -= (block_h + block_gap)

    stack_top = block_shapes[12].top
    stack_bottom = block_shapes[1].top + block_shapes[1].height

    # Outer "ViT-B/16" container box
    pad = Inches(0.15)
    container_x = stack_x - pad - Inches(0.35)
    container_y = stack_top - pad - Inches(0.65)
    container_w = block_w + 2 * pad + Inches(0.45)
    container_h = stack_bottom - stack_top + 2 * pad + Inches(0.65)
    container = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       container_x, container_y, container_w, container_h)
    container.fill.background()
    container.line.color.rgb = LINE_COLOR
    container.line.width = Pt(0.6)
    # Send container behind the blocks
    spTree = container._element.getparent()
    spTree.remove(container._element)
    spTree.insert(2, container._element)  # near front of children, behind blocks

    # Title labels above the container
    add_text_box(slide, container_x, container_y - Inches(0.7),
                 container_w, Inches(0.32),
                 "ViT-B/16", size=18, bold=True)
    add_text_box(slide, container_x, container_y - Inches(0.40),
                 container_w, Inches(0.22),
                 "Pretrained on ImageNet-21k", size=10)
    add_text_box(slide, container_x, container_y - Inches(0.20),
                 container_w, Inches(0.20),
                 "12 transformer blocks", size=9)

    # Dashed separator between block 6 (frozen) and block 7 (trainable)
    sep_y = (block_shapes[6].top - block_gap / 2 - frozen_trainable_gap / 2)
    line = slide.shapes.add_connector(1, container_x + Inches(0.05), sep_y,
                                      container_x + container_w - Inches(0.05), sep_y)
    line.line.color.rgb = LINE_COLOR
    line.line.width = Pt(0.6)
    line.line.dash_style = 7  # DASH

    # ===== Braces and labels =====
    brace_x = stack_x + block_w + Inches(0.10)
    add_brace(slide, brace_x, block_shapes[12].top,
              block_shapes[7].top + block_shapes[7].height,
              "Trainable", "(blocks 7–12)", color=TRAINABLE_FILL)
    add_brace(slide, brace_x, block_shapes[6].top,
              block_shapes[1].top + block_shapes[1].height,
              "Frozen", "(blocks 1–6)", color=FROZEN_TEXT)

    # ===== CLS output =====
    cls_x = brace_x + Inches(2.0)
    cls_y = block_shapes[10].top
    cls_w, cls_h = Inches(1.0), Inches(0.65)
    add_text_box(slide, cls_x, cls_y - Inches(0.32), cls_w, Inches(0.28),
                 "CLS output", size=11, bold=True)
    cls_box = add_block(slide, cls_x, cls_y, cls_w, cls_h,
                        "CLS", fill=GRAY_FILL, text_color=RGBColor(0, 0, 0),
                        line_color=LINE_COLOR)

    # ===== 768-d feature column =====
    feat_x = cls_x + cls_w + Inches(0.6)
    feat_y = cls_y - Inches(0.4)
    feat_w, feat_h = Inches(0.5), Inches(1.6)
    feat_box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                      feat_x, feat_y, feat_w, feat_h)
    feat_box.fill.solid(); feat_box.fill.fore_color.rgb = GREEN_FILL
    feat_box.line.color.rgb = LINE_COLOR
    feat_box.line.width = Pt(0.5)
    # Add some dots inside
    dot_size = Inches(0.10)
    dot_x = feat_x + (feat_w - dot_size) / 2
    for k in range(5):
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL,
            dot_x, feat_y + Inches(0.20 + 0.20 * k), dot_size, dot_size)
        dot.fill.solid(); dot.fill.fore_color.rgb = RGBColor(0x4F, 0x81, 0x3D)
        dot.line.color.rgb = RGBColor(0x4F, 0x81, 0x3D)
    add_text_box(slide, feat_x - Inches(0.2), feat_y - Inches(0.42),
                 feat_w + Inches(0.4), Inches(0.4),
                 "768-d\nfeature", size=11, bold=True)

    # ===== Arrows (left-to-right flow) =====
    # frame -> patches
    add_arrow(slide,
              fx + fw, fy + fh / 2,
              px, py + 2 * psize)
    # patches -> ViT
    add_arrow(slide,
              px + 4 * psize, py + 2 * psize,
              container_x, py + 2 * psize)
    # ViT -> CLS
    add_arrow(slide,
              container_x + container_w, cls_y + cls_h / 2,
              cls_x, cls_y + cls_h / 2)
    # CLS -> feature
    add_arrow(slide,
              cls_x + cls_w, cls_y + cls_h / 2,
              feat_x, feat_y + feat_h / 2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

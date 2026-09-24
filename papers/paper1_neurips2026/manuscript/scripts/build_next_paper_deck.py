"""Build a multi-slide pptx deck for the next-paper proposal.

Generates `paper/figures_slides/next_paper_proposal.pptx` containing
~18 slides that cover the two-paper plan (Paper 2A causal benchmark +
Paper 2B privileged-information distillation), the variability-scaling
context from the current paper, innovation, contributions, timeline,
and risk handling.

Designed to be self-contained: uses only python-pptx primitives, no
matplotlib chart objects. Color palette and typography are consistent
across slides.
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
OUT_DIR = ROOT / "paper" / "figures_slides"
OUT_PATH = OUT_DIR / "next_paper_proposal.pptx"


# ── Palette ───────────────────────────────────────────────────────────────────

INK = RGBColor(0x0F, 0x17, 0x2A)         # deep slate, body text
INK_SOFT = RGBColor(0x33, 0x44, 0x55)    # secondary text
INK_MUTE = RGBColor(0x6B, 0x72, 0x80)    # muted slate
BG = RGBColor(0xFF, 0xFF, 0xFF)
BG_PANEL = RGBColor(0xF8, 0xFA, 0xFC)
ACCENT = RGBColor(0x1D, 0x4E, 0xD8)      # deep blue
ACCENT_2 = RGBColor(0x0D, 0x94, 0x88)    # teal
ACCENT_3 = RGBColor(0xD9, 0x77, 0x06)    # amber
ACCENT_4 = RGBColor(0x7C, 0x3A, 0xED)    # violet
ACCENT_5 = RGBColor(0xDC, 0x26, 0x26)    # red
GRID = RGBColor(0xE2, 0xE8, 0xF0)
DIV = RGBColor(0xCB, 0xD5, 0xE1)


# ── Layout helpers ────────────────────────────────────────────────────────────

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def blank_slide(prs):
    layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(layout)
    # White background
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H
    )
    bg_shape.line.fill.background()
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG
    bg_shape.shadow.inherit = False
    return slide


def add_title(slide, text, sub=None, top=Inches(0.35), color=INK):
    box = slide.shapes.add_textbox(Inches(0.6), top, SLIDE_W - Inches(1.2), Inches(0.9))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(30)
    r.font.bold = True
    r.font.color.rgb = color
    r.font.name = "Helvetica Neue"
    if sub:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.LEFT
        r2 = p2.add_run()
        r2.text = sub
        r2.font.size = Pt(14)
        r2.font.bold = False
        r2.font.color.rgb = INK_MUTE
        r2.font.name = "Helvetica Neue"


def add_subtitle_strip(slide, text, top=Inches(1.18), color=ACCENT):
    box = slide.shapes.add_textbox(Inches(0.6), top, SLIDE_W - Inches(1.2), Inches(0.35))
    tf = box.text_frame
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = color
    r.font.name = "Helvetica Neue"


def add_text(slide, text, left, top, width, height, size=14, bold=False,
             color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             italic=False, font="Helvetica Neue"):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = font
    return box


def add_bullets(slide, items, left, top, width, height, size=14,
                color=INK, line_spacing=1.18, bullet_color=ACCENT):
    """Add a bulleted list. Each item: string or (string, sub_color)."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            text, item_color = item
        else:
            text, item_color = item, color
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        # bullet glyph
        rb = p.add_run()
        rb.text = "■  "
        rb.font.size = Pt(size)
        rb.font.bold = True
        rb.font.color.rgb = bullet_color
        rb.font.name = "Helvetica Neue"
        # body text — supports inline **bold** markers split on **
        for j, part in enumerate(text.split("**")):
            if not part:
                continue
            rr = p.add_run()
            rr.text = part
            rr.font.size = Pt(size)
            rr.font.bold = (j % 2 == 1)
            rr.font.color.rgb = item_color
            rr.font.name = "Helvetica Neue"


def add_panel(slide, left, top, width, height, fill=BG_PANEL,
              line=DIV, line_w=0.6):
    panel = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    panel.fill.solid()
    panel.fill.fore_color.rgb = fill
    panel.line.color.rgb = line
    panel.line.width = Pt(line_w)
    panel.shadow.inherit = False
    panel.adjustments[0] = 0.05
    return panel


def add_footer(slide, num, total):
    add_text(slide, f"BariatricRSD next-paper proposal  ·  Slide {num} / {total}",
             Inches(0.6), Inches(7.05), Inches(7), Inches(0.3),
             size=9, color=INK_MUTE)
    add_text(slide, "2026-05-21",
             Inches(11.4), Inches(7.05), Inches(1.4), Inches(0.3),
             size=9, color=INK_MUTE, align=PP_ALIGN.RIGHT)


# ── Slides ────────────────────────────────────────────────────────────────────

def slide_title(prs):
    s = blank_slide(prs)
    # Top accent bar
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, Inches(0.10))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()

    add_text(s, "Causal Surgical World-Model Transfer",
             Inches(0.8), Inches(2.0), Inches(12), Inches(1.0),
             size=44, bold=True, color=INK)
    add_text(s, "A Two-Paper Research Plan: Causal Benchmark + Privileged-Information Distillation",
             Inches(0.8), Inches(3.0), Inches(12), Inches(0.6),
             size=22, color=ACCENT)
    add_text(s, "Follow-up to the BariatricRSD variability-scaling paper (NeurIPS 2026, E&D track).",
             Inches(0.8), Inches(3.7), Inches(12), Inches(0.5),
             size=14, color=INK_SOFT, italic=True)

    # Bottom info block
    add_text(s, "Author: Bill",
             Inches(0.8), Inches(6.4), Inches(6), Inches(0.4),
             size=13, color=INK_SOFT)
    add_text(s, "Status: 2026-05-21  ·  Plan + brief: NEXT_PAPER_PLAN.md, NEXT_PAPER_BRIEF.md",
             Inches(0.8), Inches(6.8), Inches(11), Inches(0.4),
             size=11, color=INK_MUTE)


def slide_where_we_are(prs):
    s = blank_slide(prs)
    add_title(s, "Where we are",
              sub="What the current paper (under review at NeurIPS 2026) established.")
    add_subtitle_strip(s, "VARIABILITY-SCALING RESULT ON MB140 vs CHOLEC80")

    # Two-column layout
    add_text(s, "Findings",
             Inches(0.6), Inches(1.7), Inches(6), Inches(0.4),
             size=18, bold=True, color=ACCENT)
    add_bullets(s, [
        ("Workflow conditioning helps on **MultiBypass140** (multi-center RYGB, K=6, **H(z)=2.48**)."),
        ("Δ decoupled-oracle = **−0.85 min within-center, −0.47 cross-center**."),
        ("Statistically null on **Cholec80** (single-center, K=4, **H(z)=1.27**, 71% of videos in one cluster)."),
        ("Shuffled-token control rules out parameter-capacity explanation."),
        ("Pixel-only causal evaluator preserves **−0.18 / −0.22 min** without GT phases at test."),
    ], Inches(0.6), Inches(2.15), Inches(6.2), Inches(4.5), size=13)

    add_text(s, "Methodology contributions",
             Inches(7.0), Inches(1.7), Inches(6), Inches(0.4),
             size=18, bold=True, color=ACCENT_2)
    add_bullets(s, [
        ("**Strict prefix-only protocol** — clip ends at prediction time t; removes future-frame leakage."),
        ("**Decoupled-oracle architecture** — phase head independent of workflow token; closes circularity."),
        ("**Workflow-cluster apparatus** — phase-bigram TF-IDF + PCA + k-means; offline + per-clip lookup."),
        ("**Variability-scaling thesis** — workflow conditioning's value tracks H(z) of phase-order clusters."),
        ("**Causal-at-inference evaluator** — soft cluster posterior from model's own prefix phase predictions."),
    ], Inches(7.0), Inches(2.15), Inches(5.7), Inches(4.5), size=13,
       bullet_color=ACCENT_2)

    add_footer(s, 2, 18)


def slide_what_is_missing(prs):
    s = blank_slide(prs)
    add_title(s, "What's missing after the current paper",
              sub="Gaps that justify the next-paper program.")
    add_subtitle_strip(s, "RESEARCH GAPS")

    items = [
        ("**Training-time supervision gap.** The pixel-only causal evaluator removes the inference-time oracle, but training still uses privileged phase + workflow labels."),
        ("**No motion / action prediction.** RSD is a scalar target. The model never says ‘what comes next’ — instrument changes, phase transitions, deviation events."),
        ("**No engagement with the surgical-FM wave.** SurgMotion, SurgVISTA, ZEN, EndoMamba, EndoDINO have appeared. Our framework hasn't been benchmarked against them."),
        ("**Untested across procedures.** MB140 + Cholec80 only. No cross-procedure transfer claims yet."),
        ("**Untested under physical-AI world models.** NVIDIA Cosmos and V-JEPA 2/2.1 transfer to surgical video is an open empirical question."),
        ("**Variability-scaling thesis only on scalar RSD.** Whether the H(z) pattern generalizes to anticipation tasks is the natural next probe."),
    ]
    add_bullets(s, items, Inches(0.6), Inches(1.8), Inches(12.2), Inches(5),
                size=14, bullet_color=ACCENT_3)
    add_footer(s, 3, 18)


def slide_research_question(prs):
    s = blank_slide(prs)
    add_title(s, "The research question",
              sub="Survives any empirical outcome and isn't vendor-dependent.")
    add_subtitle_strip(s, "ONE QUESTION THAT FRAMES BOTH PAPERS")

    # Big quote panel
    add_panel(s, Inches(1.0), Inches(2.0), Inches(11.3), Inches(2.6),
              fill=RGBColor(0xEC, 0xFD, 0xF5), line=ACCENT_2, line_w=1.0)

    add_text(s,
             "Do physical-AI and surgical video foundation models improve\n"
             "causal surgical anticipation,",
             Inches(1.4), Inches(2.2), Inches(10.6), Inches(1.2),
             size=24, bold=True, color=INK)
    add_text(s,
             "and does workflow variability still determine\n"
             "when explicit workflow-state conditioning helps?",
             Inches(1.4), Inches(3.3), Inches(10.6), Inches(1.2),
             size=22, color=ACCENT_2, italic=True)

    add_text(s,
             "Why this framing works:",
             Inches(0.6), Inches(4.95), Inches(12), Inches(0.4),
             size=15, bold=True, color=ACCENT)
    add_bullets(s, [
        ("Not vendor-locked — publishable whether Cosmos wins, loses, or ties."),
        ("Uses our **strict prefix-only** causal apparatus as the defining contribution."),
        ("Forces extension from scalar RSD to **future-state prediction**."),
        ("Tests whether the **variability-scaling thesis** generalizes."),
    ], Inches(0.6), Inches(5.35), Inches(12), Inches(1.8), size=13)
    add_footer(s, 4, 18)


def slide_two_paper_overview(prs):
    s = blank_slide(prs)
    add_title(s, "Two-paper plan",
              sub="Split lets each contribution have depth and lets risk be hedged.")
    add_subtitle_strip(s, "PAPERS 2A AND 2B SHARE ~70% INFRASTRUCTURE")

    # Two-panel side-by-side
    panel_top = Inches(1.6)
    panel_h = Inches(5.0)
    panel_w = Inches(6.1)

    # Paper 2A
    add_panel(s, Inches(0.5), panel_top, panel_w, panel_h,
              fill=RGBColor(0xEF, 0xF6, 0xFF), line=ACCENT, line_w=1.0)
    add_text(s, "PAPER 2A",
             Inches(0.75), Inches(1.75), panel_w, Inches(0.4),
             size=12, bold=True, color=ACCENT)
    add_text(s, "Causal benchmark +\nfoundation-model transfer matrix",
             Inches(0.75), Inches(2.05), panel_w, Inches(1.1),
             size=18, bold=True, color=INK)
    add_text(s,
             "Thesis: strict prefix-only evaluation re-ranks foundation models for surgical forecasting. Pixel-prediction quality is a weak proxy for downstream utility. Variability-scaling generalizes across backbones and tasks.",
             Inches(0.75), Inches(3.15), panel_w - Inches(0.4), Inches(1.6),
             size=12, color=INK_SOFT, italic=True)

    add_bullets(s, [
        ("**Target:** MICCAI 2027 (Mar)"),
        ("**Compute:** 1.5K–3.2K GPU-h"),
        ("**Risk:** medium"),
        ("Backup framing: ‘Cosmos-meh’ diagnostic"),
    ], Inches(0.75), Inches(5.0), panel_w - Inches(0.4), Inches(1.6),
       size=12, bullet_color=ACCENT)

    # Paper 2B
    add_panel(s, Inches(6.75), panel_top, panel_w, panel_h,
              fill=RGBColor(0xF0, 0xFD, 0xFA), line=ACCENT_2, line_w=1.0)
    add_text(s, "PAPER 2B",
             Inches(7.0), Inches(1.75), panel_w, Inches(0.4),
             size=12, bold=True, color=ACCENT_2)
    add_text(s, "Privileged-information distillation\nfor workflow-conditioned RSD",
             Inches(7.0), Inches(2.05), panel_w, Inches(1.1),
             size=18, bold=True, color=INK)
    add_text(s,
             "Thesis: a student model that learns the workflow posterior q(z | x_{≤t}) from a privileged teacher closes most of the oracle-to-deployable gap without using ground-truth phase or workflow labels at test.",
             Inches(7.0), Inches(3.15), panel_w - Inches(0.4), Inches(1.6),
             size=12, color=INK_SOFT, italic=True)

    add_bullets(s, [
        ("**Target:** NeurIPS 2027 (May)"),
        ("**Compute:** 0.75K–1.5K GPU-h"),
        ("**Risk:** low (testable with existing assets)"),
        ("Ships independent of FM transfer outcome"),
    ], Inches(7.0), Inches(5.0), panel_w - Inches(0.4), Inches(1.6),
       size=12, bullet_color=ACCENT_2)

    add_footer(s, 5, 18)


def slide_paper_2a_innovation(prs):
    s = blank_slide(prs)
    add_title(s, "Paper 2A — Innovation",
              sub="Four claims that no competing surgical-FM paper has demonstrated.")
    add_subtitle_strip(s, "WHY THIS PAPER ISN'T SCOOPABLE BY SURGMOTION / SURGVISTA / ZEN")

    items = [
        ("**1. First causal evaluation protocol for surgical-video foundation models.** Existing FM papers (SurgMotion, SurgVISTA, ZEN) report centered-window or aggregate metrics — none under strict prefix-only protocols matching deployment."),
        ("**2. First systematic transfer matrix that includes physical-AI world models alongside surgical-native FMs.** No prior paper has tested Cosmos / V-JEPA 2.1 head-to-head against domain-specialized surgical FMs on the same downstream tasks."),
        ("**3. First diagnostic showing pixel-prediction quality is a weak proxy for downstream surgical forecasting.** A measurement contribution to the broader world-model field, not just surgical AI."),
        ("**4. First multi-task variability-scaling extension.** Current paper proved H(z) pattern on scalar RSD; Paper 2A extends to phase-transition anticipation and future-phase-sequence — demonstrating the pattern is task-general."),
    ]
    add_bullets(s, items, Inches(0.6), Inches(1.8), Inches(12.2), Inches(5),
                size=14, bullet_color=ACCENT)
    add_footer(s, 6, 18)


def slide_paper_2a_design(prs):
    s = blank_slide(prs)
    add_title(s, "Paper 2A — Experimental design",
              sub="Frozen-feature transfer matrix × three causal anticipation tasks.")
    add_subtitle_strip(s, "MODEL × TASK MATRIX")

    # Table-style grid
    # Header row
    cols = ["Backbone", "RSD MAE", "Next-transition MAE", "Future-phase F1", "Triplet mAP",
            "Compute"]
    rows = [
        ["ViT-B/16 (anchor)", "✓", "✓", "✓", "—", "low"],
        ["VideoMAE-L", "✓", "✓", "✓", "—", "med"],
        ["V-JEPA 2 / 2.1", "✓", "✓", "✓", "✓", "med"],
        ["Cosmos-Predict2", "✓", "✓", "✓", "—", "high"],
        ["SurgMotion", "✓", "✓", "✓", "✓", "med"],
        ["SurgVISTA / ZEN", "✓", "✓", "✓", "—", "med"],
        ["EndoMamba", "✓", "✓", "—", "—", "low"],
    ]

    table_left = Inches(0.6)
    table_top = Inches(1.85)
    cell_h = Inches(0.4)
    col_widths = [Inches(2.2), Inches(1.3), Inches(2.0), Inches(2.0),
                  Inches(1.5), Inches(1.4)]

    # Header
    x = table_left.emu
    for c, w in zip(cols, col_widths):
        hdr = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, table_top.emu, w.emu, cell_h.emu)
        hdr.fill.solid(); hdr.fill.fore_color.rgb = ACCENT
        hdr.line.color.rgb = ACCENT
        hdr.shadow.inherit = False
        tf = hdr.text_frame
        tf.margin_left = Inches(0.08); tf.margin_right = Inches(0.08)
        tf.margin_top = Inches(0.04); tf.margin_bottom = Inches(0.04)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = c
        r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = BG
        r.font.name = "Helvetica Neue"
        x += w.emu

    # Body rows
    y = table_top.emu + cell_h.emu
    for ri, row in enumerate(rows):
        x = table_left.emu
        for c, w in zip(row, col_widths):
            cell = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w.emu, cell_h.emu)
            cell.fill.solid()
            cell.fill.fore_color.rgb = BG if ri % 2 == 0 else BG_PANEL
            cell.line.color.rgb = GRID
            cell.line.width = Pt(0.4)
            cell.shadow.inherit = False
            tf = cell.text_frame
            tf.margin_left = Inches(0.08); tf.margin_right = Inches(0.08)
            tf.margin_top = Inches(0.04); tf.margin_bottom = Inches(0.04)
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = c
            r.font.size = Pt(11); r.font.color.rgb = INK
            r.font.name = "Helvetica Neue"
            x += w.emu
        y += cell_h.emu

    # Side notes
    add_text(s, "Datasets & splits",
             Inches(0.6), Inches(5.3), Inches(6), Inches(0.35),
             size=14, bold=True, color=ACCENT)
    add_bullets(s, [
        ("MB140 within-center: 5-fold CV (fold 0 = dev fold)"),
        ("MB140 cross-center: Bern → Strasbourg"),
        ("Cholec80: 36/6/30 split"),
        ("CholecT50: action-triplet anticipation (optional)"),
    ], Inches(0.6), Inches(5.7), Inches(6.0), Inches(1.5),
       size=12, bullet_color=ACCENT)

    add_text(s, "Conditions per (backbone, dataset)",
             Inches(7.0), Inches(5.3), Inches(6), Inches(0.35),
             size=14, bold=True, color=ACCENT_2)
    add_bullets(s, [
        ("no-token (baseline)"),
        ("retrospective oracle (upper bound)"),
        ("decoupled-oracle (closes circularity)"),
        ("shuffled-token (semantic control)"),
    ], Inches(7.0), Inches(5.7), Inches(6.0), Inches(1.5),
       size=12, bullet_color=ACCENT_2)

    add_footer(s, 7, 18)


def slide_paper_2a_contribution(prs):
    s = blank_slide(prs)
    add_title(s, "Paper 2A — Contribution to the field",
              sub="What the surgical-AI / vision community gets after Paper 2A is published.")
    add_subtitle_strip(s, "ARTIFACTS THE PAPER LEAVES BEHIND")

    # Two columns
    add_text(s, "Released artifacts", Inches(0.6), Inches(1.85),
             Inches(6), Inches(0.4), size=18, bold=True, color=ACCENT)
    add_bullets(s, [
        ("**Causal anticipation benchmark** — strict prefix-only RSD + phase + sequence evaluators."),
        ("**Model-transfer leaderboard** — anonymized per-backbone scores under matched protocol."),
        ("**Pixel-quality-vs-downstream diagnostic** — FVD/LPIPS/PSNR on a held-out surgical video set."),
        ("**Reproducibility kit** — code, configs, weights manifest, feature caches."),
    ], Inches(0.6), Inches(2.25), Inches(6.0), Inches(4.5),
       size=13, bullet_color=ACCENT)

    add_text(s, "Field-level claims", Inches(7.0), Inches(1.85),
             Inches(6), Inches(0.4), size=18, bold=True, color=ACCENT_2)
    add_bullets(s, [
        ("**Causal evaluation re-ranks FMs** — leaderboards change under deployment-relevant protocols."),
        ("**Surgical-native pretraining wins at matched compute** — informs investment direction."),
        ("**Pixel quality ≠ downstream utility** — community must use task-relevant metrics."),
        ("**Variability scaling is task-general** — Cholec80 mis-calibration extends from RSD to anticipation."),
    ], Inches(7.0), Inches(2.25), Inches(6.0), Inches(4.5),
       size=13, bullet_color=ACCENT_2)

    add_footer(s, 8, 18)


def slide_paper_2b_innovation(prs):
    s = blank_slide(prs)
    add_title(s, "Paper 2B — Innovation",
              sub="Closing the oracle-to-deployable gap with privileged-information distillation.")
    add_subtitle_strip(s, "WHY DISTILLATION IS THE NEXT MOVE")

    # Three-panel "before / method / after"
    panel_w = Inches(4.0)
    panel_h = Inches(4.6)
    panel_top = Inches(1.7)

    # Panel 1 — Current state
    add_panel(s, Inches(0.5), panel_top, panel_w, panel_h,
              fill=RGBColor(0xFE, 0xF3, 0xC7), line=ACCENT_3, line_w=1.0)
    add_text(s, "CURRENT GAP", Inches(0.7), Inches(1.85),
             panel_w - Inches(0.4), Inches(0.4),
             size=12, bold=True, color=ACCENT_3)
    add_text(s, "Train with privileged supervision\n→ Test with pixels only",
             Inches(0.7), Inches(2.2), panel_w - Inches(0.4), Inches(1.0),
             size=15, bold=True, color=INK)
    add_bullets(s, [
        ("Oracle (privileged): **−0.85 min**"),
        ("Deployable causal: **−0.18 min**"),
        ("Gap to close: **~0.67 min**"),
        ("Lost mostly to noisy prefix-cluster posterior"),
    ], Inches(0.7), Inches(3.3), panel_w - Inches(0.4), Inches(3),
       size=12, bullet_color=ACCENT_3)

    # Panel 2 — Method
    add_panel(s, Inches(4.7), panel_top, panel_w, panel_h,
              fill=RGBColor(0xDB, 0xEA, 0xFE), line=ACCENT, line_w=1.0)
    add_text(s, "METHOD", Inches(4.9), Inches(1.85),
             panel_w - Inches(0.4), Inches(0.4),
             size=12, bold=True, color=ACCENT)
    add_text(s, "Teacher-student distillation\nfor q_φ(z | x_{≤t})",
             Inches(4.9), Inches(2.2), panel_w - Inches(0.4), Inches(1.0),
             size=15, bold=True, color=INK)
    add_bullets(s, [
        ("**Teacher:** frozen decoupled-oracle model"),
        ("**Student:** workflow posterior from pixels"),
        ("**Loss:** RSD + phase + KL(posterior)"),
        ("**Eval:** zero privileged signal at test"),
    ], Inches(4.9), Inches(3.3), panel_w - Inches(0.4), Inches(3),
       size=12, bullet_color=ACCENT)

    # Panel 3 — Target
    add_panel(s, Inches(8.9), panel_top, panel_w, panel_h,
              fill=RGBColor(0xD1, 0xFA, 0xE5), line=ACCENT_2, line_w=1.0)
    add_text(s, "TARGET RESULT", Inches(9.1), Inches(1.85),
             panel_w - Inches(0.4), Inches(0.4),
             size=12, bold=True, color=ACCENT_2)
    add_text(s, "Deployable predictor approaches\nprivileged-supervision upper bound",
             Inches(9.1), Inches(2.2), panel_w - Inches(0.4), Inches(1.0),
             size=15, bold=True, color=INK)
    add_bullets(s, [
        ("Distilled student: **≤ 0.3 min from oracle**"),
        ("Variability scaling **preserved**"),
        ("Cholec80 null **preserved**"),
        ("Encoder-agnostic (ViT, V-JEPA, SurgMotion)"),
    ], Inches(9.1), Inches(3.3), panel_w - Inches(0.4), Inches(3),
       size=12, bullet_color=ACCENT_2)

    add_footer(s, 9, 18)


def slide_paper_2b_method(prs):
    s = blank_slide(prs)
    add_title(s, "Paper 2B — Method detail",
              sub="Teacher-student distillation for the workflow posterior.")
    add_subtitle_strip(s, "ARCHITECTURE")

    # Schematic via shapes — 5-stage horizontal pipeline
    stages = [
        ("Surgical prefix\nx_{≤t}", ACCENT),
        ("Visual encoder\n(ViT / V-JEPA / SurgMotion)", ACCENT_2),
        ("Student q_φ(z | x_{≤t})\nworkflow posterior", ACCENT_4),
        ("Soft workflow token\nΣ_k q_k · E_k", ACCENT_3),
        ("Temporal head\n→ RSD / phase / next-transition", ACCENT_5),
    ]
    n = len(stages)
    pipeline_top = Inches(2.0)
    pipeline_h = Inches(1.6)
    margin_x = Inches(0.6)
    gap = Inches(0.25)
    total_w_emu = SLIDE_W.emu - 2 * margin_x.emu - (n - 1) * gap.emu
    box_w_emu = total_w_emu // n
    box_w = Emu(box_w_emu)

    for i, (label, color) in enumerate(stages):
        left = Emu(margin_x.emu + i * (box_w_emu + gap.emu))
        box = s.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, left, pipeline_top, box_w, pipeline_h
        )
        box.fill.solid(); box.fill.fore_color.rgb = color
        box.line.color.rgb = color
        box.adjustments[0] = 0.12
        box.shadow.inherit = False
        tf = box.text_frame
        tf.margin_left = Inches(0.15); tf.margin_right = Inches(0.15)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for j, line in enumerate(label.split("\n")):
            p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = line
            r.font.size = Pt(13)
            r.font.bold = (j == 0)
            r.font.color.rgb = BG
            r.font.name = "Helvetica Neue"
        # Arrow to next
        if i < n - 1:
            ax = Emu(left.emu + box_w_emu)
            ay = Emu(pipeline_top.emu + Inches(0.55).emu)
            arr = s.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, ax, ay, gap, Inches(0.45)
            )
            arr.fill.solid(); arr.fill.fore_color.rgb = INK_MUTE
            arr.line.fill.background()
            arr.shadow.inherit = False

    # Teacher signal banner
    add_panel(s, Inches(0.6), Inches(3.95), Inches(12.1), Inches(1.2),
              fill=RGBColor(0xFE, 0xF3, 0xC7), line=ACCENT_3, line_w=1.0)
    add_text(s, "TRAINING ONLY — TEACHER SIGNAL",
             Inches(0.85), Inches(4.05), Inches(12), Inches(0.3),
             size=11, bold=True, color=ACCENT_3)
    add_text(s, "Full-video oracle cluster z(V)   ·   prefix-derived cluster labels   ·   phase-transition labels",
             Inches(0.85), Inches(4.4), Inches(12), Inches(0.5),
             size=14, color=INK)
    add_text(s, "→  KL distillation onto the student posterior q_φ;  removed entirely at inference.",
             Inches(0.85), Inches(4.75), Inches(12), Inches(0.4),
             size=12, italic=True, color=INK_SOFT)

    # Loss summary
    add_text(s, "Loss", Inches(0.6), Inches(5.4),
             Inches(3), Inches(0.4), size=14, bold=True, color=ACCENT_2)
    add_bullets(s, [
        ("RSD regression (MSE)"),
        ("Phase classification (CE, when labels available)"),
        ("Next-transition regression / classification"),
        ("Future-phase-sequence loss"),
        ("KL distillation: q_φ ‖ teacher posterior"),
        ("Optional calibration regularizer"),
    ], Inches(0.6), Inches(5.8), Inches(6), Inches(1.5),
       size=11, bullet_color=ACCENT_2, line_spacing=1.05)

    add_text(s, "Properties of the resulting student", Inches(7.0), Inches(5.4),
             Inches(6), Inches(0.4), size=14, bold=True, color=ACCENT_4)
    add_bullets(s, [
        ("**Pixel-only at inference**: no GT phases, no oracle cluster."),
        ("**Calibrated**: reliability diagram + ECE reported video-wise."),
        ("**Variability-scaling preserved**: Cholec80 remains null."),
        ("**Encoder-agnostic**: swap ViT for V-JEPA 2.1 or SurgMotion."),
    ], Inches(7.0), Inches(5.8), Inches(6), Inches(1.5),
       size=11, bullet_color=ACCENT_4, line_spacing=1.05)

    add_footer(s, 10, 18)


def slide_paper_2b_contribution(prs):
    s = blank_slide(prs)
    add_title(s, "Paper 2B — Contribution",
              sub="What surgical AI gets from a working privileged-information distillation recipe.")
    add_subtitle_strip(s, "DEPLOYABLE WORKFLOW CONDITIONING WITHOUT PRIVILEGED LABELS")

    # Bar-chart-style visualization of the gap
    chart_left = Inches(0.6)
    chart_top = Inches(1.85)
    chart_w = Inches(7.0)
    chart_h = Inches(4.4)

    add_panel(s, chart_left, chart_top, chart_w, chart_h,
              fill=BG_PANEL, line=DIV, line_w=0.6)

    add_text(s, "Within-center MB140 strict val MAE (lower = better)",
             chart_left + Inches(0.25), chart_top + Inches(0.18),
             chart_w - Inches(0.5), Inches(0.4),
             size=12, bold=True, color=INK_SOFT)

    # Three bars
    bar_left = chart_left + Inches(0.7)
    bar_top = chart_top + Inches(0.85)
    bar_h_units = Inches(3.1)
    bar_w = Inches(1.5)
    gap_x = Inches(0.55)

    # MAE values scaled to bar heights (no-token 13.03 = full height,
    # oracle 12.18 ≈ 84%, distilled-student target 12.4 ≈ 90%)
    values = [
        ("no-token\n(baseline)", 13.03, 1.00, ACCENT_5),
        ("deployable causal\n(current paper)", 12.85, 0.93, ACCENT_3),
        ("distilled student\n(target)", 12.45, 0.78, ACCENT_4),
        ("decoupled-oracle\n(privileged upper bound)", 12.18, 0.62, ACCENT_2),
    ]
    for i, (label, mae, frac, color) in enumerate(values):
        bx = bar_left + i * (bar_w + gap_x)
        bh = Emu(int(bar_h_units.emu * frac))
        by = bar_top + (bar_h_units - bh)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, bx, by, bar_w, bh)
        bar.fill.solid(); bar.fill.fore_color.rgb = color
        bar.line.color.rgb = color
        bar.shadow.inherit = False
        # MAE label above bar
        add_text(s, f"{mae:.2f} min", bx, by - Inches(0.45),
                 bar_w, Inches(0.4), size=12, bold=True, color=color,
                 align=PP_ALIGN.CENTER)
        # Condition label below bar
        add_text(s, label, bx, bar_top + bar_h_units + Inches(0.05),
                 bar_w, Inches(0.7), size=10, color=INK_SOFT,
                 align=PP_ALIGN.CENTER)

    # Closing-the-gap annotation
    add_text(s, "← target: close ≥ 50% of the oracle gap →",
             bar_left + Inches(1.7),
             bar_top + bar_h_units - Inches(0.3),
             Inches(4.5), Inches(0.4),
             size=12, bold=True, italic=True, color=INK_SOFT,
             align=PP_ALIGN.CENTER)

    # Right column — contributions
    add_text(s, "What ships",
             Inches(8.0), Inches(1.85), Inches(5), Inches(0.4),
             size=18, bold=True, color=ACCENT)
    add_bullets(s, [
        ("**A reusable distillation recipe** for closing oracle gaps in workflow-conditioned tasks."),
        ("**Calibrated workflow posterior** useful for many downstream surgical tasks beyond RSD."),
        ("**Ablation map** showing which teacher signals and loss formulations matter."),
        ("**Deployable predictor** that approaches the privileged-supervision upper bound under strict prefix-only protocol."),
    ], Inches(8.0), Inches(2.3), Inches(5.0), Inches(4.5),
       size=12, bullet_color=ACCENT)

    add_footer(s, 11, 18)


def slide_combined_value(prs):
    s = blank_slide(prs)
    add_title(s, "Combined value to the field",
              sub="What the two papers together let the surgical-AI / vision community do.")
    add_subtitle_strip(s, "THE TWO PAPERS AS A PROGRAM")

    rows = [
        ("Do video / world FMs help surgical forecasting?",
         "Quantitative answer with verified causal protocol (Paper 2A)"),
        ("Is generative pixel quality a good proxy for surgical understanding?",
         "No — community must use task-relevant metrics (Paper 2A diagnostic)"),
        ("How do we measure surgical-FM transfer fairly?",
         "Strict prefix-only + workflow-variability stratification (Paper 2A)"),
        ("Can a deployable model recover the privileged workflow gain?",
         "Yes, via privileged-information distillation (Paper 2B)"),
        ("Does workflow conditioning still matter with stronger backbones?",
         "Yes when H(z) is high; no when H(z) is low (both papers)"),
    ]

    # Table
    table_left = Inches(0.6)
    table_top = Inches(1.85)
    cell_h = Inches(0.85)
    q_w = Inches(6.2)
    a_w = Inches(6.5)

    for i, (q, a) in enumerate(rows):
        y = table_top.emu + i * cell_h.emu
        # Q cell
        qb = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left.emu, y,
                                q_w.emu, cell_h.emu)
        qb.fill.solid(); qb.fill.fore_color.rgb = BG if i % 2 == 0 else BG_PANEL
        qb.line.color.rgb = GRID; qb.line.width = Pt(0.4)
        qb.shadow.inherit = False
        tf = qb.text_frame
        tf.margin_left = Inches(0.15); tf.margin_right = Inches(0.15)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = q
        r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = INK
        r.font.name = "Helvetica Neue"

        # A cell
        ab = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, table_left.emu + q_w.emu, y,
                                a_w.emu, cell_h.emu)
        ab.fill.solid(); ab.fill.fore_color.rgb = RGBColor(0xEC, 0xFD, 0xF5) if i % 2 == 0 else RGBColor(0xD1, 0xFA, 0xE5)
        ab.line.color.rgb = GRID; ab.line.width = Pt(0.4)
        ab.shadow.inherit = False
        tf = ab.text_frame
        tf.margin_left = Inches(0.15); tf.margin_right = Inches(0.15)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = a
        r.font.size = Pt(12); r.font.color.rgb = ACCENT_2
        r.font.name = "Helvetica Neue"

    add_footer(s, 12, 18)


def slide_timeline(prs):
    s = blank_slide(prs)
    add_title(s, "Timeline",
              sub="Phase 0 → Phase 4 with explicit submission milestones.")
    add_subtitle_strip(s, "2026 Q3 — 2027 Q2")

    # Gantt-style chart
    months = ["Jun-26", "Jul-26", "Aug-26", "Sep-26", "Oct-26", "Nov-26",
              "Dec-26", "Jan-27", "Feb-27", "Mar-27", "Apr-27", "May-27"]
    n_months = len(months)
    chart_left = Inches(2.2)
    chart_right = Inches(13.0)
    chart_top = Inches(1.85)
    row_h = Inches(0.55)
    col_w_emu = (chart_right.emu - chart_left.emu) // n_months

    # Month headers
    for i, m in enumerate(months):
        x = chart_left.emu + i * col_w_emu
        cell = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, chart_top.emu,
                                  col_w_emu, row_h.emu)
        cell.fill.solid(); cell.fill.fore_color.rgb = ACCENT
        cell.line.color.rgb = ACCENT
        cell.shadow.inherit = False
        tf = cell.text_frame
        tf.margin_top = Inches(0.05); tf.margin_bottom = Inches(0.05)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = m
        r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = BG
        r.font.name = "Helvetica Neue"

    # Phase rows: (label, start_idx, end_idx, color)
    phases = [
        ("Phase 0: feasibility audit",      0, 3, ACCENT),
        ("Phase 1: scout matrix",           3, 6, ACCENT_2),
        ("Phase 2: confirmatory (Paper 2A)", 5, 9, ACCENT_3),
        ("Paper 2A write + submit",         8, 10, ACCENT_4),
        ("Phase 3: Paper 2B start",         8, 10, ACCENT_5),
        ("Phase 4: Paper 2B finish",        10, 12, ACCENT_2),
    ]

    for row_i, (label, s_i, e_i, color) in enumerate(phases):
        y = chart_top.emu + (row_i + 1) * row_h.emu + Inches(0.08).emu
        # Row label (left of chart)
        add_text(s, label, Inches(0.4), Emu(y),
                 chart_left - Inches(0.5), row_h,
                 size=11, color=INK_SOFT,
                 anchor=MSO_ANCHOR.MIDDLE)
        # Bar
        bx = chart_left.emu + s_i * col_w_emu + Inches(0.05).emu
        bw = (e_i - s_i) * col_w_emu - Inches(0.1).emu
        bar = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 bx, y, bw, row_h.emu - Inches(0.15).emu)
        bar.fill.solid(); bar.fill.fore_color.rgb = color
        bar.line.color.rgb = color
        bar.adjustments[0] = 0.25
        bar.shadow.inherit = False

    # Milestone markers (vertical lines + labels)
    milestones = [
        (3, "Phase 0\ncomplete"),
        (6, "Phase 1\ngo/no-go"),
        (9, "Paper 2A\n→ MICCAI 2027"),
        (12 - 1, "Paper 2B\n→ NeurIPS 2027"),
    ]
    for idx, label in milestones:
        x = chart_left.emu + idx * col_w_emu
        line_top = chart_top.emu + row_h.emu
        line_bot = chart_top.emu + (len(phases) + 1) * row_h.emu + Inches(0.1).emu
        ln = s.shapes.add_connector(1, x, line_top, x, line_bot)
        ln.line.color.rgb = ACCENT_5; ln.line.width = Pt(1.5)
        ln.line.dash_style = 7  # dashed
        add_text(s, label,
                 Emu(x - Inches(0.7).emu),
                 Emu(line_bot + Inches(0.05).emu),
                 Inches(1.4), Inches(0.6),
                 size=9, bold=True, color=ACCENT_5,
                 align=PP_ALIGN.CENTER)

    add_footer(s, 13, 18)


def slide_compute_risk(prs):
    s = blank_slide(prs)
    add_title(s, "Compute budget & risk gates",
              sub="Staged plan: <500 GPU-h to first go/no-go decision.")
    add_subtitle_strip(s, "STAGE-BY-STAGE COSTS WITH MITIGATIONS")

    # Stages table
    table_left = Inches(0.6)
    table_top = Inches(1.85)
    cell_h = Inches(0.5)
    cols_w = [Inches(2.0), Inches(2.0), Inches(2.4), Inches(2.4), Inches(3.4)]
    headers = ["Stage", "GPU-hours", "Cost ($)", "Cumulative ($)",
               "Decision gate"]

    # Header
    x = table_left.emu
    for c, w in zip(headers, cols_w):
        hdr = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, table_top.emu,
                                 w.emu, cell_h.emu)
        hdr.fill.solid(); hdr.fill.fore_color.rgb = ACCENT
        hdr.line.color.rgb = ACCENT; hdr.shadow.inherit = False
        tf = hdr.text_frame
        tf.margin_left = Inches(0.1); tf.margin_top = Inches(0.05)
        tf.margin_bottom = Inches(0.05)
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = c
        r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = BG
        r.font.name = "Helvetica Neue"
        x += w.emu

    rows = [
        ("Stage 0 — feasibility",  "40–80",      "$250",        "$250",        "Audit backbones; drop brittle ones"),
        ("Stage 1 — scout matrix", "250–500",    "$0.75K–$1.5K", "$1.0K–$1.75K","Any FM improves causal RSD by ≥0.3 min?"),
        ("Stage 2 — confirmatory","700–1,400",  "$2.1K–$4.2K",  "$3.1K–$6.0K", "Lock Paper 2A matrix; ≥3 claims defensible?"),
        ("Stage 3 — adapters",    "500–1,200",  "$1.5K–$3.6K",  "$4.6K–$9.6K", "Worth retraining selected backbones?"),
        ("Stage 4 — optional SSL","700–1,500",  "$2.1K–$4.5K",  "$6.7K–$14.1K","Surgical-SSL adapt only if Stages 2/3 win"),
        ("Paper 2B (reuses 2A)",  "750–1,500",  "$2.25K–$4.5K", "$9K–$18.6K",  "Distillation closes ≥50% of oracle gap?"),
    ]

    y = table_top.emu + cell_h.emu
    for ri, row in enumerate(rows):
        x = table_left.emu
        for c, w in zip(row, cols_w):
            cell = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w.emu, cell_h.emu)
            cell.fill.solid()
            cell.fill.fore_color.rgb = BG if ri % 2 == 0 else BG_PANEL
            cell.line.color.rgb = GRID; cell.line.width = Pt(0.4)
            cell.shadow.inherit = False
            tf = cell.text_frame
            tf.margin_left = Inches(0.1); tf.margin_top = Inches(0.06)
            tf.margin_bottom = Inches(0.06)
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = c
            r.font.size = Pt(11); r.font.color.rgb = INK
            r.font.name = "Helvetica Neue"
            x += w.emu
        y += cell_h.emu

    # Total bar
    add_text(s,
             "Full-program upper bound: ~5,000–7,000 GPU-h (~$15K–$21K with 25% overhead)",
             Inches(0.6), Inches(5.5), Inches(12), Inches(0.4),
             size=14, bold=True, color=ACCENT_2)
    add_text(s,
             "Tier 1 alone (Phase 0 + Phase 1) costs <$2K — enough to decide whether either paper is viable.",
             Inches(0.6), Inches(5.9), Inches(12), Inches(0.5),
             size=12, color=INK_SOFT, italic=True)

    add_footer(s, 14, 18)


def slide_cosmos_meh(prs):
    s = blank_slide(prs)
    add_title(s, "Risk hedge — what ships if Cosmos doesn't transfer",
              sub="Pre-register the diagnostic framing before running Cosmos experiments.")
    add_subtitle_strip(s, "‘COSMOS-IS-MEH’ RECOVERY NARRATIVE")

    # Header
    add_text(s,
             "Most likely empirical outcome: Cosmos doesn't beat ViT-B/16 on surgical forecasting "
             "(natural-world pretraining ≠ endoscopic close-ups).",
             Inches(0.6), Inches(1.85), Inches(12.2), Inches(0.7),
             size=13, color=INK_SOFT, italic=True)

    # Three narratives
    panel_top = Inches(2.55)
    panel_h = Inches(4.0)
    panel_w = Inches(4.0)

    narratives = [
        ("NARRATIVE 1 (primary)",
         "Pixel-prediction quality is a weak proxy for surgical forecasting.",
         "Cosmos generates clean pixels but mid-pack features. The diagnostic itself is the contribution.",
         ACCENT, RGBColor(0xEF, 0xF6, 0xFF)),
        ("NARRATIVE 2",
         "Domain gap dominates; surgical-native FMs win.",
         "Cosmos < ViT-B/16 < SurgMotion / SurgVISTA. Quantifies the surgical-domain gap; motivates Paper 2B.",
         ACCENT_2, RGBColor(0xF0, 0xFD, 0xFA)),
        ("NARRATIVE 3 (fallback)",
         "Cosmos as calibration anchor.",
         "Even if no FM wins, Cosmos in the matrix tells the field when surgical pretraining specifically helps.",
         ACCENT_3, RGBColor(0xFE, 0xF3, 0xC7)),
    ]

    for i, (label, headline, body, color, bg) in enumerate(narratives):
        left = Inches(0.5) + i * Inches(4.3)
        add_panel(s, left, panel_top, panel_w, panel_h,
                  fill=bg, line=color, line_w=1.0)
        add_text(s, label, left + Inches(0.2), panel_top + Inches(0.15),
                 panel_w - Inches(0.4), Inches(0.4),
                 size=11, bold=True, color=color)
        add_text(s, headline, left + Inches(0.2),
                 panel_top + Inches(0.55),
                 panel_w - Inches(0.4), Inches(1.4),
                 size=15, bold=True, color=INK)
        add_text(s, body, left + Inches(0.2),
                 panel_top + Inches(1.95),
                 panel_w - Inches(0.4), Inches(2.0),
                 size=12, color=INK_SOFT)

    # Tactic
    add_text(s,
             "Tactic: decide and document the framing **before** running Cosmos experiments. "
             "If Cosmos wins → pivot to positive story; if it loses → the pre-committed paper still ships.",
             Inches(0.6), Inches(6.75), Inches(12.2), Inches(0.5),
             size=12, bold=True, color=ACCENT_5)

    add_footer(s, 15, 18)


def slide_what_we_avoid(prs):
    s = blank_slide(prs)
    add_title(s, "What we deliberately avoid",
              sub="Framing traps that would make the papers harder to defend.")
    add_subtitle_strip(s, "GUARDRAILS")

    bad_left = Inches(0.6)
    good_left = Inches(7.0)

    add_text(s, "Won't do", bad_left, Inches(1.85), Inches(6), Inches(0.4),
             size=18, bold=True, color=ACCENT_5)
    add_bullets(s, [
        ("**Vendor-first framing** — \"NVIDIA Cosmos + OpenUSD for surgery\" reads as product adoption."),
        ("**First-surgical-FM claim** — the field already has SurgMotion, SurgVISTA, ZEN, EndoMamba."),
        ("**OpenUSD as decoration** — if a flat JSON gives the same signal, USD isn't load-bearing."),
        ("**Full Cosmos fine-tuning as the first move** — too expensive without prior evidence of transfer."),
        ("**Single-fold headline numbers** — the field expects 5-fold + cross-center + paired stats."),
        ("**Claiming clinical readiness** — these are benchmark / method papers, not deployment papers."),
    ], bad_left, Inches(2.25), Inches(6.2), Inches(5),
       size=12, bullet_color=ACCENT_5, line_spacing=1.18)

    add_text(s, "Will do", good_left, Inches(1.85), Inches(6), Inches(0.4),
             size=18, bold=True, color=ACCENT_2)
    add_bullets(s, [
        ("**Causal evaluation as the apparatus** — strict prefix-only, leakage-safe, deployment-relevant."),
        ("**Systematic transfer matrix** — physical-AI + general-video + surgical-native FMs all measured."),
        ("**Pre-registered narratives** — Cosmos-meh diagnostic framing decided before running experiments."),
        ("**Staged compute** — <$2K to first go/no-go, full program only if signal exists."),
        ("**5-fold MB140 + cross-center + paired bootstrap** — reviewer-proof stats."),
        ("**Releasable artifacts** — code, leaderboard, feature caches, manifests."),
    ], good_left, Inches(2.25), Inches(6.2), Inches(5),
       size=12, bullet_color=ACCENT_2, line_spacing=1.18)

    add_footer(s, 16, 18)


def slide_open_questions(prs):
    s = blank_slide(prs)
    add_title(s, "Open questions for external review",
              sub="Top items I want reviewer / collaborator pushback on.")
    add_subtitle_strip(s, "ASK ME ABOUT THESE")

    items = [
        ("**Is the two-paper split the right call?** Or would the field reward one comprehensive paper?"),
        ("**Is Cosmos the right physical-AI baseline?** Should V-JEPA 2.1 + SurgMotion be the primary FM pair?"),
        ("**Venue fit for Paper 2A** — MICCAI 2027 or CVPR 2027?"),
        ("**Venue fit for Paper 2B** — does the privileged-information distillation framing clear NeurIPS / ICLR?"),
        ("**Is the diagnostic claim a real contribution** or face-saving framing? How would a vision reviewer read it?"),
        ("**Is the compute budget realistic** ($21K full upper bound) or should we scope to Stage 1 first?"),
        ("**Is there a recent surgical-FM paper** from mid-2026 that we've missed?"),
        ("**OpenUSD side experiment** — cut entirely or keep as appendix?"),
        ("**Variability-scaling thesis for anticipation tasks** — does H(z) still measure the right thing?"),
        ("**Cross-procedure generalization** — push to 4 procedures (MB140 + Cholec80 + AutoLaparo + CholecT50) or stay focused?"),
    ]
    add_bullets(s, items, Inches(0.6), Inches(1.85), Inches(12.2), Inches(5.2),
                size=12, bullet_color=ACCENT_4, line_spacing=1.18)
    add_footer(s, 17, 18)


def slide_closing(prs):
    s = blank_slide(prs)

    # Decorative accent
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, Inches(0.10))
    bar.fill.solid(); bar.fill.fore_color.rgb = ACCENT; bar.line.fill.background()

    add_text(s, "Bottom line",
             Inches(0.8), Inches(1.5), Inches(12), Inches(0.8),
             size=44, bold=True, color=INK)

    add_text(s,
             "Two papers, sequenced. Paper 2A first (decision-gated), then Paper 2B on shared infrastructure.",
             Inches(0.8), Inches(2.4), Inches(12), Inches(0.6),
             size=18, color=ACCENT)

    # Key takeaways
    add_bullets(s, [
        ("**Flagship contribution:** causal-evaluation apparatus + variability-scaling generalization."),
        ("**Cosmos and OpenUSD:** in the matrix, not in the title."),
        ("**Budget:** <$2K to first go/no-go; ~$15K–$21K for the full two-paper program."),
        ("**Schedule:** Paper 2A → MICCAI 2027 (Mar); Paper 2B → NeurIPS 2027 (May)."),
        ("**Both papers ship** even if Cosmos doesn't transfer — the apparatus and the method are the contributions."),
    ], Inches(0.8), Inches(3.4), Inches(12), Inches(3.0),
       size=15, bullet_color=ACCENT_2, line_spacing=1.4)

    add_text(s, "Companion docs: NEXT_PAPER_BRIEF.md   ·   NEXT_PAPER_PLAN.md",
             Inches(0.8), Inches(6.8), Inches(12), Inches(0.4),
             size=12, italic=True, color=INK_MUTE)
    add_footer(s, 18, 18)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    slide_title(prs)
    slide_where_we_are(prs)
    slide_what_is_missing(prs)
    slide_research_question(prs)
    slide_two_paper_overview(prs)
    slide_paper_2a_innovation(prs)
    slide_paper_2a_design(prs)
    slide_paper_2a_contribution(prs)
    slide_paper_2b_innovation(prs)
    slide_paper_2b_method(prs)
    slide_paper_2b_contribution(prs)
    slide_combined_value(prs)
    slide_timeline(prs)
    slide_compute_risk(prs)
    slide_cosmos_meh(prs)
    slide_what_we_avoid(prs)
    slide_open_questions(prs)
    slide_closing(prs)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT_PATH))
    print(f"wrote {OUT_PATH}")
    print(f"slides: {len(prs.slides)}")


if __name__ == "__main__":
    main()

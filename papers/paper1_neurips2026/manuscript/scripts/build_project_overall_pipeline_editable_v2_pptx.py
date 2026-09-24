"""Build a polished editable PPTX variant of the overall pipeline figure.

This version keeps all 8 sampled BBP12 frames visible as a horizontal
prefix strip and simplifies the diagram into three readable branches:
visual model path, workflow-token construction, and evaluation question.

Output:
    paper/figures/fig_project_overall_pipeline_8frame_v2_editable.pptx
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_project_overall_pipeline_editable_pptx as base


OUT = base.ROOT / "figures/fig_project_overall_pipeline_8frame_v2_editable.pptx"


def add_prefix_strip() -> None:
    base.textbox(
        "Prefix title",
        0.42,
        0.88,
        4.8,
        0.20,
        "Observed prefix clip x_1:t",
        10.0,
        base.COLORS["ink"],
        True,
    )
    base.textbox(
        "Prefix subtitle",
        4.25,
        0.88,
        4.9,
        0.20,
        "8 sampled frames from a real MB140 / BBP12 case; orange marks the current timestamp.",
        7.4,
        base.COLORS["muted"],
    )

    x0, y, w, h, gap = 0.42, 1.16, 1.08, 0.64, 0.06
    for idx in range(8):
        x = x0 + idx * (w + gap)
        base.picture(f"Prefix frame {idx + 1}", f"rId{idx + 2}", x, y, w, h, crop_tb=9000)
        base.shape("Frame border", "rect", x, y, w, h, None, "D1D5DB", 0.6)
        base.textbox(
            "Frame index",
            x + 0.36,
            y + h + 0.04,
            0.36,
            0.10,
            f"x_{idx + 1}",
            5.7,
            base.COLORS["muted"],
            False,
            "ctr",
        )

    xt_x = x0 + 7 * (w + gap)
    base.shape("Current time border", "rect", xt_x, y, w, h, None, base.COLORS["orange"], 2.0)
    base.shape("Current time badge", "rect", xt_x, y, 0.42, 0.20, "000000", no_line=True)
    base.textbox("xt badge text", xt_x + 0.04, y + 0.03, 0.34, 0.12, "x_t", 7.5, "FFFFFF", True, "ctr")

    # Compact protocol reminder.
    base.shape("Protocol note", "roundRect", 10.10, 1.05, 2.78, 0.78, "EFF6FF", base.COLORS["blue"], 0.8)
    base.textbox("Protocol note title", 10.28, 1.18, 2.40, 0.18, "strict prefix-only protocol", 7.4, base.COLORS["blue"], True, "ctr")
    base.textbox("Protocol note body", 10.28, 1.42, 2.40, 0.22, "clip ends at t; no future frames", 7.0, base.COLORS["ink"], False, "ctr")


def add_visual_path() -> None:
    base.panel_label(0.42, 2.18, "1. Visual model path")
    y = 2.62
    base.block(0.62, y, 1.06, 0.58, "8-frame\nclip", base.COLORS["blue_light"], base.COLORS["blue"], 7.0)
    base.arrow(1.72, y + 0.29, 2.18, y + 0.29, base.COLORS["edge"])
    base.block(2.24, y, 1.30, 0.58, "ViT-B/16\nframe encoder", base.COLORS["blue_light"], base.COLORS["blue"], 7.0)
    base.arrow(3.58, y + 0.29, 4.04, y + 0.29, base.COLORS["edge"])
    base.feature_matrix(4.12, 2.42, 0.95, 0.92)
    base.arrow(5.12, y + 0.29, 5.60, y + 0.29, base.COLORS["teal"])
    base.block(5.66, y, 1.30, 0.58, "append\nworkflow token", base.COLORS["teal_light"], base.COLORS["teal"], 6.8)
    base.arrow(7.00, y + 0.29, 7.42, y + 0.29, base.COLORS["edge"])
    base.block(7.48, y, 1.28, 0.58, "9-token\nsequence", base.COLORS["gray_light"], base.COLORS["edge"], 6.8)
    base.arrow(8.80, y + 0.29, 9.26, y + 0.29, base.COLORS["edge"])
    base.block(9.32, 2.45, 1.42, 0.92, "HTA-inspired\n6-block\ntemporal head", base.COLORS["gray_light"], base.COLORS["edge"], 7.0)

    # Outputs.
    for yy, label, fill, stroke in [
        (2.25, "RSD\nhead", "EEF2FF", base.COLORS["blue"]),
        (2.78, "phase\nhead", "F0FDF4", base.COLORS["teal"]),
        (3.31, "deviation\nhead", base.COLORS["orange_light"], base.COLORS["orange"]),
    ]:
        base.arrow(10.76, 2.91, 11.24, yy + 0.20, base.COLORS["edge"])
        base.block(11.28, yy, 0.88, 0.40, label, fill, stroke, 6.2)
    base.block(12.38, 2.34, 0.98, 0.58, "remaining\nsurgery\nduration", "EEF2FF", base.COLORS["blue"], 6.0)
    base.arrow(12.18, 2.45, 12.36, 2.58, base.COLORS["blue"])


def add_workflow_branch() -> None:
    base.panel_label(0.42, 3.86, "2. Workflow signal")

    # Oracle path.
    base.textbox("Oracle path label", 0.56, 4.24, 1.55, 0.18, "oracle diagnostic path", 7.2, base.COLORS["purple"], True)
    base.block(0.56, 4.52, 1.08, 0.46, "full phase\nsequence", base.COLORS["purple_light"], base.COLORS["purple"], 6.2)
    base.phase_sequence(0.68, 5.10, 0.84, 0.16)
    base.arrow(1.68, 4.75, 2.10, 4.75, base.COLORS["purple"])

    # Causal path.
    base.textbox("Causal path label", 0.56, 5.55, 1.70, 0.18, "causal-at-inference path", 7.2, base.COLORS["teal"], True)
    base.block(0.56, 5.82, 1.08, 0.42, "prefix\npixels", base.COLORS["blue_light"], base.COLORS["blue"], 6.2)
    base.arrow(1.68, 6.03, 2.10, 6.03, base.COLORS["teal"])
    base.block(2.16, 5.82, 1.08, 0.42, "phase-head\npredictions", base.COLORS["gray_light"], base.COLORS["gray"], 5.8)
    base.arrow(3.28, 6.03, 3.70, 6.03, base.COLORS["teal"])
    base.block(3.76, 5.82, 1.20, 0.42, "prefix phase\nsequence", base.COLORS["teal_light"], base.COLORS["teal"], 5.8)

    # Shared map and token.
    base.block(2.16, 4.52, 1.14, 0.46, "phase\nbigrams", base.COLORS["purple_light"], base.COLORS["purple"], 6.2)
    base.arrow(3.34, 4.75, 3.74, 4.75, base.COLORS["gray"])
    base.block(3.80, 4.52, 1.30, 0.46, "TF-IDF\n+ PCA", base.COLORS["orange_light"], base.COLORS["orange"], 6.2)
    base.arrow(5.13, 4.75, 5.54, 4.75, base.COLORS["gray"])
    base.block(5.60, 4.52, 1.20, 0.46, "centroid\nmap", base.COLORS["orange_light"], base.COLORS["orange"], 6.2)
    base.arrow(4.96, 6.03, 5.86, 5.00, base.COLORS["teal"])
    base.arrow(6.82, 4.75, 7.24, 4.75, base.COLORS["teal"])
    base.block(7.30, 4.52, 1.34, 0.46, "z or posterior q", base.COLORS["teal_light"], base.COLORS["teal"], 6.0)
    base.arrow(8.68, 4.75, 9.08, 4.75, base.COLORS["teal"])
    base.block(9.14, 4.45, 1.36, 0.60, "workflow token\nE[z] or sum q_k E[k]", base.COLORS["teal_light"], base.COLORS["teal"], 5.8)
    base.arrow(9.82, 4.43, 6.42, 3.21, base.COLORS["teal"])

    base.textbox(
        "No label note",
        5.25,
        5.84,
        5.20,
        0.20,
        "At inference: no ground-truth phase labels and no full-case workflow labels.",
        6.7,
        base.COLORS["teal"],
        False,
    )


def add_evaluation_branch() -> None:
    base.panel_label(10.78, 3.86, "3. Evaluation question")
    base.block(10.90, 4.34, 1.08, 0.46, "MB140\nwithin-center", base.COLORS["green_light"], base.COLORS["teal"], 6.1)
    base.block(12.12, 4.34, 1.10, 0.46, "MB140\ncross-center", base.COLORS["teal_light"], base.COLORS["teal"], 6.1)
    base.block(10.90, 5.04, 1.08, 0.46, "Cholec80\ncontrast", base.COLORS["gray_light"], base.COLORS["gray"], 6.1)
    base.block(12.12, 5.04, 1.10, 0.46, "shuffled-token\ncontrol", base.COLORS["purple_light"], base.COLORS["purple"], 5.8)
    base.block(10.90, 5.74, 2.32, 0.44, "strict prefix-only vs centered-window", base.COLORS["blue_light"], base.COLORS["blue"], 5.9)
    base.textbox(
        "Claim",
        10.88,
        6.34,
        2.38,
        0.34,
        "Claim: workflow conditioning helps when workflow variation exists and the token carries meaning.",
        6.4,
        base.COLORS["ink"],
        True,
        "ctr",
    )


def build_slide_xml() -> bytes:
    base.parts.clear()
    base.shape_id = 1
    base.shape("Background", "rect", 0, 0, base.SLIDE_W, base.SLIDE_H, "FFFFFF", no_line=True)
    base.textbox("Title", 1.80, 0.10, 10.0, 0.28, "Overall pipeline: workflow-conditioned RSD prediction", 14.4, base.COLORS["ink"], True, "ctr")
    base.textbox(
        "Subtitle",
        1.30,
        0.44,
        11.0,
        0.20,
        "The model combines visual prefix evidence with a workflow token, then tests whether that token helps across datasets and protocols.",
        7.8,
        base.COLORS["muted"],
        False,
        "ctr",
    )
    add_prefix_strip()
    add_visual_path()
    add_workflow_branch()
    add_evaluation_branch()
    base.line("Footer rule", 0.38, 6.78, 13.22, 6.78, "E5E7EB", 0.6)
    base.textbox(
        "Footer",
        1.05,
        6.86,
        11.50,
        0.12,
        "Study scope: MultiBypass140 + Cholec80 | conditions: no-token, retrospective oracle, causal-at-inference | metric: validation MAE in minutes",
        6.2,
        base.COLORS["muted"],
        False,
        "ctr",
    )

    xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        "<p:grpSpPr/>"
        f"{''.join(base.parts)}"
        "</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"
    )
    return xml.encode("utf-8")


def main() -> None:
    missing = [str(p) for p in base.ASSETS if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing frame assets: {missing}")
    slide_xml = build_slide_xml()
    rels_xml = base.build_rels().encode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(base.TEMPLATE, "r") as zin, ZipFile(OUT, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in {"ppt/slides/slide1.xml", "ppt/slides/_rels/slide1.xml.rels"}:
                continue
            data = zin.read(item.filename)
            if item.filename == "ppt/presentation.xml":
                data = base.update_presentation_size(data)
            zout.writestr(item, data)
        zout.writestr("ppt/slides/slide1.xml", slide_xml)
        zout.writestr("ppt/slides/_rels/slide1.xml.rels", rels_xml)
        for idx, asset in enumerate(base.ASSETS, start=1):
            zout.writestr(f"ppt/media/project_pipeline_frame{idx}.jpeg", asset.read_bytes())

    print(OUT)


if __name__ == "__main__":
    main()

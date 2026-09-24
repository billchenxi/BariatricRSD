"""Build an editable PPTX explaining the workflow-cluster module.

This figure explains the box often labeled "Build workflow clusters
(offline)": it is a latent workflow-style discovery module that converts
phase-order information into a cluster ID/posterior, then into the workflow
token used by the RSD model.

Output:
    paper/figures/fig_workflow_cluster_module_explainer_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/fig_workflow_cluster_module_explainer_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

SLIDE_W = 13.60
SLIDE_H = 6.95

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


def box(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    *,
    fill: str,
    stroke: str,
    title_color: str | None = None,
    title_pt: float = 7.2,
    body: str | None = None,
    body_pt: float = 5.8,
) -> None:
    base.shape("Box", "roundRect", x, y, w, h, fill, stroke, 0.9)
    base.textbox("Box title", x + 0.08, y + 0.10, w - 0.16, 0.17, title, title_pt, title_color or COLORS["ink"], True, "ctr")
    if body:
        base.textbox("Box body", x + 0.10, y + 0.37, w - 0.20, h - 0.44, body, body_pt, COLORS["ink"], False, "ctr")


def panel(x: float, y: float, w: float, h: float, title: str, stroke: str, fill: str = "FFFFFF") -> None:
    base.shape("Panel", "roundRect", x, y, w, h, fill, stroke, 1.0)
    base.textbox("Panel title", x + 0.18, y + 0.12, w - 0.36, 0.18, title, 9.2, stroke, True, "ctr")


def phase_sequence(x: float, y: float, w: float, h: float, *, prefix: bool = False) -> None:
    stroke = COLORS["teal"] if prefix else COLORS["purple"]
    fill = COLORS["teal_light"] if prefix else COLORS["purple_light"]
    box(
        x,
        y,
        w,
        h,
        "phase sequence" if not prefix else "prefix phases",
        fill=fill,
        stroke=stroke,
        title_color=stroke,
        title_pt=6.1,
    )
    colors = ["2563EB", "F59E0B", "7C3AED", "DB2777", "0F766E", "D97706"]
    labels = ["A", "B", "C", "D", "E", "F"]
    max_i = 4 if prefix else 6
    gap = 0.07
    dot = 0.15
    start_x = x + (w - max_i * dot - (max_i - 1) * gap) / 2
    for i in range(max_i):
        base.shape("Phase dot", "ellipse", start_x + i * (dot + gap), y + 0.50, dot, dot, colors[i], colors[i], 0.1, labels[i], 4.2, "FFFFFF", True)
        if i < max_i - 1:
            base.line("Phase connector", start_x + i * (dot + gap) + dot, y + 0.575, start_x + (i + 1) * (dot + gap), y + 0.575, COLORS["edge"], 0.35)
    note = "full case" if not prefix else "observed so far"
    base.textbox("Phase note", x + 0.08, y + h - 0.17, w - 0.16, 0.10, note, 4.6, COLORS["muted"], False, "ctr")


def bigrams(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "transition bigrams", fill=COLORS["purple_light"], stroke=COLORS["purple"], title_color=COLORS["purple"], title_pt=6.0)
    pairs = ["(A,B)", "(B,C)", "(C,D)", "(D,E)"]
    for i, txt in enumerate(pairs):
        xx = x + 0.18 + (i % 2) * 0.52
        yy = y + 0.44 + (i // 2) * 0.22
        base.shape("Bigram chip", "roundRect", xx, yy, 0.44, 0.15, "FFFFFF", COLORS["purple"], 0.35, txt, 4.5, COLORS["ink"], True)
    base.textbox("Bigram note", x + 0.11, y + 0.88, w - 0.22, 0.10, "order pattern features", 4.5, COLORS["muted"], False, "ctr")


def tfidf_matrix(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "TF-IDF corpus matrix", fill=COLORS["orange_light"], stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=5.8)
    gx, gy = x + 0.18, y + 0.42
    rows, cols = 5, 6
    for r in range(rows):
        for c in range(cols):
            fill = "FDBA74" if c in (0, 3) else ("FED7AA" if (r + c) % 2 == 0 else "FFFFFF")
            base.shape("TFIDF cell", "rect", gx + c * 0.105, gy + r * 0.085, 0.095, 0.075, fill, COLORS["border"], 0.15)
    base.textbox("TFIDF axes", x + 0.14, y + 0.90, w - 0.28, 0.10, "videos x bigrams", 4.5, COLORS["muted"], False, "ctr")


def pca_kmeans(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "PCA + k-means", fill=COLORS["orange_light"], stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=6.1)
    px, py = x + 0.34, y + 0.50
    base.line("PCA axis x", px - 0.14, py + 0.22, px + 0.92, py + 0.22, COLORS["muted"], 0.35, arrow=True)
    base.line("PCA axis y", px, py + 0.42, px, py - 0.12, COLORS["muted"], 0.35, arrow=True)
    clusters = [
        (0.16, 0.08, COLORS["teal"]),
        (0.24, 0.22, COLORS["teal"]),
        (0.54, 0.14, COLORS["blue"]),
        (0.62, 0.32, COLORS["blue"]),
        (0.78, 0.06, COLORS["orange"]),
        (0.86, 0.24, COLORS["orange"]),
    ]
    for dx, dy, col in clusters:
        base.shape("Cluster point", "ellipse", px + dx, py + dy, 0.065, 0.065, col, col, 0.1)
    for cx, cy, col in [(0.20, 0.15, COLORS["teal"]), (0.58, 0.23, COLORS["blue"]), (0.82, 0.15, COLORS["orange"])]:
        base.shape("Centroid", "diamond", px + cx - 0.045, py + cy - 0.045, 0.09, 0.09, "FFFFFF", col, 0.75)
    base.textbox("Centroid note", x + 0.12, y + 0.90, w - 0.24, 0.10, "centroids = reusable artifacts", 4.5, COLORS["muted"], False, "ctr")


def cluster_output(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "workflow cluster", fill=COLORS["purple_light"], stroke=COLORS["purple"], title_color=COLORS["purple"], title_pt=6.0)
    base.shape("z circle", "ellipse", x + 0.34, y + 0.43, 0.46, 0.46, COLORS["purple_light"], COLORS["purple"], 1.1, "z", 16.0, COLORS["purple"], True)
    base.textbox("z note", x + 0.12, y + 0.95, w - 0.24, 0.10, "latent workflow style", 4.5, COLORS["muted"], False, "ctr")


def posterior_output(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "posterior q(z)", fill=COLORS["teal_light"], stroke=COLORS["teal"], title_color=COLORS["teal"], title_pt=6.0)
    baseline_y = y + (0.83 if h >= 0.95 else h - 0.18)
    scale = 1.0 if h >= 0.95 else 0.75
    base.line("q baseline", x + 0.22, baseline_y, x + w - 0.20, baseline_y, COLORS["muted"], 0.35)
    vals = [0.22, 0.48, 0.14, 0.36, 0.18]
    for i, val in enumerate(vals):
        color = COLORS["teal"] if i == 1 else "99F6E4"
        height = val * scale
        base.shape("q bar", "rect", x + 0.30 + i * 0.15, baseline_y - height, 0.08, height, color, COLORS["teal"], 0.2)
    if h >= 0.95:
        base.textbox("q note", x + 0.10, y + h - 0.14, w - 0.20, 0.10, "soft cluster assignment", 4.5, COLORS["muted"], False, "ctr")


def token_box(x: float, y: float, w: float, h: float, *, mode: str = "both") -> None:
    box(x, y, w, h, "workflow token w", fill=COLORS["teal_light"], stroke=COLORS["teal"], title_color=COLORS["teal"], title_pt=6.2)
    if mode == "oracle":
        base.textbox("Token formula hard", x + 0.10, y + 0.46, w - 0.20, 0.12, "w = E[z_full]", 5.4, COLORS["ink"], True, "ctr")
        base.textbox("Token formula note", x + 0.10, y + 0.62, w - 0.20, 0.10, "hard lookup", 4.5, COLORS["muted"], False, "ctr")
    elif mode == "causal":
        base.textbox("Token formula soft", x + 0.10, y + 0.48, w - 0.20, 0.12, "w = sum_k q_k E[k]", 5.0, COLORS["ink"], True, "ctr")
    else:
        base.textbox("Token formula hard", x + 0.10, y + 0.40, w - 0.20, 0.12, "oracle: w = E[z]", 5.0, COLORS["ink"], False, "ctr")
        base.textbox("Token formula soft", x + 0.10, y + 0.58, w - 0.20, 0.12, "causal: w = sum_k q_k E[k]", 5.0, COLORS["ink"], False, "ctr")
    base.shape("Token row", "rect", x + 0.36, y + h - 0.20, w - 0.72, 0.14, COLORS["purple"], COLORS["purple"], 0.1)


def frame_feature_matrix(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "frame features F", fill=COLORS["blue_light"], stroke=COLORS["blue"], title_color=COLORS["blue"], title_pt=6.0)
    mx, my = x + 0.24, y + 0.40
    mw, mh = w - 0.48, h - 0.65
    base.shape("F matrix", "rect", mx, my, mw, mh, "FFFFFF", COLORS["blue"], 0.65)
    for r in range(1, 8):
        base.line("F row", mx, my + r * mh / 8, mx + mw, my + r * mh / 8, "BFDBFE", 0.35)
    for r in range(8):
        yy = my + (r + 0.5) * mh / 8
        for c in range(4):
            xx = mx + 0.12 + c * (mw - 0.24) / 3
            base.shape("F dot", "ellipse", xx - 0.018, yy - 0.018, 0.036, 0.036, COLORS["blue"], COLORS["blue"], 0.1)
    base.textbox("F shape", x + 0.10, y + h - 0.20, w - 0.20, 0.10, "F in R^(8 x 768)", 4.9, COLORS["blue"], True, "ctr")


def temporal_use(x: float, y: float, w: float, h: float) -> None:
    box(x, y, w, h, "How it enters the RSD model", fill=COLORS["yellow_light"], stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=7.0)
    frame_feature_matrix(x + 0.18, y + 0.42, 0.92, 1.05)
    base.arrow(x + 1.14, y + 0.94, x + 1.34, y + 0.94, COLORS["orange"])
    token_box(x + 1.40, y + 0.42, 1.15, 1.05)
    base.arrow(x + 2.59, y + 0.94, x + 2.78, y + 0.94, COLORS["orange"])
    box(x + 2.84, y + 0.42, 1.02, 1.05, "sequence S", fill="FFFFFF", stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=5.8)
    base.textbox("S formula", x + 2.93, y + 0.82, 0.84, 0.13, "S = [w ; f1 ; ... ; f8]", 4.9, COLORS["ink"], True, "ctr")
    base.textbox("S shape", x + 2.93, y + 1.04, 0.84, 0.11, "R^(9 x 768)", 4.4, COLORS["muted"], False, "ctr")
    base.textbox("No plus", x + 2.94, y + 1.24, 0.82, 0.10, "prepend, not +", 4.3, COLORS["red"], True, "ctr")
    base.arrow(x + 3.91, y + 0.94, x + 4.10, y + 0.94, COLORS["edge"])
    box(x + 4.16, y + 0.42, 0.82, 1.05, "HTA", fill=COLORS["gray_light"], stroke=COLORS["edge"], title_pt=6.0)
    for i in range(5):
        base.shape("HTA line", "roundRect", x + 4.30, y + 0.73 + i * 0.09, 0.54, 0.05, "E5E7EB", COLORS["edge"], 0.18)
    base.arrow(x + 5.03, y + 0.94, x + 5.22, y + 0.94, COLORS["edge"])
    box(x + 5.28, y + 0.42, 0.58, 1.05, "heads", fill="FFFFFF", stroke=COLORS["orange"], title_color=COLORS["orange"], title_pt=5.4)
    for i, lab in enumerate(["RSD", "phase", "dev"]):
        base.shape("Head chip", "roundRect", x + 5.36, y + 0.72 + i * 0.18, 0.42, 0.12, "FFFFFF", COLORS["orange"], 0.25, lab, 3.7, COLORS["ink"], True)


def build_slide_xml() -> bytes:
    set_slide_size()
    base.parts.clear()
    base.shape_id = 1

    base.textbox("Title", 0.42, 0.16, 12.80, 0.30, "Workflow clusters: what this module is and why it is in the project", 15.0, COLORS["ink"], True, "ctr")
    base.textbox(
        "Subtitle",
        0.84,
        0.54,
        11.90,
        0.20,
        "It converts phase-order patterns into a latent workflow-style token, then prepends that token to visual frame features for RSD prediction.",
        7.5,
        COLORS["muted"],
        False,
        "ctr",
    )

    # Offline artifact fitting.
    panel(0.42, 0.95, 12.76, 1.82, "1. Fit workflow-clustering artifacts offline on training videos", COLORS["teal"], COLORS["teal_light"])
    phase_sequence(0.78, 1.34, 1.20, 1.05)
    base.arrow(2.04, 1.86, 2.34, 1.86, COLORS["purple"])
    bigrams(2.40, 1.34, 1.22, 1.05)
    base.arrow(3.68, 1.86, 3.98, 1.86, COLORS["edge"])
    tfidf_matrix(4.04, 1.34, 1.28, 1.05)
    base.arrow(5.38, 1.86, 5.68, 1.86, COLORS["edge"])
    pca_kmeans(5.74, 1.34, 1.58, 1.05)
    base.arrow(7.38, 1.86, 7.68, 1.86, COLORS["edge"])
    cluster_output(7.74, 1.34, 1.12, 1.05)
    base.arrow(8.92, 1.86, 9.22, 1.86, COLORS["teal"])
    box(
        9.28,
        1.34,
        3.36,
        1.05,
        "saved artifacts",
        fill="FFFFFF",
        stroke=COLORS["teal"],
        title_color=COLORS["teal"],
        title_pt=6.3,
        body="vocabulary + IDF, PCA transform, k-means centroids, embedding table E",
        body_pt=5.4,
    )

    # Assignment paths.
    panel(0.42, 3.05, 6.20, 3.00, "2. Use artifacts to assign workflow signal", COLORS["purple"], "FFFFFF")
    base.textbox("Oracle path label", 0.74, 3.48, 2.10, 0.14, "Oracle diagnostic path", 6.8, COLORS["purple"], True)
    phase_sequence(0.76, 3.72, 1.12, 0.98)
    base.arrow(1.94, 4.22, 2.24, 4.22, COLORS["purple"])
    cluster_output(2.30, 3.72, 1.00, 0.98)
    base.arrow(3.36, 4.22, 3.66, 4.22, COLORS["purple"])
    token_box(3.72, 3.72, 1.50, 0.98, mode="oracle")
    base.textbox("Oracle note", 0.78, 4.86, 4.62, 0.14, "Full-surgery phase order gives z_full. This is useful for diagnosis and upper-bound experiments.", 5.2, COLORS["muted"], False, "ctr")

    base.line("Path divider", 0.72, 5.02, 6.30, 5.02, "E5E7EB", 0.55)
    base.textbox("Causal path label", 0.74, 5.14, 2.18, 0.14, "Causal-at-inference path", 6.8, COLORS["teal"], True)
    phase_sequence(0.76, 5.36, 1.12, 0.82, prefix=True)
    base.arrow(1.94, 5.78, 2.24, 5.78, COLORS["teal"])
    posterior_output(2.30, 5.36, 1.00, 0.82)
    base.arrow(3.36, 5.78, 3.66, 5.78, COLORS["teal"])
    token_box(3.72, 5.36, 1.50, 0.82, mode="causal")
    base.textbox("Causal note", 0.78, 6.20, 4.62, 0.12, "Prefix phases are predicted from observed pixels, then mapped to q(z | prefix).", 5.0, COLORS["muted"], False, "ctr")

    # Relation to RSD model.
    panel(6.86, 3.05, 6.32, 3.00, "3. Relation to the overall RSD project", COLORS["orange"], COLORS["yellow_light"])
    temporal_use(7.02, 3.52, 5.92, 1.56)
    base.textbox(
        "Project relation",
        7.18,
        5.16,
        5.56,
        0.36,
        "Purpose: test whether explicit workflow-style information improves remaining-surgery-duration prediction beyond visual evidence alone.",
        6.1,
        COLORS["ink"],
        True,
        "ctr",
    )

    # Bottom clarifier.
    base.shape("Clarifier", "roundRect", 0.64, 6.34, 12.16, 0.42, COLORS["blue_light"], COLORS["blue"], 0.75)
    base.textbox(
        "Clarifier text",
        0.88,
        6.47,
        11.68,
        0.13,
        "This module is not the ViT visual encoder. It is a side-channel that summarizes procedural order/variation and produces the workflow token w.",
        6.0,
        COLORS["blue"],
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

"""Build a more detailed editable PPTX for the overall pipeline figure.

Compared with v2, this version gives every major box an internal diagram
instead of text-only nodes. All diagram components are native PowerPoint
shapes except the real BBP12 frame thumbnails.

Output:
    paper/figures/fig_project_overall_pipeline_8frame_v3_detailed_editable.pptx
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_project_overall_pipeline_editable_pptx as base


OUT = base.ROOT / "figures/fig_project_overall_pipeline_8frame_v3_detailed_editable.pptx"


def box(x, y, w, h, title, fill, stroke, title_pt=6.6):
    base.shape("Diagram box", "roundRect", x, y, w, h, fill, stroke, 0.9)
    base.textbox("Box title", x + 0.06, y + h - 0.22, w - 0.12, 0.16, title, title_pt, base.COLORS["ink"], True, "ctr")


def mini_clip(x, y, w, h):
    box(x, y, w, h, "8-frame clip", base.COLORS["blue_light"], base.COLORS["blue"])
    pad_x, pad_y = 0.10, 0.13
    cell_w = (w - 2 * pad_x - 0.09) / 4
    cell_h = (h - 0.44 - 0.06) / 2
    for idx in range(8):
        row, col = divmod(idx, 4)
        xx = x + pad_x + col * (cell_w + 0.03)
        yy = y + pad_y + (1 - row) * (cell_h + 0.06)
        base.picture(f"Mini clip frame {idx+1}", f"rId{idx+2}", xx, yy, cell_w, cell_h, crop_tb=9000)
        base.shape("mini frame border", "rect", xx, yy, cell_w, cell_h, None, "D1D5DB", 0.35)
    base.shape("current frame mark", "rect", x + pad_x + 3 * (cell_w + 0.03), y + pad_y, cell_w, cell_h, None, base.COLORS["orange"], 1.3)


def mini_vit(x, y, w, h):
    box(x, y, w, h, "ViT-B/16 encoder", base.COLORS["blue_light"], base.COLORS["blue"])
    sx, sy = x + 0.18, y + 0.20
    bw, bh = w - 0.36, 0.045
    for i in range(12):
        color = "DBEAFE" if i < 6 else "1D4ED8"
        stroke = "93C5FD" if i < 6 else "1E40AF"
        yy = sy + i * (bh + 0.018)
        base.shape("ViT block", "roundRect", sx, yy, bw, bh, color, stroke, 0.25)
    base.textbox("frozen trainable", x + 0.08, y + 0.66, w - 0.16, 0.12, "6 frozen + 6 trainable blocks", 4.8, base.COLORS["muted"], False, "ctr")


def mini_tensor(x, y, w, h):
    box(x, y, w, h, "8 x 768 tensor", base.COLORS["blue_light"], base.COLORS["blue"])
    mx, my = x + 0.22, y + 0.18
    mw, mh = w - 0.44, h - 0.52
    base.shape("matrix", "rect", mx, my, mw, mh, "EFF6FF", base.COLORS["blue"], 0.6)
    for r in range(1, 8):
        yy = my + r * mh / 8
        base.line("row", mx, yy, mx + mw, yy, "BFDBFE", 0.35)
    for r in range(8):
        yy = my + (r + 0.5) * mh / 8
        for c in range(5):
            xx = mx + 0.10 + c * (mw - 0.20) / 4
            base.shape("feature dot", "ellipse", xx - 0.018, yy - 0.018, 0.036, 0.036, base.COLORS["blue"], base.COLORS["blue"], 0.1)
    base.textbox("tensor axes", mx, my - 0.13, mw, 0.10, "frames x features", 4.8, base.COLORS["muted"], False, "ctr")


def mini_token(x, y, w, h, title="workflow token"):
    box(x, y, w, h, title, base.COLORS["teal_light"], base.COLORS["teal"])
    tx, ty = x + 0.18, y + 0.30
    cell_w = (w - 0.36) / 7
    vals = ["0F766E", "99F6E4", "CCFBF1", "0F766E", "99F6E4", "CCFBF1", "0F766E"]
    for i, color in enumerate(vals):
        base.shape("token cell", "rect", tx + i * cell_w, ty, cell_w - 0.01, 0.18, color, "0F766E", 0.25)
    base.textbox("token label", x + 0.10, y + 0.16, w - 0.20, 0.10, "learned 768-d vector", 4.7, base.COLORS["muted"], False, "ctr")


def mini_sequence(x, y, w, h, title, fill, stroke):
    box(x, y, w, h, title, fill, stroke)
    labels = ["P1", "P2", "P3", "P2", "P4", "P5"]
    colors = ["2563EB", "0F766E", "D97706", "0F766E", "7C3AED", "DB2777"]
    sx, sy = x + 0.14, y + 0.31
    seg_w = (w - 0.28) / len(labels)
    for i, (lab, col) in enumerate(zip(labels, colors)):
        base.shape("phase segment", "rect", sx + i * seg_w, sy, seg_w - 0.01, 0.18, col, "FFFFFF", 0.25, lab, 4.6, "FFFFFF", True)


def mini_bigrams(x, y, w, h):
    box(x, y, w, h, "phase bigrams", base.COLORS["purple_light"], base.COLORS["purple"])
    pairs = ["P1->P2", "P2->P3", "P3->P2"]
    for i, p in enumerate(pairs):
        base.shape("bigram pill", "roundRect", x + 0.14, y + 0.18 + i * 0.18, w - 0.28, 0.13, "EDE9FE", base.COLORS["purple"], 0.35, p, 4.7, base.COLORS["ink"], True)


def mini_tfidf_pca(x, y, w, h):
    box(x, y, w, h, "TF-IDF + PCA", base.COLORS["orange_light"], base.COLORS["orange"])
    # Left: sparse bars.
    bx, by = x + 0.18, y + 0.25
    for i, bh in enumerate([0.10, 0.22, 0.06, 0.28, 0.15]):
        base.shape("tfidf bar", "rect", bx + i * 0.08, by, 0.045, bh, "FDBA74", base.COLORS["orange"], 0.25)
    # Right: projected points.
    sx, sy = x + w - 0.42, y + 0.25
    base.line("pca axis x", sx - 0.20, sy, sx + 0.22, sy, base.COLORS["muted"], 0.35)
    base.line("pca axis y", sx, sy - 0.03, sx, sy + 0.36, base.COLORS["muted"], 0.35)
    for px, py, col in [(-0.12, 0.10, "D97706"), (0.05, 0.24, "7C3AED"), (0.13, 0.14, "0F766E")]:
        base.shape("pca point", "ellipse", sx + px, sy + py, 0.045, 0.045, col, col, 0.1)


def mini_centroids(x, y, w, h):
    box(x, y, w, h, "workflow centroids", base.COLORS["orange_light"], base.COLORS["orange"])
    cx, cy = x + w / 2, y + 0.36
    clusters = [
        (-0.26, -0.02, "0F766E"),
        (-0.08, 0.16, "1D4ED8"),
        (0.20, 0.08, "D97706"),
        (0.30, 0.24, "7C3AED"),
        (0.03, -0.10, "DB2777"),
    ]
    for dx, dy, col in clusters:
        base.shape("cluster cloud", "ellipse", cx + dx - 0.03, cy + dy - 0.03, 0.06, 0.06, col, col, 0.1)
    for dx, dy, col in [(-0.16, 0.06, "0F766E"), (0.24, 0.16, "D97706")]:
        base.shape("centroid", "diamond", cx + dx - 0.045, cy + dy - 0.045, 0.09, 0.09, "FFFFFF", col, 0.75)


def mini_posterior(x, y, w, h):
    box(x, y, w, h, "soft posterior q", base.COLORS["teal_light"], base.COLORS["teal"])
    bx, base_y = x + 0.22, y + 0.23
    base.line("posterior baseline", bx - 0.03, base_y, bx + 0.62, base_y, base.COLORS["muted"], 0.35)
    for i, bh in enumerate([0.12, 0.28, 0.08, 0.42, 0.18, 0.10]):
        color = base.COLORS["teal"] if i == 3 else "99F6E4"
        base.shape("posterior bar", "rect", bx + i * 0.10, base_y, 0.055, bh, color, base.COLORS["teal"], 0.25)
    base.textbox("q simplex", x + 0.12, y + 0.70, w - 0.24, 0.10, "q in Delta^(K-1)", 4.7, base.COLORS["muted"], False, "ctr")


def mini_hta(x, y, w, h):
    box(x, y, w, h, "HTA temporal head", base.COLORS["gray_light"], base.COLORS["edge"])
    sx, sy = x + 0.16, y + 0.18
    for i in range(6):
        yy = sy + i * 0.075
        base.shape("hta block", "roundRect", sx, yy, w - 0.32, 0.05, "E5E7EB", base.COLORS["edge"], 0.22)
    base.line("local branch", sx + 0.10, sy + 0.50, sx + 0.42, sy + 0.50, "7C3AED", 0.65, arrow=True)
    base.line("global branch", sx + 0.10, sy + 0.61, sx + 0.66, sy + 0.61, base.COLORS["teal"], 0.65, arrow=True)
    base.textbox("hta labels", x + 0.12, y + 0.73, w - 0.24, 0.10, "local + global attention", 4.6, base.COLORS["muted"], False, "ctr")


def mini_heads(x, y, w, h):
    box(x, y, w, h, "task heads", base.COLORS["gray_light"], base.COLORS["edge"])
    labels = [("RSD", "EEF2FF", base.COLORS["blue"]), ("phase", "F0FDF4", base.COLORS["teal"]), ("deviation", base.COLORS["orange_light"], base.COLORS["orange"])]
    for i, (lab, fill, stroke) in enumerate(labels):
        base.shape("head", "roundRect", x + 0.18, y + 0.20 + i * 0.18, w - 0.36, 0.13, fill, stroke, 0.35, lab, 4.7, base.COLORS["ink"], True)


def mini_eval(x, y, w, h):
    box(x, y, w, h, "evaluation", "FFFFFF", base.COLORS["edge"])
    items = [
        ("MB140", base.COLORS["teal_light"], base.COLORS["teal"]),
        ("cross-center", base.COLORS["teal_light"], base.COLORS["teal"]),
        ("Cholec80", base.COLORS["gray_light"], base.COLORS["gray"]),
        ("shuffle", base.COLORS["purple_light"], base.COLORS["purple"]),
    ]
    for i, (lab, fill, stroke) in enumerate(items):
        row, col = divmod(i, 2)
        base.shape("eval chip", "roundRect", x + 0.13 + col * 0.55, y + 0.22 + row * 0.22, 0.46, 0.15, fill, stroke, 0.25, lab, 4.0, base.COLORS["ink"], True)


def add_prefix_strip():
    base.textbox("Prefix title", 0.42, 0.75, 3.0, 0.18, "Observed prefix clip", 9.2, base.COLORS["ink"], True)
    x0, y, w, h, gap = 0.42, 0.98, 1.05, 0.58, 0.055
    for idx in range(8):
        x = x0 + idx * (w + gap)
        base.picture(f"Prefix frame {idx + 1}", f"rId{idx + 2}", x, y, w, h, crop_tb=9000)
        base.shape("Frame border", "rect", x, y, w, h, None, "D1D5DB", 0.55)
    xt_x = x0 + 7 * (w + gap)
    base.shape("x_t border", "rect", xt_x, y, w, h, None, base.COLORS["orange"], 1.8)
    base.shape("x_t badge", "rect", xt_x, y, 0.38, 0.18, "000000", no_line=True)
    base.textbox("x_t", xt_x + 0.04, y + 0.03, 0.30, 0.10, "x_t", 7, "FFFFFF", True, "ctr")
    base.textbox("Prefix note", 9.65, 1.04, 3.0, 0.30, "8 sampled BBP12 frames; the last frame is the current timestamp.", 7.0, base.COLORS["muted"], False, "ctr")


def build_slide_xml() -> bytes:
    base.parts.clear()
    base.shape_id = 1
    base.shape("Background", "rect", 0, 0, base.SLIDE_W, base.SLIDE_H, "FFFFFF", no_line=True)
    base.textbox("Title", 1.55, 0.10, 10.5, 0.28, "Detailed pipeline: workflow-conditioned RSD prediction", 14.0, base.COLORS["ink"], True, "ctr")
    base.textbox("Subtitle", 1.25, 0.43, 11.0, 0.20, "Every node shows the object being passed forward: frames, features, phase patterns, workflow token, temporal model, and evaluation.", 7.7, base.COLORS["muted"], False, "ctr")

    add_prefix_strip()

    # Visual/model row.
    base.panel_label(0.42, 1.78, "A. Visual prediction path")
    y, h = 2.08, 1.05
    mini_clip(0.42, y, 1.28, h)
    base.arrow(1.74, y + 0.50, 2.05, y + 0.50)
    mini_vit(2.10, y, 1.18, h)
    base.arrow(3.32, y + 0.50, 3.62, y + 0.50)
    mini_tensor(3.68, y, 1.22, h)
    base.arrow(4.94, y + 0.50, 5.24, y + 0.50, base.COLORS["teal"])
    mini_token(5.30, y, 1.18, h)
    base.arrow(6.52, y + 0.50, 6.82, y + 0.50)
    mini_hta(6.88, y, 1.38, h)
    base.arrow(8.30, y + 0.50, 8.60, y + 0.50)
    mini_heads(8.66, y, 1.15, h)
    base.arrow(9.85, y + 0.50, 10.16, y + 0.50, base.COLORS["blue"])
    base.shape("RSD output", "roundRect", 10.22, y + 0.30, 1.15, 0.40, "EEF2FF", base.COLORS["blue"], 0.8, "RSD minutes", 6.4, base.COLORS["ink"], True)

    # Workflow row.
    base.panel_label(0.42, 3.50, "B. Workflow-token construction")
    y2, h2 = 3.78, 1.10
    mini_sequence(0.42, y2, 1.28, h2, "full phase sequence", base.COLORS["purple_light"], base.COLORS["purple"])
    base.textbox("oracle note", 0.52, y2 + 0.13, 1.08, 0.10, "oracle path", 4.8, base.COLORS["purple"], True, "ctr")
    base.arrow(1.74, y2 + 0.54, 2.05, y2 + 0.54, base.COLORS["purple"])
    mini_bigrams(2.10, y2, 1.12, h2)
    base.arrow(3.26, y2 + 0.54, 3.56, y2 + 0.54)
    mini_tfidf_pca(3.62, y2, 1.32, h2)
    base.arrow(4.98, y2 + 0.54, 5.28, y2 + 0.54)
    mini_centroids(5.34, y2, 1.24, h2)
    base.arrow(6.62, y2 + 0.54, 6.92, y2 + 0.54, base.COLORS["teal"])
    mini_posterior(6.98, y2, 1.20, h2)
    base.arrow(8.22, y2 + 0.54, 8.52, y2 + 0.54, base.COLORS["teal"])
    mini_token(8.58, y2, 1.30, h2, "soft token")
    base.arrow(9.25, y2, 5.90, 3.12, base.COLORS["teal"])

    # Causal inset.
    base.shape("Causal inset", "roundRect", 10.18, 3.78, 2.78, 1.10, "ECFDF5", base.COLORS["teal"], 0.8)
    base.textbox("Causal inset title", 10.34, 4.64, 2.45, 0.13, "causal-at-inference path", 6.4, base.COLORS["teal"], True, "ctr")
    base.shape("pixels icon", "rect", 10.38, 4.18, 0.38, 0.24, "DBEAFE", base.COLORS["blue"], 0.35, "pixels", 3.8, base.COLORS["ink"], True)
    base.arrow(10.80, 4.30, 11.08, 4.30, base.COLORS["teal"])
    base.shape("phase icon", "rect", 11.12, 4.18, 0.48, 0.24, "F8FAFC", base.COLORS["gray"], 0.35, "phase", 3.8, base.COLORS["ink"], True)
    base.arrow(11.64, 4.30, 11.92, 4.30, base.COLORS["teal"])
    base.shape("q icon", "rect", 11.96, 4.18, 0.46, 0.24, "CCFBF1", base.COLORS["teal"], 0.35, "q", 4.2, base.COLORS["ink"], True)
    base.textbox("No labels", 10.35, 3.95, 2.40, 0.16, "no GT phases or full-case labels", 5.3, base.COLORS["muted"], False, "ctr")

    # Evaluation row.
    base.panel_label(0.42, 5.30, "C. Evaluation and controls")
    mini_eval(0.42, 5.58, 1.45, 1.00)
    base.arrow(1.92, 6.08, 2.26, 6.08)
    base.shape("Protocol", "roundRect", 2.32, 5.58, 1.55, 1.00, base.COLORS["blue_light"], base.COLORS["blue"], 0.8)
    base.textbox("Protocol title", 2.44, 6.34, 1.30, 0.12, "protocols", 6.2, base.COLORS["blue"], True, "ctr")
    base.line("strict timeline", 2.58, 5.95, 3.56, 5.95, base.COLORS["blue"], 0.55, arrow=True)
    base.shape("strict target", "ellipse", 3.43, 5.90, 0.10, 0.10, base.COLORS["blue"], base.COLORS["blue"], 0.1)
    base.line("centered timeline", 2.58, 5.75, 3.56, 5.75, base.COLORS["orange"], 0.55, arrow=True)
    base.shape("center target", "ellipse", 3.05, 5.70, 0.10, 0.10, base.COLORS["orange"], base.COLORS["orange"], 0.1)
    base.textbox("Protocol legend", 2.46, 6.10, 1.26, 0.10, "strict vs centered", 4.7, base.COLORS["muted"], False, "ctr")
    base.arrow(3.92, 6.08, 4.25, 6.08)
    base.shape("Result pattern", "roundRect", 4.31, 5.58, 2.18, 1.00, "FFFFFF", base.COLORS["edge"], 0.8)
    base.textbox("Result title", 4.48, 6.34, 1.85, 0.12, "result pattern", 6.2, base.COLORS["ink"], True, "ctr")
    for i, (lab, val, col) in enumerate([("MB140", 0.52, base.COLORS["teal"]), ("cross", 0.35, base.COLORS["teal"]), ("Chole", 0.10, base.COLORS["gray"]), ("shuffle", 0.02, base.COLORS["purple"])]):
        base.shape("result bar", "rect", 4.55 + i * 0.42, 5.78, 0.18, val, col, col, 0.1)
        base.textbox("bar label", 4.47 + i * 0.42, 5.69, 0.36, 0.08, lab, 3.9, base.COLORS["muted"], False, "ctr")
    base.arrow(6.54, 6.08, 6.88, 6.08)
    base.shape("Claim", "roundRect", 6.94, 5.58, 3.15, 1.00, "F8FAFC", base.COLORS["edge"], 0.8)
    base.textbox("Claim text", 7.12, 5.88, 2.80, 0.36, "workflow conditioning helps when workflow variation exists and the token is meaningful", 6.8, base.COLORS["ink"], True, "ctr")

    base.line("Footer rule", 0.36, 6.80, 13.22, 6.80, "E5E7EB", 0.6)
    base.textbox("Footer", 1.05, 6.88, 11.50, 0.10, "All non-image elements are editable PowerPoint shapes; real surgical frames remain embedded image thumbnails.", 6.2, base.COLORS["muted"], False, "ctr")

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

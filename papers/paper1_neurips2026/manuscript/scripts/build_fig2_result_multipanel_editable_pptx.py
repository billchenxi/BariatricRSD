"""Build an editable PPTX version of Fig. 2 result multipanel.

Every visible element is a native PowerPoint object: panel titles, axes,
gridlines, points, error bars, legend markers, and callouts. No PNG/PDF is
embedded in the slide.

Output:
    paper/figures/fig2_result_multipanel_editable.pptx
    paper/Formatting_Instructions_For_NeurIPS_2026/figures/fig2_result_multipanel_editable.pptx
"""
from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import build_vit_frame_encoder_subcomponent_pptx as base


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/fig2_result_multipanel_editable.pptx"
SUB_FIG = ROOT / "Formatting_Instructions_For_NeurIPS_2026/figures"
FINAL_FIG = ROOT / "final_draft/figures"

SLIDE_W = 10.0
SLIDE_H = 6.5

COLORS = {
    **base.COLORS,
    "axis": "374151",
    "grid": "E5E7EB",
    "panel_edge": "CBD5E1",
    "panel_bg": "FFFFFF",
    "none": "6B7280",
    "oracle": "2563EB",
    "decoupled": "0F766E",
    "prefix": "D97706",
    "shuffle": "7C3AED",
    "callout_green_bg": "ECFDF5",
    "callout_green_edge": "99F6E4",
    "callout_gray_bg": "F8FAFC",
    "callout_gray_edge": "CBD5E1",
}


def set_slide_size() -> None:
    base.SLIDE_W = SLIDE_W
    base.SLIDE_H = SLIDE_H


def y_at(value: float, ymin: float, ymax: float, plot_y: float, plot_h: float) -> float:
    return plot_y + plot_h * (ymax - value) / (ymax - ymin)


def x_positions(n: int, plot_x: float, plot_w: float) -> list[float]:
    if n == 1:
        return [plot_x + plot_w / 2]
    left = plot_x + plot_w * 0.18
    right = plot_x + plot_w * 0.82
    step = (right - left) / (n - 1)
    return [left + i * step for i in range(n)]


def add_panel_frame(x: float, y: float, w: float, h: float, title: str) -> None:
    base.shape("Panel frame", "roundRect", x, y, w, h, COLORS["panel_bg"], COLORS["panel_edge"], 0.65)
    base.textbox("Panel title", x + 0.12, y + 0.10, w - 0.24, 0.26, title, 10.8, COLORS["ink"], True, "l")


def add_axes(
    x: float,
    y: float,
    w: float,
    h: float,
    ymin: float,
    ymax: float,
    ticks: list[float],
    *,
    ylabel: str = "MAE (min)",
) -> tuple[float, float, float, float]:
    plot_x = x + 0.58
    plot_y = y + 0.62
    plot_w = w - 0.78
    plot_h = h - 1.15

    base.textbox("Y label", plot_x, y + 0.37, 1.36, 0.14, ylabel, 6.6, COLORS["muted"], False, "l")
    for tick in ticks:
        yy = y_at(tick, ymin, ymax, plot_y, plot_h)
        base.line("Y gridline", plot_x, yy, plot_x + plot_w, yy, COLORS["grid"], 0.45)
        base.textbox("Y tick", x + 0.12, yy - 0.06, 0.36, 0.12, f"{tick:g}", 6.2, COLORS["muted"], False, "r")

    base.line("Y axis", plot_x, plot_y, plot_x, plot_y + plot_h, COLORS["axis"], 0.6)
    base.line("X axis", plot_x, plot_y + plot_h, plot_x + plot_w, plot_y + plot_h, COLORS["axis"], 0.6)
    return plot_x, plot_y, plot_w, plot_h


def add_point(px: float, py: float, color: str, size: float = 0.12) -> None:
    base.shape("Data point", "ellipse", px - size / 2, py - size / 2, size, size, color, "111827", 0.35)


def add_error_bar(px: float, mean: float, sd: float, ymin: float, ymax: float, plot_y: float, plot_h: float, color: str) -> None:
    y_low = y_at(mean - sd, ymin, ymax, plot_y, plot_h)
    y_high = y_at(mean + sd, ymin, ymax, plot_y, plot_h)
    base.line("Error bar", px, y_high, px, y_low, color, 0.8)
    base.line("Error cap", px - 0.075, y_high, px + 0.075, y_high, color, 0.8)
    base.line("Error cap", px - 0.075, y_low, px + 0.075, y_low, color, 0.8)


def add_value_label(px: float, y_ref: float, text: str, plot_y: float) -> None:
    yy = max(plot_y - 0.08, y_ref - 0.32)
    base.textbox("Value label", px - 0.30, yy, 0.60, 0.24, text, 6.3, COLORS["ink"], False, "ctr")


def add_callout(
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    color: str = "0F5132",
    bg: str = COLORS["callout_green_bg"],
    edge: str = COLORS["callout_green_edge"],
) -> None:
    base.shape("Result callout", "roundRect", x, y, w, h, bg, edge, 0.55, text, 6.8, color, True)


def add_point_panel(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    labels: list[str],
    means: list[float],
    sds: list[float],
    colors: list[str],
    ymin: float,
    ymax: float,
    ticks: list[float],
    callout: str,
) -> None:
    add_panel_frame(x, y, w, h, title)
    plot_x, plot_y, plot_w, plot_h = add_axes(x, y, w, h, ymin, ymax, ticks)
    xs = x_positions(len(labels), plot_x, plot_w)

    for i in range(len(xs) - 1):
        y1 = y_at(means[i], ymin, ymax, plot_y, plot_h)
        y2 = y_at(means[i + 1], ymin, ymax, plot_y, plot_h)
        base.line("Mean connector", xs[i], y1, xs[i + 1], y2, "CBD5E1", 0.75)

    for px, label, mean, sd, color in zip(xs, labels, means, sds, colors):
        py = y_at(mean, ymin, ymax, plot_y, plot_h)
        add_error_bar(px, mean, sd, ymin, ymax, plot_y, plot_h, color)
        add_point(px, py, color)
        y_high = y_at(mean + sd, ymin, ymax, plot_y, plot_h)
        add_value_label(px, y_high, f"{mean:.2f}\n+/- {sd:.2f}", plot_y)
        base.textbox("X label", px - 0.42, plot_y + plot_h + 0.10, 0.84, 0.18, label, 6.6, COLORS["ink"], False, "ctr")

    add_callout(x + w - 1.80, y + 0.42, 1.62, 0.24, callout)


def add_legend_item(x: float, y: float, color: str, label: str) -> None:
    add_point(x, y + 0.055, color, 0.10)
    base.textbox("Legend label", x + 0.08, y, 0.62, 0.12, label, 5.9, COLORS["ink"], False, "l")


def add_cholec_panel(x: float, y: float, w: float, h: float) -> None:
    add_panel_frame(x, y, w, h, "C. Cholec80 contrast")
    ymin, ymax = 4.1, 5.2
    ticks = [4.2, 4.6, 5.0]
    plot_x, plot_y, plot_w, plot_h = add_axes(x, y, w, h, ymin, ymax, ticks)

    legend_y = y + 0.38
    add_legend_item(x + 1.60, legend_y, COLORS["oracle"], "oracle")
    add_legend_item(x + 2.28, legend_y, COLORS["none"], "no token")
    add_legend_item(x + 3.05, legend_y, COLORS["prefix"], "prefix")

    group_xs = [plot_x + plot_w * 0.30, plot_x + plot_w * 0.72]
    offsets = [-0.23, 0.0, 0.23]
    labels = ["oracle", "no token", "prefix"]
    colors = [COLORS["oracle"], COLORS["none"], COLORS["prefix"]]
    centered = [4.49, 4.61, 5.03]
    centered_sd = [0.14, 0.19, 0.07]
    strict = [4.33, 4.34, 4.26]

    strict_label_y_offsets = [-0.30, -0.13, 0.07]
    for idx, (off, mean_c, sd_c, mean_s, color) in enumerate(zip(offsets, centered, centered_sd, strict, colors)):
        px_c = group_xs[0] + off
        px_s = group_xs[1] + off
        py_c = y_at(mean_c, ymin, ymax, plot_y, plot_h)
        py_s = y_at(mean_s, ymin, ymax, plot_y, plot_h)
        add_error_bar(px_c, mean_c, sd_c, ymin, ymax, plot_y, plot_h, color)
        add_point(px_c, py_c, color, 0.11)
        add_point(px_s, py_s, color, 0.11)
        base.line("Condition connector", px_c, py_c, px_s, py_s, color, 0.55)

        y_high = y_at(mean_c + sd_c, ymin, ymax, plot_y, plot_h)
        label_c_y = max(plot_y - 0.05, y_high - 0.25)
        base.textbox(
            "Cholec centered value",
            px_c - 0.26,
            label_c_y,
            0.52,
            0.22,
            f"{mean_c:.2f}\n+/- {sd_c:.2f}",
            5.5,
            COLORS["ink"],
            False,
            "ctr",
        )
        base.textbox(
            "Cholec strict value",
            px_s - 0.18,
            py_s + strict_label_y_offsets[idx],
            0.36,
            0.11,
            f"{mean_s:.2f}",
            5.5,
            COLORS["ink"],
            False,
            "ctr",
        )

    base.textbox("Group label", group_xs[0] - 0.58, plot_y + plot_h + 0.08, 1.16, 0.28, "centered-window\n3 seeds", 6.5, COLORS["ink"], False, "ctr")
    base.textbox("Group label", group_xs[1] - 0.58, plot_y + plot_h + 0.08, 1.16, 0.28, "strict prefix-only\n1 seed", 6.5, COLORS["ink"], False, "ctr")
    add_callout(
        x + w - 1.62,
        y + h - 0.42,
        1.44,
        0.24,
        "strict range: 0.08 min",
        color=COLORS["axis"],
        bg=COLORS["callout_gray_bg"],
        edge=COLORS["callout_gray_edge"],
    )


def build_slide_xml() -> bytes:
    set_slide_size()
    base.parts.clear()
    base.shape_id = 1

    base.shape("Background", "rect", 0, 0, SLIDE_W, SLIDE_H, "FFFFFF", no_line=True)

    panel_w = 4.44
    panel_h = 2.74
    left_x = 0.35
    right_x = 5.21
    top_y = 0.20
    bottom_y = 3.40

    add_point_panel(
        left_x,
        top_y,
        panel_w,
        panel_h,
        "A. MB140 within-center (strict)",
        ["no token", "oracle", "decoupled"],
        [13.03, 12.26, 12.18],
        [0.18, 0.09, 0.11],
        [COLORS["none"], COLORS["oracle"], COLORS["decoupled"]],
        11.95,
        13.55,
        [12.0, 12.5, 13.0, 13.5],
        "decoupled gain: -0.85 min",
    )

    add_point_panel(
        right_x,
        top_y,
        panel_w,
        panel_h,
        "B. MB140 Bern -> Strasbourg (strict)",
        ["no token", "oracle", "decoupled"],
        [17.80, 17.71, 17.33],
        [0.55, 0.23, 0.15],
        [COLORS["none"], COLORS["oracle"], COLORS["decoupled"]],
        16.95,
        18.85,
        [17.0, 17.5, 18.0, 18.5],
        "decoupled gain: -0.47 min",
    )

    add_cholec_panel(left_x, bottom_y, panel_w, panel_h)

    add_point_panel(
        right_x,
        bottom_y,
        panel_w,
        panel_h,
        "D. Shuffled-token control (MB140 strict)",
        ["no token", "shuffled", "real token"],
        [13.03, 13.14, 12.18],
        [0.18, 0.15, 0.11],
        [COLORS["none"], COLORS["shuffle"], COLORS["decoupled"]],
        11.95,
        13.55,
        [12.0, 12.5, 13.0, 13.5],
        "shuffle fails to\nreproduce gain",
    )

    base.textbox(
        "Figure note",
        0.55,
        6.18,
        8.90,
        0.16,
        "Oracle and decoupled-oracle rows use retrospective cluster IDs; strict protocol removes future visual frames. Panel C strict Cholec80 uses one seed.",
        6.1,
        COLORS["muted"],
        False,
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
    if not base.TEMPLATE.exists():
        raise FileNotFoundError(f"Missing PPTX template: {base.TEMPLATE}")

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

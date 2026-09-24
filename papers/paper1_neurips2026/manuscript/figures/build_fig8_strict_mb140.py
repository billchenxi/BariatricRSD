"""
Figure 8 (per FIGURE_ROADMAP.md): strict-protocol MB140 main result.

Inputs:
  outputs/run033_summary.json                       (training-time bars)
  outputs/run035_strict_pixel_only/summary.json     (pixel-only causal bar)

Output:
  paper/figures/fig8_strict_mb140_main_result.{png,pdf}

If either input is missing this script emits a placeholder figure with an
explicit "pending Run NNN" label so the manuscript build doesn't break.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
RUN033 = ROOT / "outputs" / "run033_summary.json"
RUN033_MIRROR = ROOT / "lambda_mirror" / "outputs" / "run033_summary.json"
RUN035 = ROOT / "outputs" / "run035_strict_pixel_only" / "summary.json"
RUN035_MIRROR = ROOT / "lambda_mirror" / "outputs" / "run035_strict_pixel_only" / "summary.json"


def _load(*candidates):
    for p in candidates:
        if p and p.exists():
            with open(p) as f:
                return json.load(f), p
    return None, None


def main():
    plt.rcParams.update({"figure.dpi": 140, "savefig.bbox": "tight"})

    r033, r033p = _load(RUN033, RUN033_MIRROR)
    r035, r035p = _load(RUN035, RUN035_MIRROR)

    rows = []  # (label, mean, std, color)
    if r033:
        for cond, color in [("no_token", "#d84a4a"),
                            ("oracle", "#3b7dd8"),
                            ("decoupled", "#2ea44f")]:
            if cond in r033:
                rows.append((
                    {"no_token": "Strict no-token",
                     "oracle": "Strict oracle",
                     "decoupled": "Strict\ndecoupled-oracle"}[cond],
                    r033[cond].get("best_val_mae_min_mean"),
                    r033[cond].get("best_val_mae_min_std", 0.0),
                    color,
                ))
    if r035:
        # Pull MB140 fold-0 strict pixel-only causal: prefer "run033_decoupled"
        # if available, fall back to "run033_oracle".
        for k in ("run033_decoupled", "run033_oracle"):
            if k in r035:
                rows.append((
                    "Strict\npixel-only causal",
                    r035[k].get("mae_minutes_mean_mean"),
                    r035[k].get("mae_minutes_mean_std", 0.0),
                    "#a64a9c",
                ))
                break

    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    if not rows:
        ax.text(0.5, 0.5,
                "Pending Run 033 (training)\nand Run 035 (strict pixel-only causal eval).\n"
                "Re-run this script when:\n"
                f"  {RUN033}\n"
                f"  {RUN035}\n"
                "exist or are mirrored locally.",
                ha="center", va="center", fontsize=10, color="#777",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#fffbe5", edgecolor="#aaa"))
        ax.axis("off")
    else:
        labels = [r[0] for r in rows]
        means  = [r[1] for r in rows]
        stds   = [r[2] for r in rows]
        colors = [r[3] for r in rows]
        bars = ax.bar(range(len(labels)), means, yerr=stds, capsize=6,
                      color=colors, edgecolor="black", linewidth=0.5)
        for b, m, s in zip(bars, means, stds):
            if m is None: continue
            ax.text(b.get_x() + b.get_width() / 2, m + (s or 0) + 0.05,
                    f"{m:.2f}" + (f" ± {s:.2f}" if s else ""),
                    ha="center", va="bottom", fontsize=9)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("Validation MAE (min, ↓)")
        ax.set_title("Figure 8.  Strict-protocol MB140 fold 0 main result")
        ax.grid(axis="y", alpha=0.3)
        # Horizontal reference: legacy centered-window no-token
        ax.axhline(12.88, color="#888", linestyle=":", linewidth=0.7,
                   label="centered-window no-token (legacy 12.88)")
        ax.legend(loc="upper right", fontsize=8)

    out_png = HERE / "fig8_strict_mb140_main_result.png"
    out_pdf = HERE / "fig8_strict_mb140_main_result.pdf"
    fig.savefig(out_png); fig.savefig(out_pdf)
    print(f"wrote {out_png}, {out_pdf}")


if __name__ == "__main__":
    main()

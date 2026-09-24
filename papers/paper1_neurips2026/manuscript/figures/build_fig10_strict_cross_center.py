"""
Figure 10 (per FIGURE_ROADMAP.md): strict-protocol cross-center comparison.

Two grouped blocks (within-center MB140, cross-center Bern→Strasbourg) ×
three bars each (strict no-token, strict oracle, strict pixel-only causal).

Required inputs:
  outputs/run033_summary.json                       (within-center training bars)
  outputs/run034_summary.json                       (cross-center training bars)
  outputs/run035_strict_pixel_only/summary.json     (strict pixel-only causal in both regimes)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
ROOT = HERE.parent.parent

PATHS = {
    "run033": [ROOT / "outputs/run033_summary.json", ROOT / "lambda_mirror/outputs/run033_summary.json"],
    "run034": [ROOT / "outputs/run034_summary.json", ROOT / "lambda_mirror/outputs/run034_summary.json"],
    "run035": [ROOT / "outputs/run035_strict_pixel_only/summary.json",
               ROOT / "lambda_mirror/outputs/run035_strict_pixel_only/summary.json"],
}


def _load(name):
    for p in PATHS[name]:
        if p.exists():
            return json.load(open(p))
    return None


def main():
    plt.rcParams.update({"figure.dpi": 140, "savefig.bbox": "tight"})

    r33 = _load("run033")
    r34 = _load("run034")
    r35 = _load("run035")

    fig, ax = plt.subplots(figsize=(7.0, 4.0))

    if not (r33 and r34):
        ax.text(0.5, 0.5,
                "Pending Run 033 (within-center) + Run 034 (cross-center) + Run 035 (causal).",
                ha="center", va="center", fontsize=10, color="#777",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#fffbe5", edgecolor="#aaa"))
        ax.axis("off")
    else:
        conds = ["no_token", "oracle", "decoupled"]
        labels = ["Strict no-token", "Strict oracle", "Strict pixel-only causal"]
        colors = ["#d84a4a", "#3b7dd8", "#a64a9c"]

        wc = [(r33.get(c, {}).get("best_val_mae_min_mean"),
               r33.get(c, {}).get("best_val_mae_min_std", 0.0)) for c in conds]
        cc = [(r34.get(c, {}).get("best_val_mae_min_mean"),
               r34.get(c, {}).get("best_val_mae_min_std", 0.0)) for c in conds]

        # Replace decoupled bars with pixel-only causal from r35 if present.
        if r35:
            for k_in, slot in (("run033_decoupled", 2), ("run033_oracle", 2)):
                if k_in in r35 and r35[k_in].get("mae_minutes_mean_mean"):
                    wc[slot] = (r35[k_in]["mae_minutes_mean_mean"],
                                r35[k_in].get("mae_minutes_mean_std", 0.0))
                    break
            for k_in, slot in (("run034_decoupled", 2), ("run034_oracle", 2)):
                if k_in in r35 and r35[k_in].get("mae_minutes_mean_mean"):
                    cc[slot] = (r35[k_in]["mae_minutes_mean_mean"],
                                r35[k_in].get("mae_minutes_mean_std", 0.0))
                    break

        x = np.arange(2)
        width = 0.25
        for i, (lab, color) in enumerate(zip(labels, colors)):
            means = [wc[i][0] or 0, cc[i][0] or 0]
            stds  = [wc[i][1] or 0, cc[i][1] or 0]
            ax.bar(x + (i - 1) * width, means, width=width,
                   yerr=stds, capsize=4, label=lab, color=color,
                   edgecolor="black", linewidth=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels(["Within-center MB140", "Cross-center Bern→Strasbourg"])
        ax.set_ylabel("Validation MAE (min, ↓)")
        ax.set_title("Figure 10.  Strict-protocol within-center vs cross-center")
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    out_png = HERE / "fig10_strict_cross_center.png"
    out_pdf = HERE / "fig10_strict_cross_center.pdf"
    fig.savefig(out_png); fig.savefig(out_pdf)
    print(f"wrote {out_png}, {out_pdf}")


if __name__ == "__main__":
    main()

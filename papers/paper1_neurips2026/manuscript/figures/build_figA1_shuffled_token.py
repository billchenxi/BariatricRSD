"""
Appendix Figure A1 (per FIGURE_ROADMAP.md): shuffled-token semantic control.

Three bars on MB140 fold 0 under strict prefix-only protocol:
  - strict no-token       (Run 033 strict no_token)
  - strict shuffled-token (Run 037)  — cluster IDs permuted across videos
  - strict oracle         (Run 033 strict oracle)

Interpretation:
  shuffled ≈ no-token  → workflow token carries semantic information ✅
  shuffled ≈ oracle    → gain is from parameter capacity, not cluster meaning ✗
  in between           → cluster meaning is partial signal

Inputs:
  outputs/run033_summary.json
  outputs/run037_summary.json

Output:
  paper/figures/figA1_shuffled_token_control.{png,pdf}

Falls back to a labeled placeholder if either input is missing.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
ROOT = HERE.parent.parent

PATHS = {
    "run033": [ROOT / "outputs/run033_summary.json",
               ROOT / "lambda_mirror/outputs/run033_summary.json"],
    "run037": [ROOT / "outputs/run037_summary.json",
               ROOT / "lambda_mirror/outputs/run037_summary.json"],
}


def _load(name):
    for p in PATHS[name]:
        if p.exists():
            return json.load(open(p))
    return None


def main():
    plt.rcParams.update({"figure.dpi": 140, "savefig.bbox": "tight"})

    r33 = _load("run033")
    r37 = _load("run037")

    fig, ax = plt.subplots(figsize=(5.0, 3.4))

    if not r37:
        ax.text(0.5, 0.5,
                "Pending Run 037 (shuffled-token control)\n"
                f"  {PATHS['run037'][0]}\n"
                "Optionally: Run 033 for the no-token / oracle comparison bars.\n"
                "Re-run after Run 037 lands.",
                ha="center", va="center", fontsize=9, color="#777",
                transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#fffbe5", edgecolor="#aaa"))
        ax.axis("off")
    else:
        rows = []
        if r33 and "no_token" in r33 and r33["no_token"].get("best_val_mae_min_mean") is not None:
            rows.append(("Strict\nno-token",
                         r33["no_token"]["best_val_mae_min_mean"],
                         r33["no_token"].get("best_val_mae_min_std", 0.0),
                         "#d84a4a"))
        if r37.get("best_val_mae_min_mean") is not None:
            rows.append(("Strict\nshuffled-token",
                         r37["best_val_mae_min_mean"],
                         r37.get("best_val_mae_min_std", 0.0),
                         "#888888"))
        if r33 and "oracle" in r33 and r33["oracle"].get("best_val_mae_min_mean") is not None:
            rows.append(("Strict\noracle",
                         r33["oracle"]["best_val_mae_min_mean"],
                         r33["oracle"].get("best_val_mae_min_std", 0.0),
                         "#3b7dd8"))

        if not rows:
            ax.text(0.5, 0.5, "Run 037 summary present but empty.",
                    ha="center", va="center", fontsize=10, color="#777",
                    transform=ax.transAxes)
            ax.axis("off")
        else:
            labels = [r[0] for r in rows]
            means  = [r[1] for r in rows]
            stds   = [r[2] for r in rows]
            colors = [r[3] for r in rows]
            bars = ax.bar(range(len(labels)), means, yerr=stds, capsize=6,
                          color=colors, edgecolor="black", linewidth=0.5)
            for b, m, s in zip(bars, means, stds):
                ax.text(b.get_x() + b.get_width() / 2, m + (s or 0) + 0.05,
                        f"{m:.2f}" + (f" ± {s:.2f}" if s else ""),
                        ha="center", va="bottom", fontsize=9)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, fontsize=9)
            ax.set_ylabel("Validation MAE (min, ↓)")
            ax.set_title("Figure A1.  Shuffled-token semantic control (MB140 fold 0, strict)")
            ax.grid(axis="y", alpha=0.3)

    out_png = HERE / "figA1_shuffled_token_control.png"
    out_pdf = HERE / "figA1_shuffled_token_control.pdf"
    fig.savefig(out_png); fig.savefig(out_pdf)
    print(f"wrote {out_png}, {out_pdf}")


if __name__ == "__main__":
    main()

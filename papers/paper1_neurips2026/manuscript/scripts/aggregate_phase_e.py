"""
Aggregate Phase E metrics (Runs 038/039/040 across folds 0-4 × 3 seeds) into
a clean per-fold and 5-fold mean ± std table for Appendix C.1.

Inputs:
  lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json
    - Pre-aggregated run038/039/040 fold 1-4 metrics from earlier sync
  Run 040 fold-4 metrics from new D-cluster runs (added inline below)
  Run 033 fold-0 metrics (baseline reference: 13.03 / 12.26 / 12.18)

Output:
  paper/phase_e_summary.md   — markdown table for review
  paper/phase_e_summary.json — machine-readable per-fold and overall summaries
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AGG_JSON = ROOT / "lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json"
OUT_MD = ROOT / "paper/phase_e_summary.md"
OUT_JSON = ROOT / "paper/phase_e_summary.json"

# Fold-0 reference numbers come from Run 033 (already in §6.1, 3 seeds).
# Seed values are the best-val-MAE per training log (the values saved as
# best_model.pth checkpoints). Verified directly from
# lambda_mirror/logs/192.222.56.188/run033_{cond}_seed{seed}.log "best=" lines.
FOLD0_REF = {
    "no_token":  {"seeds": [13.17, 13.10, 12.83], "source": "Run 033"},  # mean 13.03 ± 0.18
    "oracle":    {"seeds": [12.18, 12.23, 12.36], "source": "Run 033"},  # mean 12.26 ± 0.09
    "decoupled": {"seeds": [12.32, 12.19, 12.04], "source": "Run 033"},  # mean 12.18 ± 0.14
}

# Newly completed Run 040 fold-4 metrics (Cluster D, 2026-04-29).
NEW_FOLD4_DECOUPLED = {
    "run040_strict_decoupled_fold4_seed42":  {"epoch": 14, "mae_minutes": 8.4787, "pearson_r": 0.9068},
    "run040_strict_decoupled_fold4_seed123": {"epoch": 14, "mae_minutes": 8.7428, "pearson_r": 0.9049},
    "run040_strict_decoupled_fold4_seed777": {"epoch": 14, "mae_minutes": 8.8243, "pearson_r": 0.9010},
}


def stats(xs):
    if not xs:
        return None, None
    if len(xs) == 1:
        return xs[0], 0.0
    return statistics.mean(xs), statistics.stdev(xs)


def main():
    if not AGG_JSON.exists():
        raise SystemExit(f"missing aggregate JSON: {AGG_JSON}")
    with open(AGG_JSON) as f:
        agg = json.load(f)

    # Splice in the new fold-4 decoupled results.
    agg["run040_strict_decoupled"].update(NEW_FOLD4_DECOUPLED)

    # Persist updated aggregate.
    with open(AGG_JSON, "w") as f:
        json.dump(agg, f, indent=2)
    print(f"Updated {AGG_JSON} with {len(NEW_FOLD4_DECOUPLED)} new fold-4 runs")

    # Build per-fold tables.
    conditions = {
        "no_token":  ("run038_strict_no_token", "no-token"),
        "oracle":    ("run039_strict_oracle",   "oracle (cluster ID, retrospective)"),
        "decoupled": ("run040_strict_decoupled", "decoupled-oracle (decoupled phase head)"),
    }
    folds = list(range(5))

    per_fold = {}  # cond -> fold -> {seeds:[...], mean, std}
    for cond_key, (run_prefix, _) in conditions.items():
        per_fold[cond_key] = {}
        for fold in folds:
            if fold == 0:
                seeds = FOLD0_REF[cond_key]["seeds"]
            else:
                # Pull all fold-`fold` runs from agg
                runs = agg.get(run_prefix, {})
                seeds = sorted([
                    v["mae_minutes"]
                    for k, v in runs.items()
                    if f"fold{fold}_" in k
                ])
            mean, std = stats(seeds)
            per_fold[cond_key][fold] = {
                "seeds": seeds,
                "mean": round(mean, 3) if mean is not None else None,
                "std":  round(std, 3) if std is not None else None,
            }

    # 5-fold overall mean across all (fold, seed) pairs.
    overall = {}
    for cond_key in conditions:
        all_seeds = []
        for fold in folds:
            all_seeds.extend(per_fold[cond_key][fold]["seeds"] or [])
        mean, std = stats(all_seeds)
        overall[cond_key] = {
            "n_runs": len(all_seeds),
            "mean": round(mean, 3),
            "std": round(std, 3),
        }

    # Δ vs no-token per fold + overall
    deltas = {}
    for fold in folds:
        b = per_fold["no_token"][fold]["mean"]
        deltas[fold] = {
            "oracle_minus_no_token":   round(per_fold["oracle"][fold]["mean"]   - b, 3),
            "decoupled_minus_no_token": round(per_fold["decoupled"][fold]["mean"] - b, 3),
        }
    deltas["overall"] = {
        "oracle_minus_no_token":   round(overall["oracle"]["mean"]   - overall["no_token"]["mean"], 3),
        "decoupled_minus_no_token": round(overall["decoupled"]["mean"] - overall["no_token"]["mean"], 3),
    }

    summary = {"per_fold": per_fold, "overall": overall, "deltas": deltas}
    OUT_JSON.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {OUT_JSON}")

    # Markdown table for human review (Appendix C.1 draft)
    lines = ["# Phase E — Strict-protocol 5-fold × 3-seed extension\n",
             "Validation MAE (minutes), best-checkpoint, all 5 folds × 3 seeds.",
             "Fold 0 reference: Run 033 (already in §6.1 headline). Folds 1-4: Phase E.\n",
             "## Per-fold mean ± std\n",
             "| Fold | no-token | oracle | decoupled-oracle | Δ oracle | Δ decoupled |",
             "|---:|---:|---:|---:|---:|---:|"]
    for fold in folds:
        nt = per_fold["no_token"][fold]
        oc = per_fold["oracle"][fold]
        de = per_fold["decoupled"][fold]
        lines.append(
            f"| {fold} | {nt['mean']:.2f} ± {nt['std']:.2f} | "
            f"{oc['mean']:.2f} ± {oc['std']:.2f} | "
            f"{de['mean']:.2f} ± {de['std']:.2f} | "
            f"{deltas[fold]['oracle_minus_no_token']:+.2f} | "
            f"{deltas[fold]['decoupled_minus_no_token']:+.2f} |"
        )
    nt, oc, de = overall["no_token"], overall["oracle"], overall["decoupled"]
    lines.append(
        f"| **All** | **{nt['mean']:.2f} ± {nt['std']:.2f}** | "
        f"**{oc['mean']:.2f} ± {oc['std']:.2f}** | "
        f"**{de['mean']:.2f} ± {de['std']:.2f}** | "
        f"**{deltas['overall']['oracle_minus_no_token']:+.2f}** | "
        f"**{deltas['overall']['decoupled_minus_no_token']:+.2f}** |"
    )
    lines.append("")
    lines.append(f"Total runs: 5 folds × 3 conditions × 3 seeds = 45 (15 per condition).")
    OUT_MD.write_text("\n".join(lines))
    print(f"Wrote {OUT_MD}")

    print()
    print("\n".join(lines[3:]))  # echo the table to stdout


if __name__ == "__main__":
    main()

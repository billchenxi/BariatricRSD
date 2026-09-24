"""Fold-stability and variance-decomposition analysis for Paper 2A.

Paper 1's central weakness, as all three reviewers and the AC noted, was
that a 0.85-min development-fold effect shrank to a 0.19-min five-fold
mean with two folds reversing sign. That is not a defect specific to
Paper 1: it is what happens when a conditioning effect is smaller than
the between-fold spread of the benchmark. Paper 2A compares several
backbones on the same folds, so the same trap is waiting, only wider.

This module makes the trap measurable before the matrix is run:

1. **Per-fold effect sizes.** Δ mean per fold plus a paired Cohen's d
   across the matched seeds, so a fold's effect is reported alongside
   its own seed noise rather than against the pooled noise.
2. **Paired significance.** Wilcoxon over the matched (fold, seed) runs,
   which is the only n that is not tiny, plus the fold-mean-level test
   for readers who consider folds the unit of analysis.
3. **Variance decomposition.** How much of the total MAE variance is
   attributable to fold, to condition, and to seed. The fold-to-effect
   ratio is the headline number: it says how large the benchmark's own
   fold spread is relative to the effect being claimed.
4. **Fold-count power analysis.** Given the observed spread of per-fold
   effects, how many folds are needed for 80% power on the observed mean
   effect. This is a direct input to the Phase 1 / Phase 2 run budget.

Verified against Paper 1's Appendix C numbers in
`tests/test_fold_stability.py`.

Usage:

    python -m paper2_infra.evaluation.fold_stability \\
        --summary-json papers/paper1_neurips2026/manuscript/phase_e_summary.json \\
        --baseline no_token --treatment decoupled \\
        --report-out src/paper2_infra/evaluation/fold_stability_paper1.json
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("fold_stability")


# ── Input parsing ───────────────────────────────────────────────────────────

def load_phase_e_summary(path: Path) -> Dict[str, Dict[str, List[float]]]:
    """Read a Phase-E-style summary into condition → fold → [seed MAEs].

    Accepts the schema written by `paper/scripts/aggregate_phase_e.py`:

        {"per_fold": {condition: {fold_id: {"seeds": [...], "mean":, "std":}}}}

    Fold ids are kept as strings so that non-integer fold names (e.g.
    "cross_center") survive; ordering uses numeric sort where possible.
    """
    payload = json.loads(Path(path).read_text())
    per_fold = payload.get("per_fold")
    if per_fold is None:
        raise ValueError(f"{path}: missing 'per_fold' key")

    out: Dict[str, Dict[str, List[float]]] = {}
    for condition, folds in per_fold.items():
        out[condition] = {}
        for fold_id, entry in folds.items():
            seeds = entry["seeds"] if isinstance(entry, dict) else entry
            out[condition][str(fold_id)] = [float(s) for s in seeds]
    return out


def _sorted_folds(fold_ids: Sequence[str]) -> List[str]:
    def key(f: str):
        try:
            return (0, int(f), "")
        except ValueError:
            return (1, 0, f)
    return sorted(fold_ids, key=key)


# ── Effect sizes ────────────────────────────────────────────────────────────

def paired_cohens_d(treatment: Sequence[float],
                    baseline: Sequence[float]) -> float:
    """Cohen's d for paired samples: mean(diff) / sd(diff).

    Returns NaN when fewer than two pairs are available or when every
    pair has an identical difference (zero spread), because the
    standardized effect is undefined rather than infinite in that case.
    """
    diffs = np.asarray(treatment, dtype=np.float64) - np.asarray(baseline, dtype=np.float64)
    if diffs.size < 2:
        return float("nan")
    sd = diffs.std(ddof=1)
    if sd == 0:
        return float("nan")
    return float(diffs.mean() / sd)


def per_fold_effects(data: Dict[str, Dict[str, List[float]]],
                     baseline: str, treatment: str) -> List[Dict]:
    """Per-fold Δ (treatment − baseline), seed spread, and paired d.

    Seeds are assumed to be listed in the same order for both conditions
    — that is the pairing. A fold whose two conditions have differing
    seed counts is reported with `paired = False` and its d omitted,
    rather than silently truncated.
    """
    if baseline not in data:
        raise KeyError(f"condition {baseline!r} not in summary "
                       f"(have: {sorted(data)})")
    if treatment not in data:
        raise KeyError(f"condition {treatment!r} not in summary "
                       f"(have: {sorted(data)})")

    folds = _sorted_folds(set(data[baseline]) & set(data[treatment]))
    rows = []
    for fold in folds:
        base = data[baseline][fold]
        treat = data[treatment][fold]
        paired = len(base) == len(treat) and len(base) > 0
        row = {
            "fold": fold,
            "n_seeds_baseline": len(base),
            "n_seeds_treatment": len(treat),
            "paired": paired,
            "baseline_mean": float(np.mean(base)),
            "baseline_std": float(np.std(base, ddof=1)) if len(base) > 1 else 0.0,
            "treatment_mean": float(np.mean(treat)),
            "treatment_std": float(np.std(treat, ddof=1)) if len(treat) > 1 else 0.0,
        }
        row["delta"] = row["treatment_mean"] - row["baseline_mean"]
        row["improves"] = row["delta"] < 0  # lower MAE is better
        row["paired_cohens_d"] = paired_cohens_d(treat, base) if paired else float("nan")
        # Does the fold's effect exceed its own seed noise? A fold whose Δ
        # is inside the seed spread is not evidence of anything.
        pooled_seed_sd = math.hypot(row["baseline_std"], row["treatment_std"])
        row["delta_exceeds_seed_noise"] = (
            abs(row["delta"]) > pooled_seed_sd if pooled_seed_sd > 0 else False
        )
        rows.append(row)
    return rows


# ── Significance over matched runs ──────────────────────────────────────────

def paired_significance(data: Dict[str, Dict[str, List[float]]],
                        baseline: str, treatment: str) -> Dict[str, Dict]:
    """Paired Wilcoxon at two units of analysis: run and fold.

    'run' pairs every (fold, seed) cell — the largest available n, at the
    cost of treating seeds within a fold as independent, which they are
    not entirely. 'fold' pairs the five fold means — the conservative
    unit, but n=5 has almost no power. Reporting both is the honest
    move; neither alone is sufficient.
    """
    from scipy.stats import wilcoxon

    folds = _sorted_folds(set(data[baseline]) & set(data[treatment]))

    run_base, run_treat = [], []
    fold_base, fold_treat = [], []
    for fold in folds:
        base, treat = data[baseline][fold], data[treatment][fold]
        if len(base) == len(treat):
            run_base.extend(base)
            run_treat.extend(treat)
        fold_base.append(float(np.mean(base)))
        fold_treat.append(float(np.mean(treat)))

    def _test(a: List[float], b: List[float], unit: str) -> Dict:
        arr_a = np.asarray(a, dtype=np.float64)
        arr_b = np.asarray(b, dtype=np.float64)
        diffs = arr_a - arr_b
        result = {
            "unit": unit,
            "n_paired": int(diffs.size),
            "mean_diff_treatment_minus_baseline": float(diffs.mean()) if diffs.size else float("nan"),
            "median_diff_treatment_minus_baseline": float(np.median(diffs)) if diffs.size else float("nan"),
            "n_treatment_better": int((diffs < 0).sum()),
            "n_baseline_better": int((diffs > 0).sum()),
        }
        # Wilcoxon needs a handful of non-zero pairs to mean anything, and
        # scipy raises below n=... rather than returning a useless p.
        if diffs.size < 5 or np.all(diffs == 0):
            result["p_value"] = float("nan")
            result["test_note"] = (
                f"n={diffs.size} is too small for a meaningful signed-rank "
                f"test; reported for completeness only"
            )
        else:
            res = wilcoxon(arr_a, arr_b, alternative="two-sided",
                           zero_method="wilcox")
            result["statistic"] = float(res.statistic)
            result["p_value"] = float(res.pvalue)
        return result

    return {
        "by_run": _test(run_treat, run_base, "run (fold x seed)"),
        "by_fold": _test(fold_treat, fold_base, "fold mean"),
    }


# ── Variance decomposition ──────────────────────────────────────────────────

def variance_decomposition(data: Dict[str, Dict[str, List[float]]],
                           conditions: Optional[Sequence[str]] = None
                           ) -> Dict[str, float]:
    """Attribute MAE variance to fold, condition, and seed.

    Two-way layout y[condition, fold, seed] with the seed dimension as
    replication. Sums of squares are computed on the cell means for the
    fold and condition main effects and on the within-cell deviations for
    the seed (residual) term, so the three shares partition the total.

    The number the paper should quote is `fold_sd`: the standard
    deviation of the fold means. When a claimed conditioning effect is a
    fraction of that, the benchmark's fold composition dominates the
    measurement, and a development-fold headline will not survive
    cross-validation.
    """
    conditions = list(conditions) if conditions else _sorted_folds(list(data))
    conditions = [c for c in conditions if c in data]
    if not conditions:
        raise ValueError("no conditions to decompose")

    folds = _sorted_folds(set.intersection(*(set(data[c]) for c in conditions)))
    if not folds:
        raise ValueError("conditions share no folds")

    # y[i, j, :] = seed replicates for condition i, fold j
    cells: List[List[np.ndarray]] = [
        [np.asarray(data[c][f], dtype=np.float64) for f in folds]
        for c in conditions
    ]
    all_values = np.concatenate([v for row in cells for v in row])
    grand_mean = float(all_values.mean())
    n_total = all_values.size

    cell_means = np.array([[v.mean() for v in row] for row in cells])
    cell_counts = np.array([[v.size for v in row] for row in cells], dtype=np.float64)

    # Main effects, weighted by the number of runs behind each cell so an
    # unbalanced matrix (a fold with a missing seed) does not skew shares.
    fold_means = (cell_means * cell_counts).sum(axis=0) / cell_counts.sum(axis=0)
    cond_means = (cell_means * cell_counts).sum(axis=1) / cell_counts.sum(axis=1)

    ss_fold = float((cell_counts.sum(axis=0) * (fold_means - grand_mean) ** 2).sum())
    ss_cond = float((cell_counts.sum(axis=1) * (cond_means - grand_mean) ** 2).sum())
    ss_within = float(sum(((v - v.mean()) ** 2).sum() for row in cells for v in row))
    ss_total = float(((all_values - grand_mean) ** 2).sum())
    # Whatever the main effects and seed noise do not explain is the
    # condition-by-fold interaction: the effect changing sign across folds.
    ss_interaction = ss_total - ss_fold - ss_cond - ss_within

    def share(ss: float) -> float:
        return float(ss / ss_total) if ss_total > 0 else float("nan")

    n_folds, n_conds = len(folds), len(conditions)
    return {
        "n_conditions": n_conds,
        "n_folds": n_folds,
        "n_runs": int(n_total),
        "grand_mean": grand_mean,
        "fold_means": {f: float(m) for f, m in zip(folds, fold_means)},
        "condition_means": {c: float(m) for c, m in zip(conditions, cond_means)},
        "fold_sd": float(np.std(fold_means, ddof=1)) if n_folds > 1 else 0.0,
        "condition_sd": float(np.std(cond_means, ddof=1)) if n_conds > 1 else 0.0,
        "seed_sd_within_cell": float(math.sqrt(
            ss_within / max(n_total - n_folds * n_conds, 1))),
        "ss_fold": ss_fold,
        "ss_condition": ss_cond,
        "ss_interaction": ss_interaction,
        "ss_seed_residual": ss_within,
        "ss_total": ss_total,
        "var_share_fold": share(ss_fold),
        "var_share_condition": share(ss_cond),
        "var_share_interaction": share(ss_interaction),
        "var_share_seed": share(ss_within),
    }


# ── Fold-count power analysis ───────────────────────────────────────────────

def required_folds_for_power(per_fold_deltas: Sequence[float],
                             power: float = 0.80,
                             alpha: float = 0.05,
                             max_folds: int = 200) -> Dict[str, float]:
    """How many folds a paired t-test needs to detect the observed effect.

    Treats the observed per-fold Δs as a sample from the population of
    folds: `d = mean(Δ) / sd(Δ)` is the standardized effect, and the
    required n follows from the normal approximation to the paired
    t-test, `n ≈ ((z_{1-α/2} + z_{power}) / d)²`, rounded up.

    This is a planning estimate, not an exact power calculation — with
    five observed folds the estimate of sd(Δ) is itself noisy, so treat
    the answer as an order of magnitude. Its purpose is to make the
    difference between "needs 6 folds" and "needs 300 folds" visible
    before compute is committed.
    """
    deltas = np.asarray(per_fold_deltas, dtype=np.float64)
    out: Dict[str, float] = {
        "n_folds_observed": int(deltas.size),
        "mean_delta": float(deltas.mean()) if deltas.size else float("nan"),
        "sd_delta": float(deltas.std(ddof=1)) if deltas.size > 1 else float("nan"),
        "power_target": power,
        "alpha": alpha,
    }
    if deltas.size < 2 or out["sd_delta"] == 0 or not np.isfinite(out["sd_delta"]):
        out["standardized_effect_d"] = float("nan")
        out["required_n_folds"] = float("nan")
        out["note"] = "insufficient folds to estimate the effect spread"
        return out

    d = abs(out["mean_delta"]) / out["sd_delta"]
    out["standardized_effect_d"] = float(d)
    if d == 0:
        out["required_n_folds"] = float("inf")
        out["note"] = "observed mean effect is exactly zero"
        return out

    from scipy.stats import norm
    z_alpha = float(norm.ppf(1 - alpha / 2))
    z_power = float(norm.ppf(power))
    n_required = math.ceil(((z_alpha + z_power) / d) ** 2)
    out["required_n_folds"] = float(n_required)
    if n_required > max_folds:
        out["note"] = (
            f"requires ~{n_required} folds, far beyond the {max_folds}-fold "
            f"planning ceiling — the effect is not separable from fold "
            f"variation at any practical cross-validation budget"
        )
    return out


def delta_variance_components(data: Dict[str, Dict[str, List[float]]],
                              baseline: str, treatment: str) -> Dict:
    """Split the *paired* effect's variance into fold and seed components.

    The overall variance decomposition above is dominated by between-fold
    differences in absolute difficulty, which the paired contrast already
    cancels. The planning question is different: given that we will
    always compare conditions within a fold, does buying another fold or
    another seed reduce the uncertainty on the mean effect faster?

    Model the matched difference as `delta[f, s] = mu + a_f + e_fs` with
    `a_f ~ (0, sigma_fold^2)` over folds and `e_fs ~ (0, sigma_seed^2)`
    within a fold. Then a design with F folds and S seeds per fold has

        SE(mean delta) = sqrt(sigma_fold^2 / F + sigma_seed^2 / (F * S))

    Seeds only ever shrink the second term, so when sigma_fold dominates,
    extra seeds are nearly free of statistical value and extra folds are
    the only thing that buys power. `se_for_design` below prices out the
    candidate budgets directly.
    """
    folds = _sorted_folds(set(data[baseline]) & set(data[treatment]))
    per_fold_deltas: Dict[str, np.ndarray] = {}
    for fold in folds:
        base = np.asarray(data[baseline][fold], dtype=np.float64)
        treat = np.asarray(data[treatment][fold], dtype=np.float64)
        if base.size != treat.size or base.size == 0:
            continue
        per_fold_deltas[fold] = treat - base
    if len(per_fold_deltas) < 2:
        raise ValueError("need at least two folds with matched seeds")

    fold_means = np.array([d.mean() for d in per_fold_deltas.values()])
    # Within-fold (seed) variance, pooled across folds.
    within_ss = float(sum(((d - d.mean()) ** 2).sum() for d in per_fold_deltas.values()))
    within_df = int(sum(d.size - 1 for d in per_fold_deltas.values()))
    sigma_seed_sq = within_ss / within_df if within_df > 0 else 0.0

    n_per_fold = np.array([d.size for d in per_fold_deltas.values()], dtype=np.float64)
    observed_fold_var = float(fold_means.var(ddof=1))
    # The spread of fold means already contains seed noise; subtract the
    # part attributable to averaging S seeds so sigma_fold is the true
    # between-fold component. Clamp at zero — a negative estimate means
    # the data are consistent with no genuine fold-to-fold variation.
    sigma_fold_sq = max(observed_fold_var - sigma_seed_sq / n_per_fold.mean(), 0.0)

    def se_for_design(n_folds: int, n_seeds: int) -> float:
        return math.sqrt(sigma_fold_sq / n_folds
                         + sigma_seed_sq / (n_folds * n_seeds))

    return {
        "n_folds": len(per_fold_deltas),
        "mean_seeds_per_fold": float(n_per_fold.mean()),
        "mean_delta": float(fold_means.mean()),
        "sigma_fold": math.sqrt(sigma_fold_sq),
        "sigma_seed": math.sqrt(sigma_seed_sq),
        "observed_sd_of_fold_means": math.sqrt(observed_fold_var),
        "fold_share_of_delta_variance": (
            float(sigma_fold_sq / (sigma_fold_sq + sigma_seed_sq))
            if (sigma_fold_sq + sigma_seed_sq) > 0 else float("nan")
        ),
        # Candidate Phase 1 / Phase 2 budgets, priced in runs and in the
        # standard error each budget buys on the mean effect.
        "se_by_design": {
            f"{f}fold_x_{s}seed": {
                "n_runs_per_condition": f * s,
                "se_mean_delta": se_for_design(f, s),
            }
            for f, s in ((1, 1), (1, 3), (5, 1), (5, 2), (5, 3),
                         (10, 1), (10, 3), (20, 1))
        },
    }


# ── Report ──────────────────────────────────────────────────────────────────

def analyze(data: Dict[str, Dict[str, List[float]]],
            baseline: str, treatment: str,
            all_conditions: Optional[Sequence[str]] = None) -> Dict:
    """Full fold-stability report for one baseline/treatment contrast."""
    fold_rows = per_fold_effects(data, baseline, treatment)
    deltas = [r["delta"] for r in fold_rows]
    n_improve = sum(1 for r in fold_rows if r["improves"])

    overall_base = np.concatenate(
        [np.asarray(data[baseline][r["fold"]]) for r in fold_rows])
    overall_treat = np.concatenate(
        [np.asarray(data[treatment][r["fold"]]) for r in fold_rows])

    report = {
        "baseline": baseline,
        "treatment": treatment,
        "per_fold": fold_rows,
        "aggregate": {
            "baseline_mean": float(overall_base.mean()),
            "treatment_mean": float(overall_treat.mean()),
            "mean_delta_across_folds": float(np.mean(deltas)),
            "sd_delta_across_folds": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
            "n_folds": len(fold_rows),
            "n_folds_improved": n_improve,
            "n_folds_worsened": len(fold_rows) - n_improve,
            "sign_consistent": n_improve in (0, len(fold_rows)),
        },
        "significance": paired_significance(data, baseline, treatment),
        "variance_decomposition": variance_decomposition(
            data, all_conditions or [baseline, treatment]),
        "power": required_folds_for_power(deltas),
    }
    try:
        report["delta_variance_components"] = delta_variance_components(
            data, baseline, treatment)
    except ValueError as exc:
        report["delta_variance_components"] = {"error": str(exc)}

    # The headline diagnostics: how the claimed effect compares with the
    # benchmark's own fold spread, and how much of the apparent effect is
    # really the effect changing from fold to fold.
    vd = report["variance_decomposition"]
    mean_delta = report["aggregate"]["mean_delta_across_folds"]
    report["aggregate"]["fold_sd_to_effect_ratio"] = (
        float(vd["fold_sd"] / abs(mean_delta)) if mean_delta else float("inf"))
    report["aggregate"]["interaction_to_condition_ratio"] = (
        float(vd["ss_interaction"] / vd["ss_condition"])
        if vd["ss_condition"] > 0 else float("inf"))
    return report


def format_report(report: Dict) -> str:
    """Human-readable summary, suitable for pasting into a lab notebook."""
    agg = report["aggregate"]
    vd = report["variance_decomposition"]
    pw = report["power"]
    lines = [
        f"Fold stability: {report['treatment']} vs {report['baseline']}",
        "=" * 60,
        "",
        f"{'fold':>6} {'baseline':>10} {'treatment':>10} {'delta':>8} "
        f"{'paired d':>9}  note",
    ]
    for r in report["per_fold"]:
        note = "improves" if r["improves"] else "worsens"
        if not r["delta_exceeds_seed_noise"]:
            note += ", within seed noise"
        lines.append(
            f"{r['fold']:>6} {r['baseline_mean']:>10.3f} "
            f"{r['treatment_mean']:>10.3f} {r['delta']:>+8.3f} "
            f"{r['paired_cohens_d']:>9.2f}  {note}"
        )
    lines += [
        "",
        f"Mean delta across folds : {agg['mean_delta_across_folds']:+.3f} min "
        f"(sd {agg['sd_delta_across_folds']:.3f})",
        f"Folds improved          : {agg['n_folds_improved']}/{agg['n_folds']}"
        f"{'  (sign-consistent)' if agg['sign_consistent'] else '  (SIGN REVERSES)'}",
        "",
        "Variance decomposition",
        f"  between-fold sd       : {vd['fold_sd']:.3f} min",
        f"  seed sd within cell   : {vd['seed_sd_within_cell']:.3f} min",
        f"  share fold            : {vd['var_share_fold']:.1%}",
        f"  share condition       : {vd['var_share_condition']:.1%}",
        f"  share condition x fold: {vd['var_share_interaction']:.1%}",
        f"  share seed            : {vd['var_share_seed']:.1%}",
        f"  fold sd / |effect|    : {agg['fold_sd_to_effect_ratio']:.1f}x",
        f"  interaction / condition: {agg['interaction_to_condition_ratio']:.1f}x"
        f"  <- effect is mostly fold-dependent"
        if agg["interaction_to_condition_ratio"] > 1 else
        f"  interaction / condition: {agg['interaction_to_condition_ratio']:.1f}x",
        "",
        "Significance (paired)",
    ]
    for key in ("by_run", "by_fold"):
        s = report["significance"][key]
        p = s.get("p_value")
        p_txt = "n/a" if p is None or p != p else f"{p:.4f}"
        lines.append(
            f"  {s['unit']:<18}: n={s['n_paired']:<3} p={p_txt} "
            f"({s['n_treatment_better']} better / {s['n_baseline_better']} worse)"
        )
    lines += [
        "",
        "Power",
        f"  standardized effect d : {pw['standardized_effect_d']:.3f}",
        f"  folds for 80% power   : {pw['required_n_folds']:.0f}",
    ]
    if "note" in pw:
        lines.append(f"  note                  : {pw['note']}")

    dvc = report.get("delta_variance_components", {})
    if "error" not in dvc:
        lines += [
            "",
            "Where the effect's own uncertainty lives (paired delta)",
            f"  sigma_fold            : {dvc['sigma_fold']:.3f} min",
            f"  sigma_seed            : {dvc['sigma_seed']:.3f} min",
            f"  fold share of delta var: {dvc['fold_share_of_delta_variance']:.1%}",
            "",
            f"  {'design':>16} {'runs/cond':>10} {'SE(mean delta)':>15}",
        ]
        for name, entry in dvc["se_by_design"].items():
            lines.append(
                f"  {name:>16} {entry['n_runs_per_condition']:>10} "
                f"{entry['se_mean_delta']:>15.3f}"
            )
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--summary-json", required=True, type=Path,
                    help="Phase-E-style aggregate, e.g. "
                         "papers/paper1_neurips2026/manuscript/phase_e_summary.json")
    ap.add_argument("--baseline", default="no_token")
    ap.add_argument("--treatment", default="decoupled")
    ap.add_argument("--conditions", nargs="*", default=None,
                    help="Conditions to include in the variance decomposition "
                         "(default: baseline + treatment).")
    ap.add_argument("--report-out", type=Path, default=None)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    data = load_phase_e_summary(args.summary_json)
    report = analyze(data, args.baseline, args.treatment,
                     all_conditions=args.conditions)
    print(format_report(report))

    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(json.dumps(report, indent=2))
        logger.info("\nWrote %s", args.report_out)


if __name__ == "__main__":
    main()

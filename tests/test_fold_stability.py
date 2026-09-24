"""Tests for the Paper 2A fold-stability analyzer.

Phase 0 kickoff deliverable: "Verify it reproduces Paper 1's Appendix C
numbers (Δ = −0.19 min average, per-fold: −0.85, −0.23, +0.23, +0.13,
−0.22)." Those literals are asserted below against the committed
`papers/paper1_neurips2026/manuscript/phase_e_summary.json`, so a change to either the aggregation or
the analyzer that moves the published numbers fails the suite.

The synthetic cases pin down the variance decomposition and power
estimate independently of that one dataset.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2_infra.evaluation.fold_stability import (  # noqa: E402
    analyze,
    delta_variance_components,
    format_report,
    load_phase_e_summary,
    paired_cohens_d,
    per_fold_effects,
    required_folds_for_power,
    variance_decomposition,
)

REPO = Path(__file__).resolve().parents[1]
PHASE_E = REPO / "papers" / "paper1_neurips2026" / "manuscript" / "phase_e_summary.json"

# Paper 1, Appendix C.1 — the five-fold strict-protocol table.
PAPER1_DECOUPLED_DELTAS = [-0.85, -0.23, +0.23, +0.13, -0.22]
PAPER1_DECOUPLED_MEAN_DELTA = -0.19
PAPER1_NO_TOKEN_5FOLD_MEAN = 11.02
PAPER1_DECOUPLED_5FOLD_MEAN = 10.83
PAPER1_ORACLE_5FOLD_MEAN = 10.84


@pytest.fixture(scope="module")
def phase_e():
    if not PHASE_E.exists():
        pytest.skip(f"{PHASE_E.relative_to(REPO)} not present in this checkout")
    return load_phase_e_summary(PHASE_E)


# ── Reproduction of Paper 1's published numbers ─────────────────────────────

def test_reproduces_paper1_per_fold_deltas(phase_e):
    rows = per_fold_effects(phase_e, "no_token", "decoupled")
    assert [r["fold"] for r in rows] == ["0", "1", "2", "3", "4"]
    for row, expected in zip(rows, PAPER1_DECOUPLED_DELTAS):
        assert row["delta"] == pytest.approx(expected, abs=0.005), (
            f"fold {row['fold']}: {row['delta']:+.3f} != published {expected:+.2f}"
        )


def test_reproduces_paper1_five_fold_means(phase_e):
    report = analyze(phase_e, "no_token", "decoupled")
    agg = report["aggregate"]
    assert agg["baseline_mean"] == pytest.approx(PAPER1_NO_TOKEN_5FOLD_MEAN, abs=0.005)
    assert agg["treatment_mean"] == pytest.approx(PAPER1_DECOUPLED_5FOLD_MEAN, abs=0.005)
    assert agg["mean_delta_across_folds"] == pytest.approx(
        PAPER1_DECOUPLED_MEAN_DELTA, abs=0.005)


def test_reproduces_paper1_oracle_arm(phase_e):
    report = analyze(phase_e, "no_token", "oracle")
    assert report["aggregate"]["treatment_mean"] == pytest.approx(
        PAPER1_ORACLE_5FOLD_MEAN, abs=0.005)
    # Appendix C.1's fold-0 oracle delta is −0.78.
    fold0 = report["per_fold"][0]
    assert fold0["delta"] == pytest.approx(-0.78, abs=0.005)


def test_paper1_effect_reverses_sign_across_folds(phase_e):
    """The finding that drove the rebuttal: 3 of 5 folds improve."""
    report = analyze(phase_e, "no_token", "decoupled")
    agg = report["aggregate"]
    assert agg["n_folds_improved"] == 3
    assert agg["n_folds_worsened"] == 2
    assert agg["sign_consistent"] is False


def test_paper1_fold_variance_dominates(phase_e):
    """Between-fold spread swamps the conditioning effect on MB140."""
    report = analyze(phase_e, "no_token", "decoupled")
    vd = report["variance_decomposition"]
    assert vd["var_share_fold"] > 0.90
    assert vd["var_share_condition"] < 0.02
    # The fold spread is several times the size of the claimed effect.
    assert report["aggregate"]["fold_sd_to_effect_ratio"] > 5.0


def test_paper1_five_folds_are_underpowered(phase_e):
    """5-fold MB140 cannot resolve a 0.19-min effect; quantify by how much."""
    report = analyze(phase_e, "no_token", "decoupled")
    assert report["power"]["required_n_folds"] > 20
    # And neither paired test reaches significance.
    assert report["significance"]["by_run"]["p_value"] > 0.05
    assert report["significance"]["by_fold"]["p_value"] > 0.05


def test_report_formats_without_error(phase_e):
    text = format_report(analyze(phase_e, "no_token", "decoupled"))
    assert "SIGN REVERSES" in text
    assert "fold sd / |effect|" in text


# ── Variance decomposition on controlled synthetic data ─────────────────────

def _synthetic(fold_offsets, condition_offsets, seed_noise=(0.0, 0.0, 0.0)):
    """y[cond][fold][seed] = base + fold_offset + cond_offset + seed_noise."""
    return {
        cond: {
            str(f): [10.0 + fo + co + sn for sn in seed_noise]
            for f, fo in enumerate(fold_offsets)
        }
        for cond, co in condition_offsets.items()
    }


def test_variance_decomposition_all_fold():
    """Folds differ, conditions identical → all variance is fold."""
    data = _synthetic([-2.0, -1.0, 0.0, 1.0, 2.0], {"a": 0.0, "b": 0.0})
    vd = variance_decomposition(data)
    assert vd["var_share_fold"] == pytest.approx(1.0)
    assert vd["var_share_condition"] == pytest.approx(0.0)
    assert vd["var_share_seed"] == pytest.approx(0.0)


def test_variance_decomposition_all_condition():
    """Conditions differ, folds identical → all variance is condition."""
    data = _synthetic([0.0, 0.0, 0.0], {"a": -1.0, "b": 1.0})
    vd = variance_decomposition(data)
    assert vd["var_share_condition"] == pytest.approx(1.0)
    assert vd["var_share_fold"] == pytest.approx(0.0)


def test_variance_decomposition_all_seed():
    """Only seeds differ → all variance is residual."""
    data = _synthetic([0.0, 0.0, 0.0], {"a": 0.0, "b": 0.0},
                      seed_noise=(-0.5, 0.0, 0.5))
    vd = variance_decomposition(data)
    assert vd["var_share_seed"] == pytest.approx(1.0)
    assert vd["seed_sd_within_cell"] == pytest.approx(0.5)


def test_variance_shares_sum_to_one():
    data = _synthetic([-2.0, 0.0, 3.0], {"a": -0.4, "b": 0.4},
                      seed_noise=(-0.2, 0.05, 0.15))
    vd = variance_decomposition(data)
    total = (vd["var_share_fold"] + vd["var_share_condition"]
             + vd["var_share_interaction"] + vd["var_share_seed"])
    assert total == pytest.approx(1.0)


def test_variance_decomposition_handles_unbalanced_seeds():
    data = _synthetic([-1.0, 1.0], {"a": 0.0, "b": 0.5})
    data["b"]["0"] = data["b"]["0"][:2]  # drop a seed
    vd = variance_decomposition(data)
    # 2 conditions x 2 folds x 3 seeds, minus the one dropped seed.
    assert vd["n_runs"] == 11
    assert 0.0 <= vd["var_share_fold"] <= 1.0


def test_variance_decomposition_rejects_disjoint_folds():
    data = {"a": {"0": [1.0]}, "b": {"1": [1.0]}}
    with pytest.raises(ValueError, match="share no folds"):
        variance_decomposition(data)


# ── Effect size + power ─────────────────────────────────────────────────────

def test_paired_cohens_d_known_value():
    # diffs = [1, 2, 3] → mean 2, sd 1 → d = 2
    assert paired_cohens_d([2.0, 4.0, 6.0], [1.0, 2.0, 3.0]) == pytest.approx(2.0)


def test_paired_cohens_d_undefined_without_spread():
    d = paired_cohens_d([2.0, 2.0, 2.0], [1.0, 1.0, 1.0])
    assert d != d  # NaN, not infinity


def test_required_folds_shrinks_as_effect_gets_cleaner():
    noisy = required_folds_for_power([-0.85, -0.23, 0.23, 0.13, -0.22])
    clean = required_folds_for_power([-0.85, -0.80, -0.90, -0.83, -0.87])
    assert clean["required_n_folds"] < noisy["required_n_folds"]
    assert clean["required_n_folds"] < 10


def test_required_folds_flags_hopeless_effects():
    out = required_folds_for_power([0.5, -0.5, 0.5, -0.5, 0.02])
    assert out["required_n_folds"] > 100
    assert "note" in out


def test_required_folds_needs_at_least_two_folds():
    out = required_folds_for_power([-0.5])
    assert out["required_n_folds"] != out["required_n_folds"]  # NaN
    assert "insufficient" in out["note"]


# ── Paired-delta variance components (Phase 1 budget planning) ──────────────

def test_delta_variance_is_dominated_by_folds_on_mb140(phase_e):
    """The Phase 1 budget finding: seeds buy almost no power, folds do."""
    dvc = delta_variance_components(phase_e, "no_token", "decoupled")
    assert dvc["fold_share_of_delta_variance"] > 0.90
    assert dvc["sigma_fold"] > 5 * dvc["sigma_seed"]


def test_more_folds_beat_more_seeds_at_equal_run_count(phase_e):
    """10 folds x 1 seed (10 runs) must beat 5 folds x 2 seeds (10 runs)."""
    dvc = delta_variance_components(phase_e, "no_token", "decoupled")
    by_design = dvc["se_by_design"]
    assert (by_design["10fold_x_1seed"]["n_runs_per_condition"]
            == by_design["5fold_x_2seed"]["n_runs_per_condition"])
    assert (by_design["10fold_x_1seed"]["se_mean_delta"]
            < by_design["5fold_x_2seed"]["se_mean_delta"])

    # And tripling seeds at fixed folds must be nearly useless: less than a
    # 5% reduction in SE for 3x the compute.
    se_1 = by_design["5fold_x_1seed"]["se_mean_delta"]
    se_3 = by_design["5fold_x_3seed"]["se_mean_delta"]
    assert se_3 > 0.95 * se_1


def test_single_fold_se_explains_paper1_headline(phase_e):
    """Fold 0's −0.85 is within ~2 SE of the −0.19 five-fold mean.

    This is the retrospective check on Paper 1: a one-fold design has an
    SE large enough that the development-fold headline is consistent with
    noise around the true effect, which is exactly what happened.
    """
    dvc = delta_variance_components(phase_e, "no_token", "decoupled")
    se_one_fold = dvc["se_by_design"]["1fold_x_3seed"]["se_mean_delta"]
    fold0_delta = -0.850
    z = abs(fold0_delta - dvc["mean_delta"]) / se_one_fold
    assert z < 2.0, f"fold-0 headline is {z:.1f} SE from the mean effect"


def test_delta_components_recover_known_synthetic_variance():
    """Pure fold effect, no seed noise → sigma_seed = 0."""
    data = {
        "base": {str(f): [10.0, 10.0, 10.0] for f in range(5)},
        "treat": {str(f): [10.0 + d, 10.0 + d, 10.0 + d]
                  for f, d in enumerate([-1.0, -0.5, 0.0, 0.5, 1.0])},
    }
    dvc = delta_variance_components(data, "base", "treat")
    assert dvc["sigma_seed"] == pytest.approx(0.0)
    assert dvc["sigma_fold"] == pytest.approx(0.7906, abs=1e-3)  # sd of deltas
    assert dvc["mean_delta"] == pytest.approx(0.0, abs=1e-12)
    assert dvc["fold_share_of_delta_variance"] == pytest.approx(1.0)


def test_delta_components_attribute_pure_seed_noise_to_seeds():
    """Identical fold effects, seeds differ → sigma_fold clamps to 0."""
    data = {
        "base": {str(f): [10.0, 10.0, 10.0] for f in range(5)},
        "treat": {str(f): [9.5, 10.0, 10.5] for f in range(5)},
    }
    dvc = delta_variance_components(data, "base", "treat")
    assert dvc["sigma_fold"] == pytest.approx(0.0)
    assert dvc["sigma_seed"] == pytest.approx(0.5)


def test_delta_components_need_two_matched_folds():
    data = {"base": {"0": [1.0, 2.0]}, "treat": {"0": [1.0, 2.0]}}
    with pytest.raises(ValueError, match="at least two folds"):
        delta_variance_components(data, "base", "treat")


def test_report_is_json_serializable(phase_e):
    """The CLI dumps the report; nothing in it may be a callable."""
    report = analyze(phase_e, "no_token", "decoupled")
    json.dumps(report)  # raises TypeError if any value is not serializable


# ── Input handling ──────────────────────────────────────────────────────────

def test_load_rejects_summary_without_per_fold(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"overall": {}}))
    with pytest.raises(ValueError, match="per_fold"):
        load_phase_e_summary(path)


def test_unknown_condition_names_are_reported(phase_e):
    with pytest.raises(KeyError, match="not in summary"):
        per_fold_effects(phase_e, "no_token", "does_not_exist")

"""Tests for the cross-representation workflow-variability comparison."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2_infra.workflow_representations.compare import (  # noqa: E402
    adjusted_rand_index,
    assignment_variability,
    compare_representations,
    format_comparison,
    load_hmm_assignments,
    load_kmeans_assignments,
    seed_stability,
)

REPO = Path(__file__).resolve().parents[1]


# ── Adjusted Rand index ─────────────────────────────────────────────────────

def test_ari_is_one_for_identical_clusterings():
    labels = [0, 0, 1, 1, 2, 2]
    assert adjusted_rand_index(labels, labels) == pytest.approx(1.0)


def test_ari_is_invariant_to_relabeling():
    a = [0, 0, 1, 1, 2, 2]
    b = [7, 7, 5, 5, 9, 9]  # same partition, different names
    assert adjusted_rand_index(a, b) == pytest.approx(1.0)


def test_ari_is_near_zero_for_unrelated_clusterings():
    a = [0, 0, 0, 0, 1, 1, 1, 1]
    b = [0, 1, 0, 1, 0, 1, 0, 1]
    assert abs(adjusted_rand_index(a, b)) < 0.2


def test_ari_is_one_when_both_are_trivial():
    """Both clusterings put everything in one group: perfect agreement."""
    assert adjusted_rand_index([0] * 5, [3] * 5) == pytest.approx(1.0)


def test_ari_detects_a_partial_split():
    """One family splits a cluster the other keeps whole → between 0 and 1."""
    a = [0, 0, 0, 0, 1, 1, 1, 1]
    b = [0, 0, 1, 1, 2, 2, 2, 2]
    ari = adjusted_rand_index(a, b)
    assert 0.0 < ari < 1.0


def test_ari_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="differ in length"):
        adjusted_rand_index([0, 1], [0, 1, 2])


# ── Variability ─────────────────────────────────────────────────────────────

def test_variability_is_maximal_for_a_balanced_assignment():
    assignments = {f"v{i}": i % 4 for i in range(40)}
    v = assignment_variability(assignments)
    assert v["entropy_normalized_by_used"] == pytest.approx(1.0)
    assert v["dominant_cluster_share"] == pytest.approx(0.25)
    assert v["n_clusters_used"] == 4


def test_variability_is_zero_when_every_video_shares_a_cluster():
    v = assignment_variability({f"v{i}": 0 for i in range(10)})
    assert v["entropy_nats"] == pytest.approx(0.0)
    assert v["entropy_normalized_by_used"] == 0.0
    assert v["dominant_cluster_share"] == pytest.approx(1.0)


def test_variability_flags_a_dominant_cluster():
    """9 of 10 in one cluster: entropy is low and the share exposes why."""
    assignments = {f"v{i}": (0 if i < 9 else 1) for i in range(10)}
    v = assignment_variability(assignments)
    assert v["dominant_cluster_share"] == pytest.approx(0.9)
    assert v["entropy_nats"] < 0.4


def test_variability_rejects_empty_input():
    with pytest.raises(ValueError, match="no assignments"):
        assignment_variability({})


# ── Comparison plumbing ─────────────────────────────────────────────────────

def test_compare_reports_variability_and_pairwise_agreement():
    result = compare_representations({
        "r1": {f"v{i}": i % 3 for i in range(12)},
        "r3": {f"v{i}": i % 3 for i in range(12)},
    })
    assert set(result["variability"]) == {"r1", "r3"}
    assert result["agreement"]["r1__vs__r3"]["adjusted_rand_index"] == pytest.approx(1.0)
    assert result["agreement"]["r1__vs__r3"]["n_shared_videos"] == 12


def test_compare_uses_only_shared_videos():
    result = compare_representations({
        "r1": {"a": 0, "b": 0, "c": 1, "d": 1},
        "r3": {"c": 5, "d": 5, "e": 9},  # only c, d are shared
    })
    assert result["agreement"]["r1__vs__r3"]["n_shared_videos"] == 2


def test_compare_flags_imbalanced_partitions():
    """A low ARI between two lopsided partitions must carry its caveat."""
    lopsided = {f"v{i}": (0 if i < 18 else i) for i in range(20)}
    other = {f"v{i}": (0 if i < 17 else 99) for i in range(20)}
    result = compare_representations({"a": lopsided, "b": other})
    entry = result["agreement"]["a__vs__b"]
    assert entry["max_dominant_cluster_share"] >= 0.85
    assert "caveat" in entry
    assert "minority" in entry["caveat"]


def test_compare_omits_caveat_for_balanced_partitions():
    balanced_a = {f"v{i}": i % 4 for i in range(40)}
    balanced_b = {f"v{i}": (i + 1) % 4 for i in range(40)}
    result = compare_representations({"a": balanced_a, "b": balanced_b})
    assert "caveat" not in result["agreement"]["a__vs__b"]


def test_compare_handles_no_overlap_without_crashing():
    result = compare_representations({
        "r1": {"a": 0, "b": 1},
        "r3": {"x": 0, "y": 1},
    })
    agreement = result["agreement"]["r1__vs__r3"]
    assert agreement["n_shared_videos"] == 0
    assert agreement["adjusted_rand_index"] != agreement["adjusted_rand_index"]  # NaN


def test_format_comparison_renders():
    per_dataset = {
        "MB140": compare_representations({
            "kmeans (R1)": {f"v{i}": i % 6 for i in range(30)},
            "hmm-causal (R3)": {f"v{i}": i % 6 for i in range(30)},
        })
    }
    text = format_comparison(per_dataset)
    assert "MB140" in text and "ARI" in text and "same construct" in text


def test_format_flags_disagreeing_families():
    per_dataset = {
        "D": compare_representations({
            "a": {f"v{i}": i % 2 for i in range(20)},
            "b": {f"v{i}": (i // 10) for i in range(20)},
        })
    }
    assert "DIFFERENT constructs" in format_comparison(per_dataset)


# ── Seed stability ──────────────────────────────────────────────────────────

def test_seed_stability_is_one_for_a_deterministic_representation():
    """Cholec80's case: the partition is forced, so every seed agrees."""
    fixed = {f"v{i}": i % 6 for i in range(72)}
    out = seed_stability({0: dict(fixed), 1: dict(fixed), 42: dict(fixed)})
    assert out["mean_ari"] == pytest.approx(1.0)
    assert out["min_ari"] == pytest.approx(1.0)
    assert out["n_pairs"] == 3


def test_seed_stability_detects_an_unstable_representation():
    """MB140's case: seeds produce materially different partitions."""
    by_seed = {
        0: {f"v{i}": i % 4 for i in range(40)},
        1: {f"v{i}": (i // 10) for i in range(40)},
        2: {f"v{i}": (i * 3) % 4 for i in range(40)},
    }
    out = seed_stability(by_seed)
    assert out["mean_ari"] < 0.5
    assert out["n_seeds"] == 3


def test_seed_stability_reports_the_full_pair_list():
    by_seed = {s: {f"v{i}": i % 3 for i in range(9)} for s in (7, 8, 9, 10)}
    out = seed_stability(by_seed)
    assert out["n_pairs"] == 6  # C(4, 2)
    assert {p["seed_a"] for p in out["pairs"]} == {7, 8, 9}
    assert all("adjusted_rand_index" in p for p in out["pairs"])


def test_seed_stability_needs_two_seeds():
    with pytest.raises(ValueError, match="at least two seeds"):
        seed_stability({0: {"v0": 1, "v1": 2}})


def test_seed_stability_rejects_disjoint_video_sets():
    with pytest.raises(ValueError, match="no seed pair"):
        seed_stability({0: {"a": 0, "b": 1}, 1: {"x": 0, "y": 1}})


# ── Loaders ─────────────────────────────────────────────────────────────────

def test_load_kmeans_assignments_from_real_labels():
    path = REPO / "labels" / "mb140_fold0_labels_kmeans.json"
    if not path.exists():
        pytest.skip("MB140 k-means labels not present")
    assignments = load_kmeans_assignments(path)
    assert len(assignments) == 140
    assert all(isinstance(v, int) for v in assignments.values())


def test_load_hmm_assignments_round_trip(tmp_path: Path):
    payload = {
        "representations": {
            "v1": {"causal": [0.8, 0.1, 0.1], "oracle": [0.1, 0.8, 0.1]},
            "v2": {"causal": [0.1, 0.1, 0.8], "oracle": [0.1, 0.1, 0.8]},
        }
    }
    path = tmp_path / "hmm.json"
    path.write_text(json.dumps(payload))
    assert load_hmm_assignments(path, "causal") == {"v1": 0, "v2": 2}
    assert load_hmm_assignments(path, "oracle") == {"v1": 1, "v2": 2}


def test_load_hmm_assignments_rejects_a_sweep_file(tmp_path: Path):
    path = tmp_path / "sweep.json"
    path.write_text(json.dumps({"sweep": [], "best_by_bic": 4}))
    with pytest.raises(ValueError, match="state-count sweep"):
        load_hmm_assignments(path)


# ── The Paper 1 premise ─────────────────────────────────────────────────────

def test_mb140_is_more_workflow_variable_than_cholec80_under_kmeans():
    """Paper 1's premise, measured. MB140 should spread across clusters
    while Cholec80 concentrates in one."""
    mb = REPO / "labels" / "mb140_fold0_labels_kmeans.json"
    ch = REPO / "labels" / "cholec80_labels_kmeans.json"
    if not (mb.exists() and ch.exists()):
        pytest.skip("k-means labels not present in this checkout")

    mb_v = assignment_variability(load_kmeans_assignments(mb))
    ch_v = assignment_variability(load_kmeans_assignments(ch))

    assert mb_v["entropy_nats"] > ch_v["entropy_nats"]
    # Cholec80 concentrates the majority of its videos in one workflow.
    assert ch_v["dominant_cluster_share"] > 0.5
    assert mb_v["dominant_cluster_share"] < 0.35

"""Tests for the R1d duration-aware k-means workflow representation.

R1d exists to test one hypothesis: that R1 and R3 disagree because R1
reads phase *order* and R3 reads phase *timing*. For that test to mean
anything, R1d must differ from Paper 1's R1 in exactly one respect — the
duration block — so the tests below pin the tokenizer to R1's behaviour
and check that weight 0 reproduces the order-only pipeline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

pytest.importorskip("sklearn")

from paper2_infra.workflow_representations.duration_aware_kmeans import (  # noqa: E402
    build_features,
    cluster,
    phase_bigrams,
    phase_duration_features,
    run,
)

REPO = Path(__file__).resolve().parents[1]


def _video(video_id, phases_with_durations, split="train"):
    """Build a label record from [(phase_name, seconds), ...]."""
    vocab = {"A": 0, "B": 1, "C": 2}
    frames, t = [], 0
    sequence = []
    for phase, seconds in phases_with_durations:
        sequence.append(phase)
        for _ in range(seconds):
            frames.append({"frame_idx": t, "timestamp_sec": float(t),
                           "phase": phase})
            t += 1
    return {
        "video_id": video_id, "total_duration_sec": float(t),
        "phase_sequence": sequence, "phase_vocab": vocab,
        "split": split, "frames": frames,
    }


# ── Tokenizer parity with Paper 1 ───────────────────────────────────────────

def test_bigram_tokenizer_matches_paper1_behaviour():
    """Lowercase, spaces to underscores, apostrophes stripped, arrow-joined."""
    seq = ["Preparation", "Gastric pouch creation", "Closure of Petersen's space"]
    assert phase_bigrams(seq) == (
        "preparation->gastric_pouch_creation "
        "gastric_pouch_creation->closure_of_petersens_space"
    )


def test_bigram_of_a_single_phase_is_empty():
    assert phase_bigrams(["OnlyPhase"]) == ""


# ── Duration features ───────────────────────────────────────────────────────

def test_duration_features_count_seconds_per_phase():
    vocab = {"A": 0, "B": 1, "C": 2}
    video = _video("V1", [("A", 100), ("B", 50)])
    feats = phase_duration_features(video, vocab)
    # log1p of [100 seconds of A, 50 of B, 0 of C, 150 total]
    np.testing.assert_allclose(
        feats, np.log1p([100.0, 50.0, 0.0, 150.0]), rtol=1e-9)


def test_duration_features_are_log_scaled():
    """A 3-hour case must not dominate a 1-hour case linearly."""
    vocab = {"A": 0, "B": 1, "C": 2}
    short = phase_duration_features(_video("s", [("A", 3600)]), vocab)
    long = phase_duration_features(_video("l", [("A", 10800)]), vocab)
    assert long[0] / short[0] < 1.2  # ~1.13 under log1p, not 3.0


# ── Feature assembly ────────────────────────────────────────────────────────

def _corpus():
    """Six videos: three phase orders x two duration profiles each."""
    videos = []
    for i, order in enumerate([[("A", 60), ("B", 60)],
                               [("B", 60), ("C", 60)],
                               [("A", 60), ("C", 60)]]):
        for j, scale in enumerate([1, 4]):
            scaled = [(p, s * scale) for p, s in order]
            videos.append(_video(f"V{i}{j}", scaled))
    return videos


def test_weight_zero_produces_order_only_features():
    videos = _corpus()
    order_only, meta = build_features(videos, duration_weight=0.0)
    assert "n_duration_features" not in meta
    assert meta["duration_weight"] == 0.0
    # Videos sharing a phase order must be identical when durations are
    # invisible — this is exactly the R1 property under test.
    np.testing.assert_allclose(order_only[0], order_only[1], atol=1e-9)


def test_duration_weight_separates_videos_sharing_a_phase_order():
    videos = _corpus()
    with_durations, meta = build_features(videos, duration_weight=1.0)
    assert meta["n_duration_features"] > 0
    # The same two videos must now differ.
    assert not np.allclose(with_durations[0], with_durations[1], atol=1e-6)


def test_duration_weight_scales_the_duration_block_norm():
    """The weight should control the duration block's share of the norm."""
    videos = _corpus()
    base, _ = build_features(videos, duration_weight=0.0)
    n_order = base.shape[1]
    light, _ = build_features(videos, duration_weight=0.5)
    heavy, _ = build_features(videos, duration_weight=2.0)
    light_norm = np.linalg.norm(light[:, n_order:])
    heavy_norm = np.linalg.norm(heavy[:, n_order:])
    assert heavy_norm > light_norm
    assert heavy_norm / light_norm == pytest.approx(4.0, rel=0.05)


def test_constant_duration_columns_are_dropped():
    """A phase every video runs for the same time carries no information
    and would divide by a zero standard deviation."""
    videos = [_video(f"V{i}", [("A", 60), ("B", 60 + i)]) for i in range(4)]
    feats, meta = build_features(videos, duration_weight=1.0)
    assert np.isfinite(feats).all()
    # Phase C never occurs and phase A is constant; both must be dropped.
    assert meta["n_duration_features"] < 4


# ── Clustering + end-to-end ─────────────────────────────────────────────────

def test_cluster_returns_one_label_per_video():
    videos = _corpus()
    feats, _ = build_features(videos, duration_weight=0.0)
    labels = cluster(feats, k=3, seed=42)
    assert labels.shape == (len(videos),)
    assert set(labels.tolist()) <= {0, 1, 2}


def test_run_is_deterministic_for_a_fixed_seed(tmp_path: Path):
    path = tmp_path / "labels.json"
    path.write_text(json.dumps(_corpus()))
    a, _ = run(path, k=3, duration_weight=1.0, seed=7)
    b, _ = run(path, k=3, duration_weight=1.0, seed=7)
    assert a == b


def test_run_on_real_mb140_labels():
    path = REPO / "labels" / "mb140_fold0_labels.json"
    if not path.exists():
        pytest.skip("MB140 labels not present in this checkout")
    assignments, meta = run(path, k=6, duration_weight=1.0, seed=42)
    assert len(assignments) == 140
    assert meta["k"] == 6
    assert meta["n_duration_features"] > 0
    assert set(assignments.values()) <= set(range(6))

"""Tests for the Paper 2A strict prefix-only phase-anticipation evaluator.

Phase 0 kickoff deliverable #3: "ground-truth extraction implemented,
metric functions verified against a synthetic test video with known
answers."

The synthetic fixture is a 10-minute video whose phase transitions are
placed at round numbers so every expected ground-truth value can be
computed by hand and written into the assertions as a literal.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2_infra.evaluation.evaluate_phase_anticipation import (  # noqa: E402
    ClipRecord,
    build_ground_truth,
    ece_next_phase,
    horizon_macro_f1,
    macro_f1_next_phase,
    mae_transition_time_minutes,
    paired_bootstrap_ci,
    per_video_video_weighted,
)

# The synthetic video: 600 seconds at 1 fps, three phases.
#   t ∈ [  0, 179] → phase A (id 0)
#   t ∈ [180, 419] → phase B (id 1)
#   t ∈ [420, 599] → phase C (id 2)
# Transitions therefore occur at t=180 and t=420.
VOCAB = {"A": 0, "B": 1, "C": 2}
PHASE_BOUNDARIES = [(0, 180, "A"), (180, 420, "B"), (420, 600, "C")]


def _synthetic_video(video_id: str = "SYN01", split: str = "test",
                     frame_idx_offset: int = 0,
                     timestamp_offset: float = 0.0) -> dict:
    """A 600-second, 1 fps, three-phase video in the shared label schema.

    `frame_idx_offset` / `timestamp_offset` exercise the real-data case
    where a video does not start at frame 0 / second 0 (MB140 videos
    start at frame_idx 13, timestamp_sec 14.0).
    """
    frames = []
    for t in range(600):
        phase = next(p for lo, hi, p in PHASE_BOUNDARIES if lo <= t < hi)
        frames.append({
            "frame_idx": t + frame_idx_offset,
            "timestamp_sec": float(t) + timestamp_offset,
            "rsd_sec": float(599 - t),
            "phase": phase,
        })
    return {
        "video_id": video_id,
        "total_duration_sec": 600.0,
        "phase_sequence": ["A", "B", "C"],
        "phase_vocab": VOCAB,
        "phase_order_cluster": 0,
        "split": split,
        "frames": frames,
    }


@pytest.fixture
def synthetic_label_json(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic_labels.json"
    path.write_text(json.dumps([_synthetic_video()]))
    return path


# ── Ground-truth extraction ─────────────────────────────────────────────────

def test_ground_truth_transition_times_are_exact(synthetic_label_json):
    """Hand-computed seconds-to-next-transition at known clip ends."""
    gt = build_ground_truth(synthetic_label_json, split="test",
                            min_prefix_sec=0, horizons_min=(1, 5))

    # Inside phase A, next transition is at t=180.
    assert gt[("SYN01", 0)].seconds_to_next_transition == 180.0
    assert gt[("SYN01", 0)].next_phase_id == VOCAB["B"]
    assert gt[("SYN01", 100)].seconds_to_next_transition == 80.0
    assert gt[("SYN01", 179)].seconds_to_next_transition == 1.0

    # First frame of phase B: next transition is at t=420.
    assert gt[("SYN01", 180)].seconds_to_next_transition == 240.0
    assert gt[("SYN01", 180)].next_phase_id == VOCAB["C"]
    assert gt[("SYN01", 180)].current_phase_id == VOCAB["B"]

    # Inside the final phase there is no future transition.
    assert gt[("SYN01", 420)].seconds_to_next_transition == float("inf")
    assert gt[("SYN01", 420)].next_phase_id is None
    assert gt[("SYN01", 599)].seconds_to_next_transition == float("inf")


def test_ground_truth_future_horizons(synthetic_label_json):
    """Hand-computed phase-at-horizon lookups, including past-end None."""
    gt = build_ground_truth(synthetic_label_json, split="test",
                            min_prefix_sec=0, horizons_min=(1, 2, 5, 10, 20))

    # From t=0: +1min → t=60 (A), +2min → t=120 (A), +5min → t=300 (B),
    # +10min → t=600 which is one second past the last frame (599) → None.
    r0 = gt[("SYN01", 0)].future_phase_at_horizon
    assert r0[1] == VOCAB["A"]
    assert r0[2] == VOCAB["A"]
    assert r0[5] == VOCAB["B"]
    assert r0[10] is None
    assert r0[20] is None

    # From t=170: +1min → t=230 (B), +5min → t=470 (C).
    r170 = gt[("SYN01", 170)].future_phase_at_horizon
    assert r170[1] == VOCAB["B"]
    assert r170[5] == VOCAB["C"]


def test_ground_truth_respects_frame_index_offset(tmp_path: Path):
    """Keying uses frame_idx; time arithmetic uses timestamp_sec."""
    path = tmp_path / "offset_labels.json"
    path.write_text(json.dumps([
        _synthetic_video(frame_idx_offset=13, timestamp_offset=14.0)
    ]))
    gt = build_ground_truth(path, split="test", min_prefix_sec=0,
                            horizons_min=(1,))

    # The video's own first frame is frame_idx 13 at t=14.0s. The phase-A
    # to phase-B transition is 180 frames later: frame_idx 193, t=194.0.
    assert ("SYN01", 13) in gt
    assert ("SYN01", 0) not in gt
    first = gt[("SYN01", 13)]
    assert first.clip_end_sec == 14.0
    assert first.seconds_to_next_transition == 180.0
    assert gt[("SYN01", 193)].current_phase_id == VOCAB["B"]
    assert gt[("SYN01", 193)].seconds_to_next_transition == 240.0


def test_strict_prefix_filter_excludes_early_clips(synthetic_label_json):
    """min_prefix_sec enforces the strict protocol at GT-construction time."""
    gt = build_ground_truth(synthetic_label_json, split="test",
                            min_prefix_sec=35, horizons_min=(1,))
    assert ("SYN01", 34) not in gt
    assert ("SYN01", 35) in gt
    # 600 frames minus the first 35 seconds of unusable prefix.
    assert len(gt) == 600 - 35


def test_clip_stride_subsamples_evaluable_clip_ends(synthetic_label_json):
    gt = build_ground_truth(synthetic_label_json, split="test",
                            min_prefix_sec=0, clip_stride_sec=60,
                            horizons_min=(1,))
    assert sorted(k[1] for k in gt) == list(range(0, 600, 60))


def test_split_filter(tmp_path: Path):
    path = tmp_path / "multi_split.json"
    path.write_text(json.dumps([
        _synthetic_video("TRAIN01", split="train"),
        _synthetic_video("TEST01", split="test"),
    ]))
    gt_test = build_ground_truth(path, split="test", min_prefix_sec=0,
                                 horizons_min=(1,))
    assert {k[0] for k in gt_test} == {"TEST01"}

    gt_all = build_ground_truth(path, split=None, min_prefix_sec=0,
                                horizons_min=(1,))
    assert {k[0] for k in gt_all} == {"TRAIN01", "TEST01"}


def test_unknown_phase_label_is_an_error(tmp_path: Path):
    video = _synthetic_video()
    video["frames"][10]["phase"] = "NotInVocab"
    path = tmp_path / "bad_labels.json"
    path.write_text(json.dumps([video]))
    with pytest.raises(ValueError, match="phase_vocab"):
        build_ground_truth(path, split="test", min_prefix_sec=0)


def test_real_label_schema_loads_if_present():
    """Smoke test against the committed MB140 fold-0 labels, when available."""
    labels = Path(__file__).resolve().parents[1] / "labels" / "mb140_fold0_labels.json"
    if not labels.exists():
        pytest.skip("MB140 labels not present in this checkout")
    gt = build_ground_truth(labels, split="val", clip_stride_sec=300,
                            horizons_min=(1, 5, 10))
    assert gt, "expected at least one val clip"
    for rec in gt.values():
        assert rec.seconds_to_next_transition > 0
        assert rec.clip_end_sec >= 0
        # A finite transition time always comes with a next-phase identity.
        assert (rec.seconds_to_next_transition == float("inf")) == (
            rec.next_phase_id is None)


# ── Metrics ─────────────────────────────────────────────────────────────────

def _rec(video_id="V1", frame=0, gt_sec=120.0, pred_sec=None,
         next_phase=1, pred_phase=None, posterior=None,
         gt_horizon=None, pred_horizon=None) -> ClipRecord:
    return ClipRecord(
        video_id=video_id, clip_end_frame=frame, clip_end_sec=float(frame),
        seconds_to_next_transition=gt_sec, next_phase_id=next_phase,
        future_phase_at_horizon=gt_horizon or {},
        pred_seconds_to_next_transition=pred_sec,
        pred_next_phase_id=pred_phase,
        pred_next_phase_posterior=posterior,
        pred_future_phase_at_horizon=pred_horizon,
    )


def test_mae_transition_time_known_answer():
    # Errors of 60s, 120s, 30s → 1.0, 2.0, 0.5 min → mean 1.1666… min.
    records = [
        _rec(gt_sec=120.0, pred_sec=180.0),
        _rec(gt_sec=300.0, pred_sec=180.0),
        _rec(gt_sec=60.0, pred_sec=90.0),
    ]
    assert mae_transition_time_minutes(records) == pytest.approx(3.5 / 3)


def test_mae_excludes_infinite_and_unpredicted_clips():
    records = [
        _rec(gt_sec=120.0, pred_sec=180.0),          # 1.0 min error
        _rec(gt_sec=float("inf"), pred_sec=999.0),   # excluded: no transition
        _rec(gt_sec=240.0, pred_sec=None),           # excluded: no prediction
    ]
    assert mae_transition_time_minutes(records) == pytest.approx(1.0)

    # All clips excluded → NaN rather than a misleading 0.0.
    only_inf = [_rec(gt_sec=float("inf"), pred_sec=1.0)]
    assert mae_transition_time_minutes(only_inf) != mae_transition_time_minutes(only_inf)


def test_macro_f1_perfect_and_chance():
    perfect = [_rec(next_phase=k % 3, pred_phase=k % 3) for k in range(9)]
    assert macro_f1_next_phase(perfect, n_phases=3) == pytest.approx(1.0)

    # Every prediction wrong → zero F1 in every class.
    all_wrong = [_rec(next_phase=0, pred_phase=1) for _ in range(6)]
    assert macro_f1_next_phase(all_wrong, n_phases=3) == pytest.approx(0.0)


def test_macro_f1_known_intermediate_value():
    # Class 0: 2 TP, 0 FP, 1 FN → P=1.0, R=2/3, F1=0.8
    # Class 1: 1 TP, 1 FP, 0 FN → P=0.5, R=1.0, F1=2/3
    # Class 2: 0 everywhere → F1=0
    records = [
        _rec(next_phase=0, pred_phase=0),
        _rec(next_phase=0, pred_phase=0),
        _rec(next_phase=0, pred_phase=1),
        _rec(next_phase=1, pred_phase=1),
    ]
    expected = (0.8 + 2 / 3 + 0.0) / 3
    assert macro_f1_next_phase(records, n_phases=3) == pytest.approx(expected)


def test_ece_zero_when_confidence_matches_accuracy():
    # Ten clips at confidence 1.0, all correct → perfectly calibrated.
    records = [_rec(next_phase=0, posterior=[1.0, 0.0]) for _ in range(10)]
    assert ece_next_phase(records) == pytest.approx(0.0)


def test_ece_maximal_when_confident_and_wrong():
    # Confidence 0.99 on the wrong class every time → ECE ≈ 0.99.
    records = [_rec(next_phase=1, posterior=[0.99, 0.01]) for _ in range(10)]
    assert ece_next_phase(records) == pytest.approx(0.99, abs=1e-9)


def test_horizon_macro_f1_uses_the_requested_horizon_only():
    records = [
        _rec(gt_horizon={5: 0, 10: 1}, pred_horizon={5: 0, 10: 0}),
        _rec(gt_horizon={5: 1, 10: 1}, pred_horizon={5: 1, 10: 0}),
    ]
    # At h=5 both correct; at h=10 both wrong.
    assert horizon_macro_f1(records, 5, n_phases=2) == pytest.approx(1.0)
    assert horizon_macro_f1(records, 10, n_phases=2) == pytest.approx(0.0)


def test_horizon_macro_f1_skips_none_ground_truth():
    records = [
        _rec(gt_horizon={5: None}, pred_horizon={5: 0}),
        _rec(gt_horizon={5: 0}, pred_horizon={5: 0}),
    ]
    # Only the second clip is scorable, and it is correct.
    assert horizon_macro_f1(records, 5, n_phases=1) == pytest.approx(1.0)


# ── Aggregation + bootstrap ─────────────────────────────────────────────────

def test_video_weighting_differs_from_clip_weighting():
    """A video with many clips must not dominate the video-weighted mean."""
    records = (
        # V1: 100 clips, each 1-minute error.
        [_rec(video_id="V1", gt_sec=60.0, pred_sec=120.0) for _ in range(100)]
        # V2: 1 clip, 10-minute error.
        + [_rec(video_id="V2", gt_sec=60.0, pred_sec=660.0)]
    )
    # Clip-weighted: (100*1 + 10) / 101 ≈ 1.089
    assert mae_transition_time_minutes(records) == pytest.approx(110 / 101)
    # Video-weighted: (1 + 10) / 2 = 5.5
    assert per_video_video_weighted(
        records, mae_transition_time_minutes) == pytest.approx(5.5)


def test_paired_bootstrap_ci_recovers_a_constant_offset():
    """B beats A by exactly 1 minute on every video → CI collapses to −1."""
    a = [_rec(video_id=f"V{i}", gt_sec=60.0, pred_sec=180.0) for i in range(20)]
    b = [_rec(video_id=f"V{i}", gt_sec=60.0, pred_sec=120.0) for i in range(20)]
    out = paired_bootstrap_ci(a, b, mae_transition_time_minutes, n_boot=200)

    assert out["n_paired"] == 20
    assert out["mean_diff_a_minus_b"] == pytest.approx(1.0)
    assert out["ci_low"] == pytest.approx(1.0)
    assert out["ci_high"] == pytest.approx(1.0)
    assert out["n_a_higher"] == 20
    assert out["n_b_higher"] == 0


def test_paired_bootstrap_ci_straddles_zero_for_a_null_effect():
    """Alternating signs with zero mean → CI must contain 0."""
    a, b = [], []
    for i in range(30):
        err_a, err_b = (120.0, 180.0) if i % 2 == 0 else (180.0, 120.0)
        a.append(_rec(video_id=f"V{i}", gt_sec=60.0, pred_sec=err_a))
        b.append(_rec(video_id=f"V{i}", gt_sec=60.0, pred_sec=err_b))
    out = paired_bootstrap_ci(a, b, mae_transition_time_minutes, n_boot=500)

    assert out["mean_diff_a_minus_b"] == pytest.approx(0.0)
    assert out["ci_low"] < 0 < out["ci_high"]


def test_paired_bootstrap_is_deterministic_given_a_seed():
    a = [_rec(video_id=f"V{i}", gt_sec=60.0, pred_sec=60.0 + 10 * i) for i in range(15)]
    b = [_rec(video_id=f"V{i}", gt_sec=60.0, pred_sec=60.0 + 5 * i) for i in range(15)]
    first = paired_bootstrap_ci(a, b, mae_transition_time_minutes, n_boot=200, seed=7)
    second = paired_bootstrap_ci(a, b, mae_transition_time_minutes, n_boot=200, seed=7)
    assert first == second


def test_paired_bootstrap_requires_matched_videos():
    a = [_rec(video_id="V1", gt_sec=60.0, pred_sec=120.0)]
    b = [_rec(video_id="V2", gt_sec=60.0, pred_sec=120.0)]
    with pytest.raises(ValueError, match="matched video set"):
        paired_bootstrap_ci(a, b, mae_transition_time_minutes, n_boot=10)

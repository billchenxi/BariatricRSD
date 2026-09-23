"""Tests for brsd_lib.episode_audit.

The audit exists to decide a go/no-go, so the properties worth pinning are the
ones that would silently flip that decision: episode boundaries, and the
exclusion of frames inside an ongoing episode from the anticipation
denominator. Getting the latter wrong inflates the apparent positive rate and
turns detection into "anticipation".
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brsd_lib.episode_audit import (  # noqa: E402
    audit_records,
    extract_episodes,
    horizon_balance,
    load_records,
    render,
)

REPO = Path(__file__).resolve().parents[1]
FOLD0 = REPO / "labels" / "mb140_fold0_labels.json"


def _op(video_id, flags, step=1.0):
    """Build one operation record; ``flags`` is a per-second deviation mask."""
    return {
        "video_id": video_id,
        "frames": [
            {"timestamp_sec": i * step, "is_deviation": bool(f)}
            for i, f in enumerate(flags)
        ],
    }


# ── episode extraction ──────────────────────────────────────────────────────

def test_contiguous_run_is_one_episode():
    eps = extract_episodes(_op("BBP01", [0, 0, 1, 1, 1, 0, 0]))
    assert len(eps) == 1
    assert (eps[0].onset_s, eps[0].offset_s, eps[0].n_frames) == (2.0, 4.0, 3)
    assert eps[0].duration_s == 2.0


def test_separate_runs_are_separate_episodes():
    eps = extract_episodes(_op("BBP01", [1, 0, 1, 1, 0, 1]))
    assert [(e.onset_s, e.offset_s) for e in eps] == [(0.0, 0.0), (2.0, 3.0), (5.0, 5.0)]


def test_run_open_at_end_of_operation_is_closed():
    eps = extract_episodes(_op("BBP01", [0, 1, 1]))
    assert len(eps) == 1 and eps[0].offset_s == 2.0


def test_no_flags_yields_no_episodes():
    assert extract_episodes(_op("BBP01", [0, 0, 0])) == []


def test_centre_is_taken_from_the_video_id_prefix():
    assert extract_episodes(_op("SBP42", [1]))[0].centre == "SBP"


def test_single_frame_episode_has_zero_duration():
    eps = extract_episodes(_op("BBP01", [0, 1, 0]))
    assert eps[0].duration_s == 0.0 and eps[0].n_frames == 1


# ── anticipation balance ────────────────────────────────────────────────────

def test_frames_inside_an_episode_are_excluded_from_the_denominator():
    """The core correctness property: scoring inside an episode is detection."""
    rec = _op("BBP01", [0] * 10 + [1] * 5 + [0] * 10)   # onset at t=10, offset t=14
    eps = {"BBP01": extract_episodes(rec)}
    b = horizon_balance([rec], horizon_s=5, episodes_by_op=eps)
    assert b.eligible_frames == 20, "the 5 flagged frames must not be eligible"


def test_positive_window_is_the_horizon_before_an_onset():
    rec = _op("BBP01", [0] * 10 + [1] + [0] * 9)        # single onset at t=10
    eps = {"BBP01": extract_episodes(rec)}
    b = horizon_balance([rec], horizon_s=3, episodes_by_op=eps)
    # t=7,8,9 satisfy t < 10 <= t+3; t=10 is excluded as in-episode.
    assert b.positive_frames == 3


def test_onsets_without_a_full_prefix_are_counted_separately():
    rec = _op("BBP01", [0, 1] + [0] * 20)               # onset at t=1
    eps = {"BBP01": extract_episodes(rec)}
    b = horizon_balance([rec], horizon_s=10, episodes_by_op=eps)
    assert b.onsets_total == 1
    assert b.onsets_with_usable_prefix == 0


def test_positive_rate_rises_with_horizon():
    rec = _op("BBP01", [0] * 50 + [1] + [0] * 49)
    eps = {"BBP01": extract_episodes(rec)}
    rates = [horizon_balance([rec], h, eps).positive_rate for h in (5, 10, 20)]
    assert rates == sorted(rates) and rates[0] < rates[-1]


def test_balance_of_an_event_free_operation_is_zero_not_an_error():
    rec = _op("BBP01", [0] * 10)
    b = horizon_balance([rec], 5, {"BBP01": []})
    assert b.positive_frames == 0 and b.eligible_frames == 10
    assert b.positive_rate == 0.0


# ── audit aggregation ───────────────────────────────────────────────────────

def test_audit_flags_operations_with_no_usable_prefix():
    recs = [
        _op("BBP01", [0] * 100 + [1] * 5),   # first onset at t=100, fine
        _op("BBP02", [1] * 5 + [0] * 100),   # first onset at t=0, unusable
    ]
    a = audit_records(recs, horizons_s=[30])
    assert a.operations_with_immediate_onset == ["BBP02"]
    assert a.operations_without_episode == []


def test_audit_records_operations_with_no_episode():
    a = audit_records([_op("BBP01", [0] * 20)], horizons_s=[10])
    assert a.operations_without_episode == ["BBP01"]
    assert a.n_episodes == 0


def test_render_of_an_empty_audit_does_not_crash():
    out = render(audit_records([_op("BBP01", [0] * 5)], horizons_s=[10]), "empty")
    assert "No flagged episodes" in out


def test_load_records_rejects_a_non_list(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"video_id": "BBP01"}))
    with pytest.raises(ValueError, match="not a list"):
        load_records(p)


# ── against the real export ─────────────────────────────────────────────────

@pytest.mark.skipif(not FOLD0.is_file(), reason="MB140 fold-0 export not in this checkout")
def test_real_export_supports_episode_level_anticipation():
    """The go/no-go numbers quoted in plans/STRATEGY.md §V.5."""
    a = audit_records(load_records(FOLD0))
    assert a.n_operations == 140
    assert a.n_episodes == 736
    # Both centres contribute; a single-centre signal would not transfer.
    centres = {e.centre for e in a.episodes}
    assert centres == {"BBP", "SBP"}
    # The case-level endpoint really is near-degenerate, as STRATEGY IV.1 says.
    assert len(a.operations_without_episode) == 2
    # The episode-level one is not.
    by_h = {b.horizon_s: b for b in a.balances}
    assert 0.01 < by_h[60].positive_rate < 0.10
    assert by_h[60].onsets_with_usable_prefix >= 700

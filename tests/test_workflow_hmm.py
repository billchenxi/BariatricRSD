"""Tests for the R3 HMM workflow representation.

Phase 0 kickoff deliverable #5: alternative workflow-representation
prototypes "implemented and validated on MB140 fold-0 against the current
k-means reference."

The important test in this file is
`test_filtered_posterior_ignores_the_future`, which verifies the strict
prefix-only property empirically rather than by inspection: mutating
frames after t must leave the causal representation at t bit-identical.
That is the guarantee the whole causal-evaluation protocol rests on.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper2_infra.workflow_representations.hmm import (  # noqa: E402
    WorkflowHMM,
    filtered_posteriors,
    fit_hmm,
    forward,
    load_phase_sequences,
    posterior_entropy,
    representation_entropy,
    select_n_states,
    smoothed_posteriors,
    total_log_likelihood,
    video_representation,
)

REPO = Path(__file__).resolve().parents[1]


# ── Fixtures ────────────────────────────────────────────────────────────────

def _two_state_model() -> WorkflowHMM:
    """Two sticky states with near-deterministic, disjoint emissions.

    State 0 emits phase 0, state 1 emits phase 1, each with probability
    0.95. Both states persist with probability 0.98. This makes every
    posterior hand-checkable: seeing phase 0 should drive the posterior
    toward state 0.
    """
    return WorkflowHMM(
        start=np.array([0.5, 0.5]),
        trans=np.array([[0.98, 0.02], [0.02, 0.98]]),
        emit=np.array([[0.95, 0.05], [0.05, 0.95]]),
        n_states=2, n_obs=2,
    )


def _sample_sequences(model: WorkflowHMM, n_seq: int, length: int,
                      seed: int = 0) -> list:
    """Draw observation sequences from a known model."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_seq):
        state = rng.choice(model.n_states, p=model.start)
        obs = []
        for _ in range(length):
            obs.append(rng.choice(model.n_obs, p=model.emit[state]))
            state = rng.choice(model.n_states, p=model.trans[state])
        out.append(np.asarray(obs, dtype=np.int64))
    return out


# ── The causality guarantee ─────────────────────────────────────────────────

def test_filtered_posterior_ignores_the_future():
    """Changing frames after t must not change the causal representation at t.

    This is the strict prefix-only property, tested by mutation rather
    than by reading the code.
    """
    model = _two_state_model()
    obs = np.array([0, 0, 0, 1, 1, 0, 1, 0, 0, 1], dtype=np.int64)
    baseline = filtered_posteriors(model, obs)

    for cut in (3, 5, 8):
        mutated = obs.copy()
        mutated[cut:] = 1 - mutated[cut:]  # flip every later observation
        after = filtered_posteriors(model, mutated)
        np.testing.assert_array_equal(
            baseline[:cut], after[:cut],
            err_msg=f"filtered posterior before t={cut} changed when the "
                    f"future was mutated — the representation leaks",
        )


def test_smoothed_posterior_does_use_the_future():
    """The oracle representation must depend on the future — else it is
    not an oracle and the oracle-vs-causal gap is meaningless."""
    model = _two_state_model()
    obs = np.array([0, 0, 0, 1, 1, 0, 1, 0, 0, 1], dtype=np.int64)
    baseline = smoothed_posteriors(model, obs)
    mutated = obs.copy()
    mutated[5:] = 1 - mutated[5:]
    after = smoothed_posteriors(model, mutated)
    assert not np.allclose(baseline[:5], after[:5])


def test_video_descriptors_average_over_the_video():
    """Both descriptors summarize the whole video, so a half-and-half
    video sits near 0.5 in each — not pinned to the final phase."""
    model = _two_state_model()
    obs = np.array([0] * 20 + [1] * 20, dtype=np.int64)
    causal = video_representation(model, obs, "causal")
    oracle = video_representation(model, obs, "oracle")
    assert causal.shape == oracle.shape == (2,)
    assert causal[1] == pytest.approx(0.5, abs=0.15)
    assert oracle[1] == pytest.approx(0.5, abs=0.1)


def test_video_descriptor_does_not_collapse_on_stereotyped_videos():
    """The regression that motivated averaging.

    Three videos share a terminal phase but differ earlier. Using the
    last frame's posterior would give all three the same descriptor and
    measure zero variability; averaging must keep them distinct.
    """
    model = _two_state_model()
    videos = [
        np.array([0] * 40 + [1] * 10, dtype=np.int64),
        np.array([0] * 25 + [1] * 25, dtype=np.int64),
        np.array([0] * 10 + [1] * 40, dtype=np.int64),
    ]
    descriptors = [video_representation(model, v, "causal") for v in videos]
    # All three end in phase 1, so last-frame posteriors would be identical.
    last_frames = [video_representation(model, v, "causal", at_frame=len(v) - 1)
                   for v in videos]
    assert np.allclose(last_frames[0], last_frames[1], atol=1e-6)
    assert np.allclose(last_frames[1], last_frames[2], atol=1e-6)
    # The averaged descriptors must still separate them.
    assert descriptors[0][0] > descriptors[1][0] > descriptors[2][0]


def test_at_frame_returns_the_conditioning_signal_at_that_moment():
    model = _two_state_model()
    obs = np.array([0] * 30 + [1] * 30, dtype=np.int64)
    early = video_representation(model, obs, "causal", at_frame=29)
    late = video_representation(model, obs, "causal", at_frame=59)
    assert early[0] > 0.95
    assert late[1] > 0.95


def test_video_representation_rejects_bad_mode_and_index():
    model = _two_state_model()
    obs = np.array([0, 1, 0], dtype=np.int64)
    with pytest.raises(ValueError, match="must be 'causal' or 'oracle'"):
        video_representation(model, obs, "smoothed")
    with pytest.raises(IndexError):
        video_representation(model, obs, "causal", at_frame=99)
    with pytest.raises(ValueError, match="only meaningful for mode='causal'"):
        video_representation(model, obs, "oracle", at_frame=1)


# ── Posterior correctness ───────────────────────────────────────────────────

def test_posteriors_are_normalized():
    model = _two_state_model()
    obs = np.array([0, 1, 0, 0, 1, 1, 0], dtype=np.int64)
    for post in (filtered_posteriors(model, obs), smoothed_posteriors(model, obs)):
        np.testing.assert_allclose(post.sum(axis=1), 1.0, atol=1e-10)
        assert (post >= 0).all()


def test_first_filtered_posterior_matches_bayes_rule_by_hand():
    """alpha[0] ∝ start * emit[:, o_0], computed by hand."""
    model = _two_state_model()
    obs = np.array([0, 1], dtype=np.int64)
    alpha = filtered_posteriors(model, obs)
    # start = [0.5, 0.5], emit[:,0] = [0.95, 0.05] → [0.475, 0.025] → /0.5
    np.testing.assert_allclose(alpha[0], [0.95, 0.05], atol=1e-12)


def test_posterior_tracks_a_clean_state_switch():
    """Sustained phase-1 observations must drive the posterior to state 1."""
    model = _two_state_model()
    obs = np.array([0] * 30 + [1] * 30, dtype=np.int64)
    alpha = filtered_posteriors(model, obs)
    assert alpha[29, 0] > 0.95, "should be confident in state 0 before the switch"
    assert alpha[59, 1] > 0.95, "should be confident in state 1 after the switch"


def test_forward_is_numerically_stable_on_long_sequences():
    """6,000 frames is a realistic surgical video; unscaled products underflow."""
    model = _two_state_model()
    rng = np.random.default_rng(0)
    obs = rng.integers(0, 2, size=6000)
    alpha, _, loglik = forward(model, obs)
    assert np.isfinite(alpha).all()
    np.testing.assert_allclose(alpha.sum(axis=1), 1.0, atol=1e-9)
    assert np.isfinite(loglik) and loglik < 0


# ── Baum-Welch ──────────────────────────────────────────────────────────────

def test_fit_recovers_a_known_two_state_model():
    """EM on data sampled from a known model should recover its structure."""
    truth = _two_state_model()
    seqs = _sample_sequences(truth, n_seq=30, length=400, seed=1)
    fitted = fit_hmm(seqs, n_states=2, n_obs=2, seed=7, n_iter=100)

    # States are only identifiable up to a permutation.
    emit = fitted.emit
    if emit[0, 0] < emit[1, 0]:
        emit = emit[::-1]
    np.testing.assert_allclose(emit, truth.emit, atol=0.05)
    # Both states are sticky.
    assert fitted.trans.diagonal().min() > 0.9


def test_fit_log_likelihood_increases_monotonically():
    """EM must never reduce the likelihood; catches a broken M-step."""
    truth = _two_state_model()
    seqs = _sample_sequences(truth, n_seq=10, length=200, seed=2)
    lls = [fit_hmm(seqs, n_states=2, n_obs=2, seed=3, n_iter=n).log_likelihood
           for n in range(1, 8)]
    for earlier, later in zip(lls, lls[1:]):
        assert later >= earlier - 1e-6, f"log-likelihood fell: {earlier} → {later}"


def test_fit_converges_and_reports_it():
    truth = _two_state_model()
    seqs = _sample_sequences(truth, n_seq=10, length=300, seed=4)
    fitted = fit_hmm(seqs, n_states=2, n_obs=2, seed=5, n_iter=200, tol=1e-5)
    assert fitted.converged
    assert fitted.n_iter_run < 200


def test_fit_is_deterministic_for_a_given_seed():
    seqs = _sample_sequences(_two_state_model(), n_seq=8, length=150, seed=6)
    a = fit_hmm(seqs, n_states=3, n_obs=2, seed=11, n_iter=20)
    b = fit_hmm(seqs, n_states=3, n_obs=2, seed=11, n_iter=20)
    np.testing.assert_array_equal(a.emit, b.emit)
    np.testing.assert_array_equal(a.trans, b.trans)


def test_smoothing_keeps_unseen_phases_finite():
    """A phase absent from training must not produce NaN at validation.

    MB140's vocabulary includes rare labels ('Out of body', 'Unknown')
    that appear in only a few videos, so this is the realistic case, not
    a corner case.
    """
    train = [np.array([0, 0, 1, 1, 0], dtype=np.int64) for _ in range(5)]
    model = fit_hmm(train, n_states=2, n_obs=4, seed=0, n_iter=20)
    assert (model.emit > 0).all(), "smoothing should keep every emission positive"

    unseen = [np.array([2, 3, 2], dtype=np.int64)]  # phases never trained on
    ll = total_log_likelihood(model, unseen)
    assert np.isfinite(ll)
    assert np.isfinite(filtered_posteriors(model, unseen[0])).all()


def test_restarts_never_score_worse_than_a_single_init():
    """Best-of-N restarts must be >= the first init's likelihood."""
    seqs = _sample_sequences(_two_state_model(), n_seq=10, length=200, seed=20)
    single = fit_hmm(seqs, n_states=4, n_obs=2, seed=21, n_iter=30, n_restarts=1)
    multi = fit_hmm(seqs, n_states=4, n_obs=2, seed=21, n_iter=30, n_restarts=4)
    assert multi.log_likelihood >= single.log_likelihood


def test_restarts_are_deterministic():
    seqs = _sample_sequences(_two_state_model(), n_seq=6, length=150, seed=22)
    a = fit_hmm(seqs, n_states=3, n_obs=2, seed=23, n_iter=20, n_restarts=3)
    b = fit_hmm(seqs, n_states=3, n_obs=2, seed=23, n_iter=20, n_restarts=3)
    np.testing.assert_array_equal(a.emit, b.emit)


def test_fit_rejects_empty_input():
    with pytest.raises(ValueError, match="no sequences"):
        fit_hmm([], n_states=2, n_obs=3)
    with pytest.raises(ValueError, match="n_states"):
        fit_hmm([np.array([0, 1])], n_states=0, n_obs=2)


def test_free_parameter_count():
    model = WorkflowHMM(start=np.ones(3) / 3, trans=np.ones((3, 3)) / 3,
                        emit=np.ones((3, 5)) / 5, n_states=3, n_obs=5)
    # (3-1) start + 3*(3-1) transition + 3*(5-1) emission = 2 + 6 + 12 = 20
    assert model.n_free_params == 20


def test_model_round_trips_through_json():
    model = fit_hmm(_sample_sequences(_two_state_model(), 5, 100, seed=8),
                    n_states=2, n_obs=2, seed=9, n_iter=10)
    restored = WorkflowHMM.from_dict(json.loads(json.dumps(model.to_dict())))
    np.testing.assert_allclose(restored.emit, model.emit)
    np.testing.assert_allclose(restored.trans, model.trans)
    assert restored.n_free_params == model.n_free_params


# ── Model selection ─────────────────────────────────────────────────────────

def test_select_n_states_prefers_the_true_state_count():
    """BIC should not over-select when the truth has two states."""
    truth = _two_state_model()
    train = _sample_sequences(truth, n_seq=20, length=400, seed=10)
    val = _sample_sequences(truth, n_seq=8, length=400, seed=11)
    result = select_n_states(train, n_obs=2, candidates=(2, 4, 8),
                             val=val, seed=12, n_iter=40)
    assert result["best_by_bic"] == 2
    assert all("val_loglik_per_frame" in r for r in result["sweep"])


# ── Entropy ─────────────────────────────────────────────────────────────────

def test_posterior_entropy_bounds():
    uniform = np.full((10, 4), 0.25)
    assert posterior_entropy(uniform) == pytest.approx(np.log(4))
    onehot = np.zeros((10, 4))
    onehot[:, 2] = 1.0
    assert posterior_entropy(onehot) == pytest.approx(0.0)


def test_representation_entropy_is_maximal_when_states_are_balanced():
    """Videos spread evenly across 4 states → normalized entropy 1.0."""
    reps = []
    for k in range(4):
        vec = np.full(4, 0.1)
        vec[k] = 0.7
        reps.extend([vec] * 5)
    out = representation_entropy(reps)
    assert out["hard_assignment_entropy_normalized"] == pytest.approx(1.0)
    assert out["n_states_used"] == 4
    assert out["n_videos"] == 20


def test_representation_entropy_is_zero_when_all_videos_agree():
    reps = [np.array([0.9, 0.05, 0.05])] * 12
    out = representation_entropy(reps)
    assert out["hard_assignment_entropy"] == pytest.approx(0.0)
    assert out["n_states_used"] == 1


def test_representation_entropy_rejects_ragged_input():
    with pytest.raises(ValueError, match="inconsistent dimensionality"):
        representation_entropy([np.ones(3) / 3, np.ones(4) / 4])
    with pytest.raises(ValueError, match="no representations"):
        representation_entropy([])


# ── Real label JSONs ────────────────────────────────────────────────────────

@pytest.mark.parametrize("labels_name,expected_phases", [
    ("mb140_fold0_labels.json", 14),
    ("cholec80_labels.json", 7),
])
def test_loads_real_label_schema(labels_name, expected_phases):
    path = REPO / "labels" / labels_name
    if not path.exists():
        pytest.skip(f"{labels_name} not present in this checkout")
    ids, seqs, vocab = load_phase_sequences(path, split="train")
    assert ids and len(ids) == len(seqs)
    assert len(vocab) == expected_phases
    for seq in seqs:
        assert seq.min() >= 0 and seq.max() < len(vocab)


def test_fits_on_real_mb140_data():
    """End-to-end on the committed MB140 fold-0 labels."""
    path = REPO / "labels" / "mb140_fold0_labels.json"
    if not path.exists():
        pytest.skip("MB140 labels not present in this checkout")
    _, train, vocab = load_phase_sequences(path, split="train")
    # Subsample to keep the test fast; the CLI uses the full split.
    train = [s[::10] for s in train[:20]]
    model = fit_hmm(train, n_states=4, n_obs=len(vocab), seed=42, n_iter=15)
    assert np.isfinite(model.log_likelihood)
    np.testing.assert_allclose(model.trans.sum(axis=1), 1.0, atol=1e-10)
    np.testing.assert_allclose(model.emit.sum(axis=1), 1.0, atol=1e-10)

    reps = [video_representation(model, s, "causal") for s in train]
    ent = representation_entropy(reps)
    assert 0.0 <= ent["hard_assignment_entropy_normalized"] <= 1.0

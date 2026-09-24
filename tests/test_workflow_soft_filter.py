"""Deployment invariants for the predicted-phase workflow interface."""
import numpy as np
import pytest

from paper2_infra.workflow_representations.hmm import (
    WorkflowHMM, filtered_phase_probabilities, filtered_posteriors,
)


@pytest.fixture
def model():
    return WorkflowHMM(np.array([0.6, 0.4]),
                       np.array([[0.9, 0.1], [0.2, 0.8]]),
                       np.array([[0.8, 0.2], [0.1, 0.9]]), 2, 2)


def test_one_hot_matches_hard_filter(model):
    labels = np.array([0, 0, 1, 1, 0])
    np.testing.assert_allclose(
        filtered_phase_probabilities(model, np.eye(2)[labels]),
        filtered_posteriors(model, labels))


def test_streaming_and_future_invariance(model):
    probabilities = np.array([[0.7, 0.3], [0.4, 0.6], [0.1, 0.9], [0.8, 0.2]])
    full = filtered_phase_probabilities(model, probabilities)
    first = filtered_phase_probabilities(model, probabilities[:2])
    last = filtered_phase_probabilities(model, probabilities[2:], first[-1])
    np.testing.assert_array_equal(full, np.concatenate([first, last]))
    probabilities[2:] = probabilities[2:, ::-1]
    np.testing.assert_array_equal(
        full[:2], filtered_phase_probabilities(model, probabilities)[:2])
    np.testing.assert_allclose(full.sum(axis=1), 1)


def test_uniform_evidence_preserves_predicted_prior(model):
    filtered = filtered_phase_probabilities(model, np.full((2, 2), 0.5))
    np.testing.assert_allclose(filtered[0], model.start)
    np.testing.assert_allclose(filtered[1], model.start @ model.trans)


@pytest.mark.parametrize("values", [
    [[-0.1, 1.1]], [[0.2, 0.2]], [[float('nan'), 0]],
    [[float('inf'), 0]], [0.5, 0.5], [[1, 0, 0]],
])
def test_invalid_predictions_rejected(model, values):
    with pytest.raises(ValueError):
        filtered_phase_probabilities(model, values)


def test_empty_and_invalid_stream_state(model):
    assert filtered_phase_probabilities(model, np.empty((0, 2))).shape == (0, 2)
    with pytest.raises(ValueError):
        filtered_phase_probabilities(model, [[0.5, 0.5]], np.array([0, 0]))


def test_impossible_evidence_rejected(model):
    model.emit[:] = [1, 0]
    with pytest.raises(ValueError, match="zero or invalid evidence"):
        filtered_phase_probabilities(model, [[0, 1]])

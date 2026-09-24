"""
brsd_lib — BariatricRSD library (NeurIPS 2026 submission)

A clean, self-contained library written from scratch for this project.
Nothing here is lifted from the 2019 project code or from the vendor-provided
bariatric_rsd package. All algorithmic concepts that were inspired by prior
work are reimplemented fresh with clear attribution in the module docstring
where relevant.

Modules:
    labels          — RSD percentage conversion + labels.json helpers
    evaluate        — Test-set inference + per-video MAE aggregation
    overfit_filter  — controlled per-video overfit residual filtering
    ensemble        — multi-seed ensemble + TTA + isotonic post-processing
    (more to come: phase_order, metrics, ...)
"""

__version__ = "0.4.0"

from .labels import (
    seconds_to_rsd_fraction,
    frame_time_to_rsd_fraction,
    annotate_video_with_rsd_fractions,
    normalize_labels_json,
    audit_labels,
)

__all__ = [
    # labels
    "seconds_to_rsd_fraction",
    "frame_time_to_rsd_fraction",
    "annotate_video_with_rsd_fractions",
    "normalize_labels_json",
    "audit_labels",
    # evaluate
    "run_test_eval",
    "per_video_mae_minutes",
    "summarize_mae",
    # overfit_filter
    "standardize_residual_table",
    "select_by_overfit_residuals",
    "load_labels_json",
    "estimate_sequence_samples",
    "summarize_manifest_after_selection",
    "assert_all_train_videos_have_selection",
    "write_filtered_manifest",
    # ensemble
    "run_ensemble_eval",
]

_OVERFIT_EXPORTS = {
    "standardize_residual_table",
    "select_by_overfit_residuals",
    "load_labels_json",
    "estimate_sequence_samples",
    "summarize_manifest_after_selection",
    "assert_all_train_videos_have_selection",
    "write_filtered_manifest",
}

_EVALUATE_EXPORTS = {
    "run_test_eval",
    "per_video_mae_minutes",
    "summarize_mae",
}

_ENSEMBLE_EXPORTS = {
    "run_ensemble_eval",
}

_CAUSAL_EXPORTS = {
    "ClusteringArtifacts",
    "CausalClusterAssigner",
    "phase_head_prefix_sequence",
    "soft_embedding",
    "evaluate_causal_rsd",
    "evaluate_causal_rsd_pixel_only",
    "patch_model_for_soft_cluster",
}

_SMOOTHING_EXPORTS = {
    "AdamSmootherConfig",
    "adam_smooth",
    "apply_per_video",
    "per_video_mae_minutes",
    "sweep_configs",
}

_STATS_EXPORTS = {
    "bootstrap_ci",
    "paired_wilcoxon",
    "threeway_summary",
}


def __getattr__(name):
    if name in _OVERFIT_EXPORTS:
        from . import overfit_filter

        return getattr(overfit_filter, name)

    if name in _EVALUATE_EXPORTS:
        try:
            from . import evaluate
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "brsd_lib.evaluate is unavailable because an optional dependency is missing."
            ) from exc
        return getattr(evaluate, name)

    if name in _ENSEMBLE_EXPORTS:
        try:
            from . import ensemble
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "brsd_lib.ensemble is unavailable because an optional dependency is missing."
            ) from exc
        return getattr(ensemble, name)

    if name in _CAUSAL_EXPORTS:
        try:
            from . import causal_cluster
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "brsd_lib.causal_cluster is unavailable because an optional dependency is missing."
            ) from exc
        return getattr(causal_cluster, name)

    if name in _SMOOTHING_EXPORTS:
        from . import smoothing
        return getattr(smoothing, name)

    if name in _STATS_EXPORTS:
        from . import stats
        return getattr(stats, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

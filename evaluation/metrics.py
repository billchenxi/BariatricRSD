"""
Evaluation Metrics
==================
Metrics for evaluating RSD prediction, deviation detection, and
phase recognition performance.

Replaces the manual evaluation scripts from the 2019 codebase with
a comprehensive metrics module using scikit-learn.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.stats import pearsonr, spearmanr
from scipy import signal
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
    confusion_matrix,
    classification_report,
)


def compute_rsd_metrics(
    predictions: np.ndarray,
    targets: np.ndarray,
    total_duration_sec: Optional[float] = None,
) -> Dict[str, float]:
    """
    Compute RSD prediction metrics.

    Args:
        predictions: Predicted normalized RSD values.
        targets: Ground truth normalized RSD values.
        total_duration_sec: If provided, compute MAE in seconds.

    Returns:
        Dictionary of metrics: MAE, RMSE, Pearson r, Spearman rho.
    """
    # Normalized metrics
    errors = predictions - targets
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))

    # Correlation
    if len(predictions) > 2:
        pearson_r, pearson_p = pearsonr(predictions, targets)
        spearman_r, spearman_p = spearmanr(predictions, targets)
    else:
        pearson_r = pearson_p = spearman_r = spearman_p = 0.0

    metrics = {
        "mae_normalized": float(mae),
        "rmse_normalized": float(rmse),
        "pearson_r": float(pearson_r),
        "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r),
    }

    # Convert to seconds/minutes if total duration is known
    if total_duration_sec is not None:
        mae_sec = mae * total_duration_sec
        metrics["mae_seconds"] = float(mae_sec)
        metrics["mae_minutes"] = float(mae_sec / 60.0)

    return metrics


def compute_deviation_metrics(
    predictions: np.ndarray,
    targets: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, float]:
    """
    Compute deviation detection metrics.

    Args:
        predictions: Predicted deviation probabilities (after sigmoid).
        targets: Ground truth binary deviation labels.
        threshold: Classification threshold.

    Returns:
        Dictionary of metrics: F1, precision, recall, accuracy.
    """
    binary_preds = (predictions >= threshold).astype(int)

    metrics = {
        "f1": float(f1_score(targets, binary_preds, zero_division=0)),
        "precision": float(precision_score(targets, binary_preds, zero_division=0)),
        "recall": float(recall_score(targets, binary_preds, zero_division=0)),
        "accuracy": float(accuracy_score(targets, binary_preds)),
    }

    return metrics


def compute_phase_metrics(
    predictions: np.ndarray,
    targets: np.ndarray,
    phase_names: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Compute surgical phase recognition metrics.

    Args:
        predictions: Predicted phase class indices.
        targets: Ground truth phase class indices.
        phase_names: Optional list of phase names for per-class reporting.

    Returns:
        Dictionary of metrics: accuracy, macro F1, per-class F1.
    """
    metrics = {
        "accuracy": float(accuracy_score(targets, predictions)),
        "f1_macro": float(
            f1_score(targets, predictions, average="macro", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(targets, predictions, average="weighted", zero_division=0)
        ),
    }

    # Per-class F1
    per_class_f1 = f1_score(
        targets, predictions, average=None, zero_division=0
    )
    if phase_names is not None:
        for name, f1 in zip(phase_names, per_class_f1):
            metrics[f"f1_{name}"] = float(f1)
    else:
        for i, f1 in enumerate(per_class_f1):
            metrics[f"f1_class_{i}"] = float(f1)

    return metrics


def detect_deviation_segments(
    deviation_scores: np.ndarray,
    method: str = "iqr",
    smoothing_window: int = 15,
    min_segment_length: int = 30,
) -> List[Tuple[int, int]]:
    """
    Detect deviation segments from continuous deviation scores.

    This replaces the post-hoc LOWESS + hysteresis thresholding from
    the 2019 codebase with a cleaner statistical approach, while still
    being available as a post-processing step for comparison/evaluation.

    Args:
        deviation_scores: Per-frame deviation scores (e.g., residuals
                         between predicted and expected RSD).
        method: Detection method - "iqr" (IQR-based), "std" (standard
                deviation-based), or "hysteresis" (combined).
        smoothing_window: Median filter window for smoothing.
        min_segment_length: Minimum number of frames for a valid segment.

    Returns:
        List of (start_frame, end_frame) tuples for detected deviations.
    """
    if method == "iqr":
        return _detect_iqr(deviation_scores, smoothing_window, min_segment_length)
    elif method == "std":
        return _detect_std(deviation_scores, smoothing_window, min_segment_length)
    elif method == "hysteresis":
        return _detect_hysteresis(
            deviation_scores, smoothing_window, min_segment_length
        )
    else:
        raise ValueError(f"Unknown method: {method}. Use 'iqr', 'std', or 'hysteresis'.")


def _detect_iqr(
    scores: np.ndarray,
    smoothing_window: int,
    min_length: int,
) -> List[Tuple[int, int]]:
    """IQR-based deviation detection."""
    q1, q3 = np.quantile(scores, [0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return []

    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr

    # Compute deviation magnitude
    magnitude = np.abs(
        np.array(
            [
                min((s - lower_limit) / iqr, 0) + max((s - upper_limit) / iqr, 0)
                for s in scores
            ]
        )
    )

    # Smooth with median filter
    smoothed = signal.medfilt(magnitude, max(3, smoothing_window | 1))

    return _extract_segments(smoothed > 0, min_length)


def _detect_std(
    scores: np.ndarray,
    smoothing_window: int,
    min_length: int,
) -> List[Tuple[int, int]]:
    """Standard deviation-based deviation detection."""
    std = np.std(scores)
    if std == 0:
        return []

    limits = [-std, std]
    magnitude = np.abs(
        np.array(
            [min((s - limits[0]), 0) + max((s - limits[1]), 0) for s in scores]
        )
    )

    smoothed = signal.medfilt(magnitude, max(3, smoothing_window | 1))

    return _extract_segments(smoothed > 0, min_length)


def _detect_hysteresis(
    scores: np.ndarray,
    smoothing_window: int,
    min_length: int,
) -> List[Tuple[int, int]]:
    """
    Hysteresis-based deviation detection.
    Uses SD as the lower threshold and IQR as the upper threshold.
    """
    std_segments = _detect_std(scores, smoothing_window, 1)
    iqr_segments = _detect_iqr(scores, smoothing_window, 1)

    # Hysteresis: keep IQR segments that overlap with SD segments
    result = []
    for iqr_s, iqr_e in iqr_segments:
        for std_s, std_e in std_segments:
            if iqr_s >= std_s and iqr_s <= std_e:
                segment_len = std_e - iqr_s
                if segment_len >= min_length:
                    result.append((iqr_s, std_e))
                break

    return result


def _extract_segments(
    binary_mask: np.ndarray,
    min_length: int,
) -> List[Tuple[int, int]]:
    """Extract contiguous segments from a binary mask."""
    changes = np.diff(binary_mask.astype(int))
    starts = np.where(changes == 1)[0] + 1
    ends = np.where(changes == -1)[0] + 1

    # Handle edge cases
    if binary_mask[0]:
        starts = np.insert(starts, 0, 0)
    if binary_mask[-1]:
        ends = np.append(ends, len(binary_mask))

    segments = []
    for s, e in zip(starts, ends):
        if e - s >= min_length:
            segments.append((int(s), int(e)))

    return segments


def evaluate_model(
    model,
    dataloader,
    device: str = "cuda",
    phase_names: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Full model evaluation on a dataset.

    Args:
        model: Trained BariatricRSD model.
        dataloader: Evaluation DataLoader.
        device: Device to run inference on.
        phase_names: Optional phase names for per-class reporting.

    Returns:
        Combined metrics dictionary.
    """
    import torch

    model.eval()

    all_rsd_pred = []
    all_rsd_target = []
    all_dev_pred = []
    all_dev_target = []
    all_phase_pred = []
    all_phase_target = []

    with torch.no_grad():
        for batch in dataloader:
            clips = batch["clip"].to(device)
            cluster_ids = batch["cluster_id"].to(device)

            outputs = model(clips, cluster_ids)

            # RSD
            rsd_pred = outputs["rsd"].squeeze(-1).cpu().numpy()
            rsd_target = batch["rsd"].numpy()
            all_rsd_pred.append(rsd_pred.flatten())
            all_rsd_target.append(rsd_target.flatten())

            # Deviation
            dev_pred = torch.sigmoid(outputs["deviation"]).squeeze(-1).cpu().numpy()
            dev_target = batch["deviation"].numpy()
            all_dev_pred.append(dev_pred.flatten())
            all_dev_target.append(dev_target.flatten())

            # Phase
            phase_pred = outputs["phase"].argmax(dim=-1).cpu().numpy()
            phase_target = batch["phase"].numpy()
            all_phase_pred.append(phase_pred.flatten())
            all_phase_target.append(phase_target.flatten())

    # Concatenate all predictions
    all_rsd_pred = np.concatenate(all_rsd_pred)
    all_rsd_target = np.concatenate(all_rsd_target)
    all_dev_pred = np.concatenate(all_dev_pred)
    all_dev_target = np.concatenate(all_dev_target)
    all_phase_pred = np.concatenate(all_phase_pred)
    all_phase_target = np.concatenate(all_phase_target)

    # Compute all metrics
    rsd_metrics = compute_rsd_metrics(all_rsd_pred, all_rsd_target)
    dev_metrics = compute_deviation_metrics(all_dev_pred, all_dev_target)
    phase_metrics = compute_phase_metrics(
        all_phase_pred, all_phase_target, phase_names
    )

    # Combine with prefixes
    metrics = {}
    for k, v in rsd_metrics.items():
        metrics[f"rsd/{k}"] = v
    for k, v in dev_metrics.items():
        metrics[f"deviation/{k}"] = v
    for k, v in phase_metrics.items():
        metrics[f"phase/{k}"] = v

    return metrics

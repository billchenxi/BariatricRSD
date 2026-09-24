"""
brsd_lib.overfit_filter
=======================

Controlled overfitting data filtering utilities for frame-level RSD labels.

This module implements a clean-room version of the frame filtering idea used in
the 2019 BariatricRSD pilot work: overfit a lightweight model on each training
video independently, compute an absolute residual for every frame on that same
video, and retain only frames whose residual is small relative to that video's
own residual scale.

The historical rule can be written as:

    keep(frame_i in video_v) = abs_residual_i < k * std(abs_residual_v)

with the original pilot often using ``k = 0.385``.

The implementation here is written from scratch for the current repo. It does
not copy code from the 2019 project; it only re-expresses the same algorithmic
idea in a small, reusable module with tests and manifest helpers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

PathLike = Union[str, Path]

_EMPTY_STATS_COLUMNS = [
    "video_id",
    "n_frames",
    "n_kept",
    "kept_frac",
    "residual_mean",
    "residual_std",
    "threshold",
    "reason",
]


def standardize_residual_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize common residual CSV schemas into a standard layout.

    Expected output columns:
      ``video_id``, ``frame_path``, ``abs_residual``

    Optional source columns:
      ``prediction`` and ``target`` (or aliases) to derive ``abs_residual``
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    df = df.copy()
    rename_map = {}
    aliases = {
        "video_name": "video_id",
        "vid": "video_id",
        "img_path": "frame_path",
        "frame_name": "frame_path",
        "actual": "target",
        "label": "target",
        "rsd_normalized": "target",
        "pred": "prediction",
    }
    for old_name, new_name in aliases.items():
        if old_name in df.columns and new_name not in df.columns:
            rename_map[old_name] = new_name
    if rename_map:
        df = df.rename(columns=rename_map)

    required_base = {"video_id", "frame_path"}
    missing = required_base - set(df.columns)
    if missing:
        raise ValueError(
            f"Residual table must include {sorted(required_base)}; missing {sorted(missing)}"
        )

    if "abs_residual" not in df.columns:
        if {"prediction", "target"} <= set(df.columns):
            df["abs_residual"] = (
                df["prediction"].astype(float) - df["target"].astype(float)
            ).abs()
        else:
            raise ValueError("Need abs_residual or both prediction and target columns.")

    df["video_id"] = df["video_id"].astype(str)
    df["frame_path"] = df["frame_path"].astype(str)
    df["abs_residual"] = df["abs_residual"].astype(float)
    return df


def select_by_overfit_residuals(
    residual_df: pd.DataFrame,
    k: float = 0.385,
    video_col: str = "video_id",
    frame_col: str = "frame_path",
    residual_col: str = "abs_residual",
    min_keep_frac: Optional[float] = None,
    fallback_quantile: Optional[float] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Select high-confidence frames from per-video overfit residuals.

    Parameters
    ----------
    residual_df:
        DataFrame with at least ``video_id``, ``frame_path``, and ``abs_residual``.
    k:
        Threshold multiplier. Historical value: ``0.385``.
    min_keep_frac:
        Optional guardrail. If a video keeps less than this fraction, relax the
        selection using ``fallback_quantile``.
    fallback_quantile:
        Optional quantile threshold, used only when ``min_keep_frac`` is violated.

    Returns
    -------
    selected_df, stats_df
        ``selected_df`` contains the retained rows plus selection metadata.
        ``stats_df`` has one summary row per video.
    """
    if k <= 0:
        raise ValueError(f"k must be > 0, got {k}")
    if min_keep_frac is not None and not 0.0 <= min_keep_frac <= 1.0:
        raise ValueError(
            f"min_keep_frac must be in [0, 1], got {min_keep_frac}"
        )
    if fallback_quantile is not None and not 0.0 <= fallback_quantile <= 1.0:
        raise ValueError(
            f"fallback_quantile must be in [0, 1], got {fallback_quantile}"
        )

    required = {video_col, frame_col, residual_col}
    missing = required - set(residual_df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    selected_parts: List[pd.DataFrame] = []
    stat_rows: List[Dict[str, Any]] = []

    for vid, group in residual_df.groupby(video_col, sort=False):
        group = group.copy()
        resid = group[residual_col].astype(float).to_numpy()
        scale = float(np.std(resid, ddof=0))
        threshold = k * scale

        if not np.isfinite(threshold) or threshold <= 0.0:
            keep = np.ones(len(group), dtype=bool)
            reason = "degenerate_scale_keep_all"
        else:
            keep = resid < threshold
            reason = "std_threshold"

        kept_frac = float(keep.mean()) if len(keep) else 0.0
        if min_keep_frac is not None and kept_frac < min_keep_frac:
            if fallback_quantile is None:
                raise ValueError(
                    f"{vid}: kept {kept_frac:.3f}, below min_keep_frac={min_keep_frac}"
                )
            threshold = float(np.quantile(resid, fallback_quantile))
            keep = resid <= threshold
            reason = f"fallback_quantile_{fallback_quantile}"
            kept_frac = float(keep.mean()) if len(keep) else 0.0

        kept = group.loc[keep].copy()
        kept["selection_threshold"] = float(threshold)
        kept["selection_k"] = float(k)
        kept["selection_reason"] = reason
        selected_parts.append(kept)

        stat_rows.append(
            {
                "video_id": str(vid),
                "n_frames": int(len(group)),
                "n_kept": int(keep.sum()),
                "kept_frac": kept_frac,
                "residual_mean": float(np.mean(resid)) if len(resid) else np.nan,
                "residual_std": scale,
                "threshold": float(threshold),
                "reason": reason,
            }
        )

    if selected_parts:
        selected_df = pd.concat(selected_parts, ignore_index=True)
    else:
        selected_df = residual_df.iloc[0:0].copy()
        selected_df["selection_threshold"] = pd.Series(dtype=float)
        selected_df["selection_k"] = pd.Series(dtype=float)
        selected_df["selection_reason"] = pd.Series(dtype=str)

    stats_df = pd.DataFrame(stat_rows, columns=_EMPTY_STATS_COLUMNS)
    return selected_df, stats_df


def load_labels_json(input_path: PathLike) -> List[Dict[str, Any]]:
    """Load a labels-style manifest whose top level is a list of videos."""
    path = Path(input_path)
    with path.open() as handle:
        videos = json.load(handle)
    if not isinstance(videos, list):
        raise ValueError(
            f"{path}: expected a top-level list of videos, got {type(videos).__name__}"
        )
    return videos


def estimate_sequence_samples(n_frames: int, sequence_len: int = 8, frame_stride: int = 5) -> int:
    """
    Estimate how many temporal windows remain after frame filtering.

    This mirrors the quick sanity check used in the notebook so aggressive frame
    dropping can be caught before a manifest is written.
    """
    if sequence_len <= 0:
        raise ValueError(f"sequence_len must be > 0, got {sequence_len}")
    if frame_stride <= 0:
        raise ValueError(f"frame_stride must be > 0, got {frame_stride}")
    n_frames = int(n_frames)
    return max(0, len(range(0, n_frames - sequence_len * frame_stride, frame_stride)))


def assert_all_train_videos_have_selection(
    videos: Iterable[Mapping[str, Any]],
    selected_df: pd.DataFrame,
    train_split: str = "train",
    video_key: str = "video_id",
    split_key: str = "split",
) -> bool:
    """Fail fast if any training video is missing from the selected frame table."""
    train_ids = {
        str(video[video_key])
        for video in videos
        if video.get(split_key, train_split) == train_split
    }
    selected_ids = set(selected_df["video_id"].astype(str))
    missing = sorted(train_ids - selected_ids)
    if missing:
        preview = ", ".join(missing[:10])
        raise ValueError(
            f"Selection is missing {len(missing)} training videos. First missing: {preview}"
        )
    return True


def summarize_manifest_after_selection(
    videos: Sequence[Mapping[str, Any]],
    selected_df: pd.DataFrame,
    sequence_len: int = 8,
    frame_stride: int = 5,
    train_split: str = "train",
    video_key: str = "video_id",
    split_key: str = "split",
    frame_key: str = "frame_path",
) -> pd.DataFrame:
    """Summarize how many frames and temporal windows survive the selection."""
    selected_keys = set(
        zip(selected_df["video_id"].astype(str), selected_df["frame_path"].astype(str))
    )

    rows = []
    for video in videos:
        vid = str(video[video_key])
        split = video.get(split_key, train_split)
        frames = video.get("frames", []) or []
        old_n = len(frames)

        if split == train_split:
            new_n = sum((vid, str(frame.get(frame_key))) in selected_keys for frame in frames)
        else:
            new_n = old_n

        rows.append(
            {
                "video_id": vid,
                "split": split,
                "old_frames": old_n,
                "new_frames": new_n,
                "kept_frac": (new_n / old_n) if old_n else np.nan,
                "old_samples_est": estimate_sequence_samples(
                    old_n, sequence_len=sequence_len, frame_stride=frame_stride
                ),
                "new_samples_est": estimate_sequence_samples(
                    new_n, sequence_len=sequence_len, frame_stride=frame_stride
                ),
            }
        )
    return pd.DataFrame(rows)


def write_filtered_manifest(
    videos: Sequence[Mapping[str, Any]],
    selected_df: pd.DataFrame,
    output_path: PathLike,
    k: float,
    notes: str = "controlled_overfit_data_selection",
    train_split: str = "train",
    video_key: str = "video_id",
    split_key: str = "split",
    frame_key: str = "frame_path",
) -> Path:
    """
    Write a new labels manifest where only training frames are filtered.

    Validation and test videos are copied through unchanged so the selector never
    affects held-out evaluation content.
    """
    assert_all_train_videos_have_selection(
        videos,
        selected_df,
        train_split=train_split,
        video_key=video_key,
        split_key=split_key,
    )
    selected_keys = set(
        zip(selected_df["video_id"].astype(str), selected_df["frame_path"].astype(str))
    )

    output: List[MutableMapping[str, Any]] = []
    for video in videos:
        new_video: MutableMapping[str, Any] = {
            key: value for key, value in video.items() if key != "frames"
        }
        vid = str(video[video_key])
        split = video.get(split_key, train_split)
        frames = list(video.get("frames", []) or [])

        if split == train_split:
            kept_frames = [
                frame for frame in frames if (vid, str(frame.get(frame_key))) in selected_keys
            ]
            new_video["frames"] = kept_frames
            new_video["selection_method"] = {
                "name": "controlled_overfit_residual_filter",
                "k": float(k),
                "input_split": train_split,
                "old_frame_count": len(frames),
                "new_frame_count": len(kept_frames),
                "notes": notes,
            }
        else:
            new_video["frames"] = frames
            new_video["selection_method"] = {
                "name": "not_filtered_eval_split",
                "input_split": split,
                "old_frame_count": len(frames),
                "new_frame_count": len(frames),
            }

        output.append(new_video)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))
    return output_path


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m brsd_lib.overfit_filter",
        description=(
            "Select high-confidence training frames from per-video overfit residuals "
            "and optionally write a filtered labels manifest."
        ),
    )
    parser.add_argument("residual_csv", help="CSV with per-frame residuals or prediction/target pairs")
    parser.add_argument("--selected-out", default=None, help="Optional CSV path for retained rows")
    parser.add_argument("--stats-out", default=None, help="Optional CSV path for per-video summary stats")
    parser.add_argument("--labels-json", default=None, help="Optional labels manifest to filter")
    parser.add_argument("--manifest-out", default=None, help="Where to write the filtered manifest")
    parser.add_argument("--k", type=float, default=0.385, help="Residual std multiplier")
    parser.add_argument("--min-keep-frac", type=float, default=None, help="Optional minimum keep fraction")
    parser.add_argument(
        "--fallback-quantile",
        type=float,
        default=None,
        help="Quantile threshold to use only when min_keep_frac is violated",
    )
    parser.add_argument("--sequence-len", type=int, default=8, help="Window length for manifest summary")
    parser.add_argument("--frame-stride", type=int, default=5, help="Stride for manifest summary")
    parser.add_argument(
        "--notes",
        default="controlled_overfit_data_selection",
        help="Free-text note stored in the filtered manifest metadata",
    )
    args = parser.parse_args()

    residual_df = standardize_residual_table(pd.read_csv(args.residual_csv))
    selected_df, stats_df = select_by_overfit_residuals(
        residual_df,
        k=args.k,
        min_keep_frac=args.min_keep_frac,
        fallback_quantile=args.fallback_quantile,
    )

    print(
        "Selected "
        f"{len(selected_df):,} / {len(residual_df):,} frames "
        f"({(len(selected_df) / len(residual_df)):.1%} overall)"
        if len(residual_df)
        else "Selected 0 / 0 frames"
    )

    if not stats_df.empty:
        print(
            "Median kept fraction per video: "
            f"{stats_df['kept_frac'].median():.1%} across {len(stats_df)} videos"
        )

    if args.selected_out:
        out_path = Path(args.selected_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        selected_df.to_csv(out_path, index=False)
        print(f"Wrote selected rows to {out_path}")

    if args.stats_out:
        out_path = Path(args.stats_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        stats_df.to_csv(out_path, index=False)
        print(f"Wrote per-video stats to {out_path}")

    if args.labels_json or args.manifest_out:
        if not args.labels_json or not args.manifest_out:
            raise SystemExit("--labels-json and --manifest-out must be provided together")

        videos = load_labels_json(args.labels_json)
        summary_df = summarize_manifest_after_selection(
            videos,
            selected_df,
            sequence_len=args.sequence_len,
            frame_stride=args.frame_stride,
        )
        manifest_path = write_filtered_manifest(
            videos,
            selected_df,
            args.manifest_out,
            k=args.k,
            notes=args.notes,
        )
        print(f"Wrote filtered manifest to {manifest_path}")
        if not summary_df.empty:
            grouped = (
                summary_df.groupby("split", dropna=False)[
                    ["old_frames", "new_frames", "old_samples_est", "new_samples_est"]
                ]
                .sum()
                .round(3)
            )
            print(grouped.to_string())


if __name__ == "__main__":
    _cli()

"""
brsd_lib.labels
===============

RSD label normalization and labels.json utilities.

Context
-------
Across the repo, RSD (remaining surgery duration) appears in two forms:

1. ``rsd_sec``        — seconds remaining until the surgery ends
2. ``rsd_normalized`` — the same quantity divided by the video's total duration,
                        so it lives in [0, 1]. 1.0 at surgery start, 0.0 at surgery end.

The conversion itself is arithmetic (``rsd_sec / total``) but in practice the
existing codebase inlines the formula in four separate files, each with slightly
different edge-case handling. This module centralises the logic and adds
robustness (clamping, monotonicity audit, idempotent re-normalization).

This code was written fresh for the NeurIPS 2026 submission. It is not copied
from any prior project.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple, Union

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Single-frame conversions
# ---------------------------------------------------------------------------

def seconds_to_rsd_fraction(seconds_remaining: float, total_seconds: float) -> float:
    """
    Convert seconds-remaining into the [0, 1] fraction used as a regression target.

    Parameters
    ----------
    seconds_remaining : float
        How many seconds of surgery are still to come (``0`` at surgery end).
    total_seconds : float
        Total duration of the video.

    Returns
    -------
    float in [0, 1]
        ``0`` if ``total_seconds <= 0``. The return value is clamped to [0, 1]
        to absorb small floating-point drift or slightly mis-ordered timestamps.
    """
    if total_seconds <= 0:
        return 0.0
    frac = float(seconds_remaining) / float(total_seconds)
    if frac < 0.0:
        return 0.0
    if frac > 1.0:
        return 1.0
    return frac


def frame_time_to_rsd_fraction(time_from_start: float, total_seconds: float) -> float:
    """
    Convert a timestamp measured *from the start* of the surgery into the same
    [0, 1] fraction. Provided because most frame-level annotations store
    ``timestamp_sec`` (time-from-start) rather than ``rsd_sec`` (time-to-end).

    At ``time_from_start = 0``                  → 1.0 (surgery just started)
    At ``time_from_start = total_seconds``      → 0.0 (surgery finishing)
    """
    if total_seconds <= 0:
        return 0.0
    seconds_remaining = total_seconds - float(time_from_start)
    return seconds_to_rsd_fraction(seconds_remaining, total_seconds)


# ---------------------------------------------------------------------------
# Per-video helper
# ---------------------------------------------------------------------------

def annotate_video_with_rsd_fractions(video: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """
    Given a single-video dict with ``total_duration_sec`` and ``frames[i].timestamp_sec``,
    (re)compute ``rsd_sec`` and ``rsd_normalized`` on every frame.

    - Idempotent: overwrites existing fields so re-running is safe.
    - In-place: mutates ``video`` and also returns it (for chaining).
    - Skips videos with missing or non-positive total duration
      (those are flagged by ``audit_labels`` below).

    Parameters
    ----------
    video : dict
        Must contain ``total_duration_sec`` and a ``frames`` list whose entries
        have ``timestamp_sec``.

    Returns
    -------
    The same dict, with each frame now carrying ``rsd_sec`` and ``rsd_normalized``.
    """
    total = float(video.get("total_duration_sec") or 0.0)
    frames = video.get("frames", []) or []
    if total <= 0:
        return video

    for frame in frames:
        ts = float(frame.get("timestamp_sec") or 0.0)
        rsd_sec = total - ts
        if rsd_sec < 0.0:
            rsd_sec = 0.0
        frame["rsd_sec"] = rsd_sec
        frame["rsd_normalized"] = seconds_to_rsd_fraction(rsd_sec, total)
    return video


# ---------------------------------------------------------------------------
# Whole-file helper
# ---------------------------------------------------------------------------

def normalize_labels_json(
    input_path: PathLike,
    output_path: Optional[PathLike] = None,
) -> List[Dict[str, Any]]:
    """
    Load a labels.json, recompute percentage labels on every frame, and optionally
    write to a new file. If ``output_path`` is ``None`` the input is overwritten.

    Returns the list of video dicts (same shape as the input JSON).
    """
    ipath = Path(input_path)
    with ipath.open() as f:
        videos = json.load(f)
    if not isinstance(videos, list):
        raise ValueError(
            f"{ipath}: expected a top-level list of videos, got {type(videos).__name__}"
        )

    for video in videos:
        annotate_video_with_rsd_fractions(video)

    opath = Path(output_path) if output_path is not None else ipath
    opath.parent.mkdir(parents=True, exist_ok=True)
    with opath.open("w") as f:
        json.dump(videos, f)
    return videos


# ---------------------------------------------------------------------------
# Audit / sanity check
# ---------------------------------------------------------------------------

def audit_labels(videos: Iterable[Mapping[str, Any]], tolerance: float = 1e-6) -> Dict[str, Any]:
    """
    Walk every video/frame and report anomalies useful for debugging a
    labels.json after normalization.

    Returns a dict with:
      videos_scanned, frames_scanned
      videos_with_zero_duration, videos_with_no_frames
      frames_out_of_range, frames_non_monotonic
      rsd_min, rsd_max        (observed extreme values of rsd_normalized)
      fraction_out_of_range   (frames_out_of_range / frames_scanned)
    """
    report = {
        "videos_scanned": 0,
        "frames_scanned": 0,
        "videos_with_zero_duration": 0,
        "videos_with_no_frames": 0,
        "frames_out_of_range": 0,
        "frames_non_monotonic": 0,
        "rsd_min": 1.0,
        "rsd_max": 0.0,
    }
    for v in videos:
        report["videos_scanned"] += 1
        total = float(v.get("total_duration_sec") or 0.0)
        frames = v.get("frames") or []
        if total <= 0:
            report["videos_with_zero_duration"] += 1
        if not frames:
            report["videos_with_no_frames"] += 1
            continue

        prev_norm = None
        for f in frames:
            report["frames_scanned"] += 1
            norm = float(f.get("rsd_normalized", -999.0))
            if norm < -tolerance or norm > 1.0 + tolerance:
                report["frames_out_of_range"] += 1
            else:
                report["rsd_min"] = min(report["rsd_min"], norm)
                report["rsd_max"] = max(report["rsd_max"], norm)
            # RSD should strictly not increase over time (with small slack)
            if prev_norm is not None and norm > prev_norm + 1e-3:
                report["frames_non_monotonic"] += 1
            prev_norm = norm

    fs = report["frames_scanned"]
    report["fraction_out_of_range"] = (
        report["frames_out_of_range"] / fs if fs > 0 else 0.0
    )
    return report


# ---------------------------------------------------------------------------
# CLI (optional)
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse
    import pprint

    p = argparse.ArgumentParser(
        prog="python -m brsd_lib.labels",
        description="Normalize RSD labels in a labels.json to percentages in [0, 1].",
    )
    p.add_argument("input", help="Path to the labels.json to read")
    p.add_argument("--out", default=None, help="Where to write; default = overwrite input")
    p.add_argument("--audit", action="store_true", help="Print a sanity-check report")
    args = p.parse_args()

    videos = normalize_labels_json(args.input, args.out)
    tgt = args.out or args.input
    print(f"Normalized {len(videos)} videos → {tgt}")
    if args.audit:
        pprint.pprint(audit_labels(videos))


if __name__ == "__main__":
    _cli()

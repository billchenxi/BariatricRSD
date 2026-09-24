"""Strict prefix-only phase-anticipation evaluator for Paper 2A.

Two tasks:

Task A — Time-to-next-phase-transition.
    Given prefix x_{≤t} (all frames up to t), predict:
      (i)  minutes until the next phase transition,
      (ii) identity of the next phase.

Task B — Future-phase-sequence.
    Given prefix x_{≤t}, predict the phase label at fixed horizons
    h ∈ {1, 2, 5, 10, 20, 30} minutes into the future.

Both tasks share the same strict prefix-only clip protocol as Paper 1:
the 8-frame input clip ends at time t and includes only past frames.
Ground-truth phase labels beyond t are never provided to the model at
inference.

Metrics:
- Task A: MAE for transition time (minutes), macro-F1 for next-phase
  identity, ECE for uncertainty calibration if the model emits a
  posterior.
- Task B: sequence edit score, per-horizon macro-F1, temporal Jaccard,
  horizon-binned MAE where applicable.
- All metrics reported per-video first (video-weighted) with paired
  bootstrap CIs across seeds, per the reviewer-hardened stat policy.

Phase 0 status: implemented. Ground-truth extraction reads the shared
label-JSON schema (a list of per-video records with a 1 fps `frames`
array); metrics and the paired bootstrap are verified against synthetic
videos with hand-computed answers in `tests/test_phase_anticipation.py`.
"""
from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("phase_anticipation")


# ── Data structures ─────────────────────────────────────────────────────────

@dataclass
class ClipRecord:
    """One clip's prefix + predicted / true labels for anticipation eval.

    `clip_end_frame` is the label JSON's own `frame_idx` for the last
    frame of the prefix clip — the canonical identifier a predictions
    file keys on. `clip_end_sec` is that frame's `timestamp_sec`. The two
    differ by a per-video constant offset (MB140 videos start at
    `frame_idx` 13, `timestamp_sec` 14.0), so all time arithmetic uses
    `timestamp_sec` and all keying uses `frame_idx`.
    """
    video_id: str
    clip_end_frame: int
    clip_end_sec: float
    # Task A ground truth
    seconds_to_next_transition: float
    next_phase_id: Optional[int]
    # Task B ground truth (may be None past video end)
    future_phase_at_horizon: Dict[int, Optional[int]] = field(default_factory=dict)
    # Contextual fields (useful for stratified reporting, not for scoring)
    current_phase_id: Optional[int] = None
    split: Optional[str] = None
    # Model predictions (filled in by the eval script)
    pred_seconds_to_next_transition: Optional[float] = None
    pred_next_phase_id: Optional[int] = None
    pred_next_phase_posterior: Optional[List[float]] = None  # K-dim
    pred_future_phase_at_horizon: Optional[Dict[int, int]] = None


# ── Ground-truth construction ───────────────────────────────────────────────

# Paper 1's strict prefix-only clip is sequence_len=8 frames at
# frame_stride=5, so the clip ending at t spans (8-1)*5 = 35 seconds of
# history at 1 fps. Clip ends earlier than that have no full prefix and
# are not evaluable under the strict protocol.
DEFAULT_MIN_PREFIX_SEC = (8 - 1) * 5


def build_ground_truth(label_json: Path, fps: int = 1,
                       horizons_min: Tuple[int, ...] = (1, 2, 5, 10, 20, 30),
                       split: Optional[str] = None,
                       clip_stride_sec: int = 1,
                       min_prefix_sec: int = DEFAULT_MIN_PREFIX_SEC,
                       ) -> Dict[Tuple[str, int], ClipRecord]:
    """Build the (video_id, clip_end_frame) → ClipRecord ground-truth map.

    Reads the per-video phase label sequence from the label JSON, which
    is a list of video records sharing the schema used by MB140,
    Cholec80 and (post-preprocessing) AutoLaparo:

        {"video_id", "total_duration_sec", "phase_vocab", "split",
         "frames": [{"frame_idx", "timestamp_sec", "phase", ...}, ...]}

    For every evaluable clip end t:
      - find the first frame after t whose phase differs from the phase
        at t → `transition_frame`, the first frame of the *next* phase
      - seconds_to_next_transition = ts[transition_frame] - ts[t]
      - next_phase_id = phase at `transition_frame`
      - future_phase_at_horizon[h] = phase at timestamp ts[t] + 60*h,
        or None if that timestamp is past the video end or falls in a
        gap in the frame index

    If no future transition exists (t is inside the video's last phase),
    the record gets `seconds_to_next_transition = inf` and
    `next_phase_id = None`; such records are excluded from Task A metrics
    but retained for Task B, where a fixed horizon is still well defined.

    A clip end is evaluable when it has at least `min_prefix_sec` of
    history available, which enforces the strict prefix-only protocol at
    ground-truth-construction time rather than trusting the model to
    respect it.
    """
    videos = json.loads(Path(label_json).read_text())
    if not isinstance(videos, list):
        raise ValueError(
            f"{label_json}: expected a list of video records, got "
            f"{type(videos).__name__}"
        )
    if clip_stride_sec < 1:
        raise ValueError(f"clip_stride_sec must be >= 1, got {clip_stride_sec}")

    gt: Dict[Tuple[str, int], ClipRecord] = {}
    for video in videos:
        if split is not None and video.get("split") != split:
            continue
        records = _ground_truth_one_video(
            video, fps=fps, horizons_min=horizons_min,
            clip_stride_sec=clip_stride_sec, min_prefix_sec=min_prefix_sec,
        )
        for rec in records:
            gt[(rec.video_id, rec.clip_end_frame)] = rec

    logger.info(
        "Built %d ground-truth clip records from %d videos (split=%s, "
        "stride=%ds, min_prefix=%ds)",
        len(gt), len({k[0] for k in gt}), split, clip_stride_sec, min_prefix_sec,
    )
    return gt


def _ground_truth_one_video(video: Dict, fps: int,
                            horizons_min: Tuple[int, ...],
                            clip_stride_sec: int,
                            min_prefix_sec: int) -> List[ClipRecord]:
    """Ground-truth records for a single video record. See build_ground_truth."""
    frames = video["frames"]
    if not frames:
        return []
    vocab = video["phase_vocab"]
    video_id = video["video_id"]
    vsplit = video.get("split")

    times = np.asarray([float(f["timestamp_sec"]) for f in frames], dtype=np.float64)
    idxs = [int(f["frame_idx"]) for f in frames]
    try:
        phases = np.asarray([int(vocab[f["phase"]]) for f in frames], dtype=np.int64)
    except KeyError as exc:
        raise ValueError(
            f"{video_id}: frame phase {exc} is absent from phase_vocab"
        ) from exc

    n = len(frames)
    # next_change[i] = index of the first frame after i whose phase differs
    # from phases[i], or -1 when i lies inside the final phase. One reverse
    # pass: if the next frame already differs, that is the transition;
    # otherwise it is wherever the next frame's transition is.
    next_change = np.full(n, -1, dtype=np.int64)
    for i in range(n - 2, -1, -1):
        next_change[i] = i + 1 if phases[i + 1] != phases[i] else next_change[i + 1]

    # Exact-timestamp lookup for the Task B horizons. searchsorted plus an
    # equality check means a horizon landing in a gap resolves to None
    # rather than silently snapping to a neighbouring frame.
    def phase_at_time(t_sec: float) -> Optional[int]:
        pos = int(np.searchsorted(times, t_sec, side="left"))
        if pos >= n or times[pos] != t_sec:
            return None
        return int(phases[pos])

    t0 = times[0]
    out: List[ClipRecord] = []
    for i in range(n):
        if times[i] - t0 < min_prefix_sec:
            continue
        if (idxs[i] - idxs[0]) % clip_stride_sec != 0:
            continue

        j = int(next_change[i])
        if j < 0:
            sec_to_next = float("inf")
            next_phase = None
        else:
            sec_to_next = float(times[j] - times[i])
            next_phase = int(phases[j])

        out.append(ClipRecord(
            video_id=video_id,
            clip_end_frame=idxs[i],
            clip_end_sec=float(times[i]),
            seconds_to_next_transition=sec_to_next,
            next_phase_id=next_phase,
            future_phase_at_horizon={
                h: phase_at_time(float(times[i]) + 60.0 * h) for h in horizons_min
            },
            current_phase_id=int(phases[i]),
            split=vsplit,
        ))
    return out


# ── Metric helpers ──────────────────────────────────────────────────────────

def mae_transition_time_minutes(records: List[ClipRecord]) -> float:
    """MAE between predicted and true seconds-to-next-transition, in
    minutes. Excludes clips where GT is inf (no future transition)."""
    errors = []
    for r in records:
        if r.seconds_to_next_transition == float("inf"):
            continue
        if r.pred_seconds_to_next_transition is None:
            continue
        errors.append(abs(r.pred_seconds_to_next_transition
                          - r.seconds_to_next_transition) / 60.0)
    if not errors:
        return float("nan")
    return sum(errors) / len(errors)


def macro_f1_next_phase(records: List[ClipRecord], n_phases: int) -> float:
    """Macro-F1 for next-phase identity across all clips with a valid
    next-phase GT."""
    from collections import defaultdict
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    for r in records:
        if r.next_phase_id is None or r.pred_next_phase_id is None:
            continue
        gt = r.next_phase_id
        pred = r.pred_next_phase_id
        if gt == pred:
            tp[gt] += 1
        else:
            fp[pred] += 1
            fn[gt] += 1
    f1s = []
    for k in range(n_phases):
        p = tp[k] / (tp[k] + fp[k]) if (tp[k] + fp[k]) else 0.0
        r = tp[k] / (tp[k] + fn[k]) if (tp[k] + fn[k]) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        f1s.append(f1)
    return sum(f1s) / n_phases if f1s else float("nan")


def ece_next_phase(records: List[ClipRecord], n_bins: int = 15) -> float:
    """Expected calibration error for the next-phase posterior.

    ECE = Σ_bin (|bin| / N) * |acc(bin) - conf(bin)|,
    computed on the top-1 (argmax) posterior confidence.
    """
    filtered = [r for r in records if r.pred_next_phase_posterior is not None
                and r.next_phase_id is not None]
    if not filtered:
        return float("nan")
    confs = []
    correct = []
    for r in filtered:
        post = r.pred_next_phase_posterior
        argmax = max(range(len(post)), key=lambda i: post[i])
        confs.append(post[argmax])
        correct.append(int(argmax == r.next_phase_id))
    N = len(confs)
    # Bin by confidence
    bin_lo = [i / n_bins for i in range(n_bins)]
    ece = 0.0
    for lo in bin_lo:
        hi = lo + 1.0 / n_bins
        bin_indices = [i for i, c in enumerate(confs) if lo <= c < hi]
        if not bin_indices:
            continue
        bin_acc = sum(correct[i] for i in bin_indices) / len(bin_indices)
        bin_conf = sum(confs[i] for i in bin_indices) / len(bin_indices)
        ece += (len(bin_indices) / N) * abs(bin_acc - bin_conf)
    return ece


def horizon_macro_f1(records: List[ClipRecord], horizon_min: int,
                     n_phases: int) -> float:
    """Task B: macro-F1 at one horizon."""
    from collections import defaultdict
    tp = defaultdict(int); fp = defaultdict(int); fn = defaultdict(int)
    for r in records:
        if r.pred_future_phase_at_horizon is None:
            continue
        gt = r.future_phase_at_horizon.get(horizon_min)
        pred = r.pred_future_phase_at_horizon.get(horizon_min)
        if gt is None or pred is None:
            continue
        if gt == pred:
            tp[gt] += 1
        else:
            fp[pred] += 1; fn[gt] += 1
    f1s = []
    for k in range(n_phases):
        p = tp[k] / (tp[k] + fp[k]) if (tp[k] + fp[k]) else 0.0
        rc = tp[k] / (tp[k] + fn[k]) if (tp[k] + fn[k]) else 0.0
        f1 = 2 * p * rc / (p + rc) if (p + rc) else 0.0
        f1s.append(f1)
    return sum(f1s) / n_phases if f1s else float("nan")


# ── Per-video aggregation + bootstrap ───────────────────────────────────────

def per_video_video_weighted(records: List[ClipRecord],
                             metric_fn) -> float:
    """Compute the metric per video first, then average across videos
    (video-weighted). Matches Paper 1's §6.5 matched-metric convention.
    """
    per_vid = list(_per_video_metric(records, metric_fn).values())
    return sum(per_vid) / len(per_vid) if per_vid else float("nan")


def _per_video_metric(records: List[ClipRecord], metric_fn) -> Dict[str, float]:
    """video_id → metric over that video's records, dropping NaN videos."""
    from collections import defaultdict
    by_vid = defaultdict(list)
    for r in records:
        by_vid[r.video_id].append(r)
    out = {}
    for vid, recs in by_vid.items():
        val = metric_fn(recs)
        if val == val:  # drop NaN
            out[vid] = float(val)
    return out


def paired_bootstrap_ci(records_A: List[ClipRecord],
                        records_B: List[ClipRecord],
                        metric_fn, n_boot: int = 1000,
                        seed: int = 42,
                        confidence: float = 0.95) -> Dict[str, float]:
    """Paired bootstrap on per-video metric differences (A - B).

    Returns median, 2.5th, 97.5th percentile of the (A - B) distribution.
    Requires the two record lists to share the same video_ids.

    Videos are resampled with replacement as whole units and the same
    resampled video set is used for both conditions — this is the paired
    part, and it is what makes the CI comparable to the paired Wilcoxon
    reported alongside it in Paper 1 §6.5. Mirrors the resampling scheme
    in `brsd_lib.stats.bootstrap_ci`, applied to the A−B difference.
    """
    a = _per_video_metric(records_A, metric_fn)
    b = _per_video_metric(records_B, metric_fn)
    keys = sorted(set(a) & set(b))
    if not keys:
        raise ValueError(
            "No videos shared between the two conditions — paired bootstrap "
            "requires a matched video set."
        )
    if len(keys) < len(set(a) | set(b)):
        logger.warning(
            "Paired bootstrap over %d shared videos; %d video(s) present in "
            "only one condition were dropped.",
            len(keys), len(set(a) | set(b)) - len(keys),
        )

    diffs = np.asarray([a[k] - b[k] for k in keys], dtype=np.float64)
    rng = np.random.default_rng(seed)
    n = diffs.shape[0]
    boot = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        boot[i] = diffs[rng.integers(0, n, size=n)].mean()

    alpha = 1.0 - confidence
    return {
        "n_paired": n,
        "mean_diff_a_minus_b": float(diffs.mean()),
        "median_diff_a_minus_b": float(np.median(diffs)),
        "boot_median": float(np.quantile(boot, 0.5)),
        "ci_low": float(np.quantile(boot, alpha / 2)),
        "ci_high": float(np.quantile(boot, 1 - alpha / 2)),
        "confidence": confidence,
        "n_a_higher": int((diffs > 0).sum()),
        "n_b_higher": int((diffs < 0).sum()),
    }


# ── Full eval report ────────────────────────────────────────────────────────

def evaluate(records: List[ClipRecord], n_phases: int,
             horizons_min: Tuple[int, ...] = (1, 2, 5, 10, 20, 30)
             ) -> Dict[str, float]:
    """Compute the full evaluation report for one condition/seed."""
    n_scored_a = sum(
        1 for r in records
        if r.seconds_to_next_transition != float("inf")
        and r.pred_seconds_to_next_transition is not None
    )
    return {
        "n_clips": len(records),
        "n_videos": len({r.video_id for r in records}),
        "n_clips_scored_task_a": n_scored_a,
        "task_a_mae_minutes_clip_weighted":
            mae_transition_time_minutes(records),
        "task_a_mae_minutes_video_weighted":
            per_video_video_weighted(records, mae_transition_time_minutes),
        "task_a_next_phase_macro_f1":
            macro_f1_next_phase(records, n_phases),
        "task_a_next_phase_ece":
            ece_next_phase(records),
        **{
            f"task_b_horizon_{h}min_macro_f1":
                horizon_macro_f1(records, h, n_phases)
            for h in horizons_min
        },
    }


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label-json", required=True, type=Path,
                    help="Ground-truth phase label JSON.")
    ap.add_argument("--predictions-json", required=True, type=Path,
                    help="Model predictions, keyed by "
                         "(video_id, clip_end_frame).")
    ap.add_argument("--n-phases", required=True, type=int,
                    help="Number of phase classes (MB140:14, Cholec80:7, "
                         "AutoLaparo:7).")
    ap.add_argument("--horizons", type=int, nargs="+",
                    default=[1, 2, 5, 10, 20, 30],
                    help="Task B future-phase horizons in minutes.")
    ap.add_argument("--split", default="test",
                    help="Label-JSON split to evaluate ('all' for every video).")
    ap.add_argument("--clip-stride-sec", type=int, default=1,
                    help="Evaluate every Nth clip end. 1 = every second.")
    ap.add_argument("--min-prefix-sec", type=int, default=DEFAULT_MIN_PREFIX_SEC,
                    help="Minimum history required for a clip end to be "
                         "evaluable under the strict prefix-only protocol.")
    ap.add_argument("--report-out", type=Path, required=True)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Build ground truth
    gt_map = build_ground_truth(
        args.label_json,
        horizons_min=tuple(args.horizons),
        split=None if args.split == "all" else args.split,
        clip_stride_sec=args.clip_stride_sec,
        min_prefix_sec=args.min_prefix_sec,
    )
    if not gt_map:
        raise SystemExit(
            f"No ground-truth clips for split={args.split!r} in "
            f"{args.label_json}. Check the split name."
        )

    # Load predictions and merge into ClipRecords
    preds = json.loads(args.predictions_json.read_text())
    records: List[ClipRecord] = []
    n_matched = 0
    for key, rec in gt_map.items():
        pred = preds.get(f"{key[0]}|{key[1]}")
        if pred is not None:
            n_matched += 1
            rec.pred_seconds_to_next_transition = pred.get("sec_to_next")
            rec.pred_next_phase_id = pred.get("next_phase_id")
            rec.pred_next_phase_posterior = pred.get("next_phase_posterior")
            rec.pred_future_phase_at_horizon = {
                int(h): int(p) for h, p in pred.get("future_at_horizon", {}).items()
            }
        records.append(rec)

    if n_matched == 0:
        raise SystemExit(
            f"None of the {len(preds)} predictions matched a ground-truth "
            f"clip. Predictions must be keyed '<video_id>|<frame_idx>' using "
            f"the label JSON's own frame_idx values."
        )
    logger.info("Matched predictions for %d/%d ground-truth clips",
                n_matched, len(gt_map))

    report = evaluate(records, n_phases=args.n_phases,
                      horizons_min=tuple(args.horizons))
    report["n_clips_with_predictions"] = n_matched
    args.report_out.write_text(json.dumps(report, indent=2))
    logger.info(f"Wrote {args.report_out}")


if __name__ == "__main__":
    main()

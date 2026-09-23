"""Episode-level audit of the MB140 deviation flag.

Answers the gate question in ``plans/STRATEGY.md`` §VII.2 — *"decide whether
anticipation is identifiable before scaling"* — from the label exports that are
already in this checkout, with no GPU and no frame data.

The distinction this module exists to draw
------------------------------------------
§IV.1 observes that the fold-0 export carries 70,366 flagged frames across
138 of 140 operations, and concludes that *"a binary 'any event during the
case' endpoint would have little discrimination"*. That is correct, and it is
a statement about the **case level**.

At the **episode level** the same flag looks different: contiguous runs of
``is_deviation`` form discrete events with onsets, durations and event-free
intervals between them. That is an anticipation-shaped target. This module
measures it so the choice between the two framings rests on counts rather than
on impression.

What this does not establish
----------------------------
``is_deviation`` is a lossy boolean: ``lambda_setup/scripts/06_build_labels.py``
derived it from ``Overall > 0`` and discarded event category, severity and
step, and a missing ``Overall`` was silently mapped to zero. Episodes recovered
here are therefore **flag-derived, not adjudicated events**. This module
establishes that an endpoint is *measurable*; it says nothing about whether it
is clinically valid. Clinician review of a sample is still required before any
clinical claim.

Cholec80 is deliberately excluded: its builders assign ``is_deviation = False``
with no adverse-event annotation, so its safety target is *missing*, never
negative.

Usage
-----
    python -m brsd_lib.episode_audit                      # fold 0, default horizons
    python -m brsd_lib.episode_audit --all-folds          # per-fold test-split power
    python -m brsd_lib.episode_audit --horizons 30 60 90
"""

from __future__ import annotations

import argparse
import json
import statistics as st
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

DEFAULT_HORIZONS_S: tuple[int, ...] = (15, 30, 60, 120)


@dataclass(frozen=True)
class Episode:
    """One contiguous run of flagged frames within a single operation."""
    operation: str
    centre: str
    onset_s: float
    offset_s: float
    n_frames: int

    @property
    def duration_s(self) -> float:
        return self.offset_s - self.onset_s


@dataclass
class HorizonBalance:
    """Class balance of the prefix-only anticipation task at one horizon."""
    horizon_s: int
    positive_frames: int
    eligible_frames: int
    onsets_with_usable_prefix: int
    onsets_total: int

    @property
    def positive_rate(self) -> float:
        return self.positive_frames / self.eligible_frames if self.eligible_frames else 0.0


@dataclass
class Audit:
    n_operations: int
    episodes: list[Episode]
    episodes_per_operation: list[int]
    operations_without_episode: list[str]
    operations_with_immediate_onset: list[str] = field(default_factory=list)
    balances: list[HorizonBalance] = field(default_factory=list)

    @property
    def n_episodes(self) -> int:
        return len(self.episodes)


def extract_episodes(record: dict) -> list[Episode]:
    """Contiguous runs of ``is_deviation`` in one operation's frame list.

    Frames are assumed to be in ascending time order, which is how the label
    builder writes them. A run is closed by the first unflagged frame or by the
    end of the operation.
    """
    op = record.get("video_id", "?")
    centre = op[:3]
    out: list[Episode] = []
    start: Optional[float] = None
    last: float = 0.0
    count = 0

    for frame in record.get("frames", []):
        t = frame.get("timestamp_sec", 0.0)
        if frame.get("is_deviation"):
            if start is None:
                start, count = t, 0
            last, count = t, count + 1
        elif start is not None:
            out.append(Episode(op, centre, start, last, count))
            start = None
    if start is not None:
        out.append(Episode(op, centre, start, last, count))
    return out


def horizon_balance(records: Sequence[dict], horizon_s: int,
                    episodes_by_op: dict[str, list[Episode]]) -> HorizonBalance:
    """Positive rate for "an onset falls in (t, t+H]", prefix-only.

    Frames *inside* an ongoing episode are excluded from the denominator: a
    model scoring those would be doing detection, not anticipation, and
    counting them would inflate apparent performance. Onsets closer to the
    start of the operation than ``horizon_s`` have no usable prefix and are
    reported separately rather than silently dropped.
    """
    positive = eligible = usable = total = 0
    for rec in records:
        eps = episodes_by_op.get(rec.get("video_id", "?"), [])
        onsets = [e.onset_s for e in eps]
        spans = [(e.onset_s, e.offset_s) for e in eps]
        total += len(onsets)
        usable += sum(1 for o in onsets if o >= horizon_s)
        for frame in rec.get("frames", []):
            t = frame.get("timestamp_sec", 0.0)
            if any(s <= t <= e for s, e in spans):
                continue
            eligible += 1
            if any(t < o <= t + horizon_s for o in onsets):
                positive += 1
    return HorizonBalance(horizon_s, positive, eligible, usable, total)


def audit_records(records: Sequence[dict],
                  horizons_s: Iterable[int] = DEFAULT_HORIZONS_S) -> Audit:
    episodes_by_op: dict[str, list[Episode]] = {}
    all_eps: list[Episode] = []
    per_op: list[int] = []
    empty: list[str] = []
    immediate: list[str] = []

    for rec in records:
        op = rec.get("video_id", "?")
        eps = extract_episodes(rec)
        episodes_by_op[op] = eps
        all_eps.extend(eps)
        per_op.append(len(eps))
        if not eps:
            empty.append(op)
        elif eps[0].onset_s < 60.0:
            # No usable minute of prefix before the first event.
            immediate.append(op)

    return Audit(
        n_operations=len(records),
        episodes=all_eps,
        episodes_per_operation=per_op,
        operations_without_episode=empty,
        operations_with_immediate_onset=immediate,
        balances=[horizon_balance(records, h, episodes_by_op) for h in horizons_s],
    )


def load_records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError(f"{path} is not a list of operation records")
    return payload


# ── report ──────────────────────────────────────────────────────────────────


def render(audit: Audit, title: str) -> str:
    L: list[str] = []
    w = L.append
    eps = audit.episodes
    w(f"{title}")
    w("=" * len(title))
    w("")

    if not eps:
        w("No flagged episodes found. Nothing to audit.")
        return "\n".join(L)

    centres: dict[str, int] = {}
    for e in eps:
        centres[e.centre] = centres.get(e.centre, 0) + 1
    per_op = audit.episodes_per_operation
    durs = [e.duration_s for e in eps]

    w(f"operations               : {audit.n_operations}")
    w(f"episodes                 : {audit.n_episodes}  by centre {centres}")
    w(f"episodes per operation   : median {st.median(per_op):.0f}  "
      f"mean {st.mean(per_op):.1f}  max {max(per_op)}")
    w(f"  with no episode        : {len(audit.operations_without_episode)}")
    w(f"  first onset < 60 s     : {len(audit.operations_with_immediate_onset)}"
      "   (no usable prefix; exclude or special-case)")
    w("")
    w(f"episode duration (s)     : median {st.median(durs):.0f}  "
      f"mean {st.mean(durs):.0f}  max {max(durs):.0f}")
    for label, pred in (("<= 30 s", lambda x: x <= 30), ("> 120 s", lambda x: x > 120)):
        n = sum(1 for x in durs if pred(x))
        w(f"  {label:<22}: {n:>4}  ({100 * n / len(durs):.0f}%)")
    w("")
    w("Prefix-only anticipation task — positive if an onset falls in (t, t+H];")
    w("frames inside an ongoing episode excluded from the denominator.")
    w("")
    w(f"  {'H':>6} {'positive':>10} {'eligible':>10} {'rate':>8}  {'onsets w/ prefix':>18}")
    for b in audit.balances:
        w(f"  {b.horizon_s:>5}s {b.positive_frames:>10,} {b.eligible_frames:>10,} "
          f"{100 * b.positive_rate:>7.2f}%  {b.onsets_with_usable_prefix:>10} / "
          f"{b.onsets_total}")
    w("")
    w("Episodes are flag-derived, not adjudicated: is_deviation came from")
    w("Overall > 0 with category, severity and step discarded. This shows the")
    w("endpoint is measurable, not that it is clinically valid.")
    return "\n".join(L)


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.episode_audit",
        description="Measure whether episode-level anticipation is identifiable "
                    "in the MB140 label exports.",
    )
    ap.add_argument("--labels", type=Path, default=None,
                    help="Label export to audit (default: labels/mb140_fold0_labels.json).")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="Repository root.")
    ap.add_argument("--horizons", type=int, nargs="+", default=list(DEFAULT_HORIZONS_S),
                    help="Anticipation horizons in seconds.")
    ap.add_argument("--all-folds", action="store_true",
                    help="Also report episodes in each fold's test split (power check).")
    args = ap.parse_args(list(argv) if argv is not None else None)

    root: Path = args.root.resolve()
    labels = args.labels or (root / "labels" / "mb140_fold0_labels.json")
    if not labels.is_file():
        print(f"label export not found: {labels}")
        return 2

    records = load_records(labels)
    print(render(audit_records(records, args.horizons), f"Episode audit — {labels.name}"))

    if args.all_folds:
        print()
        print("Per-fold test-split power")
        print("-------------------------")
        for fold in range(5):
            p = root / "labels" / f"mb140_fold{fold}_labels.json"
            if not p.is_file():
                print(f"  fold {fold}: missing")
                continue
            test = [r for r in load_records(p) if r.get("split") == "test"]
            n = sum(len(extract_episodes(r)) for r in test)
            print(f"  fold {fold}: {len(test):>3} test operations, {n:>4} episodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

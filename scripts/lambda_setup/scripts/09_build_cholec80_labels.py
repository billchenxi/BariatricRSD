#!/usr/bin/env python3
"""
Build labels.json for Cholec80 from the public CAMMA tarball.

The tarball (despite what TF-Cholec80's dataset.py implies) contains:
  frames/videoXX/videoXX_NNNNNN.png   — 1fps pre-extracted PNGs
  phase_annotations/videoXX-phase.txt  — native-fps phase labels (25–30 Hz, `Frame\\tPhase` rows)
  tool_annotations/videoXX-tool.txt   — tool presence (not used here)

Only 68 of 80 videos have phase labels (videos 1,2,7,18,19,34,45,46,61,62,72,73 missing).

Phase annotations are at native fps; extracted frames are at 1 fps. We figure out the
native fps per video by `len(phase_file) / num_frames_in_dir`, then subsample phase labels
accordingly, then match each 1-fps frame to its phase label and build labels.json.

Usage:
  python3 scripts/09_build_cholec80_labels.py \\
    --root /lambda/nfs/bariatric-rsd/extern/cholec80 \\
    --out_labels /lambda/nfs/bariatric-rsd/labels/cholec80_labels.json
"""
import argparse
import json
import re
import sys
from collections import OrderedDict, Counter
from pathlib import Path

CHOLEC80_PHASES = [
    "Preparation",
    "CalotTriangleDissection",
    "ClippingCutting",
    "GallbladderDissection",
    "GallbladderPackaging",
    "CleaningCoagulation",
    "GallbladderRetraction",
]
PHASE_VOCAB = OrderedDict((p, i) for i, p in enumerate(CHOLEC80_PHASES))
PHASE_FROM_TEXT = {p.lower(): p for p in CHOLEC80_PHASES}


def parse_phase_file(path):
    """Return list of (frame_native_idx, phase_str). Skips header."""
    rows = []
    with open(path) as f:
        for i, line in enumerate(f):
            if i == 0:
                continue  # header "Frame\tPhase"
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            frame_idx = int(parts[0])
            phase_str = parts[1]
            # Normalize case
            canonical = PHASE_FROM_TEXT.get(phase_str.lower())
            if canonical is None:
                raise ValueError(f"Unknown phase '{phase_str}' in {path}")
            rows.append((frame_idx, canonical))
    return rows


def build_video_entry(video_id, frames_dir, phase_file):
    frame_paths = sorted(frames_dir.glob(f"{video_id}_*.png"))
    if not frame_paths:
        return None

    # Extract numeric index from filename: video01_000001.png → 1
    frame_ids = []
    for fp in frame_paths:
        m = re.search(rf"{re.escape(video_id)}_(\d+)\.png$", fp.name)
        if m:
            frame_ids.append(int(m.group(1)))
    frame_ids.sort()

    phase_rows = parse_phase_file(phase_file)
    n_phase_rows = len(phase_rows)
    n_frames = len(frame_ids)

    # Native fps ≈ n_phase_rows / (max_frame_id_at_1fps_in_secs)
    # Phase rows are every-frame labels at native fps. The 1fps frames should correspond
    # to rows at index i*fps_native (i=0..n-1). We detect fps_native empirically from the
    # ratio: native_fps ≈ n_phase_rows / (last_frame_id - first_frame_id + 1) is ambiguous
    # because frame IDs are 1-indexed and sometimes sparse. Safer:
    # look up phase for each 1-fps frame by stepping native_idx = (frame_id - 1) * stride.
    # The known Cholec80 native fps is 25 Hz.
    # BUT the frame_id in the file naming is already the 1-fps index, NOT native.
    # So phase lookup is: phase_rows[(frame_id - 1) * stride] where stride = native_fps.
    # We can infer stride = round(n_phase_rows / frame_id_max).
    stride = max(1, round(n_phase_rows / max(frame_ids)))

    out_frames = []
    phase_sequence = []
    prev_phase_name = None
    for fid in frame_ids:
        native_idx = (fid - 1) * stride
        if native_idx >= n_phase_rows:
            native_idx = n_phase_rows - 1
        phase_name = phase_rows[native_idx][1]
        timestamp = float(fid - 1)  # 0-indexed second at 1 fps
        total_duration_sec = float(max(frame_ids))
        rsd_sec = max(0.0, total_duration_sec - timestamp)
        rsd_norm = rsd_sec / total_duration_sec if total_duration_sec > 0 else 0.0
        frame_path = f"frames/{video_id}/{video_id}_{fid:06d}.png"

        out_frames.append({
            "frame_idx": fid - 1,
            "timestamp_sec": timestamp,
            "rsd_sec": rsd_sec,
            "rsd_normalized": rsd_norm,
            "phase": phase_name,
            "is_deviation": False,
            "frame_path": frame_path,
        })
        if phase_name != prev_phase_name:
            phase_sequence.append(phase_name)
            prev_phase_name = phase_name

    total_duration_sec = float(max(frame_ids))
    return {
        "video_id": video_id,
        "total_duration_sec": total_duration_sec,
        "phase_sequence": phase_sequence,
        "phase_vocab": dict(PHASE_VOCAB),
        "phase_order_cluster": 0,
        "split": "train",  # filled later
        "frames": out_frames,
        "_fps_stride": stride,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out_labels", required=True)
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    args = ap.parse_args()

    sys.path.insert(0, args.project_src)
    from data.dataset import infer_phase_order_cluster  # type: ignore

    root = Path(args.root)
    frames_root = root / "frames"
    phase_root = root / "phase_annotations"

    phase_files = sorted(phase_root.glob("video*-phase.txt"))
    print(f"Found {len(phase_files)} phase annotation files")

    videos = []
    strides_seen = Counter()
    for pf in phase_files:
        video_id = pf.stem.replace("-phase", "")
        fd = frames_root / video_id
        if not fd.exists():
            print(f"  skip {video_id}: no frames dir")
            continue
        try:
            entry = build_video_entry(video_id, fd, pf)
        except Exception as e:
            print(f"  ERROR {video_id}: {e}", file=sys.stderr)
            continue
        if entry is None:
            continue
        strides_seen[entry.pop("_fps_stride")] += 1
        # Standard split: video 1-40 train, 41-48 val, 49-80 test
        n = int(video_id.replace("video", ""))
        entry["split"] = "train" if n <= 40 else ("val" if n <= 48 else "test")
        entry["phase_order_cluster"] = infer_phase_order_cluster(entry["phase_sequence"])
        videos.append(entry)
        print(f"  {video_id}: {len(entry['frames'])} frames, duration={entry['total_duration_sec']:.0f}s, split={entry['split']}")

    # Summary
    split_counts = Counter(v["split"] for v in videos)
    print(f"\nTotal videos: {len(videos)}")
    print(f"Split counts: {dict(split_counts)}")
    print(f"FPS stride distribution: {dict(strides_seen)} (these are the inferred native_fps / 1fps ratios)")

    out_path = Path(args.out_labels)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(videos, f)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

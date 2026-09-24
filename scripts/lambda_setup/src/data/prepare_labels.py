#!/usr/bin/env python3
"""
src/data/prepare_labels.py

Converts your 2019 dataset annotations into the labels.json format
that BariatricFrameDataset expects.

Adjust the INPUT_FORMAT section to match however your 2019 annotations
are stored (CSV, pickle, JSON, etc).

Run:
  python src/data/prepare_labels.py \
    --ann_dir /data/bariatric_surgery/annotations \
    --frames_dir /data/bariatric_surgery/frames \
    --output labels/bariatric_labels.json \
    --val_fraction 0.1 \
    --test_fraction 0.1

Also handles frame extraction from raw video files:
  python src/data/prepare_labels.py \
    --video_dir /data/bariatric_surgery/videos \
    --ann_dir /data/bariatric_surgery/annotations \
    --extract_frames \
    --fps 1
"""

import os
import sys
import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from data.dataset import infer_phase_order_cluster


# ── Phase vocabulary (from your 2019 slides) ─────────────────────────────────

PHASE_VOCAB = {
    "Gastric pouch creation": 0,
    "Gastro-jejunal anastomosis": 1,
    "Jejuno-jejunal anastomosis": 2,
    "Alimentary (roux) limb measurement": 3,
    "Biliopancreatic limb measurement": 4,
    "Closure of mesenteric defect": 5,
    "Closure of petersen's space": 6,
    "Open lesser sac": 7,
    "Liver retraction": 8,
    "Jejunal division": 9,
    "Leak test": 10,
    "Out of body": 11,
    "Unknown": 12,
}


# ── Frame extraction ──────────────────────────────────────────────────────────

def extract_frames(video_path: str, output_dir: str, fps: float = 1.0) -> List[str]:
    """Extract frames from a video at the given FPS. Returns list of frame paths."""
    try:
        import av
    except ImportError:
        raise ImportError("pip install av")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_paths = []
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        orig_fps = float(stream.average_rate)
        stride = max(1, int(orig_fps / fps))

        for i, frame in enumerate(container.decode(stream)):
            if i % stride == 0:
                frame_idx = i // stride
                img = frame.to_image().convert("RGB")
                frame_path = output_dir / f"frame_{frame_idx:06d}.jpg"
                img.save(frame_path, quality=85)
                frame_paths.append(str(frame_path))

    return frame_paths


# ── Annotation loading (adapt to your 2019 format) ───────────────────────────

def load_2019_annotation(ann_path: str) -> Optional[dict]:
    """
    Load annotation for a single video from your 2019 format.
    
    YOUR 2019 DATA FORMAT — update this function to match your actual files.
    
    The slides show annotations with:
      - video_id (e.g., "3361")
      - phase labels per frame
      - total duration
    
    Return None to skip a video.
    """
    ann_path = Path(ann_path)
    if not ann_path.exists():
        return None

    # ── ADAPT THIS SECTION TO YOUR ACTUAL FORMAT ──────────────────
    # Example 1: JSON format
    if ann_path.suffix == ".json":
        with open(ann_path) as f:
            data = json.load(f)
        return data

    # Example 2: CSV with columns: frame_idx, timestamp_sec, phase, is_deviation
    elif ann_path.suffix == ".csv":
        import pandas as pd
        df = pd.read_csv(ann_path)
        frames = []
        for _, row in df.iterrows():
            frames.append({
                "frame_idx": int(row["frame_idx"]),
                "timestamp_sec": float(row["timestamp_sec"]),
                "phase": str(row.get("phase", "Unknown")),
                "is_deviation": bool(row.get("is_deviation", False)),
            })
        total_duration = frames[-1]["timestamp_sec"] if frames else 0.0
        return {
            "video_id": ann_path.stem,
            "total_duration_sec": total_duration,
            "frames": frames,
        }

    # Example 3: Pickle (numpy arrays)
    elif ann_path.suffix in (".pkl", ".pickle"):
        import pickle
        with open(ann_path, "rb") as f:
            data = pickle.load(f)
        return data

    return None


def build_video_record(
    video_id: str,
    frames_dir: str,
    ann_data: dict,
    frames_base: str,
    split: str,
) -> Optional[dict]:
    """Convert annotation dict to the BariatricFrameDataset JSON format."""

    frames_dir = Path(frames_dir)
    frames_meta = ann_data.get("frames", [])
    total_duration = ann_data.get("total_duration_sec", 0.0)

    if total_duration <= 0 or not frames_meta:
        print(f"  Skipping {video_id}: no duration or frames")
        return None

    # Build ordered phase sequence for cluster inference
    phase_sequence = []
    seen = set()
    for fm in frames_meta:
        p = fm.get("phase", "Unknown")
        if p not in seen:
            seen.add(p)
            phase_sequence.append(p)

    phase_order_cluster = infer_phase_order_cluster(phase_sequence)

    # Build frame records with RSD
    frame_records = []
    for fm in frames_meta:
        fi = fm["frame_idx"]
        timestamp = fm["timestamp_sec"]
        rsd_sec = max(0.0, total_duration - timestamp)
        rsd_norm = rsd_sec / total_duration

        # Construct relative frame path
        frame_path = f"{frames_base}/{video_id}/frame_{fi:06d}.jpg"

        frame_records.append({
            "frame_idx": fi,
            "timestamp_sec": float(timestamp),
            "rsd_sec": float(rsd_sec),
            "rsd_normalized": float(rsd_norm),
            "phase": fm.get("phase", "Unknown"),
            "is_deviation": bool(fm.get("is_deviation", False)),
            "frame_path": frame_path,
        })

    return {
        "video_id": video_id,
        "total_duration_sec": float(total_duration),
        "phase_sequence": phase_sequence,
        "phase_order_cluster": int(phase_order_cluster),
        "phase_vocab": PHASE_VOCAB,
        "split": split,
        "frames": frame_records,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ann_dir", type=str, required=True,
                        help="Directory containing per-video annotation files")
    parser.add_argument("--frames_dir", type=str, required=True,
                        help="Directory containing per-video frame directories")
    parser.add_argument("--output", type=str, default="labels/bariatric_labels.json")
    parser.add_argument("--val_fraction", type=float, default=0.1)
    parser.add_argument("--test_fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--video_dir", type=str, default=None,
                        help="If set, extract frames from raw videos first")
    parser.add_argument("--extract_frames", action="store_true")
    parser.add_argument("--fps", type=float, default=1.0,
                        help="FPS for frame extraction")
    parser.add_argument("--ann_ext", type=str, default=".json",
                        help="Annotation file extension (.json, .csv, .pkl)")
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    ann_dir = Path(args.ann_dir)
    frames_dir = Path(args.frames_dir)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Optional: extract frames first
    if args.extract_frames and args.video_dir:
        video_dir = Path(args.video_dir)
        video_files = list(video_dir.glob("*.mp4")) + list(video_dir.glob("*.avi")) + \
                      list(video_dir.glob("*.mov")) + list(video_dir.glob("*.mkv"))
        print(f"Extracting frames from {len(video_files)} videos at {args.fps} FPS...")
        for vf in tqdm(video_files):
            vid_id = vf.stem
            out_dir = frames_dir / vid_id
            if not out_dir.exists() or len(list(out_dir.glob("*.jpg"))) == 0:
                extract_frames(str(vf), str(out_dir), fps=args.fps)

    # Find all annotation files
    ann_files = sorted(ann_dir.glob(f"*{args.ann_ext}"))
    print(f"\nFound {len(ann_files)} annotation files in {ann_dir}")

    # Load and validate all videos
    all_video_ids = []
    ann_data_map = {}
    for af in tqdm(ann_files, desc="Loading annotations"):
        vid_id = af.stem
        data = load_2019_annotation(str(af))
        if data is not None:
            all_video_ids.append(vid_id)
            ann_data_map[vid_id] = data

    print(f"Valid videos: {len(all_video_ids)}")

    # Train / val / test split (by video, not by frame — avoid leakage)
    random.shuffle(all_video_ids)
    n = len(all_video_ids)
    n_test = max(1, int(n * args.test_fraction))
    n_val = max(1, int(n * args.val_fraction))
    n_train = n - n_val - n_test

    test_ids = set(all_video_ids[:n_test])
    val_ids = set(all_video_ids[n_test:n_test + n_val])
    train_ids = set(all_video_ids[n_test + n_val:])

    print(f"Split: {n_train} train / {n_val} val / {n_test} test")

    # Build records
    records = []
    frames_base = "frames"  # relative to data_root

    for vid_id in tqdm(all_video_ids, desc="Building records"):
        split = "train" if vid_id in train_ids else ("val" if vid_id in val_ids else "test")
        record = build_video_record(
            vid_id,
            str(frames_dir / vid_id),
            ann_data_map[vid_id],
            frames_base,
            split,
        )
        if record:
            records.append(record)

    print(f"\nWriting {len(records)} video records to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)

    # Summary stats
    phase_order_counts = {}
    dev_count = 0
    total_frames = 0
    for r in records:
        c = r["phase_order_cluster"]
        phase_order_counts[c] = phase_order_counts.get(c, 0) + 1
        for fm in r["frames"]:
            total_frames += 1
            if fm["is_deviation"]:
                dev_count += 1

    print(f"\nDataset summary:")
    print(f"  Videos: {len(records)}")
    print(f"  Total frames: {total_frames:,}")
    print(f"  Deviation rate: {100*dev_count/max(1,total_frames):.1f}%")
    print(f"  Phase-order cluster distribution:")
    for cluster_id, count in sorted(phase_order_counts.items()):
        print(f"    Cluster {cluster_id}: {count} videos")

    print(f"\nDone. Label file: {output_path}")


if __name__ == "__main__":
    main()

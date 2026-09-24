#!/usr/bin/env python3
"""
Extract Cholec80 frames from TFRecord files AND build labels.json for
our PyTorch training pipeline.

TFRecord schema per frame:
  frame        : bytes (PNG, 480x854x3)
  video_id     : bytes (e.g., "video01")
  frame_id     : int64 (frame index within video, 0-indexed)
  total_frames : int64 (total frames in the video)
  phase        : int64 (phase label 0..6)
  instruments  : int64[7] (tool presence bitmask)

Runs the following for each of 80 TFRecord files:
  1. Decodes PNG frames, writes them as JPEGs to {out_frames}/{video_id}/{video_id}_{frame_id:08d}.jpg
  2. Collects phase sequence + per-frame metadata
  3. Writes labels.json with the schema BariatricFrameDataset expects.

Run on Lambda:
  python3 scripts/08_build_cholec80_labels.py \
    --tfrecord_dir /lambda/nfs/bariatric-rsd/extern/cholec80/cholec80 \
    --out_frames /lambda/nfs/bariatric-rsd/extern/cholec80/frames \
    --out_labels /lambda/nfs/bariatric-rsd/labels/cholec80_labels.json
"""
import argparse
import io
import json
import sys
from pathlib import Path
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed

from PIL import Image
from tfrecord.reader import tfrecord_loader

# Cholec80's 7-phase ontology (order matches label_id 0..6)
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

DESCRIPTION = {
    "frame": "byte",
    "video_id": "byte",
    "frame_id": "int",
    "total_frames": "int",
    "phase": "int",
    "instruments": "int",
}


def process_one_tfrecord(args):
    """Decode one TFRecord: extract JPEGs + collect video metadata."""
    tfr_path, out_frames_root = args
    tfr_path = Path(tfr_path)
    out_frames_root = Path(out_frames_root)

    loader = tfrecord_loader(str(tfr_path), index_path=None, description=DESCRIPTION)

    frames_meta = []
    video_id = None
    total_frames = None
    out_dir = None

    for record in loader:
        fid = int(record["frame_id"][0] if hasattr(record["frame_id"], "__len__") else record["frame_id"])
        vid = bytes(record["video_id"]).decode("utf-8") if isinstance(record["video_id"], (bytes, memoryview, bytearray)) else str(record["video_id"])
        if video_id is None:
            video_id = vid
            out_dir = out_frames_root / video_id
            out_dir.mkdir(parents=True, exist_ok=True)
        total_frames = int(record["total_frames"][0] if hasattr(record["total_frames"], "__len__") else record["total_frames"])
        phase_id = int(record["phase"][0] if hasattr(record["phase"], "__len__") else record["phase"])
        img_bytes = bytes(record["frame"])

        # Decode PNG, save JPEG (smaller on disk, same quality for our 224×224 downstream)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        out_path = out_dir / f"{video_id}_{fid + 1:08d}.jpg"
        if not out_path.exists():
            img.save(out_path, quality=90)

        frames_meta.append({"frame_id": fid, "phase_id": phase_id})

    return video_id, total_frames, frames_meta


def build_video_entry(video_id, total_frames, frames_meta, split, frames_root):
    """Convert to project labels.json schema."""
    frames_meta.sort(key=lambda x: x["frame_id"])
    total_duration_sec = float(total_frames)  # 1 fps

    out_frames = []
    phase_sequence = []
    prev_phase_name = None
    for fm in frames_meta:
        fid = fm["frame_id"]
        phase_name = CHOLEC80_PHASES[fm["phase_id"]]
        timestamp = float(fid)
        rsd_sec = max(0.0, total_duration_sec - timestamp)
        rsd_norm = rsd_sec / total_duration_sec if total_duration_sec > 0 else 0.0
        frame_path = f"frames/{video_id}/{video_id}_{fid + 1:08d}.jpg"

        out_frames.append({
            "frame_idx": fid,
            "timestamp_sec": timestamp,
            "rsd_sec": rsd_sec,
            "rsd_normalized": rsd_norm,
            "phase": phase_name,
            "is_deviation": False,  # Cholec80 has no deviation labels
            "frame_path": frame_path,
        })
        if phase_name != prev_phase_name:
            phase_sequence.append(phase_name)
            prev_phase_name = phase_name

    return {
        "video_id": video_id,
        "total_duration_sec": total_duration_sec,
        "phase_sequence": phase_sequence,
        "phase_vocab": dict(PHASE_VOCAB),
        "phase_order_cluster": 0,
        "split": split,
        "frames": out_frames,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tfrecord_dir", required=True, help="Dir containing the 80 .tfrecord files")
    ap.add_argument("--out_frames", required=True, help="Output dir for extracted JPEG frames")
    ap.add_argument("--out_labels", required=True, help="Output labels.json path")
    ap.add_argument("--n_workers", type=int, default=8)
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    args = ap.parse_args()

    sys.path.insert(0, args.project_src)
    from data.dataset import infer_phase_order_cluster  # type: ignore

    tfr_dir = Path(args.tfrecord_dir)
    tfr_files = sorted(tfr_dir.glob("*.tfrecord")) or sorted(tfr_dir.glob("video*"))
    print(f"Found {len(tfr_files)} TFRecord files in {tfr_dir}")
    if not tfr_files:
        raise SystemExit(f"No TFRecord files found in {tfr_dir}")

    out_frames = Path(args.out_frames)
    out_frames.mkdir(parents=True, exist_ok=True)

    # Parallel TFRecord decoding
    results = {}
    with ProcessPoolExecutor(max_workers=args.n_workers) as pool:
        futures = {pool.submit(process_one_tfrecord, (str(p), str(out_frames))): p for p in tfr_files}
        for i, fut in enumerate(as_completed(futures), 1):
            p = futures[fut]
            try:
                video_id, total_frames, frames_meta = fut.result()
                results[video_id] = (total_frames, frames_meta)
                print(f"[{i}/{len(tfr_files)}] {video_id}: {len(frames_meta)} frames, total={total_frames}")
            except Exception as e:
                print(f"ERROR on {p}: {e}", file=sys.stderr)

    # Standard Cholec80 split: videos 01-40 train, 41-48 val, 49-80 test
    # (EndoNet paper convention; re-check if paper uses different split)
    def split_for(video_id):
        n = int(video_id.replace("video", ""))
        if n <= 40:
            return "train"
        elif n <= 48:
            return "val"
        else:
            return "test"

    videos = []
    for video_id, (total_frames, frames_meta) in sorted(results.items()):
        split = split_for(video_id)
        entry = build_video_entry(video_id, total_frames, frames_meta, split, out_frames)
        entry["phase_order_cluster"] = infer_phase_order_cluster(entry["phase_sequence"])
        videos.append(entry)

    split_counts = {}
    for v in videos:
        split_counts[v["split"]] = split_counts.get(v["split"], 0) + 1
    print(f"\nTotal videos: {len(videos)}")
    print(f"Split counts: {split_counts}")
    print(f"Total frames: {sum(len(v['frames']) for v in videos):,}")

    out_path = Path(args.out_labels)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(videos, f)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

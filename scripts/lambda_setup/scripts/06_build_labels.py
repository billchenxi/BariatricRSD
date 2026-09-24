#!/usr/bin/env python3
"""
Build labels.json for BariatricFrameDataset from MultiBypass140's
CAMMA pickle labels (multibypass06_corrected/labels/{center}/labels/{split}/*.pickle).

Run on Lambda:
  python3 scripts/06_build_labels.py --fold 0 --output labels/mb140_fold0_labels.json
"""
import argparse
import json
import pickle
import sys
from pathlib import Path
from collections import OrderedDict

# Map MB140 phase names -> project ontology (used by infer_phase_order_cluster)
MB140_TO_PROJECT = {
    "preparation": "Preparation",
    "gastric_pouch_creation": "Gastric pouch creation",
    "omentum_division": "Omentum division",
    "gastrojejunal_anastomosis": "Gastro-jejunal anastomosis",
    "anastomosis_test": "Leak test",
    "jejunal_separation": "Jejunal division",
    "closure_petersen_space": "Closure of petersen's space",
    "jejunojejunal_anastomosis": "Jejuno-jejunal anastomosis",
    "closure_mesenteric_defect": "Closure of mesenteric defect",
    "cleaning_coagulation": "Cleaning/coagulation",
    "disassembling": "Disassembling",
    "other_intervention": "Other intervention",
    "out_of_body": "Out of body",
    "severe_index": "Unknown",
}

# Reverse lookup from label_id -> original mb140 name, built from per-video JSONs
PHASE_ID_TO_NAME = {
    0: "preparation",
    1: "gastric_pouch_creation",
    2: "omentum_division",
    3: "gastrojejunal_anastomosis",
    4: "anastomosis_test",
    5: "jejunal_separation",
    6: "closure_petersen_space",
    7: "jejunojejunal_anastomosis",
    8: "closure_mesenteric_defect",
    9: "cleaning_coagulation",
    10: "disassembling",
    11: "other_intervention",
    12: "out_of_body",
    13: "severe_index",
}

PHASE_VOCAB = OrderedDict(
    (MB140_TO_PROJECT[PHASE_ID_TO_NAME[i]], i) for i in range(len(PHASE_ID_TO_NAME))
)


def load_pickles(labels_root: Path, center: str, fold: int):
    """Return {video_id: (split, frames_list)}."""
    out = {}
    # Training pickle filename pattern includes percentage: 1fps_100_<fold>_with_iae.pickle
    # Val/test: 1fps_<fold>_with_iae.pickle
    pickle_files = [
        ("train", f"1fps_100_{fold}_with_iae.pickle"),
        ("val", f"1fps_{fold}_with_iae.pickle"),
        ("test", f"1fps_{fold}_with_iae.pickle"),
    ]
    for split, fname in pickle_files:
        path = labels_root / center / "labels" / split / fname
        with open(path, "rb") as f:
            data = pickle.load(f)
        for vid, frames in data.items():
            # In case a video appears in multiple splits, last one wins (shouldn't happen normally)
            out[vid] = (split, frames)
    return out


def build_video_entry(video_id: str, split: str, frames: list, center_key: str):
    """Convert one video's frame list to the project labels.json schema."""
    if len(frames) == 0:
        return None

    # Use 1 sec per frame at 1 fps. Duration = max frame index in seconds.
    # Frame_id is 1-indexed; use the last frame's index as duration upper bound.
    last_idx = int(frames[-1]["Frame_id"])
    total_duration_sec = float(last_idx)

    out_frames = []
    phase_sequence = []
    prev_phase = None

    for fm in frames:
        frame_idx = int(fm["Frame_id"])  # 1-indexed
        timestamp_sec = float(frame_idx)  # 1 fps
        rsd_sec = max(0.0, total_duration_sec - timestamp_sec)
        rsd_norm = rsd_sec / total_duration_sec if total_duration_sec > 0 else 0.0

        mb_name = PHASE_ID_TO_NAME.get(int(fm["Phase_gt"]), "severe_index")
        phase_name = MB140_TO_PROJECT[mb_name]

        is_deviation = int(fm.get("Overall", 0)) > 0

        # Frame path: {center}/frames/{vid}/{vid}_00000014.jpg
        frame_path = f"{center_key}/frames/{video_id}/{video_id}_{frame_idx:08d}.jpg"

        out_frames.append({
            "frame_idx": frame_idx - 1,          # 0-indexed for downstream code
            "timestamp_sec": timestamp_sec,
            "rsd_sec": rsd_sec,
            "rsd_normalized": rsd_norm,
            "phase": phase_name,
            "is_deviation": is_deviation,
            "frame_path": frame_path,
        })

        if phase_name != prev_phase:
            phase_sequence.append(phase_name)
            prev_phase = phase_name

    return {
        "video_id": video_id,
        "total_duration_sec": total_duration_sec,
        "phase_sequence": phase_sequence,
        "phase_vocab": dict(PHASE_VOCAB),
        "phase_order_cluster": 0,   # filled later
        "split": split,
        "frames": out_frames,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset_root", default="/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140")
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--output", required=True)
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src",
                    help="Path to project src dir (for importing infer_phase_order_cluster)")
    args = ap.parse_args()

    sys.path.insert(0, args.project_src)
    from data.dataset import infer_phase_order_cluster  # type: ignore

    root = Path(args.dataset_root)
    labels_root = root / "multibypass06_corrected" / "labels"

    videos = []
    for center, center_key in [("bern", "BernBypass70"), ("strasbourg", "StrasBypass70")]:
        print(f"[{center}] loading fold {args.fold}...")
        by_vid = load_pickles(labels_root, center, args.fold)
        print(f"  {len(by_vid)} videos")
        for vid, (split, frames) in sorted(by_vid.items()):
            entry = build_video_entry(vid, split, frames, center_key)
            if entry is None:
                continue
            entry["phase_order_cluster"] = infer_phase_order_cluster(entry["phase_sequence"])
            videos.append(entry)

    # Summary
    split_counts = {}
    cluster_counts = {}
    for v in videos:
        split_counts[v["split"]] = split_counts.get(v["split"], 0) + 1
        cluster_counts[v["phase_order_cluster"]] = cluster_counts.get(v["phase_order_cluster"], 0) + 1
    print(f"\nTotal videos: {len(videos)}")
    print(f"Split counts: {split_counts}")
    print(f"Phase-order cluster counts: {cluster_counts}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(videos, f)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

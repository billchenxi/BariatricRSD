"""
src/data/dataset.py

PyTorch Dataset for the bariatric RSD project.
Handles three data sources:
  1. Your private 4000+ video bariatric dataset
  2. MultiBypass140 (BernBypass70 / StrasBypass70)
  3. Cholec80 (for RSD comparison against TransLocal)
"""

import os
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T
from PIL import Image

try:
    import av
    AV_AVAILABLE = True
except ImportError:
    AV_AVAILABLE = False

try:
    from decord import VideoReader, cpu
    DECORD_AVAILABLE = True
except ImportError:
    DECORD_AVAILABLE = False


# ── Phase-order cluster mapping ────────────────────────────────────────────────
# From the 2019 slides: 8 distinct RYGB phase orderings observed in your data.
# Key: frozenset of (phase_name, position) tuples  →  cluster_id [0..7]

PHASE_ORDER_CLUSTERS = {
    # Cluster 0: standard order (most common, 181/242 videos)
    # Gastric Pouch → Gastro-Jejunal → Jejuno-Jejunal
    "GC_GJ_JJ": 0,
    # Cluster 1: JJ before GJ
    "GC_JJ_GJ": 1,
    # Cluster 2: GJ first (rare, 1 video)
    "GJ_JJ_GC": 2,
    # Cluster 3: JJ first
    "JJ_GC_GJ": 3,
    # Cluster 4: with Roux limb measurement - standard
    "GC_GJ_Roux_JJ": 4,
    # Cluster 5: with Roux - JJ before GJ
    "GC_JJ_Roux_GJ": 5,
    # Cluster 6: Roux first
    "Roux_JJ_GC_GJ": 6,
    # Cluster 7: other / unknown ordering
    "UNKNOWN": 7,
}
NUM_PHASE_ORDER_CLUSTERS = 8


def infer_phase_order_cluster(phase_sequence: List[str]) -> int:
    """Map a list of phase names (in order of first appearance) to a cluster ID."""
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for p in phase_sequence:
        if p not in seen:
            seen.add(p)
            deduped.append(p)

    # Build a compact key
    abbrev = {
        "Gastric pouch creation": "GC",
        "Gastro-jejunal anastomosis": "GJ",
        "Jejuno-jejunal anastomosis": "JJ",
        "Alimentary (roux) limb measurement": "Roux",
        "Biliopancreatic limb measurement": "BP",
        "Closure of mesenteric defect": "CMD",
    }
    key = "_".join(abbrev.get(p, p[:3]) for p in deduped)

    for cluster_key, cluster_id in PHASE_ORDER_CLUSTERS.items():
        if cluster_key in key or key.startswith(cluster_key):
            return cluster_id
    return PHASE_ORDER_CLUSTERS["UNKNOWN"]


# ── Video frame sampling ───────────────────────────────────────────────────────

def sample_frames_uniform(
    video_path: str,
    num_frames: int = 8,
    start_sec: float = 0.0,
    end_sec: Optional[float] = None,
) -> torch.Tensor:
    """
    Sample num_frames uniformly from [start_sec, end_sec] of a video.
    Returns tensor of shape [num_frames, C, H, W] in range [0, 1].
    """
    if DECORD_AVAILABLE:
        return _sample_decord(video_path, num_frames, start_sec, end_sec)
    elif AV_AVAILABLE:
        return _sample_av(video_path, num_frames, start_sec, end_sec)
    else:
        raise RuntimeError("Install decord or av: pip install decord av")


def _sample_decord(video_path, num_frames, start_sec, end_sec):
    vr = VideoReader(video_path, ctx=cpu(0))
    fps = vr.get_avg_fps()
    total_frames = len(vr)
    duration = total_frames / fps

    end_sec = end_sec or duration
    start_frame = int(start_sec * fps)
    end_frame = min(int(end_sec * fps), total_frames - 1)

    indices = np.linspace(start_frame, end_frame, num_frames, dtype=int)
    indices = np.clip(indices, 0, total_frames - 1)

    frames = vr.get_batch(indices).asnumpy()  # [T, H, W, C]
    frames = torch.from_numpy(frames).permute(0, 3, 1, 2).float() / 255.0
    return frames


def _sample_av(video_path, num_frames, start_sec, end_sec):
    frames = []
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        fps = float(stream.average_rate)
        duration = float(stream.duration * stream.time_base) if stream.duration else None

        end_sec = end_sec or duration or 1e9
        target_times = np.linspace(start_sec, end_sec, num_frames)

        container.seek(int(start_sec * av.time_base), any_frame=True)
        current_targets = list(target_times)

        for packet in container.demux(stream):
            if not current_targets:
                break
            for frame in packet.decode():
                t = float(frame.pts * stream.time_base)
                if t >= current_targets[0] - 0.1:
                    img = frame.to_image().convert("RGB")
                    frames.append(np.array(img))
                    current_targets.pop(0)
                    if not current_targets:
                        break

    if not frames:
        raise ValueError(f"No frames extracted from {video_path}")

    # Pad if needed
    while len(frames) < num_frames:
        frames.append(frames[-1])

    frames = np.stack(frames[:num_frames])  # [T, H, W, C]
    frames = torch.from_numpy(frames).permute(0, 3, 1, 2).float() / 255.0
    return frames


# ── Frame-level dataset (for pre-extracted frames) ───────────────────────────

class BariatricFrameDataset(Dataset):
    """
    Loads pre-extracted frames (faster than decoding video each time).
    
    Expects a label JSON with this structure per video:
    {
        "video_id": "3361",
        "total_duration_sec": 4800.0,
        "phase_sequence": ["Gastric pouch creation", "Gastro-jejunal anastomosis", ...],
        "phase_order_cluster": 0,
        "frames": [
            {
                "frame_idx": 0,
                "timestamp_sec": 0.0,
                "rsd_sec": 4800.0,
                "rsd_normalized": 1.0,
                "phase": "Gastric pouch creation",
                "is_deviation": false,
                "frame_path": "frames/3361/frame_000000.jpg"
            },
            ...
        ]
    }
    """

    def __init__(
        self,
        label_json: str,
        data_root: str,
        split: str = "train",           # train / val / test
        sequence_len: int = 8,          # frames per sample
        frame_stride: int = 5,          # sample every N frames
        img_size: int = 224,
        augment: bool = True,
        max_videos: Optional[int] = None,
        target_position: str = "middle",  # "middle" (legacy) or "last" (strict prefix-only)
    ):
        self.data_root = Path(data_root)
        self.sequence_len = sequence_len
        self.frame_stride = frame_stride
        self.augment = augment and split == "train"
        if target_position not in {"middle", "last"}:
            raise ValueError(
                f"target_position must be 'middle' or 'last', got {target_position!r}"
            )
        self.target_position = target_position

        with open(label_json) as f:
            all_data = json.load(f)

        # Filter by split
        self.videos = [v for v in all_data if v.get("split", "train") == split]
        if max_videos:
            self.videos = self.videos[:max_videos]

        # Build flat index: list of (video_idx, start_frame_idx)
        self.samples = []
        for v_idx, video in enumerate(self.videos):
            frames = video["frames"]
            # Step through the video, sampling windows
            for start in range(0, len(frames) - sequence_len * frame_stride, frame_stride):
                self.samples.append((v_idx, start))

        # Transforms
        if augment:
            self.transform = T.Compose([
                T.RandomResizedCrop(img_size, scale=(0.8, 1.0)),
                T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
                T.RandomHorizontalFlip(p=0.3),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        else:
            self.transform = T.Compose([
                T.Resize((img_size, img_size)),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])

        print(f"BariatricFrameDataset [{split}]: {len(self.videos)} videos, {len(self.samples)} samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx) -> Dict[str, torch.Tensor]:
        v_idx, start = self.samples[idx]
        video = self.videos[v_idx]
        frames_meta = video["frames"]

        # Sample sequence_len frames with stride
        frame_indices = [start + i * self.frame_stride for i in range(self.sequence_len)]
        frame_indices = [min(f, len(frames_meta) - 1) for f in frame_indices]

        # Load frames
        frame_tensors = []
        for fi in frame_indices:
            frame_meta = frames_meta[fi]
            img_path = self.data_root / frame_meta["frame_path"]
            img = Image.open(img_path).convert("RGB")
            img_t = T.ToTensor()(img)  # [C, H, W] in [0,1]
            img_t = self.transform(img_t)
            frame_tensors.append(img_t)

        frames = torch.stack(frame_tensors)  # [T, C, H, W]

        # Labels from the configured target frame of the sequence.
        # "middle" preserves the legacy centered-window protocol; "last"
        # makes the clip end exactly at the prediction timestamp.
        if self.target_position == "last":
            mid = frame_indices[-1]
        else:
            mid = frame_indices[len(frame_indices) // 2]
        mid_meta = frames_meta[mid]

        rsd_normalized = torch.tensor(mid_meta["rsd_normalized"], dtype=torch.float32)
        rsd_sec = torch.tensor(mid_meta["rsd_sec"], dtype=torch.float32)
        is_deviation = torch.tensor(float(mid_meta["is_deviation"]), dtype=torch.float32)
        phase_order_cluster = torch.tensor(video["phase_order_cluster"], dtype=torch.long)

        # Phase label (integer index into your phase vocabulary)
        phase_vocab = video.get("phase_vocab", {})
        phase_name = mid_meta.get("phase", "Unknown")
        phase_label = torch.tensor(phase_vocab.get(phase_name, 0), dtype=torch.long)

        return {
            "frames": frames,                         # [T, C, H, W]
            "rsd_normalized": rsd_normalized,         # scalar [0, 1]
            "rsd_sec": rsd_sec,                       # scalar (seconds)
            "is_deviation": is_deviation,             # scalar 0/1
            "phase_order_cluster": phase_order_cluster, # int [0..7]
            "phase_label": phase_label,               # int
            "video_id": video["video_id"],            # str
            "timestamp_sec": torch.tensor(mid_meta["timestamp_sec"], dtype=torch.float32),
            "target_frame_idx": torch.tensor(mid_meta["frame_idx"], dtype=torch.long),
            "target_frame_path": mid_meta["frame_path"],
        }


# ── MultiBypass140 adapter ────────────────────────────────────────────────────

class MultiBypass140Dataset(Dataset):
    """
    Adapter for the MultiBypass140 benchmark (BernBypass70 / StrasBypass70).
    Uses the official 5-fold cross-validation splits from the repo.
    
    Download instructions:
      git clone https://github.com/CAMMA-public/MultiBypass140
      # Fill the data request form in the README
    """

    # Map MultiBypass140's 12-phase ontology to phase-order cluster IDs
    # (approximate mapping — refine once you see the actual phase sequence distributions)
    MB140_PHASES = [
        "Preparation", "Liver retraction", "Access & dissection",
        "Gastric pouch creation", "Gastro-jejunal anastomosis",
        "Jejuno-jejunal anastomosis", "Alimentary limb measurement",
        "Biliopancreatic limb measurement", "Leak test",
        "Closure of mesenteric defect", "Drain placement", "End"
    ]
    PHASE2IDX = {p: i for i, p in enumerate(MB140_PHASES)}

    def __init__(
        self,
        data_root: str,           # path to MultiBypass140 frames
        split_file: str,          # path to official split JSON from the repo
        center: str = "bern",     # "bern" or "strasbourg"
        fold: int = 0,            # 0..4
        split: str = "test",
        sequence_len: int = 8,
        frame_stride: int = 5,
        img_size: int = 224,
    ):
        self.data_root = Path(data_root)
        self.sequence_len = sequence_len
        self.frame_stride = frame_stride

        with open(split_file) as f:
            splits = json.load(f)

        # Filter videos by center and split
        center_key = "BernBypass70" if center == "bern" else "StrasBypass70"
        video_ids = splits.get(center_key, {}).get(f"fold_{fold}", {}).get(split, [])

        # Load frame-level annotations
        self.samples = []
        ann_dir = self.data_root / "annotations" / center_key
        for vid in video_ids:
            ann_file = ann_dir / f"{vid}_labels.json"
            if ann_file.exists():
                with open(ann_file) as f:
                    ann = json.load(f)
                frames = ann["frames"]
                for start in range(0, len(frames) - sequence_len * frame_stride, frame_stride):
                    self.samples.append((vid, ann, start))

        self.transform = T.Compose([
            T.Resize((img_size, img_size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        print(f"MultiBypass140 [{center}/{split}]: {len(video_ids)} videos, {len(self.samples)} samples")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        vid, ann, start = self.samples[idx]
        frames_meta = ann["frames"]
        total_duration = ann["duration_sec"]

        indices = [min(start + i * self.frame_stride, len(frames_meta) - 1)
                   for i in range(self.sequence_len)]

        frame_tensors = []
        for fi in indices:
            img_path = self.data_root / "frames" / vid / f"frame_{fi:06d}.jpg"
            img = Image.open(img_path).convert("RGB")
            frame_tensors.append(self.transform(img))

        frames = torch.stack(frame_tensors)

        mid = indices[len(indices) // 2]
        mid_meta = frames_meta[mid]
        timestamp = mid_meta["timestamp_sec"]
        rsd_sec = total_duration - timestamp
        rsd_normalized = rsd_sec / total_duration if total_duration > 0 else 0.0

        phase_name = mid_meta.get("phase", "Preparation")
        phase_label = self.PHASE2IDX.get(phase_name, 0)

        # Infer phase-order cluster from the video's phase sequence
        phase_seq = [f["phase"] for f in frames_meta]
        phase_order_cluster = infer_phase_order_cluster(phase_seq)

        return {
            "frames": frames,
            "rsd_normalized": torch.tensor(rsd_normalized, dtype=torch.float32),
            "rsd_sec": torch.tensor(rsd_sec, dtype=torch.float32),
            "is_deviation": torch.tensor(0.0, dtype=torch.float32),  # MB140 uses IAE labels separately
            "phase_order_cluster": torch.tensor(phase_order_cluster, dtype=torch.long),
            "phase_label": torch.tensor(phase_label, dtype=torch.long),
            "video_id": vid,
            "timestamp_sec": torch.tensor(timestamp, dtype=torch.float32),
        }


# ── DataLoader factory ────────────────────────────────────────────────────────

def get_dataloader(dataset: Dataset, split: str, batch_size: int = 8, num_workers: int = 4):
    from torch.utils.data import DataLoader
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=(split == "train"),
        num_workers=num_workers,
        pin_memory=True,
        drop_last=(split == "train"),
        persistent_workers=(num_workers > 0),
    )

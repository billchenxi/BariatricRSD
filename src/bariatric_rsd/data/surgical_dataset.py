"""
Surgical Video Dataset
======================
PyTorch Dataset classes for loading surgical video frames with multi-task labels:
  - RSD (Remaining Surgery Duration) as normalized progress [0, 1]
  - Phase labels (multi-class)
  - Deviation labels (binary)

This replaces the proprietary DurrationDataset, VideoClassificationDataset,
and customData classes from the 2019 codebase with a clean, unified implementation
built entirely on standard PyTorch and open-source libraries.
"""

import os
import glob
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, SubsetRandomSampler
from torchvision import transforms
from PIL import Image

from bariatric_rsd.data.annotation_parser import AnnotationDict


def filename_to_seconds(filename: str) -> float:
    """
    Extract timestamp in seconds from a surgical video frame filename.

    Expected format: PREFIX_MM-SS-mmm.ext (minutes-seconds-milliseconds)
    """
    basename = os.path.basename(filename)
    # Try the common format: something_MM-SS-mmm.jpg
    time_part = basename.rsplit("_", 1)[-1].split(".")[0]
    parts = time_part.split("-")
    if len(parts) == 3:
        minutes, seconds, millis = parts
        return float(minutes) * 60 + float(seconds) + float(millis) / 1000
    elif len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    else:
        # Fallback: try to parse as pure seconds
        return float(time_part)


def default_image_loader(path: str) -> Optional[Image.Image]:
    """Load an image from disk, converting to RGB."""
    try:
        img = Image.open(path)
        return img.convert("RGB")
    except Exception as e:
        print(f"Cannot read image: {path} ({e})")
        return None


class SurgicalVideoDataset(Dataset):
    """
    Dataset for surgical video frame-level prediction tasks.

    Loads individual frames from surgical videos and provides:
      - Image tensor (transformed)
      - RSD label: normalized progress through the video [0.0 = start, 1.0 = end]
      - Phase label: integer class ID for the current surgical phase
      - Deviation label: binary flag (0 = normal, 1 = deviation)
      - Phase-order cluster ID: integer encoding of the video's phase ordering

    This is a frame-level dataset. For temporal (clip-level) loading,
    use SurgicalClipDataset instead.
    """

    def __init__(
        self,
        video_root: str,
        annotation_dict: AnnotationDict,
        video_ids: List[str],
        phase_names: List[str],
        phase_order_clusters: Optional[Dict[str, int]] = None,
        deviation_annotations: Optional[Dict[str, List[Tuple[float, float]]]] = None,
        transform: Optional[Callable] = None,
        remove_out_of_body: bool = True,
        frame_extension: str = "jpg",
        return_metadata: bool = False,
    ):
        """
        Args:
            video_root: Root directory containing per-video frame folders.
            annotation_dict: Parsed annotation dictionary.
            video_ids: List of video IDs to include.
            phase_names: Ordered list of surgical phase names.
            phase_order_clusters: Video ID -> cluster ID mapping.
            deviation_annotations: Video ID -> list of (start_sec, end_sec) deviation segments.
            transform: Torchvision transforms for image preprocessing.
            remove_out_of_body: Whether to exclude out-of-body frames.
            frame_extension: Image file extension.
            return_metadata: If True, also return frame path and video ID.
        """
        self.video_root = video_root
        self.annotation_dict = annotation_dict
        self.phase_names = phase_names
        self.phase_to_idx = {name: i for i, name in enumerate(phase_names)}
        self.phase_order_clusters = phase_order_clusters or {}
        self.deviation_annotations = deviation_annotations or {}
        self.transform = transform
        self.remove_out_of_body = remove_out_of_body
        self.frame_extension = frame_extension
        self.return_metadata = return_metadata
        self.loader = default_image_loader

        # Build the frame index
        self.frame_paths: List[str] = []
        self.rsd_labels: List[float] = []
        self.phase_labels: List[int] = []
        self.deviation_labels: List[int] = []
        self.cluster_ids: List[int] = []
        self.video_id_per_frame: List[str] = []

        self._build_index(video_ids)

    def _build_index(self, video_ids: List[str]):
        """Build the flat index of all frames across all videos."""
        available_dirs = set(os.listdir(self.video_root))

        for vid in video_ids:
            if vid not in available_dirs:
                continue
            if vid not in self.annotation_dict:
                continue

            video_dir = os.path.join(self.video_root, vid)
            frame_files = sorted(
                glob.glob(os.path.join(video_dir, f"*.{self.frame_extension}"))
            )
            if not frame_files:
                continue

            # Determine valid frame range (excluding out-of-body)
            frame_files = self._filter_out_of_body(frame_files, vid)
            if not frame_files:
                continue

            num_frames = len(frame_files)
            cluster_id = self.phase_order_clusters.get(vid, 0)

            # Generate RSD labels: linear interpolation [0, 1]
            rsd_values = np.linspace(0.0, 1.0, num_frames).tolist()

            # Get deviation segments for this video
            dev_segments = self.deviation_annotations.get(vid, [])

            for i, fpath in enumerate(frame_files):
                self.frame_paths.append(fpath)
                self.rsd_labels.append(rsd_values[i])
                self.phase_labels.append(
                    self._get_phase_label(fpath, vid)
                )
                self.deviation_labels.append(
                    self._get_deviation_label(fpath, dev_segments)
                )
                self.cluster_ids.append(cluster_id)
                self.video_id_per_frame.append(vid)

    def _filter_out_of_body(
        self, frame_files: List[str], video_id: str
    ) -> List[str]:
        """Remove frames that occur during out-of-body camera segments."""
        if not self.remove_out_of_body:
            return frame_files

        annotations = self.annotation_dict.get(video_id, {})
        oob_info = annotations.get("Out of body")
        if oob_info is None:
            return frame_files

        oob_starts = sorted(oob_info["start"])
        oob_ends = sorted(oob_info["end"])

        # Find the effective start: end of last OOB before first surgical phase
        other_phases = {k: v for k, v in annotations.items() if k != "Out of body"}
        if not other_phases:
            return frame_files

        earliest_phase_start = min(
            min(v["start"]) for v in other_phases.values() if v["start"]
        )
        latest_phase_end = max(
            max(v["end"]) for v in other_phases.values() if v["end"]
        )

        # Find effective video boundaries
        effective_start = 0.0
        for oob_end in oob_ends:
            if oob_end < earliest_phase_start:
                effective_start = oob_end

        effective_end = float("inf")
        for oob_start in oob_starts:
            if oob_start > latest_phase_end:
                effective_end = oob_start
                break

        # Filter frames by timestamp
        filtered = []
        for fpath in frame_files:
            try:
                t = filename_to_seconds(fpath)
                if effective_start <= t <= effective_end:
                    filtered.append(fpath)
            except (ValueError, IndexError):
                filtered.append(fpath)  # keep if timestamp can't be parsed

        return filtered if filtered else frame_files

    def _get_phase_label(self, frame_path: str, video_id: str) -> int:
        """Determine the surgical phase for a given frame."""
        try:
            frame_time = filename_to_seconds(frame_path)
        except (ValueError, IndexError):
            return 0  # default to first phase

        annotations = self.annotation_dict.get(video_id, {})
        for phase_name in self.phase_names:
            if phase_name not in annotations:
                continue
            starts = annotations[phase_name]["start"]
            ends = annotations[phase_name]["end"]
            for s, e in zip(starts, ends):
                if s <= frame_time <= e:
                    return self.phase_to_idx[phase_name]

        return 0  # default

    def _get_deviation_label(
        self,
        frame_path: str,
        deviation_segments: List[Tuple[float, float]],
    ) -> int:
        """Determine if a frame falls within a deviation segment."""
        if not deviation_segments:
            return 0
        try:
            frame_time = filename_to_seconds(frame_path)
        except (ValueError, IndexError):
            return 0

        for start, end in deviation_segments:
            if start <= frame_time <= end:
                return 1
        return 0

    def __len__(self) -> int:
        return len(self.frame_paths)

    def __getitem__(self, index: int) -> dict:
        img = self.loader(self.frame_paths[index])
        if img is None:
            # Return a black image as fallback
            img = Image.new("RGB", (224, 224), (0, 0, 0))

        if self.transform is not None:
            img = self.transform(img)

        sample = {
            "image": img,
            "rsd": torch.tensor(self.rsd_labels[index], dtype=torch.float32),
            "phase": torch.tensor(self.phase_labels[index], dtype=torch.long),
            "deviation": torch.tensor(
                self.deviation_labels[index], dtype=torch.float32
            ),
            "cluster_id": torch.tensor(self.cluster_ids[index], dtype=torch.long),
        }

        if self.return_metadata:
            sample["frame_path"] = self.frame_paths[index]
            sample["video_id"] = self.video_id_per_frame[index]

        return sample


class SurgicalClipDataset(Dataset):
    """
    Dataset that loads temporal clips (sequences of frames) for
    Transformer-based temporal modeling.

    Each sample is a clip of consecutive frames from a single video,
    suitable for input to the Surgformer HTA temporal model.
    """

    def __init__(
        self,
        video_root: str,
        annotation_dict: AnnotationDict,
        video_ids: List[str],
        phase_names: List[str],
        clip_length: int = 16,
        sampling_rate: int = 4,
        phase_order_clusters: Optional[Dict[str, int]] = None,
        deviation_annotations: Optional[Dict[str, List[Tuple[float, float]]]] = None,
        transform: Optional[Callable] = None,
        remove_out_of_body: bool = True,
        frame_extension: str = "jpg",
    ):
        """
        Args:
            video_root: Root directory containing per-video frame folders.
            annotation_dict: Parsed annotation dictionary.
            video_ids: List of video IDs to include.
            phase_names: Ordered list of surgical phase names.
            clip_length: Number of frames per clip.
            sampling_rate: Sample every Nth frame within the clip window.
            phase_order_clusters: Video ID -> cluster ID mapping.
            deviation_annotations: Video ID -> deviation segments.
            transform: Torchvision transforms for each frame.
            remove_out_of_body: Whether to exclude out-of-body frames.
            frame_extension: Image file extension.
        """
        self.video_root = video_root
        self.annotation_dict = annotation_dict
        self.phase_names = phase_names
        self.phase_to_idx = {name: i for i, name in enumerate(phase_names)}
        self.clip_length = clip_length
        self.sampling_rate = sampling_rate
        self.phase_order_clusters = phase_order_clusters or {}
        self.deviation_annotations = deviation_annotations or {}
        self.transform = transform
        self.remove_out_of_body = remove_out_of_body
        self.frame_extension = frame_extension
        self.loader = default_image_loader

        # Build clip-level index
        self.clips: List[dict] = []
        self._build_clips(video_ids)

    def _build_clips(self, video_ids: List[str]):
        """Build clip index by sliding window over each video."""
        available_dirs = set(os.listdir(self.video_root))

        for vid in video_ids:
            if vid not in available_dirs or vid not in self.annotation_dict:
                continue

            video_dir = os.path.join(self.video_root, vid)
            frame_files = sorted(
                glob.glob(os.path.join(video_dir, f"*.{self.frame_extension}"))
            )
            if not frame_files:
                continue

            # Filter out-of-body frames
            if self.remove_out_of_body:
                frame_dataset = SurgicalVideoDataset.__new__(SurgicalVideoDataset)
                frame_dataset.remove_out_of_body = True
                frame_dataset.annotation_dict = self.annotation_dict
                frame_files = frame_dataset._filter_out_of_body(frame_files, vid)

            num_frames = len(frame_files)
            window_size = self.clip_length * self.sampling_rate

            if num_frames < window_size:
                continue

            # Compute RSD for all frames
            rsd_values = np.linspace(0.0, 1.0, num_frames)
            cluster_id = self.phase_order_clusters.get(vid, 0)

            # Create clips with stride = clip_length (non-overlapping)
            stride = self.clip_length
            for start_idx in range(0, num_frames - window_size + 1, stride):
                # Sample frames from the window
                frame_indices = list(
                    range(start_idx, start_idx + window_size, self.sampling_rate)
                )[: self.clip_length]

                clip_frames = [frame_files[i] for i in frame_indices]
                # Use the label of the LAST frame in the clip as the target
                target_idx = frame_indices[-1]

                self.clips.append(
                    {
                        "video_id": vid,
                        "frame_paths": clip_frames,
                        "rsd": float(rsd_values[target_idx]),
                        "target_frame": frame_files[target_idx],
                        "cluster_id": cluster_id,
                    }
                )

    def __len__(self) -> int:
        return len(self.clips)

    def __getitem__(self, index: int) -> dict:
        clip_info = self.clips[index]
        vid = clip_info["video_id"]

        # Load and transform all frames in the clip
        frames = []
        for fpath in clip_info["frame_paths"]:
            img = self.loader(fpath)
            if img is None:
                img = Image.new("RGB", (224, 224), (0, 0, 0))
            if self.transform is not None:
                img = self.transform(img)
            frames.append(img)

        # Stack into (T, C, H, W)
        clip_tensor = torch.stack(frames, dim=0)

        # Get phase label from the target (last) frame
        phase_label = self._get_phase_label(
            clip_info["target_frame"], vid
        )

        # Get deviation label
        dev_segments = self.deviation_annotations.get(vid, [])
        dev_label = self._get_deviation_label(
            clip_info["target_frame"], dev_segments
        )

        return {
            "clip": clip_tensor,  # (T, C, H, W)
            "rsd": torch.tensor(clip_info["rsd"], dtype=torch.float32),
            "phase": torch.tensor(phase_label, dtype=torch.long),
            "deviation": torch.tensor(dev_label, dtype=torch.float32),
            "cluster_id": torch.tensor(clip_info["cluster_id"], dtype=torch.long),
        }

    def _get_phase_label(self, frame_path: str, video_id: str) -> int:
        """Determine the surgical phase for a given frame."""
        try:
            frame_time = filename_to_seconds(frame_path)
        except (ValueError, IndexError):
            return 0
        annotations = self.annotation_dict.get(video_id, {})
        for phase_name in self.phase_names:
            if phase_name not in annotations:
                continue
            for s, e in zip(
                annotations[phase_name]["start"],
                annotations[phase_name]["end"],
            ):
                if s <= frame_time <= e:
                    return self.phase_to_idx[phase_name]
        return 0

    def _get_deviation_label(
        self,
        frame_path: str,
        deviation_segments: List[Tuple[float, float]],
    ) -> int:
        """Determine if a frame falls within a deviation segment."""
        if not deviation_segments:
            return 0
        try:
            frame_time = filename_to_seconds(frame_path)
        except (ValueError, IndexError):
            return 0
        for start, end in deviation_segments:
            if start <= frame_time <= end:
                return 1
        return 0


def get_standard_transforms(
    image_size: int = 224,
    is_training: bool = True,
) -> transforms.Compose:
    """
    Get standard image transforms for surgical video frames.

    Uses ImageNet normalization statistics.
    """
    if is_training:
        return transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomAffine(
                    degrees=5, translate=(0.08, 0.08), shear=2
                ),
                transforms.ColorJitter(
                    brightness=0.2, contrast=0.2, saturation=0.1
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
    else:
        return transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )


def create_data_splits(
    video_ids: List[str],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    seed: int = 444,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Split video IDs into train/val/test sets.

    Args:
        video_ids: List of all video IDs.
        train_ratio: Fraction for training.
        val_ratio: Fraction for validation.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_ids, val_ids, test_ids).
    """
    random.seed(seed)
    shuffled = list(video_ids)
    random.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_ids = shuffled[:n_train]
    val_ids = shuffled[n_train : n_train + n_val]
    test_ids = shuffled[n_train + n_val :]

    return train_ids, val_ids, test_ids

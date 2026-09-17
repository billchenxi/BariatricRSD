"""
Annotation Parser
=================
Parses surgical video annotation JSON files into a standardized dictionary format.
Supports multiple annotation schemas (Halo-style JSON, CAMMA-style, CSV-based).

This replaces the proprietary halo_json_to_annote_dict from the 2019 codebase
with a flexible, open-source implementation.
"""

import json
import os
import csv
import re
from typing import Dict, List, Optional, Any
from pathlib import Path


# Type alias for the annotation dictionary structure:
# { video_id: { phase_name: { "start": [float, ...], "end": [float, ...] } } }
AnnotationDict = Dict[str, Dict[str, Dict[str, List[float]]]]


def parse_annotation_json(
    json_path: str,
    video_id_prefix: str = "",
    excluded_annotator_ids: Optional[List[int]] = None,
) -> AnnotationDict:
    """
    Parse a surgical video annotation JSON file into a standardized dictionary.

    Supports JSON files where each entry has:
      - 'id': video identifier
      - 'annotations': list of annotation instances, each containing 'spans'
        with 'name', 'start', 'end' fields.

    Args:
        json_path: Path to the annotation JSON file.
        video_id_prefix: Optional prefix to prepend to video IDs.
        excluded_annotator_ids: Annotator IDs to skip (e.g., automated tools).

    Returns:
        Dictionary mapping video_id -> phase_name -> {"start": [...], "end": [...]}.
    """
    if excluded_annotator_ids is None:
        excluded_annotator_ids = []

    with open(json_path, "r") as f:
        video_data = json.load(f)

    annotation_dict: AnnotationDict = {}

    for video_info in video_data:
        if video_info.get("annotations") is None:
            continue

        current_annotations: Dict[str, Dict[str, List[float]]] = {}

        for annotator_entry in video_info["annotations"]:
            if annotator_entry is None:
                continue

            # Skip excluded annotators
            annotator_ids = annotator_entry.get("assigneeIds", [])
            if any(aid in excluded_annotator_ids for aid in annotator_ids):
                continue

            spans = annotator_entry.get("spans")
            if spans is None:
                continue

            for span in spans:
                if span is None:
                    continue

                phase_name = span["name"]
                start_time = float(span["start"])
                end_time = float(span["end"])

                if phase_name not in current_annotations:
                    current_annotations[phase_name] = {
                        "start": [start_time],
                        "end": [end_time],
                    }
                else:
                    current_annotations[phase_name]["start"].append(start_time)
                    current_annotations[phase_name]["end"].append(end_time)

        video_id = os.path.join(video_id_prefix, str(video_info["id"]))
        annotation_dict[video_id] = current_annotations

    return annotation_dict


def parse_cholec80_annotations(
    annotation_dir: str,
    fps: float = 25.0,
) -> AnnotationDict:
    """
    Parse Cholec80 phase annotation files.

    Cholec80 annotations are typically per-frame text files with format:
        frame_number\tphase_label

    Args:
        annotation_dir: Directory containing per-video annotation files.
        fps: Frames per second of the video data.

    Returns:
        Annotation dictionary in the standard format.
    """
    annotation_dict: AnnotationDict = {}

    for ann_file in sorted(Path(annotation_dir).glob("*.txt")):
        video_id = _normalize_cholec80_video_id(ann_file.stem)
        phases: Dict[str, Dict[str, List[float]]] = {}

        current_phase = None
        phase_start_frame = 0

        with open(ann_file, "r") as f:
            # Skip header if present
            first_line = f.readline().strip()
            if first_line and not first_line[0].isdigit():
                pass  # was a header, continue reading
            else:
                f.seek(0)  # no header, restart

            for line in f:
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                frame_num = int(parts[0])
                phase_label = parts[1]

                if phase_label != current_phase:
                    # Close previous phase segment
                    if current_phase is not None:
                        start_sec = phase_start_frame / fps
                        end_sec = (frame_num - 1) / fps
                        if current_phase not in phases:
                            phases[current_phase] = {"start": [], "end": []}
                        phases[current_phase]["start"].append(start_sec)
                        phases[current_phase]["end"].append(end_sec)

                    current_phase = phase_label
                    phase_start_frame = frame_num

            # Close the last segment
            if current_phase is not None:
                start_sec = phase_start_frame / fps
                end_sec = frame_num / fps
                if current_phase not in phases:
                    phases[current_phase] = {"start": [], "end": []}
                phases[current_phase]["start"].append(start_sec)
                phases[current_phase]["end"].append(end_sec)

        annotation_dict[video_id] = phases

    return annotation_dict


def _normalize_cholec80_video_id(stem: str) -> str:
    """
    Normalize Cholec80 annotation filenames to the extracted frame folder name.

    Common files are named like `video01-phase.txt` while extracted frame folders
    are typically named `video01/`.
    """
    match = re.search(r"(video\d+)", stem, flags=re.IGNORECASE)
    if match is not None:
        return match.group(1).lower()
    return stem


def parse_csv_annotations(
    csv_path: str,
    video_col: str = "video_id",
    phase_col: str = "phase",
    start_col: str = "start",
    end_col: str = "end",
) -> AnnotationDict:
    """
    Parse a CSV annotation file with columns for video_id, phase, start, end.

    Args:
        csv_path: Path to the CSV file.
        video_col, phase_col, start_col, end_col: Column names.

    Returns:
        Annotation dictionary in the standard format.
    """
    annotation_dict: AnnotationDict = {}

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vid = str(row[video_col])
            phase = row[phase_col]
            start = float(row[start_col])
            end = float(row[end_col])

            if vid not in annotation_dict:
                annotation_dict[vid] = {}
            if phase not in annotation_dict[vid]:
                annotation_dict[vid][phase] = {"start": [], "end": []}

            annotation_dict[vid][phase]["start"].append(start)
            annotation_dict[vid][phase]["end"].append(end)

    return annotation_dict


def determine_phase_order(
    annotation_dict: AnnotationDict,
    phase_names: List[str],
) -> Dict[str, List[str]]:
    """
    Determine the ordering of surgical phases for each video.

    This implements the discovery from the 2019 data that RYGB surgeons
    operate in 8 distinct phase orderings.

    Args:
        annotation_dict: Parsed annotation dictionary.
        phase_names: List of phase names to consider for ordering.

    Returns:
        Dictionary mapping video_id -> ordered list of phase names
        (by earliest start time).
    """
    phase_orders: Dict[str, List[str]] = {}

    for video_id, phases in annotation_dict.items():
        # Get the earliest start time for each relevant phase
        phase_starts = []
        for phase_name in phase_names:
            if phase_name in phases and len(phases[phase_name]["start"]) > 0:
                earliest = min(phases[phase_name]["start"])
                phase_starts.append((earliest, phase_name))

        # Sort phases by their earliest start time
        phase_starts.sort(key=lambda x: x[0])
        phase_orders[video_id] = [name for _, name in phase_starts]

    return phase_orders


def cluster_phase_orders(
    phase_orders: Dict[str, List[str]],
) -> Dict[str, int]:
    """
    Assign a cluster ID to each video based on its phase ordering.

    Each unique ordering of phases gets a unique integer cluster ID.

    Args:
        phase_orders: Dictionary mapping video_id -> ordered phase list.

    Returns:
        Dictionary mapping video_id -> cluster_id (0-indexed).
    """
    unique_orderings: Dict[tuple, int] = {}
    cluster_assignments: Dict[str, int] = {}

    for video_id, order in phase_orders.items():
        order_key = tuple(order)
        if order_key not in unique_orderings:
            unique_orderings[order_key] = len(unique_orderings)
        cluster_assignments[video_id] = unique_orderings[order_key]

    return cluster_assignments

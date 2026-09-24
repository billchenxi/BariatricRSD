#!/usr/bin/env python3
"""
10_precompute_prefix_clusters.py

For every clip (v_idx, start_frame_idx) that a BariatricFrameDataset would
generate on a given labels.json, compute the argmax-posterior cluster ID that
would be assigned if the model had access only to the phase sequence *up to
the clip's middle frame* (i.e. the "prefix" — no future frames).

Output: a JSON mapping string-key "<v_idx>|<start_idx>" → cluster_id plus
per-video coverage stats. This file is loaded by `train_causal.py` at
startup; the dataset wrapper then returns the prefix cluster instead of the
per-video oracle cluster for each clip.

Training uses ground-truth phase labels to build the prefix sequence (teacher
forcing). At inference, the same clip-to-cluster mapping is re-derived from
the trained model's phase-head predictions — see `brsd_lib.causal_cluster`.

Fallback: if a clip's prefix contains fewer than `min_phases_for_causal`
unique phases, the script falls back to the video's oracle
`phase_order_cluster` for that clip. This avoids injecting garbage cluster
signal into the very first clips of each video, where the TF-IDF feature
vector is too sparse to produce a reliable posterior.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import sys


def phase_bigrams_from_sequence(names: List[str]) -> List[str]:
    toks = [n.lower().replace(" ", "_").replace("'", "") for n in names]
    if not toks:
        return []
    collapsed = [toks[0]]
    for t in toks[1:]:
        if t != collapsed[-1]:
            collapsed.append(t)
    return [f"{collapsed[i]}->{collapsed[i + 1]}" for i in range(len(collapsed) - 1)]


def posterior_from_bigrams(
    bigrams: List[str],
    vocabulary: Dict[str, int],
    idf: np.ndarray,
    pca_components: np.ndarray,
    pca_mean: np.ndarray,
    centroids: np.ndarray,
    K: int,
    temperature: float = 1.0,
) -> np.ndarray:
    V = len(vocabulary)
    tf = np.zeros(V, dtype=np.float64)
    hits = 0
    for bg in bigrams:
        j = vocabulary.get(bg)
        if j is not None:
            tf[j] += 1.0
            hits += 1
    if hits == 0:
        return np.full(K, 1.0 / K, dtype=np.float64)
    tf /= tf.sum()
    tfidf = tf * idf
    pca = pca_components @ (tfidf - pca_mean)
    d2 = np.sum((centroids - pca[None, :]) ** 2, axis=1)
    logits = -d2 / max(temperature, 1e-6)
    logits -= logits.max()
    w = np.exp(logits)
    w /= w.sum()
    return w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True,
                    help="labels/*_kmeans.json with per-frame 'phase' metadata.")
    ap.add_argument("--artifacts", required=True,
                    help="labels/*_kmeans_artifacts.json from 07b_save_cluster_artifacts.py.")
    ap.add_argument("--output", required=True,
                    help="Path for the resulting per-clip cluster mapping JSON.")
    ap.add_argument("--sequence_len", type=int, default=8)
    ap.add_argument("--frame_stride", type=int, default=5)
    ap.add_argument("--min_phases_for_causal", type=int, default=2,
                    help="If the prefix has fewer than this many unique phases, "
                         "fall back to the video's oracle cluster.")
    ap.add_argument("--splits", nargs="*", default=["train", "val", "test"])
    args = ap.parse_args()

    with open(args.labels) as f:
        videos = json.load(f)
    with open(args.artifacts) as f:
        art = json.load(f)

    vocabulary: Dict[str, int] = art["vocabulary"]
    idf = np.asarray(art["idf"], dtype=np.float64)
    pca_components = np.asarray(art["pca_components"], dtype=np.float64)
    pca_mean = np.asarray(art["pca_mean"], dtype=np.float64)
    centroids = np.asarray(art["centroids"], dtype=np.float64)
    K = int(art["K"])

    span = args.sequence_len * args.frame_stride
    mid_offset = (args.sequence_len // 2) * args.frame_stride

    per_clip: Dict[str, int] = {}
    per_clip_oracle_match: Dict[str, int] = {}
    per_video_stats: Dict[str, Dict] = {}
    fallback_count = 0
    match_count = 0
    total_count = 0

    for v_idx, v in enumerate(videos):
        if v.get("split") not in args.splits:
            continue
        frames = v.get("frames", [])
        if not frames:
            continue
        oracle = int(v.get("phase_order_cluster", 0))
        n_frames = len(frames)
        starts = list(range(0, max(0, n_frames - span + 1), args.frame_stride))
        video_match = 0
        video_fallback = 0
        for start in starts:
            mid_idx = min(start + mid_offset, n_frames - 1)
            prefix_phase_names = [frames[i].get("phase", "") for i in range(mid_idx + 1)
                                   if frames[i].get("phase")]
            bigrams = phase_bigrams_from_sequence(prefix_phase_names)
            unique_prefix_phases = len(set(prefix_phase_names))
            if unique_prefix_phases < args.min_phases_for_causal:
                cid = oracle
                video_fallback += 1
                fallback_count += 1
            else:
                post = posterior_from_bigrams(
                    bigrams, vocabulary, idf, pca_components, pca_mean, centroids, K,
                )
                cid = int(np.argmax(post))
                if cid == oracle:
                    video_match += 1
                    match_count += 1
            per_clip[f"{v_idx}|{start}"] = int(cid)
            per_clip_oracle_match[f"{v_idx}|{start}"] = int(cid == oracle)
            total_count += 1
        per_video_stats[v["video_id"]] = {
            "oracle_cluster": oracle,
            "n_clips": len(starts),
            "n_match_oracle": video_match,
            "n_fallback": video_fallback,
        }

    summary = {
        "total_clips": total_count,
        "match_oracle": match_count,
        "fallback_early_prefix": fallback_count,
        "match_rate_excluding_fallback": (
            match_count / max(total_count - fallback_count, 1)
        ),
        "fallback_rate": fallback_count / max(total_count, 1),
        "K": K,
        "sequence_len": args.sequence_len,
        "frame_stride": args.frame_stride,
        "min_phases_for_causal": args.min_phases_for_causal,
        "labels": args.labels,
        "artifacts": args.artifacts,
    }
    print(json.dumps(summary, indent=2))

    output = {
        "summary": summary,
        "per_video": per_video_stats,
        "per_clip": per_clip,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f)
    print(f"\nwrote {args.output}  ({len(per_clip):,} per-clip assignments)")


if __name__ == "__main__":
    sys.exit(main())

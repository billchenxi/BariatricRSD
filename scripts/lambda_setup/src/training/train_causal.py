"""
train_causal.py

Thin wrapper around `train.main` that substitutes each clip's
`phase_order_cluster` with a per-clip **prefix-derived** cluster ID
precomputed by `scripts/10_precompute_prefix_clusters.py`.

This turns the retrospective workflow-conditioned predictor into a causal
one at training time: the cluster token is computed from only the phases
observed up to each clip's middle frame, not from the full video. At
inference, the trained model is paired with a phase-head-derived cluster
posterior (see `brsd_lib.causal_cluster`) so no ground-truth phase labels
are consulted — the cluster signal is a function of pixels alone.

Usage is identical to `train.py` with one required extra flag:
    --prefix_cluster_map labels/mb140_fold0_prefix_clusters.json

Everything else (lr, batch size, optimizer, scheduler, loss, checkpoints,
wandb) is inherited unchanged from train.py so causal runs are directly
comparable to Run 010 / Run 022 at matched compute.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict

import torch

# Inject our monkey-patch BEFORE importing train, so `from data.dataset
# import BariatricFrameDataset` picks up the causal subclass when train.py
# constructs the dataset.
from data.dataset import BariatricFrameDataset


def _parse_prefix_arg():
    """Extract --prefix_cluster_map from argv without disturbing the rest
    (which belongs to train.main's argparse)."""
    argv = sys.argv[1:]
    path = None
    out = []
    skip = False
    for i, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == "--prefix_cluster_map":
            path = argv[i + 1]
            skip = True
        else:
            out.append(a)
    if path is None:
        raise SystemExit(
            "train_causal.py requires --prefix_cluster_map <path>; use train.py "
            "for oracle training."
        )
    sys.argv = [sys.argv[0]] + out
    return path


def _install_causal_override(per_clip: Dict[str, int]) -> None:
    """Monkey-patch BariatricFrameDataset so __getitem__ returns the
    per-clip prefix cluster instead of the video's oracle cluster."""
    orig_getitem = BariatricFrameDataset.__getitem__
    fallback_count = 0
    hit_count = 0

    # The dataset stores self.samples: list of (v_idx, start_idx). __getitem__
    # builds the sample from that pair. We re-derive the (v_idx, start) for
    # each index so we can look up the precomputed cluster.
    def patched_getitem(self, idx):
        nonlocal fallback_count, hit_count
        item = orig_getitem(self, idx)
        # self.samples[idx] == (v_idx, start)
        v_idx, start = self.samples[idx]
        key = f"{v_idx}|{start}"
        cid = per_clip.get(key)
        if cid is None:
            fallback_count += 1
            return item  # silent fallback to oracle; shouldn't happen often
        hit_count += 1
        item["phase_order_cluster"] = torch.tensor(int(cid), dtype=torch.long)
        return item

    BariatricFrameDataset.__getitem__ = patched_getitem
    # expose counters in case we want to log them later
    BariatricFrameDataset._causal_hit_count = 0
    BariatricFrameDataset._causal_fallback_count = 0


def main():
    path = _parse_prefix_arg()
    with open(path) as f:
        per_clip_raw = json.load(f)
    # The file is produced by scripts/10_precompute_prefix_clusters.py.
    # It has {"summary": {...}, "per_video": {...}, "per_clip": {key: cid}}
    per_clip = per_clip_raw["per_clip"]
    summary = per_clip_raw.get("summary", {})
    print(f"[train_causal] loaded {len(per_clip):,} per-clip prefix clusters from {path}")
    print(f"[train_causal] match_rate_excluding_fallback: "
          f"{summary.get('match_rate_excluding_fallback', float('nan')):.4f}")
    print(f"[train_causal] fallback_rate (early-prefix): "
          f"{summary.get('fallback_rate', float('nan')):.4f}")

    _install_causal_override(per_clip)

    # Defer import of train until the patch is live, so train's two
    # BariatricFrameDataset constructions use the patched __getitem__.
    from training import train as train_mod  # type: ignore
    train_mod.main()


if __name__ == "__main__":
    main()

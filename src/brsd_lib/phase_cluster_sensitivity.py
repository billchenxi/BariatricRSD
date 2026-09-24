"""
brsd_lib.phase_cluster_sensitivity
==================================

Diagnostic for Finding #3 in the Codex review: the phase head used to
derive the causal workflow signal is itself conditioned on the cluster
token. The causal pipeline assumes phase predictions are roughly
cluster-independent and substitutes a placeholder cluster ID at
inference. This module measures how strongly that assumption is violated.

For each clip in a held-out split, we run the model K times — once for
each possible cluster ID 0..K-1 — and record the per-clip phase argmax.
The two diagnostic outputs are:

  (1) `phase_agreement_rate`: across all clips, the fraction of clips for
      which the K predictions agree. High → phase head is approximately
      cluster-independent and the causal pipeline's placeholder is safe.
  (2) `mean_pairwise_phase_disagreement`: average Hamming distance over
      ordered pairs of (cluster_a, cluster_b) phase predictions.

Outputs a JSON report consumable by the manuscript's §4.5 / §6.7 / §8
limitations sections.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch


@torch.no_grad()
def measure_sensitivity(
    model: torch.nn.Module,
    dataset,
    K: int,
    device: torch.device,
    max_clips: int = 2000,
) -> Dict:
    """Measure phase-prediction sensitivity to cluster-token choice.

    Returns dict with summary statistics and per-clip predictions for
    diagnostic plotting.
    """
    model.eval()
    n_clips = min(len(dataset), max_clips)
    indices = np.linspace(0, len(dataset) - 1, n_clips, dtype=int).tolist()

    # phase_predictions[i, k] = argmax phase for clip i under cluster=k.
    phase_predictions = np.zeros((n_clips, K), dtype=np.int64)
    rsd_predictions = np.zeros((n_clips, K), dtype=np.float64)

    for i, sample_idx in enumerate(indices):
        item = dataset[sample_idx]
        frames = item["frames"].unsqueeze(0).to(device, non_blocking=True)
        for k in range(K):
            cluster_id = torch.tensor([k], dtype=torch.long, device=device)
            out = model(frames, cluster_id)
            phase_predictions[i, k] = int(out["phase"].argmax(dim=-1).item())
            rsd_predictions[i, k] = float(out["rsd"].item())

    # Agreement: clip i agrees if phase_predictions[i, :] is constant.
    n_unique_per_clip = np.array([len(set(row.tolist())) for row in phase_predictions])
    agreement_rate = float(np.mean(n_unique_per_clip == 1))

    # Mean pairwise disagreement.
    n_pairs = K * (K - 1) // 2
    pair_disagreements = []
    for a in range(K):
        for b in range(a + 1, K):
            d = float(np.mean(phase_predictions[:, a] != phase_predictions[:, b]))
            pair_disagreements.append({"a": a, "b": b, "disagreement": d})
    mean_pairwise = float(np.mean([p["disagreement"] for p in pair_disagreements]))

    # RSD shift: the maximum RSD prediction range across cluster choices,
    # averaged across clips. If small, the cluster token barely matters
    # and the causal pipeline's placeholder bias is benign.
    rsd_range_per_clip = rsd_predictions.max(axis=1) - rsd_predictions.min(axis=1)
    mean_rsd_range = float(np.mean(rsd_range_per_clip))
    median_rsd_range = float(np.median(rsd_range_per_clip))

    return {
        "n_clips_sampled": int(n_clips),
        "K": int(K),
        "phase_agreement_rate": agreement_rate,
        "mean_pairwise_phase_disagreement": mean_pairwise,
        "pairwise": pair_disagreements,
        "mean_rsd_prediction_range_norm": mean_rsd_range,
        "median_rsd_prediction_range_norm": median_rsd_range,
        "interpretation": (
            "phase_agreement_rate close to 1.0 means the phase head is "
            "approximately cluster-independent; the causal pipeline's "
            "placeholder cluster=0 is then safe. Values < 0.7 mean phase "
            "predictions depend materially on which cluster is supplied, "
            "and the causal pipeline's circularity is a real concern."
        ),
    }


def _cli():
    ap = argparse.ArgumentParser(prog="python -m brsd_lib.phase_cluster_sensitivity")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--label_json", required=True)
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--K", type=int, default=6)
    ap.add_argument("--num_phases", type=int, default=14)
    ap.add_argument("--sequence_len", type=int, default=8)
    ap.add_argument("--frame_stride", type=int, default=5)
    ap.add_argument("--max_clips", type=int, default=2000)
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    args = ap.parse_args()

    from .compute_residuals import _import_project, _load_checkpoint
    BariatricRSD, BariatricFrameDataset, _ = _import_project(args.project_src)

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ds = BariatricFrameDataset(
        args.label_json, args.data_root, split=args.split,
        sequence_len=args.sequence_len, frame_stride=args.frame_stride,
        img_size=224, augment=False,
    )
    model = BariatricRSD(
        encoder_checkpoint=None, encoder_freeze_layers=6,
        embed_dim=768, temporal_layers=6, num_phases=args.num_phases,
    ).to(dev)
    _load_checkpoint(model, args.checkpoint, dev)

    result = measure_sensitivity(model, ds, K=args.K, device=dev,
                                  max_clips=args.max_clips)
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({
        k: v for k, v in result.items() if k not in ("pairwise",)
    }, indent=2))
    print(f"\nwrote {args.output_json}")


if __name__ == "__main__":
    _cli()

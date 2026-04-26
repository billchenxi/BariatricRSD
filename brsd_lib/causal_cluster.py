"""
brsd_lib.causal_cluster
=======================

Causal (prefix-only) workflow-cluster assignment for RSD prediction.

This module converts the system from a *retrospective* workflow-conditioned
predictor (full-video phase sequence → offline cluster → embedding token) into
a *causal* one (prefix frames → phase-head predictions → cluster posterior →
soft-weighted embedding), closing the deployability gap of the oracle-cluster
setting.

Key idea
--------
The trained BariatricRSD model already contains a per-frame phase classifier
(``phase_head``). At inference time, for any prefix ``x_{<=t}``, we can:

  1. Push the prefix through the existing visual encoder + HTA + phase_head to
     get a per-frame phase distribution ``p(phase | frame_i)`` for i <= t.
  2. Accumulate those into an argmax-then-collapse phase sequence ``[p_1, p_2,
     ..., p_T']`` (with consecutive repeats merged).
  3. Vectorize that sequence with the *same* TF-IDF + PCA transforms that were
     fit offline on the ground-truth phase sequences.
  4. Assign a *soft* cluster posterior ``q(z | x_{<=t})`` by taking the softmax
     of negative squared distances to the fixed k-means centroids (optionally
     with a temperature).
  5. Replace the oracle cluster embedding ``E[z*]`` with the mixture
     ``sum_k q(z=k | x_{<=t}) * E[k]`` and feed that into the temporal head.

The cluster centroids, TF-IDF vocabulary/IDF, and PCA components are loaded
from the same artifact that drove the offline clustering (saved alongside the
labels JSON by ``scripts/07_cluster_phase_orders.py``).

Nothing in this module touches ground-truth phase labels at inference. The
only inputs at test time are video frames.

Module structure
----------------
- ``CausalClusterAssigner``: thin wrapper that owns the TF-IDF + PCA + k-means
  artifacts and produces a cluster posterior from a phase sequence.
- ``phase_head_prefix_sequence``: utility that takes a trained BariatricRSD
  model and a frame prefix and returns the predicted collapsed phase sequence.
- ``soft_embedding``: given a cluster posterior and the model's cluster
  embedding table, returns the mixture embedding.
- ``evaluate_causal_rsd``: end-to-end evaluator that swaps the oracle cluster
  token for a causal one at inference and reports MAE.

Written fresh for the NeurIPS 2026 submission.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Cluster-artifact container
# ---------------------------------------------------------------------------

@dataclass
class ClusteringArtifacts:
    """Fixed TF-IDF + PCA + k-means artifacts from offline clustering."""

    vocabulary: Dict[str, int]          # bigram token -> column index
    idf: np.ndarray                     # (vocab_size,) IDF weights
    pca_components: np.ndarray          # (n_components, vocab_size)
    pca_mean: np.ndarray                # (vocab_size,)
    centroids: np.ndarray               # (K, n_components)
    K: int
    phase_id_to_name: Dict[int, str]    # 0..num_phases-1 -> raw phase name
                                         # (same names the offline pipeline ingests)

    @classmethod
    def from_json(cls, path: str) -> "ClusteringArtifacts":
        with open(path) as f:
            data = json.load(f)
        id2name = data.get("phase_id_to_name", {})
        # JSON keys are strings — cast to int
        id2name = {int(k): v for k, v in id2name.items()}
        return cls(
            vocabulary=data["vocabulary"],
            idf=np.asarray(data["idf"], dtype=np.float64),
            pca_components=np.asarray(data["pca_components"], dtype=np.float64),
            pca_mean=np.asarray(data["pca_mean"], dtype=np.float64),
            centroids=np.asarray(data["centroids"], dtype=np.float64),
            K=int(data["K"]),
            phase_id_to_name=id2name,
        )


def _phase_to_token(name: str) -> str:
    """Match the offline `phase_bigrams` tokenizer: lowercase, underscores."""
    return name.lower().replace(" ", "_").replace("'", "")


def _bigrams_from_phase_ids(
    phase_ids: Sequence[int],
    id_to_name: Dict[int, str],
) -> List[str]:
    """Map integer phase predictions → name tokens → collapsed bigrams.

    Matches the offline clustering pipeline's bigram format exactly, so that
    a phase sequence predicted by the model's phase head produces features
    comparable to the TF-IDF vocabulary in the artifact file.
    """
    if not phase_ids:
        return []
    tokens: List[str] = []
    for p in phase_ids:
        name = id_to_name.get(int(p))
        if name is None:
            continue  # skip unknown class (shouldn't happen for in-vocab predictions)
        tokens.append(_phase_to_token(name))
    if not tokens:
        return []
    collapsed: List[str] = [tokens[0]]
    for t in tokens[1:]:
        if t != collapsed[-1]:
            collapsed.append(t)
    return [f"{collapsed[i]}->{collapsed[i + 1]}" for i in range(len(collapsed) - 1)]


class CausalClusterAssigner:
    """Produces cluster posterior over phase-bigram TF-IDF / PCA / k-means."""

    def __init__(self, artifacts: ClusteringArtifacts, temperature: float = 1.0):
        self.a = artifacts
        self.temperature = float(temperature)

    def phase_sequence_to_posterior(self, phase_seq: Sequence[int]) -> np.ndarray:
        """Return soft cluster posterior (shape (K,)) from a phase sequence.

        `phase_seq` is a list of integer phase-class IDs (as produced by the
        model's phase head). They are mapped to the original phase names via
        the artifact's ``phase_id_to_name`` table before bigram construction
        so the resulting tokens match the offline TF-IDF vocabulary exactly.

        If the sequence is too short to produce any in-vocab bigram, returns
        a uniform posterior — downstream soft-embedding becomes the average
        of the K cluster embeddings, which is a reasonable prior when we
        haven't yet seen enough of the surgery to disambiguate workflow.
        """
        bigrams = _bigrams_from_phase_ids(phase_seq, self.a.phase_id_to_name)
        if not bigrams:
            return np.full(self.a.K, 1.0 / self.a.K, dtype=np.float64)
        V = len(self.a.vocabulary)
        tf = np.zeros(V, dtype=np.float64)
        hits = 0
        for bg in bigrams:
            j = self.a.vocabulary.get(bg)
            if j is not None:
                tf[j] += 1.0
                hits += 1
        if hits == 0:
            return np.full(self.a.K, 1.0 / self.a.K, dtype=np.float64)
        tf /= tf.sum()
        tfidf = tf * self.a.idf
        pca = self.a.pca_components @ (tfidf - self.a.pca_mean)
        d2 = np.sum((self.a.centroids - pca[None, :]) ** 2, axis=1)
        logits = -d2 / max(self.temperature, 1e-6)
        logits -= logits.max()
        w = np.exp(logits)
        w /= w.sum()
        return w


# ---------------------------------------------------------------------------
# Phase-head prefix inference
# ---------------------------------------------------------------------------

@torch.no_grad()
def phase_head_prefix_sequence(
    model: torch.nn.Module,
    prefix_frames: torch.Tensor,
    prefix_cluster_placeholder: int = 0,
) -> List[int]:
    """Run prefix frames through the model's visual encoder + phase head and
    return an argmax-then-collapse phase sequence.

    Arguments:
        model: a trained BariatricRSD instance.
        prefix_frames: (B=1, T, C, H, W) tensor.
        prefix_cluster_placeholder: cluster ID to pass through the token input.
            The phase head's per-frame predictions are a function of visual
            features only; the cluster token does not feed the phase logits.
            Any valid cluster ID is fine; 0 is a safe default.

    Returns:
        List[int] of collapsed phase IDs.
    """
    dev = next(model.parameters()).device
    prefix_frames = prefix_frames.to(dev)
    cluster = torch.zeros(prefix_frames.size(0), dtype=torch.long, device=dev) + int(
        prefix_cluster_placeholder
    )
    out = model(prefix_frames, cluster)
    phase_logits = out.get("phase")
    if phase_logits is None:
        raise RuntimeError(
            "Model did not return 'phase' output — causal cluster assignment "
            "requires a trained phase head."
        )
    # phase_logits: (B, T, num_phases) or (B, num_phases) depending on aggregation.
    if phase_logits.dim() == 2:
        preds = phase_logits.argmax(dim=-1).cpu().tolist()
        if isinstance(preds, int):
            preds = [preds]
    else:
        preds = phase_logits.argmax(dim=-1).squeeze(0).cpu().tolist()
    if not isinstance(preds, list):
        preds = [int(preds)]
    return [int(p) for p in preds]


# ---------------------------------------------------------------------------
# Soft-embedding fusion
# ---------------------------------------------------------------------------

def soft_embedding(
    posterior: np.ndarray,
    embedding_table: torch.nn.Embedding,
) -> torch.Tensor:
    """Compute sum_k q(z=k) * E[k] as a single embedding vector.

    Returns a 1D tensor of shape (embed_dim,) on the same device / dtype as
    ``embedding_table.weight``.
    """
    w = torch.as_tensor(posterior, dtype=embedding_table.weight.dtype,
                        device=embedding_table.weight.device)
    # (K, d) x (K,) -> (d,)
    return embedding_table.weight.T @ w


# ---------------------------------------------------------------------------
# End-to-end causal evaluator
# ---------------------------------------------------------------------------

@torch.no_grad()
def evaluate_causal_rsd(
    model: torch.nn.Module,
    dataloader,
    assigner: CausalClusterAssigner,
    device: torch.device,
) -> Dict[str, float]:
    """DEPRECATED — buggy. Computes ONE posterior per batch and broadcasts it
    to all clips in the batch (incorrect because clips in a batch are from
    different videos at different prefix lengths). Kept here so old callers
    error loudly; please use ``evaluate_causal_rsd_pixel_only`` instead.
    """
    raise RuntimeError(
        "evaluate_causal_rsd was buggy (per-batch posterior broadcast). "
        "Use evaluate_causal_rsd_pixel_only(model, dataset, assigner, device, ...) "
        "which processes clips per-video, chronologically, with a growing "
        "predicted-phase prefix per clip."
    )


@torch.no_grad()
def evaluate_causal_rsd_pixel_only(
    model: torch.nn.Module,
    dataset,
    assigner: CausalClusterAssigner,
    device: torch.device,
    batch_size: int = 32,
) -> Dict[str, float]:
    """True pixel-only causal evaluation.

    For each video in ``dataset``, walks its clips in chronological order
    (sorted by start_idx in ``dataset.samples``), and for each clip at time
    t computes:

      1. Ground-truth visual encoder + HTA + phase_head predictions for clips
         0..t-1 in the same video (i.e. an *observed* prefix phase sequence
         derived from pixels alone, no future frames).
      2. A soft cluster posterior from the offline TF-IDF/PCA/centroid
         pipeline, applied to the bigrams of that predicted phase sequence.
      3. The mixture workflow token = sum_k q_k * E[k].
      4. The RSD prediction for clip t using the mixture token.

    Returns dict with ``mae_norm_mean``, ``mae_minutes`` (using per-video
    total_duration_sec when available), and ``per_video`` breakdown.

    Computational notes. We process all clips of a single video back-to-back
    so each clip sees the predicted phases of all prior clips in the same
    video. Memory is dominated by the model itself (~36 GB on GH200) and
    the per-video predicted phase list is tiny.

    Pre-conditions:
      * ``dataset`` exposes ``.samples`` as List[Tuple[v_idx, start_idx]] and
        ``.videos`` as List[Dict] with at least 'video_id' and
        'total_duration_sec'.
      * ``model`` has been wrapped via ``patch_model_for_soft_cluster`` so
        that ``model._causal_forward(frames, cluster_embedding)`` is callable.
    """
    assert hasattr(model, "_causal_forward"), (
        "Wrap model with patch_model_for_soft_cluster() before calling this."
    )
    model.eval()
    # Build (v_idx, start_idx, sample_idx) tuples and group by v_idx.
    by_video: Dict[int, List[Tuple[int, int]]] = {}
    for sample_idx, (v_idx, start) in enumerate(dataset.samples):
        by_video.setdefault(int(v_idx), []).append((sample_idx, int(start)))
    for v_idx in by_video:
        by_video[v_idx].sort(key=lambda x: x[1])  # chronological by start

    all_pred: Dict[str, List[float]] = {}
    all_true: Dict[str, List[float]] = {}
    all_total_min: Dict[str, float] = {}

    for v_idx, clip_list in by_video.items():
        v = dataset.videos[v_idx]
        vid = str(v["video_id"])
        all_pred.setdefault(vid, [])
        all_true.setdefault(vid, [])
        total_sec = float(v.get("total_duration_sec", 0.0)) or 0.0
        all_total_min[vid] = total_sec / 60.0 if total_sec > 0 else float("nan")

        # Predicted phase sequence accumulated chronologically across clips of v.
        # The pipeline must update `predicted_phases` *between every clip*
        # (not every chunk), because the workflow posterior is supposed to
        # depend on every prior clip's predicted phase. We therefore process
        # clips one at a time. Encoder + temporal forward at batch=1 is the
        # honest implementation; the small throughput cost is the price of
        # a correct causal evaluation.
        for sample_idx, _start in clip_list:
            posterior = assigner.phase_sequence_to_posterior(predicted_phases)
            emb = soft_embedding(posterior, model.phase_order_embed)

            item = dataset[sample_idx]
            frames = item["frames"].unsqueeze(0).to(device, non_blocking=True)
            target = float(item["rsd_normalized"])

            out = model._causal_forward(frames, emb)
            rsd_pred = float(out["rsd"].detach().float().cpu().item())
            all_pred[vid].append(rsd_pred)
            all_true[vid].append(target)

            phase_logits = out.get("phase")
            if phase_logits is not None:
                phase_pred = int(phase_logits.argmax(dim=-1).item())
                predicted_phases.append(phase_pred)

    # Aggregate.
    per_video: Dict[str, Dict[str, float]] = {}
    abs_errs_norm = []
    abs_errs_min = []
    for vid in all_pred:
        p = np.asarray(all_pred[vid])
        t = np.asarray(all_true[vid])
        e_norm = np.abs(p - t)
        per_video[vid] = {
            "n_clips": int(p.size),
            "mae_norm": float(e_norm.mean()),
        }
        abs_errs_norm.append(e_norm.mean())
        if not np.isnan(all_total_min[vid]):
            per_video[vid]["mae_minutes"] = float(e_norm.mean() * all_total_min[vid])
            abs_errs_min.append(e_norm.mean() * all_total_min[vid])
    summary = {
        "mae_norm_mean": float(np.mean(abs_errs_norm)) if abs_errs_norm else float("nan"),
        "mae_minutes_mean": float(np.mean(abs_errs_min)) if abs_errs_min else float("nan"),
        "n_videos": len(per_video),
        "per_video": per_video,
    }
    return summary


def patch_model_for_soft_cluster(model: torch.nn.Module) -> None:
    """Monkey-patch the model to accept a pre-computed cluster embedding.

    The trained ``BariatricRSD.forward`` takes ``(frames, phase_order_cluster)``
    where ``phase_order_cluster`` is an integer tensor. To inject a soft mixture
    embedding instead of a hard one-hot lookup, we temporarily replace the
    ``phase_order_embed`` submodule with a stub that returns a fixed tensor
    regardless of input, then restore the original after the forward.

    Adds ``model._causal_forward(frames, cluster_embedding)`` which:
      * temporarily patches ``model.phase_order_embed`` so its forward returns
        ``cluster_embedding`` broadcast across the batch (with the same
        downstream shape ``[B, 1, D]`` the original module produced),
      * runs the standard ``model.forward(frames, dummy_cluster_id)``,
      * restores ``model.phase_order_embed``.

    The original ``forward`` and ``phase_order_embed`` are left untouched on
    return; safe to interleave with regular oracle forwards.
    """
    import types

    def _causal_forward(self, frames: torch.Tensor, cluster_embedding: torch.Tensor):
        # cluster_embedding: (embed_dim,) — broadcast across the batch.
        B = frames.size(0)
        D = cluster_embedding.size(-1)
        tok = cluster_embedding.view(1, 1, D).expand(B, 1, D)

        original_forward = self.phase_order_embed.forward

        def patched_forward(_cluster_ids):
            return tok

        self.phase_order_embed.forward = patched_forward
        try:
            out = self.forward(
                frames,
                torch.zeros(B, dtype=torch.long, device=frames.device),
            )
        finally:
            self.phase_order_embed.forward = original_forward
        return out

    model._causal_forward = types.MethodType(_causal_forward, model)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.causal_cluster",
        description="Evaluate a trained BariatricRSD model under causal "
                    "(prefix-phase-derived) workflow conditioning.",
    )
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--cluster_artifacts", required=True,
                    help="JSON with TF-IDF vocab, IDF, PCA, k-means centroids.")
    ap.add_argument("--label_json", required=True)
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--split", default="val")
    ap.add_argument("--num_phases", type=int, default=14)
    ap.add_argument("--sequence_len", type=int, default=8)
    ap.add_argument("--frame_stride", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--num_workers", type=int, default=16)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--target_position", default="middle", choices=["middle", "last"])
    ap.add_argument("--decouple_phase_head", action="store_true")
    ap.add_argument("--output_json", required=True)
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    args = ap.parse_args()

    # Local import to avoid pulling heavy deps at module import time.
    from .compute_residuals import _import_project, _load_checkpoint
    BariatricRSD, BariatricFrameDataset, DataLoader = _import_project(args.project_src)

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ds = BariatricFrameDataset(
        args.label_json, args.data_root, split=args.split,
        sequence_len=args.sequence_len, frame_stride=args.frame_stride,
        img_size=224, augment=False,
        target_position=args.target_position,
    )
    model = BariatricRSD(
        encoder_checkpoint=None, encoder_freeze_layers=6,
        embed_dim=768, temporal_layers=6, num_phases=args.num_phases,
        decouple_phase_head=args.decouple_phase_head,
    ).to(dev)
    _load_checkpoint(model, args.checkpoint, dev)
    patch_model_for_soft_cluster(model)

    artifacts = ClusteringArtifacts.from_json(args.cluster_artifacts)
    assigner = CausalClusterAssigner(artifacts, temperature=args.temperature)

    # Use the per-video chronological evaluator (the buggy per-batch broadcast
    # version raises a RuntimeError to keep callers honest).
    results = evaluate_causal_rsd_pixel_only(
        model, ds, assigner, dev, batch_size=args.batch_size,
    )
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\ncausal MAE (normalized): {results['mae_norm_mean']:.4f}")
    print(f"wrote {args.output_json}")


if __name__ == "__main__":
    _cli()

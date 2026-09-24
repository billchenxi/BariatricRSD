"""R1d — duration-aware k-means workflow representation.

The diagnostic called for in `PHASE_0_FINDING_REPRESENTATION.md` §5.2.

Paper 1's R1 clusters TF-IDF vectors over phase-transition bigrams built
from `phase_sequence`, the ordered list of phase *segments*. Two cases
with the same phase order produce the same input vector whether one ran
55 minutes and the other 130. The R3 HMM, by contrast, models the
per-second timeline, so its likelihood is dominated by how long each
phase lasted. The two families agree on how much workflow variability a
dataset has but partition the videos near-orthogonally (ARI ≈ 0.05 on
MB140, versus 0.42–0.70 between k-means at different K).

That leaves two readings:

- **Reading A — it is about what each family reads.** R1 sees order, R3
  sees timing, and those are genuinely different views of "workflow". If
  so, adding duration features to R1 should move it toward R3.
- **Reading B — the construct is not identified at all.** Even matched
  on what they read, the families would still disagree, and "workflow
  cluster" would be an artifact of the clustering machinery.

This module builds R1d: the same bigram TF-IDF pipeline with per-phase
duration features appended, so the only thing that changed is whether
durations are visible. The ARI of R1d against R1 and against R3 decides
between the readings.

`--duration-weight` controls how much of the feature vector's norm the
duration block carries, since TF-IDF and log-duration features are not
otherwise commensurable. It is swept rather than fixed, because a single
arbitrary weight would make the answer a function of a tuning choice.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger("duration_aware_kmeans")


def phase_bigrams(phase_sequence: Sequence[str]) -> str:
    """Bigram document for one video — identical to Paper 1's tokenizer.

    Copied verbatim in behaviour from
    `scripts/lambda_setup/scripts/07_cluster_phase_orders.py` so that R1d differs
    from R1 in exactly one respect: the duration block.
    """
    toks = [p.lower().replace(" ", "_").replace("'", "") for p in phase_sequence]
    return " ".join(f"{a}->{b}" for a, b in zip(toks[:-1], toks[1:]))


def phase_duration_features(video: Dict, phase_vocab: Dict[str, int]) -> np.ndarray:
    """Per-phase seconds plus total duration, log1p-scaled.

    Log scaling because surgical durations are right-skewed and a raw
    scale would let one three-hour case dominate the k-means objective.
    Phases absent from a video contribute log1p(0) = 0.
    """
    seconds = np.zeros(len(phase_vocab), dtype=np.float64)
    for frame in video["frames"]:
        seconds[phase_vocab[frame["phase"]]] += 1.0
    total = float(video.get("total_duration_sec") or seconds.sum())
    return np.log1p(np.concatenate([seconds, [total]]))


def build_features(videos: List[Dict], duration_weight: float,
                   n_components: int = 16, seed: int = 42
                   ) -> Tuple[np.ndarray, Dict]:
    """Bigram TF-IDF (+ PCA) with an optional weighted duration block.

    `duration_weight` is the ratio of the duration block's Frobenius norm
    to the order block's, applied after each block is standardized. A
    weight of 0 reproduces R1 exactly.
    """
    from sklearn.decomposition import PCA
    from sklearn.feature_extraction.text import TfidfVectorizer

    docs = [phase_bigrams(v["phase_sequence"]) for v in videos]
    vec = TfidfVectorizer(token_pattern=r"\S+", min_df=2, sublinear_tf=True)
    order_block = vec.fit_transform(docs).toarray()

    n_comp = min(n_components, order_block.shape[0] - 1, order_block.shape[1])
    pca = PCA(n_components=n_comp, random_state=seed)
    order_block = pca.fit_transform(order_block)

    # A corpus where every video shares one bigram signature has zero
    # total variance, and sklearn returns NaN for the ratio. Report 0.0
    # rather than letting a NaN reach the JSON report.
    explained = float(pca.explained_variance_ratio_.sum())
    meta = {
        "n_bigram_features": int(len(vec.vocabulary_)),
        "n_pca_components": int(n_comp),
        "pca_explained_variance": explained if explained == explained else 0.0,
        "duration_weight": duration_weight,
    }

    if duration_weight <= 0:
        return order_block, meta

    vocab = videos[0]["phase_vocab"]
    duration_block = np.stack([phase_duration_features(v, vocab) for v in videos])
    # Standardize per column so no single phase's scale dominates, then
    # rescale the whole block to the requested share of the order block's
    # norm. Columns with zero variance (a phase every video shares
    # identically, or none has) would divide by zero, so they are dropped.
    std = duration_block.std(axis=0)
    keep = std > 1e-12
    duration_block = (duration_block[:, keep] - duration_block[:, keep].mean(axis=0)) / std[keep]

    order_norm = np.linalg.norm(order_block)
    duration_norm = np.linalg.norm(duration_block)
    if duration_norm > 0 and order_norm > 0:
        duration_block *= duration_weight * order_norm / duration_norm

    meta["n_duration_features"] = int(keep.sum())
    return np.concatenate([order_block, duration_block], axis=1), meta


def cluster(features: np.ndarray, k: int, seed: int = 42) -> np.ndarray:
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=k, n_init=20, random_state=seed)
    return km.fit_predict(features)


def _inertia(label_json: Path, k: int, seed: int,
             duration_weight: float = 0.0) -> float:
    """k-means objective value for one seed, for the flat-landscape check."""
    from sklearn.cluster import KMeans
    videos = json.loads(Path(label_json).read_text())
    features, _ = build_features(videos, duration_weight, seed=seed)
    return float(KMeans(n_clusters=k, n_init=20,
                        random_state=seed).fit(features).inertia_)


def run(label_json: Path, k: int, duration_weight: float,
        seed: int = 42) -> Tuple[Dict[str, int], Dict]:
    """Fit R1d and return (video_id -> cluster, metadata)."""
    videos = json.loads(Path(label_json).read_text())
    features, meta = build_features(videos, duration_weight, seed=seed)
    labels = cluster(features, k, seed=seed)
    meta.update({"k": k, "n_videos": len(videos),
                 "source_labels": str(label_json), "seed": seed})
    return {v["video_id"]: int(lab) for v, lab in zip(videos, labels)}, meta


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--label-json", required=True, type=Path,
                    help="Raw label JSON (not the *_kmeans.json variant).")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--duration-weights", type=float, nargs="+",
                    default=[0.0, 0.25, 0.5, 1.0, 2.0, 4.0],
                    help="Sweep of duration-block weights. 0 reproduces R1.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reference-kmeans", type=Path, default=None,
                    help="Paper 1 R1 labels JSON, to measure ARI against.")
    ap.add_argument("--reference-hmm", type=Path, default=None,
                    help="R3 HMM output JSON, to measure ARI against.")
    ap.add_argument("--hmm-mode", default="oracle", choices=["causal", "oracle"])
    ap.add_argument("--seed-stability", type=int, nargs="*", default=None,
                    metavar="SEED",
                    help="Measure across-seed stability of the order-only "
                         "representation at these seeds instead of running "
                         "the duration sweep. Default seeds if none given.")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from paper2_infra.workflow_representations.compare import (
        adjusted_rand_index, assignment_variability, load_hmm_assignments,
        load_kmeans_assignments, seed_stability,
    )

    if args.seed_stability is not None:
        seeds = args.seed_stability or [0, 1, 42, 123, 777]
        by_seed = {}
        inertias = {}
        for seed in seeds:
            assignments, meta = run(args.label_json, args.k, 0.0, seed=seed)
            by_seed[seed] = assignments
            inertias[seed] = _inertia(args.label_json, args.k, seed)
        stability = seed_stability(by_seed)
        span = max(inertias.values()) - min(inertias.values())
        mean_inertia = sum(inertias.values()) / len(inertias)
        print(f"\nSeed stability of R1 (k={args.k}) on {args.label_json.name}")
        print(f"  seeds            : {seeds}")
        print(f"  pairwise ARI     : mean {stability['mean_ari']:.3f}  "
              f"min {stability['min_ari']:.3f}  max {stability['max_ari']:.3f}")
        print(f"  k-means inertia  : spread {span:.4f} "
              f"({100 * span / mean_inertia:.2f}% of mean)")
        if stability["mean_ari"] < 0.9 and span / mean_inertia < 0.05:
            print("  -> near-identical objective, materially different "
                  "partitions: the feature space admits many equally-good "
                  "splits, so the cluster assignment is arbitrary among them.")
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(
                {"seed_stability": stability, "inertias": inertias,
                 "k": args.k, "source_labels": str(args.label_json)}, indent=2))
            logger.info("\nWrote %s", args.out)
        return

    ref_r1 = (load_kmeans_assignments(args.reference_kmeans)
              if args.reference_kmeans else None)
    ref_r3 = (load_hmm_assignments(args.reference_hmm, args.hmm_mode)
              if args.reference_hmm else None)

    def ari_against(assignments, reference):
        if reference is None:
            return float("nan")
        shared = sorted(set(assignments) & set(reference))
        if len(shared) < 2:
            return float("nan")
        return adjusted_rand_index([assignments[v] for v in shared],
                                   [reference[v] for v in shared])

    rows = []
    print(f"\n{'dur.weight':>10} {'K used':>7} {'H/logK':>8} "
          f"{'ARI vs R1':>10} {'ARI vs R3':>10}")
    for weight in args.duration_weights:
        assignments, meta = run(args.label_json, args.k, weight, seed=args.seed)
        var = assignment_variability(assignments)
        row = {
            "duration_weight": weight,
            "n_clusters_used": var["n_clusters_used"],
            "entropy_normalized": var["entropy_normalized_by_used"],
            "dominant_cluster_share": var["dominant_cluster_share"],
            "ari_vs_r1_kmeans": ari_against(assignments, ref_r1),
            "ari_vs_r3_hmm": ari_against(assignments, ref_r3),
            "meta": meta,
        }
        rows.append(row)
        print(f"{weight:>10.2f} {var['n_clusters_used']:>7} "
              f"{var['entropy_normalized_by_used']:>8.3f} "
              f"{row['ari_vs_r1_kmeans']:>10.3f} {row['ari_vs_r3_hmm']:>10.3f}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(
            {"sweep": rows, "k": args.k,
             "source_labels": str(args.label_json)}, indent=2))
        logger.info("\nWrote %s", args.out)


if __name__ == "__main__":
    main()

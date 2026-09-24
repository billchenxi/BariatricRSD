#!/usr/bin/env python3
"""
Data-driven phase-order clustering for MultiBypass140.

Groups the 140 videos into K clusters based on their actual phase-transition
signatures (bigrams of adjacent phases). Writes a new labels.json where each
video has a meaningful `phase_order_cluster` (not the broken heuristic from
infer_phase_order_cluster).

Run:
  python3 scripts/07_cluster_phase_orders.py --k 6 \
    --input_labels labels/mb140_fold0_labels.json \
    --output_labels labels/mb140_fold0_labels_kmeans.json
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA


def phase_bigrams(phase_sequence):
    """Compact bigram representation — lowercased, space-safe tokens."""
    toks = [p.lower().replace(" ", "_").replace("'", "") for p in phase_sequence]
    return " ".join(f"{a}->{b}" for a, b in zip(toks[:-1], toks[1:]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_labels", required=True)
    ap.add_argument("--output_labels", required=True)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    with open(args.input_labels) as f:
        videos = json.load(f)

    # Build bigram documents
    docs = [phase_bigrams(v["phase_sequence"]) for v in videos]
    print(f"Loaded {len(videos)} videos.")
    print(f"Example phase sequence (video 0): {videos[0]['phase_sequence'][:8]}...")
    print(f"Example bigrams: {docs[0][:200]}...")

    vec = TfidfVectorizer(token_pattern=r"\S+", min_df=2, sublinear_tf=True)
    X = vec.fit_transform(docs).toarray()
    print(f"Feature matrix: {X.shape} ({X.shape[1]} unique bigram types)")

    # Reduce dim (helps kmeans stability)
    n_comp = min(16, X.shape[0] - 1, X.shape[1])
    pca = PCA(n_components=n_comp, random_state=args.seed)
    Xp = pca.fit_transform(X)
    print(f"PCA explained variance: {pca.explained_variance_ratio_.sum():.3f}")

    km = KMeans(n_clusters=args.k, n_init=20, random_state=args.seed)
    labels = km.fit_predict(Xp)

    # Diagnostics
    cluster_counts = Counter(labels.tolist())
    print(f"\nCluster sizes (k={args.k}): {dict(cluster_counts.most_common())}")

    # Show representative phase sequences per cluster
    for c in sorted(cluster_counts):
        members = [i for i, l in enumerate(labels) if l == c]
        print(f"\n  Cluster {c}  (n={len(members)}):")
        for i in members[:3]:
            seq = " -> ".join(videos[i]["phase_sequence"][:6])
            print(f"    {videos[i]['video_id']}: {seq}...")

    # Write updated labels
    for v, c in zip(videos, labels):
        v["phase_order_cluster"] = int(c)

    # Ensure `phase_vocab` size accommodates clusters in dataset side — update NUM_PHASE_ORDER_CLUSTERS if needed
    print(f"\nNOTE: set NUM_PHASE_ORDER_CLUSTERS >= {args.k} in src/data/dataset.py")

    out_path = Path(args.output_labels)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(videos, f)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

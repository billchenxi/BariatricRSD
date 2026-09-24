#!/usr/bin/env python3
"""
07b_save_cluster_artifacts.py

Re-run the same clustering pipeline used by 07_cluster_phase_orders.py on a
given labels.json and persist the TF-IDF vocabulary + IDF, PCA components +
mean, and k-means centroids to a JSON artifact file consumable by
`brsd_lib.causal_cluster.ClusteringArtifacts.from_json`.

Exists so the causal-inference module can reproduce the offline cluster
assignment from a phase sequence *predicted* by the trained model's phase
head — without needing to rerun the k-means fit.

Usage:
  python3 scripts/07b_save_cluster_artifacts.py \
    --input_labels labels/mb140_fold0_labels.json \
    --k 6 --seed 42 \
    --output_artifacts labels/mb140_fold0_kmeans_artifacts.json
"""
import argparse
import json

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA


def phase_bigrams(phase_sequence):
    toks = [p.lower().replace(" ", "_").replace("'", "") for p in phase_sequence]
    return " ".join(f"{a}->{b}" for a, b in zip(toks[:-1], toks[1:]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_labels", required=True)
    ap.add_argument("--output_artifacts", required=True)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    with open(args.input_labels) as f:
        videos = json.load(f)
    docs = [phase_bigrams(v["phase_sequence"]) for v in videos]

    phase_vocabs = [tuple(sorted(v.get("phase_vocab", {}).items())) for v in videos]
    unique_vocabs = set(phase_vocabs)
    if len(unique_vocabs) != 1:
        raise RuntimeError(
            f"Expected one shared phase_vocab across videos; found {len(unique_vocabs)}"
        )
    phase_name_to_id = dict(videos[0]["phase_vocab"])
    phase_id_to_name = {int(v): k for k, v in phase_name_to_id.items()}

    vec = TfidfVectorizer(token_pattern=r"\S+", min_df=2, sublinear_tf=True)
    X = vec.fit_transform(docs).toarray()

    n_comp = min(16, X.shape[0] - 1, X.shape[1])
    pca = PCA(n_components=n_comp, random_state=args.seed)
    Xp = pca.fit_transform(X)

    km = KMeans(n_clusters=args.k, n_init=20, random_state=args.seed)
    km.fit(Xp)

    artifacts = {
        "vocabulary": {k: int(v) for k, v in vec.vocabulary_.items()},
        "idf": vec.idf_.tolist(),
        "pca_components": pca.components_.tolist(),
        "pca_mean": pca.mean_.tolist(),
        "centroids": km.cluster_centers_.tolist(),
        "K": int(args.k),
        "n_features": int(X.shape[1]),
        "n_components": int(n_comp),
        "source_labels": args.input_labels,
        "seed": args.seed,
        "phase_id_to_name": {str(k): v for k, v in phase_id_to_name.items()},
        "bigram_tokenizer": "lowercase_underscore_from_phase_name",
    }
    with open(args.output_artifacts, "w") as f:
        json.dump(artifacts, f)
    print(f"vocab_size={len(artifacts['vocabulary'])}  n_components={n_comp}  K={args.k}")
    print(f"wrote {args.output_artifacts}")


if __name__ == "__main__":
    main()

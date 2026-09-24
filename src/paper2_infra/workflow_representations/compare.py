"""Cross-representation workflow-variability comparison.

Paper 1 measured workflow variability with one representation family
(TF-IDF bigrams → PCA → k-means) and drew a cross-dataset conclusion
from it: MB140 is more workflow-variable than Cholec80, therefore
workflow conditioning helps on MB140 and not on Cholec80. Reviewer iSh9
objected that the K=4/6/8 ablation varies granularity inside that family
and so cannot show the conclusion is about workflow rather than about
k-means. This module answers that objection directly by asking two
questions of every dataset:

1. **Does the variability ordering survive a change of family?** If an
   HMM latent-state representation also finds MB140 more variable than
   Cholec80, the ordering is a property of the data. If it does not, the
   ordering was a property of k-means and Paper 1's premise is unsafe.
2. **Do the two families group the same videos together?** Adjusted Rand
   index between the hard assignments. High ARI means the two families
   recovered the same construct under different machinery; low ARI means
   "workflow cluster" is not well defined and any conditioning result is
   representation-specific by construction.

**A caveat that must travel with these numbers.** MB140 has 14 phase
labels and Cholec80 has 7, and they are different procedures. A larger
phase vocabulary admits more distinct transition patterns, so some of
the entropy gap is taxonomy rather than workflow heterogeneity. The
normalized entropies below partly control for the number of states
*used*, but they do not control for the vocabulary the states are built
from. This is the same confound reviewer 6eLx raised, and no measurement
in this module removes it — it is a reason to report the gap alongside
the caveat, not a reason to claim variability is isolated.
"""
from __future__ import annotations

import argparse
import collections
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np

logger = logging.getLogger("compare_representations")


# ── Agreement between two hard clusterings ──────────────────────────────────

def adjusted_rand_index(labels_a: Sequence[int], labels_b: Sequence[int]) -> float:
    """Adjusted Rand index between two hard clusterings of the same items.

    1.0 is identical up to relabeling, 0.0 is chance agreement, and
    negative values mean worse than chance. Implemented here rather than
    imported so this module stays dependency-light (numpy only).
    """
    a = np.asarray(labels_a)
    b = np.asarray(labels_b)
    if a.shape != b.shape:
        raise ValueError(f"clusterings differ in length: {a.shape} vs {b.shape}")
    n = a.size
    if n < 2:
        raise ValueError("need at least two items to compare clusterings")

    a_ids = {v: i for i, v in enumerate(sorted(set(a.tolist())))}
    b_ids = {v: i for i, v in enumerate(sorted(set(b.tolist())))}
    contingency = np.zeros((len(a_ids), len(b_ids)), dtype=np.float64)
    for va, vb in zip(a.tolist(), b.tolist()):
        contingency[a_ids[va], b_ids[vb]] += 1

    def comb2(x):
        return x * (x - 1) / 2.0

    sum_ij = comb2(contingency).sum()
    sum_i = comb2(contingency.sum(axis=1)).sum()
    sum_j = comb2(contingency.sum(axis=0)).sum()
    total = comb2(float(n))
    expected = sum_i * sum_j / total
    maximum = (sum_i + sum_j) / 2.0
    if maximum == expected:
        return 1.0  # both clusterings are trivial (all items in one group)
    return float((sum_ij - expected) / (maximum - expected))


# ── Variability of one hard assignment ──────────────────────────────────────

def assignment_variability(assignments: Dict[str, int]) -> Dict:
    """Workflow variability H(z) for a video → cluster-id mapping.

    `entropy_normalized_by_used` divides by log of the number of clusters
    actually occupied, which is what makes two representations that chose
    different K roughly comparable. `dominant_share` is reported next to
    it because a dataset where most videos fall in one cluster is not
    workflow-diverse regardless of how many clusters the algorithm was
    asked for — Cholec80 is exactly this case.
    """
    if not assignments:
        raise ValueError("no assignments provided")
    counts = collections.Counter(assignments.values())
    n = sum(counts.values())
    p = np.array([c / n for c in counts.values()], dtype=np.float64)
    H = float(-(p * np.log(p)).sum())
    k_used = len(counts)
    return {
        "n_videos": n,
        "n_clusters_used": k_used,
        "entropy_nats": H,
        "entropy_normalized_by_used": H / math.log(k_used) if k_used > 1 else 0.0,
        "dominant_cluster_share": float(max(counts.values()) / n),
        "cluster_sizes": dict(sorted(counts.items(), key=lambda kv: str(kv[0]))),
    }


# ── Loading each representation family ──────────────────────────────────────

def load_kmeans_assignments(label_json: Path,
                            field: str = "phase_order_cluster") -> Dict[str, int]:
    """R1 — the k-means cluster id Paper 1 stored on each video record."""
    videos = json.loads(Path(label_json).read_text())
    return {v["video_id"]: int(v[field]) for v in videos}


def load_hmm_assignments(hmm_json: Path, mode: str = "causal") -> Dict[str, int]:
    """R3 — argmax latent state from a fitted-HMM output file."""
    payload = json.loads(Path(hmm_json).read_text())
    reps = payload.get("representations")
    if reps is None:
        raise ValueError(
            f"{hmm_json}: no 'representations' key — this looks like a "
            f"state-count sweep output, not a fitted-model output. Re-run "
            f"hmm.py without --sweep."
        )
    out = {}
    for vid, modes in reps.items():
        if mode not in modes:
            raise ValueError(f"{hmm_json}: video {vid} has no {mode!r} mode")
        out[vid] = int(np.argmax(modes[mode]))
    return out


# ── Comparison ──────────────────────────────────────────────────────────────

def compare_representations(named_assignments: Dict[str, Dict[str, int]]) -> Dict:
    """Variability per representation plus pairwise agreement between them."""
    if not named_assignments:
        raise ValueError("nothing to compare")

    variability = {name: assignment_variability(a)
                   for name, a in named_assignments.items()}

    names = sorted(named_assignments)
    agreement = {}
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            a, b = named_assignments[name_a], named_assignments[name_b]
            shared = sorted(set(a) & set(b))
            if len(shared) < 2:
                agreement[f"{name_a}__vs__{name_b}"] = {
                    "n_shared_videos": len(shared),
                    "adjusted_rand_index": float("nan"),
                    "note": "too few shared videos to compare",
                }
                continue
            entry = {
                "n_shared_videos": len(shared),
                "adjusted_rand_index": adjusted_rand_index(
                    [a[v] for v in shared], [b[v] for v in shared]),
            }
            # ARI is harsh on imbalanced partitions: when both families put
            # most videos in one cluster, agreement on the majority is
            # already expected by chance and the index is driven almost
            # entirely by the small clusters. Carry the imbalance alongside
            # the number so a low ARI is not over-read.
            max_dominant = max(variability[name_a]["dominant_cluster_share"],
                               variability[name_b]["dominant_cluster_share"])
            entry["max_dominant_cluster_share"] = max_dominant
            if max_dominant > 0.5:
                entry["caveat"] = (
                    f"one family assigns {max_dominant:.0%} of videos to a "
                    f"single cluster; ARI is dominated by the minority "
                    f"assignments and should not be read as a clean measure "
                    f"of construct agreement"
                )
            agreement[f"{name_a}__vs__{name_b}"] = entry
    return {"variability": variability, "agreement": agreement}


def seed_stability(assignments_by_seed: Dict[int, Dict[str, int]]) -> Dict:
    """How reproducible a categorical representation is across random seeds.

    Takes the same representation fitted under several seeds and reports
    the pairwise ARI distribution. This is the *ceiling* against which any
    other agreement number must be read: a cross-family ARI of 0.05 means
    something quite different when the representation agrees with itself
    at 0.98 than when it agrees with itself at 0.63.

    It is also a claim-validity check in its own right. A conditioning
    signal less stable than the effect it is claimed to produce cannot
    support that claim, and this is cheap to measure because workflow
    representations are computed offline before any training.
    """
    seeds = sorted(assignments_by_seed)
    if len(seeds) < 2:
        raise ValueError("need at least two seeds to measure stability")

    pairs = []
    for i, sa in enumerate(seeds):
        for sb in seeds[i + 1:]:
            a, b = assignments_by_seed[sa], assignments_by_seed[sb]
            shared = sorted(set(a) & set(b))
            if len(shared) < 2:
                continue
            pairs.append({
                "seed_a": sa, "seed_b": sb,
                "adjusted_rand_index": adjusted_rand_index(
                    [a[v] for v in shared], [b[v] for v in shared]),
            })
    if not pairs:
        raise ValueError("no seed pair shared enough videos to compare")

    aris = np.array([p["adjusted_rand_index"] for p in pairs], dtype=np.float64)
    return {
        "n_seeds": len(seeds),
        "n_pairs": len(pairs),
        "mean_ari": float(aris.mean()),
        "min_ari": float(aris.min()),
        "max_ari": float(aris.max()),
        "pairs": pairs,
    }


def format_comparison(per_dataset: Dict[str, Dict]) -> str:
    """Readable table across datasets and representations."""
    lines = ["Workflow variability by dataset and representation family",
             "=" * 78, ""]
    lines.append(f"{'dataset':<16} {'representation':<18} {'n':>4} {'K':>3} "
                 f"{'H (nats)':>9} {'H/logK':>8} {'top share':>10}")
    for dataset, result in per_dataset.items():
        for rep, v in result["variability"].items():
            lines.append(
                f"{dataset:<16} {rep:<18} {v['n_videos']:>4} "
                f"{v['n_clusters_used']:>3} {v['entropy_nats']:>9.3f} "
                f"{v['entropy_normalized_by_used']:>8.3f} "
                f"{v['dominant_cluster_share']:>10.1%}"
            )
    lines += ["", "Cross-family agreement (adjusted Rand index)", "-" * 78]
    for dataset, result in per_dataset.items():
        for pair, a in result["agreement"].items():
            ari = a["adjusted_rand_index"]
            verdict = (
                "same construct" if ari >= 0.5 else
                "partial overlap" if ari >= 0.2 else
                "DIFFERENT constructs — conditioning results are "
                "representation-specific"
            )
            lines.append(f"{dataset:<16} {pair:<40} ARI {ari:>6.3f}  {verdict}")
            if "caveat" in a:
                lines.append(f"{'':<16} {'':<40} note: {a['caveat']}")
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dataset", action="append", required=True,
                    metavar="NAME=KMEANS_LABELS[,HMM_JSON]",
                    help="Repeatable. e.g. "
                         "--dataset MB140=labels/mb140_fold0_labels_kmeans.json,"
                         "src/paper2_infra/workflow_representations/outputs/mb140_hmm.json")
    ap.add_argument("--hmm-mode", default="causal", choices=["causal", "oracle"],
                    help="Which HMM representation to hard-assign from.")
    ap.add_argument("--report-out", type=Path, default=None)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    per_dataset: Dict[str, Dict] = {}
    for spec in args.dataset:
        if "=" not in spec:
            raise SystemExit(f"--dataset needs NAME=PATH form, got {spec!r}")
        name, paths = spec.split("=", 1)
        parts = [p for p in paths.split(",") if p]
        assignments: Dict[str, Dict[str, int]] = {
            "kmeans (R1)": load_kmeans_assignments(Path(parts[0]))
        }
        if len(parts) > 1:
            assignments[f"hmm-{args.hmm_mode} (R3)"] = load_hmm_assignments(
                Path(parts[1]), mode=args.hmm_mode)
        per_dataset[name] = compare_representations(assignments)

    print(format_comparison(per_dataset))

    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(json.dumps(per_dataset, indent=2))
        logger.info("\nWrote %s", args.report_out)


if __name__ == "__main__":
    main()

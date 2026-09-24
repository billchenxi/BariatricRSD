# Supplementary Material

Non-text artifacts supporting the results in the main paper. The
written appendices are inside the main paper PDF; this folder holds
only data that backs specific claims in the paper.

All identifiers refer to public dataset names (MultiBypass140, Cholec80,
Bern, Strasbourg) or to internal run identifiers (e.g., `run033`) used
during training. No author identities, institutions, hostnames, or
private credentials are included. The folder is anonymized.

## Folder layout

```
supplementary_material/
├── README.md                              # this file
├── workflow_clusters/                     # offline TF-IDF + PCA + k-means artifacts
├── eval_metrics/
│   ├── phase_e_aggregate_metrics.json     # 5-fold × 3-seed metrics (Appendix C.1)
│   ├── phase_e_summary.{json,md}          # per-fold and overall mean ± std
│   ├── run041_tau_sweep/                  # posterior-temperature ablation
│   ├── run044_oracle_baseline/            # deployable matched-metric oracle/no-token
│   └── run045_shuffled_baseline/          # deployable matched-metric shuffled token
├── deployable_causal_eval/                # Run 035 per-checkpoint JSON summaries
│                                          #   (per-clip CSVs excluded for size)
└── manifests/
    ├── results_manifest.csv               # main-paper number → on-disk source
    └── weights_manifest.json              # SHA256 of trained checkpoints (weights on HF)
```

## What backs which claim

| Main-paper section | Numbers / claim | Backed by |
|---|---|---|
| §6.1 / Appendix C.1 | Within-center fold-0 MAE (no-token 13.03 ± 0.18, oracle 12.26 ± 0.09, decoupled 12.18 ± 0.14) | `eval_metrics/phase_e_summary.json` (FOLD0_REF derived from Run 033 best-val-MAE per training log) |
| Appendix C.1.2 | 5-fold × 3-seed extension (overall decoupled gain −0.19 min) | `eval_metrics/phase_e_aggregate_metrics.json` (Runs 038/039/040 across folds 1–4) |
| §6.x / Appendix B.4 | Posterior-temperature ablation (τ ∈ {0.01, 0.05, 0.1, 0.5, 1.0}; range 11.74–11.88 min) | `eval_metrics/run041_tau_sweep/*.json` |
| §6.5 deployable | Deployable matched-metric oracle/no-token (11.70, 11.10, 11.01) | `eval_metrics/run044_oracle_baseline/*.json` |
| §6.4 / §6.8 | Shuffled-token under deployable metric | `eval_metrics/run045_shuffled_baseline/*.json` |
| §6.5 / Appendix C.2 | Strict pixel-only causal (within-center −0.18; cross-center −0.22 vs no-token) | `deployable_causal_eval/*.json` (run033/run034 × {no-token, oracle, decoupled} × 3 seeds) |
| §3 / Appendix B | Workflow-cluster pipeline (TF-IDF/PCA/k-means; K=6 MB140, K=4 Cholec80; K=4/8 sweeps) | `workflow_clusters/*_kmeans_artifacts*.json`, `*_prefix_clusters.json` |
| Reproducibility | Trained checkpoints | `manifests/weights_manifest.json` (SHA256s; weights themselves on the code-URL Hugging Face deposit) |

## Conventions

- **Standard deviation** is sample std (ddof=1) over 3 seeds in the headline tables.
  The deployable-metric tables (Run 044 / 045) use population std (ddof=0) over the
  same 3 seeds; that distinction is documented in Appendix C of the main PDF.
- **Best-val-MAE** is the lowest validation MAE observed during training across all
  epochs; the corresponding checkpoint is the one whose SHA256 is recorded in
  `weights_manifest.json`.
- **Cluster artifacts** include the TF-IDF vocabulary, PCA components, k-means
  centroids, and the per-video cluster assignment; per-frame phase labels are
  *not* included (those are derivable from the public dataset annotations).

## Reproducing the analyses

Code to reproduce these JSONs is at the code URL listed in the main paper.
The workflow-cluster pipeline + evaluation harnesses (`evaluate_causal_rsd_pixel_only`)
are also released there. This zip contains only the precomputed outputs.

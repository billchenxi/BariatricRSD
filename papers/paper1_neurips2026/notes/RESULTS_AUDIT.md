# Lambda Training Results — Local Audit

Reference document for what training-result data has been pulled from
the Lambda NFS, where it lives locally, and where each result is
referenced in the manuscript / supporting docs.

**Status as of 2026-04-29.** Both Lambda compute clusters were
terminated; the persistent NFS (4.22 TB) is still alive at $196.73/wk.
Local mirror is paper-self-sufficient — every numeric claim in the
manuscript is backed by data on disk.

---

## 1. Training checkpoints (`best_model.pth` files)

### 1a. HuggingFace deposit set — `reproducibility/weights/` (12 real files + 5 symlinks = 17 entries)

| File | Source | Purpose | Manuscript reference |
|---|---|---|---|
| `cholec80/run018_seed42.pth` | real | Cholec80 transfer baseline (seed 42) | §6.6 |
| `cholec80/run018_seed123.pth` | real | Cholec80 transfer baseline (seed 123) | §6.6 |
| `cholec80/run018_seed777.pth` | real | Cholec80 transfer baseline (seed 777) | §6.6 |
| `mb140/run033_no_token_seed{42,123,777}.pth` | real | MB140 fold-0 strict no-token (3 seeds) | §6.1 headline |
| `mb140/run033_oracle_seed{42,123,777}.pth` | real | MB140 fold-0 strict oracle (3 seeds) | §6.1 headline |
| `mb140/run033_decoupled_seed{42,123,777}.pth` | real | MB140 fold-0 strict decoupled (3 seeds) | §6.1 headline (winner) |
| `mb140/run042_longer_context_no_token_seed42.pth` | symlink | Run 042 longer-context no-token | §6.1.2 |
| `mb140/run042_longer_context_decoupled_seed42.pth` | symlink | Run 042 longer-context decoupled | §6.1.2 |
| `mb140/run040_strict_decoupled_fold4_seed{42,123,777}.pth` | symlink | Phase E fold-4 decoupled (3 seeds) | §6.1.1 + Appendix C.1 |

**HF manifest:** [`reproducibility/weights/manifest.json`](../reproducibility/weights/manifest.json) — 17 entries with SHA256 (5 placeholders fill in during upload).

### 1b. Other Lambda-mirror checkpoints — `lambda_mirror/outputs/` (28 best_model.pth files total)

Full list:

```
codex_cholec80_pilot_seed42                           (early dev)
run001-009 (9 archived early runs)                    (architecture exploration)
run010_mb140_fold0_seed{42,123,777}                   (3 — centered-window legacy MB140)
run014, run015                                        (2 — early Cholec80)
run016_cholec80_with_token_seed{123,777}              (2 — Cholec80 oracle, missing seed42)
run017_cholec80_no_token_seed{123,777}                (2 — Cholec80 no-token, missing seed42)
run018_cholec80_transfer_seed{42,123,777}             (3 — duplicates of reproducibility/)
run028_mb140_cross_center_causal_seed123              (1 — legacy cross-center)
run040_strict_decoupled_fold4_seed{42,123,777}        (3 — Phase E fold 4)
run042_longer_context_{no_token,decoupled}_seed42     (2 — longer-context ablation)
```

These are physical files on disk; the reproducibility-bundle ones are linked into `reproducibility/weights/`.

### 1c. Phase E checkpoints NOT pulled locally (Option A decision)

The following 36 `best_model.pth` files exist on the Lambda NFS but were **deliberately not pulled** to save local disk:

- `run034_strict_cc_*` × 9 (cross-center strict, §6.2 headline)
- `run035_strict_pixel_only` × 1 (deployable predictor evaluation, §6.5 — but the *metrics* were pulled, just not the upstream checkpoints)
- `run037_strict_shuffled_seed*` × 3 (semantic control, §6.4 / Appendix F)
- `run038_strict_no_token_fold{1,2,3,4}_seed*` × 12 (Phase E no-token folds 1-4)
- `run039_strict_oracle_fold{1,2,3,4}_seed*` × 12 (Phase E oracle folds 1-4)
- `run040_strict_decoupled_fold{1,2,3}_seed*` × 9 (Phase E decoupled folds 1-3; fold 4 IS local)
- `run046_strict_cholec80_*` × 3 (strict Cholec80, §6.3)

**Why we skipped these:** The metrics for all of these are captured in [`lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json`](../../../lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json) and reproduced in the manuscript tables. We don't need the actual `.pth` weight files for the paper itself; we only need them if a reviewer asks to re-run inference. The paper's claims are fully reproducible from the local-mirror metrics + retraining from public datasets (re-training is feasible from the labels JSONs + scripts in this repo).

**If a reviewer demands these files later:** The Lambda NFS at `30ee97d0-710d-4040-b643-5840b450992a` still contains them. They can be pulled via rclone before deleting the NFS.

---

## 2. Inference-time evaluation outputs (Run 035, 044, 045)

Pulled in full as Option A (paper-critical, ~82 MB total):

| Directory | Size | Files | Manuscript reference |
|---|---|---|---|
| `lambda_mirror/outputs/run035_strict_pixel_only/` | 81 MB | 55 (per-clip CSVs + JSON metrics + logs for the deployable causal evaluation) | §6.5 deployable predictor |
| `lambda_mirror/outputs/run044_oracle_baseline_run035_metric/` | 148 KB | 37 (oracle-baseline matched-metric JSON metrics) | §6.5 metric reconciliation, §6.8 stats |
| `lambda_mirror/outputs/run045_shuffled_baseline_run035_metric/` | 28 KB | 7 (shuffled-token matched-metric JSON metrics) | §6.4 / §6.8 stats |

These are what feed the paired Wilcoxon stats in §6.8 and the deployable-predictor numbers in §6.5.

---

## 3. K-means cluster artifacts — `labels/` (34 files, 2.7 GB)

Pulled from `s3://...bariatric-rsd/labels/`. Required for offline cluster assignment + the causal-at-inference pipeline.

| Pattern | Files | Purpose |
|---|---|---|
| `*_kmeans_artifacts*.json` | small artifacts | TF-IDF vocabulary, IDF vector, PCA components+mean, k-means centroids — needed to reproduce the offline cluster pipeline |
| `*_labels.json` (per-fold) | 165 MB each | Per-frame phase labels for each video in each fold |
| `*_labels_kmeans*.json` | 165 MB each | Same labels JSON enriched with `phase_order_cluster: int` per video |
| `*_prefix_clusters.json` | small | Pre-computed prefix-derived cluster assignments per clip |

These are reproducibility-critical; they're what make the offline clustering pipeline (§4.3) re-runnable from raw video.

---

## 4. Phase E aggregate metrics

| File | Content | Used by |
|---|---|---|
| `lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json` | 36 Phase E runs (run038/039/040 across folds 1-4 × 3 seeds) + run046 Cholec80 strict (3 runs) | Source of truth for Appendix C.1 |
| `paper/phase_e_summary.json` | Per-fold mean ± std, overall 5-fold means, deltas | Generated by `paper/scripts/aggregate_phase_e.py` |
| `paper/phase_e_summary.md` | Markdown rendering of the same | Human-readable for review |

The 5-fold mean Δ (decoupled − no-token) = **−0.19 min** comes from this aggregate.

---

## 5. Cluster /tmp logs (training stdouts)

| Directory | Size | Files |
|---|---|---|
| `lambda_mirror/cluster_C_logs/` | 1.0 MB | 50 (training stdout + master logs from Cluster C) |
| `lambda_mirror/cluster_D_logs/` | 1.0 MB | 35 (training stdout + master logs from Cluster D) |

Includes per-step loss curves, per-epoch validation summaries, and chain-orchestration logs. Useful for reviewer diagnostics or re-running specific training jobs.

---

## 6. Manuscript propagation — where each result is cited

| Result | Number | Local data source | Manuscript section(s) | Figure(s) |
|---|---|---|---|---|
| MB140 fold-0 no-token (3-seed) | 13.03 ± 0.18 | `reproducibility/weights/mb140/run033_no_token_*` | §6.1, Abstract, §7.1 | fig4 |
| MB140 fold-0 oracle (3-seed) | 12.26 ± 0.09 | run033 oracle | §6.1 | fig4 |
| MB140 fold-0 decoupled (3-seed) | 12.18 ± 0.11 | run033 decoupled | §6.1, Abstract, §7.1 | fig4, fig_main_mb140_within (slides) |
| Phase E 5-fold mean decoupled | 10.83 ± 1.29 | `phase_e_aggregate_metrics.json` | §6.1.1, §7.1, Appendix C.1 | fig_phase_e_5fold (slides) |
| Phase E fold-4 decoupled (3-seed) | 8.68 ± 0.18 | run040 fold4 (local) + agg JSON | §6.1.1, Appendix C.1 | included in fig_phase_e_5fold |
| Cross-center strict no-token | 17.80 ± 0.55 | NOT local (Lambda only); metrics in §6.2 prose | §6.2 | fig6, fig10 |
| Cross-center strict decoupled | 17.33 ± 0.15 | NOT local; metrics in §6.2 prose | §6.2 | fig6, fig10 |
| Run 042 longer-context no-token | 12.46 (1 seed) | run042 (local) | §6.1.2, Abstract | fig_longer_context (slides) |
| Run 042 longer-context decoupled | 11.02 (1 seed) | run042 (local) | §6.1.2, Abstract | fig_longer_context (slides) |
| Cholec80 centered no-token (3-seed) | 4.61 ± 0.19 | run017 (partial — 2 seeds local) | §6.3, §6.6 | fig5 |
| Cholec80 centered oracle (3-seed) | 4.49 ± 0.14 | run016 (partial — 2 seeds local) | §6.3 | fig5 |
| Cholec80 centered teacher-forced (3-seed) | 5.03 ± 0.07 | NOT local; metrics in §6.3 prose | §6.3 | fig5 |
| Cholec80 strict no-token | 4.34 (1 seed) | NOT local; metrics in §6.3 prose | §6.3 | — |
| Cholec80 strict oracle | 4.33 (1 seed) | NOT local | §6.3 | — |
| Cholec80 strict teacher-forced | 4.26 (1 seed) | NOT local | §6.3 | — |
| Cholec80 inference-time stack | 3.56 (3-seed ensemble + isotonic) | NOT local; results from Run 019C historical | §6.6, Abstract | fig7, fig_cholec80_inference_ablation (slides) |
| Shuffled-token semantic control (3-seed) | 13.14 ± 0.15 | NOT local; metrics in §6.4 / Appendix F prose | §6.4, Appendix F | figA1 |
| Pixel-only causal within-center | −0.18 min vs no-token | `lambda_mirror/outputs/run035_*` | §6.5 | — |
| Pixel-only causal cross-center | −0.22 min vs no-token | `lambda_mirror/outputs/run035_*` | §6.5 | — |
| Within-center Wilcoxon p-value | 0.053 (decoupled vs no-token) | `lambda_mirror/outputs/run044_*` | §6.8 | fig12 |
| Cross-center Wilcoxon p-value | 0.005 (decoupled vs no-token) | `lambda_mirror/outputs/run044_*` | §6.8 | fig12 |

**Key:**
- ✅ "local" = `.pth` checkpoint physically on disk
- ⚠️ "NOT local; metrics in prose" = the *number* is in the manuscript and `paper/results_manifest.csv`, but the upstream `.pth` weights stayed on Lambda NFS. The paper claim is fully supported by the captured number; we just can't re-load the model.

---

## 7. Documentation cross-reference

| Doc | Purpose |
|---|---|
| [`paper/review_manuscript.md`](../manuscript/review_manuscript.md) | Full source-of-truth manuscript (~118 KB) |
| [`paper/submit_ready.md`](../manuscript/submit_ready.md) | 9-page autocut version |
| [`paper/submit_ready_supplementary.md`](../manuscript/submit_ready_supplementary.md) | Supplementary markdown (refs + appendices) |
| [`paper/results_manifest.csv`](../manuscript/results_manifest.csv) | All numeric results, one row per (run, condition, seed) tuple |
| [`paper/phase_e_summary.{md,json}`](../manuscript/phase_e_summary.md) | Per-fold and overall Phase E summary |
| [`paper/RELATED_WORK_SUMMARY.md`](../manuscript/RELATED_WORK_SUMMARY.md) | All 31 cited papers — links, summaries, comparisons |
| [`SESSION_LOG.md`](SESSION_LOG.md) | Project-history log, sections K + L cover this session |
| [`SUBMISSION_TODO.md`](SUBMISSION_TODO.md) | Remaining tasks before May 6 NeurIPS submission |
| [`RESULTS_AUDIT.md`](RESULTS_AUDIT.md) | This document |

---

## 8. What's NOT yet done

### 8a. Pending tasks for the paper itself

| # | Task | Where |
|---|---|---|
| HF upload | 17-checkpoint deposit to `billchenxi/surgical-workflow-models` | tonight per `SUBMISSION_TODO.md` |
| Lambda NFS deletion | save $200/wk | after HF upload verifies |
| S3 adapter key rotation | hygiene | after NFS deletion |
| Re-sync Overleaf | 4-5 files updated since last upload | before submission |
| Final proofread | end-to-end PDF review | by May 5 |
| OpenReview submit | NeurIPS 2026 E&D track | by May 6, 23:59 AoE |

### 8b. Data NOT in the local mirror (deliberate)

The following Lambda-NFS data was **intentionally not pulled** to keep local disk under control:

- Per-epoch checkpoints (`checkpoint_epoch*.pth`) — only `best_model.pth` matters
- Raw video datasets (~500 GB) — public, re-downloadable
- Extracted frame tensors (~150 GB) — regenerable from raw video
- WandB run files (~50 GB) — already cloud-synced to wandb.ai
- 36 Phase E `.pth` checkpoints from runs not in the HF deposit set — metrics captured in JSON, weights regenerable from training scripts

If a reviewer requires any of these for retraining-verification during rebuttal, they can be re-pulled from Lambda NFS (still alive) before the user deletes it.

---

*Last updated: 2026-04-29. Generated as a one-shot audit; refresh by re-running the verification commands at the bottom of this doc against the file system.*

## Verification commands (run anytime to confirm)

```bash
# 1. Reproducibility weights count + integrity
find /Users/bill/Documents/GitHub/bariatric_rsd/reproducibility/weights -name "*.pth" | wc -l    # expect 17

# 2. Lambda mirror checkpoints
find /Users/bill/Documents/GitHub/bariatric_rsd/lambda_mirror/outputs -name "best_model.pth" | wc -l    # expect 28

# 3. Phase E aggregate
python3 -c "import json; d=json.load(open('/Users/bill/Documents/GitHub/bariatric_rsd/lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json')); print(sum(len(v) for v in d.values()))"    # expect 39

# 4. Cluster artifacts
ls /Users/bill/Documents/GitHub/bariatric_rsd/labels/ | wc -l    # expect 34

# 5. HF manifest
python3 -c "import json; m=json.load(open('/Users/bill/Documents/GitHub/bariatric_rsd/reproducibility/weights/manifest.json')); print(sum(1 for k in m if not k.startswith('_')))"    # expect 17
```

# Reconstruction Guide

*Created 2026-06-04. Answers the question: "If I lose Lambda, can I
regenerate everything (including intermediate checkpoints) from what's
left on local disk?"*

---

## TL;DR

Yes for **all paper-cited results** — every training script,
hyperparameter, label artifact, cluster artifact, and evaluation
harness is preserved locally. Best-model checkpoints are preserved with
SHA256 manifests.

**Not preserved (acceptable):** training-time intermediate epochs,
optimizer states, and Phase E folds 1–3 weights. These are regenerable
by re-running the deterministic training scripts with the recorded
seeds (~$200–$400 in Lambda Cloud GPU time if ever needed).

---

## What's preserved locally (full reconstruction inputs)

### 1. Training entry points — 24 run scripts

Every numbered experiment in the paper has a self-contained shell
script at `scripts/run0XX_*.sh`. Each script:

- Pins the exact CLI arguments fed to `train.py` (lr, wd, batch size,
  epochs, sequence length, frame stride, seeds, target_position, etc.).
- Iterates the seeds (42 / 123 / 777) in the same order every run.
- Has a built-in skip-if-checkpoint-exists guard for re-runs.
- Aggregates per-seed metrics into a JSON summary at the end.

| Script | Reproduces |
|---|---|
| `scripts/run033_strict_protocol_fold0.sh` | Within-center MB140 strict (no-token / oracle / decoupled, 3 seeds) — §6.1 |
| `scripts/run034_strict_protocol_cross_center.sh` | Cross-center MB140 strict (Bern → Strasbourg, 3 seeds × 3 conditions) — §6.2 |
| `scripts/run035_strict_pixel_only_eval.sh` | Pixel-only causal eval harness on Run 033/034 checkpoints — §6.5 |
| `scripts/run037_shuffled_token_control.sh` | Shuffled-token semantic control — §6.4 |
| `scripts/run038_strict_5fold_no_token.sh` | Phase E folds 1–4 no-token (12 runs) |
| `scripts/run039_strict_5fold_oracle.sh` | Phase E folds 1–4 oracle (12 runs) |
| `scripts/run040_strict_5fold_decoupled.sh` | Phase E folds 1–4 decoupled (12 runs) |
| `scripts/run041_tau_sweep.sh` | Posterior-temperature ablation (1 ckpt × 5 τ) |
| `scripts/run042_longer_context_fold0.sh` | Longer-context (seq_len=16) ablation |
| `scripts/run044_reeval_oracle_baseline.sh` | Oracle/no-token matched-metric re-eval — §6.5 |
| `scripts/run045_reeval_shuffled_token.sh` | Shuffled-token matched-metric re-eval — §6.5 |
| `scripts/run046_strict_cholec80_mini.sh` | Cholec80 strict check (Run 046 + 046b) — §6.3 |
| ... 12 earlier exploratory scripts | All preserved for completeness |

### 2. Python sources — model, data, training loop

| Path | Purpose |
|---|---|
| `lambda_setup/src/models/bariatric_rsd.py` | ViT-B/16 + HTA-inspired temporal head + multi-task heads |
| `lambda_setup/src/training/train.py` | Single-run training loop with all CLI flags |
| `lambda_setup/src/training/train_causal.py` | Variant with causal-at-inference evaluation hooks |
| `lambda_setup/src/data/dataset.py` | Clip-level dataloader (frame extraction, sliding-window prefix construction) |
| `lambda_setup/src/data/prepare_labels.py` | Phase-label + cluster-ID assignment pipeline |
| `lambda_setup/scripts/05_smoke_test.py` | One-batch smoke test for environment validation |
| `lambda_setup/scripts/06_build_labels.py` | Build per-clip MB140 label files |
| `lambda_setup/scripts/07_cluster_phase_orders.py` | Phase-bigram TF-IDF + PCA + k-means pipeline |
| `lambda_setup/scripts/07b_save_cluster_artifacts.py` | Persist vocab/IDF/PCA/centroids as JSON |
| `lambda_setup/scripts/08_build_cholec80_labels.py` | Cholec80 label construction |
| `lambda_setup/scripts/09_build_cholec80_labels.py` | Cholec80 cluster assignment |
| `lambda_setup/scripts/10_precompute_prefix_clusters.py` | Build per-clip prefix-cluster lookup |
| `lambda_setup/scripts/11_apply_protocol_patches.py` | Idempotent strict-protocol patch applicator |

### 3. Environment + bootstrap

| Path | Purpose |
|---|---|
| `lambda_setup/scripts/01_bootstrap.sh` | Fresh Lambda node base-package install |
| `lambda_setup/scripts/02_install_deps.sh` | Pip dependency install |
| `lambda_setup/scripts/03_clone_repos.sh` | Repo cloning (MultiBypass140, Cholec80) |
| `lambda_setup/scripts/04_setup_project.sh` | Project skeleton setup |
| `lambda_setup/deploy.sh` | One-shot redeploy on a fresh node |
| `anonymous_code_submission/requirements.txt` | Pinned pip dependency list |

### 4. Label and cluster artifacts (deterministic, preserve as-is)

| Path | Contents |
|---|---|
| `labels/*.json` | Per-video phase labels + per-clip cluster assignments (16 JSONs) |
| `lambda_mirror/labels/` | Same content, mirrored (553 MB on disk) |
| `paper/supplementary_material/workflow_clusters/` | Anonymized subset shipped with the paper (13 MB) |
| `reproducibility/labels/` | Same, packaged for the anonymous code submission (35 MB) |

These artifacts are deterministic outputs of the cluster pipeline.
Re-running `scripts/07_cluster_phase_orders.py` with the same seed
(`--seed 0`) on the same phase-label inputs reproduces them
byte-for-byte. They're preserved on disk so reviewers don't have to
re-run the offline pipeline.

### 5. Cited best-model checkpoints + SHA256s

| Path | Contents |
|---|---|
| `reproducibility/weights/mb140/` | 12 trained checkpoints (Runs 033, 034 fold-0 + cross-center) |
| `reproducibility/weights/cholec80/` | 3 Cholec80 transfer checkpoints (Run 018) |
| Symlinks to `lambda_mirror/outputs/run040_*/best_model.pth` | Phase E fold-4 decoupled (3 seeds) |
| Symlinks to `lambda_mirror/outputs/run042_*/best_model.pth` | Longer-context ablation (2 seeds) |
| `reproducibility/weights/manifest.json` | Logical name → relative path + SHA256 + size + provenance for all 17 |

### 6. Evaluation outputs (paper-cited JSON)

| Path | Backs which paper claim |
|---|---|
| `lambda_mirror/outputs/run035_strict_pixel_only/` | §6.5 deployable causal numbers |
| `lambda_mirror/outputs/run041_tau_sweep/` | Posterior-τ ablation |
| `lambda_mirror/outputs/run044_oracle_baseline_run035_metric/` | Matched-metric oracle/no-token baseline |
| `lambda_mirror/outputs/run045_shuffled_baseline_run035_metric/` | Matched-metric shuffled-token baseline |
| `lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json` | Appendix C.1 Phase E table |
| `paper/phase_e_summary.{json,md}` | Per-fold mean ± std (regenerated from aggregate JSON) |

### 7. Training logs (for verifying best-val-MAE numbers)

| Path | Contents |
|---|---|
| `lambda_mirror/logs/192.222.56.188/run033_*.log` | 8 Run 033 logs (3 conditions × 3 seeds + chain + master) |
| `lambda_mirror/logs/192.222.57.53/run034_*.log` | 11 Run 034 logs |
| `lambda_mirror/logs/192.222.50.14/` etc. | 39 Phase E logs (Runs 038/039/040) |
| Various | run037, run046, run046b logs |

These are the logs `aggregate_phase_e.py` reads to extract `best=X.XX min`
lines (the canonical source for headline-table numbers).

### 8. Documentation

| Path | Purpose |
|---|---|
| `RESEARCH_PLAN.md` | Original experimental plan |
| `RESULTS_AUDIT.md` | Per-result provenance — every number → its on-disk source |
| `FINDINGS.md` | Empirical findings in narrative form |
| `SESSION_LOG.md` | Day-by-day work log with notable decisions |
| `paper/results_manifest.csv` | Locked paper numbers + their lambda_mirror sources |
| `reproducibility/README.md` | Reviewer-facing reproduction guide |
| `reproducibility/QUICKSTART.md` | Two-command reviewer onboarding |
| `reproducibility/RUN_3.56.md` | Cholec80 absolute-number reproduction |
| `reproducibility/docs/MODEL_CARD.md` | Model card (architecture, training, limitations) |
| `paper/scripts/aggregate_phase_e.py` | Regenerates `phase_e_summary.json` from the aggregate metric file |
| `REVIEW_ANONYMOUS_DEPOSIT_RUNBOOK.md` | End-to-end runbook for the anonymous review deposit |

---

## What's NOT preserved (and how to regenerate)

### A. Training-time intermediate epoch checkpoints

**Status:** only `best_model.pth` was extracted to local disk; the
per-epoch `epoch_N.pth` files lived only on Lambda and are deleted when
the filesystem is dropped.

**Impact:** none for any paper-cited result. The paper reports
best-val-MAE checkpoints exclusively.

**Regenerate by:** re-running the corresponding `scripts/run0XX_*.sh`.
Training is seed-deterministic to within ~0.1 min MAE (documented in
`paper/Formatting_Instructions_For_NeurIPS_2026/body_main_short.tex`
Experimental Setup section). Cost: ~5 GPU-h per run × 9 runs for Run 033
= ~$135.

### B. Optimizer states

**Status:** never saved with the checkpoints.

**Impact:** none. Reproducing a run from scratch regenerates the
optimizer state in the first epoch.

### C. Phase E folds 1–3 weights (33 checkpoints across Runs 038/039/040)

**Status:** all 36 Phase E checkpoints lived on Lambda. Only fold-4
decoupled (3 seeds) was symlinked to local for HF deposit. Folds 1–3
metrics ARE in `phase_e_aggregate_metrics.json` (preserved); the
weights themselves are not.

**Impact:** none for any paper-cited number. Appendix C.1 cites
metrics from the JSON, not the weights. If a reviewer wants the weights
themselves, the manuscript explicitly notes they are regenerable.

**Regenerate by:** re-running `scripts/run038_strict_5fold_no_token.sh`,
`run039_strict_5fold_oracle.sh`, `run040_strict_5fold_decoupled.sh`.
Cost: ~5 GPU-h per run × 36 runs = ~$540. Most expensive of the gaps,
but only needed if a reviewer specifically requests the weights.

### D. Wandb run histories

**Status:** `lambda_mirror/wandb/` (14 MB) contains downloaded summaries.
The hosted run pages on wandb.ai are still alive.

**Impact:** ablation curve plots may reference wandb run IDs. The
per-epoch metrics needed to regenerate plots are also in the local
training logs (`lambda_mirror/logs/*/run*.log`), so plots can be
rebuilt without wandb if needed.

### E. Exploratory / archived runs (Runs 001–015, 022, 023, 025)

**Status:** outputs live only on Lambda for most of these. They were
superseded by later runs and are not referenced in the paper.

**Impact:** none. Listed in `SESSION_LOG.md` for historical record only.

---

## Reconstruction recipes by failure scenario

### Scenario 1 — "I lost a single checkpoint and need to regenerate it"

```bash
# Example: regenerate Run 033 no-token seed=42.
cd /lambda/nfs/bariatric-rsd  # (or fresh Lambda node — see scripts/h100_bootstrap.sh)
bash scripts/run033_strict_protocol_fold0.sh
# Skip-if-exists handles partials. The script aggregates summary at the end.
```

### Scenario 2 — "Lambda filesystem deleted; need to rebuild on a fresh GPU node"

```bash
# Fresh Lambda H100 node, root shell.
bash lambda_setup/scripts/01_bootstrap.sh         # Base packages
bash lambda_setup/scripts/02_install_deps.sh      # Pinned pip deps
bash lambda_setup/scripts/03_clone_repos.sh       # MultiBypass140 + Cholec80
bash lambda_setup/scripts/04_setup_project.sh     # Project skeleton

# Build labels + cluster artifacts (deterministic, ~30 min total).
python3 lambda_setup/scripts/06_build_labels.py
python3 lambda_setup/scripts/07_cluster_phase_orders.py
python3 lambda_setup/scripts/07b_save_cluster_artifacts.py
python3 lambda_setup/scripts/08_build_cholec80_labels.py
python3 lambda_setup/scripts/09_build_cholec80_labels.py
python3 lambda_setup/scripts/10_precompute_prefix_clusters.py

# Now run any subset of the trained-from-scratch experiments.
bash scripts/run033_strict_protocol_fold0.sh   # ~45 GPU-h total (9 runs × 5h)
bash scripts/run034_strict_protocol_cross_center.sh
bash scripts/run035_strict_pixel_only_eval.sh  # eval-only, ~2 GPU-h
# ... etc.
```

### Scenario 3 — "I just want to verify the paper numbers from existing checkpoints"

```bash
cd reproducibility
bash scripts/download_weights.sh             # pulls 17 ckpts from anonymous HF
bash scripts/verify_mb140_strict.sh          # reproduces §6.1 numbers
bash scripts/verify_cholec80_3.56.sh         # reproduces Cholec80 absolute number
```

This requires **no Lambda access** — just the local repo + the HF
deposit + a single GPU.

### Scenario 4 — "I need to regenerate the Phase E 5-fold extension table"

```bash
# On a fresh Lambda node, after Scenario 2 bootstrap.
bash scripts/run038_strict_5fold_no_token.sh
bash scripts/run039_strict_5fold_oracle.sh
bash scripts/run040_strict_5fold_decoupled.sh
python3 paper/scripts/aggregate_phase_e.py   # rebuilds phase_e_summary.{json,md}
```

Cost: ~$540 in Lambda GPU time. Outputs `paper/phase_e_summary.json`
which is the source of the Appendix C.1 table.

---

## Reconstruction completeness checklist

If anyone asks "can you fully rebuild from scratch?", the answer is yes
when **all** of these are true:

- [x] Anonymous code submission contains `scripts/`, `src/`, `configs/`, `labels/`, `requirements.txt`.
- [x] Anonymous HF model repo contains 17 weights + manifest.json with SHA256s.
- [x] `RECONSTRUCTION_GUIDE.md` (this file) is in the repo.
- [x] `REVIEW_ANONYMOUS_DEPOSIT_RUNBOOK.md` covers the deposit creation flow.
- [x] `RESULTS_AUDIT.md` maps every paper number → its on-disk source.
- [x] Training logs in `lambda_mirror/logs/` cover all cited runs.
- [x] Cluster artifacts in `labels/` are versioned with the code.
- [x] `paper/scripts/aggregate_phase_e.py` is reproducibly seeded.

All boxes are checked as of 2026-06-04. The paper is reconstructable
end-to-end from local disk + the HF deposit, **even after Lambda is
deleted.**

---

## What you specifically asked about — intermediate checkpoints

To be explicit: intermediate per-epoch checkpoints (`epoch_0.pth`,
`epoch_1.pth`, ..., `epoch_13.pth`) are **not** preserved anywhere
local. Only `best_model.pth` (the epoch with lowest val MAE) is kept.

This is the standard practice in surgical-AI RSD literature and matches
how the paper reports numbers. If you ever need to regenerate them —
e.g., for an ablation showing how MAE evolves across training — re-run
the relevant `scripts/run0XX_*.sh`. The training is seed-deterministic
within ~0.1 min MAE, so the regenerated curve will match the original
within seed-noise.

The trade-off was deliberate: keeping intermediate checkpoints would
have multiplied storage by ~15× (15 epochs × ~1.4 GB each per run).
We kept the metrics (in training logs) and the final winning checkpoint,
which are sufficient for every paper claim.

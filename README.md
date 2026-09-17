# BariatricRSD

**Multi-Task Hierarchical Temporal Attention with Phase-Order Conditioning for Surgical Video Analysis**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch 2.0+](https://img.shields.io/badge/pytorch-2.0+-ee4c2c.svg)](https://pytorch.org/)

BariatricRSD is an end-to-end Transformer framework for surgical video analysis that jointly performs three tasks from a single model: remaining surgery duration (RSD) prediction, intraoperative deviation detection, and surgical phase recognition. It also includes an automated operation log generator for real-time surgical documentation.

> **Paper:** *BariatricRSD: Joint Remaining Surgery Duration Prediction and Intraoperative Deviation Detection via Multi-Task Hierarchical Temporal Attention with Phase-Order Conditioning*
> Submitted to NeurIPS 2026 Datasets & Benchmarks (#706).

---

## Repository status (2026-08-10)

> **Planning:** all forward-looking strategy — direction, data, venues,
> funding, and the commercialization path — is consolidated in
> [`docs/STRATEGY.md`](plans/STRATEGY.md) (2026-09-17). It also records
> open conflicts, including Paper 1's acceptance status below.

| Track | State |
|---|---|
| **Paper 1** — NeurIPS 2026 E&D #706 | Submitted; awaiting notification (Sept 2026). Reviewer responses drafted in [`docs/paper1_neurips2026/REBUTTAL_FILING_READY.md`](papers/paper1_neurips2026/notes/REBUTTAL_FILING_READY.md). Log: [`SESSION_LOG.md`](papers/paper1_neurips2026/notes/SESSION_LOG.md) *(closed)* |
| **Paper 2A** — foundation-model causal benchmark | **Phase 0**: CPU-side infrastructure complete, hardware/access items blocked. See [`PHASE_0_REPORT.md`](papers/paper2_forecasting/phase_0/PHASE_0_REPORT.md) and [`SESSION_LOG.md`](papers/paper2_forecasting/SESSION_LOG.md) *(active)* |
| **Compute** | No GPU instance running. Lambda filesystem decommissioned June 2026. |

> ⚠️ **Datasets are not present in this checkout.** The raw MB140 and
> Cholec80 frames lived on the decommissioned Lambda filesystem and must
> be re-acquired before any feature extraction (Cholec80 requires a fresh
> CAMMA data-use agreement). `lambda_mirror/` retains outputs, logs and
> labels — enough to reproduce reported *numbers*, not to retrain.

Two Phase 0 findings materially affect how results in this repository
should be read:

- **[Fold-variance dominance](papers/paper2_forecasting/phase_0/PHASE_0_FINDING_FOLD_VARIANCE.md)** —
  on MB140, 98% of the paired conditioning effect's variance is
  between-fold and 2% between-seed. Effects below ~0.5 min are not
  resolvable on a 5-fold split at any seed count.
- **[Workflow-representation non-identifiability](papers/paper2_forecasting/phase_0/PHASE_0_FINDING_REPRESENTATION.md)** —
  the k-means phase-order cluster id is unstable to the random seed alone
  (ARI 0.63 on MB140) and is not recovered by an independent
  representation family (ARI 0.03–0.08).

---

## Key Features

- **Phase-Order Conditioning Token** — A learnable embedding that encodes the surgeon's procedural style (a k-means cluster over phase-transition bigrams, K=6 in the reported runs), prepended to the Transformer temporal sequence. *See the non-identifiability caveat above: this cluster id is seed-unstable on MB140, and Paper 2A moves to a continuous workflow vector.*
- **Hierarchical Temporal Attention (HTA)** — Multi-scale temporal attention at local, medium, and global scales, adapted from Surgformer (MICCAI 2024).
- **Multi-Task Learning** — Joint RSD regression + deviation detection + phase recognition with shared representations.
- **Automated Operation Logging** — Real-time generation of structured surgical reports from model predictions.
- **100% Open-Source** — Built entirely on PyTorch, timm, and einops. No proprietary dependencies.

## Architecture

```
Video Clip (B, T, 3, 224, 224)
       |
  Visual Encoder (ResNet-50 / HecVL, via timm)
       |
  (B, T, 2048) --> Projection --> (B, T, 512)
       |
  +-- Phase-Order Token prepended --+
  |                                  |
  Hierarchical Temporal Attention    |
  (4 blocks, 8 heads, 3 scales)     |
       |                             |
  (B, T, 512)                       |
       |                             |
  +----+----+----+                   |
  |    |    |    |                   |
 RSD  Dev Phase  Operation Log  <----+
 Head Head Head  (application layer)
```

## Installation

```bash
# Clone the repository
git clone https://github.com/billchenxi/BariatricRSD.git
cd BariatricRSD

# Install in development mode
pip install -e ".[dev,wandb]"

# Or install dependencies directly
pip install -r requirements.txt
```

### Requirements

- Python >= 3.9
- PyTorch >= 2.0
- CUDA-capable GPU (A100 80GB recommended, A10 24GB minimum)

## Quick Start

### 1. Prepare Data

**Cholec80** (for baseline experiments):
```bash
# Request access at http://camma.u-strasbg.fr/datasets
# Then extract frames:
bash scripts/extract_cholec80_frames.sh /path/to/cholec80/videos /path/to/cholec80/frames
```

**MultiBypass140** (for RYGB experiments):
```bash
# Request access at https://github.com/CAMMA-public/MultiBypass140
```

### 2. Train

```bash
# Experiment 1.1: Cholec80 RSD-only baseline
python -m bariatric_rsd.train_cholec80 \
    --video_root /data/cholec80/frames \
    --annotation_dir /data/cholec80/phase_annotations \
    --output_dir ./experiments/cholec80_rsd_only \
    --phase_weight 0.0 --deviation_weight 0.0 \
    --wandb

# Experiment 1.2: Cholec80 RSD + Phase recognition
python -m bariatric_rsd.train_cholec80 \
    --video_root /data/cholec80/frames \
    --annotation_dir /data/cholec80/phase_annotations \
    --output_dir ./experiments/cholec80_multitask \
    --phase_weight 0.3 --deviation_weight 0.0 \
    --wandb

# Full model on bariatric (RYGB) data
python -m bariatric_rsd.train \
    --video_root /data/rygb/frames \
    --annotation_json /data/rygb/annotations.json \
    --output_dir ./experiments/rygb_full \
    --rsd_weight 1.0 --deviation_weight 0.5 --phase_weight 0.3 \
    --wandb
```

### 3. Evaluate

```bash
python -m bariatric_rsd.evaluate \
    --checkpoint ./experiments/rygb_full/checkpoints/best_model.pth \
    --video_root /data/rygb/frames \
    --annotation_json /data/rygb/annotations.json \
    --output_dir ./experiments/rygb_full/evaluation
```

### 4. Generate Operation Log

```bash
python -m bariatric_rsd.inference.run_inference \
    --checkpoint ./experiments/rygb_full/checkpoints/best_model.pth \
    --video_root /data/videos/case_042 \
    --output_dir ./reports/case_042 \
    --procedure RYGB \
    --surgeon "Dr. Smith"
```

This produces a structured operative report:
```
================================================================
  INTRAOPERATIVE OPERATION LOG
  Automatically generated by BariatricRSD
================================================================
  Procedure:    RYGB
  Duration:     87.3 minutes
  Deviations:   2 detected

----------------------------------------------------------------
  PHASE SUMMARY
----------------------------------------------------------------
  00:00:00 - 00:22:15  Gastric Pouch Creation (GPC)        (22m 15s)
  00:22:15 - 00:51:40  Gastro-Jejunal Anastomosis (GJA)    (29m 25s)
  00:51:40 - 01:27:18  Jejuno-Jejunal Anastomosis (JJA)    (35m 38s)

----------------------------------------------------------------
  EVENT TIMELINE
----------------------------------------------------------------
  00:00:00  [NOTE]     Operation logging started
  00:00:00  [PHASE]    Phase started: Gastric Pouch Creation (GPC)
  00:21:48  [PROG]     Surgery 25% complete
  00:22:15  [PHASE]    Phase started: Gastro-Jejunal Anastomosis (GJA)
  00:34:12  [! DEV]    Deviation detected during GJA (severity: 72%)
  00:34:57  [DEV !]    Deviation resolved — duration: 45s
  ...
================================================================
```

## Project Structure

Code, documentation, plans, and per-paper material are kept separate.

```
src/                             # ALL code (importable, src-layout)
  bariatric_rsd/                 # Core model + training package
    config.py                    # Dataclass-based configuration
    train.py                     # Training entry point (bariatric data)
    train_cholec80.py            # Training entry point (Cholec80)
    evaluate.py                  # Evaluation entry point
    data/       annotation_parser.py, surgical_dataset.py
    models/     visual_encoder.py, temporal_model.py, bariatric_rsd.py
    training/   trainer.py        # Training loop with AMP, early stopping
    evaluation/ metrics.py        # RSD, deviation, phase metrics
    inference/  operation_log.py, run_inference.py
  brsd_lib/                      # Paper 1 analysis library (CPU-only)
    causal_cluster.py            # Prefix-only workflow cluster assignment
    evaluate.py, stats.py, smoothing.py, ensemble.py, overfit_filter.py
  paper2_infra/                  # Paper 2 infrastructure (CPU-only)
    backbone_features/extract.py            # Frozen-backbone extraction + registry
    evaluation/evaluate_phase_anticipation.py  # Strict prefix-only Task A/B
    evaluation/fold_stability.py            # Variance decomposition + budgeting
    workflow_representations/    hmm.py, compare.py, duration_aware_kmeans.py

tests/                           # pytest suites (146 passing)
scripts/                         # Operational + experiment scripts
  lambda_setup/                  # Lambda Cloud provisioning bundle
  paper1_runs/                   # run0NN_*.sh experiment drivers for Paper 1
  extract_cholec80_frames.sh, sync_from_lambda.sh, h100_bootstrap.sh

plans/                           # Forward-looking strategy
  STRATEGY.md                    # Single authoritative planning document
  grants/                        # Resource-access applications
  archive/                       # Superseded plans

docs/                            # Reference documentation
  runbooks/                      # Lambda deploy / HF upload / shutdown / setup

papers/                          # One directory per paper
  paper1_neurips2026/            # "When Does Workflow Conditioning Help RSD?"
    manuscript/                  # Drafts, figures, slides, poster, exports
    notes/                       # Findings, audits, rebuttal, closed log
    reproducibility/             # Cited checkpoints, manifest, verify scripts
  paper2_forecasting/            # Stable workflow representations (active)
    phase_0/                     # Feasibility findings and backbone matrix
    SESSION_LOG.md               # Active development log

labels/                          # Per-video phase label + cluster artifacts
lambda_mirror/                   # Archived run outputs and logs (gitignored)
notebooks/                       # Exploratory analysis
archive/                         # Superseded trees, kept on disk, untracked
```

**Adding a paper.** Create `papers/paperN_<topic>/` with the same shape —
`manuscript/`, `notes/`, and whatever artifacts it needs. Shared code belongs in
`src/`; anything paper-specific stays under that paper's directory.

## Training Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--encoder` | `resnet50` | Visual encoder backbone (any timm model) |
| `--embed_dim` | `512` | Transformer embedding dimension |
| `--hta_depth` | `4` | Number of HTA blocks |
| `--hta_heads` | `8` | Attention heads |
| `--clip_length` | `16` | Frames per clip |
| `--sampling_rate` | `4` | Sample every Nth frame |
| `--lr` | `1e-4` | Learning rate |
| `--rsd_weight` | `1.0` | RSD loss weight |
| `--deviation_weight` | `0.5` | Deviation loss weight |
| `--phase_weight` | `0.3` | Phase loss weight |
| `--seed` | `444` | Random seed |

## Benchmarks

### Datasets

| Dataset | Videos | Procedure | Annotations | Distinct phase orders |
|---------|--------|-----------|-------------|----------------------:|
| [Cholec80](http://camma.u-strasbg.fr/datasets) | 80 (72 phase-labeled) | Cholecystectomy | Phase (7 classes) | 6 |
| [MultiBypass140](https://github.com/CAMMA-public/MultiBypass140) | 140 (70 Bern + 70 Strasbourg) | RYGB | Phase (14 classes) + Deviation | 104 |

The last column is the workflow-heterogeneity gap the papers turn on, and
it is also why the two benchmarks behave so differently under categorical
workflow conditioning — see the non-identifiability finding linked above.

### Results — MB140 RSD under the strict prefix-only protocol

Five folds × three seeds, mean val MAE in minutes. Reproduce the analysis
with `python -m paper2_infra.evaluation.fold_stability --summary-json
paper/phase_e_summary.json --baseline no_token --treatment decoupled`.

| Fold | No token | Oracle | Decoupled | Δ decoupled |
|---|---:|---:|---:|---:|
| 0 *(development split)* | 13.03 ± 0.18 | 12.26 ± 0.09 | 12.18 ± 0.14 | **−0.85** |
| 1 | 11.29 ± 0.13 | 11.32 ± 0.29 | 11.07 ± 0.13 | −0.23 |
| 2 | 11.60 ± 0.19 | 11.62 ± 0.26 | 11.84 ± 0.14 | +0.23 |
| 3 | 10.27 ± 0.07 | 10.32 ± 0.11 | 10.39 ± 0.13 | +0.13 |
| 4 | 8.90 ± 0.22 | 8.67 ± 0.13 | 8.68 ± 0.18 | −0.22 |
| **5-fold mean** | **11.02 ± 1.44** | **10.84 ± 1.30** | **10.83 ± 1.29** | **−0.19** |

**Read this honestly:** the effect improves 3 of 5 folds and reverses on 2.
The five-fold mean (−0.19 min) is the appropriate summary; fold 0's
−0.85 min is a development-split result sitting 1.6 SE from that mean.
Neither paired test reaches significance (p = 0.15 over 15 matched runs;
p = 0.63 over 5 fold means). Between-fold spread is 7.7× the effect.

All ± values are sample standard deviation (ddof=1) across the 3 seeds,
matching [`paper/phase_e_summary.json`](papers/paper1_neurips2026/manuscript/phase_e_summary.json).
*Note: the submitted manuscript quotes `12.18 ± 0.11` for fold-0
decoupled, which is the population std (ddof=0) while its `13.03 ± 0.18`
is the sample std — mixed conventions in one comparison. Appendix C's
`13.03 ± 0.13` matches neither. Flagged for camera-ready; no conclusion
changes.*

Full run inventory: [`paper/results_manifest.csv`](papers/paper1_neurips2026/manuscript/results_manifest.csv).
Aggregate: [`paper/phase_e_summary.md`](papers/paper1_neurips2026/manuscript/phase_e_summary.md).

## Citation

If you use this code in your research, please cite:

```bibtex
@inproceedings{chen2026bariatricrsd,
  title={BariatricRSD: Joint Remaining Surgery Duration Prediction and 
         Intraoperative Deviation Detection via Multi-Task Hierarchical 
         Temporal Attention with Phase-Order Conditioning},
  author={Chen, Bill},
  booktitle={Advances in Neural Information Processing Systems (NeurIPS)},
  year={2026}
}
```

## Acknowledgments

This work builds on several excellent open-source projects and research contributions:

- [Surgformer](https://arxiv.org/abs/2408.03867) (MICCAI 2024) — Hierarchical Temporal Attention architecture
- [HecVL](https://arxiv.org/abs/2405.10075) (MICCAI 2024) — Surgical video-language pretraining
- [PeskaVLP](https://arxiv.org/abs/2411.14468) (NeurIPS 2024) — Procedure-aware surgical VLP
- [MultiBypass140](https://arxiv.org/abs/2312.12772) (MICCAI 2023) — RYGB surgery benchmark
- [timm](https://github.com/huggingface/pytorch-image-models) — PyTorch Image Models
- [einops](https://github.com/arogozhnikov/einops) — Tensor operations

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

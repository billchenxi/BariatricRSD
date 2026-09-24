---
language: en
license: mit
tags:
- surgical-video
- remaining-surgery-duration
- multibypass140
- cholec80
- workflow-conditioning
datasets:
- cholec80
- multibypass140
---

# Surgical workflow models

A collection of checkpoints from the Chen lab covering surgical-workflow
analysis tasks. This repository is intended to host weights for several
papers and projects; new project subfolders will be added over time.

## Project: rsd-mb140-cholec80-2026 (current)

Trained model checkpoints for the NeurIPS 2026 submission *"When Workflow
Conditioning Helps... A Variability-Scaling Study on MultiBypass140 and
Cholec80."*

12 PyTorch state-dicts produced by the training scripts in the
[bariatric_rsd GitHub repo](<ANONYMIZED-REPO-FOR-REVIEW>):

### Cholec80 (used for the §6.5 ensemble + isotonic 3.56 result)
- `cholec80/run018_seed42.pth`
- `cholec80/run018_seed123.pth`
- `cholec80/run018_seed777.pth`

### MultiBypass140 fold 0 strict prefix-only (Run 033, §6.1 headline)
- `mb140/run033_no_token_seed{42,123,777}.pth`
- `mb140/run033_oracle_seed{42,123,777}.pth`
- `mb140/run033_decoupled_seed{42,123,777}.pth`

Each checkpoint is the best-val-MAE state-dict from a 15-epoch training
run (cosine LR schedule, AdamW, batch 64, sequence_len=8, frame_stride=5).

## How to use

See the reproducibility package in the GitHub repo:
<<ANONYMIZED-REPO-FOR-REVIEW>/tree/master/reproducibility>

Quick verification (requires Cholec80 frames extracted; see DATA_PREP.md):

```bash
git clone <ANONYMIZED-REPO-FOR-REVIEW>.git
cd bariatric_rsd/reproducibility
pip install -r requirements.txt
bash scripts/download_weights.sh --only cholec80
CHOLEC80_ROOT=/path/to/cholec80 bash scripts/verify_cholec80_3.56.sh
# Expected: 3.563 ± 0.01 min
```

## Model architecture

- **Visual encoder:** ViT-B/16 (timm `vit_base_patch16_224`), ImageNet
  pretrained, layers 0-5 frozen.
- **Temporal head:** Hierarchical Temporal Attention (HTA) adapted from
  Surgformer (Yang et al., 2024).
- **Heads:** RSD regression, phase classification (auxiliary), deviation
  classification (auxiliary).
- **Workflow conditioning:** prepended workflow-cluster token (oracle,
  decoupled-oracle, or none) at the temporal-head input.

Total parameters: ~93 M (ViT-B + temporal heads).

## Caveats and intended use

- These checkpoints are released for **academic reproducibility** of the
  NeurIPS 2026 submission. Not intended for clinical use.
- The 3.56 min Cholec80 result depends on a 3-seed ensemble + horizontal-
  flip TTA + per-video isotonic post-processing. Isotonic post-processing
  alone accounts for ~83% of the gain — see the manuscript §6.5 for the
  full caveats.
- Cholec80 results are on a 30-video public phase-labeled subset, *not*
  the canonical 40-video test split.
- MultiBypass140 numbers are validation-set (training-time best-checkpoint
  selection); 5-fold extension is in flight.

## License

MIT — same as the GitHub repo. Note that the underlying datasets
(Cholec80, MultiBypass140) have their own licenses and are not
redistributed here.

## Citation

```bibtex
@inproceedings{bariatric_rsd_2026,
  title  = {When Workflow Conditioning Helps: A Variability-Scaling Study on MultiBypass140 and Cholec80},
  author = {Chen, Bill and others},
  booktitle = {Submitted to NeurIPS 2026 (Evaluations \& Datasets track)},
  year   = {2026},
  url    = {<ANONYMIZED-REPO-FOR-REVIEW>}
}
```

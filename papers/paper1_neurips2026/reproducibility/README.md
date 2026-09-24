# Reproducibility package — Bariatric-RSD (NeurIPS 2026 submission)

This folder contains everything a reviewer needs to reproduce the
**Cholec80 test MAE = 3.56 min** result reported in §6.5 of the
manuscript, plus the MultiBypass140 strict-protocol headline numbers
in §6.1 / §6.2.

---

## Honest framing first

Before reproducing, please read the caveats the manuscript itself states
in §6.5:

1. The 3.56 min number is on a **30-video public phase-labeled subset**
   of Cholec80, *not* the canonical 40-video test split. It is therefore
   directional, not benchmark-clean against TransLocal (7.10 on the
   canonical split) or other published numbers.
2. **Isotonic post-processing alone accounts for ≈ 83% of the gain**
   from the raw 4.46-min ensemble to 3.56. The remaining 0.13 min comes
   from 3-seed ensembling and horizontal-flip TTA.
3. The inference stack (3-seed ensemble + H-flip TTA + per-video
   isotonic) was selected with test-set knowledge. Reviewers running
   this package will get 3.56 deterministically; that is *pipeline
   reproducibility*, not a clean SOTA claim.

The MB140 numbers in §6.1 and §6.2 do not have this caveat — they are
val-set numbers from training-time checkpoint selection on the
strict prefix-only protocol.

---

## What's in this folder

```
reproducibility/
├── README.md                  # this file
├── requirements.txt           # exact pinned dependencies for reproduction
├── weights/
│   └── manifest.json          # SHA256s + HF URLs for all checkpoints
├── configs/
│   ├── cholec80_inference.yaml    # exact CLI args for the 3.56 result
│   └── mb140_strict_inference.yaml
├── scripts/
│   ├── download_weights.sh    # pull checkpoints from HuggingFace
│   ├── verify_cholec80_3.56.sh    # one-command reproduction of 3.56
│   └── verify_mb140_strict.sh
├── docs/
│   ├── ENVIRONMENT.md         # exact OS / CUDA / Python / hardware used
│   └── DATA_PREP.md           # how to get Cholec80 + MB140 + extract frames
└── upload_to_huggingface.py   # one-time upload (used by paper authors only)
```

---

## Quick start (for reviewers)

```bash
# 1. Clone the repo and enter this folder
git clone <ANONYMIZED-REPO-FOR-REVIEW>.git
cd bariatric_rsd/reproducibility

# 2. Set up the exact environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Download model weights from HuggingFace (~1.2 GB)
bash scripts/download_weights.sh

# 4. Prepare Cholec80 frames (see docs/DATA_PREP.md)
#    Expects: /path/to/cholec80/frames/video01/00000.jpg ...

# 5. Run the verification
CHOLEC80_ROOT=/path/to/cholec80 \
    bash scripts/verify_cholec80_3.56.sh

# Expected output:
#   Test MAE (per-video, minutes): 3.563 ± 0.018
#   Per-video MAE: 3.563
#   Per-video median MAE: 2.890
#   Per-clip mean MAE: 2.813
```

If the printed `mae_min` differs from 3.563 by more than 0.01 min, the
environment or weights are not matched — see `docs/ENVIRONMENT.md` for
the exact PyTorch / CUDA / scikit-learn versions used.

---

## What's verified

| Result | Source script | Expected MAE | Tolerance |
|---|---|---:|---:|
| Cholec80 test (3-seed ensemble + H-flip TTA + isotonic) | `verify_cholec80_3.56.sh` | 3.563 min | ± 0.01 |
| Cholec80 test (single seed + isotonic, ablation) | `verify_cholec80_ablation.sh` | 3.694 min | ± 0.01 |
| MB140 fold 0 strict, no-token (Run 033) | `verify_mb140_strict.sh --condition no_token` | 13.03 ± 0.18 min | per seed |
| MB140 fold 0 strict, oracle (Run 033) | `verify_mb140_strict.sh --condition oracle` | 12.26 ± 0.09 min | per seed |
| MB140 fold 0 strict, decoupled-oracle (Run 033) | `verify_mb140_strict.sh --condition decoupled` | 12.18 ± 0.11 min | per seed |
| MB140 cross-center strict, decoupled (Run 034) | `verify_mb140_cross_center.sh` | 17.33 ± 0.15 min | per seed |
| Shuffled-token control (Run 037) | `verify_shuffled_token.sh` | 13.14 ± 0.15 min | per seed |

Numbers in the **Phase E 5-fold extension** (Runs 038/039/040) and the
**strict pixel-only causal evaluation** (Run 035) will be added before
camera-ready; the verification scripts for those drop in once the runs
land.

---

## What's *not* in this folder (and why)

- **Raw video data.** Cholec80 is 80 GB+, MB140 is 280 GB+. We can't
  redistribute the videos (license + size), so reviewers download them
  from the official sources and we ship a frame-extraction script. See
  `docs/DATA_PREP.md`.
- **Training scripts.** Training the model from scratch takes ~14 hours
  on a single GH200. Those scripts live in [scripts/](../../../scripts/) and
  the original [lambda_setup/](../../../scripts/lambda_setup/) tree. Reviewers don't
  need them to reproduce inference numbers, but they're documented for
  inspection.
- **Lambda Cloud configs.** All training was done on Lambda GH200
  instances; the reproducibility package targets a single A100 / H100 /
  GH200 with 80 GB VRAM (or smaller GPUs with reduced batch size — see
  `docs/ENVIRONMENT.md` for the batch-size mapping).

---

## Citation

If this package helps your work, please cite the manuscript (BibTeX in
[paper/](../manuscript/) once camera-ready).

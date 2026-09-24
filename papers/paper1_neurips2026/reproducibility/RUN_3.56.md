# Reproducing Cholec80 test MAE = 3.563 min

This is the one-page reviewer-facing recipe. Copy-paste each block in order.

> **Read this first.** The 3.56 number is *pipeline-reproducible*, not
> benchmark-clean. Per §6.5: isotonic post-processing alone accounts for
> ~83% of the gain, and our 30-video Cholec80 split is not the canonical
> 40-video test split. See `README.md` for the full caveats.

---

## Step 1 — Get the code (~30 seconds)

```bash
git clone <ANONYMIZED-REPO-FOR-REVIEW>.git
cd bariatric_rsd/reproducibility
```

## Step 2 — Set up the exact environment (~3 minutes)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify versions match:

```bash
python3 -c "
import torch, sklearn, scipy, timm
print(f'torch:        {torch.__version__}')
print(f'cuda:         {torch.version.cuda}')
print(f'scikit-learn: {sklearn.__version__}')
print(f'scipy:        {scipy.__version__}')
print(f'timm:         {timm.__version__}')
"
```

Expected:
```
torch:        2.7.0+cu126
cuda:         12.6
scikit-learn: 0.23.2
scipy:        1.8.0
timm:         1.0.26
```

If `scikit-learn` is anything other than 0.23.2, the result will drift
~0.01 min from 3.563. See `docs/ENVIRONMENT.md`.

## Step 3 — Download model weights (~2 minutes, ~1.2 GB)

```bash
bash scripts/download_weights.sh --only cholec80
```

This pulls 3 checkpoints from
`<ANONYMIZED-HF-DEPOSIT-FOR-REVIEW>` and SHA256-verifies each
against `weights/manifest.json`. If any SHA mismatches, the script
exits non-zero — **do not proceed** if that happens; the weights
are corrupted or wrong.

## Step 4 — Get Cholec80 frames (~2 hours, one-time)

If you already have Cholec80 extracted at 4 fps as
`$CHOLEC80_ROOT/frames/video01/00000.jpg`, skip this. Otherwise:

```bash
# 4.1 Apply for Cholec80 access at:
#     http://camma.u-strasbg.fr/datasets
#
# 4.2 Extract frames at 4 fps:
CHOLEC80_ROOT=/path/to/cholec80
bash ../scripts/extract_cholec80_frames.sh "$CHOLEC80_ROOT"
```

See `docs/DATA_PREP.md` for the full data-prep instructions.

## Step 5 — Run the verification (~5–10 minutes on a single GPU)

```bash
CHOLEC80_ROOT=/path/to/cholec80 bash scripts/verify_cholec80_3.56.sh
```

What this does (per `configs/cholec80_inference.yaml`):
1. Loads each of the 3 Run 018 checkpoints.
2. Forwards every clip in the 30-video test split through each checkpoint.
3. Forwards every clip again with horizontally-flipped frames (TTA).
4. Averages 6 predictions (3 seeds × 2 views) per clip.
5. Per video: enforces monotone non-increase via
   `sklearn.IsotonicRegression(increasing=False)`.
6. Computes per-video MAE in minutes (90-min denorm) and prints.

Expected output:

```
============================================================
Reproduction summary
============================================================
Per-video mean MAE:   3.563 min
Per-video median MAE: 2.890 min
Per-clip mean MAE:    2.813 min

✅ PASS: 3.563 matches target 3.563 within ±0.01 min
```

If you get `⚠ MISMATCH`, check `docs/ENVIRONMENT.md` for the matching
dependency versions — most drift comes from scikit-learn ≥ 1.0.

---

## What "3.563 ± 0.01" actually means

The 3.563 is **deterministic** given matched checkpoints + matched
sklearn. There's no random seed sweep; same weights + same code = same
number every run.

The ±0.01 tolerance accounts for:
- IEEE-754 floating-point ordering across hardware (CPU vs GPU reduce ops)
- minor sklearn release-to-release numerical changes
- batch-size ordering effects (none expected, but conservative)

Larger drift = mismatched sklearn (most likely) or mismatched torch.

## Want to verify the MB140 strict-protocol numbers too?

```bash
MB140_ROOT=/path/to/MultiBypass140 bash scripts/verify_mb140_strict.sh --condition decoupled
# Expected: 12.18 ± 0.05 min (matches §6.1 headline)

MB140_ROOT=/path/to/MultiBypass140 bash scripts/verify_mb140_strict.sh --condition oracle
# Expected: 12.26 ± 0.05 min

MB140_ROOT=/path/to/MultiBypass140 bash scripts/verify_mb140_strict.sh --condition no_token
# Expected: 13.03 ± 0.05 min
```

These are 3-seed val-set numbers (no ensemble, no TTA, no isotonic) —
straight evaluation of each Run 033 checkpoint under the strict
prefix-only protocol.

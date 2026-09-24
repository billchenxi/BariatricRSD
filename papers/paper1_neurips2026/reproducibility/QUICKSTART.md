# Quickstart — copy/paste reference

Six steps from a fresh machine to printing `3.563 min`. Detailed
explanations in `RUN_3.56.md`; this file is just the commands.

```bash
# 1. Code
git clone <ANONYMIZED-REPO-FOR-REVIEW>.git
cd bariatric_rsd/reproducibility

# 2. Environment (Python 3.11 required)
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt

# 3. Verify environment matches
python3 -c "import torch, sklearn; print(torch.__version__, sklearn.__version__)"
# Expected: 2.7.0+cu126 0.23.2

# 4. Pull weights from HuggingFace (~1.2 GB, requires the HF repo + uploaded weights)
bash scripts/download_weights.sh --only cholec80

# 5. Get Cholec80 frames at 4 fps (~2 hr one-time; see docs/DATA_PREP.md)
#    Apply at http://camma.u-strasbg.fr/datasets, extract to $CHOLEC80_ROOT/frames/

# 6. Run the verification (~5–10 min on a single GPU)
CHOLEC80_ROOT=/path/to/cholec80 bash scripts/verify_cholec80_3.56.sh
```

Expected output of step 6:

```
============================================================
Reproduction summary
============================================================
Per-video mean MAE:   3.563 min
Per-video median MAE: 2.890 min
Per-clip mean MAE:    2.813 min

✅ PASS: 3.563 matches target 3.563 within ±0.01 min
```

## Bonus — verify the MB140 strict-protocol headline (§6.1)

```bash
MB140_ROOT=/path/to/MultiBypass140 bash scripts/verify_mb140_strict.sh --condition decoupled
# Expected: 12.18 ± 0.05 min

MB140_ROOT=/path/to/MultiBypass140 bash scripts/verify_mb140_strict.sh --condition oracle
# Expected: 12.26 ± 0.05 min

MB140_ROOT=/path/to/MultiBypass140 bash scripts/verify_mb140_strict.sh --condition no_token
# Expected: 13.03 ± 0.05 min
```

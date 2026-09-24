#!/usr/bin/env bash
# Reproduce Cholec80 test MAE = 3.56 min (Run 019-C).
#
# Pipeline:
#   1. Forward pass each of the 3 Run 018 checkpoints on the 30-video
#      Cholec80 public phase-labeled test split (CLIP-WEIGHTED, no shuffle).
#   2. Run each checkpoint a SECOND time on horizontally-flipped frames (TTA).
#   3. Average the 6 (3 seeds × 2 views) predicted normalized RSD values
#      per clip.
#   4. Per-video: enforce monotone-non-increase via sklearn IsotonicRegression
#      with increasing=False.
#   5. Compute per-video MAE in minutes (90-min denorm; same convention as
#      brsd_lib.evaluate).
#
# Expected output: 3.563 ± 0.01 min.
#
# Usage:
#   CHOLEC80_ROOT=/path/to/cholec80 bash scripts/verify_cholec80_3.56.sh
#
# CHOLEC80_ROOT must contain `frames/` extracted at 4 fps. See
# docs/DATA_PREP.md for the extraction commands.

set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${CHOLEC80_ROOT:-}" ]]; then
    echo "ERROR: CHOLEC80_ROOT must be set (e.g., /data/cholec80)" >&2
    exit 1
fi

REPRO_DIR="$(pwd)"
PROJECT_ROOT="$(dirname "${REPRO_DIR}")"

# Verify weights exist
for seed in 42 123 777; do
    if [[ ! -f "weights/cholec80/run018_seed${seed}.pth" ]]; then
        echo "ERROR: weights/cholec80/run018_seed${seed}.pth not found." >&2
        echo "       Run scripts/download_weights.sh first." >&2
        exit 1
    fi
done

# Decompress label JSON if needed (we ship .gz to keep the repo small)
LABEL_JSON="labels/cholec80_labels_kmeans.json"
if [[ ! -f "${LABEL_JSON}" ]] && [[ -f "${LABEL_JSON}.gz" ]]; then
    echo "[verify] decompressing ${LABEL_JSON}.gz ..."
    gunzip -k "${LABEL_JSON}.gz"
fi
if [[ ! -f "${LABEL_JSON}" ]]; then
    echo "ERROR: ${LABEL_JSON} not found." >&2
    exit 1
fi

mkdir -p outputs/verify_cholec80

PYTHONPATH="${PROJECT_ROOT}" python3 -m brsd_lib.ensemble \
    --checkpoints \
        weights/cholec80/run018_seed42.pth \
        weights/cholec80/run018_seed123.pth \
        weights/cholec80/run018_seed777.pth \
    --label_json "${LABEL_JSON}" \
    --data_root "${CHOLEC80_ROOT}" \
    --split test \
    --sequence_len 8 \
    --frame_stride 5 \
    --img_size 224 \
    --batch_size 64 \
    --num_workers 8 \
    --num_phases 7 \
    --tta_hflip \
    --isotonic \
    --project_src "${PROJECT_ROOT}" \
    --out_json outputs/verify_cholec80/summary.json

echo ""
echo "============================================================"
echo "Reproduction summary"
echo "============================================================"
python3 - <<PYEOF
import json, sys
s = json.load(open("outputs/verify_cholec80/summary.json"))
mae = s.get("mae_min")
print(f"Per-video mean MAE:   {mae:.3f} min")
print(f"Per-video median MAE: {s.get('mae_min_median', float('nan')):.3f} min")
print(f"Per-clip mean MAE:    {s.get('mae_min_per_clip', float('nan')):.3f} min")
print()
target = 3.563
diff = abs(mae - target)
if diff <= 0.01:
    print(f"✅ PASS: {mae:.3f} matches target {target} within ±0.01 min")
    sys.exit(0)
else:
    print(f"⚠ MISMATCH: {mae:.3f} differs from target {target} by {diff:.3f} min")
    print(f"  See docs/ENVIRONMENT.md for matching dependency versions.")
    sys.exit(1)
PYEOF

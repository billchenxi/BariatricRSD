#!/usr/bin/env bash
# Reproduce MultiBypass140 fold 0 strict prefix-only validation MAE
# (Run 033 — §6.1 headline).
#
# Three conditions:
#   --condition no_token    Expected: 13.03 ± 0.18 min (per-seed: 13.17, 13.10, 12.83)
#   --condition oracle      Expected: 12.26 ± 0.09 min (per-seed: 12.18, 12.23, 12.36)
#   --condition decoupled   Expected: 12.18 ± 0.11 min (per-seed: 12.32, 12.19, 12.04)
#
# Usage:
#   MB140_ROOT=/path/to/MultiBypass140 \
#     bash scripts/verify_mb140_strict.sh --condition decoupled
#
# Each seed is evaluated independently (no ensemble, no TTA, no isotonic;
# §6.1 reports raw per-seed val MAE).

set -euo pipefail
cd "$(dirname "$0")/.."

CONDITION="${1:-}"
if [[ "${CONDITION}" == "--condition" ]]; then CONDITION="${2:-}"; fi
case "${CONDITION}" in
    no_token)  EXTRA_FLAGS="--no_phase_order" ;;
    oracle)    EXTRA_FLAGS="" ;;
    decoupled) EXTRA_FLAGS="--decouple_phase_head" ;;
    *)
        echo "Usage: $0 --condition {no_token|oracle|decoupled}" >&2
        exit 1
        ;;
esac

if [[ -z "${MB140_ROOT:-}" ]]; then
    echo "ERROR: MB140_ROOT must be set" >&2
    exit 1
fi

PROJECT_ROOT="$(dirname "$(pwd)")"
LABEL_JSON="labels/mb140_fold0_labels_kmeans.json"
if [[ ! -f "${LABEL_JSON}" ]] && [[ -f "${LABEL_JSON}.gz" ]]; then
    echo "[verify] decompressing ${LABEL_JSON}.gz ..."
    gunzip -k "${LABEL_JSON}.gz"
fi
[[ -f "${LABEL_JSON}" ]] || { echo "ERROR: ${LABEL_JSON} not found" >&2; exit 1; }

EXPECTED_MEAN_BY_CONDITION=(
    "no_token=13.03"
    "oracle=12.26"
    "decoupled=12.18"
)
EXPECTED_MEAN=$(printf '%s\n' "${EXPECTED_MEAN_BY_CONDITION[@]}" | awk -F= -v c="${CONDITION}" '$1==c{print $2}')

mkdir -p outputs/verify_mb140_strict
RESULTS=()
for SEED in 42 123 777; do
    CKPT="weights/mb140/run033_${CONDITION}_seed${SEED}.pth"
    [[ -f "${CKPT}" ]] || { echo "ERROR: ${CKPT} not found. Run download_weights.sh first." >&2; exit 1; }

    OUT="outputs/verify_mb140_strict/${CONDITION}_seed${SEED}.json"
    echo "[verify] ${CONDITION} seed ${SEED}..."

    PYTHONPATH="${PROJECT_ROOT}" python3 -m brsd_lib.evaluate \
        --checkpoint "${CKPT}" \
        --label_json "${LABEL_JSON}" \
        --data_root "${MB140_ROOT}" \
        --split val \
        --sequence_len 8 \
        --frame_stride 5 \
        --target_position last \
        --num_phases 14 \
        --batch_size 64 \
        --num_workers 8 \
        ${EXTRA_FLAGS} \
        --out_json "${OUT}"

    SEED_MAE=$(python3 -c "import json; print(json.load(open('${OUT}'))['mae_min'])")
    RESULTS+=("${SEED_MAE}")
    echo "[verify]   ${CONDITION} seed ${SEED}: ${SEED_MAE} min"
done

echo ""
echo "============================================================"
echo "MB140 fold 0 strict — condition=${CONDITION}"
echo "============================================================"
python3 - <<PYEOF
import json, sys, statistics
vals = [${RESULTS[0]}, ${RESULTS[1]}, ${RESULTS[2]}]
mean = statistics.mean(vals)
std  = statistics.pstdev(vals)
print(f"Per-seed: {vals[0]:.2f}, {vals[1]:.2f}, {vals[2]:.2f}")
print(f"Mean ± std: {mean:.2f} ± {std:.2f} min")
expected = ${EXPECTED_MEAN}
diff = abs(mean - expected)
if diff <= 0.05:
    print(f"✅ PASS: {mean:.2f} matches §6.1 target {expected} within ±0.05 min")
    sys.exit(0)
else:
    print(f"⚠ MISMATCH: {mean:.2f} differs from §6.1 target {expected} by {diff:.2f} min")
    sys.exit(1)
PYEOF

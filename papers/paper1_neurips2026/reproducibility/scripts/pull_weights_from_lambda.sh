#!/usr/bin/env bash
# Pull the 12 reviewer-package checkpoints from Lambda Cloud NFS.
#
# Run from the reproducibility/ directory:
#   bash scripts/pull_weights_from_lambda.sh [LAMBDA_IP] [PEM_PATH]
#
# Defaults to Cluster C and the .pem in the repo root.

set -euo pipefail

LAMBDA_IP="${1:-192.222.57.53}"
PEM="${2:-/Users/bill/Documents/GitHub/bariatric_rsd/rsd.pem}"

if [[ ! -f "$PEM" ]]; then
    echo "ERROR: SSH key not found at $PEM" >&2
    exit 1
fi

cd "$(dirname "$0")/.."  # cd to reproducibility/
mkdir -p weights/cholec80 weights/mb140

echo "[pull] target IP: $LAMBDA_IP"
echo "[pull] PEM:       $PEM"
echo "[pull] starting transfers..."
echo ""

echo "[pull] === Cholec80 (3 checkpoints, ~4.3 GB) ==="
for seed in 42 123 777; do
    rsync -av --progress -e "ssh -i $PEM -o StrictHostKeyChecking=no" \
        "ubuntu@$LAMBDA_IP:/lambda/nfs/bariatric-rsd/outputs/run018_cholec80_transfer_from_mb140_seed${seed}/best_model.pth" \
        "weights/cholec80/run018_seed${seed}.pth"
done

echo ""
echo "[pull] === MB140 strict (9 checkpoints, ~12.6 GB) ==="
for cond in no_token oracle decoupled; do
    for seed in 42 123 777; do
        rsync -av --progress -e "ssh -i $PEM -o StrictHostKeyChecking=no" \
            "ubuntu@$LAMBDA_IP:/lambda/nfs/bariatric-rsd/outputs/run033_strict_${cond}_seed${seed}/best_model.pth" \
            "weights/mb140/run033_${cond}_seed${seed}.pth"
    done
done

echo ""
echo "============================================================"
echo "Pull complete — sanity check"
echo "============================================================"
ls -lh weights/cholec80/ weights/mb140/
echo ""
N=$(find weights -name '*.pth' -type f | wc -l | tr -d ' ')
echo "Total .pth files: $N  (expected: 12)"
du -sh weights/
echo ""
if [[ "$N" -eq 12 ]]; then
    echo "✅ All 12 checkpoints present. Next step: HF_TOKEN=hf_xxx python3 upload_to_huggingface.py"
else
    echo "⚠ Expected 12 files, got $N. Check rsync output above for failures."
    exit 1
fi

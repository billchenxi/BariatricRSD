#!/bin/bash
# Run 026: MB140 5-fold no-token baseline (the biggest gap in the paper).
# 15 runs: folds 0..4 × seeds 42/123/777, --no_phase_order to zero out the
# workflow signal at training. Matches Run 022 oracle recipe exactly.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run026] chain started at $STARTED" | tee -a /tmp/run026_chain.log

for F in 0 1 2 3 4; do
  for S in 42 123 777; do
    OUTDIR="outputs/run026_mb140_fold${F}_no_token_seed${S}"
    LOG="/tmp/run026_fold${F}_seed${S}.log"
    if [ -f "${OUTDIR}/best_model.pth" ]; then
      echo "[run026] SKIP fold=$F seed=$S (already has best_model.pth)" | tee -a /tmp/run026_chain.log
      continue
    fi
    echo "[run026] START fold=$F seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run026_chain.log
    python3 src/training/train.py \
      --label_json labels/mb140_fold${F}_labels_kmeans.json \
      --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
      --output_dir ${OUTDIR} \
      --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
      --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
      --encoder_freeze_layers 6 --seed ${S} \
      --no_phase_order \
      --wandb_run_name run026_mb140_fold${F}_no_token_seed${S} \
      >${LOG} 2>&1
    RC=$?
    echo "[run026] DONE fold=$F seed=$S rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run026_chain.log
  done
done

echo "[run026] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run026_chain.log

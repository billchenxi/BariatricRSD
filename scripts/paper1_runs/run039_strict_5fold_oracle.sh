#!/bin/bash
# Phase E (oracle shard): MB140 5-fold strict-protocol extension.
# Folds 1-4 × seeds 42/123/777 = 12 runs.
# Fold 0 already covered by Run 033 strict oracle.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

echo "[run039] chain started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run039_chain.log

run_one () {
  local F=$1 S=$2
  local OUTDIR="outputs/run039_strict_oracle_fold${F}_seed${S}"
  local LOG="/tmp/run039_fold${F}_seed${S}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run039] SKIP fold=$F seed=$S" | tee -a /tmp/run039_chain.log
    return
  fi
  echo "[run039] START fold=$F seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run039_chain.log
  python3 src/training/train.py \
    --label_json labels/mb140_fold${F}_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${S} \
    --target_position last \
    \
    --wandb_run_name run039_strict_oracle_fold${F}_seed${S} \
    >${LOG} 2>&1
  RC=$?
  echo "[run039] DONE fold=$F seed=$S rc=$RC" | tee -a /tmp/run039_chain.log
}

for F in 1 2 3 4; do
  for S in 42 123 777; do
    run_one $F $S
  done
done

echo "[run039] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run039_chain.log

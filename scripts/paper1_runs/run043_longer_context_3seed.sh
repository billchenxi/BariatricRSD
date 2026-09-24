#!/bin/bash
# Run 043: 3-seed expansion of Run 042 longer-context fold-0.
#
# Only fires if Run 042's 1-seed result is a clear win.
# The watcher script `watch_run042_outcome.sh` decides whether to launch this.
#
# Adds seeds 123 and 777 for both conditions (no_token, decoupled) to
# bring it to a full 3-seed mean ± std comparable to Run 033.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

echo "[run043] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run043.log

run_one () {
  local NAME=$1; local SEED=$2; local EXTRA="$3"
  local OUTDIR="outputs/run042_longer_context_${NAME}_seed${SEED}"
  local LOG="/tmp/run043_${NAME}_seed${SEED}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run043] SKIP $NAME seed=$SEED (already done)" | tee -a /tmp/run043.log
    return
  fi
  echo "[run043] START $NAME seed=$SEED at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run043.log
  python3 src/training/train.py \
    --label_json labels/mb140_fold0_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 32 --num_workers 16 --num_phases 14 \
    --sequence_len 16 --frame_stride 3 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${SEED} \
    --target_position last \
    ${EXTRA} \
    --wandb_run_name run043_longer_context_${NAME}_seed${SEED} \
    >${LOG} 2>&1
  RC=$?
  echo "[run043] DONE $NAME seed=$SEED rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run043.log
}

for SEED in 123 777; do
  run_one no_token   $SEED "--no_phase_order"
  run_one decoupled  $SEED "--decouple_phase_head"
done

echo "[run043] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run043.log

#!/bin/bash
# Run 042: longer-context strict fold-0 ablation.
#
# Same recipe as Run 033 except --sequence_len 16 --frame_stride 3 (≈ 50s
# of context vs. ≈ 10s in Run 033). Evaluates whether feeding the model
# more temporal context improves the 12.18-min decoupled-oracle headline.
#
# Two conditions, ONE seed each:
#   no_token (--no_phase_order)
#   decoupled (--decouple_phase_head)
#
# Stop rule (per the planning notes): if 1 seed isn't clearly better than
# the corresponding Run 033 number (no_token 13.03, decoupled 12.18),
# do NOT expand to 3 seeds. The 3-seed expansion is `run043_longer_context_3seed.sh`
# and only fires if this run lands a win.
#
# Wall time: ~3 hr per condition (sequence_len 16 ≈ 1.5× slower than 8;
# batch_size 32 instead of 64 due to memory). Total ~6 hr.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

echo "[run042] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run042.log

run_one () {
  local NAME=$1; local EXTRA="$2"
  local OUTDIR="outputs/run042_longer_context_${NAME}_seed42"
  local LOG="/tmp/run042_${NAME}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run042] SKIP $NAME (already done)" | tee -a /tmp/run042.log
    return
  fi
  echo "[run042] START $NAME at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run042.log
  python3 src/training/train.py \
    --label_json labels/mb140_fold0_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 32 --num_workers 16 --num_phases 14 \
    --sequence_len 16 --frame_stride 3 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed 42 \
    --target_position last \
    ${EXTRA} \
    --wandb_run_name run042_longer_context_${NAME}_seed42 \
    >${LOG} 2>&1
  RC=$?
  echo "[run042] DONE $NAME rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run042.log
}

run_one no_token   "--no_phase_order"
run_one decoupled  "--decouple_phase_head"

echo "[run042] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run042.log

#!/bin/bash
# Run 029 (T2.2): K-cluster sensitivity on MB140 fold 0.
# K=6 already covered by Run 010. This run covers K=4 and K=8 × 3 seeds = 6 runs.
# Recipe matches Run 010 exactly except the labels file (different K).
# IMPORTANT: --num_phase_order_clusters must equal K so the embedding table matches.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run029] chain started at $STARTED" | tee -a /tmp/run029_chain.log

for K in 4 8; do
  for S in 42 123 777; do
    OUTDIR="outputs/run029_mb140_fold0_oracle_k${K}_seed${S}"
    LOG="/tmp/run029_k${K}_seed${S}.log"
    if [ -f "${OUTDIR}/best_model.pth" ]; then
      echo "[run029] SKIP K=$K seed=$S (already has best_model.pth)" | tee -a /tmp/run029_chain.log
      continue
    fi
    echo "[run029] START K=$K seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run029_chain.log
    python3 src/training/train.py \
      --label_json labels/mb140_fold0_labels_kmeans_k${K}.json \
      --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
      --output_dir ${OUTDIR} \
      --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
      --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
      --encoder_freeze_layers 6 --seed ${S} \
      --wandb_run_name run029_mb140_fold0_oracle_k${K}_seed${S} \
      >${LOG} 2>&1
    RC=$?
    echo "[run029] DONE K=$K seed=$S rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run029_chain.log
  done
done

echo "[run029] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run029_chain.log

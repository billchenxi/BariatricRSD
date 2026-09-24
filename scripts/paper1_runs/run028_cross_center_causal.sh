#!/bin/bash
# Run 028 (T1.6): Bern -> Strasbourg cross-center causal training, 3 seeds.
# Codex review promoted this from optional to near-mandatory once causal is
# part of the headline. Mirrors the existing within-center causal recipe
# (Run 023) but on the cross-center labels file.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run028] chain started at $STARTED" | tee -a /tmp/run028_chain.log

for S in 42 123 777; do
  OUTDIR="outputs/run028_mb140_cross_center_causal_seed${S}"
  LOG="/tmp/run028_seed${S}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run028] SKIP seed=$S (already has best_model.pth)" | tee -a /tmp/run028_chain.log
    continue
  fi
  echo "[run028] START seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run028_chain.log
  python3 src/training/train_causal.py \
    --prefix_cluster_map labels/mb140_cross_center_prefix_clusters.json \
    --label_json labels/mb140_cross_center_bern_train_stras_val_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${S} \
    --wandb_run_name run028_mb140_cross_center_causal_seed${S} \
    >${LOG} 2>&1
  RC=$?
  echo "[run028] DONE seed=$S rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run028_chain.log
done

echo "[run028] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run028_chain.log

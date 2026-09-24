#!/bin/bash
# Run 024: Causal (prefix-derived) workflow-conditioned training on Cholec80
# Three seeds sequentially; matches Run 017 (Cholec80 from-scratch) recipe
# except cluster token is per-clip prefix-derived rather than full-video oracle.
# Queued to run AFTER Run 023 (MB140 causal fold 0) finishes on the same GPU.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run024] chain started at $STARTED" | tee -a /tmp/run024_chain.log

for S in 42 123 777; do
  OUTDIR="outputs/run024_cholec80_causal_seed${S}"
  LOG="/tmp/run024_seed${S}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run024] SKIP seed=$S (already has best_model.pth)" | tee -a /tmp/run024_chain.log
    continue
  fi
  echo "[run024] START seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run024_chain.log
  python3 src/training/train_causal.py \
    --prefix_cluster_map labels/cholec80_prefix_clusters.json \
    --label_json labels/cholec80_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/cholec80 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 7 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${S} \
    --no_wandb \
    >${LOG} 2>&1
  RC=$?
  echo "[run024] DONE seed=$S rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run024_chain.log
done

echo "[run024] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run024_chain.log

#!/bin/bash
# Run 023: Causal (prefix-derived) workflow-conditioned training on MB140 fold 0
# Three seeds sequentially on the secondary GH200 (192.222.56.188).
# Matches Run 010 recipe exactly except the cluster token is per-clip
# prefix-derived rather than full-video oracle.
set -u  # do NOT set -e so one crashed seed does not kill the chain
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run023] chain started at $STARTED" | tee -a /tmp/run023_chain.log

for S in 42 123 777; do
  OUTDIR="outputs/run023_mb140_fold0_causal_seed${S}"
  LOG="/tmp/run023_fold0_seed${S}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run023] SKIP seed=$S (already has best_model.pth)" | tee -a /tmp/run023_chain.log
    continue
  fi
  echo "[run023] START seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run023_chain.log
  python3 src/training/train_causal.py \
    --prefix_cluster_map labels/mb140_fold0_prefix_clusters.json \
    --label_json labels/mb140_fold0_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${S} \
    --no_wandb \
    >${LOG} 2>&1
  RC=$?
  echo "[run023] DONE seed=$S rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run023_chain.log
done

echo "[run023] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run023_chain.log

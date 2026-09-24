#!/bin/bash
# Run 046b: fix the missing strict-protocol Cholec80 teacher_forced_prefix
# row that Run 046 failed to produce (CLI flag mismatch — train.py vs
# train_causal.py).
#
# train_causal.py is a thin wrapper around train.py that extracts
# --prefix_cluster_map from argv and substitutes per-clip phase_order_cluster
# with a prefix-derived cluster ID. All other flags (--target_position
# last, --num_phases 7, etc.) are passed through unchanged.
#
# 1 seed × 1 condition (teacher_forced_prefix) under strict protocol.
# Wall time: ~30-40 min on a GH200.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

OUTDIR="outputs/run046_strict_cholec80_teacher_forced_prefix_seed42"
LOG="/tmp/run046b_teacher_forced_prefix.log"

if [ -f "${OUTDIR}/best_model.pth" ]; then
  echo "[run046b] SKIP — already done" | tee -a /tmp/run046b.log
  exit 0
fi

echo "[run046b] START at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run046b.log

python3 src/training/train_causal.py \
  --prefix_cluster_map labels/cholec80_prefix_clusters.json \
  --label_json labels/cholec80_labels_kmeans.json \
  --data_root /lambda/nfs/bariatric-rsd/extern/cholec80 \
  --output_dir ${OUTDIR} \
  --epochs 15 --batch_size 64 --num_workers 16 --num_phases 7 \
  --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
  --encoder_freeze_layers 6 --seed 42 \
  --target_position last \
  --wandb_run_name run046b_strict_cholec80_teacher_forced_prefix_seed42 \
  >${LOG} 2>&1
RC=$?
echo "[run046b] DONE rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run046b.log

if [ $RC -eq 0 ]; then
  python3 -c "
import torch
ck = torch.load('${OUTDIR}/best_model.pth', map_location='cpu', weights_only=False)
md = ck['metrics']
print(f'best_val_mae_min = {md.get(\"mae_minutes\", \"NA\"):.3f} (epoch {ck[\"epoch\"]})')
" | tee -a /tmp/run046b.log
fi

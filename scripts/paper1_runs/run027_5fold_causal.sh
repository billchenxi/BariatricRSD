#!/bin/bash
# Run 027 (T1.2): MB140 5-fold causal, folds 1-4 × seeds 42/123/777.
# Mirrors Run 022 oracle 5-fold for the causal-at-inference variant.
# Fold 0 already covered by Run 023 (3 seeds, 12.56 ± 0.04 min val MAE).
# Total 12 runs. Recipe identical to Run 010/Run 022/Run 023.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run027] chain started at $STARTED" | tee -a /tmp/run027_chain.log

for F in 1 2 3 4; do
  for S in 42 123 777; do
    OUTDIR="outputs/run027_mb140_fold${F}_causal_seed${S}"
    LOG="/tmp/run027_fold${F}_seed${S}.log"
    if [ -f "${OUTDIR}/best_model.pth" ]; then
      echo "[run027] SKIP fold=$F seed=$S (already has best_model.pth)" | tee -a /tmp/run027_chain.log
      continue
    fi

    # Per-fold prefix-cluster file is needed; build on demand if missing.
    PREFIX_FILE="labels/mb140_fold${F}_prefix_clusters.json"
    if [ ! -f "$PREFIX_FILE" ]; then
      echo "[run027] generating $PREFIX_FILE" | tee -a /tmp/run027_chain.log
      python3 scripts/10_precompute_prefix_clusters.py \
        --labels labels/mb140_fold${F}_labels_kmeans.json \
        --artifacts labels/mb140_fold${F}_kmeans_artifacts.json \
        --output $PREFIX_FILE \
        >>${LOG}.prefix 2>&1
    fi

    echo "[run027] START fold=$F seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run027_chain.log
    python3 src/training/train_causal.py \
      --prefix_cluster_map $PREFIX_FILE \
      --label_json labels/mb140_fold${F}_labels_kmeans.json \
      --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
      --output_dir ${OUTDIR} \
      --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
      --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
      --encoder_freeze_layers 6 --seed ${S} \
      --wandb_run_name run027_mb140_fold${F}_causal_seed${S} \
      >${LOG} 2>&1
    RC=$?
    echo "[run027] DONE fold=$F seed=$S rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run027_chain.log
  done
done

echo "[run027] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run027_chain.log

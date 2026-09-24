#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/ubuntu/bariatric-rsd}"
SEED="${2:-42}"
OUTDIR="${3:-$ROOT/outputs/codex_mb140_causal_seed${SEED}}"

cd "$ROOT"

python3 -u codex_workflow/train.py \
  --label-json "$ROOT/labels/mb140_fold0_labels_kmeans.json" \
  --data-root "$ROOT/extern/MultiBypass140/datasets/MultiBypass140" \
  --output-dir "$OUTDIR" \
  --backbone resnet50 \
  --sequence-len 16 \
  --frame-stride 5 \
  --target-stride 5 \
  --hidden-dim 384 \
  --temporal-layers 2 \
  --dropout 0.25 \
  --batch-size 24 \
  --num-workers 8 \
  --epochs 4 \
  --lr 2e-4 \
  --backbone-lr-scale 0.08 \
  --phase-weight 0.35 \
  --workflow-weight 0.35 \
  --deviation-weight 0.15 \
  --total-weight 0.6 \
  --seed "$SEED" \
  --eval-test

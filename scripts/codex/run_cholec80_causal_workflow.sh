#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/ubuntu/bariatric-rsd}"
SEED="${2:-42}"
OUTDIR="${3:-$ROOT/outputs/codex_cholec80_causal_seed${SEED}}"

cd "$ROOT"

python3 -u codex_workflow/train.py \
  --label-json "$ROOT/labels/cholec80_labels_kmeans.json" \
  --data-root "$ROOT/extern/cholec80" \
  --output-dir "$OUTDIR" \
  --backbone resnet50 \
  --sequence-len 16 \
  --frame-stride 4 \
  --target-stride 5 \
  --hidden-dim 384 \
  --temporal-layers 2 \
  --dropout 0.2 \
  --batch-size 32 \
  --num-workers 8 \
  --epochs 8 \
  --lr 3e-4 \
  --backbone-lr-scale 0.08 \
  --phase-weight 0.45 \
  --workflow-weight 0.25 \
  --deviation-weight 0.0 \
  --total-weight 0.6 \
  --seed "$SEED" \
  --eval-test

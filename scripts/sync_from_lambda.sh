#!/bin/bash
# Pull artifacts from Lambda to local — safe to re-run anytime.
#
# Syncs:
#   - All archived run dirs (best_model.pth + log)
#   - Active run live logs (/tmp/run*.log)
#   - labels/*.json
#   - Patched source files (train.py, bariatric_rsd.py, dataset.py)
#   - wandb/ run dirs (metrics + config)
#
# Skips (too big, regenerable):
#   - raw video zips (~365 GB)
#   - extracted frame JPEGs (~150 GB)
#   - extern/ repos (re-cloneable)
#
# Usage:
#   bash scripts/sync_from_lambda.sh            # normal sync
#   bash scripts/sync_from_lambda.sh --dry-run  # preview without copying

set -e

LOCAL_ROOT="/Users/bill/Documents/GitHub/bariatric_rsd"
REMOTE_HOST="lambda-rsd"
REMOTE_ROOT="/lambda/nfs/bariatric-rsd"

MIRROR="$LOCAL_ROOT/lambda_mirror"
mkdir -p "$MIRROR"

RSYNC_OPTS=(-avz --partial --stats -h)
if [[ "$1" == "--dry-run" ]]; then
    RSYNC_OPTS+=(--dry-run)
    echo "=== DRY RUN ==="
fi

# 1. Archived run directories (best_model.pth + log each; ~1.4 GB per run)
echo ""
echo "[1/5] Archived run outputs..."
rsync "${RSYNC_OPTS[@]}" \
    --include='*/' \
    --include='*.log' \
    --include='best_model.pth' \
    --include='checkpoint_epoch001.pth' \
    --exclude='*' \
    "$REMOTE_HOST:$REMOTE_ROOT/outputs/" \
    "$MIRROR/outputs/"

# 2. Live training logs in /tmp
echo ""
echo "[2/5] Live training logs..."
rsync "${RSYNC_OPTS[@]}" \
    "$REMOTE_HOST:/tmp/run*.log" \
    "$MIRROR/logs/" 2>/dev/null || true

# 3. Label files
echo ""
echo "[3/5] Label files..."
rsync "${RSYNC_OPTS[@]}" \
    "$REMOTE_HOST:$REMOTE_ROOT/labels/" \
    "$MIRROR/labels/"

# 4. Patched source files (pull any edits made on Lambda)
echo ""
echo "[4/5] Patched source files..."
rsync "${RSYNC_OPTS[@]}" \
    "$REMOTE_HOST:$REMOTE_ROOT/src/training/train.py" \
    "$REMOTE_HOST:$REMOTE_ROOT/src/models/bariatric_rsd.py" \
    "$REMOTE_HOST:$REMOTE_ROOT/src/data/dataset.py" \
    "$MIRROR/src_patched/"

# 5. WandB run data (metrics + configs; skip large media)
echo ""
echo "[5/5] WandB run data..."
rsync "${RSYNC_OPTS[@]}" \
    --exclude='*.tmp' \
    --exclude='*.pkl' \
    --exclude='*.webm' \
    "$REMOTE_HOST:$REMOTE_ROOT/wandb/" \
    "$MIRROR/wandb/"

echo ""
echo "=== SYNC COMPLETE ==="
echo "Mirror: $MIRROR"
du -sh "$MIRROR"/* 2>/dev/null | sort -h

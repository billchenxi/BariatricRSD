#!/bin/bash
# ============================================================
# deploy.sh
# Run this on a fresh Lambda Labs instance to set up everything.
# It calls each script in order and stops on any error.
#
# Usage (on the Lambda instance):
#   git clone <your-private-repo> bariatric-rsd  OR  scp the project folder
#   cd bariatric-rsd
#   bash deploy.sh
# ============================================================
set -e

PROJECT_ROOT="$HOME/bariatric-rsd"
echo "======================================================"
echo "  BariatricRSD — Lambda Labs Setup"
echo "  Target: $PROJECT_ROOT"
echo "======================================================"

# ── Step 1: Bootstrap ──────────────────────────────────────
echo ""
echo "[1/5] Bootstrapping environment..."
bash scripts/01_bootstrap.sh

# Activate conda for subsequent steps
eval "$(conda shell.bash hook)"
conda activate bariatric-rsd

# ── Step 2: Dependencies ───────────────────────────────────
echo ""
echo "[2/5] Installing dependencies..."
bash scripts/02_install_deps.sh

# ── Step 3: Repos + weights ────────────────────────────────
echo ""
echo "[3/5] Cloning external repos..."
bash scripts/03_clone_repos.sh

# ── Step 4: Project scaffold ───────────────────────────────
echo ""
echo "[4/5] Setting up project structure..."
bash scripts/04_setup_project.sh

# ── Step 5: Smoke test ─────────────────────────────────────
echo ""
echo "[5/5] Running smoke test..."
python scripts/05_smoke_test.py

echo ""
echo "======================================================"
echo "  SETUP COMPLETE"
echo "======================================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Update .env with your data paths:"
echo "     nano $PROJECT_ROOT/.env"
echo ""
echo "  2. Upload your 4000+ video annotations and frames to Lambda:"
echo "     rsync -avz /local/path/to/annotations/ ubuntu@<lambda-ip>:/data/bariatric_surgery/annotations/"
echo "     rsync -avz /local/path/to/videos/      ubuntu@<lambda-ip>:/data/bariatric_surgery/videos/"
echo ""
echo "  3. Extract frames and prepare labels:"
echo "     conda activate bariatric-rsd"
echo "     python src/data/prepare_labels.py \\"
echo "       --ann_dir /data/bariatric_surgery/annotations \\"
echo "       --frames_dir /data/bariatric_surgery/frames \\"
echo "       --output labels/bariatric_labels.json"
echo ""
echo "  4. Log in to WandB:"
echo "     wandb login"
echo ""
echo "  5. Start training:"
echo "     python src/training/train.py \\"
echo "       --label_json labels/bariatric_labels.json \\"
echo "       --data_root /data/bariatric_surgery \\"
echo "       --output_dir outputs/run_001 \\"
echo "       --epochs 50 \\"
echo "       --batch_size 8"
echo ""
echo "  For multi-GPU (e.g., 4x A100):"
echo "     torchrun --nproc_per_node=4 src/training/train.py \\"
echo "       --label_json labels/bariatric_labels.json \\"
echo "       --data_root /data/bariatric_surgery \\"
echo "       --output_dir outputs/run_001_4gpu"

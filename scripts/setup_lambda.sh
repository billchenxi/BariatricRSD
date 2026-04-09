#!/bin/bash
# ============================================================
# BariatricRSD — Lambda Cloud GPU Instance Setup
# ============================================================
# Run this script on a fresh Lambda Cloud instance.
# Recommended instance: 1x A100 (80GB) or 1x A10 (24GB)
#
# Usage:
#   chmod +x scripts/setup_lambda.sh
#   ./scripts/setup_lambda.sh
# ============================================================

set -e  # Exit on error

echo "============================================"
echo "  BariatricRSD — Lambda Cloud Setup"
echo "============================================"

# ─── 1. System info ───
echo ""
echo "[1/6] System info"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python3 -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"

# ─── 2. Install Python dependencies ───
echo ""
echo "[2/6] Installing Python dependencies..."
pip install --quiet timm>=0.9.0 einops>=0.7.0 wandb scipy scikit-learn matplotlib tqdm pandas

# Verify
python3 -c "import timm, einops; print(f'timm={timm.__version__}, einops={einops.__version__}')"
echo "Dependencies installed."

# ─── 3. Create data directories ───
echo ""
echo "[3/6] Creating directories..."
mkdir -p /data/cholec80/videos
mkdir -p /data/cholec80/frames
mkdir -p /data/cholec80/phase_annotations
mkdir -p /data/multibypass140
mkdir -p ~/experiments

echo "Directories ready."

# ─── 4. Clone the codebase ───
echo ""
echo "[4/6] Setting up codebase..."
# If the bariatric_rsd folder is already on the instance (e.g., via SCP), skip this.
# Otherwise, clone from your repo:
#   git clone <your-repo-url> ~/bariatric_rsd
#
# For now, we assume the code is at ~/bariatric_rsd/
if [ ! -d "$HOME/bariatric_rsd" ]; then
    echo "WARNING: ~/bariatric_rsd not found."
    echo "Upload the code with: scp -r bariatric_rsd/ ubuntu@<lambda-ip>:~/"
fi

# ─── 5. Verify code can import ───
echo ""
echo "[5/6] Verifying code imports..."
cd ~/bariatric_rsd/.. 2>/dev/null || cd ~
python3 -c "
from bariatric_rsd.config import DataConfig, ModelConfig, TrainingConfig
from bariatric_rsd.models.bariatric_rsd import BariatricRSD, MultiTaskLoss
from bariatric_rsd.data.annotation_parser import parse_cholec80_annotations
import torch

# Quick model sanity check
model = BariatricRSD(
    encoder_name='resnet50',
    encoder_pretrained=True,
    hta_embed_dim=512,
    hta_num_heads=8,
    hta_depth=4,
    num_phase_orders=1,
    num_phases=7,
)
model = model.cuda()

# Dummy forward pass
dummy = torch.randn(2, 16, 3, 224, 224).cuda()
cluster = torch.zeros(2, dtype=torch.long).cuda()
with torch.no_grad():
    out = model(dummy, cluster)

print(f'Model OK — RSD shape: {out[\"rsd\"].shape}, Phase shape: {out[\"phase\"].shape}')
total = sum(p.numel() for p in model.parameters())
print(f'Parameters: {total:,}')
print('GPU forward pass: SUCCESS')
"

# ─── 6. Summary ───
echo ""
echo "============================================"
echo "  SETUP COMPLETE"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. DOWNLOAD CHOLEC80:"
echo "     Request access at: http://camma.u-strasbg.fr/datasets"
echo "     (You may already have access — check your email)"
echo ""
echo "  2. EXTRACT FRAMES from videos:"
echo "     for v in /data/cholec80/videos/video*.mp4; do"
echo "       name=\$(basename \$v .mp4)"
echo "       mkdir -p /data/cholec80/frames/\$name"
echo "       ffmpeg -i \$v -vf fps=1 -q:v 2 /data/cholec80/frames/\$name/frame_%06d.jpg"
echo "     done"
echo ""
echo "  3. COPY ANNOTATIONS:"
echo "     cp /data/cholec80/videos/video*-phase.txt /data/cholec80/phase_annotations/"
echo ""
echo "  4. RUN EXP 1.1 (RSD only baseline):"
echo "     cd ~ && python -m bariatric_rsd.train_cholec80 \\"
echo "       --video_root /data/cholec80/frames \\"
echo "       --annotation_dir /data/cholec80/phase_annotations \\"
echo "       --output_dir ~/experiments/cholec80_exp1_1 \\"
echo "       --phase_weight 0.0 --deviation_weight 0.0 \\"
echo "       --wandb"
echo ""
echo "  5. RUN EXP 1.2 (RSD + Phase):"
echo "     cd ~ && python -m bariatric_rsd.train_cholec80 \\"
echo "       --video_root /data/cholec80/frames \\"
echo "       --annotation_dir /data/cholec80/phase_annotations \\"
echo "       --output_dir ~/experiments/cholec80_exp1_2 \\"
echo "       --phase_weight 0.3 --deviation_weight 0.0 \\"
echo "       --wandb"
echo ""

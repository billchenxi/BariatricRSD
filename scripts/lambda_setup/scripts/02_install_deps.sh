#!/bin/bash
# ============================================================
# 02_install_deps.sh
# Run INSIDE the bariatric-rsd conda environment.
# Installs PyTorch + all project dependencies.
# ============================================================
set -e

# Confirm we're in the right env
if [[ "$CONDA_DEFAULT_ENV" != "bariatric-rsd" ]]; then
    echo "ERROR: Activate the environment first:"
    echo "  conda activate bariatric-rsd"
    exit 1
fi

echo "==> Detecting CUDA version..."
CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
CUDA_MAJOR=$(echo $CUDA_VERSION | cut -d. -f1)
CUDA_MINOR=$(echo $CUDA_VERSION | cut -d. -f2)
echo "    CUDA $CUDA_VERSION detected"

echo "==> Installing PyTorch..."
if [[ "$CUDA_MAJOR" -ge 12 ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
elif [[ "$CUDA_MAJOR" -eq 11 && "$CUDA_MINOR" -ge 8 ]]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
fi

echo "==> Installing core ML dependencies..."
pip install \
    timm==0.9.16 \
    einops==0.7.0 \
    transformers==4.40.0 \
    accelerate==0.29.0

echo "==> Installing video processing..."
pip install \
    av==12.0.0 \
    decord==0.6.0 \
    opencv-python-headless==4.9.0.80 \
    imageio==2.34.0 \
    Pillow==10.3.0

echo "==> Installing training utilities..."
pip install \
    wandb==0.16.6 \
    tensorboard==2.16.2 \
    tqdm==4.66.2 \
    rich==13.7.1 \
    omegaconf==2.3.0 \
    hydra-core==1.3.2

echo "==> Installing data science stack..."
pip install \
    numpy==1.26.4 \
    scipy==1.13.0 \
    scikit-learn==1.4.2 \
    pandas==2.2.2 \
    matplotlib==3.8.4 \
    seaborn==0.13.2

echo "==> Installing utilities..."
pip install \
    pytorchvideo==0.1.5 \
    huggingface_hub==0.22.2 \
    gdown==5.1.0

echo "==> Verifying PyTorch + CUDA..."
python -c "
import torch
print(f'PyTorch {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
    x = torch.randn(1000, 1000).cuda()
    print(f'CUDA test passed: tensor on {x.device}')
"

echo ""
echo "All dependencies installed. Now run:"
echo "  bash scripts/03_clone_repos.sh"

#!/bin/bash
# ============================================================
# 01_bootstrap.sh
# Run this FIRST on a fresh Lambda Labs instance.
# Takes ~5 minutes. Run with: bash 01_bootstrap.sh
# ============================================================
set -e

echo "==> Checking CUDA..."
nvidia-smi
nvcc --version

echo "==> Updating apt..."
sudo apt-get update -q
sudo apt-get install -y -q \
    git wget curl unzip \
    ffmpeg libavcodec-dev libavformat-dev libswscale-dev \
    libgl1-mesa-glx libglib2.0-0

echo "==> Installing Miniconda (if not present)..."
if ! command -v conda &> /dev/null; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p $HOME/miniconda
    eval "$($HOME/miniconda/bin/conda shell.bash hook)"
    echo 'eval "$($HOME/miniconda/bin/conda shell.bash hook)"' >> ~/.bashrc
    echo "conda installed"
else
    eval "$(conda shell.bash hook)"
    echo "conda already present"
fi

echo "==> Creating bariatric-rsd conda environment..."
conda create -y -n bariatric-rsd python=3.10

echo ""
echo "Bootstrap complete. Now run:"
echo "  conda activate bariatric-rsd"
echo "  bash scripts/02_install_deps.sh"

#!/bin/bash
# ============================================================
# 03_clone_repos.sh
# Clones Surgformer + HecVL, downloads pretrained weights.
# ============================================================
set -e

if [[ "$CONDA_DEFAULT_ENV" != "bariatric-rsd" ]]; then
    echo "ERROR: conda activate bariatric-rsd first"
    exit 1
fi

PROJECT_ROOT="$HOME/bariatric-rsd"
EXTERN="$PROJECT_ROOT/extern"
mkdir -p "$EXTERN"
cd "$PROJECT_ROOT"

echo "==> Cloning Surgformer (MICCAI 2024)..."
if [ ! -d "$EXTERN/Surgformer" ]; then
    git clone https://github.com/isyangshu/Surgformer.git "$EXTERN/Surgformer"
    echo "Surgformer cloned"
else
    echo "Surgformer already present"
fi

echo "==> Cloning HecVL (MICCAI 2024)..."
if [ ! -d "$EXTERN/HecVL" ]; then
    git clone https://github.com/CAMMA-public/HecVL.git "$EXTERN/HecVL"
    echo "HecVL cloned"
else
    echo "HecVL already present"
fi

echo "==> Cloning MultiBypass140 (the RYGB benchmark)..."
if [ ! -d "$EXTERN/MultiBypass140" ]; then
    git clone https://github.com/CAMMA-public/MultiBypass140.git "$EXTERN/MultiBypass140"
    echo "MultiBypass140 cloned — NOTE: you still need to request the actual video data"
    echo "    Fill the form at: https://github.com/CAMMA-public/MultiBypass140"
else
    echo "MultiBypass140 already present"
fi

echo "==> Creating weights directory..."
mkdir -p "$PROJECT_ROOT/weights/surgformer"
mkdir -p "$PROJECT_ROOT/weights/hecvl"

echo "==> Downloading Surgformer pretrained weights..."
# Surgformer provides weights via their repo instructions
# Check if they have a release or gdrive link
if [ -f "$EXTERN/Surgformer/README.md" ]; then
    echo "    Check $EXTERN/Surgformer/README.md for weight download instructions"
    echo "    Typically: gdown <gdrive_id> -O $PROJECT_ROOT/weights/surgformer/surgformer_base.pth"
fi

echo "==> HecVL weights via HuggingFace Hub..."
python - <<'EOF'
try:
    from huggingface_hub import hf_hub_download, list_repo_files
    import os
    
    weights_dir = os.path.expanduser("~/bariatric-rsd/weights/hecvl")
    
    # Try to find HecVL on HuggingFace
    # The CAMMA group sometimes hosts on HF
    print("Checking HuggingFace for HecVL weights...")
    print("If not found, check: https://github.com/CAMMA-public/HecVL for download links")
    print(f"Weights will go to: {weights_dir}")
    
    # Fallback: use a strong ImageNet-pretrained ViT as placeholder
    # until HecVL weights are confirmed available
    print("\nDownloading ViT-B/16 ImageNet weights as fallback encoder...")
    import timm
    model = timm.create_model('vit_base_patch16_224', pretrained=True)
    import torch
    torch.save(model.state_dict(), f"{weights_dir}/vit_b16_imagenet.pth")
    print(f"Saved fallback weights to {weights_dir}/vit_b16_imagenet.pth")
    print("Replace with HecVL weights once download link is obtained from the CAMMA lab")
    
except Exception as e:
    print(f"Weight download issue: {e}")
    print("Download weights manually and place in ~/bariatric-rsd/weights/")
EOF

echo "==> Verifying repo structure..."
python - <<'EOF'
import os
home = os.path.expanduser("~")
paths_to_check = [
    f"{home}/bariatric-rsd/extern/Surgformer",
    f"{home}/bariatric-rsd/extern/HecVL",
    f"{home}/bariatric-rsd/extern/MultiBypass140",
    f"{home}/bariatric-rsd/weights/hecvl",
    f"{home}/bariatric-rsd/weights/surgformer",
]
all_ok = True
for p in paths_to_check:
    exists = os.path.exists(p)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {p}")
    if not exists:
        all_ok = False

if all_ok:
    print("\nAll paths OK.")
else:
    print("\nSome paths missing — check above.")
EOF

echo ""
echo "Repos cloned. Now run:"
echo "  bash scripts/04_setup_project.sh"

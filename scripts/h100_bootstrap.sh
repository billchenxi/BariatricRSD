#!/bin/bash
# h100_bootstrap.sh
#
# Bring a fresh Lambda H100 80GB PCIe instance up to parity with the GH200
# working copy and start causal-cluster development.
#
# Usage (from YOUR LAPTOP, after Lambda gives you the new instance IP):
#
#   export H100_IP=<new.ip.here>
#   export GH200_IP=192.222.50.14
#   bash scripts/h100_bootstrap.sh
#
# Prereqs on laptop:
#   - rsd.pem exists at repo root (same key works for both instances)
#   - gh200 is reachable and is the source of truth for code + labels
#
# This script:
#   1. Sanity-checks SSH to both instances
#   2. Rsyncs code + labels from GH200 to H100 (skips raw video zips)
#   3. Installs conda env + Python deps on H100
#   4. Extracts MB140 frames on H100 (the 150 GB regenerable chunk)
#   5. Leaves H100 ready to run brsd_lib.causal_cluster

set -eu

: "${H100_IP:?set H100_IP to the new Lambda instance IP}"
: "${GH200_IP:=192.222.50.14}"
KEY="${KEY:-$(pwd)/rsd.pem}"
if [ ! -f "$KEY" ]; then
  echo "ERROR: SSH key $KEY not found"
  exit 1
fi

SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o ConnectTimeout=15"

echo "==> [1/5] SSH sanity check"
ssh $SSH_OPTS ubuntu@"$H100_IP"  "echo H100 ok; nvidia-smi --query-gpu=name,memory.total --format=csv"
ssh $SSH_OPTS ubuntu@"$GH200_IP" "echo GH200 ok"

echo "==> [2/5] Installing base conda env + deps on H100"
ssh $SSH_OPTS ubuntu@"$H100_IP" bash -s <<'REMOTE'
set -eu
if ! command -v conda >/dev/null 2>&1; then
  curl -sL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh -o /tmp/miniconda.sh || \
    curl -sL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh  -o /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p $HOME/miniconda3
  echo '. $HOME/miniconda3/etc/profile.d/conda.sh' >> ~/.bashrc
fi
source $HOME/miniconda3/etc/profile.d/conda.sh || true
conda create -n brsd python=3.10 -y || true
conda activate brsd
pip install --upgrade pip
pip install torch==2.5.1 torchvision timm==0.9.16 pandas numpy scipy scikit-learn tqdm wandb pillow opencv-python-headless
echo "python deps installed:"
python -c "import torch,timm; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
REMOTE

echo "==> [3/5] Rsyncing code + labels from GH200 to H100"
# Pull tarball on GH200 side (fast, avoids 150 GB of video frames)
ssh $SSH_OPTS ubuntu@"$GH200_IP" "cd /lambda/nfs/bariatric-rsd && \
  tar --exclude='extern/MultiBypass140/datasets/MultiBypass140/multibypass06_corrected/frames' \
      --exclude='outputs/*/checkpoint_epoch*.pth' \
      --exclude='wandb/*/logs' \
      -czf /tmp/brsd_code.tgz src/ scripts/ labels/ configs/ brsd_lib/ outputs/run010_mb140_fold0_seed*/best_model.pth outputs/run022_mb140_fold*_seed*/best_model.pth 2>/dev/null || true"
scp $SSH_OPTS ubuntu@"$GH200_IP":/tmp/brsd_code.tgz /tmp/brsd_code.tgz
scp $SSH_OPTS /tmp/brsd_code.tgz ubuntu@"$H100_IP":/tmp/brsd_code.tgz
ssh $SSH_OPTS ubuntu@"$H100_IP" "mkdir -p ~/bariatric-rsd && cd ~/bariatric-rsd && tar -xzf /tmp/brsd_code.tgz && ls -la"

echo "==> [4/5] Extracting MB140 frames on H100 (the 150 GB regenerable chunk)"
# Option A: re-download raw zips via dataset script (slow, ~1 hr)
# Option B: rsync pre-extracted frames from GH200 NFS (~90 min at 100 MB/s)
# We do Option B — simpler and avoids re-paying extraction CPU cost.
ssh $SSH_OPTS ubuntu@"$H100_IP" "mkdir -p ~/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140/multibypass06_corrected/frames"
echo "    (rsync running in a detached screen; monitor with 'screen -ls' on H100)"
ssh $SSH_OPTS ubuntu@"$H100_IP" "screen -dmS framesync bash -lc 'rsync -av --progress ubuntu@$GH200_IP:/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140/multibypass06_corrected/frames/ ~/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140/multibypass06_corrected/frames/ > /tmp/framesync.log 2>&1'"

echo "==> [5/5] H100 ready. Next steps:"
echo "  1. Wait for 'framesync' screen on H100 to finish (~90 min). Check:"
echo "       ssh -i $KEY ubuntu@$H100_IP 'tail -f /tmp/framesync.log'"
echo "  2. When done, kick off the first causal-cluster smoke test:"
echo "       ssh -i $KEY ubuntu@$H100_IP"
echo "       cd ~/bariatric-rsd && conda activate brsd"
echo "       python3 -m brsd_lib.causal_cluster \\"
echo "         --checkpoint outputs/run010_mb140_fold0_seed42/best_model.pth \\"
echo "         --cluster_artifacts labels/mb140_fold0_kmeans_artifacts.json \\"
echo "         --label_json labels/mb140_fold0_labels_kmeans.json \\"
echo "         --data_root extern/MultiBypass140/datasets/MultiBypass140 \\"
echo "         --split val \\"
echo "         --output_json outputs/run023_causal_smoke_fold0.json \\"
echo "         --project_src ~/bariatric-rsd/src"
echo ""
echo "    If MAE is within ~0.5 min of the oracle number (12.59), causal"
echo "    conditioning works at inference time. If it's much worse, we"
echo "    need to retrain with causal sampling during training."

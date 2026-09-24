# BariatricRSD — NeurIPS 2026

Multi-task Transformer for real-time Remaining Surgery Duration (RSD) prediction
and intraoperative deviation detection in laparoscopic RYGB bariatric surgery.

## Quick start (Lambda Labs fresh instance)

```bash
# 1. Get the code onto your Lambda instance
scp -r bariatric-rsd/ ubuntu@<your-lambda-ip>:~/

# 2. SSH in and run the deploy script
ssh ubuntu@<your-lambda-ip>
cd bariatric-rsd
bash deploy.sh
```

That's it. The deploy script handles everything:
bootstrap → conda env → dependencies → external repos → smoke test.

---

## Directory structure

```
bariatric-rsd/
├── deploy.sh                    ← run this first on Lambda
├── scripts/
│   ├── 01_bootstrap.sh          ← conda, apt packages
│   ├── 02_install_deps.sh       ← PyTorch, timm, WandB, etc.
│   ├── 03_clone_repos.sh        ← Surgformer, HecVL, MultiBypass140
│   ├── 04_setup_project.sh      ← directory scaffold
│   └── 05_smoke_test.py         ← end-to-end pipeline check
├── src/
│   ├── data/
│   │   ├── dataset.py           ← BariatricFrameDataset, MultiBypass140Dataset
│   │   └── prepare_labels.py    ← convert 2019 annotations → labels.json
│   ├── models/
│   │   └── bariatric_rsd.py     ← HecVL + Surgformer HTA + 3 MTL heads
│   └── training/
│       └── train.py             ← training loop, evaluation, checkpointing
├── configs/                     ← YAML configs for different runs
├── data/
│   ├── raw/                     ← symlink or mount your actual data here
│   ├── processed/
│   └── splits/
├── outputs/
│   ├── checkpoints/
│   ├── logs/
│   └── predictions/
├── extern/                      ← cloned external repos (Surgformer, HecVL)
└── weights/                     ← pretrained checkpoints
```

---

## Step by step (manual)

### 1. Environment setup

```bash
conda activate bariatric-rsd
wandb login    # paste your API key from wandb.ai/authorize
```

### 2. Prepare your data

Upload your 4000+ bariatric surgery videos and annotations to Lambda:

```bash
# From your local machine:
rsync -avz --progress /path/to/annotations/ ubuntu@<lambda-ip>:/data/bariatric_surgery/annotations/
rsync -avz --progress /path/to/videos/      ubuntu@<lambda-ip>:/data/bariatric_surgery/videos/
```

Then extract frames and build the label file:

```bash
python src/data/prepare_labels.py \
  --ann_dir /data/bariatric_surgery/annotations \
  --frames_dir /data/bariatric_surgery/frames \
  --output labels/bariatric_labels.json \
  --extract_frames \
  --fps 1 \
  --val_fraction 0.1 \
  --test_fraction 0.1
```

**Note:** Edit `src/data/prepare_labels.py` → `load_2019_annotation()` to match
your actual 2019 annotation format (CSV / JSON / pickle).

### 3. Download MultiBypass140

Request access at: https://github.com/CAMMA-public/MultiBypass140

Then run their frame extraction script and point `MULTIBYPASS_DATA` in `.env`
to the extracted frames directory.

### 4. Download HecVL / Surgformer weights

**Surgformer** weights: follow instructions in `extern/Surgformer/README.md`
```bash
# Typically something like:
gdown <gdrive_id> -O weights/surgformer/surgformer_base.pth
```

**HecVL** weights: check `extern/HecVL/README.md` or contact the CAMMA lab
(camma.u-strasbg.fr). While waiting, the fallback ViT-B/16 ImageNet weights
at `weights/hecvl/vit_b16_imagenet.pth` will be used automatically.

### 5. Train

**Single GPU:**
```bash
python src/training/train.py \
  --label_json labels/bariatric_labels.json \
  --data_root /data/bariatric_surgery \
  --encoder_checkpoint weights/hecvl/hecvl_encoder.pth \
  --output_dir outputs/run_001 \
  --epochs 50 \
  --batch_size 8 \
  --lr 1e-4 \
  --sequence_len 8 \
  --embed_dim 768 \
  --temporal_layers 6
```

**Multi-GPU (4x A100):**
```bash
torchrun --nproc_per_node=4 src/training/train.py \
  --label_json labels/bariatric_labels.json \
  --data_root /data/bariatric_surgery \
  --output_dir outputs/run_001_4gpu \
  --batch_size 32 \
  --epochs 50
```

---

## Key papers to beat

| Paper | Metric | Our target |
|---|---|---|
| TransLocal (2024) | MAE = 7.1 min on Cholec80 | MAE < 7.1 min |
| BetaMixer (MICCAI 2025) | F1 = 0.76 on RYGB bypass | F1 > 0.76 |
| MultiBypass140 TCN (2021) | Phase F1 on BernBypass70 | +5 F1 points |

## NeurIPS 2026 deadline

- Abstract due: **May 4, 2026 AoE**
- Full paper due: **May 6, 2026 AoE**
- Conference: December 6–12, 2026

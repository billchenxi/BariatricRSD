# Environment used to produce the reported numbers

The 3.56 min Cholec80 result and the strict-protocol MB140 numbers were
produced on the following stack. Reviewers reproducing the numbers should
match this within reason. The most version-sensitive component is
**scikit-learn**, whose `IsotonicRegression` numerical tolerance changed
between 0.23 and later releases.

## Hardware

| Component | Spec |
|---|---|
| GPU | NVIDIA GH200 96 GB or 480 GB (Lambda Cloud `gpu_1x_gh200`) |
| CPU | NVIDIA Grace ARM (72 cores) on GH200, or Xeon for x86 nodes |
| RAM | 480 GB unified memory on GH200 |
| Storage | NFS at `/lambda/nfs/bariatric-rsd/` |

A single A100 80 GB or H100 80 GB will reproduce the inference numbers
identically. With smaller VRAM (e.g., 24 GB), reduce
`--batch_size 64 → 16` or `8` — predictions are deterministic w.r.t.
batch size for inference (no batchnorm running stats updated).

## Operating system

| Component | Spec |
|---|---|
| OS | Ubuntu 22.04 LTS |
| Kernel | Linux 6.5+ |
| CUDA toolkit | 12.6 |
| cuDNN | 9.x (bundled with PyTorch wheel) |
| NVIDIA driver | 555+ |

## Python stack

| Package | Version | Notes |
|---|---|---|
| Python | 3.11.x | tested 3.11.7 and 3.11.9 |
| torch | 2.7.0 | CUDA 12.6 wheel |
| torchvision | 0.22.0 | matches torch 2.7.0 |
| timm | 1.0.26 | ViT-B/16 layout depends on this |
| scipy | **1.8.0** | `pearsonr().statistic` is 1.9+; we use `pearsonr()[0]` |
| scikit-learn | **0.23.2** | `IsotonicRegression` numerical tolerance change in 1.0+ shifts MAE by ~0.01 min |
| numpy | 1.24.4 | |
| pandas | 2.0.3 | |
| matplotlib | 3.7.5 | for the figure builders only |
| Pillow | 10.3.0 | JPEG decode |

The pinned `requirements.txt` in this folder produces the same
`IsotonicRegression` numerical behavior as the original training run.

## Determinism

Inference is deterministic across runs given:
- same checkpoints (verified by SHA256)
- same dataloader ordering (`shuffle=False` for inference)
- same numerical libraries (esp. scikit-learn)
- same Python and CUDA versions

We do **not** set `torch.backends.cudnn.deterministic = True` during
training (it would slow training significantly), but inference uses no
operations that depend on cudnn algorithm selection in non-deterministic
ways at the precisions we use.

The 3.56 min number reproduces to ±0.01 min on identical environments.
Larger drift indicates a mismatched numerical library — most commonly
scikit-learn ≥ 1.0.

## Quick environment check

```bash
python3 -c "
import torch, sklearn, scipy, timm
print(f'torch:        {torch.__version__}')
print(f'cuda:         {torch.version.cuda}')
print(f'scikit-learn: {sklearn.__version__}')
print(f'scipy:        {scipy.__version__}')
print(f'timm:         {timm.__version__}')
"
```

Expected:
```
torch:        2.7.0+cu126
cuda:         12.6
scikit-learn: 0.23.2
scipy:        1.8.0
timm:         1.0.26
```

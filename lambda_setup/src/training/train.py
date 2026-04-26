"""
src/training/train.py

Main training loop for BariatricRSD.
Supports single-GPU and multi-GPU (DDP) training.

Usage:
  # Single GPU
  python src/training/train.py --config configs/train_bariatric.yaml

  # Multi-GPU (e.g. 4 GPUs)
  torchrun --nproc_per_node=4 src/training/train.py --config configs/train_bariatric.yaml
"""

import os
import sys
import time
import argparse
import json
import random
from pathlib import Path

import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler
from torch.optim.lr_scheduler import CosineAnnealingLR
import numpy as np
from scipy.stats import pearsonr, spearmanr

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from models.bariatric_rsd import BariatricRSD, BariatricRSDLoss
from data.dataset import BariatricFrameDataset, get_dataloader


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_rsd_metrics(
    rsd_pred_norm: np.ndarray,
    rsd_true_norm: np.ndarray,
    rsd_true_sec: np.ndarray,
) -> dict:
    """Compute MAE (normalized + seconds), Pearson r, Spearman r."""
    mae_norm = np.mean(np.abs(rsd_pred_norm - rsd_true_norm))
    rsd_pred_sec = rsd_pred_norm * rsd_true_sec / (rsd_true_norm + 1e-8)  # approx
    mae_sec = np.mean(np.abs(rsd_pred_sec - rsd_true_sec))

    pr = pearsonr(rsd_pred_norm, rsd_true_norm).statistic if len(rsd_pred_norm) > 2 else 0.0
    sr = spearmanr(rsd_pred_norm, rsd_true_norm).statistic if len(rsd_pred_norm) > 2 else 0.0

    return {
        "mae_normalized": float(mae_norm),
        "mae_seconds": float(mae_sec),
        "mae_minutes": float(mae_sec / 60),
        "pearson_r": float(pr),
        "spearman_r": float(sr),
    }


def compute_deviation_metrics(dev_pred_logits: np.ndarray, dev_true: np.ndarray) -> dict:
    from sklearn.metrics import f1_score, precision_score, recall_score
    dev_pred = (torch.sigmoid(torch.tensor(dev_pred_logits)) > 0.5).numpy().astype(int)
    dev_true = dev_true.astype(int)
    f1 = f1_score(dev_true, dev_pred, zero_division=0)
    prec = precision_score(dev_true, dev_pred, zero_division=0)
    rec = recall_score(dev_true, dev_pred, zero_division=0)
    return {"deviation_f1": float(f1), "deviation_precision": float(prec), "deviation_recall": float(rec)}


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ── Training step ─────────────────────────────────────────────────────────────

def train_one_epoch(
    model,
    loader,
    optimizer,
    loss_fn,
    device,
    epoch,
    scaler,
    log_interval=50,
    no_phase_order: bool = False,
):
    model.train()
    total_loss = 0.0
    rsd_losses, dev_losses, phase_losses = [], [], []
    t0 = time.time()

    for step, batch in enumerate(loader):
        frames = batch["frames"].to(device, non_blocking=True)
        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)
        if no_phase_order:
            cluster = torch.zeros_like(cluster)
        targets = {
            "rsd_normalized": batch["rsd_normalized"].to(device, non_blocking=True),
            "is_deviation": batch["is_deviation"].to(device, non_blocking=True),
            "phase_label": batch["phase_label"].to(device, non_blocking=True),
        }

        optimizer.zero_grad(set_to_none=True)

        with torch.cuda.amp.autocast():
            preds = model(frames, cluster)
            losses = loss_fn(preds, targets)

        scaler.scale(losses["loss"]).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()

        total_loss += losses["loss"].item()
        rsd_losses.append(losses["loss_rsd"].item())
        dev_losses.append(losses["loss_deviation"].item())
        phase_losses.append(losses["loss_phase"].item())

        if step % log_interval == 0:
            elapsed = time.time() - t0
            print(f"  Epoch {epoch} | step {step}/{len(loader)} | "
                  f"loss={losses['loss'].item():.4f} "
                  f"(rsd={losses['loss_rsd'].item():.4f}, "
                  f"dev={losses['loss_deviation'].item():.4f}) | "
                  f"{elapsed:.0f}s")

    return {
        "train_loss": total_loss / len(loader),
        "train_loss_rsd": np.mean(rsd_losses),
        "train_loss_deviation": np.mean(dev_losses),
        "train_loss_phase": np.mean(phase_losses),
    }


# ── Validation ────────────────────────────────────────────────────────────────

@torch.no_grad()
def evaluate(model, loader, loss_fn, device, no_phase_order: bool = False):
    model.eval()
    total_loss = 0.0
    all_rsd_pred, all_rsd_true, all_rsd_sec = [], [], []
    all_dev_pred, all_dev_true = [], []

    for batch in loader:
        frames = batch["frames"].to(device, non_blocking=True)
        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)
        if no_phase_order:
            cluster = torch.zeros_like(cluster)
        targets = {
            "rsd_normalized": batch["rsd_normalized"].to(device, non_blocking=True),
            "is_deviation": batch["is_deviation"].to(device, non_blocking=True),
            "phase_label": batch["phase_label"].to(device, non_blocking=True),
        }

        with torch.cuda.amp.autocast():
            preds = model(frames, cluster)
            losses = loss_fn(preds, targets)

        total_loss += losses["loss"].item()
        all_rsd_pred.append(preds["rsd"].cpu().numpy())
        all_rsd_true.append(batch["rsd_normalized"].numpy())
        all_rsd_sec.append(batch["rsd_sec"].numpy())
        all_dev_pred.append(preds["deviation"].cpu().numpy())
        all_dev_true.append(batch["is_deviation"].numpy())

    rsd_metrics = compute_rsd_metrics(
        np.concatenate(all_rsd_pred),
        np.concatenate(all_rsd_true),
        np.concatenate(all_rsd_sec),
    )
    dev_metrics = compute_deviation_metrics(
        np.concatenate(all_dev_pred),
        np.concatenate(all_dev_true),
    )

    return {"val_loss": total_loss / len(loader), **rsd_metrics, **dev_metrics}


# ── Checkpoint ────────────────────────────────────────────────────────────────

def save_checkpoint(model, optimizer, scheduler, epoch, metrics, output_dir, is_best=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "epoch": epoch,
        "model": model.state_dict() if not isinstance(model, DDP) else model.module.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "metrics": metrics,
    }
    ckpt_path = output_dir / f"checkpoint_epoch{epoch:03d}.pth"
    torch.save(state, ckpt_path)
    print(f"  Saved checkpoint: {ckpt_path}")

    if is_best:
        best_path = output_dir / "best_model.pth"
        torch.save(state, best_path)
        print(f"  New best model saved: {best_path}")

    return ckpt_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label_json", type=str, required=True,
                        help="Path to dataset label JSON")
    parser.add_argument("--data_root", type=str, required=True,
                        help="Root dir containing frame images")
    parser.add_argument("--output_dir", type=str, default="outputs/run_001")
    parser.add_argument("--encoder_checkpoint", type=str, default=None)
    parser.add_argument("--encoder_freeze_layers", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight_decay", type=float, default=0.05)
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--sequence_len", type=int, default=8)
    parser.add_argument("--frame_stride", type=int, default=5)
    parser.add_argument("--img_size", type=int, default=224)
    parser.add_argument("--embed_dim", type=int, default=768)
    parser.add_argument("--temporal_layers", type=int, default=6)
    parser.add_argument("--num_phases", type=int, default=12)
    parser.add_argument("--wandb_project", type=str, default="bariatric-rsd-neurips2026")
    parser.add_argument("--wandb_run_name", type=str, default=None)
    parser.add_argument("--no_wandb", action="store_true")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for python/numpy/torch")
    parser.add_argument("--target_position", type=str, default="middle",
                        choices=["middle", "last"],
                        help="Label frame inside each clip. 'middle' preserves the legacy centered-window protocol; "
                             "'last' makes the clip end at the prediction timestamp.")
    parser.add_argument("--decouple_phase_head", action="store_true",
                        help="Predict phase from visual features before workflow-token mixing.")
    parser.add_argument("--no_phase_order", action="store_true",
                        help="Replace every workflow cluster ID with 0 as a constant-token ablation.")
    args = parser.parse_args()

    # Distributed setup
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    is_distributed = world_size > 1
    is_main = local_rank == 0

    if is_distributed:
        dist.init_process_group("nccl")
        torch.cuda.set_device(local_rank)
        device = torch.device(f"cuda:{local_rank}")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    set_seed(args.seed)

    if is_main:
        print(f"Device: {device} | World size: {world_size}")

    # WandB
    if is_main and WANDB_AVAILABLE and not args.no_wandb:
        wandb.init(
            project=args.wandb_project,
            name=args.wandb_run_name or f"run_{time.strftime('%Y%m%d_%H%M%S')}",
            config=vars(args),
        )

    # Datasets
    train_ds = BariatricFrameDataset(
        args.label_json, args.data_root, split="train",
        sequence_len=args.sequence_len, frame_stride=args.frame_stride,
        img_size=args.img_size, augment=True,
        target_position=args.target_position,
    )
    val_ds = BariatricFrameDataset(
        args.label_json, args.data_root, split="val",
        sequence_len=args.sequence_len, frame_stride=args.frame_stride,
        img_size=args.img_size, augment=False,
        target_position=args.target_position,
    )

    train_sampler = DistributedSampler(train_ds) if is_distributed else None
    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size,
        sampler=train_sampler, shuffle=(train_sampler is None),
        num_workers=args.num_workers, pin_memory=True, drop_last=True,
        persistent_workers=(args.num_workers > 0),
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers, pin_memory=True,
    )

    # Model
    model = BariatricRSD(
        encoder_checkpoint=args.encoder_checkpoint,
        encoder_freeze_layers=args.encoder_freeze_layers,
        embed_dim=args.embed_dim,
        temporal_layers=args.temporal_layers,
        num_phases=args.num_phases,
        decouple_phase_head=args.decouple_phase_head,
    ).to(device)

    if is_distributed:
        model = DDP(model, device_ids=[local_rank], find_unused_parameters=True)

    # Loss, optimizer, scheduler
    loss_fn = BariatricRSDLoss(learn_weights=True).to(device)
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(loss_fn.parameters()),
        lr=args.lr, weight_decay=args.weight_decay,
    )
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler = torch.cuda.amp.GradScaler()

    # Resume
    start_epoch = 0
    best_mae = float("inf")
    if args.resume and Path(args.resume).exists():
        ckpt = torch.load(args.resume, map_location=device)
        model_state = ckpt["model"]
        if is_distributed:
            model.module.load_state_dict(model_state)
        else:
            model.load_state_dict(model_state)
        optimizer.load_state_dict(ckpt["optimizer"])
        scheduler.load_state_dict(ckpt["scheduler"])
        start_epoch = ckpt["epoch"] + 1
        best_mae = ckpt["metrics"].get("mae_minutes", float("inf"))
        print(f"Resumed from epoch {start_epoch}, best MAE = {best_mae:.2f} min")

    # Training loop
    for epoch in range(start_epoch, args.epochs):
        if is_distributed:
            train_sampler.set_epoch(epoch)

        train_metrics = train_one_epoch(
            model, train_loader, optimizer, loss_fn, device, epoch, scaler,
            no_phase_order=args.no_phase_order,
        )
        val_metrics = evaluate(model, val_loader, loss_fn, device,
                               no_phase_order=args.no_phase_order)
        scheduler.step()

        is_best = val_metrics["mae_minutes"] < best_mae
        if is_best:
            best_mae = val_metrics["mae_minutes"]

        if is_main:
            all_metrics = {**train_metrics, **val_metrics, "epoch": epoch, "lr": scheduler.get_last_lr()[0]}
            print(f"\nEpoch {epoch:3d} | "
                  f"val_mae={val_metrics['mae_minutes']:.2f}min | "
                  f"pearson_r={val_metrics['pearson_r']:.4f} | "
                  f"dev_f1={val_metrics['deviation_f1']:.3f} | "
                  f"best={best_mae:.2f}min\n")

            if WANDB_AVAILABLE and not args.no_wandb:
                wandb.log(all_metrics)

            save_checkpoint(model, optimizer, scheduler, epoch, val_metrics,
                            args.output_dir, is_best=is_best)

    if is_main and WANDB_AVAILABLE and not args.no_wandb:
        wandb.finish()

    if is_distributed:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()

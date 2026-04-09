"""
Training Pipeline
=================
Modern PyTorch training loop for the BariatricRSD model.

Features:
  - Mixed precision training (AMP)
  - Gradient clipping
  - Learning rate warmup + cosine annealing
  - Early stopping
  - WandB logging (optional)
  - Checkpoint saving and resumption

Replaces the manual training loops from the 2019 codebase with
a clean, well-structured training pipeline.
"""

import os
import time
import math
from typing import Dict, Optional, Tuple
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import GradScaler, autocast

try:
    import wandb

    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False


class CosineWarmupScheduler:
    """Learning rate scheduler with linear warmup + cosine annealing."""

    def __init__(
        self,
        optimizer: torch.optim.Optimizer,
        warmup_epochs: int,
        max_epochs: int,
        min_lr: float = 1e-6,
    ):
        self.optimizer = optimizer
        self.warmup_epochs = warmup_epochs
        self.max_epochs = max_epochs
        self.min_lr = min_lr
        self.base_lrs = [pg["lr"] for pg in optimizer.param_groups]

    def step(self, epoch: int):
        if epoch < self.warmup_epochs:
            # Linear warmup
            alpha = epoch / max(self.warmup_epochs, 1)
        else:
            # Cosine annealing
            progress = (epoch - self.warmup_epochs) / max(
                self.max_epochs - self.warmup_epochs, 1
            )
            alpha = 0.5 * (1.0 + math.cos(math.pi * progress))

        for pg, base_lr in zip(self.optimizer.param_groups, self.base_lrs):
            pg["lr"] = max(self.min_lr, base_lr * alpha)

    def get_lr(self) -> float:
        return self.optimizer.param_groups[0]["lr"]


class EarlyStopping:
    """Early stopping to terminate training when validation loss stops improving."""

    def __init__(self, patience: int = 15, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float("inf")
        self.counter = 0

    def should_stop(self, val_loss: float) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            return False
        else:
            self.counter += 1
            return self.counter >= self.patience


class Trainer:
    """
    Training manager for BariatricRSD.

    Handles the full training loop with modern best practices:
    mixed precision, gradient clipping, learning rate scheduling,
    early stopping, checkpointing, and optional WandB logging.
    """

    def __init__(
        self,
        model: nn.Module,
        criterion: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        learning_rate: float = 1e-4,
        weight_decay: float = 1e-4,
        max_epochs: int = 100,
        warmup_epochs: int = 5,
        gradient_clip_val: float = 1.0,
        early_stopping_patience: int = 15,
        checkpoint_dir: str = "checkpoints",
        save_every_n_epochs: int = 5,
        device: str = "cuda",
        mixed_precision: bool = True,
        use_wandb: bool = False,
        wandb_project: str = "bariatric-rsd",
        wandb_run_name: Optional[str] = None,
    ):
        self.model = model.to(device)
        self.criterion = criterion.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.max_epochs = max_epochs
        self.gradient_clip_val = gradient_clip_val
        self.checkpoint_dir = Path(checkpoint_dir)
        self.save_every_n_epochs = save_every_n_epochs
        self.mixed_precision = mixed_precision and device == "cuda"

        # Optimizer: AdamW with weight decay
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay,
            betas=(0.9, 0.999),
        )

        # Learning rate scheduler
        self.scheduler = CosineWarmupScheduler(
            self.optimizer, warmup_epochs, max_epochs
        )

        # Early stopping
        self.early_stopping = EarlyStopping(patience=early_stopping_patience)

        # Mixed precision scaler
        self.scaler = GradScaler(enabled=self.mixed_precision)

        # Logging
        self.use_wandb = use_wandb and WANDB_AVAILABLE
        if self.use_wandb:
            wandb.init(project=wandb_project, name=wandb_run_name)
            wandb.watch(model, log="all", log_freq=100)

        # Create checkpoint directory
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Track best model
        self.best_val_loss = float("inf")
        self.best_epoch = 0

    def train(self) -> Dict[str, list]:
        """
        Run the full training loop.

        Returns:
            Dictionary with training history (losses per epoch).
        """
        history = {
            "train_loss": [],
            "val_loss": [],
            "train_rsd_loss": [],
            "val_rsd_loss": [],
            "learning_rate": [],
        }

        print(f"Starting training for {self.max_epochs} epochs")
        print(f"  Device: {self.device}")
        print(f"  Mixed precision: {self.mixed_precision}")
        print(f"  Train batches: {len(self.train_loader)}")
        print(f"  Val batches: {len(self.val_loader)}")
        print("-" * 60)

        for epoch in range(1, self.max_epochs + 1):
            epoch_start = time.time()

            # Update learning rate
            self.scheduler.step(epoch)
            current_lr = self.scheduler.get_lr()
            history["learning_rate"].append(current_lr)

            # Training phase
            train_metrics = self._train_epoch()
            history["train_loss"].append(train_metrics["loss_total"])
            history["train_rsd_loss"].append(train_metrics["loss_rsd"])

            # Validation phase
            val_metrics = self._validate_epoch()
            history["val_loss"].append(val_metrics["loss_total"])
            history["val_rsd_loss"].append(val_metrics["loss_rsd"])

            epoch_time = time.time() - epoch_start

            # Logging
            print(
                f"Epoch {epoch:3d}/{self.max_epochs} | "
                f"Train: {train_metrics['loss_total']:.4f} | "
                f"Val: {val_metrics['loss_total']:.4f} | "
                f"RSD: {val_metrics['loss_rsd']:.4f} | "
                f"LR: {current_lr:.2e} | "
                f"Time: {epoch_time:.1f}s"
            )

            if self.use_wandb:
                wandb.log(
                    {
                        "epoch": epoch,
                        "train/loss": train_metrics["loss_total"],
                        "train/rsd_loss": train_metrics["loss_rsd"],
                        "train/dev_loss": train_metrics["loss_deviation"],
                        "train/phase_loss": train_metrics["loss_phase"],
                        "val/loss": val_metrics["loss_total"],
                        "val/rsd_loss": val_metrics["loss_rsd"],
                        "val/dev_loss": val_metrics["loss_deviation"],
                        "val/phase_loss": val_metrics["loss_phase"],
                        "learning_rate": current_lr,
                    }
                )

            # Save best model
            if val_metrics["loss_total"] < self.best_val_loss:
                self.best_val_loss = val_metrics["loss_total"]
                self.best_epoch = epoch
                self._save_checkpoint(epoch, is_best=True)

            # Periodic checkpoint
            if epoch % self.save_every_n_epochs == 0:
                self._save_checkpoint(epoch)

            # Early stopping check
            if self.early_stopping.should_stop(val_metrics["loss_total"]):
                print(f"Early stopping at epoch {epoch} (best: {self.best_epoch})")
                break

        print(f"\nTraining complete. Best val loss: {self.best_val_loss:.4f} at epoch {self.best_epoch}")

        if self.use_wandb:
            wandb.finish()

        return history

    def _train_epoch(self) -> Dict[str, float]:
        """Run one training epoch."""
        self.model.train()
        running_metrics = {}
        num_batches = 0

        for batch in self.train_loader:
            # Move data to device
            clips = batch["clip"].to(self.device)
            targets = {
                "rsd": batch["rsd"].to(self.device),
                "deviation": batch["deviation"].to(self.device),
                "phase": batch["phase"].to(self.device),
            }
            cluster_ids = batch["cluster_id"].to(self.device)

            self.optimizer.zero_grad()

            # Forward pass with mixed precision
            with autocast(enabled=self.mixed_precision):
                predictions = self.model(clips, cluster_ids)
                loss, loss_dict = self.criterion(predictions, targets)

            # Backward pass
            self.scaler.scale(loss).backward()

            # Gradient clipping
            if self.gradient_clip_val > 0:
                self.scaler.unscale_(self.optimizer)
                nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.gradient_clip_val
                )

            self.scaler.step(self.optimizer)
            self.scaler.update()

            # Accumulate metrics
            for k, v in loss_dict.items():
                running_metrics[k] = running_metrics.get(k, 0.0) + v
            num_batches += 1

        # Average metrics
        return {k: v / max(num_batches, 1) for k, v in running_metrics.items()}

    @torch.no_grad()
    def _validate_epoch(self) -> Dict[str, float]:
        """Run one validation epoch."""
        self.model.eval()
        running_metrics = {}
        num_batches = 0

        for batch in self.val_loader:
            clips = batch["clip"].to(self.device)
            targets = {
                "rsd": batch["rsd"].to(self.device),
                "deviation": batch["deviation"].to(self.device),
                "phase": batch["phase"].to(self.device),
            }
            cluster_ids = batch["cluster_id"].to(self.device)

            with autocast(enabled=self.mixed_precision):
                predictions = self.model(clips, cluster_ids)
                _, loss_dict = self.criterion(predictions, targets)

            for k, v in loss_dict.items():
                running_metrics[k] = running_metrics.get(k, 0.0) + v
            num_batches += 1

        return {k: v / max(num_batches, 1) for k, v in running_metrics.items()}

    def _save_checkpoint(self, epoch: int, is_best: bool = False):
        """Save a training checkpoint."""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scaler_state_dict": self.scaler.state_dict(),
            "best_val_loss": self.best_val_loss,
        }

        if is_best:
            path = self.checkpoint_dir / "best_model.pth"
        else:
            path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"

        torch.save(checkpoint, path)

    def load_checkpoint(self, checkpoint_path: str):
        """Resume training from a checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "scaler_state_dict" in checkpoint:
            self.scaler.load_state_dict(checkpoint["scaler_state_dict"])
        self.best_val_loss = checkpoint.get("best_val_loss", float("inf"))
        print(f"Resumed from epoch {checkpoint['epoch']}")

"""
BariatricRSD Training Script
============================
Main entry point for training the BariatricRSD multi-task model.

Usage:
    python -m bariatric_rsd.train \
        --video_root /path/to/videos \
        --annotation_json /path/to/annotations.json \
        --output_dir ./experiments/run_001

    # With HecVL pretrained weights:
    python -m bariatric_rsd.train \
        --video_root /path/to/videos \
        --annotation_json /path/to/annotations.json \
        --hecvl_weights /path/to/hecvl_checkpoint.pth \
        --output_dir ./experiments/run_002
"""

import argparse
import random
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from bariatric_rsd.config import DataConfig, ModelConfig, TrainingConfig
from bariatric_rsd.data.annotation_parser import (
    parse_annotation_json,
    determine_phase_order,
    cluster_phase_orders,
)
from bariatric_rsd.data.surgical_dataset import (
    SurgicalClipDataset,
    get_standard_transforms,
    create_data_splits,
)
from bariatric_rsd.models.bariatric_rsd import BariatricRSD, MultiTaskLoss
from bariatric_rsd.training.trainer import Trainer


def parse_args():
    parser = argparse.ArgumentParser(description="Train BariatricRSD model")

    # Data paths
    parser.add_argument("--video_root", type=str, required=True,
                        help="Root directory containing per-video frame folders")
    parser.add_argument("--annotation_json", type=str, required=True,
                        help="Path to annotation JSON file")
    parser.add_argument("--deviation_csv", type=str, default=None,
                        help="Optional CSV with deviation annotations")
    parser.add_argument("--output_dir", type=str, default="./experiments",
                        help="Output directory for checkpoints and logs")

    # Model
    parser.add_argument("--encoder", type=str, default="resnet50",
                        help="Visual encoder model name (timm)")
    parser.add_argument("--hecvl_weights", type=str, default=None,
                        help="Path to HecVL pretrained weights")
    parser.add_argument("--embed_dim", type=int, default=512,
                        help="Transformer embedding dimension")
    parser.add_argument("--hta_depth", type=int, default=4,
                        help="Number of HTA blocks")
    parser.add_argument("--hta_heads", type=int, default=8,
                        help="Number of attention heads")

    # Data
    parser.add_argument("--clip_length", type=int, default=16,
                        help="Number of frames per clip")
    parser.add_argument("--sampling_rate", type=int, default=4,
                        help="Frame sampling rate")
    parser.add_argument("--batch_size", type=int, default=16,
                        help="Training batch size")
    parser.add_argument("--num_workers", type=int, default=8,
                        help="DataLoader workers")
    parser.add_argument("--image_size", type=int, default=224,
                        help="Input image size")

    # Training
    parser.add_argument("--epochs", type=int, default=100,
                        help="Maximum training epochs")
    parser.add_argument("--lr", type=float, default=1e-4,
                        help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=1e-4,
                        help="Weight decay")
    parser.add_argument("--warmup_epochs", type=int, default=5,
                        help="LR warmup epochs")
    parser.add_argument("--patience", type=int, default=15,
                        help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=444,
                        help="Random seed")

    # Loss weights
    parser.add_argument("--rsd_weight", type=float, default=1.0)
    parser.add_argument("--deviation_weight", type=float, default=0.5)
    parser.add_argument("--phase_weight", type=float, default=0.3)

    # Misc
    parser.add_argument("--wandb", action="store_true",
                        help="Enable WandB logging")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume from")

    return parser.parse_args()


def set_seed(seed: int):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main():
    args = parse_args()
    set_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save args
    with open(output_dir / "args.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # ─── Parse annotations ───
    print("Parsing annotations...")
    annotation_dict = parse_annotation_json(args.annotation_json)
    all_video_ids = list(annotation_dict.keys())
    print(f"Found {len(all_video_ids)} annotated videos")

    # Determine phase orderings
    data_config = DataConfig()
    phase_orders = determine_phase_order(annotation_dict, data_config.phase_names)
    cluster_assignments = cluster_phase_orders(phase_orders)
    unique_clusters = set(cluster_assignments.values())
    print(f"Found {len(unique_clusters)} distinct phase orderings")

    # ─── Split data ───
    train_ids, val_ids, test_ids = create_data_splits(
        all_video_ids, seed=args.seed
    )
    print(f"Split: {len(train_ids)} train / {len(val_ids)} val / {len(test_ids)} test")

    # ─── Create datasets ───
    print("Creating datasets...")
    train_transform = get_standard_transforms(args.image_size, is_training=True)
    val_transform = get_standard_transforms(args.image_size, is_training=False)

    train_dataset = SurgicalClipDataset(
        video_root=args.video_root,
        annotation_dict=annotation_dict,
        video_ids=train_ids,
        phase_names=data_config.phase_names,
        clip_length=args.clip_length,
        sampling_rate=args.sampling_rate,
        phase_order_clusters=cluster_assignments,
        transform=train_transform,
    )

    val_dataset = SurgicalClipDataset(
        video_root=args.video_root,
        annotation_dict=annotation_dict,
        video_ids=val_ids,
        phase_names=data_config.phase_names,
        clip_length=args.clip_length,
        sampling_rate=args.sampling_rate,
        phase_order_clusters=cluster_assignments,
        transform=val_transform,
    )

    print(f"Train clips: {len(train_dataset)}, Val clips: {len(val_dataset)}")

    # ─── Create data loaders ───
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
    )

    # ─── Create model ───
    print("Building model...")
    model = BariatricRSD(
        encoder_name=args.encoder,
        encoder_pretrained=True,
        hta_embed_dim=args.embed_dim,
        hta_num_heads=args.hta_heads,
        hta_depth=args.hta_depth,
        num_phase_orders=len(unique_clusters),
        num_phases=len(data_config.phase_names),
    )

    # Load HecVL weights if provided
    if args.hecvl_weights:
        print(f"Loading HecVL weights from {args.hecvl_weights}")
        model.visual_encoder.load_hecvl_weights(args.hecvl_weights)

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")

    # ─── Loss function ───
    criterion = MultiTaskLoss(
        rsd_weight=args.rsd_weight,
        deviation_weight=args.deviation_weight,
        phase_weight=args.phase_weight,
    )

    # ─── Train ───
    trainer = Trainer(
        model=model,
        criterion=criterion,
        train_loader=train_loader,
        val_loader=val_loader,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        max_epochs=args.epochs,
        warmup_epochs=args.warmup_epochs,
        early_stopping_patience=args.patience,
        checkpoint_dir=str(output_dir / "checkpoints"),
        device=device,
        use_wandb=args.wandb,
    )

    if args.resume:
        trainer.load_checkpoint(args.resume)

    history = trainer.train()

    # Save training history
    with open(output_dir / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nDone! Results saved to {output_dir}")


if __name__ == "__main__":
    main()

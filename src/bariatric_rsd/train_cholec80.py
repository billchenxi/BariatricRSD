"""
BariatricRSD — Cholec80 Baseline Training Script
=================================================
Trains the BariatricRSD model on the Cholec80 dataset for RSD + phase recognition.
This is Experiment 1.1 / 1.2 from the research roadmap.

Cholec80 has 7 surgical phases and no explicit "phase-order" variation,
so the phase-order conditioning token gets a single cluster (k=1).

Usage:
    # Exp 1.1: RSD only
    python -m bariatric_rsd.train_cholec80 \
        --video_root /data/cholec80/frames \
        --annotation_dir /data/cholec80/phase_annotations \
        --output_dir ./experiments/cholec80_exp1_1 \
        --phase_weight 0.0 --deviation_weight 0.0

    # Exp 1.2: RSD + Phase recognition
    python -m bariatric_rsd.train_cholec80 \
        --video_root /data/cholec80/frames \
        --annotation_dir /data/cholec80/phase_annotations \
        --output_dir ./experiments/cholec80_exp1_2 \
        --phase_weight 0.3 --deviation_weight 0.0
"""

import argparse
import random
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from bariatric_rsd.data.annotation_parser import (
    parse_cholec80_annotations,
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
    parser = argparse.ArgumentParser(
        description="Train BariatricRSD on Cholec80"
    )

    # Data
    parser.add_argument("--video_root", type=str, required=True,
                        help="Root dir with per-video frame folders (video01/, video02/, ...)")
    parser.add_argument("--annotation_dir", type=str, required=True,
                        help="Dir with Cholec80 phase annotation .txt files")
    parser.add_argument("--output_dir", type=str, default="./experiments/cholec80",
                        help="Output directory")

    # Model
    parser.add_argument("--encoder", type=str, default="resnet50")
    parser.add_argument("--embed_dim", type=int, default=512)
    parser.add_argument("--hta_depth", type=int, default=4)
    parser.add_argument("--hta_heads", type=int, default=8)

    # Data loading
    parser.add_argument("--clip_length", type=int, default=16)
    parser.add_argument("--sampling_rate", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--num_workers", type=int, default=8)
    parser.add_argument("--image_size", type=int, default=224)

    # Training
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--warmup_epochs", type=int, default=5)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--seed", type=int, default=444)

    # Loss weights
    parser.add_argument("--rsd_weight", type=float, default=1.0)
    parser.add_argument("--deviation_weight", type=float, default=0.0,
                        help="Set to 0 for Cholec80 (no deviation labels)")
    parser.add_argument("--phase_weight", type=float, default=0.0,
                        help="0.0 for Exp 1.1 (RSD only), 0.3 for Exp 1.2 (multi-task)")

    # Misc
    parser.add_argument("--wandb", action="store_true")
    parser.add_argument("--wandb_project", type=str, default="bariatric-rsd")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--frame_extension", type=str, default="jpg",
                        help="Frame file extension (jpg or png)")

    return parser.parse_args()


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def main():
    args = parse_args()
    set_seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save args
    with open(output_dir / "args.json", "w") as f:
        json.dump(vars(args), f, indent=2)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

    # ─── Parse Cholec80 annotations ───
    print("Parsing Cholec80 annotations...")
    annotation_dict = parse_cholec80_annotations(
        args.annotation_dir, fps=25.0
    )
    all_video_ids = sorted(annotation_dict.keys())
    print(f"Found {len(all_video_ids)} annotated videos")

    # Get phase names from the data
    phase_names = sorted(set(
        phase for vid_phases in annotation_dict.values()
        for phase in vid_phases.keys()
    ))
    print(f"Phases ({len(phase_names)}): {phase_names}")

    # Phase ordering (for Cholec80, this is mostly uniform)
    phase_orders = determine_phase_order(annotation_dict, phase_names)
    cluster_assignments = cluster_phase_orders(phase_orders)
    num_clusters = len(set(cluster_assignments.values()))
    print(f"Phase-order clusters: {num_clusters}")

    # ─── Split data (video-level) ───
    # Standard Cholec80 split: first 40 train, next 8 val, last 32 test
    # Or use random split with seed
    train_ids, val_ids, test_ids = create_data_splits(
        all_video_ids, train_ratio=0.5, val_ratio=0.125, seed=args.seed
    )
    print(f"Split: {len(train_ids)} train / {len(val_ids)} val / {len(test_ids)} test")

    # ─── Create datasets ───
    print("Building datasets (this may take a while for frame indexing)...")
    train_transform = get_standard_transforms(args.image_size, is_training=True)
    val_transform = get_standard_transforms(args.image_size, is_training=False)

    train_dataset = SurgicalClipDataset(
        video_root=args.video_root,
        annotation_dict=annotation_dict,
        video_ids=train_ids,
        phase_names=phase_names,
        clip_length=args.clip_length,
        sampling_rate=args.sampling_rate,
        phase_order_clusters=cluster_assignments,
        transform=train_transform,
        remove_out_of_body=False,  # Cholec80 doesn't have OOB annotations
        frame_extension=args.frame_extension,
    )

    val_dataset = SurgicalClipDataset(
        video_root=args.video_root,
        annotation_dict=annotation_dict,
        video_ids=val_ids,
        phase_names=phase_names,
        clip_length=args.clip_length,
        sampling_rate=args.sampling_rate,
        phase_order_clusters=cluster_assignments,
        transform=val_transform,
        remove_out_of_body=False,
        frame_extension=args.frame_extension,
    )

    print(f"Train clips: {len(train_dataset)}, Val clips: {len(val_dataset)}")

    if len(train_dataset) == 0:
        print("\nERROR: No training clips were created!")
        print("Check that:")
        print(f"  1. Frame folders exist under {args.video_root}")
        print(f"  2. Frames have .{args.frame_extension} extension")
        print(f"  3. Annotation files exist in {args.annotation_dir}")
        print(f"  4. Video folder names match annotation file stems")
        return

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=args.num_workers, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers, pin_memory=True,
    )

    # ─── Build model ───
    print("Building model...")
    model = BariatricRSD(
        encoder_name=args.encoder,
        encoder_pretrained=True,
        hta_embed_dim=args.embed_dim,
        hta_num_heads=args.hta_heads,
        hta_depth=args.hta_depth,
        num_phase_orders=max(num_clusters, 1),
        num_phases=len(phase_names),
    )

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Parameters: {total_params:,} total, {trainable_params:,} trainable")

    # ─── Loss ───
    criterion = MultiTaskLoss(
        rsd_weight=args.rsd_weight,
        deviation_weight=args.deviation_weight,
        phase_weight=args.phase_weight,
    )
    print(f"Loss weights: RSD={args.rsd_weight}, Dev={args.deviation_weight}, Phase={args.phase_weight}")

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

    print("\n" + "=" * 60)
    print("STARTING TRAINING")
    print("=" * 60 + "\n")

    history = trainer.train()

    # Save history
    with open(output_dir / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print(f"\nDone! Results saved to {output_dir}")


if __name__ == "__main__":
    main()

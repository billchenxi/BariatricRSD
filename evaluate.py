"""
BariatricRSD Evaluation Script
==============================
Evaluate a trained BariatricRSD model on test data.

Usage:
    python -m bariatric_rsd.evaluate \
        --checkpoint ./experiments/run_001/checkpoints/best_model.pth \
        --video_root /path/to/videos \
        --annotation_json /path/to/annotations.json \
        --output_dir ./experiments/run_001/evaluation

    # Evaluate on Cholec80:
    python -m bariatric_rsd.evaluate \
        --checkpoint ./experiments/run_001/checkpoints/best_model.pth \
        --video_root /path/to/cholec80/frames \
        --annotation_dir /path/to/cholec80/phase_annotations \
        --dataset cholec80 \
        --output_dir ./experiments/run_001/cholec80_eval
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from bariatric_rsd.config import DataConfig
from bariatric_rsd.data.annotation_parser import (
    parse_annotation_json,
    parse_cholec80_annotations,
    determine_phase_order,
    cluster_phase_orders,
)
from bariatric_rsd.data.surgical_dataset import (
    SurgicalClipDataset,
    get_standard_transforms,
)
from bariatric_rsd.models.bariatric_rsd import BariatricRSD
from bariatric_rsd.evaluation.metrics import (
    evaluate_model,
    detect_deviation_segments,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate BariatricRSD model")

    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model checkpoint")
    parser.add_argument("--video_root", type=str, required=True,
                        help="Root directory of video frames")
    parser.add_argument("--annotation_json", type=str, default=None,
                        help="Annotation JSON (for bariatric data)")
    parser.add_argument("--annotation_dir", type=str, default=None,
                        help="Annotation directory (for Cholec80)")
    parser.add_argument("--dataset", type=str, default="bariatric",
                        choices=["bariatric", "cholec80"],
                        help="Dataset type")
    parser.add_argument("--output_dir", type=str, default="./evaluation",
                        help="Output directory for results")

    # Model config (must match training)
    parser.add_argument("--encoder", type=str, default="resnet50")
    parser.add_argument("--embed_dim", type=int, default=512)
    parser.add_argument("--hta_depth", type=int, default=4)
    parser.add_argument("--hta_heads", type=int, default=8)

    # Data
    parser.add_argument("--clip_length", type=int, default=16)
    parser.add_argument("--sampling_rate", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--num_workers", type=int, default=8)
    parser.add_argument("--image_size", type=int, default=224)

    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    data_config = DataConfig()

    # ─── Parse annotations ───
    print("Parsing annotations...")
    if args.dataset == "cholec80":
        annotation_dict = parse_cholec80_annotations(args.annotation_dir)
        phase_names = list(
            set(p for v in annotation_dict.values() for p in v.keys())
        )
        phase_names.sort()
    else:
        annotation_dict = parse_annotation_json(args.annotation_json)
        phase_names = data_config.phase_names

    all_video_ids = list(annotation_dict.keys())
    print(f"Evaluating on {len(all_video_ids)} videos")

    # Phase ordering
    phase_orders = determine_phase_order(annotation_dict, phase_names)
    cluster_assignments = cluster_phase_orders(phase_orders)

    # ─── Create dataset ───
    eval_transform = get_standard_transforms(args.image_size, is_training=False)
    eval_dataset = SurgicalClipDataset(
        video_root=args.video_root,
        annotation_dict=annotation_dict,
        video_ids=all_video_ids,
        phase_names=phase_names,
        clip_length=args.clip_length,
        sampling_rate=args.sampling_rate,
        phase_order_clusters=cluster_assignments,
        transform=eval_transform,
    )

    eval_loader = DataLoader(
        eval_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=True,
    )

    print(f"Evaluation clips: {len(eval_dataset)}")

    # ─── Load model ───
    print("Loading model...")
    model = BariatricRSD(
        encoder_name=args.encoder,
        encoder_pretrained=False,
        hta_embed_dim=args.embed_dim,
        hta_num_heads=args.hta_heads,
        hta_depth=args.hta_depth,
        num_phase_orders=max(cluster_assignments.values()) + 1
        if cluster_assignments
        else 8,
        num_phases=len(phase_names),
    )

    checkpoint = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    print(f"Loaded checkpoint from epoch {checkpoint.get('epoch', '?')}")

    # ─── Evaluate ───
    print("Running evaluation...")
    metrics = evaluate_model(
        model, eval_loader, device=device, phase_names=phase_names
    )

    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    for key, value in sorted(metrics.items()):
        print(f"  {key}: {value:.4f}")
    print("=" * 60)

    # Save results
    results_path = output_dir / "metrics.json"
    with open(results_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()

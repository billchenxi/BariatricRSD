"""
BariatricRSD Real-Time Inference + Operation Log
=================================================
Runs the trained model on a surgical video and generates an automatic
operation log. Can process pre-extracted frames or live video feed.

Usage:
    # On pre-extracted frames
    python -m bariatric_rsd.inference.run_inference \
        --checkpoint ./experiments/best_model.pth \
        --video_root /data/videos/case_042 \
        --output_dir ./reports/case_042 \
        --procedure RYGB \
        --surgeon "Dr. Smith"

    # On a video file (extracts frames on the fly)
    python -m bariatric_rsd.inference.run_inference \
        --checkpoint ./experiments/best_model.pth \
        --video_file /data/videos/case_042.mp4 \
        --output_dir ./reports/case_042
"""

import argparse
import json
import glob
import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from bariatric_rsd.config import DataConfig
from bariatric_rsd.data.surgical_dataset import get_standard_transforms, filename_to_seconds
from bariatric_rsd.models.bariatric_rsd import BariatricRSD
from bariatric_rsd.inference.operation_log import OperationLogger


def parse_args():
    parser = argparse.ArgumentParser(description="Run inference + generate operation log")

    # Input
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--video_root", type=str, default=None,
                        help="Directory with pre-extracted frame images")
    parser.add_argument("--video_file", type=str, default=None,
                        help="Path to video file (will extract frames)")
    parser.add_argument("--frame_extension", type=str, default="jpg")

    # Model config (must match training)
    parser.add_argument("--encoder", type=str, default="resnet50")
    parser.add_argument("--embed_dim", type=int, default=512)
    parser.add_argument("--hta_depth", type=int, default=4)
    parser.add_argument("--hta_heads", type=int, default=8)
    parser.add_argument("--num_phases", type=int, default=3)
    parser.add_argument("--num_phase_orders", type=int, default=8)
    parser.add_argument("--clip_length", type=int, default=16)
    parser.add_argument("--sampling_rate", type=int, default=4)
    parser.add_argument("--image_size", type=int, default=224)

    # Inference
    parser.add_argument("--cluster_id", type=int, default=0,
                        help="Phase-order cluster ID (0 if unknown)")
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--device", type=str, default="cuda")

    # Operation log
    parser.add_argument("--procedure", type=str, default="RYGB")
    parser.add_argument("--surgeon", type=str, default="")
    parser.add_argument("--patient_id", type=str, default="")
    parser.add_argument("--output_dir", type=str, default="./reports")
    parser.add_argument("--deviation_threshold", type=float, default=0.5)

    return parser.parse_args()


def load_model(args, device):
    """Load trained model from checkpoint."""
    model = BariatricRSD(
        encoder_name=args.encoder,
        encoder_pretrained=False,
        hta_embed_dim=args.embed_dim,
        hta_num_heads=args.hta_heads,
        hta_depth=args.hta_depth,
        num_phase_orders=args.num_phase_orders,
        num_phases=args.num_phases,
    )

    ckpt = torch.load(args.checkpoint, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model = model.to(device)
    model.eval()

    phase_names = ckpt.get("phase_names", DataConfig().phase_names)
    print(f"Model loaded from epoch {ckpt.get('epoch', '?')}")
    print(f"Phases: {phase_names}")

    return model, phase_names


def run_inference(args):
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Load model
    model, phase_names = load_model(args, device)
    transform = get_standard_transforms(args.image_size, is_training=False)

    # Get frame files
    frame_dir = args.video_root
    if args.video_file and not args.video_root:
        # Extract frames from video
        frame_dir = Path(args.output_dir) / "frames"
        frame_dir.mkdir(parents=True, exist_ok=True)
        print(f"Extracting frames from {args.video_file}...")
        os.system(
            f"ffmpeg -i {args.video_file} -vf fps=1 -q:v 2 "
            f"{frame_dir}/frame_%06d.jpg -loglevel warning"
        )

    frame_files = sorted(glob.glob(os.path.join(frame_dir, f"*.{args.frame_extension}")))
    print(f"Processing {len(frame_files)} frames")

    if not frame_files:
        print("ERROR: No frames found!")
        return

    # Initialize logger
    logger = OperationLogger(
        phase_names=phase_names,
        procedure_type=args.procedure,
        surgeon_name=args.surgeon,
        patient_id=args.patient_id,
        deviation_threshold=args.deviation_threshold,
        fps=1.0,
    )

    # Process frames in sliding window clips
    window_size = args.clip_length * args.sampling_rate
    all_predictions = []

    print("Running inference...")
    with torch.no_grad():
        for i in tqdm(range(0, len(frame_files) - window_size + 1, args.clip_length)):
            # Sample clip frames
            indices = list(range(i, i + window_size, args.sampling_rate))[:args.clip_length]
            clip_paths = [frame_files[idx] for idx in indices]

            # Load and transform frames
            frames = []
            for fpath in clip_paths:
                img = Image.open(fpath).convert("RGB")
                frames.append(transform(img))
            clip = torch.stack(frames).unsqueeze(0).to(device)  # (1, T, C, H, W)

            cluster = torch.tensor([args.cluster_id], dtype=torch.long, device=device)

            # Forward pass
            outputs = model(clip, cluster)

            # Get predictions from last frame of clip
            rsd = torch.sigmoid(outputs["rsd"][0, -1, 0]).item()
            dev = torch.sigmoid(outputs["deviation"][0, -1, 0]).item()
            phase_logits = outputs["phase"][0, -1]
            phase_idx = phase_logits.argmax().item()
            phase_conf = torch.softmax(phase_logits, dim=0)[phase_idx].item()
            phase_name = phase_names[phase_idx] if phase_idx < len(phase_names) else "Unknown"

            # Timestamp from filename or index
            target_frame = frame_files[indices[-1]]
            try:
                timestamp = filename_to_seconds(target_frame)
            except (ValueError, IndexError):
                timestamp = float(indices[-1])  # fallback to frame index

            # Update logger
            logger.update(
                timestamp_sec=timestamp,
                phase_pred=phase_name,
                rsd_pred=rsd,
                deviation_score=dev,
                phase_confidence=phase_conf,
            )

            all_predictions.append({
                "timestamp": timestamp,
                "frame": os.path.basename(target_frame),
                "rsd": round(rsd, 4),
                "deviation": round(dev, 4),
                "phase": phase_name,
                "phase_confidence": round(phase_conf, 4),
            })

    # Save outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save raw predictions
    pred_path = output_dir / "predictions.json"
    with open(pred_path, "w") as f:
        json.dump({"predictions": all_predictions}, f, indent=2)
    print(f"Predictions saved: {pred_path}")

    # Generate and save operation log
    logger.save_report(str(output_dir), formats=["txt", "json"])

    # Print report to console
    print("\n" + logger.generate_report())


if __name__ == "__main__":
    args = parse_args()
    run_inference(args)

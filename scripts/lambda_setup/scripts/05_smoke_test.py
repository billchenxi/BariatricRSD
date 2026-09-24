#!/usr/bin/env python3
"""
scripts/05_smoke_test.py

Verifies the full pipeline works on synthetic data before touching your real videos.
Runs in ~60 seconds. Should print PASSED at the end.

Run with:  python scripts/05_smoke_test.py
"""

import sys
import time
import json
import tempfile
from pathlib import Path

import torch
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def make_fake_dataset(tmpdir: str, n_videos: int = 3, frames_per_video: int = 30, img_size: int = 224):
    """Create a tiny synthetic dataset with random images for testing."""
    tmpdir = Path(tmpdir)
    frames_dir = tmpdir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    phases = ["Gastric pouch creation", "Gastro-jejunal anastomosis", "Jejuno-jejunal anastomosis"]
    phase_vocab = {p: i for i, p in enumerate(phases)}

    videos = []
    for v in range(n_videos):
        vid_id = f"smoke_video_{v:04d}"
        vid_dir = frames_dir / vid_id
        vid_dir.mkdir(exist_ok=True)

        total_duration = 3600.0  # 1 hour
        frame_data = []
        for fi in range(frames_per_video):
            # Create a random RGB image
            img_arr = np.random.randint(0, 255, (img_size, img_size, 3), dtype=np.uint8)
            img = Image.fromarray(img_arr)
            frame_path = vid_dir / f"frame_{fi:06d}.jpg"
            img.save(frame_path)

            timestamp = fi * (total_duration / frames_per_video)
            rsd_sec = total_duration - timestamp
            phase = phases[fi % len(phases)]
            is_dev = (fi % 10 == 0)  # 10% deviation rate

            frame_data.append({
                "frame_idx": fi,
                "timestamp_sec": timestamp,
                "rsd_sec": rsd_sec,
                "rsd_normalized": rsd_sec / total_duration,
                "phase": phase,
                "is_deviation": is_dev,
                "frame_path": f"frames/{vid_id}/frame_{fi:06d}.jpg",
            })

        split = ["train", "train", "val"][v % 3]
        videos.append({
            "video_id": vid_id,
            "total_duration_sec": total_duration,
            "phase_sequence": phases,
            "phase_vocab": phase_vocab,
            "phase_order_cluster": 0,
            "split": split,
            "frames": frame_data,
        })

    label_path = tmpdir / "labels.json"
    with open(label_path, "w") as f:
        json.dump(videos, f)

    return str(label_path), str(tmpdir)


def test_dataset(label_json, data_root):
    print("\n[1/5] Testing Dataset...")
    from data.dataset import BariatricFrameDataset, get_dataloader

    ds_train = BariatricFrameDataset(label_json, data_root, split="train",
                                      sequence_len=4, frame_stride=2, img_size=64)
    ds_val = BariatricFrameDataset(label_json, data_root, split="val",
                                    sequence_len=4, frame_stride=2, img_size=64)

    assert len(ds_train) > 0, "Train dataset is empty"
    assert len(ds_val) > 0, "Val dataset is empty"

    sample = ds_train[0]
    assert "frames" in sample and sample["frames"].shape[0] == 4
    assert "rsd_normalized" in sample
    assert "is_deviation" in sample
    assert "phase_order_cluster" in sample
    assert 0.0 <= sample["rsd_normalized"].item() <= 1.0

    loader = get_dataloader(ds_train, split="train", batch_size=2, num_workers=0)
    batch = next(iter(loader))
    assert batch["frames"].shape == (2, 4, 3, 64, 64), f"Wrong frame shape: {batch['frames'].shape}"
    print(f"   Dataset OK: {len(ds_train)} train samples, {len(ds_val)} val samples")
    return loader


def test_model(batch):
    print("\n[2/5] Testing Model (CPU forward pass)...")
    from models.bariatric_rsd import BariatricRSD, BariatricRSDLoss

    model = BariatricRSD(
        encoder_checkpoint=None,
        encoder_freeze_layers=0,
        embed_dim=192,       # tiny for smoke test
        temporal_layers=2,
        temporal_heads=3,
        num_phases=3,
    )
    model.eval()

    frames = batch["frames"]    # [2, 4, 3, 64, 64]
    cluster = batch["phase_order_cluster"]  # [2]

    with torch.no_grad():
        preds = model(frames, cluster)

    assert "rsd" in preds and preds["rsd"].shape == (2,)
    assert "deviation" in preds and preds["deviation"].shape == (2,)
    assert "phase" in preds and preds["phase"].shape == (2, 3)
    assert 0.0 <= preds["rsd"].min().item() <= 1.0
    print(f"   Model OK: rsd={preds['rsd'].tolist()}, dev={torch.sigmoid(preds['deviation']).tolist()}")
    return model, preds


def test_loss(preds, batch):
    print("\n[3/5] Testing Loss Function...")
    from models.bariatric_rsd import BariatricRSDLoss

    loss_fn = BariatricRSDLoss(learn_weights=True)
    targets = {
        "rsd_normalized": batch["rsd_normalized"],
        "is_deviation": batch["is_deviation"],
        "phase_label": batch["phase_label"],
    }
    losses = loss_fn(preds, targets)
    assert "loss" in losses and not torch.isnan(losses["loss"]), "Loss is NaN!"
    assert losses["loss"].item() > 0
    print(f"   Loss OK: total={losses['loss'].item():.4f}, "
          f"rsd={losses['loss_rsd'].item():.4f}, "
          f"dev={losses['loss_deviation'].item():.4f}")
    return loss_fn


def test_backward(model, loss_fn, batch):
    print("\n[4/5] Testing backward pass + gradient flow...")
    from models.bariatric_rsd import BariatricRSDLoss

    model.train()
    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(loss_fn.parameters()), lr=1e-4
    )

    frames = batch["frames"]
    cluster = batch["phase_order_cluster"]
    targets = {
        "rsd_normalized": batch["rsd_normalized"],
        "is_deviation": batch["is_deviation"],
        "phase_label": batch["phase_label"],
    }

    preds = model(frames, cluster)
    losses = loss_fn(preds, targets)
    losses["loss"].backward()

    # Check gradients exist
    grad_norms = []
    for name, p in model.named_parameters():
        if p.grad is not None:
            grad_norms.append(p.grad.norm().item())

    assert len(grad_norms) > 0, "No gradients computed"
    assert not any(np.isnan(g) for g in grad_norms), "NaN gradients detected"

    optimizer.step()
    print(f"   Backward OK: {len(grad_norms)} param groups with gradients, "
          f"max_grad_norm={max(grad_norms):.4f}")


def test_gpu(model, loader):
    if not torch.cuda.is_available():
        print("\n[5/5] GPU test SKIPPED (no CUDA available on this machine)")
        return

    print("\n[5/5] Testing GPU forward pass...")
    device = torch.device("cuda:0")
    model = model.to(device)
    model.eval()

    batch = next(iter(loader))
    frames = batch["frames"].to(device)
    cluster = batch["phase_order_cluster"].to(device)

    t0 = time.time()
    with torch.no_grad():
        with torch.cuda.amp.autocast():
            preds = model(frames, cluster)
    torch.cuda.synchronize()
    elapsed = time.time() - t0

    print(f"   GPU OK: {torch.cuda.get_device_name(0)} | "
          f"forward pass = {elapsed*1000:.1f}ms | "
          f"VRAM used = {torch.cuda.memory_allocated()/1e9:.2f}GB")


def main():
    print("=" * 60)
    print("BariatricRSD Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nCreating synthetic dataset in {tmpdir}...")
        label_json, data_root = make_fake_dataset(tmpdir, n_videos=3, frames_per_video=40, img_size=64)
        print(f"Synthetic dataset created")

        loader = test_dataset(label_json, data_root)
        batch = next(iter(loader))

        model, preds = test_model(batch)
        loss_fn = test_loss(preds, batch)
        test_backward(model, loss_fn, batch)
        test_gpu(model, loader)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Update .env with your actual data paths")
    print("  2. Run: python src/data/prepare_labels.py  (to create labels.json from your videos)")
    print("  3. Run: python src/training/train.py --label_json ... --data_root ...")


if __name__ == "__main__":
    main()

"""
brsd_lib.compute_residuals
==========================

Dump per-frame (prediction, target) pairs from a trained checkpoint on a given
split. Output is a CSV with columns ``video_id, frame_path, prediction, target,
abs_residual`` suitable for ``brsd_lib.overfit_filter``.

Typical use: compute residuals on the *training* split so the overfit-filter
can flag noisy frames for removal before retraining.

This module is in the "data-selection" track of the paper. It is independent
of the causal-workflow-posterior effort (CW-BariatricRSD); the two can be
combined but do not depend on each other.

Written fresh for the NeurIPS 2026 submission.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch


# ---------------------------------------------------------------------------
# Project import helper (same pattern as brsd_lib.evaluate / brsd_lib.ensemble)
# ---------------------------------------------------------------------------

def _import_project(project_src: str):
    """
    Load BariatricRSD and BariatricFrameDataset by *file path*, bypassing any
    conflicting ``data`` package in the import search path. There is a vendor
    ``data/`` package at the repo root that shadows ``src/data/`` when cwd is
    the repo root; we dodge it by explicit importlib loading.
    """
    import importlib.util
    src_dir = Path(project_src)

    def _load(modname: str, rel_path: str):
        spec = importlib.util.spec_from_file_location(modname, str(src_dir / rel_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load {modname} from {src_dir / rel_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)
        return module

    models_mod = _load("brsd_src_models_bariatric_rsd", "models/bariatric_rsd.py")
    dataset_mod = _load("brsd_src_data_dataset", "data/dataset.py")
    BariatricRSD = getattr(models_mod, "BariatricRSD")
    BariatricFrameDataset = getattr(dataset_mod, "BariatricFrameDataset")
    from torch.utils.data import DataLoader                    # type: ignore
    return BariatricRSD, BariatricFrameDataset, DataLoader


def _load_checkpoint(model: torch.nn.Module, ckpt_path: str, device: torch.device) -> None:
    state = torch.load(ckpt_path, map_location=device, weights_only=False)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    model.load_state_dict(state)
    model.eval()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@torch.no_grad()
def dump_residuals(
    checkpoint_path: str,
    label_json: str,
    data_root: str,
    output_csv: str,
    split: str = "train",
    sequence_len: int = 8,
    frame_stride: int = 5,
    img_size: int = 224,
    batch_size: int = 64,
    num_workers: int = 16,
    num_phases: int = 14,
    target_position: str = "middle",
    decouple_phase_head: bool = False,
    no_phase_order: bool = False,
    project_src: str = "/lambda/nfs/bariatric-rsd/src",
    device: str = "cuda",
) -> pd.DataFrame:
    """
    Run the model on `split` and dump per-clip (video_id, frame_path, pred, target)
    to a CSV. The frame_path recorded is that of the clip's middle frame, which
    matches `BariatricFrameDataset.__getitem__`'s label convention.
    """
    BariatricRSD, BariatricFrameDataset, DataLoader = _import_project(project_src)
    dev = torch.device(device if torch.cuda.is_available() else "cpu")

    ds = BariatricFrameDataset(
        label_json, data_root, split=split,
        sequence_len=sequence_len, frame_stride=frame_stride,
        img_size=img_size, augment=False,
        target_position=target_position,
    )

    loader = DataLoader(ds, batch_size=batch_size, shuffle=False,
                        num_workers=num_workers, pin_memory=True)

    model = BariatricRSD(
        encoder_checkpoint=None,
        encoder_freeze_layers=6,
        embed_dim=768,
        temporal_layers=6,
        num_phases=num_phases,
        decouple_phase_head=decouple_phase_head,
    ).to(dev)
    _load_checkpoint(model, checkpoint_path, dev)

    rows: List[Dict] = []
    sample_cursor = 0
    for batch in loader:
        frames = batch["frames"].to(dev, non_blocking=True)
        cluster = batch["phase_order_cluster"].to(dev, non_blocking=True)
        if no_phase_order:
            cluster = torch.zeros_like(cluster)
        vids = list(batch["video_id"])
        targets = batch["rsd_normalized"].float().cpu().numpy()
        frame_paths = list(batch.get("target_frame_path", []))

        preds = model(frames, cluster)["rsd"].detach().float().cpu().numpy()
        for i, (vid, p, t) in enumerate(zip(vids, preds, targets)):
            if frame_paths:
                fpath = frame_paths[i]
            else:
                fpath = f"sample_{sample_cursor + i}"
            rows.append({
                "video_id": str(vid),
                "frame_path": str(fpath),
                "prediction": float(p),
                "target": float(t),
                "abs_residual": float(abs(p - t)),
            })
        sample_cursor += len(vids)

    df = pd.DataFrame(rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def _cli():
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.compute_residuals",
        description="Dump per-frame residuals from a trained checkpoint on a given split.",
    )
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--label_json", required=True)
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--output_csv", required=True)
    ap.add_argument("--num_phases", type=int, default=14,
                    help="Match the trained model — MB140=14, Cholec80=7")
    ap.add_argument("--sequence_len", type=int, default=8)
    ap.add_argument("--frame_stride", type=int, default=5)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--num_workers", type=int, default=16)
    ap.add_argument("--target_position", default="middle", choices=["middle", "last"])
    ap.add_argument("--decouple_phase_head", action="store_true")
    ap.add_argument("--no_phase_order", action="store_true")
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    args = ap.parse_args()

    df = dump_residuals(
        checkpoint_path=args.checkpoint,
        label_json=args.label_json,
        data_root=args.data_root,
        output_csv=args.output_csv,
        split=args.split,
        sequence_len=args.sequence_len,
        frame_stride=args.frame_stride,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        num_phases=args.num_phases,
        target_position=args.target_position,
        decouple_phase_head=args.decouple_phase_head,
        no_phase_order=args.no_phase_order,
        project_src=args.project_src,
    )
    print(f"\nWrote {len(df):,} rows to {args.output_csv}")
    print(f"Per-video summary:")
    grouped = df.groupby("video_id")["abs_residual"].agg(["count", "mean", "std"])
    print(grouped.describe().to_string())


if __name__ == "__main__":
    _cli()

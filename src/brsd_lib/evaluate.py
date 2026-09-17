"""
brsd_lib.evaluate
=================

Standalone test-set evaluation for a trained BariatricRSD checkpoint.

Loads a best_model.pth, runs frame-level inference over a given split
('test' by default), converts normalized RSD back to minutes using each
video's total duration, and reports per-video MAE + global summary.

Written fresh for the NeurIPS 2026 submission.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Tuple

import numpy as np
import torch


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _import_project(project_src: str):
    """Load BariatricRSD + BariatricFrameDataset by explicit file path.

    Bypasses any conflicting ``data/`` package elsewhere on sys.path. There
    is a vendor ``data/`` package at the repo root that shadows ``src/data/``
    when cwd is the repo root, so we dodge it via importlib.util loading.
    Same pattern as ``brsd_lib.compute_residuals._import_project``.
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


# ---------------------------------------------------------------------------
# Per-video aggregation
# ---------------------------------------------------------------------------

def per_video_mae_minutes(
    pred_norm: Dict[str, List[float]],
    true_norm: Dict[str, List[float]],
    durations_sec: Dict[str, float],
) -> Dict[str, float]:
    """
    Convert normalized RSD preds/targets back to minutes using each video's
    total duration, then compute per-video MAE in minutes.

    Parameters
    ----------
    pred_norm, true_norm : dict[video_id -> list[float]]
        Predictions and ground truth in [0, 1].
    durations_sec : dict[video_id -> float]
        Total surgery duration (seconds) per video.

    Returns
    -------
    dict[video_id -> MAE in minutes]
    """
    out: Dict[str, float] = {}
    for vid, preds in pred_norm.items():
        truths = true_norm[vid]
        total_sec = durations_sec[vid]
        preds_arr = np.asarray(preds, dtype=np.float64)
        truths_arr = np.asarray(truths, dtype=np.float64)
        errors_sec = np.abs(preds_arr - truths_arr) * total_sec
        out[vid] = float(np.mean(errors_sec) / 60.0)
    return out


def summarize_mae(per_video: Dict[str, float]) -> Dict[str, float]:
    """Aggregate a per-video MAE dict into a summary."""
    vals = list(per_video.values())
    if not vals:
        return {"n_videos": 0, "mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    return {
        "n_videos": len(vals),
        "mean":     float(mean(vals)),
        "median":   float(median(vals)),
        "std":      float(stdev(vals)) if len(vals) >= 2 else 0.0,
        "min":      float(min(vals)),
        "max":      float(max(vals)),
    }


# ---------------------------------------------------------------------------
# Main eval loop
# ---------------------------------------------------------------------------

def run_test_eval(
    checkpoint_path: str,
    label_json: str,
    data_root: str,
    split: str = "test",
    sequence_len: int = 8,
    frame_stride: int = 5,
    img_size: int = 224,
    batch_size: int = 64,
    num_workers: int = 16,
    num_phases: int = 7,
    no_phase_order: bool = False,
    target_position: str = "middle",
    decouple_phase_head: bool = False,
    project_src: str = "/lambda/nfs/bariatric-rsd/src",
    device: str = "cuda",
) -> Dict:
    """
    Load a checkpoint, run inference on `split`, return a summary dict.
    """
    BariatricRSD, BariatricFrameDataset, DataLoader = _import_project(project_src)

    dev = torch.device(device if torch.cuda.is_available() else "cpu")

    # Load dataset for the requested split
    ds = BariatricFrameDataset(
        label_json, data_root, split=split,
        sequence_len=sequence_len, frame_stride=frame_stride,
        img_size=img_size, augment=False,
        target_position=target_position,
    )
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False,
                        num_workers=num_workers, pin_memory=True)

    # Load labels.json for durations
    with open(label_json) as f:
        videos = json.load(f)
    durations_sec = {v["video_id"]: float(v["total_duration_sec"]) for v in videos}

    # Rebuild the model architecture that was trained (matches train.py defaults
    # plus the num_phases override we actually used).
    model = BariatricRSD(
        encoder_checkpoint=None,
        encoder_freeze_layers=6,
        embed_dim=768,
        temporal_layers=6,
        num_phases=num_phases,
        decouple_phase_head=decouple_phase_head,
    ).to(dev)
    state = torch.load(checkpoint_path, map_location=dev)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    model.load_state_dict(state)
    model.eval()

    pred_by_vid: Dict[str, List[float]] = {}
    true_by_vid: Dict[str, List[float]] = {}

    with torch.no_grad():
        for batch in loader:
            frames = batch["frames"].to(dev, non_blocking=True)
            cluster = batch["phase_order_cluster"].to(dev, non_blocking=True)
            if no_phase_order:
                cluster = torch.zeros_like(cluster)
            preds = model(frames, cluster)
            rsd_pred = preds["rsd"].detach().float().cpu().numpy()
            rsd_true = batch["rsd_normalized"].float().cpu().numpy()
            vids = batch["video_id"]
            for v, p, t in zip(vids, rsd_pred, rsd_true):
                pred_by_vid.setdefault(v, []).append(float(p))
                true_by_vid.setdefault(v, []).append(float(t))

    per_vid = per_video_mae_minutes(pred_by_vid, true_by_vid, durations_sec)
    summary = summarize_mae(per_vid)
    summary["per_video"] = per_vid
    summary["checkpoint"] = str(checkpoint_path)
    summary["split"] = split
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli():
    ap = argparse.ArgumentParser(
        prog="python -m brsd_lib.evaluate",
        description="Test-set evaluation for a BariatricRSD checkpoint.",
    )
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--label_json", required=True)
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--sequence_len", type=int, default=8)
    ap.add_argument("--frame_stride", type=int, default=5)
    ap.add_argument("--img_size", type=int, default=224)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--num_workers", type=int, default=16)
    ap.add_argument("--num_phases", type=int, default=7)
    ap.add_argument("--no_phase_order", action="store_true")
    ap.add_argument("--target_position", default="middle", choices=["middle", "last"])
    ap.add_argument("--decouple_phase_head", action="store_true")
    ap.add_argument("--project_src", default="/lambda/nfs/bariatric-rsd/src")
    ap.add_argument("--out_json", default=None,
                    help="Optional path to write the full summary JSON.")
    ap.add_argument("--output_json", default=None,
                    help="Backward-compatible alias for --out_json.")
    args = ap.parse_args()
    out_json = args.out_json or args.output_json

    summary = run_test_eval(
        checkpoint_path=args.checkpoint,
        label_json=args.label_json,
        data_root=args.data_root,
        split=args.split,
        sequence_len=args.sequence_len,
        frame_stride=args.frame_stride,
        img_size=args.img_size,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        num_phases=args.num_phases,
        no_phase_order=args.no_phase_order,
        target_position=args.target_position,
        decouple_phase_head=args.decouple_phase_head,
        project_src=args.project_src,
    )

    print(f"\n=== Test-set results: {summary['checkpoint']} ===")
    print(f"Split: {summary['split']} ({summary['n_videos']} videos)")
    print(f"Mean per-video MAE:   {summary['mean']:.3f} min")
    print(f"Median per-video MAE: {summary['median']:.3f} min")
    print(f"Std across videos:    {summary['std']:.3f} min")
    print(f"Min / Max:            {summary['min']:.3f} / {summary['max']:.3f} min")

    if out_json:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nWrote full summary → {out_json}")


if __name__ == "__main__":
    _cli()

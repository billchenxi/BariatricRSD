#!/usr/bin/env python3
"""
Apply the strict-protocol flags required by Run 033/034 onto the active Lambda
training stack in `/lambda/nfs/bariatric-rsd/src`.

This script is intentionally idempotent. It patches three files in place:

1. `src/data/dataset.py`
   - adds `target_position={"middle","last"}`
2. `src/models/bariatric_rsd.py`
   - adds `decouple_phase_head`
3. `src/training/train.py`
   - adds `--seed`, `--target_position`, `--decouple_phase_head`,
     and `--no_phase_order`

The repository also carries the same functionality in `lambda_setup/src/*`.
This helper exists because the queued Lambda scripts invoke `python3
scripts/11_apply_protocol_patches.py` from the remote checkout.
"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path("/lambda/nfs/bariatric-rsd/src")
DATASET_PY = ROOT / "data/dataset.py"
MODEL_PY = ROOT / "models/bariatric_rsd.py"
TRAIN_PY = ROOT / "training/train.py"


def patch_dataset() -> None:
    src = DATASET_PY.read_text()

    if "target_position" not in src:
        src = src.replace(
            "        augment: bool = True,\n        max_videos: Optional[int] = None,\n    ):",
            (
                "        augment: bool = True,\n"
                "        max_videos: Optional[int] = None,\n"
                "        target_position: str = \"middle\",\n"
                "    ):"
            ),
            1,
        )
        src = src.replace(
            "        self.augment = augment and split == \"train\"\n",
            (
                "        self.augment = augment and split == \"train\"\n"
                "        if target_position not in {\"middle\", \"last\"}:\n"
                "            raise ValueError(\n"
                "                f\"target_position must be 'middle' or 'last', got {target_position!r}\"\n"
                "            )\n"
                "        self.target_position = target_position\n"
            ),
            1,
        )
        src = src.replace(
            "        # Labels from the MIDDLE frame of the sequence\n        mid = frame_indices[len(frame_indices) // 2]\n        mid_meta = frames_meta[mid]",
            (
                "        # Labels from the configured target frame of the sequence.\n"
                "        if self.target_position == \"last\":\n"
                "            mid = frame_indices[-1]\n"
                "        else:\n"
                "            mid = frame_indices[len(frame_indices) // 2]\n"
                "        mid_meta = frames_meta[mid]"
            ),
            1,
        )
        src = src.replace(
            '            "timestamp_sec": torch.tensor(mid_meta["timestamp_sec"], dtype=torch.float32),\n',
            (
                '            "timestamp_sec": torch.tensor(mid_meta["timestamp_sec"], dtype=torch.float32),\n'
                '            "target_frame_idx": torch.tensor(mid_meta["frame_idx"], dtype=torch.long),\n'
                '            "target_frame_path": mid_meta["frame_path"],\n'
            ),
            1,
        )
        DATASET_PY.write_text(src)
        print("[dataset] patched")
    else:
        print("[dataset] already patched")


def patch_model() -> None:
    src = MODEL_PY.read_text()

    if "decouple_phase_head" not in src:
        src = src.replace(
            "        num_phases: int = 12,\n        num_phase_order_clusters: int = NUM_PHASE_ORDER_CLUSTERS,\n    ):",
            (
                "        num_phases: int = 12,\n"
                "        num_phase_order_clusters: int = NUM_PHASE_ORDER_CLUSTERS,\n"
                "        decouple_phase_head: bool = False,\n"
                "    ):"
            ),
            1,
        )
        src = src.replace(
            "        self.encoder = VisualEncoder(\n",
            "        self.decouple_phase_head = decouple_phase_head\n        self.encoder = VisualEncoder(\n",
            1,
        )
        src = src.replace(
            "        # 5. Task heads\n        return {\n            \"rsd\": self.rsd_head(global_feat),             # [B]\n            \"deviation\": self.deviation_head(global_feat), # [B]  (logits)\n            \"phase\": self.phase_head(global_feat),          # [B, num_phases]\n        }",
            (
                "        # 5. Task heads. In the decoupled variant, the phase head reads visual\n"
                "        # features before workflow-token mixing so the causal evaluator is not\n"
                "        # circular with respect to the supplied cluster token.\n"
                "        if self.decouple_phase_head:\n"
                "            phase_feat = frame_feats.mean(dim=1)\n"
                "        else:\n"
                "            phase_feat = global_feat\n"
                "        return {\n"
                "            \"rsd\": self.rsd_head(global_feat),             # [B]\n"
                "            \"deviation\": self.deviation_head(global_feat), # [B]  (logits)\n"
                "            \"phase\": self.phase_head(phase_feat),          # [B, num_phases]\n"
                "        }"
            ),
            1,
        )
        MODEL_PY.write_text(src)
        print("[model] patched")
    else:
        print("[model] already patched")


def patch_train() -> None:
    src = TRAIN_PY.read_text()

    if "import random" not in src:
        src = src.replace("import json\n", "import json\nimport random\n", 1)

    if "def set_seed(" not in src:
        src = src.replace(
            '    rec = recall_score(dev_true, dev_pred, zero_division=0)\n    return {"deviation_f1": float(f1), "deviation_precision": float(prec), "deviation_recall": float(rec)}\n',
            (
                '    rec = recall_score(dev_true, dev_pred, zero_division=0)\n'
                '    return {"deviation_f1": float(f1), "deviation_precision": float(prec), "deviation_recall": float(rec)}\n\n\n'
                'def set_seed(seed: int) -> None:\n'
                '    random.seed(seed)\n'
                '    np.random.seed(seed)\n'
                '    torch.manual_seed(seed)\n'
                '    if torch.cuda.is_available():\n'
                '        torch.cuda.manual_seed_all(seed)\n'
            ),
            1,
        )

    if "no_phase_order: bool = False" not in src:
        src = src.replace(
            "def train_one_epoch(model, loader, optimizer, loss_fn, device, epoch, scaler, log_interval=50):",
            (
                "def train_one_epoch(\n"
                "    model, loader, optimizer, loss_fn, device, epoch, scaler, log_interval=50,\n"
                "    no_phase_order: bool = False,\n"
                "):"
            ),
            1,
        )
        src = src.replace(
            '        frames = batch["frames"].to(device, non_blocking=True)\n        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)\n',
            (
                '        frames = batch["frames"].to(device, non_blocking=True)\n'
                '        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)\n'
                '        if no_phase_order:\n'
                '            cluster = torch.zeros_like(cluster)\n'
            ),
            1,
        )
        src = src.replace(
            "@torch.no_grad()\ndef evaluate(model, loader, loss_fn, device):",
            "@torch.no_grad()\ndef evaluate(model, loader, loss_fn, device, no_phase_order: bool = False):",
            1,
        )
        src = src.replace(
            '        frames = batch["frames"].to(device, non_blocking=True)\n        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)\n',
            (
                '        frames = batch["frames"].to(device, non_blocking=True)\n'
                '        cluster = batch["phase_order_cluster"].to(device, non_blocking=True)\n'
                '        if no_phase_order:\n'
                '            cluster = torch.zeros_like(cluster)\n'
            ),
            1,
        )

    if "--no_phase_order" not in src:
        src = src.replace(
            '    parser.add_argument("--resume", type=str, default=None)\n',
            (
                '    parser.add_argument("--resume", type=str, default=None)\n'
                '    parser.add_argument("--seed", type=int, default=42,\n'
                '                        help="Random seed for python/numpy/torch")\n'
                '    parser.add_argument("--target_position", type=str, default="middle",\n'
                '                        choices=["middle", "last"],\n'
                '                        help="Label frame inside each clip. middle preserves the legacy centered-window protocol; "\n'
                '                             "last makes the clip end at the prediction timestamp.")\n'
                '    parser.add_argument("--decouple_phase_head", action="store_true",\n'
                '                        help="Predict phase from visual features before workflow-token mixing.")\n'
                '    parser.add_argument("--no_phase_order", action="store_true",\n'
                '                        help="Replace every workflow cluster ID with 0 as a constant-token ablation.")\n'
            ),
            1,
        )
        src = src.replace(
            "    else:\n        device = torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\")\n",
            (
                "    else:\n"
                "        device = torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\")\n\n"
                "    set_seed(args.seed)\n"
            ),
            1,
        )
        src = re.sub(
            r"(BariatricFrameDataset\(\s*args\.label_json, args\.data_root, split=\"(?:train|val)\",\s*sequence_len=args\.sequence_len, frame_stride=args\.frame_stride,\s*img_size=args\.img_size, augment=)(True|False)(,\s*)\)",
            lambda m: m.group(1) + m.group(2) + ", target_position=args.target_position" + m.group(3) + ")",
            src,
        )
        src = src.replace(
            "        temporal_layers=args.temporal_layers,\n        num_phases=args.num_phases,\n    ).to(device)",
            (
                "        temporal_layers=args.temporal_layers,\n"
                "        num_phases=args.num_phases,\n"
                "        decouple_phase_head=args.decouple_phase_head,\n"
                "    ).to(device)"
            ),
            1,
        )
        src = src.replace(
            "        train_metrics = train_one_epoch(\n            model, train_loader, optimizer, loss_fn, device, epoch, scaler\n        )\n        val_metrics = evaluate(model, val_loader, loss_fn, device)\n",
            (
                "        train_metrics = train_one_epoch(\n"
                "            model, train_loader, optimizer, loss_fn, device, epoch, scaler,\n"
                "            no_phase_order=args.no_phase_order,\n"
                "        )\n"
                "        val_metrics = evaluate(\n"
                "            model, val_loader, loss_fn, device,\n"
                "            no_phase_order=args.no_phase_order,\n"
                "        )\n"
            ),
            1,
        )
        TRAIN_PY.write_text(src)
        print("[train] patched")
    else:
        print("[train] already patched")


if __name__ == "__main__":
    patch_dataset()
    patch_model()
    patch_train()
    print("\nDone.")

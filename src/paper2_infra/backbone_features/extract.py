"""Frozen-backbone feature extraction for Paper 2A.

Reads clips from a dataset, runs them through one of N candidate
backbones, and caches per-clip feature tensors to disk. The downstream
temporal head then trains on the cached features — no re-extraction
per training step.

Design principles:
- One backbone registry entry per candidate model (see BACKBONES dict).
- Every backbone exposes the same interface: `load(device) -> encoder`,
  and `encoder(clips: Tensor[B,T,3,H,W]) -> Tensor[B,T,D]` where D is
  the model's feature dim. Pooling / projection to the fixed downstream
  shape (8, 768) happens in a separate stage.
- Cache format: numpy .npy per (video_id, clip_end_frame), grouped in
  Zarr or one directory per (backbone, dataset).
- Idempotent: skip-if-cached; safe to Ctrl-C and resume.

**Image vs video backbones.** The anchor (ViT-B/16) is an *image* model
that consumes (B, 3, H, W); the candidates (VideoMAE, TimeSformer,
V-JEPA) are *video* models that consume a whole clip at once. Rather
than special-casing every call site, each loader returns a module
wrapped to the single (B, T, 3, H, W) -> (B, T, D) contract above. See
`ClipwiseImageEncoder`. An earlier version of this file documented that
contract but fed image models a 5-D tensor directly, which failed with
`ValueError: too many values to unpack (expected 4)` the first time the
anchor was actually run.

**Weights are pinned by tag.** `BackboneSpec.pretrained_tag` records the
exact weight revision. This matters more than it looks: `timm.create_model
("vit_base_patch16_224", pretrained=True)` resolves to timm's *default*
tag, which is currently `augreg2_in21k_ft_in1k` — ImageNet-21k pretrained
**and then ImageNet-1k finetuned** — not the plain `orig_in21k` weights
that a backbone named `vit_b16_in21k` implies. The default tag can also
change between timm releases, which would silently change the anchor
under a reproduction attempt. Every row now names its tag explicitly.

Phase 0 status: anchor implemented and smoke-tested on CPU. Video-model
loaders are implemented but not yet smoke-tested (they need the GPU box
and, for gated rows, an HF token) — see papers/paper2_forecasting/
phase_0/backbone_feasibility_matrix.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

logger = logging.getLogger("backbone_features")

# Paper 1 trained its ViT with timm's default tag for this architecture.
# Pinned here so Paper 2A's anchor cannot drift when timm changes defaults.
PAPER1_VIT_TAG = "augreg2_in21k_ft_in1k"


# ── Backbone registry ────────────────────────────────────────────────────────

@dataclass
class BackboneSpec:
    """Metadata for one candidate backbone.

    - name: registry key (e.g. "vit_b16_in21k").
    - hf_id: HuggingFace repo ID or None if not on HF.
    - params_millions: total parameter count (M).
    - clip_frames: expected clip length in frames.
    - input_hw: (H, W) input resolution.
    - feature_dim: per-frame or per-clip feature dim (varies by model).
    - license: SPDX or human-readable license label.
    - stage_0_status: "pass" | "fail" | "pending" | "skipped".
    - pretrained_tag: exact weight revision/tag; None when the row's
      weight source is still unresolved.
    - loader: callable that returns a torch.nn.Module encoder honouring
      the (B, T, 3, H, W) -> (B, T, D) contract.
    """
    name: str
    hf_id: Optional[str]
    params_millions: float
    clip_frames: int
    input_hw: Tuple[int, int]
    feature_dim: int
    license: str
    stage_0_status: str
    loader: Callable[..., "torch.nn.Module"]
    pretrained_tag: Optional[str] = None


# ── Shape adapters ──────────────────────────────────────────────────────────

def _clipwise_image_encoder(module):
    """Wrap an image model so it honours the (B, T, 3, H, W) contract.

    Folds the time axis into the batch, runs the image model once, and
    unfolds. Equivalent to looping over frames but keeps the GPU busy.
    """
    import torch

    class ClipwiseImageEncoder(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, clips):
            if clips.dim() != 5:
                raise ValueError(
                    f"expected (B, T, 3, H, W), got {tuple(clips.shape)}")
            b, t = clips.shape[:2]
            flat = clips.reshape(b * t, *clips.shape[2:])
            feats = self.inner(flat)
            if feats.dim() != 2:
                raise ValueError(
                    f"image backbone returned {tuple(feats.shape)}; expected "
                    f"(B*T, D). Ensure num_classes=0 so the head is dropped.")
            return feats.reshape(b, t, feats.shape[-1])

    return ClipwiseImageEncoder(module)


def _video_encoder(module, n_out_frames: int):
    """Wrap a HuggingFace video model to the (B, T, 3, H, W) contract.

    Video transformers return a token sequence of shape (B, N, D) where N
    is patches x temporal positions rather than frames. We reshape to
    (B, t_out, patches, D) and mean-pool the spatial patches, giving one
    vector per temporal position. `n_out_frames` is the model's temporal
    output resolution, which is not always the input frame count —
    VideoMAE halves it via its tubelet embedding.
    """
    import torch

    class VideoEncoder(torch.nn.Module):
        def __init__(self, inner, t_out):
            super().__init__()
            self.inner = inner
            self.t_out = t_out

        def forward(self, clips):
            if clips.dim() != 5:
                raise ValueError(
                    f"expected (B, T, 3, H, W), got {tuple(clips.shape)}")
            out = self.inner(pixel_values=clips).last_hidden_state  # (B, N, D)
            b, n, d = out.shape
            if n % self.t_out != 0:
                raise ValueError(
                    f"token count {n} is not divisible by the expected "
                    f"temporal resolution {self.t_out}; check the model's "
                    f"tubelet/patch configuration before trusting features.")
            return out.reshape(b, self.t_out, n // self.t_out, d).mean(dim=2)

    return VideoEncoder(module, n_out_frames)


# ── Loaders ─────────────────────────────────────────────────────────────────

def _load_vit_b16_in21k(device: str = "cuda", tag: str = PAPER1_VIT_TAG):
    """Anchor backbone — ViT-B/16, the encoder Paper 1 trained on.

    Note the tag: `augreg2_in21k_ft_in1k` is ImageNet-21k pretrained and
    ImageNet-1k finetuned. Paper 1 called this "ImageNet-21k init", which
    is imprecise; the weights are pinned here so at least Paper 2A's
    anchor is unambiguous and reproducible.

    Paper 1 froze the lower 6 blocks during *training*. Paper 2A caches
    features from a fully frozen backbone under `torch.no_grad()`, so the
    per-block `requires_grad` flags are irrelevant to the forward pass and
    are deliberately not set here.
    """
    import timm
    m = timm.create_model(f"vit_base_patch16_224.{tag}",
                          pretrained=True, num_classes=0)
    m.eval().to(device)
    return _clipwise_image_encoder(m)


def _load_videomae_large(device: str = "cuda"):
    """VideoMAE-Large (MCG-NJU/videomae-large).

    License: CC-BY-NC-4.0 (non-commercial). Research use only.

    VideoMAE uses a tubelet embedding of 2 frames, so a 16-frame clip
    produces 8 temporal positions — which happens to match the 8-frame
    convention the downstream head expects, no extra pooling needed.
    """
    from transformers import VideoMAEModel
    m = VideoMAEModel.from_pretrained("MCG-NJU/videomae-large")
    m.eval().to(device)
    return _video_encoder(m, n_out_frames=8)


def _load_timesformer_k400(device: str = "cuda"):
    """TimeSformer-base fine-tuned on Kinetics-400.

    License: CC-BY-NC-4.0. Divided space-time attention, feature dim 768,
    8 input frames preserved as 8 temporal positions. The CLS token is
    dropped so the token grid divides evenly by the frame count.
    """
    import torch
    from transformers import TimesformerModel

    inner = TimesformerModel.from_pretrained(
        "facebook/timesformer-base-finetuned-k400")
    inner.eval().to(device)

    class TimesformerEncoder(torch.nn.Module):
        def __init__(self, model, t_out):
            super().__init__()
            self.model = model
            self.t_out = t_out

        def forward(self, clips):
            if clips.dim() != 5:
                raise ValueError(
                    f"expected (B, T, 3, H, W), got {tuple(clips.shape)}")
            out = self.model(pixel_values=clips).last_hidden_state
            tokens = out[:, 1:, :]  # drop CLS
            b, n, d = tokens.shape
            if n % self.t_out != 0:
                raise ValueError(
                    f"token count {n} after dropping CLS is not divisible by "
                    f"{self.t_out}")
            return tokens.reshape(b, self.t_out, n // self.t_out, d).mean(dim=2)

    return TimesformerEncoder(inner, t_out=8)


def _load_vjepa2(device: str = "cuda", size: str = "vitl"):
    """V-JEPA 2 latent predictive world model.

    Meta AI. License: CC-BY-NC-4.0. HF login required. The fpc16 variant
    is used so the 16-frame clip matches our stride convention; V-JEPA's
    tubelet of 2 yields 8 temporal positions like VideoMAE.

    Unverified: the HF class name and the tubelet size are taken from the
    model card, not from a run. This loader stays `pending` in the
    registry until it is smoke-tested on the GPU box.
    """
    from transformers import VJEPA2Model
    m = VJEPA2Model.from_pretrained(f"facebook/vjepa2-{size}-fpc16-256")
    m.eval().to(device)
    return _video_encoder(m, n_out_frames=8)


def _load_vjepa2p1(device: str = "cuda"):
    """V-JEPA 2.1 (March 2026 update).

    Dense features + robotic-grasping improvements. HF ID TBD as of
    2026-07-29; verify before implementing.
    """
    raise NotImplementedError(
        "V-JEPA 2.1 loader — verify HF model ID, then load same as 2.0."
    )


def _load_cosmos_predict2(device: str = "cuda", size: str = "2B"):
    """NVIDIA Cosmos-Predict2 (2B or 14B Video2World variant).

    License: NVIDIA Open Model License (accept via HF UI). Gated.
    Feature extraction: use the intermediate video-tokenizer latents,
    NOT the diffuser final output.
    """
    raise NotImplementedError(
        "Cosmos-Predict2 loader — accept license on HF, install "
        "`cosmos-sdk`, then extract intermediate latents from the "
        "video-tokenizer stage of `Cosmos-Predict2-{size}-Video2World`. "
        "Feature dim is model-specific; measure during smoke test."
    )


def _load_surgmotion(device: str = "cuda"):
    """SurgMotion — V-JEPA-based surgical-native FM (~1B params).

    Released March 2026 by CAIR HKISI. Weights location TBD as of
    2026-07-29.
    """
    raise NotImplementedError(
        "SurgMotion loader — resolve weight source (HF or download URL "
        "from CAIR HKISI), then load V-JEPA-style."
    )


def _load_surgvista(device: str = "cuda"):
    """SurgVISTA (HKUST) — encoder-decoder surgical FM.

    Code at github.com/isyangshu/SurgVISTA. License TBD.
    """
    raise NotImplementedError(
        "SurgVISTA loader — see github.com/isyangshu/SurgVISTA for the "
        "loading script; extract encoder features only."
    )


def _load_endomamba(device: str = "cuda"):
    """EndoMamba — efficient state-space FM for endoscopic video.

    Apache-2.0. github.com/TianCuteQY/EndoMamba.
    """
    raise NotImplementedError(
        "EndoMamba loader — hierarchical Mamba blocks. See repo README."
    )


def _load_zen(device: str = "cuda"):
    """ZEN — cross-procedure surgical FM (arxiv 2602.13633).

    Weight location TBD as of 2026-07-29.
    """
    raise NotImplementedError(
        "ZEN loader — locate weights + license before implementing."
    )


BACKBONES: Dict[str, BackboneSpec] = {
    "vit_b16_in21k": BackboneSpec(
        # Named for continuity with Paper 1. The weights are in21k
        # pretrained *and* in1k finetuned — see PAPER1_VIT_TAG.
        name="vit_b16_in21k", hf_id=f"timm/vit_base_patch16_224.{PAPER1_VIT_TAG}",
        params_millions=86, clip_frames=8, input_hw=(224, 224),
        feature_dim=768, license="apache-2.0",
        stage_0_status="pass", loader=_load_vit_b16_in21k,
        pretrained_tag=PAPER1_VIT_TAG,
    ),
    "videomae_large": BackboneSpec(
        name="videomae_large", hf_id="MCG-NJU/videomae-large",
        params_millions=343, clip_frames=16, input_hw=(224, 224),
        feature_dim=1024, license="cc-by-nc-4.0",
        stage_0_status="pending", loader=_load_videomae_large,
        pretrained_tag="main",
    ),
    "timesformer_k400": BackboneSpec(
        name="timesformer_k400", hf_id="facebook/timesformer-base-finetuned-k400",
        params_millions=120, clip_frames=8, input_hw=(224, 224),
        feature_dim=768, license="cc-by-nc-4.0",
        stage_0_status="pending", loader=_load_timesformer_k400,
        pretrained_tag="main",
    ),
    "vjepa2_vitl": BackboneSpec(
        name="vjepa2_vitl", hf_id="facebook/vjepa2-vitl-fpc16-256",
        params_millions=305, clip_frames=16, input_hw=(256, 256),
        feature_dim=1024, license="cc-by-nc-4.0",
        stage_0_status="pending", loader=_load_vjepa2,
    ),
    "vjepa2p1_vitl": BackboneSpec(
        name="vjepa2p1_vitl", hf_id=None,  # HF ID pending verification
        params_millions=305, clip_frames=16, input_hw=(256, 256),
        feature_dim=1024, license="cc-by-nc-4.0",
        stage_0_status="pending", loader=_load_vjepa2p1,
    ),
    "cosmos_predict2_2b": BackboneSpec(
        name="cosmos_predict2_2b", hf_id="nvidia/Cosmos-Predict2-2B-Video2World",
        params_millions=2000, clip_frames=8, input_hw=(480, 480),
        feature_dim=0, license="nvidia-open-model-license",
        stage_0_status="pending", loader=_load_cosmos_predict2,
    ),
    "surgmotion": BackboneSpec(
        name="surgmotion", hf_id=None,  # TBD
        params_millions=1000, clip_frames=16, input_hw=(224, 224),
        feature_dim=1024, license="TBD",
        stage_0_status="pending", loader=_load_surgmotion,
    ),
    "surgvista": BackboneSpec(
        name="surgvista", hf_id="isyangshu/SurgVISTA",
        params_millions=400, clip_frames=8, input_hw=(224, 224),
        feature_dim=768, license="TBD",
        stage_0_status="pending", loader=_load_surgvista,
    ),
    "endomamba": BackboneSpec(
        name="endomamba", hf_id=None,  # GitHub-hosted
        params_millions=200, clip_frames=8, input_hw=(224, 224),
        feature_dim=768, license="apache-2.0",
        stage_0_status="pending", loader=_load_endomamba,
    ),
    "zen": BackboneSpec(
        name="zen", hf_id=None,  # TBD
        params_millions=0, clip_frames=8, input_hw=(224, 224),
        feature_dim=0, license="TBD",
        stage_0_status="pending", loader=_load_zen,
    ),
}


# ── Extraction pipeline ──────────────────────────────────────────────────────

def clip_id_hash(video_id: str, clip_end_frame: int) -> str:
    """Deterministic 12-char hash for cache filename."""
    return hashlib.sha256(f"{video_id}|{clip_end_frame}".encode()).hexdigest()[:12]


def cache_path(cache_root: Path, backbone: str, dataset: str,
               video_id: str, clip_end_frame: int) -> Path:
    """Cache path for one clip's features."""
    h = clip_id_hash(video_id, clip_end_frame)
    subdir = cache_root / backbone / dataset / video_id
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir / f"{clip_end_frame:07d}_{h}.npy"


def extract_one_dataset(backbone_name: str, dataset_name: str,
                         data_root: Path, cache_root: Path,
                         label_json: Path, device: str = "cuda",
                         dry_run: bool = False) -> None:
    """Extract per-clip features for one (backbone, dataset) pair.

    Reads the label JSON (produced by our existing labels pipeline),
    iterates clip-end positions per video (strict prefix-only), calls
    the backbone's encoder on each clip, saves the per-clip feature
    tensor to the cache.
    """
    spec = BACKBONES[backbone_name]
    if spec.stage_0_status not in ("pass", "pending"):
        raise RuntimeError(
            f"{backbone_name} has stage_0_status={spec.stage_0_status}; "
            f"cannot extract features until it passes Phase 0 audit."
        )

    logger.info(f"[extract] backbone={backbone_name} dataset={dataset_name}")
    logger.info(f"[extract] data_root={data_root}")
    logger.info(f"[extract] cache_root={cache_root}")
    logger.info(f"[extract] label_json={label_json}")

    labels = json.loads(Path(label_json).read_text())
    videos = labels.get("videos", labels)  # accept either flat or nested

    if dry_run:
        logger.info(f"[extract] DRY RUN — would extract features for "
                    f"{len(videos)} videos.")
        return

    # Placeholder — real implementation:
    # 1. encoder = spec.loader(device)
    # 2. for video_id, video_meta in videos.items():
    #      for clip_end in range(0, video_len, frame_stride):
    #          if clip already cached: skip
    #          clip_tensor = load_clip(video_id, clip_end, spec.clip_frames, spec.input_hw)
    #          with torch.no_grad(): features = encoder(clip_tensor)
    #          np.save(cache_path(...), features.cpu().numpy())
    #
    # Real implementation waits until Phase 0 audit confirms the backbone
    # and dataset are ready.

    raise NotImplementedError(
        "Real extraction loop lands in Phase 0 week 2 after the backbone "
        "audit confirms which loaders resolve. This file only registers "
        "the interface for now."
    )


# ── Smoke tests (Phase 0 gate) ───────────────────────────────────────────────

def smoke_test(backbone_name: str, device: str = "cuda",
               n_clips: int = 5) -> dict:
    """Load the backbone, feed it n_clips of random-noise input, measure
    throughput, and check the output honours the interface contract.

    Fills in the throughput and cache-size columns of the feasibility
    matrix without needing real dataset access. A backbone that loads and
    runs but returns the wrong shape is reported as `contract_violation`
    rather than `ok`: a silently mis-shaped feature tensor would be far
    more expensive to discover during Phase 1.
    """
    import torch
    spec = BACKBONES[backbone_name]
    logger.info("[smoke] Loading %s...", backbone_name)
    t0 = time.time()
    try:
        encoder = spec.loader(device)
    except NotImplementedError as e:
        return {"backbone": backbone_name, "status": "loader_not_implemented",
                "error": str(e)}
    except Exception as e:
        return {"backbone": backbone_name, "status": "load_failed",
                "error": f"{type(e).__name__}: {e}"}
    load_seconds = time.time() - t0

    H, W = spec.input_hw
    T = spec.clip_frames
    dummy = torch.randn(n_clips, T, 3, H, W, device=device)

    t0 = time.time()
    try:
        with torch.no_grad():
            out = encoder(dummy)
    except Exception as e:
        return {"backbone": backbone_name, "status": "forward_failed",
                "error": f"{type(e).__name__}: {e}",
                "load_seconds": round(load_seconds, 2)}
    infer_seconds = time.time() - t0

    result = {
        "backbone": backbone_name,
        "status": "ok",
        "pretrained_tag": spec.pretrained_tag,
        "params_millions": spec.params_millions,
        "load_seconds": round(load_seconds, 2),
        "infer_seconds_for_n_clips": round(infer_seconds, 3),
        "clips_per_second": round(n_clips / max(infer_seconds, 1e-6), 2),
        "output_shape": list(out.shape),
        "declared_feature_dim": spec.feature_dim,
        "measured_feature_dim": int(out.shape[-1]),
        # 4 bytes per float32 value, one cached tensor per clip.
        "bytes_per_clip": int(out[0].numel() * 4),
    }

    problems = []
    if out.dim() != 3:
        problems.append(
            f"expected a 3-D (B, T, D) tensor, got {out.dim()}-D "
            f"{tuple(out.shape)}")
    else:
        if out.shape[0] != n_clips:
            problems.append(
                f"batch dim {out.shape[0]} != {n_clips} clips in")
        if spec.feature_dim and out.shape[-1] != spec.feature_dim:
            problems.append(
                f"feature dim {out.shape[-1]} != declared "
                f"{spec.feature_dim} in the registry")
    if problems:
        result["status"] = "contract_violation"
        result["problems"] = problems
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List registered backbones.")

    p_smoke = sub.add_parser("smoke", help="Smoke-test a backbone.")
    p_smoke.add_argument("backbone", choices=list(BACKBONES.keys()))
    p_smoke.add_argument("--n-clips", type=int, default=5)
    p_smoke.add_argument("--device", default="cuda")

    p_extract = sub.add_parser("extract", help="Extract features for one (backbone, dataset).")
    p_extract.add_argument("--backbone", required=True, choices=list(BACKBONES.keys()))
    p_extract.add_argument("--dataset", required=True,
                           choices=["mb140", "cholec80", "autolaparo"])
    p_extract.add_argument("--data-root", required=True, type=Path)
    p_extract.add_argument("--cache-root", required=True, type=Path)
    p_extract.add_argument("--label-json", required=True, type=Path)
    p_extract.add_argument("--device", default="cuda")
    p_extract.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.cmd == "list":
        for name, spec in BACKBONES.items():
            print(f"  {name:22s} status={spec.stage_0_status:8s} "
                  f"params={spec.params_millions:6.0f}M  "
                  f"license={spec.license}")
        return

    if args.cmd == "smoke":
        result = smoke_test(args.backbone, device=args.device, n_clips=args.n_clips)
        print(json.dumps(result, indent=2))
        return

    if args.cmd == "extract":
        extract_one_dataset(
            backbone_name=args.backbone, dataset_name=args.dataset,
            data_root=args.data_root, cache_root=args.cache_root,
            label_json=args.label_json, device=args.device,
            dry_run=args.dry_run,
        )
        return


if __name__ == "__main__":
    main()

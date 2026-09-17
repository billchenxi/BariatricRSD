# Backbone Feasibility Matrix

> **Note (2026-09-17):** references below to `NEXT_PAPER_PLAN.md`,
> `NEXT_PAPER_BRIEF.md`, or `PAPER_2A_REVIEWER_HARDENING.md` now resolve to
> [`docs/STRATEGY.md`](../../../plans/STRATEGY.md), which merged them. Originals are at
> git commit `58c99bc`.

*Phase 0 deliverable. Last updated 2026-08-08. Rows were originally
populated from public HuggingFace model cards, GitHub READMEs, and paper
pages; the anchor row now carries numbers measured by actually running
it. Every row must pass the audit criteria in `PHASE_0_KICKOFF.md`
before being kept in the Paper 2A matrix.*

> **2026-08-08 — interface contract fixed before any audit ran.** The
> first real execution of the anchor loader failed: `smoke_test` fed a
> 5-D `(B, T, 3, H, W)` tensor to an image model expecting 4-D, so
> *every* row would have failed its smoke test for a reason unrelated to
> the backbone. `extract.py` now wraps image models
> (`_clipwise_image_encoder`) and video models (`_video_encoder`) to a
> single `(B, T, 3, H, W) -> (B, T, D)` contract, and `smoke_test`
> verifies the returned shape and feature dim rather than reporting
> `ok` for anything that did not raise. Audit results recorded before
> this date should be treated as void.

> **2026-08-08 — weight provenance is now pinned per row.** Paper 1 (and
> the first version of this matrix) called the anchor "ImageNet-21k
> init", and the loader used `timm.create_model("vit_base_patch16_224",
> pretrained=True)`. That resolves to timm's *default* tag, which is
> `augreg2_in21k_ft_in1k` — ImageNet-21k pretrained **and then
> ImageNet-1k finetuned**, not the plain `orig_in21k` weights the name
> implies. The default tag can also change between timm releases, which
> would silently change the anchor under a reproduction attempt. Every
> row now records an explicit `pretrained_tag`, and a test asserts that
> any row marked `pass` has one. If Paper 1 reaches camera-ready, its
> encoder description should be corrected to "ImageNet-21k pretrained,
> ImageNet-1k finetuned (timm `augreg2_in21k_ft_in1k`)".

**Audit criteria per row:**

- **Weights** — publicly obtainable under a research-compatible
  license, no waitlist, downloadable via `huggingface_hub` or `git-lfs`
  or direct URL.
- **License** — permits research use and (ideally) redistribution of
  fine-tuned derivatives.
- **Preprocessing** — documented pipeline (frame rate, resolution,
  normalization) that we can reproduce.
- **Feature shape** — stable per-clip tensor shape consumable by our
  temporal head through a simple projection layer.
- **Smoke test** — one-video feature extraction succeeds on GH200 /
  H100 in a fresh environment.
- **Throughput** — measured clips/sec on 100 clips.
- **Cache size** — estimated feature-cache footprint per dataset.

If any of the first three fail, the row becomes related-work only, not
a baseline. `pass_stage_0` should be one of `pending`, `pass`, `fail`,
`skipped`.

---

## Backbone rows

### 1. ViT-B/16 (current baseline — reference)

| Field | Value |
|---|---|
| Source | timm `vit_base_patch16_224.augreg2_in21k_ft_in1k` |
| Pretrained tag | `augreg2_in21k_ft_in1k` (**pinned**; in21k pretrain + in1k finetune) |
| Params (trainable / total) | ~44M / ~86M (lower 6 blocks frozen *during Paper 1 training*; Paper 2A caches features from a fully frozen backbone) |
| Feature shape | **8 × 768 per clip — measured** |
| Weights license | Apache-2.0 |
| Preprocessing | 224×224, ImageNet norm, no temporal SSL |
| Smoke test | **pass** — 2026-08-08, CPU (macOS arm64, torch 2.13.0, timm 1.0.28) |
| Load time | 2.5 s from warm HF cache (401 s on first download) |
| Throughput | 3.2 clips/s on CPU; GH200 number still to be measured |
| Cache size | **24,576 B/clip** (8 × 768 × float32) |
| pass_stage_0 | **pass** (Paper 1 anchor) |
| Notes | Already-trained checkpoints live in `reproducibility/weights/`. Used as the "anchor" backbone against which every FM is compared. Cache-size projection for MB140 at 1 fps: ~14 GB at clip-stride 1, ~2.8 GB at clip-stride 5. |

### 2. VideoMAE-Large

| Field | Value |
|---|---|
| Source | HF `MCG-NJU/videomae-large` |
| Params | ~343M |
| Feature shape | (T=16, patches, 1024) — pool needed |
| Weights license | **CC-BY-NC-4.0** (non-commercial) |
| Gating | none (public) |
| Preprocessing | 224×224, 16-frame clip, 4×2 spatial patches, ImageNet norm |
| Loader | **implemented** (`_load_videomae_large`), not yet smoke-tested |
| pass_stage_0 | **pending — needs GPU-box smoke test** |
| Notes | License is NC — permitted for research paper but blocks any downstream commercial redistribution. Pooling resolved: VideoMAE's 2-frame tubelet turns a 16-frame clip into 8 temporal positions, which already matches the downstream 8-frame convention; the loader mean-pools spatial patches within each position. The 1024→768 projection remains a separate downstream stage, as designed. |

### 3. TimeSformer (base, K400)

| Field | Value |
|---|---|
| Source | HF `facebook/timesformer-base-finetuned-k400` |
| Params | ~120M (estimated) |
| Feature shape | (T=8, patches, 768) |
| Weights license | **CC-BY-NC-4.0** (non-commercial) |
| Gating | none (public) |
| Preprocessing | 224×224, 8-frame clip, ImageNet norm |
| Loader | **implemented** (`_load_timesformer_k400`), not yet smoke-tested |
| pass_stage_0 | **pending — needs GPU-box smoke test** |
| Notes | Divided space-time attention. Drops in cleanly as an 8-frame @ 224×224 replacement for ViT-B/16 at the same 768 feature dim. The loader drops the CLS token before reshaping so the token grid divides evenly by the 8 frames. Same license caveat as VideoMAE. |

### 4. V-JEPA 2 (Latent World Model)

| Field | Value |
|---|---|
| Source | HF `facebook/vjepa2-vitl-fpc64-256` (large) or `-vitg-` (giant) |
| Params | ~305M (ViT-L) / ~1B (ViT-g) |
| Feature shape | (T=64 or 16, patches, hidden) — configurable |
| Weights license | CC-BY-NC-4.0 (Meta) |
| Gating | HF login required; not fine-grained gating |
| Preprocessing | 256×256, 64-frame or 16-frame clip, self-normalized |
| Loader | **implemented** (`_load_vjepa2`), **unverified** — HF class name and tubelet size taken from the model card, not from a run |
| pass_stage_0 | **pending — needs GPU-box smoke test + HF login** |
| Notes | Latent predictive model — features are more downstream-relevant than pixel-quality-optimized models. `vjepa2-vitl-fpc16-256` matches our 8-frame convention if we downsample stride. Meta's model card documents downstream anticipation and planning results. **Risk:** if the tubelet is not 2, the loader's `n_out_frames=8` assumption is wrong; the smoke test's divisibility check will catch this rather than silently mis-pooling. |

### 5. V-JEPA 2.1 (Dense Features Update)

| Field | Value |
|---|---|
| Source | HF (search for `vjepa2.1` — released March 2026) |
| Params | ~1B (matches 2.0 g variant) |
| Feature shape | Denser than 2.0 |
| Weights license | CC-BY-NC-4.0 |
| Gating | HF login required |
| pass_stage_0 | **pending** — verify HF model ID |
| Notes | Stronger dense features + real-robot grasping gains. May be a better fit than 2.0 for our per-clip anticipation tasks. If the HF weights aren't yet listed, defer to 2.0 as the primary V-JEPA row. |

### 6. Cosmos-Predict2 (Physical AI World Model)

| Field | Value |
|---|---|
| Source | HF `nvidia/Cosmos-Predict2-2B-Video2World` (also 14B variant) |
| Params | 2B or 14B |
| Feature shape | Diffusers-native latent + text embedding |
| Weights license | **NVIDIA Open Model License** (accept before download) |
| Gating | **YES — automatic gating; must accept license through HF UI** |
| Preprocessing | 720p or 480p input; internal preprocessing via `diffusers` |
| pass_stage_0 | **pending — check gate + feature-extraction contract** |
| Notes | Generative video predictor. To use as a feature extractor we probably need to extract the intermediate video-tokenizer latents rather than raw diffuser outputs. The 2B variant is the realistic starting point on a single GH200 (14B needs multi-GPU). If integration is complicated, keep as a diagnostic row per the Cosmos-meh recovery narrative. |

### 7. SurgMotion (Surgical-native, V-JEPA-based)

| Field | Value |
|---|---|
| Source | Not yet confirmed on HF (see note); GitHub repo not indexed as of 2026-07-29 |
| Params | ~1B (per launch announcement) |
| Feature shape | V-JEPA-native (similar to V-JEPA 2) |
| Weights license | Open-source per launch announcement, exact license TBD |
| Gating | TBD |
| Preprocessing | 224 or 256 spatial; V-JEPA-style temporal masking during pretrain |
| pass_stage_0 | **pending — locate weights + license terms** |
| Notes | Released March 24 2026 by CAIR HKISI. 3,658-hour SurgMotion-15M corpus, 50 sources, 13 organs. As a surgical-native V-JEPA-based FM, this is the most relevant single row. **Priority action: find the HF or download URL before writing off the row.** |

### 8. SurgVISTA (Surgical-native, encoder-decoder)

| Field | Value |
|---|---|
| Source | HF `isyangshu/SurgVISTA` (per GitHub README), also linked from npj DM paper |
| Params | ~400M (estimated from the encoder-decoder architecture description) |
| Feature shape | Video-level encoder output; specifics TBD |
| Weights license | Not specified on GitHub — need to confirm |
| Gating | HF login likely required |
| Preprocessing | Documented in GitHub repo |
| pass_stage_0 | **pending — confirm license** |
| Notes | HKUST group, 3,650-video corpus, 13 downstream datasets. Direct competitor + baseline for Paper 2A. |

### 9. EndoMamba (Surgical/endoscopic, State-space)

| Field | Value |
|---|---|
| Source | GitHub `TianCuteQY/EndoMamba` |
| Params | ~200M (estimated) |
| Feature shape | Bidirectional Mamba spatial + Mamba temporal blocks |
| Weights license | Apache-2.0 |
| Gating | none |
| Preprocessing | Documented in repo |
| pass_stage_0 | **pending — confirm weights download + smoke test** |
| Notes | Efficient real-time inference — good for online anticipation tasks. Trained on 74k video clips (11.3M frames). MICCAI 2025. |

### 10. EndoDINO (Surgical/GI-endoscopy, image-level)

| Field | Value |
|---|---|
| Source | Not clearly on HF as of check; paper page + institutional PDF |
| Params | Multiple sizes (86M / 307M / 1B via DINOv2 methodology) |
| Feature shape | Per-frame DINOv2-style patch embedding |
| Weights license | TBD |
| Gating | TBD |
| Preprocessing | DINOv2 conventions |
| pass_stage_0 | **skipped — image-level, secondary priority** |
| Notes | Image-level pretraining (not video). Useful as an image-domain baseline but doesn't compete with video-native FMs for temporal tasks. Include only if weights are trivially obtainable. |

### 11. ZEN (Cross-procedure intraoperative FM)

| Field | Value |
|---|---|
| Source | arXiv 2602.13633; GitHub / HF not identified as of check |
| Params | Not disclosed |
| Feature shape | Not documented publicly |
| Weights license | TBD |
| Gating | TBD |
| Preprocessing | Multi-teacher distillation |
| pass_stage_0 | **pending — locate release** |
| Notes | Trained on 4M+ frames from 21+ procedures. **Cross-procedure generalization** is a core paper claim, directly relevant to our variability-scaling thesis. Priority for the audit: check whether Park et al. have released weights. |

---

## Dataset rows (Phase 0 hardening addition)

### D1. MultiBypass140 — already local

| Field | Value |
|---|---|
| Status | Already downloaded via public release; used in Paper 1 |
| License | CC-BY-NC-SA 4.0 (research use) |
| Videos | 140 (70 Bern + 70 Strasbourg) |
| Phases | 14 |
| Native fps | 25; resampled to 1 fps |
| pass_stage_0 | **pass** |

### D2. Cholec80 — already local

| Field | Value |
|---|---|
| Status | Already downloaded; used in Paper 1 |
| License | Research-use only |
| Videos | 72 (public phase-labeled subset), 80 total |
| Phases | 7 |
| Native fps | 25; resampled to 1 fps |
| pass_stage_0 | **pass** |

### D3. AutoLaparo — reviewer hardening addition

| Field | Value |
|---|---|
| Source | https://autolaparo.github.io/ (request form) |
| Videos | 21 laparoscopic hysterectomy |
| Duration | 27–112 minutes per video |
| Native resolution | 1920×1080 @ 25 fps |
| Phases | 7 workflow-recognition phases |
| Additional tasks | Instrument segmentation, laparoscope motion prediction |
| License | CC-BY-NC-SA 4.0 |
| Gating | Access form required |
| pass_stage_0 | **pending — submit request form** |
| Notes | The third dataset the Paper 1 reviewers wanted. Smaller than MB140 (21 vs 140 videos) but independent variation in workflow entropy. Extend Phase 0 audit to include cluster-entropy computation for this dataset. |

### D4. CholecT50 — optional stretch (action-triplet task)

| Field | Value |
|---|---|
| Source | https://huggingface.co/datasets/Voxel51/cholect50 |
| Videos | 50 (extension of Cholec80 with instrument-verb-target triplets) |
| pass_stage_0 | **skipped for Phase 0 — Phase 2 stretch only** |
| Notes | Only include if Task C (action-triplet anticipation) survives scoping. |

---

## Alternative workflow-representation prototypes (hardening addition)

Paper 1 used only TF-IDF + PCA + k-means clustering, which iSh9 flagged
as a potential confound. Paper 2A needs at least two alternative
representations for a sensitivity study.

### R1. TF-IDF + PCA + k-means (current) — reference

- Already implemented in `labels/` and `lambda_setup/scripts/07_cluster_phase_orders.py`.
- Reused as-is.

### R2. Learned continuous embedding

- Train a small transformer that pools per-video visual features into a
  128-dim vector.
- No clustering; each video's workflow rep is a continuous point in
  128-dim space.
- Downstream conditioning: workflow token = MLP(video_embedding).
- Estimated implementation: ~1 day, ~10 GPU-h to train.

### R3. HMM-based phase segmentation

- Use ground-truth phase labels + HMM state transitions to represent
  workflow.
- State-space rep with T states (T = phase count per dataset).
- Downstream conditioning: workflow token = MLP(HMM state posterior).
- Estimated implementation: ~2 days, minimal compute.

Note: All three representations should be trainable / computable
offline before the main-experiment matrix runs, so they don't add to
the frozen-feature training-time cost.

---

## Summary counts (audit target)

| Category | Count | Notes |
|---|---|---|
| Backbones targeted | 11 | 1 anchor + 3 general video + 2 physical-AI + 5 surgical-native |
| Backbones expected to `pass` after Phase 0 | 5–8 | Cosmos + one V-JEPA + one general video + 1–3 surgical-native |
| Datasets targeted | 3 (+ 1 optional) | MB140 + Cholec80 + AutoLaparo + (CholecT50) |
| Workflow-rep families | 3 | k-means + learned embedding + HMM |

Phase 1 scout-matrix scope (from `NEXT_PAPER_BRIEF.md` §6, adjusted):
**≥ 4 backbones × 3 datasets × 2 conditions × 2 seeds** = ~48 trained-head
runs (frozen features), ~250–500 GPU-h.

---

## Next-action queue (do in order)

Done 2026-08-08:

- [x] **Fix the extraction interface contract** so smoke tests measure the
      backbone rather than the harness (`_clipwise_image_encoder`,
      `_video_encoder`, shape-checking `smoke_test`; 18 tests in
      `tests/test_backbone_extract.py`).
- [x] **Anchor row audited end-to-end** — ViT-B/16 loads, runs, and
      returns the contracted `(B, 8, 768)`; throughput and cache size
      measured on CPU; weight tag pinned.
- [x] **Loaders implemented** for VideoMAE-Large, TimeSformer, V-JEPA 2
      (code complete; smoke tests still pending hardware).

Remaining, in order:

1. **Submit AutoLaparo access request** (form submission, ~10 min).
   *Blocking:* needs a human to fill the form. Longest lead time of
   anything here, so do it first.
2. **Register an HF read token** and accept licenses for the gated rows
   (Cosmos-Predict2, V-JEPA 2 / 2.1).
3. **Locate SurgMotion weights** (email authors or search HF exhaustively).
4. **Locate SurgVISTA + ZEN license** (GitHub / paper appendix search).
5. **Run smoke tests on the GPU box** for VideoMAE, TimeSformer, V-JEPA 2
   — the loaders are written, so this is now `python -m
   paper2_infra.backbone_features.extract smoke <name> --device cuda`
   per row. Expect the V-JEPA row to need its `n_out_frames` corrected
   if the tubelet is not 2; the divisibility check will say so.
6. **Populate throughput + cache-size columns** with GH200 numbers.
7. **Update `pass_stage_0`** from `pending` to `pass` / `fail` per row.
8. **Freeze the backbone set** for the Phase 1 scout matrix — noting
   that Phase 1's sampling changed to 5 folds × 1 seed, so the run
   budget per backbone is now 5 rather than 2 on MB140 (see
   [PHASE_0_FINDING_FOLD_VARIANCE.md](PHASE_0_FINDING_FOLD_VARIANCE.md)).

Kill-switch: if fewer than 4 backbones pass Phase 0 (1 anchor + 3
non-anchor), narrow Paper 2A scope to "ViT vs. one strong FM" — see
NEXT_PAPER_BRIEF.md §3 "Minimum Viable Paper 2A."

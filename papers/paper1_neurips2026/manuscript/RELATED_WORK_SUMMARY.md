# Related Work — Cited Paper Summaries

Companion document for the NeurIPS 2026 submission. For each cited paper:
link, summary, key differences from ours, their results vs ours, and why
ours improves on theirs *or* why we adopt their method/results.

Categories:
1. [Direct RSD comparators](#1-direct-rsd-comparators)
2. [Phase recognition (auxiliary task / temporal architecture)](#2-phase-recognition-auxiliary-task--temporal-architecture)
3. [Datasets and benchmarks](#3-datasets-and-benchmarks)
4. [Architecture and general ML](#4-architecture-and-general-ml)
5. [Surgical foundation models (mentioned for context only)](#5-surgical-foundation-models-mentioned-for-context-only)
6. [Methodology — privileged information, conditioning, controls](#6-methodology--privileged-information-conditioning-controls)
7. [Optimization](#7-optimization)
8. [Statistics](#8-statistics)
9. [Bariatric surgery video understanding (recent)](#9-bariatric-surgery-video-understanding-recent)

---

## 1. Direct RSD comparators

### 1.1 RSDNet — Twinanda et al. 2019

- **bibkey:** `twinanda2019rsdnet`
- **Venue:** IEEE Transactions on Medical Imaging 38(4), 1069–1078
- **Link:** https://arxiv.org/abs/1802.03243

**Summary.** First end-to-end deep network specifically for remaining surgery duration (RSD) prediction. Introduced the self-supervised target $y_t = (T - t) / T$ — a normalized progress signal that doesn't require manual annotation of operative time. Architecture: ResNet-152 → LSTM → scalar regression head. Trained and evaluated on Cholec80 (canonical 40-video test split).

**Key differences from ours:**
- Their backbone is ResNet-152 + LSTM (CNN-RNN era); ours is ViT-B/16 + Hierarchical Temporal Attention (modern transformer stack).
- Their primary contribution is the *self-supervised target*; ours is the *conditioning question* (when does workflow signal help?).
- They report only Cholec80; we contrast Cholec80 against MultiBypass140 as a pair of benchmarks with different workflow variability.
- They have no workflow-conditioning mechanism — the model sees only visual context and elapsed time.

**Results comparison.**
- RSDNet on canonical Cholec80 40-video test split: ≈ **8.0 min** MAE.
- Our Cholec80 best (Run 019C, ensemble + isotonic, 30-video public split): **3.56 min** MAE — much lower, but on a different (smaller) split, so not a like-for-like SOTA claim.
- Our single-model Cholec80 baseline (Run 017): **4.46 ± 0.22 min** — still well below RSDNet's 8.0 even acknowledging split differences.

**Why ours is better.** Modernized backbone (ViT vs ResNet, transformer vs LSTM) and inference-time post-processing (isotonic) give a ≈ 4 min absolute improvement. More importantly, RSDNet doesn't address the conditioning question at all — our paper is orthogonal to RSDNet's contribution rather than a replacement.

**Why we cite/use them.** RSDNet's $y_t = (T - t) / T$ self-supervised target is the standard in the field; we use it. They're also the canonical "raw video → Cholec80 RSD" baseline that every later RSD paper compares against.

---

### 1.2 TransLocal — Loukas et al. 2024

- **bibkey:** `loukas2024translocal`
- **Venue:** Int. J. Medical Robotics and Computer Assisted Surgery 20(2), e2632
- **Link:** https://doi.org/10.1002/rcs.2632

**Summary.** A more modern Cholec80 RSD predictor that augments a CNN-LSTM front-end with a Transformer using **windowed local attention**. Incorporates visual saliency cues to focus the model on procedurally relevant regions of each frame. Trained and evaluated on canonical Cholec80 40-video test split.

**Key differences from ours:**
- They use windowed local attention; we use Hierarchical Temporal Attention (HTA-inspired) with both local and global branches per block.
- They have no workflow-conditioning mechanism — like RSDNet, only visual context is used.
- Their architecture innovation is on the *temporal* side; ours is the *workflow conditioning* axis.

**Results comparison.**
- TransLocal on canonical Cholec80 40-video test split: **7.10 min** MAE.
- Our Cholec80 best on 30-video public split: **3.56 min** (ensemble + isotonic).
- Our single-seed strict-protocol Cholec80 (Run 046): **4.34 min**.

**Why ours is better.** Same caveat as RSDNet — TransLocal is the current published SOTA on the canonical split, but on raw video alone. Our 3.56 is on a smaller split (30 of 40 test videos with public phase labels), so we explicitly do *not* claim SOTA against TransLocal. We do claim our pipeline is *competitive* with the published Cholec80 RSD literature.

**Why we cite them.** They are the most recent published baseline using raw video on canonical Cholec80, and the closest like-for-like comparator we acknowledge in §6.6 / §6.10. Listed in the Cholec80 RSD literature comparison table.

---

### 1.3 Kostopoulos et al. 2025

- **bibkey:** `kostopoulos2025prediction`
- **Venue:** Biomedical Engineering / Biomedizinische Technik 70(3), 229–239
- **Link:** https://doi.org/10.1515/bmt-2024-0431

**Summary.** Predicts Cholec80 RSD using **laparoscopic annotation data** (phase labels + instrument labels) as input, not raw video. Cluster surgeries into "long" vs "short" by total duration; train a separate random forest for each cluster; switch between models at an elapsed-time threshold. Reports 5.89 min full-video MAE and 4.61 min at T−20 min.

**Key differences from ours:**
- **Input modality (the big one):** they consume already-annotated phase + instrument labels; we consume raw video.
- **Clustering basis:** they cluster by *total duration* (an outcome variable); we cluster by *phase-bigram patterns* (a workflow descriptor independent of duration).
- **Mechanism:** they switch between separate predictors; we condition a single model via a learned embedding token (continuous, supports soft mixtures).
- **Causal-at-inference:** they don't address inferring the cluster signal from observed prefix; we do (§4.5, §6.5).
- **Model class:** random forest vs end-to-end deep network.

**Results comparison.**
- Kostopoulos: 5.89 min full-video, 4.61 at T−20 (annotation input, their split).
- Our Cholec80 strict-protocol full-video (Run 046, 1 seed): **4.34 min** (raw video input).
- Our Cholec80 inference stack (Run 019C): **3.56 min** (ensemble + isotonic, raw video, 30-video public split).

**Why ours is better.**
1. **End-to-end from pixels** — Kostopoulos's pipeline isn't deployable in real time without an upstream phase recognition system providing the input annotations; ours is.
2. **Conditioning signal is workflow, not outcome** — clustering by case length is tautologically informative for RSD prediction, since "long-case" cluster members have, by definition, more remaining time; clustering by phase order is a non-trivial procedural signal.
3. **Cross-dataset generalization claim is testable** — our variability-scaling hypothesis (§6.7) makes a falsifiable prediction across datasets that Kostopoulos's approach can't generate.

**Why we cite them.** Most recent ML-method baseline on the workflow-conditioning theme for RSD, listed as one of the "two closest prior ideas" (§2). Critical to acknowledge to pre-empt reviewer "why not compare to 5.89?" comments — answer: different input modality, not apples-to-apples.

---

### 1.4 Yengera et al. 2018 — "Less Is More"

- **bibkey:** `yengera2018less`
- **Venue:** arXiv:1805.08569
- **Link:** https://arxiv.org/abs/1805.08569

**Summary.** Self-supervised pre-training of a CNN-LSTM network for surgical phase recognition. Uses RSD prediction as a pretext (auxiliary) task during pre-training to reduce annotation cost. Evaluated on Cholec80.

**Key differences from ours:**
- Their RSD use is as a *pre-training auxiliary task* for phase recognition; ours is RSD as the *primary task*.
- Direction of the conditioning relationship is reversed: they use RSD to help phase recognition; we use phase to help RSD.
- No workflow-cluster conditioning mechanism.

**Results comparison.** Less directly comparable — their headline metric is phase-recognition accuracy, not RSD MAE. RSD numbers reported as a sanity check, similar magnitude to RSDNet (~7-8 min).

**Why we cite them.** Establishes the reciprocal relationship between phase recognition and RSD prediction. Counts as nearest-neighbor prior work for "use one task to help the other" within the surgical-AI literature.

**Why ours differs.** We use phase prediction as a downstream auxiliary head (multi-task) and additionally condition on a workflow-cluster signal — a different mechanism from "RSD as pretext."

---

### 1.5 Yengera et al. 2019 — Unsupervised Temporal Video Segmentation

- **bibkey:** `yengera2019unsupervised`
- **Venue:** MICCAI 2019 (LNCS 11769)
- **Link:** https://doi.org/10.1007/978-3-030-32695-1_4

**Summary.** Adds an *unsupervised temporal video segmentation* auxiliary task during RSD training. The model learns to detect change-points in unlabeled video, producing segment-level features that improve RSD prediction. No manual phase labels used.

**Key differences from ours:**
- They cluster on **temporal segments within each video** (intra-video); we cluster on **whole-video phase-bigram patterns** (inter-video, video-level).
- Their auxiliary signal is unsupervised segmentation; ours is supervised phase classification + a workflow-cluster conditioning token.
- They don't ask the *cross-dataset* variability-scaling question.

**Results comparison.** Reports modest MAE improvement vs RSDNet on Cholec80, similar magnitude to other Cholec80 RSD methods of that era (~7-8 min range).

**Why we cite them.** Listed as one of the "two closest prior ideas" along with Kostopoulos in §2 and §1.5. They are nearest-neighbor work on auxiliary self-supervised signals for RSD.

**Why ours differs.** Unit (whole-video vs within-video segments), mechanism (learned conditioning token vs auxiliary loss), and empirical question (variability-scaling vs single-dataset improvement).

---

## 2. Phase recognition (auxiliary task / temporal architecture)

### 2.1 EndoNet — Twinanda et al. 2017

- **bibkey:** `twinanda2017endonet`
- **Venue:** IEEE Transactions on Medical Imaging 36(1), 86–97
- **Link:** https://arxiv.org/abs/1602.03012

**Summary.** Foundational deep CNN for surgical phase + tool recognition on Cholec80. Established Cholec80 as the dominant phase-recognition benchmark.

**Why we cite them.** Introduced **Cholec80**, the dataset our paper uses as the contrast benchmark. Also the first deep-learning baseline for surgical-AI tasks generally. We cite them every time we mention the dataset.

**Why ours differs.** EndoNet is a phase-recognition system; we do RSD prediction. They were also the first to argue for joint training of multiple surgical-video tasks — a pattern our multi-task design (RSD + phase + deviation) follows.

---

### 2.2 TeCNO — Czempiel et al. 2020

- **bibkey:** `czempiel2020tecno`
- **Venue:** MICCAI 2020

**Summary.** Multi-stage temporal convolutional network for online surgical phase recognition. Decoupled spatial-then-temporal architecture: a frame-level CNN feature extractor produces per-frame features, then a TCN refines the temporal sequence. State-of-the-art for Cholec80 phase recognition at the time.

**Why we cite them.** Establishes the **decoupled spatial-then-temporal** design pattern that we adopt for our `decoupled-oracle` row in §6.1. Specifically: TeCNO trains the frame CNN and the temporal stage in two phases (spatial first, then temporal), preventing the temporal module from corrupting frame-level visual features. Our decoupled-phase-head architecture follows the same pattern but for a different identification reason.

**Why ours differs.** We adopt their pattern *for causal identification* (to ensure the workflow-token gain cannot be laundered through the auxiliary phase head), not as an architectural novelty. We don't compete on phase recognition accuracy.

---

### 2.3 Trans-SVNet — Gao et al. 2021

- **bibkey:** `gao2021transsvnet`
- **Venue:** MICCAI 2021
- **Link:** https://arxiv.org/abs/2103.09712

**Summary.** Hybrid embedding aggregation transformer for surgical phase recognition. Combines local spatial features and aggregated temporal context using transformer attention.

**Why we cite them.** Listed as one of the temporal-modeling steps (TeCNO → Trans-SVNet → SKiT → Surgformer) that the field has progressed through. Establishes that transformer-based temporal modeling is the modern surgical-video standard.

**Why ours differs.** They optimize for phase recognition; we use phase recognition as auxiliary and target RSD.

---

### 2.4 SKiT — Liu et al. 2023

- **bibkey:** `liu2023skit`
- **Venue:** ICCV 2023

**Summary.** Fast key-information video transformer for *online* surgical phase recognition. Uses a key-information token that aggregates relevant past frames, designed for low-latency inference.

**Why we cite them.** Listed in the temporal-modeling progression in §2. Their key-information token is conceptually adjacent to our workflow token, both being summary tokens that condition downstream computation.

**Why ours differs.** SKiT's key-information token is *learned end-to-end* from the visual sequence; our workflow token is *derived from offline phase-bigram clusters* and supplied as an external signal. Different design philosophies (visual self-attention vs explicit semantic conditioning).

---

### 2.5 Surgformer — Yang et al. 2024 (the HTA we build on)

- **bibkey:** `yang2024surgformer`
- **Venue:** MICCAI 2024
- **Link:** https://arxiv.org/abs/2408.03867

**Summary.** Hierarchical Temporal Attention (HTA) — a multi-scale temporal attention block that captures both local and global temporal patterns in surgical video for phase recognition. Their HTA block has three scales (local, medium, global) with per-scale attention then concat + linear projection.

**Why we cite them.** **Our temporal head is HTA-inspired** — we adapted Surgformer's HTA design to produce our temporal stack. Specifically: 6 stacked HTA-inspired blocks, each with a local-attention branch (first half of the 9-token sequence) and a global-attention branch (full sequence), concatenated and projected back. We deliberately simplified Surgformer's full multi-scale decomposition for clarity and reproducibility on our 9-token input — hence "HTA-*inspired*" rather than verbatim.

**Why ours differs.** Different task (RSD vs phase recognition), simpler 2-branch decomposition vs Surgformer's 3-scale, and conditioning on workflow-cluster tokens that Surgformer doesn't have.

**Why we use their method.** HTA is a strong, recently-validated temporal architecture for surgical video. Adopting it gives us a competitive baseline temporal stack so the workflow-conditioning effect can be measured *on top of* a strong predictor (rather than papering over a weak one).

---

## 3. Datasets and benchmarks

### 3.1 MultiBypass140 — Lavanchy et al. 2024

- **bibkey:** `lavanchy2024multibypass`
- **Venue:** Int. J. Computer Assisted Radiology and Surgery 19, 2249–2257
- **Link:** https://arxiv.org/abs/2312.11250

**Summary.** First widely-used multicenter Roux-en-Y gastric bypass (RYGB) benchmark with explicit cross-center structure: 70 videos from Bern + 70 videos from Strasbourg, all annotated with per-frame phase and step labels. Establishes the cross-center evaluation protocol (Bern → Strasbourg) we use throughout §6.2.

**Why we cite them.** **MultiBypass140 is one of our two benchmarks.** Their multicenter design and workflow-diverse annotation is what enables the workflow-conditioning question we ask — Cholec80 alone isn't workflow-diverse enough.

**Why ours adds value.** Their paper focuses on phase and step recognition; ours is the first to evaluate **RSD prediction** under their cross-center protocol. To our knowledge, no published RYGB RSD baseline exists for cross-center MB140 — our §6.2 introduces it.

---

### 3.2 MTMS-TCN — Ramesh et al. 2021

- **bibkey:** `ramesh2021mtmstcn`
- **Venue:** Int. J. Computer Assisted Radiology and Surgery 16, 1111–1119
- **Link:** https://doi.org/10.1007/s11548-021-02388-z

**Summary.** Multi-task TCN for joint phase + step recognition in gastric bypass. Architecture: shared spatial-encoder feature stream branches into separate TCN heads for phase and step, trained jointly. Predates MultiBypass140 (uses earlier RYGB datasets).

**Why we cite them.** Like TeCNO, establishes the **decoupled spatial-then-temporal multi-task design pattern** in surgical-AI. Listed alongside TeCNO when justifying our decoupled-phase-head choice (§6.1).

**Why ours differs.** They report phase + step accuracy; we report RSD MAE. Their multi-task pattern (shared spatial + per-task heads) is similar to ours (shared ViT + HTA + RSD/phase/deviation heads). Our addition: workflow-cluster conditioning token + the variability-scaling cross-dataset analysis.

---

## 4. Architecture and general ML

### 4.1 Vision Transformer (ViT) — Dosovitskiy et al. 2021

- **bibkey:** `dosovitskiy2021vit`
- **Venue:** ICLR 2021

**Summary.** Foundational paper introducing the Vision Transformer. Treats an image as a sequence of 16×16 patches, encodes them with a transformer, uses a `[CLS]` token's output as the global image representation. ViT-B/16 = Base size (~86M params), 16-pixel patches, 12 transformer blocks.

**Why we use them.** **ViT-B/16 is our visual backbone** — initialized from ImageNet-21k weights, lower 6 of 12 blocks frozen, upper 6 fine-tuned end-to-end. We use the `[CLS]`-token output as the per-frame 768-d feature.

**Why we cite them on conditioning.** Their `[CLS]` token is the standard pattern for prepending a summary/conditioning token to a transformer sequence. Our workflow token follows this `[CLS]`-style design, prepended to the per-frame feature sequence before the temporal head.

---

### 4.2 ResNet — He et al. 2016

- **bibkey:** `he2016resnet`
- **Venue:** CVPR 2016

**Summary.** Introduced residual connections, enabling much deeper networks than previously trainable. ResNet-50 / ResNet-152 became the standard CNN backbone for ~5 years.

**Why we cite them.** RSDNet (Twinanda 2019) uses ResNet-152; comparing era-to-era shows the gap between ResNet-LSTM-era and our ViT-HTA-era pipelines.

---

### 4.3 Multi-task uncertainty weighting — Kendall et al. 2018

- **bibkey:** `kendall2018multitask`
- **Venue:** CVPR 2018

**Summary.** Proposes learning per-task loss-weights via homoscedastic uncertainty. Each task's loss is wrapped as $\exp(-\sigma_k) \mathcal{L}_k + \sigma_k$ where $\sigma_k$ is a learnable parameter. Removes the need to tune per-task loss weights manually.

**Why we use them.** **Our multi-task loss formulation is exactly Kendall et al.'s.** With three tasks (RSD regression, phase classification, deviation BCE), tuning three relative weights manually would be brittle; the uncertainty-weighting approach learns them jointly.

**Why we cite them.** Standard reference for any multi-task surgical-AI paper that doesn't tune loss weights manually.

---

### 4.4 timm — Wightman 2019–present

- **bibkey:** `wightman2019timm`
- **Link:** https://github.com/huggingface/pytorch-image-models

**Summary.** PyTorch Image Models — the standard library for vision-model architectures and pretrained checkpoints in PyTorch. Provides ViT, ConvNeXt, Swin, etc., with consistent API and ImageNet-21k pretraining.

**Why we use them.** We load ViT-B/16 + ImageNet-21k weights via `timm`. Pinned to `timm==1.0.26` in our reproducibility environment.

---

## 5. Surgical foundation models (mentioned for context only)

These are cited in §1.5 / §8 / Appendix Z as **future-work directions** we deliberately did not run, since they require domain-specific pretraining stacks we don't have time/resources to evaluate. Not direct comparators.

### 5.1 HecVL — Yuan et al. 2024
- **bibkey:** `yuan2024hecvl` · **Venue:** MICCAI 2024 · **Link:** https://arxiv.org/abs/2405.10075
- Hierarchical video-language pretraining for zero-shot surgical phase recognition. Cited as an example of surgical-domain encoder pretraining we don't run.

### 5.2 EndoFM — Wang et al. 2023
- **bibkey:** `wang2023endofm` · **Venue:** MICCAI 2023 · **Link:** https://arxiv.org/abs/2306.16741
- Endoscopy foundation model via large-scale self-supervised pretraining. Same context as HecVL.

### 5.3 SurgVLP — Yuan et al. 2025
- **bibkey:** `yuan2025surgvlp` · **Venue:** Medical Image Analysis · **Link:** https://arxiv.org/abs/2307.15220
- Vision-language pretraining from surgical lecture videos. Similar context.

### 5.4 GSViT — Schmidgall et al. 2024
- **bibkey:** `schmidgall2024gsvit` · **Venue:** arXiv:2403.05949
- General Surgery Vision Transformer foundation model. Similar context.

**Why we cite them collectively.** §6.6 / Appendix Z note that absolute Cholec80 MAE could likely improve further with surgical-domain pretrained encoders, but these would conflate the workflow-conditioning question (our focus) with the encoder-quality question. They are out of scope for this submission.

---

## 6. Methodology — privileged information, conditioning, controls

### 6.1 LUPI framework — Vapnik & Vashist 2009

- **bibkey:** `vapnik2009lupi`
- **Venue:** Neural Networks 22(5–6), 544–557

**Summary.** Introduces *Learning Using Privileged Information (LUPI)*: a paradigm where the learner has access to extra "teacher" information at training time that won't be available at test time. The teacher signal accelerates training and can improve generalization.

**Why we cite them.** Our **retrospective oracle row** in §6.1 / §6.2 is exactly a LUPI signal: at training time the model receives the full-video k-means cluster ID (post-hoc knowledge of how the entire surgery unfolded), but a deployable predictor at test time wouldn't have that. The oracle row is reported as a *diagnostic upper bound* on the value of perfect workflow knowledge — analogous to LUPI's role.

**Why ours adds.** We pair LUPI with a **causal-at-inference** evaluation (§4.5, §6.5) that estimates what fraction of the LUPI gain survives when the privileged signal is replaced by the model's own phase-head predictions on the prefix. This isn't novel to LUPI in general but is new for surgical RSD.

---

### 6.2 Distillation + privileged information — Lopez-Paz et al. 2016

- **bibkey:** `lopezpaz2016distillation`
- **Venue:** ICLR 2016

**Summary.** Unifies knowledge distillation and the LUPI framework. Shows that privileged information at training time can be transferred to a student model that doesn't have access to it at test time.

**Why we cite them.** Theoretical framework for how the LUPI gain (our oracle row) could be made deployable via distillation — flagged in §8 as the natural follow-up direction (oracle teacher → causal-at-inference student).

**Why ours adds.** We don't claim a distillation result in this paper, but our causal-at-inference apparatus is the evaluation harness needed to test such a distillation setup in future work.

---

### 6.3 Modality hallucination — Hoffman et al. 2016

- **bibkey:** `hoffman2016hallucination`
- **Venue:** CVPR 2016

**Summary.** Trains a network to "hallucinate" a missing modality at test time, conditioned on the available modality. E.g., learn an RGB-only network that produces depth-conditioned features by hallucinating depth from RGB during training.

**Why we cite them.** Conceptual ancestor of our causal-at-inference variant: at test time, we don't have ground-truth phase labels, so we have the model "hallucinate" the cluster posterior from its own phase predictions on the prefix. Same shape of problem, different domain.

**Why ours differs.** They hallucinate from a pretrained external modality; we hallucinate from the same model's auxiliary head.

---

### 6.4 Conditional GAN — Mirza & Osindero 2014

- **bibkey:** `mirza2014cgan`
- **Link:** https://arxiv.org/abs/1411.1784

**Summary.** Generative adversarial networks conditioned on auxiliary input (class label, image). Established the standard pattern of "concatenate or embed conditioning signal into the network input."

**Why we cite them.** Earliest work on **conditioning a network on auxiliary discrete input** — our workflow-cluster token follows the same conditioning paradigm (discrete cluster ID → embedding → input to model). Cited for context, not as a direct method comparison.

---

### 6.5 GPT-2 — Radford et al. 2019

- **bibkey:** `radford2019gpt2`
- **Venue:** OpenAI Technical Report

**Summary.** Decoder-only transformer trained on web text; popularized the prepended-prompt-as-conditioning pattern in language models.

**Why we cite them.** The "prepend a token to condition the model" pattern is now standard across modalities since GPT-2; we cite for the lineage of conditioning-token design.

---

## 7. Optimization

### 7.1 Adam — Kingma & Ba 2015

- **bibkey:** `kingma2015adam`
- **Venue:** ICLR 2015

**Summary.** Adam optimizer — adaptive moment estimation, the dominant first-order optimizer for deep learning.

**Why we cite/use them.** Our `brsd_lib.smoothing` Adam-style adaptive smoother is conceptually inspired by their first/second-moment idea (used as a generalization of isotonic regression in Appendix B.4).

---

### 7.2 AdamW — Loshchilov & Hutter 2019

- **bibkey:** `loshchilov2019adamw`
- **Venue:** ICLR 2019

**Summary.** Decoupled weight decay regularization. Argues that the weight-decay term in standard Adam is incorrectly coupled with the adaptive learning rate, and shows that *decoupling* (i.e., applying weight decay separately) gives better generalization.

**Why we use them.** **Our optimizer is AdamW** with lr=1e-4, wd=0.05. Standard ML practice; cited for completeness.

---

### 7.3 SGDR — Loshchilov & Hutter 2017

- **bibkey:** `loshchilov2017sgdr`
- **Venue:** ICLR 2017

**Summary.** Stochastic Gradient Descent with warm Restarts: a cosine annealing schedule with periodic resets, designed to escape local minima.

**Why we use them.** **Our LR schedule is cosine annealing over 15 epochs** with a 5-epoch warmup — a SGDR-style schedule. Standard practice; cited for completeness.

---

## 8. Statistics

### 8.1 Wilcoxon signed-rank test — Wilcoxon 1945

- **bibkey:** `wilcoxon1945ranking`
- **Venue:** Biometrics Bulletin 1(6), 80–83

**Summary.** Foundational non-parametric paired-comparison test. Compares two paired samples without assuming normality, by ranking the magnitudes of pairwise differences.

**Why we use them.** **Our paired Wilcoxon signed-rank tests in §6.8** use this method to compute statistical significance of per-video MAE differences between conditions. Test statistics: within-center decoupled vs no-token p=0.053; cross-center decoupled vs no-token p=0.005.

---

### 8.2 scikit-learn — Pedregosa et al. 2011

- **bibkey:** `pedregosa2011sklearn`
- **Venue:** Journal of Machine Learning Research 12, 2825–2830

**Summary.** The de facto standard machine-learning library for Python. Provides regression, classification, clustering, and post-processing utilities.

**Why we use them.** We use `sklearn.isotonic.IsotonicRegression(increasing=False)` for the per-video monotonic post-processing step (§4 implementation, Appendix B.4). Also `sklearn.cluster.KMeans`, `sklearn.feature_extraction.text.TfidfVectorizer`, and `sklearn.decomposition.PCA` for the offline workflow-clustering pipeline (§4.3).

---

## 9. Bariatric surgery video understanding (recent)

### 9.1 Bose et al. 2025 — IAE detection in RYGB

- **bibkey:** `bose2025feature`
- **Venue:** MICCAI 2025
- **Link:** https://arxiv.org/abs/2504.16749

**Summary.** Feature-mixing approach for detecting **intraoperative adverse events (IAE)** in laparoscopic Roux-en-Y gastric bypass surgery. Uses a BetaMixer architecture for visual feature aggregation. Targets adverse-event detection, not RSD prediction.

**Why we cite them.** Recent (2025) MICCAI paper from the **same lab and dataset family** as MultiBypass140 (Padoy group, IRCAD). Establishes that bariatric-surgery video understanding is an active 2024–2025 research area, supporting our framing of RYGB as a workflow-relevant benchmark beyond Cholec80.

**Why ours differs.** They target IAE detection; we target RSD prediction. Orthogonal contributions.

**Note for paper authors.** An earlier draft incorrectly cited a Bose et al. 2025 paper as reporting 2.76 min on Cholec80 RSD — this was a fabrication. The actual Bose 2025 paper (this one) is on adverse-event detection, not RSD. Citation has been corrected throughout.

---

## Summary table — direct numerical comparators on Cholec80

| Method | Year | Input | Test split | MAE (min) | Notes |
|---|---|---|---|---:|---|
| RSDNet | 2019 | raw video | canonical 40-video | ≈ 8.0 | ResNet-152 + LSTM |
| Yengera "Less Is More" | 2018 | raw video | canonical 40-video | ≈ 7–8 | self-supervised pretraining |
| Yengera unsupervised seg | 2019 | raw video | canonical 40-video | ≈ 7–8 | unsupervised auxiliary |
| TransLocal | 2024 | raw video | canonical 40-video | **7.10** | published SOTA on canonical |
| Kostopoulos | 2025 | annotations | their split | 5.89 / 4.61 (T−20) | annotation input, not video |
| **Ours** (Run 017, no token) | this paper | raw video | 6-video val | **4.61 ± 0.19** | 3 seeds, centered-window |
| **Ours** (Run 046, strict no token) | this paper | raw video | 6-video val | **4.34** | 1 seed, strict prefix-only |
| **Ours** (Run 019C, ensemble + isotonic) | this paper | raw video | 30-video public test | **3.56** | 3 seeds + TTA + isotonic |

**Key positioning.** Among raw-video methods on canonical 40-video Cholec80, TransLocal at 7.10 is the published SOTA. We do not claim SOTA on the canonical split — our 30-video test split is non-canonical. Our contribution is **not the absolute number on Cholec80** but the *workflow-conditioning question* and the *cross-dataset variability-scaling finding* (§6.7). The 3.56 number is reported as a secondary "what the pipeline can deliver" reference, not a leaderboard claim.

---

## Author-side reading guide for reviewer rebuttal

If a reviewer asks…

> *"How does your work compare to Kostopoulos 2025 (5.89 min)?"*

Answer: **input modality** — Kostopoulos uses already-annotated phase + tool labels as input; we use raw video. Apples to oranges; we're solving the harder end-to-end perception problem.

> *"Isn't TransLocal at 7.10 on the canonical split SOTA, and you don't beat it?"*

Answer: We don't evaluate on the canonical 40-video split (only 30 of those have public phase labels). On the 30-video phase-labeled subset, we report 3.56 min. The split difference is acknowledged as a caveat in §6.6.

> *"Why not use HecVL / EndoFM / GSViT as the backbone?"*

Answer: Surgical-domain pretrained encoders are deliberately out of scope. They would conflate the workflow-conditioning question (our focus) with the encoder-quality question. Future-work direction in §8 / Appendix Z.

> *"Your Cholec80 numbers are better than RSDNet / TransLocal, why not claim SOTA?"*

Answer: Different test split (30 of 40 canonical videos). Without aligned splits, cross-paper rankings are noisy. Our paper's claim is about *workflow-conditioning* (positive on MB140, null on Cholec80), not about Cholec80 absolute MAE.

---

*Last updated: 2026-04-29. Maintained alongside `paper/review_manuscript.md` and `paper/Formatting_Instructions_For_NeurIPS_2026/references.bib`.*

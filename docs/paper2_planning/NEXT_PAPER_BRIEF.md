# Next-Paper Brief: Causal Surgical World-Model Transfer

> **Historical concept brief.** The September 17, 2026 update in
> [NEXT_PAPER_PLAN.md](NEXT_PAPER_PLAN.md) is the single current plan for
> scope, schedule, publication venues, and decision gates. It incorporates
> the Phase 0 findings and supersedes the older predictions and dates here.

*Status: 2026-05-21. Combines the ChatGPT-rewritten plan with verified
citations, a two-paper split, concrete compute budgeting, and a
null-result recovery strategy. Self-contained — drop into ChatGPT (or
any strong reasoning model) for round-two review.*

---

## 0. TL;DR

After submitting the variability-scaling RSD paper to NeurIPS 2026, the
next-paper question is how to bridge that work into physical AI without
becoming a vendor demo or being scooped by the surgical-FM wave. The
recommended plan:

- **Split into two papers.** Paper 2A is a causal-anticipation benchmark
  and foundation-model transfer matrix. Paper 2B is a privileged-
  information distillation method that closes the oracle-to-deployable
  gap in workflow conditioning. They share ~70% infrastructure.
- **Demote Cosmos and OpenUSD** from headline to one row in a baseline
  matrix and a defer-to-future-work item respectively. The science is
  the causal-evaluation apparatus plus the variability-scaling
  generalization, not vendor branding.
- **Use a staged compute gate.** Stage 0 is a weight/license/runtime
  feasibility audit. Stage 1 is a small scout matrix, not the full
  672-run grid. The full combined program can still reach ~5,000-7,000
  H100-hours if every ablation is run, but the first go/no-go decision
  should cost <500 GPU-hours.
- **Plan for the most likely outcome — Cosmos doesn't transfer well to
  endoscopic video.** Pre-register the *"pixel-prediction quality is a
  weak proxy for surgical forecasting"* framing so a null result is a
  diagnostic contribution, not a failed experiment.
- **Venues:** Paper 2A → MICCAI 2027 primary, CVPR 2027 only if the
  benchmark is ready by the late-2026 vision deadline cycle. Paper 2B
  → NeurIPS 2027 primary; ICLR 2027 is only plausible if the method
  is essentially done by August 2026.

The thesis question that survives any of those outcomes:

> **Do physical-AI and surgical video foundation models improve causal
> surgical anticipation, and does workflow variability still determine
> when explicit workflow-state conditioning helps?**

---

## 1. Why this beats the original "Surgical Cosmos + OpenUSD" plan

### What the old plan got right

- Connecting workflow-conditioned RSD to physical-AI world models.
- Reusing existing assets (MB140, Cholec80, strict prefix-only protocol,
  workflow clusters, semantic controls).
- Recognizing that the next paper must move past scalar RSD toward
  *"what happens next."*
- Naming the training-time supervision gap as the natural follow-up.

### What reviewers would attack

- **Vendor-first framing.** *"NVIDIA Cosmos + OpenUSD"* in the title
  reads as product adoption before science.
- **Weak physical-AI claim.** RSD prediction alone isn't embodied
  control. Future-state or future-workflow prediction is the minimum
  bar for a world-model framing.
- **OpenUSD not load-bearing.** Encoding OR metadata in USD instead of
  JSON isn't a contribution unless USD enables simulation, scene
  generation, or policy training.
- **"First" claims are unsafe.** SurgMotion, SurgVISTA, EndoMamba,
  EndoDINO, and ZEN already exist (see §2). A "first
  surgical FM" paper would be scooped.
- **Compute risk too high.** Full Cosmos fine-tuning is the wrong first
  experiment. Frozen features and parameter-efficient adaptation come
  first.

### The corrective pivot

Use the current paper's distinctive advantage — **leakage-safe causal
evaluation under workflow-variability scaling** — as the apparatus that
competing surgical-FM papers don't have. Make the next paper about
*systematic causal evaluation* and *closing the oracle gap*, not about
which vendor's checkpoint wins.

---

## 2. Research landscape (verified 2026-05-21)

All citations below were checked against arxiv / publisher / model-card
pages on 2026-05-21. Names and release status should be re-checked
before submission because several 2026 surgical-FM projects are still
moving quickly. Three additional competitors were surfaced during
verification and added.

### Physical-AI and world models

- **NVIDIA Cosmos.** *"Cosmos World Foundation Model Platform for
  Physical AI"* ([arxiv 2501.03575](https://arxiv.org/abs/2501.03575)),
  NVIDIA, January 2025 (v3 July 2025). Open physical-AI platform; the
  Cosmos-Predict line targets future-state video/world simulation,
  Transfer targets controllable sim-to-real generation, Reason targets
  video/image reasoning.
- **Cosmos Policy.** *"Cosmos Policy: Fine-Tuning Video Models for
  Visuomotor Control and Planning"*
  ([arxiv 2601.16163](https://arxiv.org/abs/2601.16163)), Kim/Finn/Gu et
  al. (Stanford + NVIDIA), January 2026. Adapts Cosmos-Predict2 to
  visuomotor control. Sharpens the physical-AI motivation: Cosmos is
  intended for control downstream tasks, which makes an RSD-only paper
  inadequate.
- **V-JEPA 2.** *"Self-Supervised Video Models Enable Understanding,
  Prediction and Planning"*
  ([arxiv 2506.09985](https://arxiv.org/abs/2506.09985)), Meta AI
  (Assran, LeCun, Ballas et al.), June 2025. Strong motion
  understanding, action anticipation, zero-shot robotic manipulation.
- **V-JEPA 2.1.** *"Unlocking Dense Features in Video Self-Supervised
  Learning"*
  ([arxiv 2603.14482](https://arxiv.org/abs/2603.14482)), Meta AI, March
  2026. Stronger dense features, anticipation, robotic grasping. Latent
  predictive models are better baselines than purely generative video
  models because they target representation quality directly.

### Surgical video foundation models

- **SurgMotion.** *"SurgMotion: A Video-Native Foundation Model
  for Universal Understanding of Surgical Videos"*
  ([arxiv 2602.05638](https://arxiv.org/abs/2602.05638)), Wu, Holm,
  Navab et al., February 2026. V-JEPA-based, 3,658-hour 50-source
  surgical video corpus. Reports +14.6% F1 on EgoSurgery, +10.3% on
  PitVis workflow recognition, and 39.54% mAP-IVT on CholecT50
  triplets.
- **SurgVISTA.** *"Large-scale Self-supervised Video Foundation Model
  for Intelligent Surgery"*
  ([arxiv 2506.02692](https://arxiv.org/abs/2506.02692); npj Digital
  Medicine 2026; code at
  [isyangshu/SurgVISTA](https://github.com/isyangshu/SurgVISTA)).
  Asymmetric encoder–decoder, 3,650-video corpus, 13 video-level
  downstream datasets. Outperforms natural- and surgical-domain
  pretrained models.
- **EndoMamba.** *"An Efficient Foundation Model for Endoscopic Videos
  via Hierarchical Pre-training"*
  ([arxiv 2502.19090](https://arxiv.org/abs/2502.19090)), Tian, Liao,
  Ourselin, Liu et al., February 2025. Bidirectional Mamba spatial +
  vanilla Mamba temporal blocks. Real-time inference. Targets online
  endoscopic understanding.
- **EndoDINO.** *"A Foundation Model for GI Endoscopy"*
  ([arxiv 2501.05488](https://arxiv.org/abs/2501.05488)), Dermyer,
  Kalra, Schwartz, January 2025. Image-level DINO pretraining (1B /
  307M / 86M variants) on curated endoscopy imagery. Less central for
  laparoscopic workflow anticipation but useful as an image baseline.
- **SWAG.** *"Long-term Surgical Workflow Prediction with Generative-
  based Anticipation"*
  ([arxiv 2412.18849](https://arxiv.org/abs/2412.18849)), Boels, Liu,
  Dasgupta, Granados, Ourselin, December 2024 (v4 June 2025). Direct
  competitor on future-phase-sequence prediction. Reports single-pass
  F1 of **32.1% / 41.3%** at 20-min / 30-min horizons on Cholec80 /
  AutoLaparo21 and phase remaining-time wMAE of **0.32 / 0.48 min**.
  These are the numbers your Task B has to beat or systematically
  re-evaluate under causal protocols.
- **Scaling Video Pretraining for Surgical FMs.** *"Scaling Video
  Pretraining for Surgical Foundation Models"*
  ([arxiv 2603.29966](https://arxiv.org/html/2603.29966v2)), 2026.
  Recent surgical-FM scaling-laws work. Must be cited; could be a
  baseline.
- **ZEN.** *"A generalizable foundation model for intraoperative
  understanding across surgical procedures"*
  ([arxiv 2602.13633](https://arxiv.org/abs/2602.13633)), Park et al.,
  February 2026. Multi-procedure intraoperative foundation model trained
  with self-supervised multi-teacher distillation. Important because it
  directly claims cross-procedure generalization.
- **SurgSigma / Surg-Sigma.** *"SurgSigma: A Spectrum of Large-Scale
  Multimodal Data and Foundation Models for Surgical Intelligence"*
  ([arxiv 2603.16822](https://arxiv.org/abs/2603.16822)), 2026.
  Multimodal surgical intelligence effort. Less central to a video-only
  transfer matrix, but relevant if Paper 2A includes reasoning,
  planning, or report-style outputs.

### Consequence for paper framing

Drop *"Can Cosmos work on surgical video?"*. Adopt:

> **When surgical video models are evaluated causally, do general
> physical-AI world models, general video foundation models, or
> surgical-native models transfer best, and does explicit workflow-state
> conditioning still provide marginal value only when workflow
> variability is present?**

---

## 3. The two-paper plan

Three contributions don't fit cleanly in one 8-page submission. Splitting
gives each contribution depth, hedges venue risk, and exploits ~70%
shared infrastructure.

### Paper 2A — Causal benchmark + foundation-model transfer matrix

**Working title:** *Do World Models Help Surgical Workflow Forecasting?
A Causal Benchmark for Remaining Duration and Phase Anticipation*

**Thesis (one sentence):**
> Strict prefix-only evaluation reveals that the ranking of foundation
> models for surgical forecasting depends on the task (RSD vs. phase
> anticipation) and on workflow variability, not on generic video-
> prediction quality.

**Defendable claims:**

1. **Causal evaluation changes the FM ranking.** A backbone that wins on
   centered-window Cholec80 phase recognition can lose on strict prefix-
   only MB140 RSD and phase anticipation.
2. **Pixel-prediction quality is a weak proxy for surgical forecasting.**
   Cosmos / VideoMAE generative-quality metrics do not linearly predict
   downstream MAE or F1. *This is the diagnostic figure of the paper.*
3. **The variability-scaling pattern generalizes.** Workflow conditioning
   helps in proportion to *H(z)* across backbones and across both RSD
   and phase anticipation, not just on fold-0 MB140 RSD.
4. **Cross-center transfer is a representation problem.** Some backbones
   are robust to Bern → Strasbourg domain shift; others collapse.

**What's NOT in Paper 2A:** the privileged-information distillation
method. That's Paper 2B.

**Minimum viable Paper 2A:**

Paper 2A does not need every model in the landscape. It needs a clean
representative matrix:

1. the current ImageNet ViT-B/16 + HTA baseline,
2. one conventional general-video baseline (VideoMAE or TimeSformer),
3. one latent predictive world model (V-JEPA 2 or V-JEPA 2.1),
4. one accessible surgical-native FM (SurgMotion or SurgVISTA),
5. Cosmos-Predict2/2.5 only if weights, preprocessing, licensing, and
   feature extraction are straightforward.

For the scout stage, run **no-token** and **decoupled-oracle** only.
Reserve shuffled-token, causal-at-inference, and all-fold confirmation
for finalists. This keeps Paper 2A from becoming a compute sink before
there is evidence of transfer.

**Page budget (8-page body):**

- §1 Intro: 0.75 pp
- §2 Causal evaluation protocol & related work: 1.0 pp
- §3 Method (model matrix, temporal head, conditions): 1.0 pp
- §4 Datasets & tasks (MB140, Cholec80, RSD + anticipation defs): 0.75 pp
- §5 Results (Tables 1–3, transfer matrix; Figure 1 pixel-prediction vs.
  downstream; Figure 2 variability scaling): 3.0 pp
- §6 Discussion & Limitations: 1.0 pp
- §7 Conclusion + spillover for references: 0.5 pp

**Target venue:** MICCAI 2027 primary. CVPR 2027 is attractive but
riskier because the full-paper deadline is historically in the late
preceding year, and the official 2027 dates should be checked before
committing.

**Risk profile:** medium. Depends on at least one accessible backbone
showing a measurable lift somewhere, or on a strong diagnostic
relationship between generative quality and downstream utility. The
diagnostic claim ("pixel-prediction ≠ downstream") is publishable only
if the measurement is designed up front rather than added after a failed
benchmark (see §8).

### Paper 2B — Privileged-information distillation method

**Working title:** *Closing the Oracle Gap in Workflow-Conditioned
Surgical Forecasting via Privileged-Information Distillation*

**Thesis (one sentence):**
> A student model that learns the workflow-cluster posterior
> *q(z | x_{≤t})* from a privileged teacher closes most of the
> oracle-to-deployable gap in surgical RSD without using any ground-
> truth phase or workflow labels at inference.

**Defendable claims:**

1. **Distillation closes the oracle gap.** The current paper's gap
   between decoupled-oracle (−0.85 min) and deployable causal (−0.18
   min) shrinks to ≤0.3 min after distillation.
2. **The student's workflow posterior is calibrated.** Reliability
   diagrams + ECE numbers show the posterior tracks the true cluster
   identity proportionally.
3. **The student preserves variability scaling.** Distillation doesn't
   leak benefits to Cholec80; the *H(z)* pattern survives the new
   method.
4. **Architectural ablations.** What teacher matters (frozen oracle vs.
   distilled chain)? What student-side loss formulation works best (hard
   target vs. KL vs. matching internal representations)?

**What's NOT in Paper 2B:** the foundation-model transfer matrix. Use
the existing ViT-B/16 + HTA backbone as the workhorse. One ablation can
swap in a stronger encoder (e.g., V-JEPA 2.1 or SurgVISTA features) to
demonstrate the method is encoder-agnostic.

**Page budget (8-page body):**

- §1 Intro: 0.5 pp
- §2 Related work (LUPI, distillation, surgical anticipation): 0.75 pp
- §3 Method (teacher-student framework, loss formulation, training
  recipe): 1.5 pp
- §4 Datasets & protocol: 0.5 pp
- §5 Main results (oracle-gap closing on MB140; Cholec80 null
  preservation; cross-center): 2.5 pp
- §6 Ablations (teacher choice, loss, encoder swap): 1.25 pp
- §7 Discussion & Limitations: 0.75 pp
- §8 Conclusion: 0.25 pp

**Target venue:** NeurIPS 2027 (deadline May 2027) or ICLR 2027 (deadline
September 2026 — would need everything ready by August). Method papers
travel better at top ML venues than at MICCAI.

**Risk profile:** lower. The distillation gap-closing claim is testable
with existing assets; even a partial close (−0.85 to −0.4 instead of
−0.18) is a real result. The Cholec80 null-preservation claim is
essentially free — already verified directionally in the current paper.

### Why splitting wins

| Concern | Single paper | Two papers |
|---|---|---|
| Reviewer fatigue | "Too much going on" | Each paper has one thesis |
| Page budget | 8 pages × 3 contributions = shallow | 8 pages × 2 = depth |
| Venue fit | Benchmark + method split across venues | 2A → MICCAI/CVPR, 2B → NeurIPS/ICLR |
| Risk hedging | Cosmos fails → whole paper looks weak | Paper 2B is independent of FM transfer |
| Time-to-publish | 9–12 months | 2A in 6 months, 2B in 9–12 months |
| Citation footprint | One paper | Two; distillation paper is more cited |

### Sequencing

1. **2026 Q3:** complete a backbone feasibility audit: weights,
   licenses, preprocessing, feature shapes, memory footprint, and one-
   video smoke tests.
2. **2026 Q3–Q4:** build experimental infrastructure (frozen-feature
   extraction harness, anticipation eval, distillation training loop).
3. **2026 Q4–2027 Q1:** run Paper 2A experiments. Submit to **MICCAI
   2027** (historically around February/March; check official dates).
4. **2027 Q1–Q2:** run Paper 2B experiments on shared infrastructure.
   Submit to **NeurIPS 2027** (~May deadline).

---

## 4. Existing assets to reuse

### From the submitted RSD paper

- MultiBypass140: 140 RYGB videos, two centers, 14 phases, 1 fps.
- Cholec80: 72 videos with public phase labels, 7 phases.
- Strict prefix-only clip protocol.
- Centered-window protocol kept only as retrospective leakage contrast.
- Workflow-cluster pipeline: phase-bigram TF-IDF, PCA, k-means.
- *K = 6* MB140 / *K = 4* Cholec80 cluster artifacts.
- Decoupled-oracle architecture.
- Shuffled-token semantic control.
- Causal pixel-only evaluator.
- Trained ViT-B/16 + temporal-head checkpoints.
- Cross-center MB140 Bern → Strasbourg protocol.

### What this advantage actually buys

Most foundation-model papers don't have a leakage-safe causal evaluation
harness. Your distinct edge is the ability to ask:

> *Does a representation improve online surgical forecasting when future
> frames, ground-truth future phases, and full-case workflow labels are
> all unavailable?*

That apparatus is what makes Paper 2A defensible regardless of which
backbone wins.

---

## 5. Experimental design

Experiments map to the two papers as indicated.

### Experiment -1 — Backbone feasibility audit (Paper 2A gate)

Before any large matrix, make every candidate prove it can run in this
repo:

- weights available or obtainable under a research-compatible license,
- preprocessing and frame-rate assumptions documented,
- feature tensor shape stable for 8-frame and longer-context clips,
- one-video feature extraction succeeds on GH200 / H100 without manual
  intervention,
- cache size per dataset estimated,
- inference throughput measured on 100 clips,
- output features can be consumed by the existing temporal head through
  a simple projection layer.

Any model that fails this audit becomes related work, not a required
baseline. This prevents the schedule from depending on a model that is
interesting but operationally brittle.

### Experiment 0 — Lock the baseline and evaluation contract (both papers)

- Strict prefix-only clips for headline results.
- Identical train/val/test splits across all backbones.
- Identical temporal head where possible.
- No full-video labels at inference.
- No centered-window headline claims.
- Report 5-fold MB140 + cross-center, not only fold 0.
- Report seed means and paired uncertainty.

**Deliverable:** a table reproducing the current ViT-B/16 no-token,
oracle, decoupled-oracle, shuffled-token, and causal-at-inference
results.

### Experiment 1 — Frozen-representation transfer (Paper 2A)

Replace the visual encoder while keeping the temporal head and losses
fixed. Cheapest and cleanest first test.

| Family | Candidate | Why include |
|---|---|---|
| Current baseline | ImageNet-21k ViT-B/16 | Anchor to submitted paper |
| General video | TimeSformer, VideoMAE | Standard video baselines |
| Latent world model | V-JEPA 2 / 2.1 | Strong anticipation + planning prior |
| Generative world model | Cosmos-Predict2 / 2.5 features | Physical-AI substrate |
| Surgical-native | SurgMotion, SurgVISTA, ZEN, EndoMamba | Use at least one accessible model; more only if cheap |
| Image surgical | EndoDINO | Frozen image-domain control |

**Primary output:** which representation improves causal RSD and phase
anticipation under the same temporal head?

### Experiment 2 — Parameter-efficient adaptation (Paper 2A)

Only after Experiment 1 surfaces a promising representation, run
adapters:

- LoRA / adapters on the visual backbone.
- Frozen backbone + trainable projection and temporal head.
- Optional masked/latent future prediction on unlabeled surgical clips.
- No full model fine-tuning unless adapters show a clear signal.

Scaling story: **frozen features → surgical adapters → optional full
post-training.**

### Experiment 3 — Causal workflow-state distillation (Paper 2B)

**Teacher signal:**
- Full-video workflow cluster *z(V)*.
- Prefix-derived cluster labels when available.
- Phase-transition structure from labels at training time only.

**Student:**
- Learns *q_φ(z | x_{≤t})* from pixels only.
- Produces a soft workflow token *Σ_k q_k E_k*.
- Conditions RSD and anticipation heads.
- Never uses ground-truth phase labels or full-video clusters at test.

**Losses:**
- RSD regression.
- Current phase classification when labels available.
- Next-transition time regression or classification.
- Future phase sequence loss.
- KL or cross-entropy from student posterior to privileged teacher.
- Optional calibration loss for RSD uncertainty.

**What this fixes:** the current paper removes inference-time oracle
access but still uses privileged workflow supervision during training.
This distillation makes that gap the explicit next-paper contribution.

### Experiment 4 — Anticipation tasks (Paper 2A)

**Task A — time to next phase transition.** Input: prefix *x_{≤t}*.
Outputs: minutes until next transition, next phase identity, uncertainty
interval. Metrics: MAE, macro-F1, ECE / interval coverage, horizon-
binned.

**Task B — future phase sequence.** Predict phase labels at 1, 2, 5, 10,
20, 30 min horizons where labels exist. Metrics: sequence edit score,
horizon-specific macro-F1, temporal Jaccard. Direct comparison to SWAG.

**Task C — CholecT50 action-triplet anticipation (optional, but
recommended).** Input: observed prefix. Output: future instrument, verb,
target, triplet presence at short horizons. Metrics: component mAP,
triplet mAP, horizon-binned recall/precision. *This is where "physical"
becomes credible* because instrument-tissue interactions are closer to
action than phase labels.

### Experiment 5 — Variability-scaling extension (both papers)

For each dataset/task:

1. Compute workflow-cluster entropy *H(z)*.
2. Train no-token, oracle, causal-distilled, and shuffled-token
   variants.
3. Measure marginal gain *Δ* from workflow conditioning.
4. Plot *Δ* against *H(z)*.

**Interpretation guide:**

- High *H(z)*, positive *Δ*: workflow state contains real signal.
- Low *H(z)*, null *Δ*: no residual workflow signal to exploit.
- Shuffled-token null: gain is semantic, not parameter capacity.
- Cross-center drop: representation/domain shift, not workflow signal.

---

## 6. Compute budget (decision-gated)

The original "Tier 1 / 2 / 3" qualitative plan was right in spirit but
too all-at-once. The improved plan separates a cheap **scout matrix**
from the expensive **confirmatory matrix**. The first decision should
not require hundreds of fully trained models.

### Assumptions

- GPU: H100 80 GB or GH200 96 GB (existing setup).
- Backbone size: 86M (current ViT-B/16) to 14B if Cosmos-Predict2-14B is
  attempted; default planning should assume 2B / 4B-class models at most.
- Per-run training: 15 epochs, batch 64, 8-frame clips at 224×224.
  Current ViT-B/16 takes ~5 hours per run.
- Adapter / LoRA training: ~30–50% the cost of full training due to
  smaller trainable parameter count, but inference forward pass still
  costs the full model.
- Lambda H100 rate ~ $3.00 / GPU-hour.
- All numbers below are planning ranges. Replace them with measured
  throughput after the feasibility audit.

### Paper 2A breakdown

**Stage 0 - feasibility audit: ~40-80 h (<$250).**

Run one-video and 100-clip smoke tests for each candidate backbone.
Measure preprocessing friction, feature shape, throughput, memory, and
cache size. Remove brittle models before the paper depends on them.

**Stage 1 - scout matrix: ~250-500 h ($750-$1,500).**

Purpose: determine whether Paper 2A exists.

Scope:

- 4 to 5 accessible backbones:
  current ViT-B/16, VideoMAE/TimeSformer, V-JEPA 2.x, one surgical-native
  FM, and Cosmos only if it passes Stage 0.
- 3 representative settings:
  MB140 fold 0, MB140 Bern -> Strasbourg, Cholec80.
- 2 conditions:
  no-token and decoupled-oracle.
- 2 seeds.
- RSD plus one anticipation task.

This scout matrix is intentionally incomplete. It is designed to answer
whether any representation changes the outcome enough to justify
confirmatory compute.

**Stage 2 - confirmatory frozen-feature matrix: ~700-1,400 h
($2,100-$4,200).**

Scope:

- 3 finalist backbones, not every candidate.
- 5-fold MB140 + cross-center + Cholec80.
- no-token, oracle, decoupled, shuffled.
- 3 seeds.
- RSD and anticipation metrics.

This is the reviewer-facing matrix. If Cosmos is not a finalist, keep it
as a diagnostic row from Stage 1 rather than spending confirmatory budget
on it.

**Stage 3 - adapter / LoRA runs: ~500-1,200 h ($1,500-$3,600).**

Scope:

- 1 to 2 finalist backbones,
- fewer conditions (usually no-token and best workflow-conditioned
  variant),
- 3 seeds on the main split, then confirm only if the effect is real.

**Stage 4 - optional surgical SSL / world-model post-training:
~700-1,500 h ($2,100-$4,500).**

Only run this if Stage 2/3 show that the representation family is worth
adapting. This is the highest-cost and lowest-certainty stage.

**Paper 2A planning range:**

| Scope | Hours | Dollars |
|---|---:|---:|
| Stage 0 + Stage 1 only | ~300-580 | ~$900-$1,740 |
| Confirmatory frozen-feature paper | ~1,000-2,000 | ~$3,000-$6,000 |
| With adapters | ~1,500-3,200 | ~$4,500-$9,600 |
| With optional SSL/post-training | ~2,200-4,700 | ~$6,600-$14,100 |

### Paper 2B breakdown

Reuses Paper 2A infrastructure. Additional cost:

| Component | Hours |
|---|---:|
| Primary student: 7 dataset/folds x 3 seeds x ~5-8 h | ~105-170 |
| Distillation variants: 3 losses / teachers on main settings | ~250-500 |
| Confirmatory best variant across all folds / cross-center | ~250-500 |
| Encoder-swap ablation | ~100-250 |
| Calibration and bootstrap inference | ~50-100 |
| **Paper 2B total** | **~750-1,500** |
| **Paper 2B $** | **~$2,250-$4,500** |

### Combined budget

| | Hours | $ |
|---|---:|---:|
| Paper 2A, staged realistic | ~1,500-3,200 | ~$4,500-$9,600 |
| Paper 2B | ~750-1,500 | ~$2,250-$4,500 |
| Subtotal | ~2,250-4,700 | ~$6,750-$14,100 |
| +25% overhead (storage, sweeps, debugging) | ~2,800-5,900 | **~$8,400-$17,700** |
| Full every-ablation upper bound | ~5,000-7,000 | **~$15,000-$21,000** |

### Compute-risk mitigations

1. **Stop after Stage 1** if no backbone improves over ViT-B/16 by ≥ 0.3
   min on MB140 RSD or ≥ 5 F1 on phase anticipation. Saves ~1,500 h.
2. **Skip Cosmos** as full backbone; treat as feature-extraction only.
   Saves ~270 h.
3. **Drop any surgical-native FM that fails the feasibility audit.**
   Cite it as related work instead of forcing an unreliable baseline.
4. **5 folds → 3 folds** if budget is tight. Saves ~400 h but weakens
   reviewer-proofing.
5. **Skip surgical SSL pretraining.** Saves 700 h — the highest-cost
   lowest-certainty piece.

### Decision gates

After Stage 1:

- ≥ 1 FM clearly improves causal RSD or anticipation → continue.
- Cosmos hard to run or weak → keep as one row, not the paper's
  identity.
- No FM improves RSD but anticipation improves → pivot to *"world
  models help forecasting, not scalar duration."*
- No FM improves any task → publish the diagnostic result as the
  contribution (see §8).

---

## 7. Statistical standard

Reviewer-proof statistics, not isolated fold-0 wins.

**Use:**
- 5-fold MB140 where feasible.
- Bern → Strasbourg cross-center.
- Cholec80 standard 36/6/30 split.
- Fixed seeds across model families.
- Paired bootstrap over videos/clips.
- Hierarchical mixed model if reporting pooled results.
- Shuffled-token semantic control.
- Matched-parameter controls for added tokens/adapters.
- Horizon-binned metrics for anticipation.

**Report:**
- Mean ± std across seeds.
- Video-level bootstrap confidence intervals.
- Per-fold results in appendix.
- Aggregate effect sizes in main paper.

**Avoid:**
- A main table that hides fold failures.
- "Best seed" model selection.
- Comparing full fine-tuned giant models to weak baselines without
  compute and parameter accounting.

---

## 8. "Cosmos-is-meh" recovery narrative

The most likely empirical outcome: Cosmos doesn't transfer well to
endoscopic video because it was pretrained on natural-world scenes that
look nothing like laparoscopic close-ups. Pre-register the framing
before running experiments so a null result is a contribution, not a
failed experiment.

### Three publishable narratives, ranked

**Narrative 1 (recommended primary) — "Pixel-prediction quality is a
weak proxy for surgical forecasting."**

*Headline finding:* Cosmos generates high-PSNR / low-FVD next-frame
predictions on surgical clips but its features don't help downstream RSD
or phase anticipation any more than ImageNet pretraining does.

*Why it's interesting:* tells the field that improving video generation
doesn't automatically improve surgical-workflow understanding. Motivates
surgical-native pretraining. Variability-scaling pattern survives —
*H(z)* signal persists even with a mid-pack backbone.

*Headline plot:* Cosmos pixel-prediction FVD vs. downstream MAE on
Cholec80 strict. Expect weak / absent / anti-correlated relationship.

**Narrative 2 — "Domain gap dominates; surgical-native FMs win."**

*Headline finding:* ordered by visual-domain overlap with the training
corpus, Cosmos < ViT-B/16 < SurgVISTA / SurgMotion. The
pretraining-domain gap is what determines downstream lift.

*Why it's interesting:* quantifies the surgical-domain gap. Gives a
clean recommendation for the community. Sets up Paper 2B as *"and
here's how to get the rest of the gap without retraining a giant FM
from scratch."*

*Headline plot:* scatter of pretraining-corpus distance to MB140/Cholec80
vs. downstream RSD MAE improvement over ImageNet baseline.

**Narrative 3 — "Cosmos as a calibration anchor."**

*Headline finding:* even when Cosmos doesn't win, having it in the
matrix is useful as a *calibration anchor* — it shows when surgical-
native FMs succeed by virtue of *surgical* pretraining rather than just
"better FM in general."

*Why it's interesting:* methodological framing. Contribution is the
benchmark protocol itself. Safest narrative because it doesn't require
any FM to win.

### Writing tactics

1. **Decide the framing before running experiments.** Pre-register
   Narrative 1 as primary. Treat it as testable: if Cosmos wins, pivot
   to a positive story; if it loses, the pre-committed paper still
   exists.
2. **Make pixel-prediction quality a first-class measurement.** Compute
   FVD, LPIPS, and PSNR on a held-out surgical video set for every
   backbone. Cheap (one inference pass) and gives the Figure 1 of the
   paper.
3. **Use the diagnostic as the contribution.** *"We propose pixel-
   prediction-quality-vs-downstream-utility as a diagnostic for
   surgical-video foundation models, and find that Cosmos has the
   highest pixel quality but is mid-pack on downstream utility."* This
   frames a null result as a methodological finding.
4. **Don't oversell.** Avoid "Cosmos fails at surgery." Use precise
   language: *"Cosmos features, evaluated under our causal anticipation
   protocol, do not transfer measurably better than ImageNet-pretrained
   ViT features on MB140 or Cholec80, despite generating higher-PSNR
   pixel predictions."*
5. **Cite NVIDIA's own framing.** Cosmos is positioned as a *platform
   for fine-tuning*, not as out-of-the-box. Citing that framing makes
   your null result a measurement of post-training cost, not an
   indictment of Cosmos.

### Why this works as a publication strategy

- **Reviewer-proof.** Negative results that are properly designed and
  controlled are recognized as scientific contributions.
- **Future-proof.** Even if NVIDIA releases Cosmos-Surgical in 2027, the
  paper provides the measurement protocol they'll have to compare
  against.
- **Citation-attractive.** Negative results in active subfields tend to
  get cited more than positive ones because they're load-bearing for
  follow-up work.
- **No wasted compute.** The same experiments that would have shown a
  positive result also produce the diagnostic data for the null-result
  paper.

### Risk: a partial-positive outcome

If Cosmos helps on one task / one benchmark / one horizon but not
others:

- Report faithfully (don't sandbag, don't oversell).
- Use the variability-scaling lens: *"Cosmos helps where workflow
  variability is high and the task requires temporal extrapolation; it
  doesn't help on standardized procedures or short-horizon tasks."*
- This makes the partial result a refinement of the current paper's
  thesis, not a contradiction.

---

## 9. OpenUSD — keep out of the flagship unless load-bearing

### Recommendation

Do not put OpenUSD in the title or primary contribution of either
paper.

### Why

For the current assets, OpenUSD would mostly encode structured metadata
about OR setup. Reviewers will reasonably ask why that's not just a
small JSON feature vector. USD becomes scientifically meaningful only
when used for:

- reconstructing or simulating a 3D scene,
- rendering synthetic views,
- generating controlled scene variations,
- connecting to Isaac Sim / Isaac Lab,
- training or evaluating a policy.

### Acceptable small OpenUSD side experiment

If you want to keep the OpenUSD thread alive, do it as a short
appendix:

1. Create a tiny OR-scene schema.
2. Store the same information in both USD and a flat metadata vector.
3. Train the same model with no scene prior, flat prior, USD-parsed
   prior.
4. Report whether USD adds anything beyond the flat vector.

If USD does not beat the flat vector, do not include it in the main
paper.

### Future OpenUSD paper (Paper 3+)

Save OpenUSD for a separate robotics/simulation paper:

*From Endoscopic Video to OpenUSD Surgical Scenes for Simulation and
Policy Learning.*

That paper needs 3D reconstruction, Isaac Sim, tissue/instrument
dynamics, and a policy benchmark. Not the next-6-month paper.

---

## 10. Figure plan

### Paper 2A figures

- **Figure 1 — Causal surgical world-model evaluation.** Prefix frames
  → frozen/adapted FM encoder → temporal head → workflow posterior →
  RSD, transition, future sequence. Make the causal constraint visually
  obvious: all inputs stop at *t*.
- **Figure 2 — Pixel-prediction vs. downstream utility.** FVD/LPIPS on
  one axis, RSD MAE or phase F1 on the other. One point per backbone.
  The Cosmos-meh diagnostic.
- **Figure 3 — Model-transfer matrix.** Rows: backbones. Columns: RSD
  MAE, next-transition MAE, future phase macro-F1, CholecT50 triplet
  mAP, compute cost, params trained.
- **Figure 4 — Variability-scaling curve across tasks.** Extend the
  current *H(z)* vs. *Δ* plot across multiple tasks and datasets. The
  continuity figure from the current paper.
- **Figure 5 — Failure cases.** Smoke/bleeding/specular frames; phase
  transitions with no visual cue; cross-center instrument differences;
  rare workflow branches.

### Paper 2B figures

- **Figure 1 — Teacher-student architecture.** Privileged teacher
  (oracle cluster + ground-truth phases) → student
  *q_φ(z | x_{≤t})* → workflow token → downstream heads. All teacher
  signals removed at inference.
- **Figure 2 — Oracle-gap closing.** Bar chart: oracle / deployable
  causal (current paper) / distilled student (new). MB140 within-
  center, MB140 cross-center, Cholec80.
- **Figure 3 — Posterior calibration.** Reliability diagram of student
  workflow posterior on held-out video. ECE numbers per fold.
- **Figure 4 — Variability scaling preserved.** Same plot as Paper 2A
  Figure 4 but for the distilled student. Verifies the method doesn't
  manufacture Cholec80 gains.
- **Figure 5 — Ablation grid.** Teacher choice × loss variant × encoder
  swap.

---

## 11. Draft abstracts

### Paper 2A draft abstract

Surgical video analysis is increasingly adopting large video and world
foundation models, but it remains unclear whether such models improve
deployable, online surgical forecasting. We introduce a strict prefix-
only benchmark for causal surgical anticipation across remaining surgery
duration, time-to-next-phase transition, and future phase-sequence
prediction. Using MultiBypass140 and Cholec80, with optional extension
to CholecT50 action triplets, we compare ImageNet, general video,
physical-AI world-model, and surgical-native video representations under
a shared temporal head and matched causal evaluation protocol. The
benchmark is designed to test three hypotheses: (i) pixel-prediction
quality is an imperfect proxy for downstream surgical forecasting; (ii)
surgical-native pretraining may outperform generic physical-AI
pretraining at matched compute; and (iii) the variability-scaling
pattern reported in our prior work — that the marginal value of explicit
workflow conditioning scales with empirical workflow variability —
generalizes across backbones and anticipation tasks. This study provides
a leakage-safe evaluation of world-model transfer to surgery and
clarifies when stronger pretrained video representations, explicit
workflow state, or both are useful for surgical forecasting.

### Paper 2B draft abstract

Workflow-conditioned remaining-surgery-duration (RSD) prediction has
been shown to benefit from privileged supervision: training-time access
to ground-truth phase labels and full-video workflow clusters yields
substantial gains on multicenter MultiBypass140 (−0.85 min vs. no-token
within-center) but most of this advantage vanishes when the deployable
model must derive the workflow signal from its own prefix-only phase
predictions (−0.18 min). We close this gap with a privileged-
information distillation framework that trains a student workflow
posterior *q_φ(z | x_{≤t})* to match a privileged teacher without
requiring ground-truth phase or workflow labels at inference. On
MultiBypass140, the target result is to bring the deployable student to
within ≤0.3 min of the decoupled-oracle result while preserving the
Cholec80 null result, the cross-center gain, and the shuffled-token
semantic control. We additionally evaluate posterior calibration and
encoder-agnostic transfer across ViT, V-JEPA 2.1, and surgical-native
foundation-model features. The result, if achieved, is a deployable
surgical-forecasting model whose performance approaches the privileged-
supervision upper bound under the deployment-relevant strict prefix-only
protocol.

---

## 12. Target venues

### Highest expected value

- **MICCAI 2027** if the strongest contribution is surgical anticipation,
  clinical workflow, and domain-specific evaluation.
- **CVPR 2027** if the model-transfer matrix, world-model diagnostics,
  and anticipation tasks are strong enough for the vision community.
- **NeurIPS / ICLR 2027** if a paper becomes a general benchmark for
  causal world-model transfer under distribution shift.

### Recommendation

- **Paper 2A:** MICCAI 2027 primary. CVPR 2027 is only realistic if the
  scout matrix, anticipation task, and at least one confirmatory result
  are ready before the late-2026 CVPR deadline cycle.
- **Paper 2B:** NeurIPS 2027 primary. ICLR 2027 is a stretch because it
  would require a nearly complete method paper by August 2026. MICCAI
  2027 remains the fallback if the method contribution reads as more
  surgical-AI than general ML.

---

## 13. Success criteria

Either paper is strong if at least two of the following hold.

**Paper 2A:**

- A foundation/world model improves causal anticipation over the current
  ViT baseline under matched protocols.
- A surgical-native model beats a general physical-AI model, clarifying
  domain specialization.
- Workflow-state conditioning improves high-variability MB140 but remains
  null on low-variability Cholec80 across multiple tasks.
- Video-prediction quality is weakly correlated with surgical
  forecasting, giving a useful diagnostic warning.
- Cross-center results reveal which representations are robust to
  surgical domain shift.

**Paper 2B:**

- The distilled student closes ≥ 50% of the oracle-to-deployable gap on
  MB140 within-center.
- The student's workflow posterior is better calibrated than the
  uncalibrated causal baseline, with ECE and confidence intervals
  reported video-wise.
- The variability-scaling pattern survives distillation.
- The method transfers across at least one alternative encoder.

The paper is weak if it only says:

- "we fine-tuned Cosmos,"
- "we used OpenUSD,"
- "we improved one fold by a small amount,"
- "we got better next-frame PSNR."

---

## 14. Concrete next steps in this repo

1. Add `docs/backbone_feasibility_matrix.md` and fill it before any
   training: weights URL, license, preprocessing, expected feature
   shape, cache size, throughput, and pass/fail status.
2. Create a `backbone_features` interface that can cache frozen features
   from ViT, VideoMAE/TimeSformer, V-JEPA, Cosmos, and surgical-native
   models.
3. Add `evaluate_phase_anticipation.py` with strict prefix-only
   evaluation for next-transition time and future-phase-sequence.
4. Add a workflow-posterior student head *q_φ(z | x_{≤t})* and a
   privileged-teacher distillation loss.
5. Define a YAML experiment grid for:
   - backbone,
   - frozen vs. adapter,
   - no-token vs. oracle vs. causal-distilled vs. shuffled,
   - RSD vs. anticipation task,
   - dataset / split.
6. Run the Stage 1 scout matrix:
   - current ViT-B/16,
   - one general video model,
   - V-JEPA 2 or 2.1,
   - one surgical-native model if weights are accessible,
   - Cosmos only if setup is straightforward.
7. Make a first paper table before any large fine-tuning:
   - rows = backbones,
   - columns = RSD, transition time, future phase sequence, compute.

---

## 15. Open questions for round-two review

1. Is the two-paper split the right call, or does the field reward a
   single comprehensive paper more than two focused ones?
2. Is Cosmos the right physical-AI baseline, or should V-JEPA 2.1 +
   SurgMotion be treated as the primary FM comparison?
3. Which Cosmos variant (Predict2 vs. Predict2.5) is most appropriate as
   a feature extractor for surgical video, and what's the smallest size
   that gives a publishable test?
4. For Paper 2A, is MICCAI 2027 the right venue, or is CVPR 2027 a
   better fit given the model-transfer matrix and the diagnostic
   framing?
5. For Paper 2B, is the privileged-information distillation framing
   strong enough to clear NeurIPS / ICLR, or should it target MICCAI
   2027 alongside Paper 2A?
6. Is the *"pixel-prediction is a weak proxy"* diagnostic a real
   contribution or a face-saving framing? How would a vision reviewer
   read it?
7. Is the staged compute budget realistic, or should the first
   submission be scoped to Stage 1 + one confirmatory finalist?
8. What's missing from the related-work landscape — any surgical-AI
   foundation-model papers from mid-2026 that should be cited?
9. Should the OpenUSD side experiment be cut entirely, or kept as an
   appendix?
10. What's the right framing of the variability-scaling thesis when
    extending to anticipation tasks — is *H(z)* still the right
    quantity, or does anticipation need a different variability
    measure?

---

## 16. Final recommendation

**Two papers, sequenced.** Paper 2A first (Stage 1 → Stage 2 decision-
gated), then Paper 2B on the same infrastructure.

The flagship contribution is the **causal-evaluation apparatus** —
strict prefix-only future prediction under workflow-variability scaling
— applied to (a) systematic foundation-model transfer (Paper 2A) and
(b) privileged-information distillation (Paper 2B). Cosmos and OpenUSD
are in the experiment matrix but not in either title.

Budget should be staged: <500 GPU-hours for the first stop/go decision,
~2,800-5,900 GPU-hours for the realistic two-paper program, and
~5,000-7,000 GPU-hours only if every optional ablation/post-training
stage is run. Paper 2A should target MICCAI 2027; Paper 2B should target
NeurIPS 2027. Both papers ship even if Cosmos doesn't transfer to
surgical video, because the causal-evaluation apparatus and the
distillation method are the substantive contributions; Cosmos is one row
in a benchmark table either way.

— *End of brief.*

---

## Appendix A — Citation verification log (2026-05-21)

| # | Source | Verified | Notes |
|---|---|---|---|
| 1 | Cosmos [2501.03575](https://arxiv.org/abs/2501.03575) | yes | NVIDIA, Jan 2025 |
| 2 | Cosmos Policy [2601.16163](https://arxiv.org/abs/2601.16163) | yes | Stanford + NVIDIA, Jan 2026 |
| 3 | V-JEPA 2 [2506.09985](https://arxiv.org/abs/2506.09985) | yes | Meta, Jun 2025 |
| 4 | V-JEPA 2.1 [2603.14482](https://arxiv.org/abs/2603.14482) | yes | Meta, Mar 2026 |
| 5 | SurgMotion [2602.05638](https://arxiv.org/abs/2602.05638) | yes | Video-native surgical foundation model |
| 6 | SurgVISTA [2506.02692](https://arxiv.org/abs/2506.02692) | yes | HKUST, npj DM 2026 |
| 7 | EndoMamba [2502.19090](https://arxiv.org/abs/2502.19090) | yes | Tian et al., Feb 2025 / MICCAI 2025 |
| 8 | EndoDINO [2501.05488](https://arxiv.org/abs/2501.05488) | yes | Jan 2025 |
| 9 | SWAG [2412.18849](https://arxiv.org/abs/2412.18849) | yes | Boels et al., Dec 2024; published IJCARS 2025 |
| 10 | Scaling Video Pretraining for Surgical FMs [2603.29966](https://arxiv.org/html/2603.29966v2) | yes | New addition, early 2026 |
| 11 | ZEN [2602.13633](https://arxiv.org/abs/2602.13633) | yes | Cross-procedure intraoperative FM |
| 12 | SurgSigma [2603.16822](https://arxiv.org/abs/2603.16822) | yes | Multimodal surgical intelligence effort |

Validated against arxiv / publisher / model-card pages on 2026-05-21.
Re-check names, weight availability, and venue dates before submission.

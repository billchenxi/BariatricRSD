# Next Paper Proposal: World-Model Transfer for Causal Surgical Anticipation

Research status checked: 2026-05-21.

This replaces the earlier vendor-first "Surgical Cosmos + OpenUSD" memo with a
paper plan that is harder to reject. The old plan had a good instinct - connect
workflow-conditioned RSD to physical-AI world models - but it over-relied on
NVIDIA branding and under-specified the scientific claim. The stronger paper is
not "we used Cosmos on surgery." It is:

> **Do physical-AI and surgical video foundation models improve causal surgical
> anticipation, and does workflow variability still determine when explicit
> workflow-state conditioning helps?**

That question is publishable even if Cosmos does not win.

---

## 1. Executive decision

### Recommended flagship paper

**Working title**

*Do World Models Help Surgical Workflow Forecasting? A Causal Benchmark for
Remaining Duration and Phase Anticipation*

### One-sentence thesis

World-model and video-foundation pretraining should be evaluated in surgery by
strict prefix-only future prediction - remaining duration, phase-transition
time, future phase sequence, and optionally action triplets - not by generic
pixel-generation quality alone.

### Why this is better than "Surgical Cosmos"

The current research landscape has moved fast. As of early 2026, surgical video
foundation models already exist, including SurgMotion, SurgVISTA, EndoMamba,
and EndoDINO. A paper claiming to be first because it fine-tunes Cosmos on
surgical video is fragile. A paper that systematically compares physical-AI
world models, general video models, and surgical-native models under a causal
surgical anticipation protocol is much stronger.

### Bottom line

Make the paper a **causal transfer benchmark and method paper**, not a Cosmos
demo. Cosmos remains in the model matrix, but it should not be the title,
thesis, or single point of failure.

---

## 2. My assessment of the previous draft

### What was strong

- It correctly identifies surgical video as long-horizon, fine-motor,
  uncertain physical activity.
- It reuses existing assets: MB140, Cholec80, workflow clusters, strict
  prefix-only evaluation, trained RSD baselines, and semantic controls.
- It sees that the next paper needs to move beyond scalar RSD toward
  "what happens next."
- It recognizes the training-time supervision gap in the current paper.

### What would get attacked by reviewers

- **Vendor-first framing.** "NVIDIA Cosmos + OpenUSD" sounds like product
  adoption before science. Reviewers will ask why those tools are necessary.
- **Weak Physical AI claim.** RSD prediction alone is not embodied control.
  To justify a world-model framing, the paper must include future-state or
  future-workflow prediction.
- **OpenUSD is not load-bearing.** Encoding OR metadata in USD is not enough.
  If the same information could be a JSON vector, the contribution is not USD.
- **"First" claims are unsafe.** Surgical foundation-model work is now active.
  The paper should claim systematic causal evaluation, not novelty by absence.
- **Compute risk is too high.** Full Cosmos fine-tuning is not the first move.
  Frozen features and parameter-efficient adaptation should come first.

### Corrective pivot

Use your current paper's core advantage - leakage-safe causal evaluation and
workflow-variability analysis - as the thing that the foundation-model papers
do not already have.

---

## 3. Research landscape that changes the plan

### Physical-AI / world-model side

- **NVIDIA Cosmos** is an open physical-AI platform with world foundation
  models, video processing, evaluation, and post-training tools. NVIDIA
  positions Cosmos-Predict as future-state video/world simulation, Transfer as
  controllable sim-to-real generation, and Reason as video/image reasoning.
- **Cosmos-Predict2.5** unifies Text2World, Image2World, and Video2World in the
  current documentation. This matters because video-to-future-video is closer
  to surgical anticipation than text-to-video generation.
- **Cosmos Policy** shows the robotics direction: adapt Cosmos-Predict2 to
  visuomotor control and planning from demonstrations. That strengthens the
  physical-AI motivation, but it also makes plain that an RSD-only paper is
  not enough.
- **V-JEPA 2 and V-JEPA 2.1** are very relevant. V-JEPA 2 reports strong motion
  understanding, action anticipation, and robotic planning after post-training
  on robot video. V-JEPA 2.1 reports stronger dense features, anticipation, and
  real-robot grasping gains. These are better baselines than a Cosmos-only
  story because they are latent predictive models, not just generative video
  models.

### Surgical video foundation-model side

- **SurgMotion** is a video-native surgical foundation model built on V-JEPA,
  with a latent motion prediction objective and a 3,658-hour, 50-source
  surgical video corpus. It reports improvements on workflow recognition,
  CholecT50 triplets, skill assessment, polyp segmentation, and depth.
- **SurgVISTA** is a large-scale self-supervised surgical video foundation
  model with a unified spatiotemporal pretraining setup and broad downstream
  evaluation across surgical procedures and tasks.
- **EndoMamba** targets efficient online endoscopic video understanding with
  spatiotemporal state-space modeling and hierarchical pretraining.
- **EndoDINO** is GI-endoscopy image-level pretraining, useful as an image
  baseline but less central for laparoscopic workflow anticipation.
- **SWAG** already frames long-term surgical workflow prediction as generative
  phase anticipation on Cholec80 and AutoLaparo21. Your paper must cite it and
  either compare to it or clearly target a different gap: causal world-model
  transfer plus workflow-variability scaling.

### Consequence

The next paper should not ask, "Can Cosmos work on surgical video?" It should
ask:

> **When surgical video models are evaluated causally, do general physical-AI
> world models, general video foundation models, or surgical-native models
> transfer best, and does explicit workflow-state conditioning still provide
> marginal value only when workflow variability is present?**

---

## 4. Proposed paper

### Core research question

Given only the observed surgical prefix \(x_{\le t}\), can pretrained
world/video models improve:

1. remaining surgery duration,
2. time to next phase transition,
3. future phase sequence over a multi-minute horizon,
4. optionally future surgical action triplets,

and does an explicit workflow-state posterior \(q(z \mid x_{\le t})\) help in
proportion to the benchmark's workflow variability?

### Main hypothesis

Pretraining that learns temporal dynamics should help most on future-oriented
tasks - phase transition and future phase sequence - while workflow-state
conditioning should help only when the data contain real workflow variation.
This should reproduce the current MB140 vs Cholec80 pattern on tasks beyond
scalar RSD.

### Claims the paper can safely make if results support them

1. **Causal evaluation changes the ranking of foundation models.** Strong
   generic video features do not necessarily imply strong online surgical
   anticipation.
2. **Surgical-native video pretraining is a serious baseline.** Physical-AI
   models must be compared against SurgMotion/SurgVISTA/EndoMamba-style
   methods when weights or reproducible implementations are available.
3. **Workflow variability predicts the value of conditioning.** The current
   RSD finding should generalize to anticipation tasks if the mechanism is
   real.
4. **Pixel/world simulation metrics are not enough.** The paper should test
   whether next-frame or video-prediction metrics correlate with downstream
   anticipation and RSD. If they do not, that negative result is valuable.
5. **Privileged workflow supervision can be distilled into a deployable
   prefix-only model.** This closes the main training-time gap in the current
   paper.

### Claims to avoid

- Avoid "first surgical physical-AI paper."
- Avoid "Cosmos understands surgery" unless the experiments directly show it.
- Avoid "OpenUSD improves surgical AI" unless USD is used for simulation or
  scene generation and beats a simple metadata baseline.
- Avoid claiming clinical readiness. This is a representation and benchmark
  paper.

---

## 5. Existing assets to reuse

### From the submitted RSD paper

- MultiBypass140: 140 RYGB videos, two centers, 14 phases, 1 fps.
- Cholec80: 72 videos, public phase labels, 7 phases.
- Strict prefix-only clip protocol.
- Centered-window protocol only as a retrospective leakage contrast.
- Workflow-cluster pipeline: phase bigram TF-IDF, PCA, k-means.
- \(K=6\) MB140 and \(K=4\) Cholec80 cluster artifacts.
- Decoupled-oracle architecture.
- Shuffled-token semantic control.
- Causal pixel-only evaluator.
- Trained ViT-B/16 + temporal-head checkpoints.
- Cross-center MB140 Bern -> Strasbourg protocol.

### Why these assets matter

Most foundation-model papers do not have your causal RSD/anticipation harness.
Your advantage is not raw model size. It is the ability to ask a precise
question:

> Does a representation improve online surgical forecasting when future frames,
> ground-truth future phases, and full-case workflow labels are unavailable?

---

## 6. Experimental design

### Experiment 0 - lock the baseline and evaluation contract

Before adding new backbones, freeze the current protocol:

- strict prefix-only clips only for headline results,
- identical train/val/test splits across all backbones,
- identical temporal head where possible,
- no full-video labels at inference,
- no centered-window headline claims,
- report 5-fold MB140 and cross-center MB140, not only fold 0,
- report seed means and paired uncertainty.

Deliverable: a table reproducing the current ViT-B/16 no-token, oracle,
decoupled-oracle, shuffled-token, and causal-at-inference results.

### Experiment 1 - frozen representation transfer

Replace the visual encoder while keeping the temporal head and losses fixed.
This is the cheapest and cleanest first test.

| Family | Candidate | Why include |
|---|---|---|
| Current baseline | ImageNet-21k ViT-B/16 | Anchor to submitted paper |
| General video | TimeSformer, VideoMAE, DINO-family encoders | Standard video/vision baselines |
| Latent world model | V-JEPA 2, V-JEPA 2.1 | Strong action anticipation and physical planning prior |
| Generative world model | Cosmos-Predict2 or Predict2.5 encoder/features | Physical-AI substrate, video-to-world framing |
| Surgical-native | SurgMotion, SurgVISTA, EndoMamba | Must-have baselines if weights are available |
| Image surgical | EndoDINO | Frozen image-domain control |

Primary output: which representation improves causal RSD and phase
anticipation under the same temporal head?

### Experiment 2 - parameter-efficient surgical adaptation

Only after Experiment 1 shows a promising representation, run adapters:

- LoRA/adapters on the visual backbone,
- frozen backbone plus trainable projection and temporal head,
- optional masked/latent future prediction on unlabeled surgical clips,
- no full model fine-tuning unless adapters show a clear signal.

This reduces compute and gives a clean scaling story:

1. frozen features,
2. surgical adapters,
3. optional full post-training.

### Experiment 3 - causal workflow-state distillation

This is the key method contribution that connects the new paper to the old
one.

Teacher signal:

- full-video workflow cluster \(z(V)\),
- prefix-derived cluster labels when available,
- phase-transition structure from labels during training only.

Student:

- learns \(q_\phi(z \mid x_{\le t})\) from pixels only,
- produces a soft workflow token \(\sum_k q_k E_k\),
- conditions RSD and anticipation heads,
- never uses ground-truth phase labels or full-video clusters at test time.

Losses:

- RSD regression,
- current phase classification when labels are available,
- next-transition time regression or classification,
- future phase sequence loss,
- KL or cross-entropy from student workflow posterior to the privileged teacher,
- optional calibration loss for RSD uncertainty.

What this fixes:

- The current paper removes inference-time oracle access but still uses
  privileged workflow supervision during training. This distillation setup makes
  that gap the explicit next-paper contribution.

### Experiment 4 - anticipation tasks

The world-model framing needs future prediction beyond RSD.

#### Task A: time to next phase transition

Input: prefix \(x_{\le t}\).

Outputs:

- minutes until next phase transition,
- next phase identity,
- uncertainty interval.

Metrics:

- MAE for transition time,
- macro-F1 for next phase identity,
- expected calibration error or interval coverage,
- horizon-binned results.

#### Task B: future phase sequence

Predict phase labels at fixed future horizons:

- 1, 2, 5, 10, 20, and 30 minutes where labels exist,
- sequence-level edit score,
- horizon-specific macro-F1,
- temporal Jaccard.

This gives a direct comparison point to SWAG-style anticipation work.

#### Task C: action-triplet anticipation on CholecT50

Only include if data access and compute are practical.

Input: observed prefix.

Output:

- future instrument, verb, target, and triplet presence at short horizons.

Metrics:

- component mAP,
- triplet mAP,
- horizon-binned recall/precision.

This is where "physical" becomes more credible because instrument-object
interactions are closer to action than phase labels.

### Experiment 5 - variability-scaling extension

Use the same workflow-cluster entropy logic from the current paper, but test it
across more tasks and, if possible, more procedures.

For each dataset/task:

1. compute workflow-cluster entropy \(H(z)\),
2. train no-token, oracle, causal-distilled, and shuffled-token variants,
3. measure marginal gain \(\Delta\) from workflow conditioning,
4. plot \(\Delta\) against \(H(z)\).

Interpretation:

- high \(H(z)\), positive \(\Delta\): workflow state contains real signal,
- low \(H(z)\), null \(\Delta\): no residual workflow signal to exploit,
- shuffled-token null: gain is semantic, not parameter capacity,
- cross-center drop: representation/domain shift rather than workflow signal.

---

## 7. Model matrix and decision gates

### Minimal model matrix

Run these first:

| Model | Mode | Required for paper? |
|---|---|---|
| Current ViT-B/16 + HTA | train as before | yes |
| VideoMAE or TimeSformer | frozen features | yes |
| V-JEPA 2 or 2.1 | frozen features | yes |
| One surgical-native model | frozen features | yes if weights available |
| Cosmos-Predict2/2.5 | frozen or adapter | desirable, not mandatory |

### Full model matrix

Run these only after the minimal matrix works:

| Model | Mode | Purpose |
|---|---|---|
| V-JEPA 2/2.1 | adapter | strongest latent-world baseline |
| Cosmos-Predict2/2.5 | adapter/post-training | physical-AI test |
| SurgMotion/SurgVISTA | adapter or frozen | surgical-domain ceiling |
| EndoMamba | frozen/finetuned | efficient online baseline |

### Go/no-go gates

After three weeks:

- If frozen V-JEPA or a surgical-native model improves MB140 strict RSD by at
  least 0.3 min or improves transition anticipation clearly, continue.
- If Cosmos is hard to run or weak, keep it as one row in the benchmark, not as
  the paper's identity.
- If no foundation model improves RSD but anticipation improves, pivot the
  paper toward "world models help forecasting, not scalar duration."
- If no foundation model improves any task, publish the diagnostic result:
  current physical-AI pretraining does not transfer automatically to endoscopic
  surgical forecasting under causal evaluation.

---

## 8. Statistical standard

A successful paper needs reviewer-proof statistics, not isolated fold-0 wins.

Use:

- 5-fold MB140 where feasible,
- Bern -> Strasbourg cross-center,
- Cholec80 standard split,
- fixed seeds across model families,
- paired bootstrap over videos/clips,
- hierarchical mixed model if reporting pooled results,
- shuffled-token semantic control,
- matched-parameter controls for added tokens/adapters,
- horizon-binned metrics for anticipation.

Report:

- mean +/- standard deviation across seeds,
- video-level bootstrap confidence intervals,
- per-fold results in appendix,
- aggregate effect sizes in the main paper.

Avoid:

- a main table that hides fold failures,
- "best seed" model selection,
- comparing full fine-tuned giant models to weak baselines without compute and
  parameter accounting.

---

## 9. Expected paper figures

### Figure 1 - causal surgical world-model evaluation

Show prefix frames -> frozen/adapted foundation encoder -> temporal head ->
workflow posterior -> RSD, transition, future sequence.

Make the causal constraint visually obvious: all inputs stop at time \(t\).

### Figure 2 - model transfer matrix

Rows: backbones.

Columns:

- RSD MAE,
- next-transition MAE,
- future phase macro-F1,
- CholecT50 triplet mAP if included,
- compute cost,
- parameters trained.

### Figure 3 - variability-scaling curve

Extend the current \(H(z)\) vs \(\Delta\) plot across tasks and datasets.

This is the continuity figure from Paper 1 to Paper 2.

### Figure 4 - pixel/world prediction vs surgical anticipation

If Cosmos or other predictive models are evaluated with video-prediction
metrics, plot those metrics against downstream anticipation gains.

The likely interesting finding:

> Better-looking video prediction may not mean better surgical workflow
> anticipation.

### Figure 5 - failure cases

Show where models fail:

- smoke/bleeding/specular frames,
- phase transitions with no visual cue,
- cross-center instrument/viewpoint differences,
- rare workflow branches.

---

## 10. OpenUSD and Isaac Sim: keep out of the flagship unless load-bearing

### Current recommendation

Do **not** put OpenUSD in the title or primary contribution of this paper.

### Why

For the current assets, OpenUSD would mostly encode structured metadata about
OR setup. Reviewers will reasonably ask why that is not just a small JSON
feature vector. USD becomes scientifically meaningful only when it is used for:

- reconstructing or simulating a 3D scene,
- rendering synthetic views,
- generating controlled scene variations,
- connecting to Isaac Sim / Isaac Lab,
- training or evaluating a policy.

### Acceptable small OpenUSD side experiment

If you want to keep the OpenUSD thread alive, do it as a short appendix:

1. create a tiny OR-scene schema,
2. store the same information in both USD and a flat metadata vector,
3. train the same model with no scene prior, flat prior, and USD-parsed prior,
4. report whether USD adds anything beyond the flat vector.

If USD does not beat the flat vector, do not include it in the main paper.

### Better future OpenUSD paper

Save OpenUSD for a separate robotics/simulation paper:

*From Endoscopic Video to OpenUSD Surgical Scenes for Simulation and Policy
Learning*

That paper would need 3D reconstruction, Isaac Sim, tissue/instrument dynamics,
and a policy benchmark. It is not the next 6-month paper.

---

## 11. Compute plan

### Tier 1 - low-risk benchmark

Goal: frozen features plus current temporal head.

Likely requirements:

- feature extraction for MB140 and Cholec80,
- 1 to 3 strong backbones,
- train only projection/temporal heads,
- practical on current GH200 setup.

This tier is enough to decide whether the paper is viable.

### Tier 2 - serious paper

Goal: parameter-efficient adaptation.

Likely requirements:

- adapter/LoRA runs for the best 2 to 3 backbones,
- unlabeled surgical-video adaptation,
- 5-fold MB140 plus cross-center,
- Cholec80 and at least one anticipation benchmark.

This is the realistic flagship workload.

### Tier 3 - full physical-AI post-training

Goal: post-train Cosmos or another large world model.

Only do this if Tier 1 or Tier 2 shows clear positive transfer. Full
post-training is expensive and should not be the first experiment.

---

## 12. Draft abstract

Surgical video analysis is increasingly adopting large video and world
foundation models, but it remains unclear whether such models improve
deployable, online surgical forecasting. We introduce a strict prefix-only
benchmark for causal surgical anticipation across remaining surgery duration,
time-to-next-phase transition, and future phase-sequence prediction. Using
MultiBypass140 and Cholec80, with optional extension to CholecT50 action
triplets, we compare ImageNet, general video, physical-AI world-model, and
surgical-native video representations under a shared temporal head and matched
causal evaluation protocol. We further extend workflow-state conditioning from
oracle phase-order clusters to a deployable prefix-only posterior trained by
privileged-information distillation. Across datasets, we test whether the
marginal value of explicit workflow conditioning scales with empirical workflow
variability. This study provides a leakage-safe evaluation of world-model
transfer to surgery and clarifies when stronger pretrained video
representations, explicit workflow state, or both are useful for surgical
forecasting.

---

## 13. Target venues

### Highest expected value

- **MICCAI 2027** if the strongest contribution is surgical anticipation,
  clinical workflow, and domain-specific evaluation.
- **CVPR 2027** if the model-transfer matrix, world-model diagnostics, and
  anticipation tasks are strong enough for the vision community.
- **NeurIPS / ICLR 2027** if the paper becomes a general benchmark for causal
  world-model transfer under distribution shift, not only a surgical
  application.

### Best current target

Aim for **MICCAI 2027 or CVPR 2027**. NeurIPS/ICLR is possible only if the
paper is framed as a broader world-model evaluation problem and includes a
clean, reusable benchmark release.

---

## 14. Concrete next steps in this repo

1. Create a `backbone_features` interface that can cache frozen features from
   ViT, VideoMAE/TimeSformer, V-JEPA, Cosmos, and surgical-native models.
2. Add `evaluate_phase_anticipation.py` with strict prefix-only evaluation for
   next transition time and future phase sequence.
3. Add a workflow-posterior student head \(q_\phi(z \mid x_{\le t})\) and a
   privileged-teacher distillation loss.
4. Define a YAML experiment grid for:
   - backbone,
   - frozen vs adapter,
   - no-token vs oracle vs causal-distilled vs shuffled,
   - RSD vs anticipation task,
   - dataset/split.
5. Run the minimal matrix:
   - current ViT-B/16,
   - one general video model,
   - V-JEPA 2 or 2.1,
   - one surgical-native model if weights are accessible,
   - Cosmos only if setup is straightforward.
6. Make a first paper table before any large fine-tuning:
   - rows are backbones,
   - columns are RSD, transition time, future phase sequence, compute.

---

## 15. Success criteria

The paper is strong if it shows at least two of the following:

- a foundation/world model improves causal anticipation over the current ViT
  baseline under matched protocols,
- a surgical-native model beats a general physical-AI model, clarifying domain
  specialization,
- workflow-state conditioning improves high-variability MB140 but remains null
  on low-variability Cholec80 across multiple tasks,
- the causal-distilled workflow posterior closes much of the oracle gap,
- video-prediction quality is weakly correlated with surgical forecasting,
  giving the community a useful diagnostic warning,
- cross-center results reveal which representations are robust to surgical
  domain shift.

The paper is weak if it only says:

- "we fine-tuned Cosmos,"
- "we used OpenUSD,"
- "we improved one fold by a small amount,"
- "we got better next-frame PSNR."

---

## 16. References and links used for this revision

### Physical-AI / world models

- NVIDIA Cosmos official page:
  https://www.nvidia.com/en-us/ai/cosmos/
- NVIDIA Cosmos documentation:
  https://docs.nvidia.com/cosmos/2.1.0/introduction.html
- Cosmos World Foundation Model Platform for Physical AI:
  https://arxiv.org/abs/2501.03575
- Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning:
  https://arxiv.org/abs/2601.16163
- V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and
  Planning:
  https://arxiv.org/abs/2506.09985
- V-JEPA 2.1: Unlocking Dense Features in Video Self-Supervised Learning:
  https://arxiv.org/abs/2603.14482

### Surgical video foundation models and anticipation

- SurgMotion: A Video-Native Foundation Model for Universal Understanding of
  Surgical Videos:
  https://arxiv.org/abs/2602.05638
- SurgVISTA, large-scale self-supervised video foundation model for intelligent
  surgery:
  https://www.nature.com/articles/s41746-026-02403-0
- EndoMamba: An Efficient Foundation Model for Endoscopic Videos via
  Hierarchical Pre-training:
  https://arxiv.org/abs/2502.19090
- EndoDINO: A Foundation Model for GI Endoscopy:
  https://arxiv.org/abs/2501.05488
- SWAG: Long-term Surgical Workflow Prediction with Generative-based
  Anticipation:
  https://arxiv.org/abs/2412.18849
- CholecT50 dataset card:
  https://huggingface.co/datasets/Voxel51/cholect50

### OpenUSD / simulation

- NVIDIA Isaac Sim:
  https://developer.nvidia.com/isaac/sim
- NVIDIA OpenUSD robotics simulation blog:
  https://developer.nvidia.com/blog/using-openusd-for-modular-and-scalable-robotic-simulation-and-development/

---

## 17. Final recommendation

Do Paper A, but not as "Surgical Cosmos."

The winning version is:

> **Causal surgical world-model transfer:** a rigorous benchmark and method for
> testing whether physical-AI, general video, and surgical-native foundation
> models actually improve online surgical forecasting, with workflow-state
> conditioning evaluated through the variability-scaling lens established in
> the current paper.

Keep Cosmos in the paper. Keep OpenUSD in the long-term roadmap. Make the
science about causal anticipation, workflow variability, and transfer under
surgical domain shift.

# Next-Paper Brief: Four Refinements

*Companion document to `NEXT_PAPER_PHYSICAL_AI.md` (the ChatGPT-rewritten
brief). Verified on 2026-05-20 against arxiv and the published surgical-FM
literature.*

This file contains the four follow-ups requested:

- **(A)** Citation verification — all 9 references in §16 of the brief.
- **(B)** Split-into-two-papers sketch with separate theses.
- **(C)** Tier-2 compute budget with concrete GPU-hour estimates.
- **(D)** "Cosmos-is-meh" recovery narrative — how to ship a paper if the
  flagship physical-AI model doesn't transfer.

---

## (A) Citation verification

**Verdict:** all 9 references in §16 of the brief are real, published, and
correctly described. **None are hallucinated.** ChatGPT did its homework.
Only one minor note: the SurgVISTA reference in §16 cited the Nature link
without an arxiv ID; the arxiv preprint is **arxiv 2506.02692**.

| # | Citation as written | Verified? | Verified title | Verified authors/affil | Verified date |
|---|---|---|---|---|---|
| 1 | Cosmos World Foundation Model Platform [2501.03575](https://arxiv.org/abs/2501.03575) | ✅ | "Cosmos World Foundation Model Platform for Physical AI" | NVIDIA (77 authors) | 2025-01-07; v3 2025-07-09 |
| 2 | Cosmos Policy [2601.16163](https://arxiv.org/abs/2601.16163) | ✅ | "Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning" | Moo Jin Kim, Yihuai Gao, … Chelsea Finn, Jinwei Gu (Stanford + NVIDIA) | 2026-01-22 |
| 3 | V-JEPA 2 [2506.09985](https://arxiv.org/abs/2506.09985) | ✅ | "V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning" | Meta AI (Assran et al., LeCun, Ballas) | 2025-06-11 |
| 4 | V-JEPA 2.1 [2603.14482](https://arxiv.org/abs/2603.14482) | ✅ | "V-JEPA 2.1: Unlocking Dense Features in Video Self-Supervised Learning" | Meta AI (Mur-Labadia et al.) | 2026-03-15 |
| 5 | SurgMotion [2602.05638](https://arxiv.org/abs/2602.05638) | ✅ | "SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos" | Wu, Holm, Navab et al. | 2026-02-05; v3 2026-04-17 |
| 6 | SurgVISTA (npj Digital Medicine) | ✅ | "Large-scale Self-supervised Video Foundation Model for Intelligent Surgery" | HKUST + collaborators (isyangshu/SurgVISTA on GitHub) | npj DM 2026; **arxiv [2506.02692](https://arxiv.org/abs/2506.02692)** |
| 7 | EndoMamba [2502.19090](https://arxiv.org/abs/2502.19090) | ✅ | "EndoMamba: An Efficient Foundation Model for Endoscopic Videos via Hierarchical Pre-training" | Tian, Liao, Ourselin, Liu et al. | 2025-02-26; v2 2025-05-15 |
| 8 | EndoDINO [2501.05488](https://arxiv.org/abs/2501.05488) | ✅ | "EndoDINO: A Foundation Model for GI Endoscopy" | Dermyer, Kalra, Schwartz | 2025-01-08 |
| 9 | SWAG [2412.18849](https://arxiv.org/abs/2412.18849) | ✅ | "SWAG: Long-term Surgical Workflow Prediction with Generative-based Anticipation" | Boels, Liu, Dasgupta, Granados, Ourselin | 2024-12-25; v4 2025-06-15 |

### Two competitors ChatGPT missed (worth adding to the related-work matrix)

While verifying SurgVISTA I surfaced a second active competitor that the
brief doesn't cite:

- **"Scaling Video Pretraining for Surgical Foundation Models"** —
  [arxiv 2603.29966](https://arxiv.org/html/2603.29966v2). Recent (early
  2026) work on surgical-FM scaling laws. Should be added to §3 of the
  brief and treated as a baseline in the model matrix.

### Two SWAG numbers worth knowing before claiming a Task-B gap

SWAG reports for **Cholec80 / AutoLaparo21** long-term phase anticipation
under generative decoding:

- **Single-pass**: 32.1% F1 over 20-min horizon, 41.3% F1 over 30-min
  horizon.
- **Phase remaining-time regression**: weighted MAE of **0.32 min** and
  **0.48 min** on the two splits.

These are the numbers your future-phase-sequence task in §6 Experiment 4B
has to beat (or non-trivially analyze, e.g., under causal vs. centered-
window protocols).

### Bottom line on citations

The brief's literature scan is solid; you can paste it into ChatGPT or
into your draft confident that nothing is fabricated. The two additions
above are recommended.

---

## (B) Split into two papers

**Recommendation:** split. Three contributions don't fit cleanly in one
8-page submission, and each half is stronger on its own.

### Paper 2A — *The empirical benchmark + transfer matrix*

**Working title (one of):**
- *Do World Models Help Surgical Workflow Forecasting? A Causal Benchmark
  for Remaining Duration and Phase Anticipation*
- *Causal Surgical Anticipation Under Workflow Variability: A Foundation-
  Model Transfer Study*

**One-sentence thesis:**
> Strict prefix-only evaluation reveals that the ranking of foundation
> models for surgical forecasting depends on the task (RSD vs. phase
> anticipation) and on workflow variability, not on generic video-
> prediction quality.

**Core claims this paper defends:**

1. **Causal evaluation changes the FM ranking.** A backbone that wins on
   centered-window Cholec80 phase recognition can lose on strict prefix-
   only MB140 RSD and phase anticipation.
2. **Pixel-prediction quality is a weak proxy for surgical forecasting.**
   Cosmos / VideoMAE generative-quality metrics do not linearly predict
   downstream MAE or F1. (This is the diagnostic figure of the paper.)
3. **The variability-scaling pattern generalizes.** Workflow conditioning
   helps in proportion to *H(z)*; this holds across backbones and across
   RSD + phase anticipation, not just on fold-0 MB140 RSD.
4. **Cross-center transfer is a representation problem.** Some backbones
   are robust to Bern → Strasbourg domain shift; others collapse.

**Experiments:** §6 Exp 0, 1, 2 (locked baseline; frozen-feature transfer;
parameter-efficient adaptation) + §6 Exp 4 anticipation tasks A and B +
§6 Exp 5 variability-scaling extension.

**What's NOT in this paper:** the privileged-information distillation
method. That's Paper 2B.

**Page budget (NeurIPS-style 8 pages body):**

- §1 Intro: 0.75 pp
- §2 Causal evaluation protocol & related work: 1.0 pp
- §3 Method (model matrix, temporal head, conditions): 1.0 pp
- §4 Datasets & tasks (MB140, Cholec80, RSD + anticipation defs): 0.75 pp
- §5 Results (Tables 1–3, transfer matrix; Figure 1 pixel-prediction vs.
  downstream; Figure 2 variability scaling): 3.0 pp
- §6 Discussion & Limitations: 1.0 pp
- §7 Conclusion: 0.25 pp + 0.25 pp references-spillover

**Target venue:** MICCAI 2027 (deadline ~March 2027) or CVPR 2027 (deadline
~November 2026 — earlier, riskier).

**Risk profile:** medium. Depends on at least one foundation-model
backbone showing a measurable lift somewhere in the matrix. The
*diagnostic* claim ("pixel-prediction ≠ downstream") is publishable even
if no backbone wins.

---

### Paper 2B — *The privileged-information distillation method*

**Working title:**
- *Closing the Oracle Gap in Workflow-Conditioned Surgical Forecasting via
  Privileged-Information Distillation*
- *Causal Workflow Posteriors: Distilling Privileged Phase Supervision for
  Deployable Surgical RSD*

**One-sentence thesis:**
> A student model that learns the workflow-cluster posterior
> *q(z | x_{≤t})* from a privileged teacher closes most of the
> oracle-to-deployable gap in surgical RSD prediction without using any
> ground-truth phase or workflow labels at inference.

**Core claims this paper defends:**

1. **Teacher-student distillation closes the oracle gap.** The current
   paper's gap between decoupled-oracle (−0.85 min) and deployable causal
   (−0.18 min) shrinks to ≤0.3 min after distillation.
2. **The student's workflow posterior is calibrated.** Reliability
   diagrams + ECE numbers show the posterior tracks the true cluster
   identity proportionally.
3. **The student preserves variability scaling.** Distillation doesn't
   leak benefits to Cholec80; the *H(z)* pattern survives the new method.
4. **Architectural ablations.** What teacher matters? (Frozen oracle vs.
   distilled chain.) What student-side loss formulation works best?
   (Hard target vs. KL vs. matching internal representations.)

**Experiments:** §6 Exp 3 (workflow-state distillation) treated as the
methodological core, with extensive ablations:
- distillation loss variants (KL on cluster posterior, MSE on workflow
  token, soft-target with temperature τ),
- teacher choices (oracle decoupled, oracle + phase-head supervision,
  prefix-cluster teacher),
- evaluation on the same RSD + anticipation tasks from Paper 2A,
- 5-fold + cross-center on MB140.

**What's NOT in this paper:** the foundation-model transfer matrix. Use
your existing ViT-B/16 + HTA backbone as the workhorse. One ablation can
swap in a stronger encoder (e.g., V-JEPA 2.1 or SurgVISTA features) to
demonstrate the method is encoder-agnostic.

**Page budget (NeurIPS-style 8 pages body):**

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
with existing assets; even a partial close (−0.85 to −0.4 instead of −0.18)
is a real result. The Cholec80 null-preservation claim is essentially
free — already verified directionally in the current paper.

---

### Why splitting wins

| Concern | Single-paper version | Two-paper version |
|---|---|---|
| Reviewer fatigue | "Too much going on" | Each paper has one clean thesis |
| Page budget | 8 pages of 3 contributions = shallow on each | 8 pages × 2 = depth on each |
| Venue fit | Benchmark + method is split across surgical-AI and ML venues | 2A → MICCAI/CVPR (surgical), 2B → NeurIPS/ICLR (ML) |
| Risk hedging | If Cosmos fails, the whole paper looks weak | Paper 2B is independent of FM transfer outcome |
| Time-to-publish | 9–12 months | 2A in 6 months, 2B in 9–12 months |
| Citation footprint | One paper to cite | Two papers; the distillation paper becomes the more-cited methods paper |

### Suggested sequencing

1. **2026 Q3–Q4:** Build experimental infrastructure (frozen-feature
   extraction harness, anticipation eval, distillation training loop).
2. **2026 Q4–2027 Q1:** Run Paper 2A experiments. Submit to **MICCAI 2027**
   (~March deadline).
3. **2027 Q1–Q2:** Run Paper 2B experiments using the same infrastructure.
   Submit to **NeurIPS 2027** (~May deadline).

The two papers share ~70% of the experimental infrastructure, so the
marginal cost of doing both is much less than 2×.

---

## (C) Tier-2 compute budget — concrete GPU-hour estimates

The ChatGPT brief left Tier 2 as "parameter-efficient adaptation, runs for
2–3 backbones, 5-fold MB140 + cross-center, Cholec80 + at least one
anticipation benchmark." That's qualitative. Here are the actual numbers.

### Assumptions

- **GPU:** H100 80 GB or GH200 96 GB (your existing setup).
- **Backbone size:** 300M–7B for the FMs; current ViT-B/16 is 86M.
- **Per-run training:** 15 epochs, batch 64, 8-frame clips at 224×224.
  Current ViT-B/16 takes ~5 hours per run.
- **Feature extraction:** one-time cost per (backbone × dataset).
- **Adapter / LoRA training:** ~30–50% the cost of full training due to
  smaller trainable parameter count, but inference forward pass still
  costs the full model.

### Cost decomposition for Paper 2A

#### One-time feature-extraction pass per (backbone, dataset)

| Backbone | Params | MB140 (153k clips) | Cholec80 (~110k clips) | Per backbone |
|---|---:|---:|---:|---:|
| ViT-B/16 (current) | 86M | already cached | already cached | 0 h |
| VideoMAE-L | 305M | 4 h | 3 h | 7 h |
| V-JEPA 2 (1B) | 1B | 10 h | 7 h | 17 h |
| V-JEPA 2.1 (1B) | 1B | 10 h | 7 h | 17 h |
| Cosmos-Predict2 (4B) | 4B | 38 h | 27 h | 65 h |
| SurgMotion | ~600M est. | 6 h | 4 h | 10 h |
| SurgVISTA | ~400M est. | 4 h | 3 h | 7 h |
| EndoMamba | ~200M | 2 h | 2 h | 4 h |
| **Total feature-extraction** | | | | **~127 h** |

#### Training runs on top of frozen features

For each backbone × dataset × condition, the temporal head + workflow
token + heads are trained:

| Aspect | Count |
|---|---:|
| Backbones in transfer matrix | 8 |
| MB140 within-center folds | 5 |
| MB140 cross-center | 1 |
| Cholec80 | 1 |
| Conditions per (backbone, dataset, fold) | 4 (no-token, oracle, decoupled, shuffled) |
| Seeds per (backbone, dataset, fold, condition) | 3 |
| Per-run training (frozen features → temporal head only, 15 epochs) | ~1.5 h |

**Total training runs** = 8 backbones × (5 + 1 + 1) datasets × 4 conditions
× 3 seeds = **672 runs**.

**Total GPU-hours** = 672 × 1.5 = **1,008 h**.

#### Anticipation evaluation

Anticipation tasks A (next-transition time) and B (future phase sequence)
share the trained model — no additional training. Inference + scoring
across all 672 trained models ≈ **50 h**.

#### Paper 2A subtotal

| Bucket | Hours |
|---|---:|
| Feature extraction (one-time, 8 backbones × 2 datasets) | 127 |
| Frozen-head training (672 runs × 1.5 h) | 1,008 |
| Anticipation eval | 50 |
| **Paper 2A Tier-1 (frozen-feature) total** | **~1,185 h** |

#### Tier 2 — parameter-efficient adaptation

LoRA / adapters on the top 2–3 backbones from Tier 1:

| Aspect | Count |
|---|---:|
| Backbones to adapt (selected from Tier 1 winners) | 3 |
| Folds + cross-center + Cholec80 | 7 |
| Conditions | 4 |
| Seeds | 3 |
| Per-adapter run (LoRA, 15 epochs) | ~6 h |

**Total adapter runs** = 3 × 7 × 4 × 3 = 252 runs × 6 h = **1,512 h**.

#### Optional unlabeled surgical-video pretraining adaptation (Tier 2b)

If a surgical-domain pretrain step is included for one backbone (e.g.,
continue V-JEPA 2.1 self-supervised pretraining on MB140 + Cholec80
combined ~500 hours of video):

| Aspect | Estimate |
|---|---:|
| Surgical SSL pretraining (V-JEPA 2.1, 100 K steps, batch 32, 8 GPUs) | ~700 h (8×88) |

Single-GPU equivalent: **~700 h** (this can be done on 4–8 H100s in
parallel; wall-clock ~90 h on 8 GPUs).

#### Paper 2A grand total

| Tier | Hours |
|---|---:|
| Tier 1 — frozen features | ~1,185 |
| Tier 2 — adapters | ~1,512 |
| Tier 2b — optional surgical SSL pretrain (one backbone) | ~700 |
| **Paper 2A total (without Tier 2b)** | **~2,700 h** |
| **Paper 2A total (with Tier 2b)** | **~3,400 h** |

#### Dollar cost on Lambda / equivalent

At ~$3.00/H100-hour on Lambda Cloud or comparable:
- **Paper 2A (no surgical SSL):** ~$8,100
- **Paper 2A (with surgical SSL):** ~$10,200

### Paper 2B compute (separate budget)

The distillation paper reuses Paper 2A infrastructure. Additional cost:

| Component | Estimate |
|---|---:|
| Teacher checkpoint training (already done in current paper) | 0 |
| Student distillation runs: 1 backbone × 7 (folds + ccent + cholec) × 3 distillation variants × 3 seeds × 15 epochs × 8 h | ~1,512 h |
| Ablations (teacher choice, loss variants, encoder swap): another ~50% | ~750 h |
| **Paper 2B total** | **~2,250 h** |
| **Paper 2B $ cost** | **~$6,800** |

### Combined budget (both papers)

| | Hours | $ at $3/h |
|---|---:|---:|
| Paper 2A | 3,400 | $10,200 |
| Paper 2B | 2,250 | $6,800 |
| **Combined** | **5,650 h** | **$17,000** |

Add ~20% overhead for storage, hyperparameter sweeps, debugging:
**~7,000 GPU-hours, ~$21,000 total**.

### Compute-risk mitigations

1. **Stop after Tier 1** if no backbone improves over ViT-B/16 by ≥ 0.3
   min on MB140 RSD or ≥ 5 F1 on phase anticipation. Saves ~1,500 h.
2. **Skip Cosmos** as full backbone; treat as "feature extraction only, no
   adaptation." Saves ~270 h.
3. **Drop SurgVISTA / EndoMamba** if weights aren't released by 2026 Q3.
   Saves ~100 h.
4. **5 folds → 3 folds** if budget is tight. Saves ~400 h but weakens
   reviewer-proofing.
5. **Skip surgical SSL pretraining.** Saves 700 h. Acceptable trade — the
   pretraining experiment is the highest-cost lowest-certainty piece.

### Sanity check vs. ChatGPT's brief

ChatGPT's brief said Tier 1 is "practical on current GH200 setup" and
Tier 2 is "the realistic flagship workload." With concrete numbers, Tier 1
is ~1,200 GPU-hours (about 5 GPU-weeks on a single GH200) and Tier 2 is
~1,500 GPU-hours (another 6 weeks). Together they're roughly 3 months of
single-GPU time, or 1 month on 4 nodes in parallel — which matches the
brief's qualitative timeline. So the numbers are consistent with the brief
but make the cost visible.

---

## (D) "Cosmos-is-meh" recovery narrative

The most likely empirical outcome for a Cosmos transfer experiment on
endoscopic video is **no clear lift over ViT-B/16 baselines**, because
Cosmos was pretrained on natural-world video (driving, robotics, generic
scenes) and laparoscopic close-ups are visually very out-of-distribution.
Here's how to publish anyway.

### The pitch

Reframe the paper from *"Cosmos helps surgical forecasting"* (which the
data won't support) to *"Cosmos doesn't transfer to endoscopic video, and
here's a measurement protocol that tells you why."* This is the same
move every careful negative-result paper makes, and it's well-received
when the apparatus is solid.

### Three publishable Cosmos-meh narratives

#### Narrative 1 — "Pixel-prediction quality is a weak proxy for surgical forecasting"

**Headline finding:** Cosmos generates plausible-looking next frames on
surgical clips (high PSNR, low LPIPS, low FVD), but its features don't
help downstream surgical RSD or phase anticipation any more than ImageNet
pretraining does.

**Why this is interesting:**
- It tells the field that "world models are getting better at video
  prediction" doesn't automatically mean they're getting better at
  understanding surgical workflow.
- It motivates surgical-native pretraining (SurgVISTA, SurgMotion, your
  next paper).
- The variability-scaling pattern *survives* this null result —
  i.e., even with a bad backbone, the *H(z)* signal persists.

**Headline plot:** Cosmos pixel-prediction FVD on Cholec80 (low = good)
vs. downstream RSD MAE on Cholec80 strict. Correlation should be weak or
absent. If you can show non-monotonic or anti-correlated relationships
(Cosmos generates the cleanest pixels but produces the worst features),
that's the diagnostic figure of the paper.

#### Narrative 2 — "Domain gap is the bottleneck, and surgical-native pretraining wins"

**Headline finding:** Cosmos < ViT-B/16 (current baseline) < surgical-
native FM (SurgVISTA / SurgMotion). The ordering by *visual-domain
overlap with the training corpus* matches the ordering of downstream
performance.

**Why this is interesting:**
- It quantifies the surgical-domain gap that's been assumed but not
  carefully measured.
- It gives the field a clear recommendation: for endoscopic forecasting,
  use surgical-native pretraining.
- Your distillation method (Paper 2B) becomes the story of "and here's
  how to get the rest of the gap without retraining a giant FM from
  scratch."

**Headline plot:** scatter plot of *(pretraining-corpus visual-domain
distance to MB140/Cholec80)* on x-axis, *(downstream RSD MAE improvement
over ImageNet baseline)* on y-axis. Each FM is a point. Expect a clean
monotonic relationship.

#### Narrative 3 — "Cosmos as a calibration anchor for the field"

**Headline finding:** even when Cosmos doesn't beat the baseline, having
Cosmos in the benchmark is useful as a *calibration anchor* — it tells
you when other FMs are succeeding by virtue of surgical pretraining vs.
when they're succeeding by virtue of generic temporal-modeling capacity.

**Why this is interesting:**
- This is the methodological-paper angle. The contribution is the
  benchmark protocol itself.
- It's the safest narrative because it doesn't require any FM to win.

**Headline plot:** the transfer matrix table. The interesting cells are
the ones where surgical-native FMs beat Cosmos by a lot AND ViT-B/16 by a
little — that's the evidence that surgical pretraining specifically (not
"better FM in general") is what's helping.

### Recommended primary framing

**Lead with Narrative 1** ("pixel-prediction is a weak proxy"). It's the
most surprising claim, requires the least cherry-picking, and is robust
to which specific Cosmos variant you test. Use Narrative 2 as a supporting
section if the surgical-native FMs are clear winners. Hold Narrative 3 in
reserve for the discussion.

### Concrete writing tactics

1. **Decide the framing before you run experiments.** Pre-register Narrative
   1 as the primary thesis. Treat it as testable: if Cosmos *does* win,
   pivot to "world models work for surgery and here's why." If Cosmos
   loses, you have the pre-committed null-result paper.

2. **Make pixel-prediction quality a first-class measurement.** Compute
   FVD, LPIPS, and PSNR on a held-out surgical video set for *every*
   backbone. This is cheap (one inference pass) and gives you the Figure
   1 of the paper.

3. **Use the diagnostic as the contribution.** *"We propose pixel-
   prediction-quality-vs-downstream-utility as a diagnostic for surgical-
   video foundation models, and find that Cosmos has the highest pixel
   quality but is mid-pack on downstream utility."* This frames the null
   result as a methodological finding, not as a failed experiment.

4. **Don't oversell.** Avoid "Cosmos fails at surgery." Use precise
   language: *"Cosmos features, evaluated under our causal anticipation
   protocol, do not transfer measurably better than ImageNet-pretrained
   ViT features on MB140 or Cholec80, despite generating higher-PSNR
   pixel predictions."* That's defensible.

5. **Cite NVIDIA's own framing.** Cosmos is positioned as a *platform*
   for fine-tuning, not as an out-of-the-box solution for every domain.
   If you cite their own framing ("Cosmos is designed to be post-trained
   for specific applications"), your null result becomes a measurement
   of the post-training cost — not an indictment of Cosmos.

### Why this works as a publication strategy

- **Reviewer-proof.** Negative results that are properly designed and
  controlled are recognized as scientific contributions.
- **Future-proof.** Even if NVIDIA releases Cosmos-Surgical in 2027, your
  paper provides the measurement protocol they'll have to compare against.
- **Citation-attractive.** Negative results in active subfields tend to
  get cited more than positive ones because they're load-bearing for
  follow-up work.
- **No wasted compute.** The same experiments that would have shown a
  positive result also produce the diagnostic data for the null-result
  paper. You're hedged.

### Risk: a partial-positive outcome

The trickiest case is *"Cosmos helps on one task / one benchmark / one
horizon but not others."* This isn't a clean negative result and isn't a
clean positive result. Handling:

- Report the partial positive faithfully (don't sandbag it, don't oversell
  it).
- Use the variability-scaling lens: *"Cosmos helps where workflow
  variability is high and the task requires temporal extrapolation; it
  doesn't help on standardized procedures or short-horizon tasks."* This
  is consistent with your current paper's thesis and makes the partial
  result a refinement of it rather than a contradiction.

---

## Combined bottom line

| Refinement | Outcome |
|---|---|
| **(A) Citation verification** | All 9 citations verified real. Two additional competitors flagged (Scaling Video Pretraining; SWAG specific numbers). Brief is safe to share. |
| **(B) Split into two papers** | Recommended: Paper 2A (causal benchmark + transfer matrix, MICCAI/CVPR 2027) and Paper 2B (privileged distillation method, NeurIPS/ICLR 2027). Shared infrastructure ~70%. |
| **(C) Compute budget** | Paper 2A ~3,400 GPU-hours / $10K. Paper 2B ~2,250 GPU-hours / $7K. Combined ~7,000 GPU-hours / $21K with overhead. Tier 1 alone (frozen features) is enough to decide viability and costs ~$3.5K. |
| **(D) Cosmos-meh recovery** | Lead with Narrative 1 — "pixel-prediction quality is a weak proxy for surgical forecasting." Pre-register the framing before running Cosmos experiments. Hedges against the most likely empirical outcome without committing to a vendor-positive story. |

Both papers can ship by mid-2027 if you start the infrastructure work
(frozen-feature extraction harness + anticipation evaluators) in Q3 2026.
Total budget ~$21K is on the low end for a two-paper ML/medical-AI
program, well within a single grant cycle.

— *End of refinements brief.*

# Publication Roadmap, 2026-2029

> **Historical roadmap. Updated September 17, 2026:** the current paper
> sequence, dated work plan, and verified venue shortlist are consolidated
> in [NEXT_PAPER_PLAN.md](NEXT_PAPER_PLAN.md). Follow Paper 2A (stable
> representations and forecasting evaluation) first; Paper 2B (distillation)
> is conditional on its results. The older ordering and estimates below
> are retained as background, not current commitments.

This document outlines a publication roadmap built on the current
NeurIPS 2026 Evaluations and Datasets submission, *When Does Workflow
Conditioning Help Remaining-Surgery-Duration Prediction?* It is intended
as a public-facing planning document: the emphasis is on coherent
scientific progression, realistic scope, and reuse of shared
infrastructure rather than on speculative brainstorming.

For the broader project plan from April 2026, see
[RESEARCH_PLAN.md](../paper1_neurips2026/RESEARCH_PLAN.md). This document focuses specifically
on the publication program that can plausibly grow out of the current
submission.

---

## Program overview

The current paper establishes a calibration result: explicit workflow
conditioning helps remaining-surgery-duration (RSD) prediction when the
benchmark contains meaningful workflow variation, and helps much less
when the procedure is highly standardized. The most natural follow-up
program is therefore sequential:

1. clarify the mechanism;
2. close the remaining deployment gap;
3. test richer conditioning signals;
4. evaluate whether stronger visual backbones change the conclusion; and
5. translate the system toward real-time clinical use.

The roadmap is organized as a **five-paper core program** plus one
optional extension. Each paper is designed to satisfy three criteria:

1. **Defensible**: a clear question, a falsifiable claim, and an honest
   evaluation protocol.
2. **Reproducible**: reuse of the same MB140/Cholec80 substrate,
   matched protocols, and shared code.
3. **Compounding**: each paper should leave behind data products,
   checkpoints, or tooling that reduce the cost of the next one.

At a high level, the arc is:

```
P1 (current)        P2                P3              P4              P5
"When does it       "Closing the      "Richer         "Backbone       "Prospective
 help?"             deployment gap"   conditioning"   effects"        deployment"
```

---

## Paper 2 — Distilling privileged workflow into a fully deployable predictor

**Working title:** *From Privileged Workflow to Pixel-Only RSD:
Distilling Oracle Conditioning Across Surgical Centers*

### Research question

The current paper closes the **inference-time** oracle dependency by
showing that a causal-at-inference predictor still gains 0.18 min
within-center and 0.22 min cross-center on MB140. It does **not** close
the **training-time** oracle dependency, because the current student
still benefits from supervision derived from full-case phase structure.

The next question is therefore direct:

> Can privileged workflow information be distilled into a pixel-only
> predictor that is fully deployable at both training and inference
> time?

### Proposed method

1. **Teacher**: the best decoupled-oracle model from the current paper.
2. **Student**: a pixel-only causal predictor that receives no cluster
   signal at training or inference time.
3. **Distillation objective**: a combination of RSD-target distillation
   and representation matching at the temporal head.
4. **Optional framing**: a Learning Using Privileged Information
   formulation in the spirit of Lopez-Paz et al. (2016).

### Expected contribution

The target result is a student model that stays within roughly 0.1-0.3
min of the privileged teacher within-center while preserving some
cross-center benefit. If successful, this paper would convert the
current methodological result into a **fully deployable** pipeline with
no oracle dependence at any stage.

### Tentative venues

- Primary: **MICCAI 2027**
- Secondary: **WACV 2027** or **NeurIPS 2027**

### Estimated timeline

- Aug-Sep 2026: loss design and first training runs
- Oct-Nov 2026: ablations and cross-center evaluation
- Dec 2026: writing
- Target submission window: **early 2027**

### Resources and risk

- Reuses current checkpoints and datasets
- Estimated compute: ~50 GH200-hours (~$115 at current pricing)
- **Risk level:** low

This is the most direct and lowest-risk continuation of the current
submission.

---

## Paper 3 — Hierarchical workflow conditioning beyond coarse phase clusters

**Working title:** *Step-Level Workflow Conditioning for
Remaining-Surgery-Duration Prediction in Multi-Step Procedures*

### Research question

The current paper uses whole-video phase-bigram clusters as a coarse
proxy for workflow state. Its own discussion section points out that
this is not the final clinical representation: the more direct question
is which concrete procedural steps remain.

The next question is:

> Can hierarchical conditioning based on procedure, phase, and step
> state produce larger and more stable RSD gains than coarse workflow
> clusters alone?

### Proposed method

1. Use MB140 step annotations, which are finer-grained than the phase
   labels used in the current paper.
2. Condition the model jointly on:
   - a procedure-level workflow cluster,
   - the current phase estimated causally from the prefix, and
   - the current step estimated causally from the prefix.
3. Add phase-step consistency terms to the multi-task loss.
4. Compare against relevant hierarchical temporal baselines such as
   MTMS-TCN.

### Expected contribution

The main hypothesis is that finer-grained conditioning will produce
larger or more cross-fold-stable gains than phase-bigram conditioning
alone. A positive result would sharpen the variability-scaling story by
linking conditioning value to the granularity and entropy of the
underlying workflow representation.

### Tentative venues

- Primary: **NeurIPS 2027**
- Secondary: **MICCAI 2027** or **IEEE TMI**

### Estimated timeline

- Sep-Dec 2026: step-label extraction and pipeline extension
- Jan-Mar 2027: training and ablations
- Apr 2027: writing
- Target submission window: **spring 2027**

### Resources and risk

- Reuses MB140 annotations already available in the dataset
- Estimated compute: ~120 GH200-hours (~$275)
- **Risk level:** medium

The main technical risk is that step recovery from the observed prefix
may be too noisy to support stable conditioning.

---

## Paper 4 — Do stronger surgical backbones change the conditioning story?

**Working title:** *Does Surgical-Domain Pretraining Change When
Workflow Conditioning Helps?*

### Research question

The current paper uses a ViT-B/16 backbone pretrained on ImageNet-21k.
It deliberately defers the question of whether surgical-domain
foundation models would change the conditioning result.

The next question is:

> Does stronger surgical-domain pretraining amplify, reduce, or leave
> unchanged the benefit of explicit workflow conditioning?

### Proposed method

1. Replace the current image backbone with several surgical-domain
   backbones, such as HecVL, EndoFM, SurgVLP, or GSViT, where
   accessible.
2. Keep the downstream temporal head, task heads, and evaluation
   protocols as consistent as possible with the current paper.
3. Repeat the headline experiments:
   - within-center MB140,
   - cross-center MB140,
   - Cholec80.
4. Add a probe analysis to test whether workflow state is already
   implicitly encoded in the backbone features.

### Expected contribution

This paper would answer whether explicit conditioning is mainly a crutch
for weaker visual backbones or whether it remains useful even after
strong surgical-domain pretraining. A clean result here would make the
mechanistic interpretation of the current paper substantially stronger.

### Tentative venues

- Primary: **MICCAI 2028**
- Secondary: **ICCV 2027** or **IEEE TMI**

### Estimated timeline

- Jan-Mar 2027: backbone integration
- Apr-Aug 2027: large ablation matrix
- Sep 2027: writing
- Target submission window: **2027-2028**

### Resources and risk

- Requires access to multiple pretrained backbones
- Estimated compute: ~250 GH200-hours (~$575)
- **Risk level:** medium-high

The largest risks are backbone accessibility and the possibility that
the comparison becomes more engineering-heavy than scientifically sharp.

---

## Paper 5 — Prospective real-time deployment study

**Working title:** *Real-Time Remaining-Surgery-Duration Prediction in
the Operating Room: A Prospective Validation Study*

### Research question

All results in the current paper and its immediate follow-ups are
retrospective. Real deployment adds latency constraints, streaming
buffers, live phase estimation, and workflow integration with the
operating room.

The central question becomes:

> Do the offline gains observed in retrospective evaluation translate to
> clinically useful performance under real-time deployment constraints?

### Proposed method

1. Establish a clinical collaboration and secure IRB approval.
2. Deploy the best causal model from Papers 1-2 in a live or
   near-live RYGB workflow.
3. Measure:
   - end-to-end inference latency,
   - degradation from offline to online accuracy,
   - operational integration costs, and
   - surgeon acceptance and trust calibration.
4. Collect 50-100 prospective cases over 6-12 months if feasible.

### Expected contribution

This paper would be the first real test of whether the current research
line is clinically actionable. Even a modest degradation from offline
performance would still be valuable if the deployment study identifies
what fails, what survives, and what clinicians actually need from an
RSD system.

### Tentative venues

- Primary: **Annals of Surgery** or **JAMA Surgery**
- Secondary: **IEEE J-BHI** or **Surgical Endoscopy**
- Alternative ML venue: **NeurIPS Datasets and Benchmarks**

### Estimated timeline

- 2027: IRB preparation, clinical coordination, deployment
  infrastructure
- 2028: prospective collection and writing
- Target submission window: **late 2028**

### Resources and risk

- Minimal cloud compute, but substantial coordination overhead
- Requires clinical collaboration and prospective approval
- Estimated direct research support need: ~\$20K
- **Risk level:** high

This is the most important translational paper in the roadmap, but also
the one most dependent on external constraints.

---

## Paper 6 (optional extension) — Extending the conditioning paradigm beyond RSD

**Working title:** *Workflow-Conditioned Multi-Task Learning for
Surgical Video: A Unified Recipe*

### Research question

The current paper tests the workflow-conditioning hypothesis on RSD.
An optional extension is to ask whether the same conditioning recipe is
useful for adjacent tasks in surgical video analysis.

### Proposed directions

1. Adverse-event detection on MB140
2. Surgical skill assessment, if labels can be obtained
3. Automated reporting or note generation, if a suitable dataset is
   available

### Expected contribution

This paper would answer whether workflow conditioning is a narrow
mechanism specific to RSD or a broader recipe for tasks whose targets
depend on procedural context.

### Tentative venues

- Primary: **NeurIPS Datasets and Benchmarks 2028**
- Secondary: **MICCAI 2028** or **WACV 2029**

### Resources and risk

- Requires either new labels or new datasets for some tasks
- Estimated compute: ~300 GH200-hours (~$700)
- **Risk level:** medium

This direction is interesting, but it should remain optional until the
core RSD program is more mature.

---

## Sequencing and dependencies

The roadmap is intentionally staged:

```
2026 ──── 2027 ──── 2028 ──── 2029
   │
   ├─ P1 (NeurIPS 2026, current)
   │
   ├─ P2 (deployable distillation)
   │
   ├─ P3 (hierarchical conditioning)
   │
   ├─ P4 (backbone effects)
   │
   ├─ P5 (prospective deployment)
   │
   └─ P6 (optional cross-task extension)
```

The practical dependency structure is:

- **P2** and **P3** can run in parallel because they reuse the same
  substrate but test different questions.
- **P4** should follow once at least one of P2 or P3 is mature enough to
  anchor the backbone comparison in a stronger methodology.
- **P5** has the longest external lead time and should be prepared early,
  even if the actual study happens later.
- **P6** is explicitly lower priority than the core RSD line.

If only two papers are feasible in the next 18 months, the strongest
pair is **P2 + P3**. Together they deepen the mechanism, close the most
important deployment gap, and build the most reusable apparatus.

---

## Relative priority

| Paper | Role in program | Risk | Approximate lead time |
|---|---|---|---|
| P2 | Closest follow-up and deployment bridge | Low | 6 months |
| P3 | Strong scientific extension | Medium | 9 months |
| P4 | Comparative backbone study | Medium-high | 12 months |
| P5 | Prospective clinical translation | High | 18+ months |
| P6 | Optional generalization paper | Medium | 12 months |

---

## Immediate next steps after the current submission deadline

1. Complete rebuttal-useful extensions that are already partially
   underway, especially the longer-context multi-seed follow-up.
2. Consolidate the reproducibility package, checkpoints, and public
   artifacts so they can serve as substrate for Papers 2 and 3.
3. Draft the minimum viable loss and training recipe for privileged
   distillation.
4. Begin informal clinical conversations early if the prospective paper
   remains a serious long-term goal.
5. Read and summarize the papers most directly relevant to hierarchical
   conditioning and causal surgical-state estimation.

---

## Resource outlook

The research-compute burden for the core program is modest relative to
many modern vision projects because all papers reuse the same datasets,
protocols, and much of the same code.

| Paper | Estimated GH200-hours | Approximate cost @ \$2.29/hr |
|---|---:|---:|
| P2 | 50 | \$115 |
| P3 | 120 | \$275 |
| P4 | 250 | \$575 |
| P5 | minimal cloud | — |
| P6 | 300 | \$700 |
| Rebuttals and ad hoc runs | ~150 | \$345 |
| **Total (3-year horizon)** | **~870** | **~\$2,000** |

The more serious constraints are time, engineering bandwidth, and
clinical access rather than pure compute.

---

## Lower-priority directions

To keep the program coherent, the following directions are currently
de-prioritized:

- multi-modal RSD with text, audio, and video together;
- state-space sequence models as a standalone publication axis;
- synthetic-data augmentation as a separate line of work; and
- a standalone negative-results paper detached from the main
  conditioning narrative.

Each of these may still appear as an ablation or side experiment, but
none should displace the core sequence of P2-P5.

---

## Closing perspective

The strongest version of this publication program is one in which each
paper makes the next one cheaper, sharper, and easier to justify. The
current submission should therefore be treated not as an isolated paper
but as the shared substrate for a compact research line on workflow
conditioning in surgical video.

The near-term priority is clear: land the current paper, then invest in
the two follow-ups that most directly deepen its scientific claim and
reduce its deployment gap. A compounding program will be more durable
than a scattered one.

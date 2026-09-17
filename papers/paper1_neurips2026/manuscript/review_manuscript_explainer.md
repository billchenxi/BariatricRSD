# Detailed Project Explainer and Current Status

**Last updated:** Sunday, April 26, 2026 09:47 AM Pacific time  
**Timezone note:** you asked for `PST`. The machine clock reports `PDT`, but in this document I write times as **Pacific time** and keep raw UTC times from the session log when useful.  
**Purpose:** this is the document you should read if you want to understand, in plain English, what the paper is about, what Claude has been doing, what I changed, what the current experiments mean, and what is still missing.

---

## 1. What this document is for

This is **not** the paper.

This is the human-readable guide to the paper and the repo. It tries to answer:

1. What problem are we solving?
2. What is the actual scientific idea?
3. What code paths and experiment families exist in the repo?
4. What has Claude been doing?
5. What have I changed?
6. What do the run numbers mean?
7. What can the paper honestly claim right now?
8. What results are real, which are pending, and which are only upper bounds?
9. Which figures are already done, and which figures still depend on pending experiments?

If you only read **one** internal document, read this one.

---

## 2. One-page summary

The paper is about **remaining surgery duration prediction**:

> Given the video of a surgery partway through the case, can a model predict how much time is left?

The key scientific idea is:

> This problem is easier if the model knows **which workflow pattern** the case is following.

That matters because the same nominal operation can be done in different orders by different surgeons or different hospitals.

The paper compares this idea on two benchmarks:

- **MultiBypass140**: multicenter gastric bypass, real workflow variation, wider duration variation
- **Cholec80**: single-center cholecystectomy, much more standardized workflow

The real contribution is **not** “we invented a magic new architecture.”

The real contribution is:

> Workflow conditioning helps when workflow variation is real, and helps little or can even hurt when the benchmark is already standardized.

That is why this is strongest as a **NeurIPS Evaluations & Datasets** paper.

---

## 3. The shortest honest version of the paper

If you had to explain the work to someone in 30 seconds, say this:

> We are studying whether explicit workflow information helps predict remaining surgery time. On MultiBypass140, which has real multicenter workflow diversity, it helps. On Cholec80, which is much more standardized, it is mostly neutral or harmful. So benchmark heterogeneity changes the conclusion. Retrospective workflow labels are a useful upper bound, but the real deployable question is how much of that gain survives under strict prefix-only pixel-based inference.

That is the current center of gravity of the project.

---

## 4. What problem the model is solving

Imagine an operating room coordinator asking:

> “This surgery has already been running for 50 minutes. How much longer will it take?”

Why this matters:

- downstream cases may already be waiting
- anesthesia planning depends on remaining time
- room turnover depends on remaining time
- delays propagate through the whole OR schedule

From the machine-learning side:

- input = video frames seen so far
- output = remaining duration

At first glance that sounds like ordinary regression. It is not.

Two surgeries with the same operation name may still follow different trajectories.

Example:

- **Case A**: pouch creation -> gastro-jejunal anastomosis -> jejuno-jejunal anastomosis
- **Case B**: pouch creation -> jejuno-jejunal anastomosis -> gastro-jejunal anastomosis

If the model does not know which path it is inside, it produces a blurry average prediction.

So the core intuition is:

> Knowing the current **workflow family** should improve the duration prediction.

---

## 5. The four settings you must keep separate

This is the biggest source of confusion in the paper and in the code discussion.

### 5.1 No-token baseline

The model only sees:

- video frames

It does **not** get a workflow token.

This is the main control condition.

### 5.2 Oracle / retrospective workflow token

The model gets a workflow token built from the **entire surgery**, including parts that happen after the current prediction time.

This is:

- scientifically useful
- **not** deployable

This answers:

> If I knew the true workflow identity perfectly, how much would that help?

So this is an **upper bound**.

### 5.3 Teacher-forced prefix token

The token is built from the surgical prefix only, but using the **ground-truth phase labels** of that prefix.

This is better than full oracle in one sense, but it is still not a fully deployable result, because a real deployed model would not have true phase labels at test time.

This answers:

> If I only use the prefix, but I still know the correct phases in that prefix, does workflow conditioning help?

That is a useful intermediate analysis.

### 5.4 True pixel-only causal inference

This is the real end goal.

At inference time the model should use:

- only the pixels seen so far

Then it should:

1. infer phases from the video
2. turn those predicted phases into a workflow posterior
3. use that posterior as the workflow-conditioning signal
4. predict remaining time

This is the only version that cleanly supports a deployable claim.

### 5.5 The table version

| Setting | Uses future information? | Uses ground-truth phase labels at inference? | Deployable? |
|---|---|---|---|
| No-token | No | No | Yes |
| Oracle / retrospective | Yes | Yes | No |
| Teacher-forced prefix | No future, but still uses phase labels | Yes | No |
| True pixel-only causal | No | No | Yes |

If you remember one conceptual table, remember this one.

---

## 6. Why there are two datasets

The datasets are there to answer **different scientific questions**.

### 6.1 MultiBypass140

This is the important benchmark for the paper’s main claim.

Why:

- multicenter
- longer surgeries
- real workflow diversity
- real duration diversity
- center-specific differences matter

If workflow conditioning matters anywhere, it should matter here.

### 6.2 Cholec80

This is the contrast case.

Why:

- more standardized
- less workflow diversity
- most cases follow a dominant pattern

This makes it useful for asking:

> What happens when we apply workflow conditioning to a benchmark that does not really need it?

That is why a **null or negative Cholec80 result** is not a failure. It is part of the point.

---

## 7. The clean scientific claim

The strongest claim the project is trying to support is:

> The value of workflow conditioning scales with the amount of workflow heterogeneity present in the benchmark.

That implies:

- MultiBypass140 should show a positive effect
- Cholec80 should show a weak, null, or negative effect
- cross-center transfer may remain hard even if workflow conditioning helps within-center

This is more of an **evaluation principle** than a pure architecture contribution.

---

## 8. What Claude has been doing

This section is based on the repo plus `SESSION_LOG.md`, not on hidden chat history.

From the log and file structure, Claude has been doing most of the following:

### 8.1 Lambda training and queue management

Claude set up and managed the main Lambda training/evaluation queue, including many of these scripts:

- [run023_causal_mb140_fold0.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run023_causal_mb140_fold0.sh:1)
- [run024_causal_cholec80.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run024_causal_cholec80.sh:1)
- [run025_adam_smooth_eval.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run025_adam_smooth_eval.sh:1)
- [run026_5fold_no_token.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run026_5fold_no_token.sh:1)
- [run027_5fold_causal.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run027_5fold_causal.sh:1)
- [run028_cross_center_causal.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run028_cross_center_causal.sh:1)
- [run029_k_cluster_sweep.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run029_k_cluster_sweep.sh:1)
- [run030_pixel_only_causal_eval.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run030_pixel_only_causal_eval.sh:1)
- [run031_per_video_metric.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run031_per_video_metric.sh:1)
- [run033_strict_protocol_fold0.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run033_strict_protocol_fold0.sh:1)
- [run034_strict_protocol_cross_center.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run034_strict_protocol_cross_center.sh:1)
- [run036_dump_per_clip_csvs.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run036_dump_per_clip_csvs.sh:1)

### 8.2 The `lambda_setup` stack

Claude also built or extended the separate Lambda-focused training stack under:

- [lambda_setup/src/data/dataset.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/data/dataset.py:1)
- [lambda_setup/src/models/bariatric_rsd.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/models/bariatric_rsd.py:1)
- [lambda_setup/src/training/train.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/training/train.py:1)
- [lambda_setup/src/training/train_causal.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/training/train_causal.py:1)

### 8.3 The paper skeleton and review manuscript

Claude has also been heavily editing:

- [review_manuscript.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/review_manuscript.md:1)
- [results_manifest.csv](/Users/bill/Documents/GitHub/bariatric_rsd/paper/results_manifest.csv:1)
- [EXPERIMENT_PLAN.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/EXPERIMENT_PLAN.md:1)
- [FIGURE_ROADMAP.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/FIGURE_ROADMAP.md:1)

### 8.4 Figure builders and figure queue

The newest log entries show Claude adding builder scripts for the future main-paper figures:

- [build_fig8_strict_mb140.py](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/build_fig8_strict_mb140.py:1)
- [build_fig9_progress_curves.py](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/build_fig9_progress_curves.py:1)
- [build_fig10_strict_cross_center.py](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/build_fig10_strict_cross_center.py:1)
- [build_fig11_diagnostic_chain.py](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/build_fig11_diagnostic_chain.py:1)
- [build_fig12_paired_diff.py](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/build_fig12_paired_diff.py:1)

Those are meant to consume the outputs of Runs 033–036.

---

## 9. What I changed

I have mainly been acting as:

- code reviewer
- claim reviewer
- protocol auditor
- patch author for the strict protocol / causal-eval plumbing

### 9.1 I audited the paper-critical path

I reread the active training and evaluation code and identified the main credibility issues:

1. future-frame leakage from centered windows
2. teacher-forced causal evaluation
3. phase/token circularity
4. checkpoint selection on clip-weighted MAE while the paper reports per-video MAE

### 9.2 I added the leakage explanation figure

I added:

- [fig3c_centered_window_leakage.png](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/fig3c_centered_window_leakage.png)
- [fig3c_centered_window_leakage.pdf](/Users/bill/Documents/GitHub/bariatric_rsd/paper/figures/fig3c_centered_window_leakage.pdf)

and wired it into:

- [review_manuscript.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/review_manuscript.md:429)

### 9.3 I rewrote the active experiment plan

I replaced the older long sprint plan with a simpler “must-run / nice-to-have / cut-if-needed / stop-rules” structure in:

- [EXPERIMENT_PLAN.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/EXPERIMENT_PLAN.md:1)

### 9.4 I patched the strict-protocol plumbing and committed it

I made two local commits:

- `bca87a2` — `Patch strict protocol and causal eval plumbing`
- `b3c6968` — `Make strict pixel-only eval script executable`

Those commits:

- added strict-protocol support directly into the checked-in `lambda_setup` stack
- added the missing strict pixel-only evaluator script
- fixed CLI mismatches
- made the queue reproducible from repo code

### 9.5 I added the missing strict pixel-only causal eval step

This is important.

Before my patch, `Run 033` and `Run 034` produced:

- strict no-token
- strict oracle
- strict decoupled-oracle

But **not** the actual strict pixel-only causal row.

I added:

- [run035_strict_pixel_only_eval.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run035_strict_pixel_only_eval.sh:1)

to generate the true strict pixel-only causal evaluation on the strict checkpoints.

### 9.6 I added the figure roadmap

I mapped future experiments to exact paper figures in:

- [FIGURE_ROADMAP.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/FIGURE_ROADMAP.md:1)

---

## 10. The code paths you should know

There are several partially overlapping stacks in this repo. That is another reason the project feels confusing.

### 10.1 Root/original stack

Examples:

- `models/`
- `training/`
- `evaluate.py`

This appears to be the older original project path.

### 10.2 `lambda_setup` stack

Examples:

- [lambda_setup/src/data/dataset.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/data/dataset.py:1)
- [lambda_setup/src/models/bariatric_rsd.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/models/bariatric_rsd.py:1)
- [lambda_setup/src/training/train.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/training/train.py:1)

This is the paper-critical training stack for the current Lambda runs.

### 10.3 `brsd_lib`

Examples:

- [causal_cluster.py](/Users/bill/Documents/GitHub/bariatric_rsd/brsd_lib/causal_cluster.py:1)
- [evaluate.py](/Users/bill/Documents/GitHub/bariatric_rsd/brsd_lib/evaluate.py:1)
- [compute_residuals.py](/Users/bill/Documents/GitHub/bariatric_rsd/brsd_lib/compute_residuals.py:1)
- [stats.py](/Users/bill/Documents/GitHub/bariatric_rsd/brsd_lib/stats.py:1)

This is the cleaner paper-side evaluation / analysis library.

### 10.4 `codex_workflow`

Examples:

- `codex_workflow/*`

This is the separate clean-room causal rewrite I started earlier. It is **not** the main paper path right now.

---

## 11. The run numbers explained

This is the most practical section in the document.

### 11.1 Historical / baseline runs

| Run | Meaning |
|---|---|
| `Run 010` | MB140 fold-0 oracle / retrospective workflow-token baseline |
| `Run 016` | Cholec80 oracle |
| `Run 017` | Cholec80 no-token baseline |
| `Run 018` | MB140 -> Cholec80 transfer / secondary Cholec80 absolute number path |
| `Run 019` | Cholec80 ensemble / TTA / isotonic secondary analysis |

### 11.2 Teacher-forced “causal” family

| Run | Meaning |
|---|---|
| `Run 023` | MB140 fold-0 teacher-forced prefix workflow token |
| `Run 024` | Cholec80 teacher-forced prefix workflow token |
| `Run 027` | 5-fold teacher-forced causal family |
| `Run 028` | cross-center teacher-forced prefix |

These are useful, but they are **not** the final deployable-causal result.

### 11.3 Repair and strict-protocol family

| Run | Meaning |
|---|---|
| `Run 030` | true pixel-only causal eval on the older centered-window checkpoints |
| `Run 031` | re-extract per-video MAE on existing checkpoints |
| `Run 032` | phase-cluster sensitivity / diagnostic step |
| `Run 033` | strict prefix-only fold-0 training: no-token / oracle / decoupled-oracle |
| `Run 034` | strict prefix-only cross-center training |
| `Run 035` | strict pixel-only causal eval on the strict checkpoints |
| `Run 036` | per-clip CSV dumps for figures that need progress-binned rows |

This `030–036` range is the most important current block.

---

## 12. What the current results mean

### 12.1 MultiBypass140 within-center

The main story is:

- workflow conditioning helps
- the effect is real
- the effect is smaller than the older draft suggested

The old “about 1 minute” story came from comparing to a weaker baseline.

The newer matched baseline makes the improvement look more like a **modest but real** effect.

### 12.2 Cross-center MB140

The important insight is:

- workflow conditioning does not solve cross-center transfer

That is not bad news. It is scientifically important.

It suggests the main remaining problem is not simple workflow order. It is more likely:

- visual domain shift
- center-specific style
- hardware / image differences
- broader distribution shift

### 12.3 Cholec80

The Cholec80 result is mostly a contrast case:

- oracle is nearly neutral
- noisy workflow inference hurts

That supports the paper’s main thesis, because Cholec80 does not have enough workflow diversity to reward this kind of conditioning.

### 12.4 Cholec80 absolute best number

The `3.56` minute Cholec80 result is still secondary.

It depends heavily on:

- non-canonical split
- ensemble
- TTA
- isotonic post-processing

That is why it should **not** be the center of the paper.

### 12.5 Pure leaderboard reading

If you ignore, for a moment, all the honesty and deployability caveats and ask
only:

> "What gave the lowest number on each benchmark?"

then the answer is:

| Dataset / regime | Numerical winner | Best MAE | What actually produced the win |
|---|---|---:|---|
| MB140 within-center | Teacher-forced prefix | 12.56 ± 0.04 | Workflow conditioning |
| MB140 cross-center | Oracle | 18.05 | Tiny edge over no-token; teacher-forced prefix fails |
| Cholec80 validation | Oracle | 4.49 ± 0.14 | Basically a null gain versus no-token |
| Cholec80 test | Ensemble + TTA + isotonic | 3.56 | Mostly isotonic post-processing |

This is an important result, because it says the "winning trick" is not the
same on every dataset.

Plain English:

- on **MultiBypass140**, adding workflow information is the thing that helps
- on **Cholec80**, the biggest gain comes from post-processing, not from workflow conditioning

So if someone only looks at the final MAE table, the message should still be:

> MultiBypass140 is where workflow conditioning earns its keep. Cholec80 is where monotonic post-processing earns its keep.

That is one of the clearest reasons this paper should not be written as
"our workflow-conditioned model wins everywhere." It does not. It wins in the
place where workflow diversity is real.

---

## 13. What the paper can honestly claim right now

The safest strong version is:

> Workflow conditioning helps remaining-duration prediction when the benchmark truly contains workflow heterogeneity. MultiBypass140 reveals this effect; Cholec80 mostly does not. Retrospective workflow labels provide a useful upper bound, and the strict pixel-only causal experiments are the key remaining test of how much of that gain survives in a deployable setting.

Strong claims you can make:

- workflow variation matters
- benchmark choice changes the conclusion
- MultiBypass140 is more informative than Cholec80 for this question
- on raw MAE alone, MB140 is won by workflow conditioning while Cholec80 is won by isotonic-style post-processing
- retrospective workflow tokens are a useful upper bound
- cross-center shift remains hard

Claims you should avoid until the strict results land:

- “we already proved deployable causal parity with oracle”
- “we solved cross-center generalization”
- “workflow conditioning gives about a 1-minute gain”
- “we beat SOTA because of workflow conditioning”

---

## 14. What was confusing before, and what changed

### 14.1 Previous confusion

The older manuscript and queue logic blurred:

- teacher-forced prefix
- true deployable pixel-only causal

It also mixed:

- centered-window retrospective numbers
- what sounded like online deployable claims

### 14.2 What changed

The project is now more explicit about:

- leakage
- retrospective oracle vs teacher-forced prefix vs true pixel-only causal
- strict prefix-only protocol
- phase/token circularity
- per-video metric re-extraction

The current docs that express that most clearly are:

- [review_manuscript.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/review_manuscript.md:1)
- [EXPERIMENT_PLAN.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/EXPERIMENT_PLAN.md:1)
- [FIGURE_ROADMAP.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/FIGURE_ROADMAP.md:1)

---

## 15. The strict protocol, in plain English

The strict protocol exists to answer:

> If we remove the obvious loopholes, does the workflow-conditioning effect still survive?

The strict protocol does two main things:

1. **prefix-ending clips**
   - the clip label is moved to the **last** frame, not the middle frame
   - this removes future-frame leakage inside the clip

2. **decoupled phase head**
   - the phase head is made less circular with respect to the workflow token
   - this helps make the causal evaluator more honest

Then `Run 035` evaluates strict pixel-only causal inference on those strict checkpoints.

That is why `Run 035` is so important.

---

## 16. The latest repo changes you should know about

These are the most important recent changes after the earlier explainer:

### 16.1 Strict-protocol support is now in the checked-in repo

The strict protocol is no longer only an idea in the log. It is now directly represented in:

- [lambda_setup/src/data/dataset.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/data/dataset.py:192)
- [lambda_setup/src/models/bariatric_rsd.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/models/bariatric_rsd.py:272)
- [lambda_setup/src/training/train.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/src/training/train.py:196)

### 16.2 The patch helper path mismatch was fixed

The queue scripts expected:

- `scripts/11_apply_protocol_patches.py`

That now exists in the repo and is also mirrored by:

- [lambda_setup/scripts/11_apply_protocol_patches.py](/Users/bill/Documents/GitHub/bariatric_rsd/lambda_setup/scripts/11_apply_protocol_patches.py:1)

### 16.3 The missing strict pixel-only eval step was added

This is the newest crucial addition:

- [run035_strict_pixel_only_eval.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run035_strict_pixel_only_eval.sh:1)

### 16.4 The figure pipeline was extended

There are now dedicated builder scripts for the future main-paper figures:

- Figure 8
- Figure 9
- Figure 10
- Figure 11
- Figure 12

plus:

- `Run 036` for per-clip CSVs that those figures need

---

## 17. Last logged queue state

This is the **last logged** queue state from `SESSION_LOG.md`. It is not a live poll from this turn.

As of the last detailed log entry:

| Cluster | Last logged chain | Last logged ETA |
|---|---|---|
| A | `Run 022 -> Run 030 -> Run 031 -> Run 032` | early Sunday morning Pacific (`2026-04-26 09:00 UTC`) |
| B | `Run 029 -> Run 033` | Sunday afternoon / evening Pacific (`2026-04-27 00:00 UTC`) |
| C | `Run 026 -> Run 034 -> Run 035 -> Run 036` | late Sunday night / early Monday Pacific (`2026-04-27 12:00 UTC`) |
| D | `Run 027` then idle | Sunday morning / midday Pacific (`2026-04-26 14:00 UTC`) |

Read this carefully:

- this is the **last recorded queue state**
- it may already have moved forward since the log entry
- the point is to explain the plan and dependencies, not to pretend this document is a live dashboard

---

## 18. The figure plan, in plain English

The new figure plan is documented separately in:

- [FIGURE_ROADMAP.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/FIGURE_ROADMAP.md:1)

The important part is:

### Figure 8

Strict MB140 main result:

- strict no-token
- strict oracle
- strict decoupled-oracle
- strict pixel-only causal

### Figure 9

MAE over surgery progress:

- when does workflow information start helping?

### Figure 10

Strict within-center vs strict cross-center:

- shows that workflow conditioning is not the main cure for transfer

### Figure 11

Phase -> cluster -> RSD diagnostic chain:

- explains the mechanism

### Figure 12

Paired per-video difference plot:

- shows whether gains are broad or driven by a few cases

---

## 19. The reading order I recommend

If you want to understand the project without getting lost, read in this order:

1. this file  
   [review_manuscript_explainer.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/review_manuscript_explainer.md:1)

2. the current paper draft for reviewers  
   [review_manuscript.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/review_manuscript.md:1)

3. the active experiment plan  
   [EXPERIMENT_PLAN.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/EXPERIMENT_PLAN.md:1)

4. the figure plan  
   [FIGURE_ROADMAP.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/FIGURE_ROADMAP.md:1)

5. the latest queue / implementation narrative  
   [SESSION_LOG.md](/Users/bill/Documents/GitHub/bariatric_rsd/SESSION_LOG.md:1)

---

## 20. What is still unresolved

The biggest unresolved scientific question is still:

> After removing the obvious loopholes, how much of the workflow-conditioning effect survives under strict pixel-only causal inference?

That is the question `Run 033 + Run 034 + Run 035` are trying to answer.

Other unresolved points:

- exact strict cross-center behavior
- progress-binned behavior for the strict causal model
- whether gains are broad across videos or sparse
- whether the shuffled-token control confirms semantic value

---

## 21. What I think the paper becomes depending on the strict results

### Best case

If strict pixel-only causal:

- beats strict no-token
- stays reasonably close to oracle
- still shows the expected Cholec80 null / negative result
- still struggles cross-center

then the paper becomes a strong E&D submission and maybe has a Main Track upgrade path.

### Middle case

If strict causal helps, but much less than oracle:

then the paper is still good, but the story is:

> retrospective workflow conditioning is informative, but deployable workflow inference is harder than teacher-forced numbers suggest

### Negative case

If strict causal collapses:

the paper is still publishable as an E&D paper if it is written honestly:

> benchmark heterogeneity matters, retrospective gains exist, but deployable causal workflow inference is harder and more protocol-sensitive than earlier drafts implied

That is still a meaningful contribution.

---

## 22. What you should say in meetings

Safe version:

> Our main result is that workflow conditioning matters when workflow heterogeneity is real. MultiBypass140 shows that effect; Cholec80 mostly does not. The strict causal protocol is the key remaining test of how much of that benefit survives in a deployable setting.

Stronger but still honest version:

> The contribution is not that we built one more model. It is that we clarified when workflow-aware duration prediction should be expected to help at all, and we are now stress-testing that conclusion under a stricter causal protocol.

What not to say:

- “we solved deployable causal inference”
- “we already proved oracle-level online performance”
- “we beat SOTA because of workflow conditioning”

---

## 23. Bottom line

If you strip away the run numbers and the queue machinery, the project currently says:

> Remaining surgery duration prediction is partly a workflow-heterogeneity problem. Whether workflow-aware modeling helps depends strongly on the benchmark. MultiBypass140 exposes that effect; Cholec80 mostly hides it. Retrospective workflow labels are a useful upper bound, and the strict prefix-only pixel-only experiments are the crucial test of how much of that insight survives in a truly deployable form.

That is the cleanest way to understand where the project stands today.

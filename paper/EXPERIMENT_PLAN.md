# Experiment Plan — Active Submission Plan

**Last revised:** 2026-04-25  
**Target:** NeurIPS 2026 Evaluations & Datasets by default; Main Track only if the strict causal result is genuinely strong  
**Purpose:** Maximize publication probability, not just lower one benchmark number

---

## 1. What This Paper Must Prove

The paper becomes publishable if it supports this claim cleanly:

> Workflow conditioning helps remaining-duration prediction when workflow variability is real, and benchmark choice determines whether that effect is visible.

That means the submission should prioritize:

1. **Clean MB140 evidence**: no-token vs oracle vs causal
2. **A truthful deployability story**: how much survives under pixel-only / prefix-only inference
3. **A contrast case**: Cholec80 as a null or negative result
4. **A negative but informative transfer result**: cross-center MB140

The paper does **not** need:

- a Cholec80 SOTA headline
- more inference-time trick tuning
- more architecture variety than is needed to close the current credibility gaps

---

## 2. Current Publication Blockers

These are the four issues most likely to trigger reviewer skepticism or rejection:

1. **Future-frame leakage**  
   The active dataset predicts the middle frame of a centered window, so the model still sees a few frames after the target timestamp.

2. **Teacher-forced causal training / evaluation**  
   The current causal path uses prefix clusters built from ground-truth phase labels, which is useful scientifically but not the same as deployable inference.

3. **Phase/token circularity**  
   The phase head used to recover workflow state is affected by the workflow token itself in the current model path.

4. **Metric mismatch**  
   Training selects checkpoints on clip-weighted MAE, while the manuscript reports per-video MAE.

All next experiments should be judged by how directly they reduce one or more of these four risks.

---

## 3. Must-Run Experiments

These are the experiments that most improve the chance of acceptance. If time or compute gets tight, protect these first.

| ID | Experiment | Why it matters | Risk closed | Expected cost |
|---|---|---|---|---:|
| MR1 | **Run 031**: re-evaluate all headline checkpoints under per-video MAE | Aligns manuscript metric with actual reported results | #4 | Low |
| MR2 | **Run 030**: true pixel-only causal evaluation on existing checkpoints | Tests whether the deployable story survives without phase-label leakage at inference | #2 | Low-moderate |
| MR3 | **Strict prefix-only fold-0 protocol**: retrain no-token, oracle, and causal under `target_position=last` or equivalent prefix-ending clips | Removes future-frame leakage from the core comparison | #1 | Moderate |
| MR4 | **Decoupled phase-head fold-0 protocol**: phase head predicts from visual/temporal features before workflow-token conditioning | Removes phase/token circularity from the causal story | #3 | Moderate |
| MR5 | **Strict pixel-only causal eval on the strict checkpoints** | Converts the strict training checkpoints into the actual deployable-causal row | #2, #3 | Low-moderate |
| MR6 | **Cross-center strict causal evaluation** | Prevents the paper from sounding within-center only | #1, #2, #3 | Moderate |

### Deliverable from the must-run block

At submission, the paper should contain:

- one **clean within-center MB140 table** with `no-token`, `oracle`, `strict causal`
- one **cross-center MB140 table**
- one **Cholec80 contrast table**
- one sentence explicitly stating whether strict causal stayed close to oracle or not

---

## 4. Nice-to-Have Experiments

These are valuable if the core evidence is already locked, but they should not delay the must-run block.

| ID | Experiment / analysis | Why it helps |
|---|---|---|
| NH1 | **Soft-posterior / train-test aligned causal training** | Best next attempt if strict causal loses too much relative to oracle |
| NH2 | **Time-of-surgery MAE curves** at 10/25/50/75/90% progress | Likely the best single figure for the paper |
| NH3 | **Diagnostic chain**: phase accuracy, cluster recovery, RSD MAE over progress | Explains why MB140 helps, Cholec80 does not, and cross-center fails |
| NH4 | **Shuffled-token control** on MB140 fold 0 | Shows the token helps because it carries workflow semantics, not just extra parameters |
| NH5 | **Bootstrap CIs + paired Wilcoxon** | Important for E&D credibility; should be considered near-mandatory analysis |
| NH6 | **Failure-case panels** | Good reviewer-facing qualitative support |

---

## 5. Cut-If-Needed Work

These are the first things to drop if schedule or compute becomes tight.

1. More Cholec80 SOTA chasing
2. More post-processing sweeps
3. RSDNet baseline
4. Surgical-domain pretraining
5. K-cluster sweep
6. Any larger backbone sweep

These can improve the appendix, but they do not fix the current publication blockers.

---

## 6. Recommended Queue

This is the execution order that best improves publication odds.

### Phase A — Finish measurement repair

1. **Run 031**
   - Goal: replace clip-weighted numbers with per-video numbers everywhere they matter
   - Output: one clean ledger for all existing checkpoints

2. **Run 030**
   - Goal: get the honest pixel-only causal number on existing checkpoints
   - Output: whether the current causal story survives at all

### Phase B — Fix the protocol

3. **Strict prefix-only fold-0 no-token**
   - Goal: establish honest baseline under prefix-ending clips

4. **Strict prefix-only fold-0 oracle**
   - Goal: measure how much workflow conditioning helps when future-frame leakage is removed

5. **Strict prefix-only fold-0 decoupled-oracle**
   - Goal: evaluate the cleanest non-circular training path before pixel-only causal inference

6. **Strict pixel-only eval on the strict checkpoints**
   - Goal: turn strict no-token / strict oracle / strict decoupled-oracle into the real strict causal row

### Phase C — Only if Phase B is promising

7. **Soft-posterior / train-test aligned causal fold-0**
   - Goal: recover some of the gap between strict causal and oracle

8. **Cross-center strict causal**
   - Goal: determine whether the causal effect is only within-center

### Phase D — Paper-strengthening analyses

See also [FIGURE_ROADMAP.md](/Users/bill/Documents/GitHub/bariatric_rsd/paper/FIGURE_ROADMAP.md:1) for the exact figure outputs these analyses are meant to produce.

9. **Time-of-surgery curves**
10. **Diagnostic chain**
11. **Shuffled-token control**
12. **Bootstrap CIs and paired tests**
13. **Failure-case panels**

### Phase E — 5-fold extension only if justified

14. **5-fold strict causal**
   - Run this only if fold 0 shows a real effect

---

## 7. Stop Rules

These rules exist to prevent wasted compute and to keep the paper honest.

| Trigger | Interpretation | Action |
|---|---|---|
| Run 030 pixel-only causal is much worse than the teacher-forced result | The current causal story is fragile | Downgrade current causal result to an intermediate analysis, not a deployable claim |
| Strict prefix-only no-token is much worse than old centered-window no-token | Future-frame leakage was materially helping | Treat old results as retrospective only; do not use them to support deployability |
| Strict prefix-only oracle does not beat strict no-token | Workflow conditioning may not survive the honest protocol | Pivot the paper to an evaluation-insight paper |
| Strict causal with decoupled phase head does not beat strict no-token | The deployable causal claim does not stand | Report negative result; do not launch 5-fold strict causal |
| Soft-posterior causal does not improve over strict causal | Train-test alignment did not help | Skip further causal training variants |
| Cross-center strict causal fails badly | Workflow conditioning is not the main transfer solution | Keep as a key negative result, not a failure of the paper |

---

## 8. Decision Tree for Submission

### Best case

If the strict prefix-only causal model:

- beats strict no-token on MB140
- stays reasonably close to oracle
- still fails or weakens on Cholec80
- still struggles cross-center

then the paper becomes:

> A strong E&D paper, and possibly a Main Track paper if the causal protocol is truly clean and the gap to oracle is small.

### Middle case

If strict causal helps on MB140 but loses a lot relative to oracle:

the paper becomes:

> A solid E&D paper showing that retrospective workflow conditioning is informative, but deployable causal workflow inference is harder than teacher-forced numbers suggest.

### Negative-but-still-publishable case

If strict causal collapses:

the paper becomes:

> An E&D paper about benchmark heterogeneity, protocol sensitivity, and the danger of overstating teacher-forced workflow conditioning as deployable inference.

That is still publishable if written correctly.

---

## 9. Exact Recommendation for the Paper Story

Until the strict protocol runs are done, write the paper as if the likely final contribution is:

1. **MB140 reveals workflow-conditioning effects that Cholec80 mostly hides**
2. **Retrospective oracle workflow labels are a useful upper bound**
3. **Teacher-forced prefix conditioning is an informative intermediate result**
4. **True deployable causal inference must be evaluated separately**
5. **Cross-center shift remains the dominant unsolved problem**

Do not write the paper as:

- “we beat SOTA”
- “we already proved deployable causal workflow inference”
- “workflow conditioning solves surgical duration prediction”

---

## 10. Minimal Submission Package

If time becomes extremely tight, this is the smallest package still worth submitting:

1. `Run 031` completed
2. `Run 030` completed
3. One strict prefix-only fold-0 comparison: `no-token`, `oracle`, `strict causal`
4. One strict pixel-only causal result on the strict protocol
5. One cross-center strict causal result
6. One Cholec80 contrast table
7. One strong progress-over-time or diagnostic figure
8. Statistical support on per-video MAE
9. Tight wording discipline around retrospective vs causal

Everything beyond that is upside, not requirement.

---

## 11. Working Rule

From this point on:

- do not spend a GPU-hour on a new benchmark trick if it does not reduce one of the four core publication blockers
- do not add a new model family before the strict prefix-only protocol exists
- do not claim more than the strictest completed experiment supports

That is the plan most likely to convert this repo into a publishable paper.

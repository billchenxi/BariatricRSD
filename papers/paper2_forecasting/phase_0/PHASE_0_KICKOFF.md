# Phase 0 Kickoff Checklist

> **Note (2026-09-17):** references below to `NEXT_PAPER_PLAN.md`,
> `NEXT_PAPER_BRIEF.md`, or `PAPER_2A_REVIEWER_HARDENING.md` now resolve to
> [`docs/STRATEGY.md`](../../../plans/STRATEGY.md), which merged them. Originals are at
> git commit `1511e55`.

*Paper 2A infrastructure work. Target duration: ~4 weeks. Compute budget:
$250 (per `NEXT_PAPER_PLAN.md` §Phase 0). Extended with hardening items
from `PAPER_2A_REVIEWER_HARDENING.md`.*

**Goal:** by the end of Phase 0, know exactly which backbones can run,
which datasets are accessible, which workflow-representation families
compile, and which foundation-model checkpoints are worth carrying into
the Phase 1 scout matrix. Nothing large gets trained yet.

**Success = able to run Phase 1 without any "wait, does this even
work?" surprises.**

---

## Progress log

> **Wrap-up written: [PHASE_0_REPORT.md](PHASE_0_REPORT.md)** — deliverable
> status, both findings, the frozen Phase 1 scope, and the green-light
> conditions. Read that first; the log below is the detail behind it.

**2026-08-08 — CPU-side infrastructure landed; Phase 1 design revised.**

Done (all runnable on a laptop, no GPU or dataset access required):

- **Deliverable 3 — phase-anticipation evaluator.** `build_ground_truth()`
  and `paired_bootstrap_ci()` implemented in
  `paper2_infra/evaluation/evaluate_phase_anticipation.py`; no
  `NotImplementedError` remains. 21 tests in
  `tests/test_phase_anticipation.py` cover a synthetic 10-minute video
  with hand-computed transition times and horizon lookups, the
  frame-index-offset case that real MB140 videos exhibit, strict-prefix
  filtering, and every metric against a known answer. The suite also
  smoke-tests the real committed MB140 labels.
- **Week 4 fold-stability prototype (pulled forward).**
  `paper2_infra/evaluation/fold_stability.py` reproduces Paper 1's
  Appendix C.1 numbers exactly (per-fold Δ −0.85 / −0.23 / +0.23 / +0.13
  / −0.22, five-fold mean −0.19) and those literals are asserted in
  `tests/test_fold_stability.py`, so the published numbers cannot drift
  silently. It adds a variance decomposition and a fold-vs-seed budget
  analysis.
- **Deliverable 5 — R3 HMM and R1d duration-aware representations.**
  `paper2_infra/workflow_representations/hmm.py`: Baum-Welch with scaled
  forward-backward, best-of-N restarts, BIC + held-out state-count
  selection, and workflow-entropy measurement. 28 tests, including a
  mutation test proving the filtered posterior is prefix-only.
  `duration_aware_kmeans.py` adds the R1d diagnostic and the across-seed
  stability measurement. R2 (learned embedding) still needs a GPU.
- **Deliverable 2 (partial) — extraction interface repaired.** The anchor
  ViT loader now runs end-to-end and returns the contracted
  `(B, 8, 768)`; loaders for VideoMAE, TimeSformer and V-JEPA 2 are
  written but need the GPU box. 18 tests in
  `tests/test_backbone_extract.py`.

**Two findings came out of this that change the science, not just the
plumbing:**

- [PHASE_0_FINDING_FOLD_VARIANCE.md](PHASE_0_FINDING_FOLD_VARIANCE.md) —
  MB140 is fold-variance-dominated: 98% of the paired effect's variance
  is between-fold, so the planned "fold-0 × 2 seeds" scout design could
  not have decided its own D1.1 gate.
- [PHASE_0_FINDING_REPRESENTATION.md](PHASE_0_FINDING_REPRESENTATION.md) —
  the k-means workflow cluster id is unstable to the random seed alone,
  and is stable on Cholec80 only because that dataset has just 6 distinct
  phase orders. Categorical workflow conditioning is well-defined exactly
  where it is vacuous and ill-defined exactly where it might help.

`NEXT_PAPER_PLAN.md` §Phase 1 is updated accordingly: 5 folds × 1 seed, a
sign-consistency clause on the gate, and a third conditioning arm
carrying the continuous HMM posterior.

Still blocked on access or hardware:

- Backbone smoke tests for the three written video loaders (needs GH200).
- Gated-weight rows and remaining surgical-FM rows (needs HF token /
  author contact).
- AutoLaparo (needs the access request submitted).
- R2 learned continuous embedding (needs a GPU).
- Reproducing Paper 1's ViT RSD numbers (needs the MB140 frames).

---

## Prerequisites

- Lambda filesystem deletion complete (or a fresh instance ready).
  Phase 0 needs one CPU instance for feasibility audits + one H100/GH200
  for smoke tests. Cost: <$50 total.
- HuggingFace read token (not the write token that got leaked earlier).
  A read-only token is sufficient for downloading gated model weights.
- AutoLaparo access request submitted (Week 1 deliverable).

---

## Deliverables (all should exist and be committed by end of Phase 0)

1. **`docs/paper2_planning/phase_0/backbone_feasibility_matrix.md`** —
   populated with real `pass_stage_0` status per row (not "pending"),
   throughput + cache-size measured on GH200.
2. **`paper2_infra/backbone_features/extract.py`** — smoke-tests all
   passing backbones end-to-end; no NotImplementedError left.
3. **`paper2_infra/evaluation/evaluate_phase_anticipation.py`** —
   ground-truth extraction implemented, metric functions verified
   against a synthetic test video with known answers.
4. **AutoLaparo dataset locally accessible**, preprocessed to 1 fps with
   labels JSON in the existing schema.
5. **Alternative workflow-representation prototypes** (learned
   embedding + HMM) implemented and validated on MB140 fold-0 against
   the current k-means reference.
6. **Paper 1 ViT-B/16 RSD numbers reproduced** on a fresh checkout to
   confirm the pipeline works without Lambda.
7. **Phase 1 scout matrix scope frozen** (which backbones × which
   datasets × which conditions × which seeds).

---

## Week-by-week plan

### Week 1 — Access + audits (no code changes yet)

**Access requests (submit Day 1):**

- [ ] Submit AutoLaparo download request via https://autolaparo.github.io/
      → save the confirmation email; access typically arrives in 1–7 days.
- [ ] Register a fresh HuggingFace read token; save in password
      manager.
- [ ] For gated models: accept licenses on the HF UI for each of
      Cosmos-Predict2, V-JEPA 2, V-JEPA 2.1. Record acceptance date in
      the feasibility matrix.

**Weight-availability audits (finish by Day 5):**

For each backbone in `backbone_feasibility_matrix.md` with
`stage_0_status = pending`, do:

- [ ] Confirm HF model card exists and lists a license.
- [ ] Download the model card + config only (not weights yet), inspect
      feature shape and input resolution.
- [ ] Note whether the model requires a special SDK (e.g., Cosmos needs
      `diffusers` + `cosmos-sdk`).
- [ ] Update `backbone_feasibility_matrix.md` with the license, gating
      status, and any special install requirements.

Priority order for the audit:
1. **V-JEPA 2** and **V-JEPA 2.1** (strong latent world models; likely
   pass cleanly).
2. **VideoMAE-Large** and **TimeSformer** (well-established, minimal
   risk).
3. **Cosmos-Predict2 2B** (gated but well-documented).
4. **SurgVISTA** and **EndoMamba** (surgical-native but license less
   documented).
5. **SurgMotion** (may require reaching out to CAIR HKISI directly).
6. **ZEN** (may require reaching out to Park et al. via arXiv author
   email).

**Kill-switch:** if by end of Week 1 fewer than 4 backbones show
`pass_stage_0 = pass`, escalate to the minimum-viable Paper 2A scope
(ViT + one FM) in the brief. Consider whether to still pursue Paper 2A
or pivot to Paper 2B (distillation-only, no FM comparison).

### Week 2 — Infrastructure implementation

**Feature extraction (Day 1–4):**

- [ ] Implement `_load_vit_b16_in21k()` end-to-end (this is the
      anchor; must work first).
- [ ] Reproduce Paper 1's ViT-B/16 no-token RSD number on a single
      fold-0 seed. Use `bash reproducibility/scripts/verify_mb140_strict.sh
      --condition no_token` if MB140 is accessible; otherwise skip and
      note in the Phase 0 report.
- [ ] Implement 2–3 more backbone loaders (start with V-JEPA 2 and
      VideoMAE, then Cosmos if the SDK is straightforward).
- [ ] Run `python -m paper2_infra.backbone_features.extract smoke <backbone>`
      for each; record clips-per-second and load time in the feasibility
      matrix.
- [ ] Implement the real extraction loop in
      `extract_one_dataset()` for backbones that passed smoke.

**Phase-anticipation evaluator (Day 3–5):**

- [ ] Implement `build_ground_truth()` in
      `evaluate_phase_anticipation.py`. Confirm it handles all three
      dataset label-JSON formats (MB140, Cholec80, AutoLaparo).
- [ ] Add unit tests: a synthetic 10-min video with known phase
      transitions should produce known GT records.
- [ ] Implement `paired_bootstrap_ci` by borrowing from
      `brsd_lib/stats.py`.
- [ ] Run the evaluator on a fake predictions JSON to confirm the
      output-report JSON schema is stable.

### Week 3 — Workflow-representation prototypes + AutoLaparo integration

**Workflow-representation alternatives (Day 1–3):**

- [ ] Implement R2 (learned continuous embedding): a small transformer
      that pools per-video visual features into a 128-dim vector. Train
      on MB140 training-set videos only. Save embeddings per video.
- [ ] Implement R3 (HMM state posterior): use ground-truth phase labels
      + a first-order HMM. Compute per-video state-posterior sequence.
      Save per video.
- [ ] Verify all three representations (k-means / learned / HMM)
      produce vectors the temporal head can consume.

**AutoLaparo integration (Day 3–5):**

Assumes access has arrived by now.

- [ ] Download AutoLaparo (21 videos, ~10–30 GB depending on encoding).
- [ ] Preprocess to 1 fps + 224×224 frames using the existing
      `lambda_setup/scripts/prepare_labels.py` pipeline.
- [ ] Verify phase labels map cleanly to a 7-class array per video.
- [ ] Compute workflow-cluster entropy H(z) for AutoLaparo (K=4, K=6,
      K=8 sweep).
- [ ] Add AutoLaparo to the feasibility matrix with measured video
      duration distribution + entropy value.

### Week 4 — Freeze + write-up

**Fold-stability analysis prototype (Day 1–2):**

- [ ] Write `paper2_infra/evaluation/fold_stability.py` — reads
      Paper 1's `phase_e_aggregate_metrics.json` and produces:
        - per-fold effect size + Wilcoxon
        - variance decomposition (seed vs fold vs backbone once we have
          multiple backbones)
- [ ] Verify it reproduces Paper 1's Appendix C numbers (Δ = −0.19 min
      average, per-fold: -0.85, -0.23, +0.23, +0.13, -0.22).

**Freeze the Phase 1 scope (Day 3):**

- [ ] Convene a self-review: given the actual audit results, what's the
      Phase 1 scout-matrix scope?
- [ ] Update `NEXT_PAPER_BRIEF.md` §Experimental Design if the
      matrix shape changed.
- [ ] Update `PAPER_2A_REVIEWER_HARDENING.md` if AutoLaparo integration
      failed and we need a substitute dataset.

**Phase 0 wrap-up report (Day 4–5):**

- [ ] Write `docs/paper2_planning/phase_0/PHASE_0_REPORT.md` — for each
      backbone: pass/fail + measured throughput + cache-size estimate.
      For each dataset: video count + duration distribution + workflow
      entropy H(z).
- [ ] Attach the Phase 1 scout-matrix spec: exact set of runs to
      execute in Phase 1, with GPU-hour estimate.
- [ ] Green-light or red-light Phase 1.

---

## Compute budget breakdown

| Item | Estimate |
|---|---|
| Access requests + audits (Week 1) | $0 (browser + laptop only) |
| Backbone smoke tests × 10 backbones × 5 min each | ~1 GPU-h ≈ $3 |
| Feature extraction dry-runs (Week 2) | ~2 GPU-h ≈ $6 |
| AutoLaparo preprocessing (Week 3) | ~2 CPU-h ≈ $0.20 |
| Alt-representation training (learned embedding) | ~10 GPU-h ≈ $30 |
| Phase 1 scout matrix (post-Phase-0, per brief) | ~40–80 GPU-h ≈ $120–240 |
| **Phase 0 total** | **~$40–$300** |
| Phase 0 alone (excluding scout matrix) | **~$40** |

Well under the $250 budget in the brief. The scout matrix that
follows Phase 0 is where the money starts to be spent.

---

## Kill-switch conditions

Stop Phase 0 and escalate to the user immediately if:

1. **<4 backbones pass the Phase 0 audit.** This means the "systematic
   FM transfer matrix" pitch of Paper 2A collapses to "ViT + one FM
   comparison." Consider whether to still pursue Paper 2A or pivot to
   Paper 2B (distillation-only, no FM comparison).
2. **AutoLaparo access denied or unusable.** The two-dataset confound
   Paper 1 got dinged on stays unfixed. Consider HeiChole as a
   substitute or a different corroborating dataset entirely.
3. **Learned-embedding representation fails to train stably.** The
   workflow-rep-sensitivity claim weakens; would need to fall back to
   only K-sweep + HMM.
4. **Paper 1 ViT-B/16 numbers don't reproduce.** Something is wrong
   with the current checkpoint/label/harness setup. Fix before doing
   anything else.

---

## After Phase 0 → Phase 1

Once Phase 0 wrap-up report is green-lit, kick off the scout matrix as
specified in `NEXT_PAPER_PLAN.md` §Phase 1:

- 4–5 accessible backbones × 3 settings (MB140 fold-0 + cross-center +
  Cholec80 + AutoLaparo if it passed) × 2 conditions (no-token,
  decoupled-oracle) × 2 seeds × RSD + one anticipation task
- ~48–80 trained-head runs, ~250–500 GPU-h, ~$750–$1,500.

The decision gate after Phase 1: does at least one non-ViT backbone
improve causal RSD by ≥ 0.3 min or improve transition anticipation MAE
by ≥ 0.5 min? If yes → Phase 2 confirmatory experiments. If no →
pivot to the Cosmos-meh diagnostic narrative pre-registered in the
brief.

---

## Non-goals for Phase 0

Do **not** in Phase 0:

- Train any model (except the learned-embedding prototype on MB140 to
  test the representation).
- Run any full 5-fold experiment.
- Do any adapter / LoRA fine-tuning (Stage 3 territory).
- Write the Paper 2A LaTeX skeleton (Phase 2 territory).
- Start Paper 2B distillation experiments (Phase 3 territory).

Phase 0 is infrastructure + feasibility only. Every hour spent on
downstream work now is an hour wasted if a backbone or dataset kills
its own row later.

# Phase 0 Report — Paper 2A

> **Note (2026-09-17):** references below to `NEXT_PAPER_PLAN.md`,
> `NEXT_PAPER_BRIEF.md`, or `PAPER_2A_REVIEWER_HARDENING.md` now resolve to
> [`docs/STRATEGY.md`](../../STRATEGY.md), which merged them. Originals are at
> git commit `58c99bc`.

*Status as of 2026-08-08. Covers the CPU-side Phase 0 programme.
Hardware- and access-dependent items remain open and are listed
explicitly in §4.*

**Recommendation: proceed to Phase 1, with the revised sampling design in
§5.** The two blocking questions Phase 0 existed to answer — "does the
infrastructure work?" and "is the planned Phase 1 capable of deciding its
own gate?" — are answered yes and *no, until changed*. The change is
specified below and costs roughly 2.5× the MB140 runs the original plan
budgeted, which is the difference between a decidable experiment and an
undecidable one.

---

## 1. Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Backbone feasibility matrix with real `pass_stage_0` per row | **Partial** — anchor audited end-to-end and measured; 3 loaders written but not smoke-tested; 6 rows still need weight/license resolution |
| 2 | `backbone_features/extract.py` smoke-tests all passing backbones | **Partial** — interface contract fixed and anchor passes; video-model loaders implemented, awaiting GPU |
| 3 | `evaluate_phase_anticipation.py` implemented and verified | **Done** |
| 4 | AutoLaparo accessible and preprocessed | **Not started** — blocked on the access request |
| 5 | Alternative workflow-representation prototypes | **Done for R3 (HMM) and R1d (duration-aware)**; R2 (learned embedding) needs a GPU |
| 6 | Paper 1 ViT-B/16 RSD numbers reproduced | **Not attempted** — needs MB140 frames, which are not on this machine |
| 7 | Phase 1 scout-matrix scope frozen | **Done** — §5 |

Test coverage added this phase: **131 tests** across five suites, all
passing (`pytest tests/ --ignore=tests/test_model.py`; `test_model.py`
needs CUDA-side torch and is unrelated).

## 2. What Phase 0 caught before it became expensive

Three defects that would each have corrupted Phase 1 results or wasted
its compute:

1. **The extraction interface was broken in a way that would have failed
   every backbone identically.** `smoke_test` fed a 5-D
   `(B, T, 3, H, W)` tensor to an image model expecting 4-D. Every row
   would have "failed its audit" for a reason having nothing to do with
   the backbone. Fixed by wrapping image and video models to one
   contract, and by making `smoke_test` verify the returned shape and
   feature dim rather than reporting `ok` for anything that did not raise.
2. **The anchor's weights were not what its name said.** `timm.create_model
   ("vit_base_patch16_224", pretrained=True)` resolves to the *default*
   tag — `augreg2_in21k_ft_in1k`, ImageNet-21k pretrained **and**
   ImageNet-1k finetuned — not the plain in21k weights that
   `vit_b16_in21k` implies, and the default can change between timm
   releases. Paper 1 used the same untagged call, so its "ImageNet-21k
   init" description is imprecise. All rows now pin an explicit tag and a
   test enforces it for any row marked `pass`.
3. **The planned Phase 1 sampling could not decide its own decision
   gate.** See §3.

## 3. Findings

Two results came out of Phase 0 that change the science, not just the
plumbing. Both are written up in full with reproduction commands:

### [Fold-variance dominance](PHASE_0_FINDING_FOLD_VARIANCE.md)

On Paper 1's own five-fold data, **98% of the paired conditioning
effect's variance is between-fold and 2% is between-seed**. Consequences:

- A fold-0 design has SE ≈ 0.42 min on the effect; 5 folds × 1 seed has
  SE ≈ 0.19 min for a comparable run count. **Seeds buy almost nothing;
  folds buy everything** — tripling seeds at fixed folds reduces SE by 1%.
- The planned D1.1 gate (0.3 min on MB140 fold-0 × 2 seeds) sat inside
  one standard error, so Phase 1 would have selected finalists largely by
  noise and Phase 2 would have spent 250–400 runs confirming that
  selection.
- Between-fold spread is 7.7× the five-fold effect, and the
  condition×fold interaction is 4.0× the condition main effect.
- This also retroactively explains Paper 1: fold 0's −0.85 min sits
  1.6 SE from the −0.19 min five-fold mean. No fold-specific mechanism
  needs to be invoked.

### [Workflow-representation non-identifiability](PHASE_0_FINDING_REPRESENTATION.md)

The aggregate *amount* of workflow variability is robust across
representation families — both k-means and an HMM find MB140 far more
variable than Cholec80 (normalized entropy ≈0.95 vs ≈0.63), so **Paper 1's
premise survives**. The per-video *grouping* does not survive anything:

- **Seed instability.** Rerunning the identical k-means pipeline with only
  a different `random_state` gives pairwise ARI 0.49–0.76 (mean 0.63) on
  MB140, while the objective moves 0.69%. The feature space admits many
  equally-good 6-way splits.
- **The K-sweep tested nothing.** K=4/6/8 agreement (0.42–0.70) is
  indistinguishable from that seed noise floor. Reviewer iSh9's criticism
  was better founded than the rebuttal conceded.
- **Cross-family agreement collapses** to ARI 0.03–0.08, far below the
  0.63 self-agreement ceiling — a real effect, not seed noise.
- **The order-vs-timing explanation was tested and ruled out.** Adding
  duration features to k-means moves it away from order-only k-means
  (ARI 0.787→0.310) but never toward the timing-based HMM (flat 0.04–0.10).
- **The sharpest result:** Cholec80's clustering is *perfectly* stable
  (ARI 1.000) because it has only **6 distinct phase orders among 72
  videos** — with K=6 the partition is forced. MB140 has **104 distinct
  orders among 140 videos** and is unstable. Categorical workflow
  clustering is therefore well-defined exactly where it is vacuous
  (standardized procedures) and ill-defined exactly where it might help
  (heterogeneous ones). The conditioning token meant structurally
  different things on the two datasets, which is a mechanism for the
  cross-dataset confound beyond the procedure/center/taxonomy differences
  already conceded.

**Design consequence:** Paper 2A should condition on a **continuous**
workflow vector (HMM posterior, learned embedding) rather than a hard
cluster id, keeping k-means only as the legacy comparator.

## 4. Open items, and what each is blocked on

| Item | Blocked on | Who |
|---|---|---|
| AutoLaparo access | Access-request form submission | **User** — longest lead time of anything here; submit first |
| HF read token + gated licenses (Cosmos, V-JEPA 2/2.1) | Account action | **User** |
| Smoke tests for VideoMAE / TimeSformer / V-JEPA 2 | GPU box | Loaders are written; one command per row once an instance is up |
| SurgMotion / SurgVISTA / ZEN weights + licenses | Web search, possibly author contact | Either |
| Reproduce Paper 1 ViT RSD numbers | MB140 frames, not on this machine | Needs the GPU box |
| R2 learned continuous embedding | GPU | ~1 day + ~10 GPU-h |
| Matched-settings check on Paper 1's stored clusterings | Nothing — CPU work | Next session |

## 5. Frozen Phase 1 scope

Revised from `NEXT_PAPER_PLAN.md` §Phase 1 in light of §3.

**Sampling.** MB140 is evaluated at **5 folds × 1 seed**, not fold-0 × 2
seeds. Cross-center and Cholec80 keep single splits for now, with the
caveat in §6.

**Conditioning arms.** Three, not two: `no-token`, `decoupled-R1`
(legacy k-means cluster id), and `decoupled-R3` (continuous HMM
posterior). Carrying both representations measures the §3
family-sensitivity result on the downstream task rather than only on the
representation itself — which is the whole point of having found it.

**Matrix.** 5 backbones × {MB140 5-fold, MB140 cross-center, Cholec80}
× 3 conditions × 1 seed = 5 × (5 + 1 + 1) × 3 = **105 trained-head
runs**.

That is above the original plan's ~60–80, from two changes: folds
replace seeds on MB140 (5× rather than 2× per cell, and the reason is
§3), and the R3 arm is added. If the budget binds, **drop a backbone
before dropping either folds or R3** — four backbones at 84 runs still
answers the question, whereas fold-0 sampling at any backbone count does
not.

**Revised gate D1.1.** A non-ViT backbone passes if it beats the ViT
baseline on causal RSD on MB140 by **either** ≥ 0.5 min mean across
folds, **or** ≥ 0.3 min mean with the sign consistent on ≥ 4 of 5 folds.

**Mandatory reporting per row.** Mean Δ across folds, per-fold signs,
interaction/condition ratio, and the representation's own across-seed
stability. A row whose interaction/condition ratio exceeds 1 is reported
as fold-dependent, not as a gain.

**Compute.** Feature extraction dominates and cannot be estimated
honestly until GH200 throughput is measured — the anchor runs at 3.2
clips/s on a laptop CPU, which says nothing useful about the target
hardware. Cache size *is* known: 24.6 kB/clip for the anchor, so ~2.8 GB
for MB140 at clip-stride 5 and ~14 GB at stride 1, per backbone.

## 6. Risks carried into Phase 1

1. **Cholec80 and cross-center are still single-split.** The fold-variance
   finding is measured on MB140; there is no reason to expect Cholec80 to
   be different in kind. Any Cholec80 conclusion from Phase 1 will carry
   fold-0-sized error bars and should be reported as suggestive.
2. **Task B's long horizons are barely measurable on Cholec80.** At a
   30-minute horizon, ground truth exists for 69% of MB140 test clips but
   only 27% of Cholec80's, because the procedures are shorter. Comparing
   Task B across datasets at long horizons compares different
   subpopulations — only the longest Cholec80 cases contribute. Either
   cap the cross-dataset comparison at 10 minutes (66% coverage) or
   report coverage alongside every horizon.
3. **The V-JEPA loader's `n_out_frames=8` is an unverified assumption**
   taken from the model card. If the tubelet is not 2, the smoke test's
   divisibility check will fail loudly rather than mis-pool — but it will
   fail, and the row will need a fix.
4. **AutoLaparo may not arrive in time.** If it does not, the two-dataset
   confound Paper 1 was criticized for stays unfixed, and Paper 2A's
   variability-scaling claim stays correspondingly narrow. The §3
   representation finding partly compensates by giving a
   dataset-independent result, which is why it is worth foregrounding.

## 7. Green light

**Proceed to Phase 1** once (a) an instance is up and the three written
loaders pass their smoke tests, and (b) the AutoLaparo request has been
submitted, whatever its outcome. Neither blocks writing; both block
spending.

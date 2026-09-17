# BariatricRSD — Session Log (Paper 2A / 2B)

> Running log for the second-paper programme. Paper 1's log is closed and
> lives at [`docs/paper1_neurips2026/SESSION_LOG.md`](../paper1_neurips2026/SESSION_LOG.md).
> Update after every session.

---

## Programme

| | Paper 2A | Paper 2B |
|---|---|---|
| Working title | *Do World Models Help Surgical Workflow Forecasting? A Causal Benchmark* | *Closing the Oracle Gap via Privileged-Information Distillation* |
| Primary venue | MICCAI 2027 (Feb/Mar 2027 submission) | NeurIPS 2027 (May 2027) |
| Current phase | **Phase 0 — CPU side complete, hardware side blocked** | Not started (Phase 3) |

Plan and brief consolidated into [`STRATEGY.md`](../STRATEGY.md) on 2026-09-17.
Phase 0 wrap-up: [`phase_0/PHASE_0_REPORT.md`](phase_0/PHASE_0_REPORT.md)

---

## 📍 Live state (2026-08-10)

**Nothing training. No GPU instance running. No spend.**

Phase 0's CPU-side programme is complete (131 tests passing). Phase 1 is
**green-lit conditionally** — it cannot start until the datasets are
re-acquired and the three written video-model loaders pass smoke tests on
a GPU.

**Critical path, longest lead time first:**

| # | Blocker | Owner | Lead time |
|---|---|---|---|
| 1 | **Re-acquire MB140 + Cholec80 frames** (Cholec80 needs a fresh CAMMA DUA) | User | days–weeks |
| 2 | AutoLaparo access request | User | 1–7 days |
| 3 | Confirm Paper 1 rebuttal filed | User | now |
| 4 | HF read token + gated licenses (Cosmos, V-JEPA 2) | User | ~30 min |
| 5 | Launch a GPU instance → I run the smoke tests | User, then me | ~1 hr, ~$40 |

Full write-up of these: see the 2026-08-09 entry below.

---

### 2026-08-08 — Phase 0 CPU programme: infrastructure built, two findings, Phase 1 redesigned

First substantive Paper 2A session. Started from a Phase 0 skeleton where
`extract.py` and `evaluate_phase_anticipation.py` were entirely
`NotImplementedError` and every feasibility-matrix row read `pending`.

Worked on a local `.venv` (gitignored) with numpy/scipy/pytest, later
torch/timm/scikit-learn. No GPU, no cloud spend.

#### A. What was built

| Module | Purpose | Tests |
|---|---|---:|
| `paper2_infra/evaluation/evaluate_phase_anticipation.py` | Strict prefix-only Task A/B evaluator — ground truth + paired bootstrap implemented | 21 |
| `paper2_infra/evaluation/fold_stability.py` | Per-fold effects, variance decomposition, fold-vs-seed budget analysis | 27 |
| `paper2_infra/workflow_representations/hmm.py` | R3 latent-state workflow representation (Baum-Welch, scaled forward-backward, restarts, BIC/held-out selection, entropy) | 28 |
| `paper2_infra/workflow_representations/compare.py` | Cross-representation ARI + variability + seed stability | 26 |
| `paper2_infra/workflow_representations/duration_aware_kmeans.py` | R1d duration-aware diagnostic | 11 |
| `paper2_infra/backbone_features/extract.py` | Interface contract repaired; anchor + 3 video loaders | 18 |

**131 tests passing** (`pytest tests/ --ignore=tests/test_model.py`;
that file needs CUDA-side torch and is unrelated).

#### B. Three defects caught before they cost compute

1. **The extraction interface was broken identically for every backbone.**
   `smoke_test` fed a 5-D `(B,T,3,H,W)` tensor to an image model
   expecting 4-D — the anchor died with `ValueError: too many values to
   unpack (expected 4)` on its first real run. Every row would have
   "failed its audit" for harness reasons. Fixed with
   `_clipwise_image_encoder` / `_video_encoder` wrappers to one
   `(B,T,3,H,W) → (B,T,D)` contract, and `smoke_test` now verifies the
   returned shape and feature dim instead of reporting `ok` for anything
   that didn't raise.
2. **The anchor's weights weren't what its name said.**
   `timm.create_model("vit_base_patch16_224", pretrained=True)` resolves
   to the *default* tag `augreg2_in21k_ft_in1k` — in21k pretrained **and
   in1k finetuned** — not the plain in21k weights `vit_b16_in21k`
   implies, and the default can move between timm releases. Paper 1 used
   the same untagged call, so its "ImageNet-21k init" wording is
   imprecise. All rows now pin an explicit tag; a test enforces it for
   any row marked `pass`.
3. **My own HMM video descriptor collapsed.** Defaulting the "causal"
   whole-video descriptor to the *last* frame's filtered posterior gave
   Cholec80 H(z) = exactly 0 — every video ends in the same phase, so all
   72 got an identical descriptor. Changed to average the per-frame
   prefix-only posteriors. Caught by the entropy coming out at 0.000, not
   by a test; a regression test now covers it.

Anchor now measured: `(2, 8, 768)` output, 24,576 B/clip cache footprint
(→ ~2.8 GB for MB140 at clip-stride 5, ~14 GB at stride 1, per backbone),
3.2 clips/s on laptop CPU (says nothing about GH200).

#### C. Finding 1 — MB140 is fold-variance-dominated

Full write-up: [`phase_0/PHASE_0_FINDING_FOLD_VARIANCE.md`](phase_0/PHASE_0_FINDING_FOLD_VARIANCE.md)

Ran `fold_stability.py` over Paper 1's committed `paper/phase_e_summary.json`
(3 conditions × 5 folds × 3 seeds). Reproduces Appendix C.1 exactly
(−0.85 / −0.23 / +0.23 / +0.13 / −0.22, mean −0.19) — those literals are
now asserted in `tests/test_fold_stability.py`, so the published numbers
can't drift silently.

| Variance source | Share |
|---|---:|
| Between-fold | **96.7%** |
| Condition × fold interaction | 1.8% |
| Seed | 1.1% |
| **Condition (the reported effect)** | **0.4%** |

For the *paired* effect: σ_fold 0.422 min, σ_seed 0.058 min → **98.1% of
the effect's own variance is between-fold**.

| Design | Runs/condition | SE(mean Δ) |
|---|---:|---:|
| 1 fold × 3 seeds | 3 | 0.423 |
| 5 folds × 1 seed | 5 | **0.191** |
| 5 folds × 3 seeds | 15 | 0.189 |
| 10 folds × 1 seed | 10 | **0.135** |

**Seeds buy nothing; folds buy everything.** Tripling seeds at fixed folds
cuts SE by 1%. At equal cost, 10 folds × 1 seed beats 5 folds × 2 seeds.

Consequences: the planned Phase 1 (fold-0 × 2 seeds, gate at 0.3 min) had
SE ≈ 0.42 — **it could not decide its own gate**, so finalists would have
been picked by noise and Phase 2 would have burned 250–400 runs
confirming that. Also: fold 0's −0.85 sits 1.6 SE from the −0.19
five-fold mean, so Paper 1's reversals need no mechanism.

#### D. Finding 2 — the workflow cluster id is not an identified construct

Full write-up: [`phase_0/PHASE_0_FINDING_REPRESENTATION.md`](phase_0/PHASE_0_FINDING_REPRESENTATION.md)

Built R3 (HMM) as a second representation family and compared against
Paper 1's k-means.

**Good news first:** aggregate variability is family-robust. Both find
MB140 far more variable than Cholec80 (normalized entropy ≈0.95 vs
≈0.63); held-out HMM likelihood agrees (0.485 vs 0.146 nats/frame).
**Paper 1's premise survives.**

Its *signal* does not:

- **Seed instability.** Rerunning the identical k-means with only a
  different `random_state`: pairwise ARI 0.49–0.76 (mean 0.63) on MB140,
  while inertia moves 0.69%. The feature space admits many equally-good
  6-way splits; `n_init=20` already picks best-of-20 within each seed.
- **The K-sweep tested nothing.** K=4/6/8 agreement (0.42–0.70) is
  indistinguishable from that seed noise floor.
- **Cross-family agreement collapses** to ARI 0.03–0.08, far below the
  0.63 self-agreement ceiling.
- **Order-vs-timing explanation tested and ruled out.** R1d (duration-aware
  k-means) moves *away* from order-only k-means as duration weight rises
  (0.787 → 0.310) but never toward the HMM (flat 0.04–0.10).
- **The sharpest result.** Cholec80's clustering is *perfectly* stable
  (ARI 1.000, inertia spread 0.00%) because it has only **6 distinct
  phase orders among 72 videos** — at K=6 the partition is forced. MB140
  has **104 among 140** and is unstable.

> Categorical workflow clustering is well-defined exactly where it is
> vacuous (standardized procedures) and ill-defined exactly where it might
> help (heterogeneous ones). The conditioning token therefore meant
> structurally different things on the two datasets Paper 1 compares — a
> mechanism for the cross-dataset confound beyond the procedure/center/
> taxonomy differences already conceded.

#### E. Phase 1 redesigned

Updated `NEXT_PAPER_PLAN.md` (now [`STRATEGY.md`](../STRATEGY.md)) §Phase 1:

- MB140 sampling: fold-0 × 2 seeds → **5 folds × 1 seed**
- Conditions: 2 → **3** (`no-token`, `decoupled-R1`, `decoupled-R3`)
- Runs: ~60–80 → **105**. If budget binds, **drop a backbone, not folds
  or the R3 arm.**
- Gate D1.1: ≥0.5 min mean across folds, **or** ≥0.3 min with sign
  consistent on ≥4/5 folds
- Every row must report its interaction/condition ratio and the
  representation's own seed stability

#### F. Evaluator validated on real data

`build_ground_truth` runs on both committed label sets. MB140 test split:
7,650 clips over 40 videos at 30 s stride, 96.8% Task-A-scorable. Full CLI
path checked end-to-end against a synthetic predictions file — a random
baseline scores macro-F1 ≈ 0.05 ≈ 1/14, exactly chance for 14 phases.

**Scoping issue found:** at a 30-min horizon, ground truth exists for 69%
of MB140 test clips but only **27%** of Cholec80's (shorter procedures).
Cross-dataset Task B comparison at long horizons compares different
subpopulations. Either cap it at 10 min (66% coverage) or report coverage
per horizon.

---

### 2026-08-09 — Dataset loss discovered; user action list produced

While assembling the blocker list, checked whether the raw frames were
still reachable. **They are not.**

- Local `*.jpg` count outside `paper/` and `2019/`: **18** (sample frames
  under `lambda_mirror/extern/MultiBypass140/`).
- `lambda_mirror/` (45 GB) is outputs / labels / logs only.
- The frames lived on the Lambda filesystem stopped in June 2026.
  [STOP_LAMBDA_NOW.md](../runbooks/STOP_LAMBDA_NOW.md) listed them under
  "acceptable losses" — correct for Paper 1, wrong for Paper 2A, because
  every backbone in the scout matrix must re-read pixels.

**This is now the critical path**, ahead of AutoLaparo: MB140 needs
re-downloading and Cholec80 needs a fresh CAMMA data-use agreement, which
has historically taken days to weeks. Recorded in the Paper 1 log header
and in [`phase_0/PHASE_0_REPORT.md`](phase_0/PHASE_0_REPORT.md) §4.

Also flagged: nothing in-repo confirms the Paper 1 rebuttal was actually
filed. If the window is open, the fold-variance result gives a strictly
better answer than the current "the present experiments do not establish
why folds 2 and 3 reverse."

Storage lesson for next time: decide where the datasets live *before*
spinning up, and don't let frames exist only on ephemeral cloud storage.

---

### 2026-08-10 — Log/README refresh; manuscript std-convention inconsistency found

Updated the Paper 1 log header (dead Lambda IP, April deadlines, stale
"live state"), opened this log, and refreshed the root `README.md` with
current status, the real `paper2_infra/` tree, and the actual five-fold
results in place of the old "Our Target" table.

While checking the README's numbers against
`paper/phase_e_summary.json`, found a **std-convention inconsistency in
the submitted manuscript**. Fold-0, 3 seeds:

| Condition | Seeds | ddof=1 | ddof=0 | JSON artifact | Manuscript |
|---|---|---:|---:|---:|---|
| no-token | 13.17, 13.10, 12.83 | **0.180** | 0.147 | 0.18 | 0.18 (body) / **0.13 (App. C)** |
| oracle | 12.18, 12.23, 12.36 | **0.093** | 0.076 | 0.093 | 0.09 |
| decoupled | 12.32, 12.19, 12.04 | **0.140** | 0.114 | 0.14 | **0.11** |

Two problems:

1. **Mixed conventions inside one comparison.** The headline
   "13.03 ± 0.18 → 12.18 ± 0.11" pairs a sample std with a population
   std. This appears in the abstract, §6.1, §6.5 and Appendix C.
2. **Appendix C's `13.03 ± 0.13` matches neither convention** (0.180 /
   0.147). It is simply wrong, and it contradicts the paper's own body
   text, which says 0.18 for the same number.

No conclusion changes — the Δ of −0.85 min and every significance test
are unaffected, since these are dispersion annotations, not the effect.
But it is exactly the class of internal inconsistency a careful reviewer
of an *evaluation* paper is entitled to notice.

**Camera-ready action (if #706 is accepted):** regenerate every ± in the
manuscript from `phase_e_summary.json` with one stated convention
(recommend ddof=1, which is what the artifact and `aggregate_phase_e.py`
already use) and state the convention in the caption. `paper/phase_e_summary.md`
is already correct and can serve as the source of truth.

---

### Next session — unblocked work queue

No user input needed for any of these:

1. Check whether Paper 1's stored MB140 and Cholec80 clusterings were
   built under matched K and `min_df` (stored Cholec80 has 4 occupied
   clusters, MB140 has 6). If not matched, the cross-dataset conditioning
   comparison needs re-running before Paper 2A cites it.
2. Sweep the manuscript for every ± and regenerate under one std
   convention (see the 2026-08-10 entry), so the fix is ready if #706 is
   accepted rather than being written under camera-ready time pressure.
3. Write the R2 learned-embedding code so it's ready to train the moment
   a GPU exists.
4. Fold both findings into `NEXT_PAPER_BRIEF.md` (now [`STRATEGY.md`](../STRATEGY.md)) as
   Paper 2A evaluation contributions.
5. Commit the Phase 0 work (nothing is committed yet).

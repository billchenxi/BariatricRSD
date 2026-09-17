# Phase 0 Finding — MB140 is fold-variance-dominated, and the planned Phase 1 design cannot detect its own decision gate

> **Note (2026-09-17):** references below to `NEXT_PAPER_PLAN.md`,
> `NEXT_PAPER_BRIEF.md`, or `PAPER_2A_REVIEWER_HARDENING.md` now resolve to
> [`docs/STRATEGY.md`](../../../plans/STRATEGY.md), which merged them. Originals are at
> git commit `58c99bc`.

*Status: analysis complete, reproducible from committed artifacts.
Produced by `paper2_infra/evaluation/fold_stability.py` on
`paper/phase_e_summary.json` (Paper 1's five-fold × three-seed strict
protocol run). Verified against Paper 1 Appendix C.1 in
`tests/test_fold_stability.py`.*

Reproduce with:

```bash
python -m paper2_infra.evaluation.fold_stability \
    --summary-json paper/phase_e_summary.json \
    --baseline no_token --treatment decoupled \
    --conditions no_token oracle decoupled \
    --report-out paper2_infra/evaluation/reports/fold_stability_paper1_decoupled.json
```

---

## 1. What the analysis says

Decomposing the 45 strict-protocol runs (3 conditions × 5 folds × 3
seeds) attributes MAE variance as follows:

| Source | Share of total variance |
|---|---:|
| Between-fold | **96.7%** |
| Condition × fold interaction | 1.8% |
| Seed (residual) | 1.1% |
| **Condition (the effect we report)** | **0.4%** |

Two ratios follow, and they are the numbers to carry into Paper 2A:

- **fold sd / |effect| = 7.7×.** The between-fold spread of MB140
  (1.43 min) is nearly eight times the five-fold conditioning effect
  (0.19 min).
- **interaction / condition = 4.0×.** The effect of workflow
  conditioning varies across folds about four times more than it exists
  on average. It is more accurate to say conditioning *behaves
  differently on different folds* than to say it *helps*.

Neither paired test reaches significance: p = 0.15 over the 15 matched
(fold, seed) runs, p = 0.63 over the 5 fold means.

## 2. Where the effect's uncertainty actually lives

The table above concerns absolute MAE, and between-fold differences in
case difficulty are cancelled by the paired contrast we always use. The
planning question is narrower: for the *paired difference*, does another
fold or another seed reduce uncertainty faster?

Modelling `delta[f,s] = mu + a_f + e_fs`:

| Component | Estimate |
|---|---:|
| σ_fold (between-fold spread of the effect) | **0.422 min** |
| σ_seed (within-fold seed noise on the effect) | **0.058 min** |
| Fold share of the effect's variance | **98.1%** |

Pricing candidate designs by the standard error each buys on the mean
effect:

| Design | Runs per condition | SE(mean Δ) |
|---|---:|---:|
| 1 fold × 1 seed | 1 | 0.426 |
| 1 fold × 3 seeds | 3 | 0.423 |
| **5 folds × 1 seed** | **5** | **0.191** |
| 5 folds × 2 seeds | 10 | 0.190 |
| 5 folds × 3 seeds | 15 | 0.189 |
| **10 folds × 1 seed** | **10** | **0.135** |
| 10 folds × 3 seeds | 30 | 0.134 |
| 20 folds × 1 seed | 20 | 0.095 |

Read the bolded rows against each other. **Seeds are nearly worthless
and folds are everything.** Going from 1 seed to 3 seeds at 5 folds
triples the compute and reduces SE by 1%. Going from 5 folds to 10 folds
at 1 seed doubles the compute and reduces SE by 29%. At an equal budget
of 10 runs, 10 folds × 1 seed (SE 0.135) beats 5 folds × 2 seeds
(SE 0.190).

The same ordering holds on the oracle arm, where seed noise is larger
(σ_fold 0.338, σ_seed 0.175, fold share 79%): 10 folds × 1 seed at 10
runs (SE 0.120) still beats 5 folds × 3 seeds at 15 runs (SE 0.158).

## 3. This retroactively explains Paper 1

A single-fold design has SE ≈ 0.42 min on the effect. Paper 1's
development fold produced −0.85 min against a five-fold mean of
−0.19 min — a deviation of 1.6 SE. That is an unremarkable draw, not an
anomaly requiring a mechanism.

This is worth stating plainly because the rebuttal currently says the
present experiments "do not establish why folds 2 and 3 reverse." We now
have a better answer than "unknown": **the per-fold effects are
consistent with a single small effect plus fold-level noise of the size
MB140 actually exhibits.** No fold-specific mechanism needs to be
invoked. If Paper 1 is accepted, this belongs in the camera-ready as a
one-paragraph addition to Appendix C.1; it strengthens the honest
reading rather than rescuing the headline.

**Note:** with only five folds, σ_fold is itself estimated from five
numbers and is correspondingly uncertain. Everything above is a planning
estimate whose purpose is to separate "needs 6 folds" from "needs 40
folds," not to give an exact power calculation. It should not be quoted
as a precise result.

## 4. What this changes in the Phase 1 plan

`NEXT_PAPER_PLAN.md` §Phase 1 currently specifies:

> 3 settings: MB140 fold-0, MB140 cross-center, Cholec80. 2 conditions.
> 2 seeds. Decision gate D1.1: at least one non-ViT backbone improves
> causal RSD on MB140 by ≥ 0.3 min.

**This design cannot decide its own gate.** MB140 fold-0 with 2 seeds
has SE ≈ 0.42 min on the effect. A 0.3-min threshold sits well inside
one standard error, so a backbone that truly does nothing has a large
chance of clearing the gate and a backbone that truly helps by 0.3 min
has roughly a coin-flip chance of missing it. Phase 1 would be selecting
finalists mostly at random, and Phase 2 would then spend 250–400 runs
confirming a selection made by noise.

**Recommended change — same compute, decidable gate:**

| | Current plan | Proposed |
|---|---|---|
| MB140 sampling | fold 0 only, 2 seeds | **5 folds, 1 seed** |
| Runs per backbone × condition on MB140 | 2 | 5 |
| SE on the effect | 0.42 min | **0.19 min** |
| D1.1 gate at 0.3 min | undecidable | ~1.6 SE, marginal but usable |

The run count rises from 2 to 5 per backbone × condition on MB140, but
the fold-0-only design was never going to produce a usable answer, so
this is the difference between spending a little more and spending
everything on noise. If the budget is fixed, drop a backbone rather than
drop folds.

**Two further consequences:**

1. **Reconsider the 0.3-min gate itself.** Even at 5 folds × 1 seed, a
   0.3-min gate is only ~1.6 SE. Either raise the threshold to ~0.5 min
   (≈2.6 SE, comfortably decidable), or keep 0.3 min and require the
   sign to be consistent across at least 4 of 5 folds — a sign-stability
   criterion costs nothing extra and is exactly the check Paper 1
   failed. Recommend **both**: gate on 0.5 min *or* on 0.3 min with 4/5
   sign consistency.
2. **Report the interaction ratio for every backbone.** If a backbone's
   interaction/condition ratio is above 1, its headline number is
   describing fold-dependence, not a transfer effect. This is a cheap
   diagnostic that turns Paper 1's embarrassment into Paper 2A's
   standard reporting practice.

## 5. Why this is a Paper 2A contribution, not just a planning note

Paper 1's reviewers rejected the causal framing partly because the
effect did not survive cross-validation. The generalizable version of
that criticism is a claim about the benchmark rather than about our
model: **MB140 RSD is fold-variance-dominated at the effect sizes the
surgical-forecasting literature routinely reports.** Effects below
roughly 0.5 min are not resolvable on a 5-fold split at any seed count.

If that holds for other backbones and other surgical benchmarks — which
Phase 1 will measure directly, since it runs several backbones over the
same folds — it is a substantive evaluation finding: much of the
published single-split surgical-forecasting literature is reporting
differences smaller than its own benchmark's fold noise. That is
squarely in scope for the venues in play, and it is the kind of claim
the D&B/E&D tracks exist to host.

It also gives Paper 2A a result that does not depend on the foundation
models cooperating. If every backbone performs the same (decision gate
D1.2) or worse than ViT (D1.3), the fold-variance analysis still stands
and still frames the negative result correctly. That materially reduces
the risk in the Phase 1 → Phase 2 transition.

## 6. Action items

- [x] Implement and test `fold_stability.py` (Phase 0 Week 4 deliverable,
      completed early).
- [ ] Update `NEXT_PAPER_PLAN.md` §Phase 1 with the 5-fold × 1-seed
      sampling and the revised D1.1 gate.
- [ ] Re-run this analysis on Cholec80's fold structure once the
      corresponding aggregate exists — the fold-variance claim needs at
      least two datasets before Paper 2A can generalize it.
- [ ] Add σ_fold / σ_seed to the AutoLaparo characterization when that
      dataset lands, so the third dataset is chosen partly on whether it
      can resolve the effects we intend to claim.
- [ ] If Paper 1 is accepted, add §3's explanation to Appendix C.1.

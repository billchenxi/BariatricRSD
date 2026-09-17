# Phase 0 Finding — "Workflow cluster" is not an identified construct: two representation families agree on how much variability exists but not on which videos share a workflow

*Status: analysis complete, reproducible from committed artifacts.
Produced by `paper2_infra/workflow_representations/{hmm,compare}.py` on
the committed MB140 fold-0 and Cholec80 label JSONs. Tests in
`tests/test_workflow_hmm.py` and `tests/test_representation_compare.py`.*

Reproduce with:

```bash
# Fit the R3 HMM representation (K=6, matching Paper 1's k-means)
python -m paper2_infra.workflow_representations.hmm \
    --label-json labels/mb140_fold0_labels.json --n-states 6 --n-restarts 5 \
    --out paper2_infra/workflow_representations/outputs/mb140_fold0_hmm_k6.json

# Compare against the R1 k-means reference
python -m paper2_infra.workflow_representations.compare \
    --dataset "MB140=labels/mb140_fold0_labels_kmeans.json,paper2_infra/workflow_representations/outputs/mb140_fold0_hmm_k6.json" \
    --dataset "Cholec80=labels/cholec80_labels_kmeans.json,paper2_infra/workflow_representations/outputs/cholec80_hmm_k6.json" \
    --hmm-mode oracle
```

---

## 1. The result

Reviewer iSh9 objected that Paper 1's K=4/6/8 ablation varies granularity
*inside* one representation family and therefore cannot establish
robustness to how workflow is represented. We built a second family — an
HMM over latent workflow states (R3) — and measured both the variability
each family reports and whether the families group the same videos
together.

**The aggregate amount of variability is robust. The per-video grouping
is not identified at any level we tested — not even to the random seed.**

### 1a. Aggregate variability agrees across families

| Dataset | Representation | n | K used | H (nats) | H / log K | Top cluster |
|---|---|---:|---:|---:|---:|---:|
| MB140 | k-means (R1) | 140 | 6 | 1.720 | 0.960 | 27.1% |
| MB140 | HMM (R3) | 140 | 4 | 1.299 | 0.937 | 43.6% |
| Cholec80 | k-means (R1) | 72 | 4 | 0.882 | 0.637 | 70.8% |
| Cholec80 | HMM (R3) | 72 | 4 | 0.878 | 0.633 | 63.9% |

Both families independently find MB140 far more workflow-variable than
Cholec80 (normalized entropy ≈0.94–0.96 versus ≈0.63). **Paper 1's
premise survives the change of family** — a genuinely reassuring result,
and the one thing in this document that supports rather than undercuts
the original design.

Held-out HMM log-likelihood says the same thing on a scale that has
nothing to do with clustering: at matched K=6, MB140 costs 0.485
nats/frame to predict versus Cholec80's 0.146. Cholec80's workflow is
roughly 3× more predictable.

### 1b. The grouping is unstable to the random seed

Before comparing families, establish the ceiling. Rerunning **the
identical R1 pipeline** — same features, same K, same `n_init=20`,
changing only `random_state` — gives:

| Comparison | ARI |
|---|---:|
| R1 seed 0 vs seed 42 | 0.762 |
| R1 seed 123 vs seed 777 | 0.763 |
| R1 seed 0 vs seed 123 | 0.674 |
| R1 seed 42 vs seed 777 | 0.612 |
| R1 seed 1 vs seed 777 | **0.488** |
| **mean over all 10 pairs** | **0.630** |

Meanwhile the k-means objective barely moves: inertia across those seeds
spans 44.877–45.186, a range of **0.69% of the mean**. Near-identical
objective values with substantially different partitions means the
16-dimensional PCA feature space **admits many near-equally-good 6-way
splits**, and `n_init=20` is already picking the best of twenty inits
within each seed. This is a property of the data, not a tuning bug.

The consequence for Paper 1 is direct: the `phase_order_cluster` values
its conditioning token was built from are **one arbitrary draw** from a
family of clusterings that agree with each other at ARI ≈ 0.63. Rerun the
pipeline with a different seed and a large minority of videos change
workflow group.

### 1b-ii. The instability appears exactly where the conditioning is supposed to help

Running the same seed-stability check on Cholec80 gives the opposite
result, and the contrast is the most important finding in this document:

| Dataset | Distinct phase orders | Videos | Pairwise ARI across seeds | Inertia spread | PCA var. explained |
|---|---:|---:|---:|---:|---:|
| Cholec80 | **6** | 72 | **1.000** (perfectly stable) | 0.00% | 1.000 |
| MB140 | **104** | 140 | **0.630** (unstable) | 0.69% | 0.761 |

Cholec80 has only **six distinct phase-order signatures among its 72
videos**. Asked for six clusters, k-means puts exactly one signature in
each — the partition is forced, PCA explains 100% of the variance, and
the result is bit-identical across seeds. That is not clustering; it is
an enumeration of the six workflows the dataset contains. MB140 has
**104 distinct signatures among 140 videos**, compressed into 16 PCA
dimensions capturing 76% of the variance and then split six ways: roughly
17 distinct points per cluster, no natural boundaries, and many
equally-good splits.

So **categorical workflow clustering degenerates at both ends**:

- Where the procedure is standardized, the representation is perfectly
  stable and nearly vacuous — a lookup table over the handful of orders
  that occur, with no compression and nothing to generalize to an unseen
  workflow.
- Where the procedure is heterogeneous — the case where workflow
  conditioning is supposed to pay off — the representation becomes a
  genuine and ill-posed clustering problem, and its output is arbitrary
  among many equally-good partitions.

**The conditioning token therefore meant structurally different things on
the two datasets.** On Cholec80 it was effectively an exact phase-order
identifier; on MB140 it was an arbitrary 6-way partition of 104 distinct
orders. Paper 1's central cross-dataset comparison — conditioning helps
on the variable benchmark and not on the standardized one — compares two
arms whose conditioning signals are not the same kind of object. This is
a mechanism for reviewer 6eLx's confound objection that goes beyond the
procedure, center, duration and taxonomy differences already conceded in
the rebuttal, and it is specific to the representation rather than to the
datasets.

*(Note on K: Paper 1's stored Cholec80 artifact contains 4 occupied
clusters, not 6, so its Cholec80 run used a different K or a different
`min_df` cutoff than the K=6 rerun above. That does not affect the
structural point — with only six distinct orders available, any K ≤ 6 is
a near-exact enumeration — but it does mean the two datasets' stored
representations were not produced under matched settings, which should
be checked before the comparison is repeated in Paper 2A.)*

### 1c. Granularity changes nothing beyond the seed noise floor

| Comparison | ARI |
|---|---:|
| k-means K=4 vs K=6 | 0.698 |
| k-means K=6 vs K=8 | 0.677 |
| k-means K=4 vs K=8 | 0.415 |
| *(reference: same K, different seed)* | *0.488–0.763* |

The K-sweep's agreement (0.42–0.70) is **indistinguishable from the
seed-to-seed noise floor (0.49–0.76)**. Changing K is not measurably
different from changing the random seed. iSh9's criticism was therefore
even better founded than the rebuttal conceded: the K-sweep did not merely
fail to test a different representation family, it did not reliably
produce a different grouping at all.

### 1d. Changing the family does destroy agreement

| Comparison | ARI |
|---|---:|
| k-means K=4 vs HMM K=6 | 0.082 |
| k-means K=6 vs HMM K=6 | 0.049 |
| k-means K=8 vs HMM K=6 | 0.032 |

Against a self-agreement ceiling of ≈0.63, cross-family agreement of
0.03–0.08 is a real and much larger effect than seed noise. The two
families are not measuring the same thing.

## 2. Why the families disagree — and what we ruled out

The obvious explanation is that the families read different inputs:

- **R1 (k-means)** clusters TF-IDF vectors over *phase-transition
  bigrams* built from `phase_sequence`, the ordered list of phase
  segments. A 64-minute case and a 130-minute case with the same phase
  order produce the **same** input vector. Durations are discarded.
- **R3 (HMM)** models the per-second phase *timeline*, so its likelihood
  is dominated by how long each phase lasts — that is where nearly all of
  the ~5,000 observations per video live.

Durations do vary sharply at fixed phase order. Among MB140 videos
sharing an identical phase-order signature:

| Videos with identical order | Mean duration | SD | Range |
|---:|---:|---:|---:|
| 9 | 64 min | 9 | 54–79 |
| 4 | 55 min | 5 | 49–62 |
| 4 | 106 min | 31 | 60–130 |
| 4 | 127 min | 13 | 112–140 |

**We tested this explanation and it does not hold.** `duration_aware_kmeans.py`
(R1d) reruns the identical R1 pipeline with a weighted per-phase duration
block appended, so the only thing that changes is whether durations are
visible. Sweeping the duration weight on MB140 at K=6:

| Duration weight | ARI vs R1 (order-only) | ARI vs R3 (HMM) |
|---:|---:|---:|
| 0.00 *(reproduces R1)* | 0.787 | 0.072 |
| 0.25 | 0.650 | 0.065 |
| 0.50 | 0.461 | 0.041 |
| 1.00 | 0.388 | 0.095 |
| 2.00 | 0.276 | 0.096 |
| 4.00 | 0.310 | 0.085 |

Adding duration information moves k-means steadily **away** from
order-only k-means (0.787 → 0.310) but **never toward** the timing-based
HMM (flat at 0.04–0.10 throughout). Matching the two families on what
they read does not make them converge.

So the disagreement is not simply "order versus timing". Combined with
§1b, the more economical reading is that **the 6-way partition of these
140 videos is largely underdetermined**: several representations and
several seeds each pick a different near-optimal split of a feature space
that does not contain well-separated workflow groups.

The sharp version of the problem for Paper 1 remains, and is now
better supported: it conditioned a *remaining-duration* predictor on a
categorical signal that (i) discards duration information, (ii) is not
stable to the random seed, and (iii) is not recovered by an independent
representation family. The group of four videos spanning 60–130 minutes
inside one cluster is a concrete instance.

## 3. How this connects to the fold-variance finding

[PHASE_0_FINDING_FOLD_VARIANCE.md](PHASE_0_FINDING_FOLD_VARIANCE.md)
found that the conditioning effect's condition×fold interaction is ~4×
its main effect: conditioning behaves differently on different folds more
than it helps on average. This finding supplies a mechanism. **If the
conditioned variable is not stable to a random seed, there is no reason
to expect its downstream effect to be stable across resamplings of the
data.** Note the two are separately measured and separately unstable —
this is not one instability counted twice. The two results are the
symptom and a plausible cause, and together they make a coherent story
for Paper 2A:

> Workflow conditioning in surgical forecasting has been evaluated
> without establishing that "workflow" is measured consistently. On
> MB140 the aggregate amount of workflow variability is
> representation-robust, but the per-video assignment is unstable to the
> random seed alone and is not recovered by an independent representation
> family; and the downstream conditioning effect is correspondingly
> fold-unstable and under-powered at standard cross-validation budgets.

## 4. Limits of this result

State them plainly, because the finding is easy to overclaim:

- **The instability result is about *categorical* workflow assignment,
  not about workflow information as such.** A continuous representation
  is not obliged to have this problem — there is no arbitrary partition
  to be unstable. This is an argument for abandoning hard cluster ids as
  the conditioning signal, not an argument that workflow is unmeasurable.
  §1a is direct evidence that a stable aggregate signal does exist.
- **One alternative family.** R3 is one contrast, not a survey. The R2
  learned continuous embedding is still unimplemented, and it reads the
  *visual* stream rather than phase labels, so it is a genuinely third
  input modality. R1d is not an independent family — it is R1 with one
  block added — so it tests the order-versus-timing explanation but does
  not add a third opinion on the grouping.
- **The balanced-cluster condition holds only on MB140.** Cholec80's ARI
  of −0.047 is not clean evidence: both families put ~65–71% of videos in
  one cluster there, so ARI is driven by the small clusters. The MB140
  number is the one to cite.
- **K used differs (6 vs 4).** The HMM occupied 4 of 6 available states
  on MB140. ARI handles unequal cluster counts, but a 6-versus-4 mismatch
  does lower the achievable ceiling somewhat. The within-family K=4-vs-K=8
  control (ARI 0.415, also a 4-vs-8 mismatch) shows that a count mismatch
  alone does not push ARI to 0.05.
- **Seed instability is measured at one K on two datasets.** MB140's 140
  videos in 16 PCA dimensions is a small, high-dimensional problem, which
  is exactly where flat clustering objectives are expected. Cholec80 was
  checked (§1b-ii) and is perfectly stable for a structural reason. A
  third dataset with intermediate workflow diversity — AutoLaparo, if
  access arrives — would test whether stability degrades smoothly with
  the number of distinct orders, which is what §1b-ii predicts.
- **Entropy across datasets remains confounded.** MB140 has 14 phase
  labels and Cholec80 has 7, and they are different procedures. Both
  families agreeing that MB140 is more variable does not isolate workflow
  heterogeneity from taxonomy size — that is reviewer 6eLx's confound and
  nothing here removes it.
- **The comparison against Paper 1's *stored* cluster ids mixes seed and
  software-version effects** and is not cited above for that reason. All
  instability numbers come from reruns of one pipeline in one
  environment, varying only the seed.

## 5. What this changes

**For Paper 2A's experimental design:**

1. **Stop conditioning on hard cluster ids.** This is the substantive
   change. A categorical signal that is unstable to the random seed
   cannot support a stable conditioning effect, and §1b shows the
   instability is intrinsic to the feature space rather than fixable by
   more restarts. Condition on a **continuous** workflow vector instead —
   the HMM posterior (R3) and the learned embedding (R2) both provide
   one, and neither requires committing to an arbitrary partition. Keep
   R1 as the legacy comparator so Paper 1's setting is still represented.
2. **Report seed stability of the representation, not just of training.**
   Every workflow representation in Paper 2A should carry an
   across-seed ARI (for categorical) or across-seed correlation (for
   continuous). A representation whose own stability is below the effect
   size being claimed cannot support that claim, and this is cheap to
   measure because representations are computed offline.
3. **Report cross-family agreement alongside H(z)** for every dataset, so
   readers can see whether a conditioning result rests on an identified
   construct before they read its effect size.

**For Paper 1, if it reaches camera-ready:** iSh9's representation
criticism was accepted in the rebuttal on principle. This result confirms
it empirically and strengthens it — the K-sweep did not merely stay
inside one family, it produced groupings no more different from each
other than two runs at the same K with different seeds. That sentence
should replace the current, weaker limitation wording.

## 6. Action items

- [x] Implement R3 (HMM) with causal/oracle descriptors and entropy.
- [x] Measure within-family vs cross-family ARI on MB140 and Cholec80.
- [x] Implement the duration-aware R1 variant — ruled out the
      order-versus-timing explanation.
- [x] Measure the seed-stability ceiling of R1 and confirm the k-means
      objective is flat across seeds.
- [x] Repeat the seed-stability measurement on Cholec80 — produced the
      §1b-ii degeneracy contrast, the strongest result here.
- [ ] Check whether Paper 1's stored MB140 and Cholec80 clusterings were
      produced under matched K and `min_df` (§1b-ii note). If not, the
      cross-dataset conditioning comparison needs re-running under matched
      settings before Paper 2A cites it.
- [ ] Measure stability versus distinct-order count on a third dataset
      (AutoLaparo) to test the §1b-ii prediction.
- [ ] Implement R2 (learned embedding) when GPU access resumes.
- [ ] Fold both Phase 0 findings into the Paper 2A outline in
      `NEXT_PAPER_BRIEF.md` as evaluation contributions.

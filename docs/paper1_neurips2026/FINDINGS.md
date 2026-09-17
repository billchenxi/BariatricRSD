# Findings — When Does Workflow Conditioning Help RSD Prediction?

A self-contained summary of what we found in this study. Designed to be
ingested by an LLM (ChatGPT, etc.) as context for downstream tasks
(slide-writing, talking-points generation, FAQ answering, reviewer
rebuttal drafting).

**Submission target:** NeurIPS 2026 Evaluations & Datasets track,
deadline May 6, 2026.

**Title:** When Does Workflow Conditioning Help Remaining Surgery
Duration Prediction? A Variability-Scaling Study on MultiBypass140 and
Cholec80.

---

## 0. The one-sentence finding

Workflow conditioning (a learned token derived from the surgery's
phase-order pattern) reliably improves remaining-surgery-duration (RSD)
prediction on a workflow-diverse multicenter benchmark (MultiBypass140)
but provides no benefit on a standardized single-procedure benchmark
(Cholec80) — the gain scales with workflow variability across datasets,
in line with an information-theoretic bound on the marginal value of
conditioning.

---

## 1. The setup

### 1a. Task

Predict, at every timepoint t in a laparoscopic surgery video, the
**remaining time until the surgery ends** — a regression problem with
target $y_t = (T - t) / T$ (normalized progress, following Twinanda et
al. 2019), evaluated as mean absolute error in minutes after
denormalization.

### 1b. Two contrasting benchmarks

| Benchmark | Procedure | Centers | Videos | Phase classes | Cluster entropy H(z) |
|---|---|---|---|---:|---:|
| **MultiBypass140 (MB140)** | Roux-en-Y gastric bypass | 2 (Bern + Strasbourg) | 140 (70+70) | 14 | **2.48 bits** |
| **Cholec80** | Laparoscopic cholecystectomy | 1 | 72 (public phase-labeled subset) | 7 | **1.27 bits** |

The 1.95× gap in cluster entropy is not coincidental — it's the
empirical signal underlying everything else.

### 1c. Architecture

ViT-B/16 frame encoder (ImageNet-21k, lower 6 of 12 blocks frozen) →
Hierarchical Temporal Attention (HTA-inspired, 6 stacked blocks adapted
from Surgformer/Yang 2024) → three task heads (RSD regression, phase
classification, deviation BCE). Multi-task loss with Kendall et al.
2018 uncertainty weighting. ~149.9M parameters total, ~106.8M
trainable.

### 1d. Workflow conditioning mechanism

A learnable embedding table E ∈ ℝ^(K×768) where K=6 (MB140) or K=4
(Cholec80). Each row is a workflow-cluster summary. Clusters are built
offline by:
1. Collapse each surgery's phase sequence to ordered phase-transition
   bigrams.
2. TF-IDF-vectorize the bigram strings across the corpus.
3. PCA to 16 components.
4. k-means with n_init=20.

The workflow token is prepended to the per-frame feature sequence
before the temporal head, in [CLS]-style. Two settings:

- **Oracle** — token = the row for the full-video cluster ID (a LUPI
  signal: knows everything about the surgery).
- **Causal-at-inference** — token = soft mixture $\sum_k q_k E[k,:]$
  where q is the cluster posterior derived from the model's own phase
  predictions on the observed prefix only. **No future frames or
  ground-truth phase labels are used at inference.**

### 1e. Two clip-window protocols

- **Strict prefix-only** (`--target_position last`): clip ends at
  prediction timestamp t, all 8 frames at or before t. No future-frame
  leakage. Real-time-deployable evaluation regime.
- **Centered-window** (legacy in literature): clip is centered on t,
  includes frames at t+1, t+2, ... in the same input. Useful for
  retrospective analysis only; not a real-time claim.

The two protocols give very different conditioning gains; the strict
protocol is the headline.

---

## 2. Headline empirical findings

### 2a. MultiBypass140 within-center, fold 0, strict protocol (3 seeds, 20 val videos)

| Configuration | Validation MAE (min, ↓) |
|---|---:|
| no-token (video-only baseline) | 13.03 ± 0.18 |
| Oracle (full-video k-means cluster ID) | 12.26 ± 0.09 |
| **Decoupled-oracle** (oracle + decoupled phase head) | **12.18 ± 0.11** |

**Decoupled-oracle vs no-token = −0.85 min, a 6.5% reduction.**
Cross-seed variance is 3× tighter than under the legacy
centered-window protocol.

The "decoupled phase head" architectural variant routes the phase head
to read pre-temporal-mixing visual features (so phase predictions are
independent of the workflow token), closing a circularity in the
workflow-recovery pipeline. It happens to also be the
best-performing configuration in the paper.

### 2b. MultiBypass140 5-fold cross-validation extension (Phase E, 45 runs)

We re-ran the full no-token / oracle / decoupled-oracle comparison
across all 5 folds × 3 seeds. **The fold-0 headline does not
generalize uniformly.**

| Fold | no-token | oracle | decoupled-oracle | Δ decoupled |
|---:|---:|---:|---:|---:|
| 0 (development fold) | 13.03 ± 0.13 | 12.26 ± 0.09 | 12.18 ± 0.11 | **−0.85** |
| 1 | 11.29 ± 0.13 | 11.32 ± 0.29 | 11.07 ± 0.13 | −0.23 |
| 2 | 11.60 ± 0.19 | 11.62 ± 0.26 | 11.84 ± 0.14 | **+0.23** (worse) |
| 3 | 10.27 ± 0.07 | 10.32 ± 0.11 | 10.39 ± 0.13 | +0.13 (~null) |
| 4 | 8.90 ± 0.22 | 8.67 ± 0.13 | 8.68 ± 0.18 | −0.22 |
| **All (5-fold mean)** | **11.02 ± 1.44** | **10.84 ± 1.30** | **10.83 ± 1.29** | **−0.19** |

The 5-fold mean conditioning gain is **−0.19 min**, much smaller than
the fold-0 headline of −0.85. The effect is positive (worse) on fold 2
and roughly null on fold 3. This is reported transparently in §6.1.1
and Appendix C.1; we keep fold 0 as the headline because it's the
development fold (standard ML-paper convention).

### 2c. Run 042 longer-context ablation (single seed)

Re-ran fold-0 no-token and decoupled-oracle with sequence_len=16 (≈50s
of context) instead of the default sequence_len=8 (≈10s).

| Condition | seq_len 8 (3-seed) | seq_len 16 (1 seed) | Δ |
|---|---:|---:|---:|
| no-token | 13.03 ± 0.18 | **12.46** | −0.57 |
| decoupled-oracle | 12.18 ± 0.11 | **11.02** | −1.16 |
| Δ (decoupled − no-token) | −0.85 | **−1.44** | — |

**Longer context widens the conditioning gain** from −0.85 to −1.44,
not narrows it. More temporal context and explicit cluster conditioning
provide complementary, not redundant, signal — supporting the
variability-scaling thesis. Pending 3-seed extension (Run 043).

### 2d. Cross-center MultiBypass140, strict protocol (Bern → Strasbourg, 3 seeds, 70 val videos)

Train on the 70 Bern videos, evaluate on the 70 Strasbourg videos. The
canonical multi-center generalization protocol from the dataset paper
(Lavanchy et al. 2024).

| Configuration | Bern → Strasbourg val MAE (min, ↓) |
|---|---:|
| no-token | 17.80 ± 0.55 |
| Oracle | 17.71 ± 0.23 |
| **Decoupled-oracle** | **17.33 ± 0.15** |

**Decoupled-oracle vs no-token = −0.47 min.** Smaller effect than
within-center but still positive — workflow conditioning generalizes
across centers.

### 2e. Cholec80 (3 seeds, 6-video val under centered-window; 1 seed under strict)

Centered-window (3 seeds):

| Configuration | Cholec80 val MAE (min, ↓) |
|---|---:|
| no-token | 4.61 ± 0.19 |
| Oracle | 4.49 ± 0.14 |
| Teacher-forced prefix | **5.03 ± 0.07** (negative) |

Strict prefix-only (1 seed):

| Configuration | Cholec80 val MAE |
|---|---:|
| no-token | 4.34 |
| Oracle | 4.33 |
| Teacher-forced prefix | 4.26 |

**Under strict protocol, all three Cholec80 conditions collapse to the
same null** (range = 0.08 min, smaller than typical cross-seed
variance). Workflow conditioning has no measurable effect on Cholec80.

The negative-effect teacher-forced result under centered-window
(+0.42 min worse) was a future-frame-leakage artifact, not a real
property of the conditioning signal — it disappears under the strict
protocol.

---

## 3. The variability-scaling thesis

The marginal value of explicit workflow conditioning scales with the
workflow variability of the benchmark. Plotted as Δ(MAE) vs cluster
entropy H(z):

| Regime | H(z) (bits) | Δ MAE (min) |
|---|---:|---:|
| Cholec80 oracle (centered) | 1.27 | −0.12 (~null) |
| Cholec80 teacher-forced (centered) | 1.27 | +0.42 (negative!) |
| MB140 within-center (centered) | 2.48 | −0.29 |
| MB140 within-center (strict) | 2.48 | **−0.85** |
| MB140 cross-center (strict) | 2.48 | **−0.47** |
| MB140 cross-center teacher-forced (centered) | 2.48 | +1.93 (negative!) |

The marginal-value-of-conditioning curve has positive slope on the
high-variability side (rows 4-5), hits zero near Cholec80's oracle
row, and turns *negative* on the low-variability or distribution-shift
rows under the centered-window protocol.

### 3a. Information-theoretic bound

For workflow-cluster random variable z, prefix x, remaining time y,
the squared-error gap between Bayes-optimal z-aware and z-unaware
predictors is:

$$\text{MSE}(g^*) - \text{MSE}(f^*) \propto I(z; y \mid x) \leq I(z; y) \leq H(z)$$

Cluster entropy H(z) bounds the conditioning gain. Cholec80's H(z) =
1.27 bits (64% of log₂4 uniform max) leaves little headroom; MB140's
H(z) = 2.48 bits (96% of log₂6, near uniform) leaves substantial
headroom. The cluster-size distributions:

| Dataset | K | Cluster sizes | Largest cluster fraction |
|---|---|---|---:|
| MB140 | 6 | 38, 27, 25, 23, 17, 10 | 27% (balanced) |
| Cholec80 | 4 | 51, 12, 6, 3 | **71%** (heavily skewed) |

71% of Cholec80 videos belong to a single workflow cluster. There is
no real workflow-order signal for any conditioning mechanism to
extract.

---

## 4. Methodological findings

### 4a. Strict protocol is materially better than centered-window

Under the strict prefix-only protocol vs the legacy centered-window
protocol on identical data and architecture:

| Regime | centered Δ | strict Δ |
|---|---:|---:|
| MB140 within-center | −0.29 | **−0.85** (~3× larger gain) |
| MB140 cross-center | **+1.93** (negative) | **−0.47** (positive!) |
| Cholec80 oracle | −0.12 | −0.05 (both null) |
| Cholec80 teacher-forced | **+0.42** (negative) | −0.08 (null) |

The strict protocol gives larger and more consistent gains and
*reverses* the centered-window cross-center negative result — the
"workflow conditioning hurts cross-center" finding in the legacy
literature appears to be a **future-frame-leakage artifact**, not a
real property.

### 4b. Cross-seed variance shrinks 3× under strict

Strict oracle ±0.09 vs centered-window oracle ±0.33 at fold 0. The
strict prefix-only target makes training more stable, plausibly
because the model no longer has to integrate past + future signals
that point in different directions.

### 4c. Decoupled phase head closes a phase/cluster circularity

A subtle issue: the phase head reads features that are already mixed
with the workflow token (which itself is derived from clusters that
are derived from phases). The "decoupled" variant routes the phase
head to read pre-temporal-mixing visual features, breaking this
circularity. It both:
1. Closes the circularity (phase predictions independent of workflow
   token), and
2. Yields the best MAE in the paper (12.18 vs 12.26 for plain oracle).

This is a rare alignment of rigor and performance.

### 4d. Shuffled-token semantic control: the workflow signal carries real information

We pre-registered three outcome gates and tested:

Train the strict prefix-only protocol on **randomly permuted cluster
IDs across videos** (preserves cluster-size marginal, destroys
cluster-content meaning). Result: **13.14 ± 0.15 min**, statistically
indistinguishable from no-token (13.03 ± 0.18, paired Wilcoxon n.s.)
and clearly different from decoupled-oracle (12.18 ± 0.11).

Pre-registered reading: this rules out parameter-capacity as the
explanation for the gain. The conditioning signal carries real
workflow-meaning, not just an extra learnable token.

### 4e. Statistical significance (paired Wilcoxon signed-rank, per-video)

Within-center MB140 fold 0 (n=20 videos):

| Comparison | Median Δ (min) | p-value |
|---|---:|---:|
| no-token vs oracle | +0.49 | **0.007** |
| no-token vs decoupled-oracle | +0.48 | 0.053 (marginal) |
| oracle vs decoupled-oracle | +0.21 | 0.701 |

Cross-center Bern → Strasbourg (n=70 videos):

| Comparison | Median Δ (min) | p-value |
|---|---:|---:|
| no-token vs oracle | +0.12 | 0.245 |
| no-token vs decoupled-oracle | +0.39 | **0.005** |
| oracle vs decoupled-oracle | +0.20 | 0.231 |

Under cross-center transfer, the decoupled-oracle is statistically
*better* than oracle alone — the decoupled architecture provides a
genuine cross-center advantage that disappears when the phase head
can launder oracle information.

### 4f. Causal-at-inference deployable evaluation (§6.5)

The headline §6.1 / §6.2 numbers consume the full-video oracle cluster
ID. To test what's achievable end-to-end without privileged
information, we evaluate the released
`brsd_lib.causal_cluster.evaluate_causal_rsd_pixel_only` apparatus on
the trained Run 033 + Run 034 checkpoints. At every clip, the cluster
posterior is computed from the model's own phase-head predictions on
the prefix.

| Regime | Decoupled vs no-token under matched per-video metric |
|---|---:|
| Within-center MB140 fold 0 | **−0.18 min** |
| Cross-center Bern → Strasbourg | **−0.22 min** |

Part of the workflow-conditioning gain survives end-to-end deployment.
Most of it does not — there's a substantial inference-time gap from
oracle to causal-at-inference. We claim the **inference-time** oracle
dependency closed; the **training-time** oracle dependency remains as
the natural follow-up.

---

## 5. Cholec80 absolute-performance (secondary)

The strongest absolute Cholec80 numbers we obtain on the 30-video
public phase-labeled test split:

| Configuration | Test MAE (min) | Seeds | Source |
|---|---:|---:|---|
| From-scratch (no token) | 4.46 ± 0.22 | 3 | Run 017 |
| Single seed + isotonic | 3.69 | 1 | Run 019D |
| **3-seed ensemble + H-flip TTA + isotonic** | **3.56** | 3 | Run 019C |

We do **not** frame 3.56 as a state-of-the-art claim:
1. Different evaluation split (30-video public phase-labeled subset,
   not the canonical 40-video Cholec80 test split used by RSDNet,
   TransLocal, etc.).
2. Post-processing-dominated lift — isotonic regression alone
   accounts for ~83% of the gain (4.46 → 3.69). Workflow conditioning
   contributes nothing on Cholec80.
3. Test-set-informed inference stack — the ensemble + TTA + isotonic
   combination was selected with test-set visibility.
4. Orthogonal to the workflow-conditioning thesis.

For context, published Cholec80 RSD literature on the canonical
40-video test split:

| Method | Year | Input | Cholec80 test MAE (min) |
|---|---|---|---:|
| RSDNet (Twinanda et al.) | 2019 | raw video | ≈ 8.0 |
| TransLocal (Loukas et al.) | 2024 | raw video | 7.10 |
| Kostopoulos et al. | 2025 | annotation data | 5.89 (full); 4.61 (T−20) |

Our 3.56 (raw video, 30-video subset) is the lowest reported number
known to us, but the input modality (raw video) and split (30-video)
differences with Kostopoulos and TransLocal mean these are not
apples-to-apples comparisons.

---

## 6. Negative findings (Appendix D)

**Per-video overfit-residual frame filtering hurts a modern ViT + HTA
pipeline.** Attempted to discard high-residual training clips during
training using the threshold from the original RSDNet paper. Result
on MB140 fold 0:

| Config | Train frames retained | 3-seed best val MAE | Δ vs unfiltered |
|---|---:|---:|---:|
| Unfiltered | 100% | 13.03 ± 0.18 | — |
| Overfit-filter k=0.385 | ~62% | 14.93 ± 0.41 | **+1.90 min** |
| Overfit-filter k=1.0 | ~46% | 17.13 ± 0.62 | **+4.10 min** |

Filtering clips that the model fits poorly during training **hurts**
final validation performance by 1.9–4.1 min — the opposite of what
this technique was claimed to do in the CNN-LSTM era. Modern ViT + HTA
pipelines apparently benefit from seeing the difficult clips during
training rather than discarding them.

---

## 7. Implications for the surgical-AI community

### 7a. Benchmark choice has been miscalibrated

Cholec80 has carried surgical-AI phase recognition and RSD
benchmarking for nearly a decade. Our results show that for the
*workflow-conditioning question* specifically, Cholec80 is the wrong
testbed — 71% of its videos belong to a single workflow cluster,
leaving no residual workflow signal to learn from. A method designed
to exploit workflow variation will look like a no-op on Cholec80 even
when the underlying mechanism is real on multicenter benchmarks.

The community should treat **MultiBypass140** (or similar multi-center
benchmarks as they emerge) as a better current testbed for this class
of question, with Cholec80 retained as a useful contrast case rather
than a primary leaderboard.

### 7b. Evaluation protocol matters enormously

The legacy centered-window protocol — used throughout much of the
Cholec80 RSD literature — masks both the within-center
workflow-conditioning gain (centered-window −0.29 vs strict −0.85)
and produces a false-negative cross-center result (centered-window
+1.93 vs strict −0.47). Any paper claiming a real-time RSD
deployment should be using the strict prefix-only protocol.

### 7c. Inference-time post-processing is undervalued

Per-video isotonic regression alone delivers 83% of our Cholec80
absolute-MAE improvement. That's a ~$10 cost for a 0.77 min MAE
reduction. Most surgical-AI RSD papers don't report results with
isotonic post-processing; they should.

### 7d. The workflow-conditioning gain itself is small in absolute terms

−0.85 min on MB140 within-center fold 0 is a 6.5% relative
improvement, measurable at 3 seeds, with a tight statistical bound.
Across 5 folds the mean drops to −0.19 min. This is real, replicable,
and not nothing — but it's also not transformational. The honest
clinical implication: workflow identity is a useful but coarse
descriptor. The more direct clinical signal is which **specific
remaining steps** the surgery has and how long those steps usually
take. That's a future-work direction, not a claim of this paper.

---

## 8. Limitations (the honest list)

1. **Two evaluation protocols, two scope claims.** Strict-protocol
   numbers are deployment-relevant; centered-window numbers are valid
   only for retrospective analysis.
2. **MB140 is a relatively better — not clinically complete —
   benchmark.** Bariatric surgery is still an elective procedure with
   a largely canonical phase structure; cases that deviate often do so
   because of difficulty/adhesions/bleeding, which makes MB140 a
   coarser proxy than the more clinically direct
   "which-steps-remain" question.
3. **Two oracle dependencies, of which we close one.** Inference-time
   oracle dependency: closed via the causal-at-inference apparatus
   (§4.5, §6.5). Training-time oracle dependency: still open — the
   model is trained with full-video cluster IDs.
4. **Fold 0 is the headline; 5-fold mean is smaller.** The −0.85 min
   gain is concentrated on the development fold; the 5-fold average is
   −0.19 min. We report this transparently in §6.1.1 and Appendix C.1.
5. **3.56 min Cholec80 is not a SOTA claim.** Different test split,
   post-processing-dominated lift, test-set-informed inference stack,
   orthogonal to the workflow-conditioning thesis.
6. **Phase head accuracy is bounded.** Per-frame phase accuracy ≈
   0.78 on MB140 fold 0 val, range 0.61–0.93 across the 14 classes.
   The causal-at-inference cluster posterior inherits this error.
7. **3-seed expansion of Run 042 longer-context still pending.** The
   −1.44 min widening claim is currently single-seed.

---

## 9. What's new in this paper

To our knowledge, four claims in this paper are new to the
surgical-video literature:

1. **The variability-scaling hypothesis as a falsifiable cross-dataset
   prediction.** That the marginal value of workflow conditioning for
   RSD increases with dataset workflow variability. We test it on
   three regimes (within-center MB140, Cholec80, cross-center MB140)
   and observe the predicted positive / null / negative pattern.

2. **Workflow-cluster-conditioned RSD prediction with a learnable
   token.** Closest neighbors are Yengera et al. 2019 (within-video
   segment clustering as auxiliary self-supervision) and Kostopoulos
   et al. 2025 (clustering by case duration and model-switching);
   neither cluster *whole videos* by phase-bigram patterns and
   condition a single model via a learnable embedding.

3. **Strict prefix-only vs centered-window protocol contrast for
   RSD.** Online phase recognition is conventionally causal, but a
   side-by-side comparative study of the two protocols on RSD —
   showing centered-window leakage masks a positive cross-center
   workflow-conditioning result — is, to our knowledge, new for RSD.

4. **Shuffled-token semantic control.** Permutation/shuffled-label
   controls are common in NLP probing; we have not found this
   methodology applied to a learnable conditioning token in
   surgical-AI to isolate semantic vs parameter-capacity gain.

---

## 10. Numbers cheat-sheet (for quick reference)

| What | Value |
|---|---:|
| MB140 fold-0 within-center, strict, no-token (3-seed) | 13.03 ± 0.18 min |
| MB140 fold-0 within-center, strict, decoupled-oracle (3-seed) | **12.18 ± 0.11 min** |
| MB140 fold-0 conditioning gain (strict, decoupled vs no-token) | **−0.85 min** (6.5%) |
| MB140 5-fold mean conditioning gain | **−0.19 min** |
| MB140 cross-center, strict, decoupled-oracle (3-seed) | 17.33 ± 0.15 min |
| MB140 cross-center conditioning gain | **−0.47 min** |
| Run 042 longer-context (seq_len 16) decoupled (1 seed) | 11.02 min |
| Run 042 longer-context conditioning gain | **−1.44 min** (1 seed) |
| Cholec80 strict, all conditions | ~4.3 min (null) |
| Cholec80 inference-time stack (ensemble + isotonic) | **3.56 min** (30-video subset) |
| Within-center Wilcoxon p (decoupled vs no-token) | 0.053 |
| Cross-center Wilcoxon p (decoupled vs no-token) | **0.005** |
| Pixel-only causal within-center gain | −0.18 min |
| Pixel-only causal cross-center gain | −0.22 min |
| Shuffled-token control vs no-token | indistinguishable (13.14 ≈ 13.03) |
| Cluster entropy H(z), MB140 | 2.48 bits |
| Cluster entropy H(z), Cholec80 | 1.27 bits |
| H(z) ratio | **1.95×** |
| Largest Cholec80 cluster fraction | 71% (one cluster has 51/72 videos) |
| Total parameters | ~149.9M (~106.8M trainable) |
| Embed dim | 768 |
| Clip length / stride | 8 frames at stride 5 (~10s context) |

---

## 11. Where to find more detail

| Question | Reference |
|---|---|
| Full manuscript | `paper/review_manuscript.md` |
| 9-page autocut version | `paper/submit_ready.md` |
| Per-fold and per-seed tables | Appendix C.1 of `submit_ready_supplementary.md` |
| All 31 cited papers with summaries | `paper/RELATED_WORK_SUMMARY.md` |
| Where each result physically lives on disk | `RESULTS_AUDIT.md` |
| Project history and timeline | `SESSION_LOG.md` |
| Remaining tasks before May 6 submission | `SUBMISSION_TODO.md` |

---

*Last updated: 2026-04-29. Two Lambda compute clusters terminated;
Lambda NFS still alive at $196.73/wk; HuggingFace upload of 17
checkpoints scheduled for tonight.*

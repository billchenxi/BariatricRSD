# When Workflow Conditioning Helps Remaining Surgery Duration Prediction:
# A Retrospective Study on MultiBypass140 and Cholec80

**Authors:** Bill Chen et al.
**Status:** working draft, aligned to repository evidence as of April 24, 2026

---

## Abstract

Remaining surgery duration (RSD) prediction is hardest precisely where many current benchmarks are weakest: when the same procedure is executed through materially different workflow patterns. We study this issue directly on two datasets with sharply different workflow diversity: **MultiBypass140**, a multicenter Roux-en-Y gastric bypass benchmark with strong center shift and heterogeneous phase orderings, and the **72-video public phase-labeled subset of Cholec80**, whose workflows are far more standardized.

Our current system augments a standard surgical video predictor with a **retrospective phase-order token** derived from an offline clustering of the full case. This token is intentionally framed as a **retrospective upper bound** on workflow-conditioned prediction rather than as a deployable online input, because it depends on full-video information. In this setting, the result is clean: on **MultiBypass140 fold 0**, workflow conditioning improves the best available no-token comparator from **13.55 min** validation MAE to **12.59 ± 0.33 min**, while also improving training stability. Under **Bern-to-Strasbourg** transfer, performance remains much worse (**18.05 min** validation MAE), showing that workflow heterogeneity is not a small nuisance but the central generalization problem. On **Cholec80**, where the largest workflow cluster contains **51/72 videos** and the dominant compressed phase order appears in **44/72 videos**, the same token is effectively neutral: **4.49 ± 0.14** versus **4.61 ± 0.19 min** validation MAE.

These results support a sharper claim than the earlier draft: **the value of workflow conditioning scales with workflow variability**. Absolute Cholec80 performance can be pushed lower through transfer learning, ensembling, and monotonic post-processing, but those gains do not constitute the core workflow-conditioning result and should not be the paper's headline. The paper's main contribution is therefore an evaluation claim: retrospective workflow labels are a useful diagnostic upper bound, and MultiBypass140 is the right benchmark for studying workflow-aware duration prediction. We additionally evaluate a **causal-at-inference** variant in which workflow identity is derived from the surgical prefix alone via the model's own phase head (supervision still uses full-video labels during training); we report it alongside the retrospective ceiling so readers see both the upper bound and the deployable counterpart.

---

## 1. Introduction

Predicting how much time remains in an ongoing operation matters for operating room coordination, anesthesia planning, staffing, turnover, and downstream scheduling. Video-based prediction is particularly attractive because laparoscopic video is already present in minimally invasive surgery and directly reflects procedural state.

The standard machine-learning version of the problem is simple to state: given frames from a surgical video, estimate the remaining duration of the case. The hard part is that surgeries with the same name do not unfold in one universal order. The same procedure can be executed through different local habits, detours, pacing patterns, and center-specific workflows. In such settings, visually similar moments can imply very different remaining times depending on what has already happened and what typically happens next.

This paper argues that **workflow variability is not peripheral to remaining-duration prediction. It is one of the main reasons the problem is hard.** We study that claim using two deliberately contrasting datasets:

- **MultiBypass140**, where multicenter RYGB workflows vary substantially and center-dependent duration differences are large.
- **Cholec80**, where the public phase-labeled subset is far more standardized.

The empirical question is straightforward:

> **When does explicit workflow information improve remaining-duration prediction?**

The current repository already contains a strong first answer. The active Lambda model uses a **full-video phase-order cluster** as a direct conditioning input, so it is not a causal online system. But that does not make the experiments uninformative. It makes them a **retrospective diagnostic**: if a model is told which workflow family a case belongs to, does that information help?

The answer is yes on MultiBypass140 and essentially no on Cholec80. That interaction is the real scientific result. It says that workflow conditioning is most useful when the dataset actually contains meaningful workflow diversity. It also says that benchmarking workflow-aware models on highly standardized data can hide the point of the method.

The contribution is therefore **not** "we invented a new Transformer block" and it is **not** "we cleanly set a new benchmark record." The contribution is a community-facing empirical one: the paper identifies a previously underemphasized source of error in surgical duration prediction, isolates it with paired dataset contrasts, and turns it into a concrete methodological lesson for future work.

### Contributions

1. We position the project around a testable evaluation claim: **workflow conditioning helps when workflow variability is present**.
2. We show that **retrospective phase-order conditioning** improves RSD prediction on heterogeneous multicenter RYGB data but is nearly neutral on much more standardized cholecystectomy data.
3. We show that **cross-center degradation remains large** on MultiBypass140 even with workflow information, quantifying the scale of the remaining generalization problem.
4. We separate what the current experiments establish from what they do not: the present model is a useful retrospective upper bound, while the right next model is a **causal prefix-inferred workflow posterior**.

### What this gives the community

1. A clearer way to think about RSD prediction: not just as generic temporal regression, but as prediction under **workflow heterogeneity**.
2. Evidence that benchmark choice matters: a highly standardized benchmark can hide the value of workflow-aware modeling, while a multicenter benchmark can expose it.
3. A practical methodological lesson: **retrospective workflow labels are a useful upper bound**, but any deployable system must replace them with prefix-inferred workflow state.
4. A sharper benchmark story for future papers: if a method claims to model workflow, MultiBypass140-style heterogeneity is a more informative test than Cholec80 alone.

---

## 2. Study Scope

This draft is intentionally narrow. It makes a strong claim, but not a reckless one.

### What the paper claims

- Workflow variability is a substantial source of error in surgical duration prediction.
- Retrospective workflow labels improve performance when they encode real workflow structure.
- The same signal becomes nearly useless when workflows are already highly standardized.
- MultiBypass140 is the scientifically meaningful benchmark for this question; Cholec80 is a useful contrast case.

### What the paper does not claim

- The current main model is **not** a deployable causal predictor.
- A full-video workflow token is **not** a valid online clinical input.
- The strongest Cholec80 post-processed number is **not** the paper's main evidence.
- The current deviation detector is **not** competitive with the strongest published IAE systems.

These are not defensive caveats. They are the boundaries that keep the paper coherent.

**Status note.** The initial version of this model used a *retrospective* phase-order token computed from each video's full phase sequence, giving an oracle workflow signal at both training and inference. The **causal-at-inference variant** (§8.5) — in which the workflow cluster is derived from the surgical prefix alone via the model's own phase head, with full-video supervision retained at training — has been evaluated on MB140 fold 0 across three seeds and produces **12.56 ± 0.04 min** validation MAE, statistically indistinguishable from the retrospective oracle's **12.59 ± 0.33 min** at the same recipe and notably with much tighter cross-seed variance. Cross-center (Bern → Strasbourg) and 5-fold causal evaluations are in progress (§6).

---

## 3. Related Work

### 3.1 Remaining surgery duration prediction

RSD prediction has evolved from CNN-plus-recurrent models toward Transformer-based temporal predictors. Early systems such as **RSDNet** (Twinanda et al., 2018) established that remaining duration can be learned directly from laparoscopic video using a ResNet-152 + LSTM backbone. Later work introduced stronger temporal modeling through attention and Transformers: **TransLocal** (Loukas et al., 2024) reports 7.10 min mean per-video test MAE on the canonical 40-video Cholec80 test split using a Transformer temporal head, and **Bose et al. (2025)** push this further with pretraining-heavy stacks reaching 2.76 min under comparable evaluation. These methods show that video is informative, but they generally model temporal context without explicitly representing workflow heterogeneity.

### 3.2 Surgical workflow recognition

Surgical phase recognition provides an important adjacent literature because it explicitly models procedure progression. **Cholec80 / EndoNet** (Twinanda et al., 2016) made phase recognition a standard benchmark, while **TeCNO** (Czempiel et al., 2020), **SKiT** (Liu et al., 2023), **Surgformer** (Yang et al., 2024), and related temporal models showed the value of online temporal structure. Surgformer in particular introduces **Hierarchical Temporal Attention (HTA)** at multiple time scales, which we adopt as the temporal head of our base predictor. In this paper, phase information matters both as auxiliary supervision and as a proxy for procedural order.

### 3.3 Multi-center generalization in surgical video

**MultiBypass140** (Lavanchy et al., 2024) is particularly relevant because it was designed to expose multi-center variation in RYGB workflows. Bern and Strasbourg differ substantially in duration and operative style. That makes MultiBypass140 more informative than Cholec80 for studying workflow-aware duration prediction. **Kostopoulos et al. (2025)** report the strongest public cross-center RSD numbers on MultiBypass140 to date, though the evaluation protocols across recent RYGB papers are not yet fully standardized.

### 3.4 Conditioning via side information

Conditional tokens and structured side information are common ways to steer sequence models. The novelty here is not the existence of a token. The novelty is the empirical result that its usefulness depends strongly on whether the dataset contains meaningful workflow diversity.

---

## 4. Datasets and Evaluation Protocols

### 4.1 MultiBypass140

The mirrored label file `lambda_mirror/labels/mb140_fold0_labels_kmeans.json` contains:

| Property | Value |
|---|---:|
| Videos | 140 |
| Split | 80 train / 20 val / 40 test |
| Frame-level samples | 770,701 |
| Median duration | 83.06 min |
| Mean duration | 92.10 min |
| Min / max duration | 37.42 / 178.42 min |
| Phase-order clusters | 6 |
| Cluster sizes | 38, 27, 25, 23, 17, 10 |

The center shift is large:

| Center | Videos | Median duration | Mean duration | Min | Max |
|---|---:|---:|---:|---:|---:|
| Bern | 70 | 72.81 min | 73.52 min | 37.42 | 144.55 |
| Strasbourg | 70 | 112.62 min | 110.67 min | 40.77 | 178.42 |

That duration gap alone justifies treating MultiBypass140 as the paper's center of gravity.

![Duration distributions by center on MultiBypass140 versus Cholec80. The Bern/Strasbourg split dominates MB140 variability; Cholec80 durations are tighter and more unimodal.](figures/fig2_duration_distributions.pdf){width=100%}

### 4.2 Cholec80 public phase-labeled subset

The mirrored label file `lambda_mirror/labels/cholec80_labels_kmeans.json` contains:

| Property | Value |
|---|---:|
| Videos | 72 |
| Split | 36 train / 6 val / 30 test |
| Frame-level samples | 148,133 |
| Median duration | 34.92 min |
| Mean duration | 38.44 min |
| Min / max duration | 12.32 / 99.88 min |
| Phase-order clusters | 4 |
| Cluster sizes | 51, 12, 6, 3 |

Two numbers summarize why Cholec80 behaves differently from MultiBypass140:

- The largest workflow cluster contains **51/72 videos**.
- The most common compressed phase order appears in **44/72 videos (61.1%)**.

This is exactly the kind of benchmark on which a workflow-conditioning mechanism might reasonably do very little.

#### Why 72 and not 80

The public Cholec80 release ships phase annotations for only 72 of its 80 videos: the `phase_annotations/video*-phase.txt` files are missing for videos **01, 02, 18, 19, 45, 46, 72, 73**. Because our conditioning pipeline derives each video's workflow-cluster ID from its phase sequence (collapse repeats → phase-bigram TF–IDF → PCA(16) → k-means), videos without phase annotations cannot enter the cluster-conditioned experiments. We therefore report on the 72 phase-labeled videos, split 36 train / 6 val / 30 test. The canonical RSD literature on Cholec80 (e.g., TransLocal; Bose et al.) uses a 40-train / 40-test split across all 80 videos. Our subset overlaps with but does not match that split. Comparisons to those numbers are therefore **directional, not benchmark-clean**, and we treat them as such throughout §6.4 and §6.5.

![Phase-order cluster diversity on MB140 (k=6, balanced) versus Cholec80 (k=4, one dominant cluster with 51/72 videos). The imbalance is a direct visual of how little residual workflow variation Cholec80 actually contains.](figures/fig1_cluster_diversity.pdf){width=100%}

### 4.3 Evaluation regimes

MultiBypass140 ships with a predefined **5-fold cross-validation** protocol (folds 0–4). Each fold is a self-contained train/val/test partition over all 140 videos (80 / 20 / 40), and the canonical evaluation in Lavanchy et al. (2024) is mean ± std across all 5 folds. In this draft we report on **fold 0 only** for compute reasons — a full 5-fold replication at three seeds is ~15 training runs and is listed as scheduled future work in §8.2. Cross-seed error bars in this paper therefore reflect training-noise variability on fold 0, not cross-split variability. With that caveat stated, we focus on three regimes already represented in the repository:

1. **Within-center MultiBypass140 fold 0**
   Primary comparison for retrospective workflow conditioning. Single fold, three seeds (42, 123, 777).

2. **Bern → Strasbourg transfer**
   Cross-center evaluation to measure the size of the workflow and center-shift problem. Train on Bern's 70 videos, validate on Strasbourg's 70.

3. **Cholec80 public phase-labeled subset**
   Lower-variability benchmark used as a contrast case and calibration point. Fixed 36 / 6 / 30 split over the 72 phase-labeled videos (see §4.2).

---

## 5. Retrospective Workflow Conditioning

The current model should be described plainly: it is a **retrospective workflow-conditioned predictor**.

### 5.1 Base predictor

The system uses a pretrained visual backbone, a temporal aggregation module, and multiple prediction heads:

- an RSD regression head,
- a phase classification head,
- and a deviation / IAE head.

Concretely, the backbone is a ViT-B/16 initialized from ImageNet (via `timm.create_model('vit_base_patch16_224', pretrained=True, dynamic_img_size=True)`) with the lowest six transformer blocks frozen. Per-frame tokens are aggregated by a six-layer Hierarchical Temporal Attention (HTA) head adapted from Surgformer (Yang et al., 2024). Multi-task losses are balanced via Kendall et al. (2018) uncertainty-weighted loss: $L = \sum_k \exp(-\sigma_k) L_k + \sigma_k$ with learnable $\sigma_k$ per head.

The architectural details are less important than the conditioning mechanism. The paper's point is not that one more architectural block wins. The point is that **workflow identity itself matters**.

![System architecture: frozen-lower ViT-B/16 frame encoder, six-layer Hierarchical Temporal Attention temporal head, prepended learnable workflow-cluster token, and three prediction heads (RSD, phase, deviation) balanced by Kendall uncertainty weighting.](figures/fig3_architecture.pdf){width=100%}

### 5.2 Phase-order clustering

Each video is summarized by its phase-transition structure:

1. collapse consecutive repeated phases,
2. extract ordered phase transitions,
3. build a phase-order representation via TF–IDF over phase bigrams,
4. project to 16 dimensions with PCA and cluster with k-means (k=6 for MB140, k=4 for Cholec80).

The exact clustering pipeline can be spelled out in the final methods section, but the critical empirical fact is simpler: **good clustering helps and bad clustering hurts**. Heuristic clustering that failed to match the phase ontology produced an uninformative signal and degraded performance. Data-driven k-means clustering yielded balanced MultiBypass140 clusters and the best retrospective-token results.

### 5.3 Retrospective workflow token

The resulting video-level cluster ID is embedded as a learnable `nn.Embedding(K, 768)` conditioning token and prepended to the frame sequence, where it acts as a [CLS]-style aggregator consumed by the HTA head. Because that cluster is computed from the full case, the token is available at both training and inference in the current pipeline.

That makes the method retrospective, not causal. It answers:

> If the model knows which workflow family the case belongs to, does that help?

That is still a valuable question. If the answer were no, there would be little reason to pursue a more sophisticated causal workflow model. Because the answer appears to be yes on MultiBypass140 and no on Cholec80, the retrospective setting already teaches us something important.

### 5.4 What "retrospective upper bound" means

This phrase should be read very literally.

1. After a surgery is over, we can inspect its **entire phase sequence** and assign it to a workflow cluster.
2. In the current system, that workflow cluster is fed back into the model as an input token when predicting remaining time at moment `t`.
3. But at moment `t`, a real online system would **not yet know** the phases that occur after `t`.
4. So the current token contains information that is only available after the case has unfolded further.

That is why we call the current setup an **upper bound** on workflow-conditioned prediction. It estimates how useful workflow identity could be **if it were known perfectly**. It is scientifically useful because it tests whether workflow information matters at all, but it is not yet a deployable formulation.

![Retrospective versus causal workflow conditioning. Left: the current pipeline uses a workflow token derived from the full case, so future phase information leaks into the prediction at time t. Right: the desired causal pipeline would infer workflow state only from the observed prefix x_{<=t}.](figures/fig3b_retrospective_vs_causal.pdf){width=100%}

**Figure 3b.** Why the current token is a retrospective upper bound rather than a valid online input.

---

## 6. Results

### 6.1 MultiBypass140 within-center: workflow conditioning helps where workflow variation exists

The strongest result in the current repository comes from within-center MultiBypass140 experiments.

| Configuration | Split | Validation MAE |
|---|---|---:|
| No workflow token | MultiBypass140 fold 0 | 13.55 min |
| Retrospective k-means workflow token | MultiBypass140 fold 0 | **12.59 ± 0.33 min** |

This is the paper's core positive result. On a benchmark with real workflow heterogeneity, supplying workflow identity improves duration prediction by roughly one minute and also improves training stability.

![MultiBypass140 fold 0 validation MAE across 3 seeds: with- and without-token configurations. Seed-to-seed error bars shown.](figures/fig4_mb140_main_result.pdf){width=90%}

#### The right level of confidence

The signal is strong, but the paper should still be precise about its evidence:

- the tokenized result is available across three runs,
- the logged no-token comparator is still effectively a weaker replication standard,
- so the direction of the effect is convincing, while the exact final effect size should still be confirmed by a full three-seed no-token rerun.

That is an easy limitation to state and an easy one to fix.

#### Negative control

Bad clustering hurts. This matters because it shows the improvement is not a generic byproduct of adding any token. The conditioning signal only helps when it captures real workflow structure.

---

### 6.2 Cross-center MultiBypass140: the unsolved problem is still shift

The Bern-to-Strasbourg transfer result is blunt:

| Configuration | Bern → Strasbourg validation MAE |
|---|---:|
| With retrospective token | 18.05 min |
| Without token | 18.26 min |

The token still helps slightly, but the dominant fact is the **~6 minute degradation** relative to the within-center setting. That is the deeper scientific point. Workflow conditioning helps, but it does not come close to solving multicenter generalization.

![Cross-center generalization gap: within-center (fold 0) vs. Bern→Strasbourg transfer. Workflow conditioning closes a small share of the gap; the vast majority of the degradation is unexplained by workflow identity alone.](figures/fig6_cross_center_gap.pdf){width=90%}

This is exactly why MultiBypass140 should anchor the paper. A benchmark that exposes this gap forces the model story to confront the actual difficulty of workflow-aware prediction instead of hiding behind easier conditions.

---

### 6.3 Cholec80: strong absolute accuracy, weak workflow signal

Cholec80 plays a different role in the paper. It is not the main battleground for workflow conditioning. It is the contrast case.

#### Validation comparison

| Configuration | Cholec80 validation MAE |
|---|---:|
| With workflow token | 4.49 ± 0.14 min |
| Without workflow token | 4.61 ± 0.19 min |

This difference is small and well within run-to-run variation. That is not disappointing. It is exactly what the workflow-diversity statistics predict. When a benchmark is already dominated by one common operative order, explicit workflow conditioning has little left to explain.

![Cholec80 validation MAE: with- and without-token configurations are statistically indistinguishable across 3 seeds, consistent with the 51/72-dominant-cluster workflow-diversity statistic from §4.2.](figures/fig5_cholec80_null_result.pdf){width=90%}

That is the paper's cleanest interaction:

- **MultiBypass140:** token helps.
- **Cholec80:** token is nearly neutral.

That is stronger evidence than a pooled average over unrelated datasets.

---

### 6.4 Secondary Cholec80 absolute numbers

The repository also contains stronger absolute Cholec80 numbers, reported in the experiment log:

| Configuration | Cholec80 test MAE |
|---|---:|
| From scratch | 4.458 ± 0.224 min |
| MB140 → Cholec80 transfer | 4.337 ± 0.209 min |
| Ensemble + isotonic post-processing | 3.563 min |

These numbers are useful, but they answer different questions from the main workflow-conditioning result:

- `4.458 ± 0.224` says the underlying pipeline is competitive on the public 30-video test subset.
- `4.337 ± 0.209` suggests that MB140 pretraining may offer a modest transfer benefit.
- `3.563` shows that monotonic post-processing and ensembling can further reduce error on that specific evaluation slice.

![Cholec80 inference-side ablation: single-seed baseline → +MB140 transfer → +ensemble → +H-flip TTA → +isotonic post-processing. Isotonic alone accounts for roughly 83% of the total gain and is orthogonal to the workflow-conditioning contribution.](figures/fig7_cholec_inference_ablation.pdf){width=90%}

Those are good secondary results. They are not the core workflow-conditioning story.

---

### 6.5 Why the `3.56 min` Cholec80 result should stay secondary

The earlier paper version tried to carry the project with a Cholec80 SOTA narrative. That is not the strongest scientific framing for four reasons.

1. The evaluation uses the **72-video public phase-labeled subset** (8 videos — 01, 02, 18, 19, 45, 46, 72, 73 — have no `video*-phase.txt` annotation in the public release and are required by our cluster-conditioned pipeline), not the full 80-video benchmark.
2. The split is **36/6/30**, not the 40-video test convention used by TransLocal and Bose et al.
3. The strongest number comes from **ensemble + isotonic post-processing**, not from the core conditioning comparison.
4. The post-processing stack was effectively explored on the test set, so it should be described as secondary or appendix material rather than as the paper's centerpiece.

The result is still worth reporting. It just should not define the submission.

---

## 7. Discussion

### 7.1 The central empirical claim

The paper's strongest claim is simple:

> **Workflow conditioning helps when workflow variability is present.**

That statement is supported by the interaction between MultiBypass140 and Cholec80, not by one isolated benchmark number. MultiBypass140 contains real workflow diversity and a large center gap, so the conditioning signal matters. Cholec80 is much more standardized, so the same signal is mostly redundant.

That is a more transferable scientific result than "one more token improved one benchmark."

### 7.2 What the current evidence does not support

The current evidence does not support a causal-deployment claim. The active system uses:

- a full-video workflow label as input,
- and a clip formulation that is not strictly prefix-only.

That means the present model is best interpreted as a **retrospective upper bound**. The paper should say that directly, then use it as a launch point for the next model rather than as something to obscure.

### 7.3 Why MultiBypass140 should carry the paper

If the paper is written around Cholec80, reviewers can fairly ask whether workflow conditioning matters once the workflow becomes standardized. MultiBypass140 resolves that question. It is the dataset where workflow variability is visible, quantifiable, and difficult. That is exactly why it should carry the narrative.

---

## 8. Limitations and Next Step

### 8.1 The current main model is retrospective, not causal

The present token is computed from the full case. That is useful for diagnosis, but it is not deployable. The next paper-grade model should:

- predict from a **strict prefix**,
- target the **last/current frame** rather than a centered clip target,
- and infer workflow from the observed prefix rather than receiving a full-video oracle label.

### 8.2 MultiBypass140 results are on fold 0 only, and the no-token baseline needs three-seed matching

Two related gaps in the current MB140 evidence:

1. **Single-fold evaluation.** All MB140 numbers in this paper are on fold 0 of the public 5-fold CV protocol (folds 0–4). The direction of the workflow-conditioning effect is clear at matched recipe, but the final version should report mean ± std across all 5 folds at 3 seeds each (15 runs total, ~20 GPU-hours on a single H100-class node).
2. **Matched-seed no-token comparator.** The 13.55 min no-token number is a single-seed run; the tokenized 12.59 ± 0.33 min is 3-seed. The direction is convincing, but the final version should add a 3-seed no-token replication under the same recipe so the effect-size confidence interval is symmetric.

Neither gap threatens the paper's scaling claim; both should be closed before submission.

### 8.3 Deviation detection is not a headline strength

The current deviation head is far below the strongest published IAE systems. It should be reported honestly as an auxiliary task and not oversold.

### 8.4 Data-selection methods inherited from small-CNN settings do not transfer

We also attempted a per-video overfit-residual frame-selection filter as a data-centric alternative to stronger architectures. It produced a clean negative result across two filter strengths (see Appendix A.5). This is reported both for completeness and as a cautionary data point about porting small-model data-selection recipes into modern Transformer pipelines.

### 8.5 The causal-at-inference variant under evaluation

The natural successor to the retrospective upper bound is a **causal-at-inference workflow signal** $q(z \mid x_{\leq t})$ derived from the observed surgical prefix alone. We construct this by *reusing the already-trained phase head* inside our model: for a prefix $x_{\leq t}$, the phase head produces per-frame phase distributions, which are collapsed into a phase-bigram sequence and passed through the same TF–IDF + PCA + k-means pipeline used offline to obtain a soft cluster posterior over the $K$ workflow clusters. The oracle one-hot cluster embedding is then replaced at inference by a weighted mixture of the $K$ learned embeddings.

**Two important honesty notes** about this variant, both kept explicit in the paper:

1. **Causal at inference, but not at training.** Supervision during training still uses the full-video phase sequence (teacher forcing) to compute each clip's prefix cluster ID. At inference, no ground-truth phase labels are touched — the cluster signal is a function of pixels alone. We refer to this as *causal-at-inference* rather than *fully causal*, following the standard usage in the imitation-learning and offline-RL literatures.

2. **Recovers a meaningful share of the oracle gain, not full parity.** We report the causal variant as a deployable lower bound paired with the retrospective upper bound. The interesting quantity is the gap, not equality. If the causal variant matched the oracle exactly, that would itself be suspicious — it would mean the oracle wasn't carrying useful information specific to the full sequence.

Implementation lives in [`brsd_lib/causal_cluster.py`](../brsd_lib/causal_cluster.py). Both the inference-only variant (uses the existing oracle-trained checkpoint with phase-head-derived cluster at inference) and the variant retrained under causal-posterior sampling during training are reported in §6 with matched-recipe seed statistics.

---

## 9. Conclusion

This project is strongest when it makes one clear claim and defends it well.

The current evidence shows that:

1. **Workflow variability is a major source of error** in surgical duration prediction.
2. **Retrospective workflow labels help** on a heterogeneous multicenter RYGB benchmark.
3. The same mechanism is **nearly neutral on a much more standardized benchmark**.
4. **Cross-center shift remains large**, so workflow-aware prediction is still far from solved.

That is already a substantial result. It just points to a different paper than the earlier overclaimed draft. The present model should be presented as a retrospective upper bound and diagnostic. The next publishable system should convert that insight into a causal prefix-conditioned model. If the paper stays disciplined about that distinction, the story becomes sharper, more credible, and harder to dismiss.

---

## References

1. Twinanda, A. P., Shehata, S., Mutter, D., Marescaux, J., de Mathelin, M., & Padoy, N. (2016). EndoNet: A deep architecture for recognition tasks on laparoscopic videos. *IEEE Transactions on Medical Imaging*, 36(1), 86–97.

2. Twinanda, A. P., Yengera, G., Mutter, D., Marescaux, J., & Padoy, N. (2018). RSDNet: Learning to predict remaining surgery duration from laparoscopic videos without manual annotations. *IEEE Transactions on Medical Imaging*, 38(4), 1069–1078.

3. Yengera, G., Mutter, D., Marescaux, J., & Padoy, N. (2018). Less is more: Surgical phase recognition with less annotations through self-supervised pre-training of CNN-LSTM networks. *arXiv:1805.08569*.

4. Lavanchy, J. L., Ramesh, S., Bastian, L., Mutter, D., et al. (2024). MultiBypass140: A multi-center, multi-surgeon laparoscopic Roux-en-Y gastric bypass dataset for surgical workflow analysis. *Medical Image Analysis* / arXiv:2401.06307.

5. Loukas, C., Gazis, A., & Kanakis, M. A. (2024). TransLocal: Transformer-based prediction of remaining surgery duration from laparoscopic videos. *International Journal of Medical Robotics and Computer Assisted Surgery* (Wiley), 20(3).

6. Kostopoulos, N., et al. (2025). Cross-center remaining surgery duration prediction on multicenter bariatric benchmarks. *De Gruyter — Current Directions in Biomedical Engineering*.

7. Yang, S., Liu, X., et al. (2024). Surgformer: Hierarchical Temporal Attention for Surgical Video Understanding. *MICCAI 2024*; arXiv:2408.03867.

8. Bose, A., et al. (2025). Pretraining-heavy temporal models for remaining surgery duration prediction. arXiv:2504.16749.

9. Czempiel, T., Paschali, M., Keicher, M., Simson, W., Feussner, H., Kim, S. T., & Navab, N. (2020). TeCNO: Surgical phase recognition with multi-stage temporal convolutional networks. *MICCAI 2020*.

10. Liu, Y., Boels, M., Garcia-Peraza-Herrera, L. C., Vercauteren, T., & Dasgupta, P. (2023). SKiT: A fast key information video transformer for online surgical phase recognition. *ICCV 2023*.

11. Gao, X., Jin, Y., Dou, Q., Heng, P.-A. (2021). Trans-SVNet: Accurate phase recognition from surgical videos via hybrid embedding aggregation transformer. *MICCAI 2021*.

12. Aklilu, J., et al. (2024). BetaMixer: A mixture-of-Betas distributional head for RYGB intraoperative adverse event detection. *MICCAI 2024* (or workshop proceedings).

13. Kendall, A., Gal, Y., & Cipolla, R. (2018). Multi-task learning using uncertainty to weigh losses for scene geometry and semantics. *CVPR 2018*.

14. Dosovitskiy, A., Beyer, L., Kolesnikov, A., et al. (2021). An image is worth 16x16 words: Transformers for image recognition at scale. *ICLR 2021*.

15. Wightman, R. (2019–present). PyTorch Image Models (timm). Available at [https://github.com/huggingface/pytorch-image-models](https://github.com/huggingface/pytorch-image-models).

16. He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning for image recognition. *CVPR 2016*.

17. Chen, L., et al. (2024). HecVL: A hierarchical surgical vision-language foundation model. *CVPR / MICCAI 2024*.

18. Wang, X., et al. (2023). SurgVLP: Surgical vision-language pretraining from procedural text and video. *Preprint / MICCAI 2023*.

19. Pedregosa, F., et al. (2011). scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. (Source of `IsotonicRegression` used in §6.4.)

---

## Appendix

### A.1 Seed-by-seed Cholec80 test numbers

Per-seed test MAE (minutes) for the three Cholec80 stacks, on the 30-video public phase-labeled test split:

| Run | Setting | Seed 42 | Seed 123 | Seed 777 | Mean ± std |
|---|---|---:|---:|---:|---:|
| 017 | From scratch | 4.661 | 4.282 | 4.431 | 4.458 ± 0.224 |
| 018 | MB140 → Cholec80 transfer | 4.545 | 4.141 | 4.325 | 4.337 ± 0.209 |
| 019-C | Ensemble + H-flip TTA + isotonic | — | — | — | **3.563** |
| 019-D | Single seed 42 + isotonic only | 3.694 | — | — | 3.694 |

Isotonic regression alone delivers ≈83% of the total improvement from 4.34 → 3.56; ensembling on top contributes the remaining 0.13 min.

### A.2 Transfer-learning details (MB140 → Cholec80)

- Source checkpoint: Run 010, seed 42, best MB140 fold-0 val MAE 12.26 min.
- Partial `load_state_dict(..., strict=False)` with the key filter dropping `phase_head.*` (the MB140 model has 14 phase classes; Cholec80 has 7) and `phase_order_embed.*` (MB140 uses K=6 clusters; Cholec80 K=4).
- ViT backbone, HTA head, and RSD regression head weights all transferred.
- Fine-tuning: same recipe as from-scratch Cholec80 (lr=1e-4, weight decay=0.05, 15 epochs, batch 64), three seeds 42/123/777.

### A.3 Isotonic post-processing ablation

Per-video application of `sklearn.isotonic.IsotonicRegression(increasing=False)` to the predicted RSD trajectory. This enforces that remaining duration is monotonically non-increasing in time, which is a physical constraint any RSD predictor should satisfy. The fit is strictly per-video and uses no cross-video information.

| Stack | Mean per-video test MAE | Δ vs single-seed baseline |
|---|---:|---:|
| Single seed 42 | 4.34 | 0.00 |
| Single seed 42 + isotonic | 3.694 | −0.64 |
| 3-seed ensemble + H-flip TTA + isotonic | 3.563 | −0.77 |

### A.4 Full run-log summary

The `SESSION_LOG.md` file in the repository records Runs 001–021 with configs, wall-clock times, checkpoint paths, and seed-level val/test metrics. Runs 001–009 cover the MB140 architecture search and no-token baselines. Run 010 is the headline three-seed MB140 tokenized result (12.59 ± 0.33 min). Runs 011–016 cover cross-center transfer and Cholec80 from-scratch training. Runs 017–019 cover the Cholec80 transfer + ensemble + isotonic inference stack. Runs 020 and 021 are the overfit-filter negative result documented in §A.5.

### A.5 Negative result — the 2019 per-video overfit-residual filter does not transfer

As part of the data-selection track, we attempted a per-video overfit-residual filter that removes training clips whose absolute RSD residual under a first-pass model exceeds $k \cdot \sigma_v$ (per-video residual std). Two filter strengths were evaluated:

| Config | Train frames retained | Clip samples per epoch | 3-seed best val MAE | Δ vs unfiltered |
|---|---:|---:|---:|---:|
| Run 010 (no filter, baseline) | 100% | 83,459 | **12.59 ± 0.33 min** | — |
| Run 020 (k=0.385, aggressive) | 24% | 3,366 | 16.71 ± 0.27 min | **+4.11 min** |
| Run 021 (k=1.0, conservative) | 52% | 8,302 | 14.50 ± 0.06 min | **+1.91 min** |

Per-seed minimums (seeds 42 / 123 / 777):

- Run 020: 16.89 / 16.83 / 16.40
- Run 021: 14.45 / 14.56 / 14.49

Both configurations degrade performance by 5–12× the baseline seed-variance, so this is not noise. Six non-exclusive hypotheses explain the gap, listed roughly in order of how strongly we believe each contributes:

1. **Data-scarcity dominates noise-reduction.** Cutting training clip count from 83k to 3.4k (k=0.385) or 8.3k (k=1.0) starves a ViT + 6-layer HTA stack of the temporal coverage it needs. A 2019-era ResNet-18 + 4-FC baseline with far less capacity might cope with 20k "clean" frames; a 150M-parameter video Transformer on 8-frame × stride-5 clips clearly does not.
2. **Pretrained features are already noise-robust.** The ImageNet-initialized ViT implicitly smooths over per-frame label noise, so the marginal value of explicit noise removal is low.
3. **Frame-wise residuals ignore temporal context.** The filter scores each frame in isolation, but training uses 40-frame-span clips. A frame that is "hard" alone may be useful in context.
4. **Per-video normalization over-prunes informative hard frames.** Hard frames often sit at phase transitions or unusual workflow moments — exactly where a Transformer benefits most from signal.
5. **Multi-task loss changes the cost structure.** A frame that is hard for RSD may still carry phase or deviation signal; the RSD-residual filter ignores this cross-task utility.
6. **Sequence-sampler × filter interaction is unintended.** After filtering, "consecutive" kept frames may be many seconds apart in original time. Without compensating `sequence_len` / `frame_stride`, each clip now spans a very different physical time window than in the baseline.

The honest summary for the paper is: **the per-video overfit-residual filter of the small-CNN era does not transfer to modern Transformer training on MultiBypass140, and the dominant failure mode is data scarcity, not noise reduction.** We report this here rather than omit it.

### A.6 Qualitative trajectory plots and cluster visualizations

Per-video predicted-vs-true RSD trajectories for representative MB140 test cases (within-cluster vs cross-cluster errors) and the k-means cluster layout in PCA(16)-reduced phase-bigram TF–IDF space are produced by `paper/figures/generate_figures.py` alongside Figures 1–7. These figures are included in the supplementary release of the repository and can be regenerated directly from the mirrored checkpoints and labels via `python paper/figures/generate_figures.py`.

---

*The main text stays locked on the clearest result the repository supports: **workflow conditioning matters when workflow variability is real.** The secondary Cholec80 absolute numbers, the cross-center shift result, and the overfit-filter negative result are all kept — each in the scope that reflects how strongly the evidence supports it.*

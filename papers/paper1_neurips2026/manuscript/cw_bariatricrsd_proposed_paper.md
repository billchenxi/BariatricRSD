# Causal Workflow-Conditioned Prediction of Remaining Duration in Roux-en-Y Gastric Bypass Surgery

Bill Chen

Xi Lab

## Abstract

Accurate prediction of remaining surgery duration (RSD) can improve operating room coordination, staffing, anesthesia planning, and intraoperative decision support. In laparoscopic Roux-en-Y gastric bypass (RYGB), however, duration prediction is difficult because visually similar operative states can belong to different workflow styles, centers, and phase-order patterns. Existing surgical video models typically represent workflow progress from visual features and temporal context, but they do not explicitly model uncertainty over the evolving operative style from the observed prefix of the case.

We propose **Causal Workflow-Conditioned BariatricRSD (CW-BariatricRSD)**, a temporal surgical video model that predicts RSD from only the information available up to the prediction time, while using surgical phase and deviation labels as auxiliary supervision. The key idea is to infer a posterior distribution over latent workflow styles from the observed surgical prefix and use this posterior as a soft conditioning signal for a causal temporal encoder. Unlike an oracle phase-order token computed from the full video, the proposed workflow posterior is estimated online from prefix frames, elapsed time, and optional non-future metadata. This design makes the model suitable for deployment and creates a clear experimental distinction between causal workflow inference and non-deployable oracle workflow conditioning.

We ground the study in MultiBypass140, a multicenter RYGB dataset with 140 videos from Bern and Strasbourg. The local fold-0 manifest contains 770,701 frame-level samples, balanced centers (70 Bern, 70 Strasbourg), and substantial center-dependent duration variation: median duration is 72.8 minutes for Bern and 112.6 minutes for Strasbourg. Preliminary non-causal pilot experiments motivate workflow conditioning for RSD: a k-means phase-order token run reaches 12.27 minutes validation MAE compared with 13.55 minutes for a 15-epoch no-token run. However, the same pilot logs do not show a deviation-detection benefit, and cross-center gains are small. We therefore treat these results as motivation only and define the main contribution as a leakage-safe causal workflow-conditioning study with paired ablations, cross-center evaluation, and uncertainty calibration.

## 1. Introduction

Operating rooms are high-cost, high-variance clinical environments. Even small errors in predicted case duration can affect patient flow, staff allocation, anesthesia planning, and downstream scheduling. Remaining surgery duration prediction has therefore become an important task in computer-assisted intervention. Video-based methods are especially attractive because laparoscopic video directly captures the operative state and is already available in most minimally invasive procedures.

RYGB is a strong test case for duration prediction because its workflow is structured but not rigid. Surgeons can complete the same major operative goals in different orders, and hospitals may differ in phase definitions, case mix, technical style, and average duration. In the local MultiBypass140 manifest used in this project, Strasbourg videos are substantially longer than Bern videos despite the same broad procedure category. This creates a modeling problem: a frame that visually resembles an anastomosis may imply different remaining time depending on the workflow style and what has already occurred.

Prior surgical video models generally address temporal prediction by adding recurrent networks, temporal convolution, or Transformers over visual features. These methods can model temporal context, but they often treat all cases as samples from one shared workflow. A direct phase-order token computed from the full surgery can help in offline experiments, but it is not deployable if it depends on future phases. At minute 20 of a surgery, the final phase order is not known.

This paper proposes a causal alternative: infer a belief over workflow style from the observed prefix only, then condition RSD and deviation prediction on that belief. The model does not need to know the final phase sequence. Instead, it maintains a posterior distribution over latent workflow styles that can be uncertain early in the operation and sharpen as more evidence arrives.

Our central hypothesis is:

> Workflow-variable RSD prediction improves when the model estimates and uses a causal posterior over operative workflow style from the observed prefix.

This hypothesis is clinically meaningful and experimentally testable. It predicts the largest benefit in early and mid-case prediction, under cross-center shift, and in cases whose phase order diverges from the dominant workflow.

## 2. Contributions

This proposed paper makes four contributions.

1. We formulate RSD prediction in RYGB as a **causal workflow-conditioned prediction** problem, where the model must predict from information available only up to the current time.

2. We introduce **CW-BariatricRSD**, a multi-task temporal video architecture that infers a prefix workflow posterior `q(z | x_{<=t})` and uses the expected workflow embedding as a soft conditioning token for RSD prediction, with phase and deviation as auxiliary outputs.

3. We define a leakage-safe experimental protocol separating deployable prefix-conditioned inference from non-deployable oracle phase-order conditioning.

4. We provide an evaluation plan for multicenter RYGB videos that reports RSD accuracy, calibration, cross-center generalization, phase metrics, and event-level deviation metrics without overstating preliminary deviation results.

## 3. Related Work

### Remaining Surgery Duration Prediction

RSD prediction has been studied using workflow features, laparoscopic video, recurrent networks, and temporal models. RSDNet showed that remaining duration can be learned from laparoscopic videos without manual annotations, establishing the task as a video-based prediction problem. More recent methods use attention and Transformer-style temporal representations, including visual saliency and temporal attention for laparoscopic RSD prediction.

These methods motivate the visual-temporal backbone of CW-BariatricRSD, but they do not explicitly model uncertainty over workflow style as a causal latent state.

### Surgical Workflow Recognition

Surgical phase recognition has a long history in computer-assisted intervention. EndoNet introduced deep recognition of phases and tools from laparoscopic video and helped establish Cholec80 as a benchmark dataset. TeCNO showed the value of temporal convolution for online surgical phase recognition. SKiT and later Transformer-based methods improved online surgical workflow modeling with efficient temporal attention. Surgformer introduced hierarchical temporal attention for surgical phase recognition.

CW-BariatricRSD borrows the idea that temporal context matters, but uses phase recognition as an auxiliary task and as a source of prefix workflow evidence for RSD and deviation prediction.

### Multicenter RYGB Workflow Modeling

MultiBypass140 provides multicenter RYGB videos from Bern and Strasbourg with phase and step annotations. The associated generalization work highlights center shift and workflow variation in RYGB, making it a natural dataset for testing workflow-conditioned prediction. Recent work on IAE detection in RYGB, including BetaMixer, further shows that adverse event detection is clinically relevant but strongly imbalanced.

CW-BariatricRSD is designed for exactly this setting: structured surgical workflows, center-dependent variation, and rare adverse events.

### Surgical Foundation Models

Surgical video pretraining and foundation models are rapidly developing. HecVL explores hierarchical video-language pretraining for surgical phase recognition. SurgBench and UniSurg/SurgMotion-style surgical video-native foundation models show increasing interest in broad surgical video understanding. CW-BariatricRSD is complementary to these models: the proposed workflow posterior can be built on top of ImageNet, HecVL, or future surgical video foundation encoders.

## 4. Dataset and Local Statistics

We use the local MultiBypass140 fold-0 k-means manifest mirrored in this repository:

`lambda_mirror/labels/mb140_fold0_labels_kmeans.json`

The manifest contains:

| Property | Value |
|---|---:|
| Videos | 140 |
| Centers | 70 Bern, 70 Strasbourg |
| Frame-level samples | 770,701 |
| Splits | 80 train, 20 validation, 40 test |
| Median duration | 83.06 min |
| Mean duration | 92.10 min |
| Min / max duration | 37.42 / 178.42 min |
| Deviation frames | 70,366 |
| Deviation frame rate | 9.13% |
| Phase-order clusters | 6 k-means clusters |

Duration differs strongly by center:

| Center | Videos | Median duration | Mean duration | Min | Max |
|---|---:|---:|---:|---:|---:|
| Bern | 70 | 72.81 min | 73.52 min | 37.42 | 144.55 |
| Strasbourg | 70 | 112.63 min | 110.67 min | 40.77 | 178.42 |

This center effect motivates workflow-conditioned prediction. A model that only learns visual appearance may confuse workflow state with center-dependent duration priors. A model that learns a causal workflow posterior can represent both visible progress and uncertainty about the operative style.

## 5. Problem Formulation

For a surgery video with total duration `D`, at prediction time `t`, the goal is to predict:

`RSD_t = D - t`

from only the observed prefix:

`X_{<=t} = {x_1, x_2, ..., x_t}`

The model must not use future frames, future phase labels, or any cluster derived from the complete phase sequence as a deployable input.

We jointly predict:

- remaining duration distribution `p(RSD_t | X_{<=t})`
- current phase `p(y_t^phase | X_{<=t})`
- current or near-term deviation risk `p(y_t^dev | X_{<=t})` as an auxiliary output
- workflow posterior `q(z_t | X_{<=t})`, where `z` indexes latent workflow style/order

The workflow posterior is not assumed to be known. It is inferred from the observed prefix.

## 6. Method

### 6.1 Overview

CW-BariatricRSD has four modules:

1. **Visual encoder**: extracts per-frame surgical visual features.
2. **Causal temporal encoder**: summarizes observed prefix features up to time `t`.
3. **Workflow posterior network**: estimates a distribution over latent workflow styles from prefix evidence.
4. **Multi-task heads**: predict RSD distribution, phase label, deviation probability, and optionally progress.

### 6.2 Visual Encoder

Each sampled frame is resized to 224 x 224 and encoded using a ViT or surgical video foundation encoder. In the current pilot code, the Lambda-trained model uses `vit_base_patch16_224` from `timm`, optionally initialized from ImageNet or a surgical checkpoint. Early ViT blocks may be frozen for compute efficiency.

Let:

`h_i = f_visual(x_i)`

where `h_i` is the visual embedding for frame `i`.

### 6.3 Causal Temporal Encoder

The temporal encoder receives only frames up to the target time. This can be implemented as:

- a causal Transformer with attention mask,
- a masked hierarchical temporal attention module,
- or a prefix window ending at time `t`, pooled from the last token.

The temporal state is:

`u_t = f_temporal(h_1, ..., h_t)`

For a fixed-length training clip, the target should be the last/current frame in the clip, not a middle frame surrounded by future context.

### 6.4 Workflow Posterior Network

The workflow posterior network estimates:

`q_t = q(z | X_{<=t})`

where `z` is a latent workflow style. Prefix features may include:

- temporal visual state `u_t`
- predicted phase histogram over the prefix
- predicted phase transition counts over the prefix
- elapsed time
- center or surgeon metadata if known before or during the case

If final workflow clusters are available offline, they can supervise the posterior during training:

`L_workflow = CE(q_t, z_final)`

This is acceptable because `z_final` is a label, not an input. At inference, `q_t` is computed from prefix evidence only.

### 6.5 Soft Workflow Conditioning

Each workflow style has a learnable embedding `E_k`. Rather than selecting a hard cluster, the model uses the posterior expectation:

`s_t = sum_k q_t[k] E_k`

This soft token is more appropriate than a hard cluster early in the procedure because workflow identity may be uncertain.

The style token is fused with the temporal state:

`g_t = Fuse(u_t, s_t)`

Possible fusion functions include:

- attention over `[s_t, u_t]`
- gated residual addition
- feature-wise linear modulation (FiLM)
- concatenation followed by an MLP

### 6.6 RSD Distribution Head

Instead of predicting only a normalized scalar, the proposed model predicts a distribution over remaining minutes. A simple choice is a Gaussian head:

`mu_t, log_sigma_t = f_RSD(g_t)`

trained with negative log likelihood:

`L_RSD = 0.5 * ((r_t - mu_t) / sigma_t)^2 + log_sigma_t`

Alternatively, quantile regression can predict 10%, 50%, and 90% remaining-duration quantiles. This enables clinically useful uncertainty intervals.

### 6.7 Deviation and Phase Heads

The deviation head predicts current IAE/deviation risk:

`p_dev_t = sigmoid(f_dev(g_t))`

Because deviations are rare, training should use class-balanced BCE or focal loss. Evaluation should include PR-AUC and event-level detection, not only frame-level F1.

The phase head predicts the current phase:

`p_phase_t = softmax(f_phase(g_t))`

Phase prediction is both an auxiliary task and a source of workflow-state evidence.

### 6.8 Training Objective

The total loss is:

`L = L_RSD + lambda_phase L_phase + lambda_dev L_dev + lambda_workflow L_workflow + lambda_cal L_cal`

where:

- `L_RSD`: Gaussian NLL, log-normal NLL, or quantile loss
- `L_phase`: cross-entropy for current phase
- `L_dev`: focal loss or class-balanced BCE
- `L_workflow`: cross-entropy/KL for prefix workflow posterior supervision
- `L_cal`: optional calibration penalty for interval coverage

The uncertainty-weighted multi-task loss used in pilot experiments can remain as an ablation, but the main paper should focus on predictive accuracy and calibration rather than the sign of the training loss.

## 7. Experimental Design

### 7.1 Primary Experiments

The main experiments should be paired and leakage-safe. Each method should use the same encoder, folds, seeds, and training budget.

| ID | Model | Description | Purpose |
|---|---|---|---|
| B0 | Duration prior | Uses elapsed time, center, and training duration statistics only | Non-visual baseline |
| B1 | Causal ViT + temporal encoder | Visual-temporal model without workflow conditioning | Core baseline |
| B2 | B1 + phase auxiliary head | Adds current phase supervision | Tests multi-task phase benefit |
| B3 | B2 + known metadata | Adds only preoperatively known metadata | Separates metadata from inferred workflow |
| M1 | CW-BariatricRSD | Prefix workflow posterior soft token | Main method |
| M2 | Oracle phase-order token | Full-video cluster direct input | Non-deployable upper bound |
| M3 | Shuffled workflow token | Randomized workflow conditioning | Sanity check |

### 7.2 Cross-Center Generalization

The key generalization experiments are:

1. train Bern, test Strasbourg
2. train Strasbourg, test Bern
3. train mixed-center fold, test held-out videos

The hypothesis is that workflow conditioning should improve cross-center RSD and calibration because it explicitly models workflow variation rather than relying on one center's average duration.

### 7.3 Evaluation Metrics

RSD:

- MAE in minutes
- median absolute error
- MAE by elapsed quartile: 0-25%, 25-50%, 50-75%, 75-100%
- calibration of prediction intervals
- cross-center MAE

Deviation:

- PR-AUC
- frame-level F1
- event-level recall with temporal tolerance
- false alarms per hour
- per-phase recall

Phase:

- accuracy
- balanced accuracy
- macro F1

Workflow posterior:

- prefix cluster accuracy over time
- entropy over time
- relation between posterior confidence and RSD error

### 7.4 Statistical Analysis

All primary comparisons should be paired at the video level. Frame-level predictions are useful for training and temporal analysis, but confidence intervals should be computed by resampling videos, not individual frames, because adjacent frames from the same surgery are highly correlated.

For each main model comparison, report:

- mean and median per-video RSD MAE
- 95% bootstrap confidence intervals over videos
- paired bootstrap or Wilcoxon signed-rank test for the MAE difference
- mean +/- standard deviation across at least three random seeds
- per-center results and cross-center deltas

For deviation detection, report frame-level metrics as secondary and event-level metrics as primary. A clinically useful detector should reduce missed events without producing an unusable false alarm rate.

For workflow conditioning, include two sanity checks: an oracle full-video workflow token as a non-deployable upper bound, and a shuffled workflow token as a negative control. The main claim is supported only if the causal prefix posterior improves RSD over the matched causal baseline and approaches the oracle upper bound without using future information.

## 8. Preliminary Pilot Results From the Current Logs

The current local runs are non-causal pilot experiments and should not be presented as final evidence for the deployable method. They are useful for motivating the causal workflow-conditioning study and for identifying what the final experiments must fix.

Parsed Lambda logs show:

| Run | Description | Epochs logged | Best validation MAE | Best deviation F1 | Notes |
|---|---|---:|---:|---:|---|
| run001 | multitask, heuristic clusters | 14 | 13.20 min | 0.364 | early pilot |
| run002 | regularized multitask | 6 | 14.58 min | 0.411 | reduced trainable params; weaker RSD |
| run003 | lower LR / higher WD | 6 | 13.29 min | 0.415 | better deviation F1 |
| run004 | RSD-only | 3 | 13.60 min | 0.169 | deviation head not trained usefully |
| run005 | no phase-order, older setup | 8 | 12.51 min | 0.353 | not cleanly paired |
| run006 | k-means phase-order token | 15 | 12.27 min | 0.369 | best pilot RSD MAE |
| run007 | no phase-order, 15 epochs | 15 | 13.55 min | 0.426 | better F1 but worse RSD |
| run008 | Bern train -> Strasbourg validation, token | 15 | 18.05 min | 0.395 | cross-center gap remains large |
| run009 | Bern train -> Strasbourg validation, no token | 15 | 18.26 min | 0.406 | token gain is small for RSD and not helpful for F1 |
| run010 | fold-0 seed 42 | 0 validation epochs | N/A | N/A | incomplete log; stopped before validation |

These results suggest:

1. Workflow conditioning may help RSD in within-fold pilot experiments.
2. Deviation detection is not improved by the current phase-order token; `run007` and `run009` have stronger F1 than their token counterparts.
3. Cross-center generalization remains difficult. The token improves Bern-to-Strasbourg MAE only slightly in the current logs: 18.05 min versus 18.26 min.
4. The final paper needs paired causal ablations, not only pilot log comparisons.

The pilot conclusion is therefore narrow:

> Phase-order conditioning is promising for RSD, but the deployable paper claim should be tested with causal workflow posterior conditioning, not direct full-video phase-order tokens.

## 9. Expected Results Tables

The final manuscript should include these tables.

### Table 1: Dataset Characteristics

Report videos, frames, durations, phases, deviations, and clusters by center.

### Table 2: Main RSD Results

| Model | MAE | Median AE | Early MAE | Mid MAE | Late MAE | Calibration error |
|---|---:|---:|---:|---:|---:|---:|
| B0 duration prior | TBD | TBD | TBD | TBD | TBD | TBD |
| B1 causal temporal | TBD | TBD | TBD | TBD | TBD | TBD |
| B2 + phase auxiliary | TBD | TBD | TBD | TBD | TBD | TBD |
| M1 CW-BariatricRSD | TBD | TBD | TBD | TBD | TBD | TBD |
| M2 oracle workflow | TBD | TBD | TBD | TBD | TBD | TBD |

### Table 3: Cross-Center Results

| Train center | Test center | Baseline MAE | CW-BariatricRSD MAE | Delta |
|---|---|---:|---:|---:|
| Bern | Strasbourg | TBD | TBD | TBD |
| Strasbourg | Bern | TBD | TBD | TBD |

### Table 4: Deviation Results

| Model | PR-AUC | F1 | Event recall | False alarms/hour |
|---|---:|---:|---:|---:|
| causal temporal | TBD | TBD | TBD | TBD |
| CW-BariatricRSD | TBD | TBD | TBD | TBD |
| BetaMixer-style baseline | TBD | TBD | TBD | TBD |

### Table 5: Workflow Posterior Over Time

| Elapsed quartile | Posterior entropy | Cluster accuracy | RSD MAE |
|---|---:|---:|---:|
| 0-25% | TBD | TBD | TBD |
| 25-50% | TBD | TBD | TBD |
| 50-75% | TBD | TBD | TBD |
| 75-100% | TBD | TBD | TBD |

### Recommended Figures

The final submission should include:

1. Dataset and duration variability: per-video RSD timelines and center-wise duration statistics from `notebooks/figures/rsd_all_videos_linear.png` and `notebooks/figures/phase_statistics.png`.
2. Method overview: old oracle-token setup versus CW-BariatricRSD causal posterior conditioning from `notebooks/method_figures/old_vs_publishable.png` and `notebooks/method_figures/cw_bariatricrsd_architecture.png`.
3. Workflow posterior dynamics: entropy and cluster-confidence curves over elapsed time from `notebooks/method_figures/workflow_posterior_over_time.png`.
4. Final performance: RSD error by elapsed quartile, calibration curve, and cross-center error bars once the paired experiments are complete.

## 10. Discussion

CW-BariatricRSD reframes RSD prediction as a problem of causal state estimation under workflow uncertainty. This is important because duration is not determined by visual appearance alone. In RYGB, different surgeons and centers may perform key steps in different orders, spend different time in specific phases, or introduce additional closure and inspection steps. A model that estimates workflow style from the prefix can adapt its remaining-duration estimate as evidence accumulates.

The most important methodological choice is separating deployable inference from oracle analysis. Full-video phase-order clusters are informative, but they are not available at prediction time. Treating them as an upper bound makes the analysis honest and still useful: if oracle conditioning helps substantially but causal posterior conditioning does not, then the problem is workflow inference. If causal posterior conditioning approaches the oracle, then the method has learned a useful online workflow representation.

The current logs also clarify the limits of the idea. Direct phase-order conditioning improves fold-0 RSD MAE in the strongest pilot comparison, but does not consistently improve deviation F1 and only marginally improves the current Bern-to-Strasbourg transfer run. This shifts the final paper away from a broad "phase-order token solves everything" narrative and toward a sharper RSD-centered claim: online workflow-state estimation may improve duration prediction under workflow variability.

The proposed distributional RSD head also improves clinical relevance. A single point estimate can be misleading when workflow state is uncertain. Prediction intervals can communicate uncertainty to clinicians and schedulers, and calibration can be evaluated directly.

## 11. Limitations

This proposed study has several limitations.

First, MultiBypass140 contains 140 videos, which is large for a specialized surgical dataset but still small for deep temporal modeling. Strong regularization, paired evaluation, and careful cross-validation are necessary.

Second, workflow clusters are abstractions. They may correlate with center, surgeon, annotation style, or procedure variant. The paper should analyze whether the learned posterior captures clinically meaningful workflow differences or simply center identity.

Third, deviation detection is highly imbalanced, and the current logs do not show that workflow conditioning improves it. Frame-level F1 may not reflect clinical usefulness. Event-level detection and false alarm rate are required.

Fourth, any model using center or surgeon metadata must distinguish between known-at-inference metadata and labels derived after the surgery.

Finally, this paper should avoid claiming that the operation log is a model contribution unless it is evaluated independently.

## 12. Conclusion

We proposed CW-BariatricRSD, a causal workflow-conditioned model for predicting remaining duration in laparoscopic RYGB videos, with phase and deviation labels used as auxiliary supervision. The key idea is to infer an online posterior over workflow style from the observed prefix and use it to condition temporal video prediction. This replaces non-deployable full-video phase-order conditioning with a leakage-safe mechanism that can be evaluated under within-center and cross-center settings. Pilot results motivate the approach for RSD, but the central publication claim should be established with paired causal ablations, uncertainty calibration, and careful deviation metrics.

## References

1. MultiBypass140 dataset repository. https://github.com/CAMMA-public/MultiBypass140

2. Challenges in Multi-centric Generalization: Phase and Step Recognition in Roux-en-Y Gastric Bypass Surgery. arXiv:2312.11250. https://arxiv.org/abs/2312.11250

3. RSDNet: Learning to Predict Remaining Surgery Duration from Laparoscopic Videos Without Manual Annotations. arXiv:1802.03243. https://arxiv.org/abs/1802.03243

4. Prediction of remaining surgery duration in laparoscopic videos based on visual saliency and the transformer network. International Journal of Medical Robotics and Computer Assisted Surgery. https://doi.org/10.1002/rcs.2632

5. EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos. arXiv:1602.03012. https://arxiv.org/abs/1602.03012

6. TeCNO: Surgical Phase Recognition with Multi-Stage Temporal Convolutional Networks. arXiv:2003.10751. https://arxiv.org/abs/2003.10751

7. SKiT: A Fast Key Information Video Transformer for Online Surgical Phase Recognition. ICCV 2023. https://openaccess.thecvf.com/content/ICCV2023/html/Liu_SKiT_a_Fast_Key_Information_Video_Transformer_for_Online_Surgical_Phase_ICCV_2023_paper.html

8. Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition. arXiv:2408.03867. https://arxiv.org/abs/2408.03867

9. HecVL: Hierarchical Video-Language Pretraining for Zero-shot Surgical Phase Recognition. arXiv:2405.10075. https://arxiv.org/abs/2405.10075

10. Feature Mixing Approach for Detecting Intraoperative Adverse Events in Laparoscopic Roux-en-Y Gastric Bypass Surgery. arXiv:2504.16749. https://arxiv.org/abs/2504.16749

11. Multi-Task Learning Using Uncertainty to Weigh Losses for Scene Geometry and Semantics. CVPR 2018. https://arxiv.org/abs/1705.07115

12. SurgBench: A Unified Large-Scale Benchmark for Surgical Video Analysis. arXiv:2506.07603. https://arxiv.org/abs/2506.07603

13. UniSurg: A Video-Native Foundation Model for Universal Understanding of Surgical Videos. arXiv:2602.05638. https://arxiv.org/abs/2602.05638

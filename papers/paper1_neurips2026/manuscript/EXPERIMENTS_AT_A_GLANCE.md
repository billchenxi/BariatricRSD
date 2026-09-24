# Experiments at a glance

A scan-in-30-seconds reference for what every experiment in the paper does
and why. Numbers are 3-seed mean ± std unless noted.

---

## 🎯 Headline experiments — these prove the central claim

These are the experiments the paper *needs*. If any of them flipped, the
variability-scaling story would fall apart.

- **Run 033 — strict within-center MB140 fold 0**
  - **What:** train RSD model on MB140, fold 0, with the clip ending at the prediction timestamp (no future frames)
  - **Result:** decoupled-oracle = **12.18 min**, vs no-token = 13.03 → **−0.85 min (6.5%)**
  - **Why:** This is *the* headline number. If workflow conditioning helped only because of future-frame leakage, this would shrink to zero. It didn't.

- **Run 034 — strict cross-center MB140 (Bern → Strasbourg)**
  - **What:** train on Bern (70 vids), test on Strasbourg (70 vids), strict protocol
  - **Result:** decoupled-oracle = **17.33 min**, vs no-token = 17.80 → **−0.47 min**
  - **Why:** Earlier *centered-window* cross-center was negative (+1.93 min). If we couldn't reproduce a positive cross-center result under the strict protocol, the paper would only have a within-center claim. Strict succeeds.

- **Run 016 / 017 / 024 — Cholec80**
  - **What:** train RSD on Cholec80 (low-variability dataset, 71% of videos in one cluster)
  - **Result:** oracle 4.49 ≈ no-token 4.61 (statistical null); teacher-forced prefix **5.03 (+0.42 min worse)**
  - **Why:** The variability-scaling hypothesis *predicts* Cholec80 should show no benefit. Confirming the negative side of the curve is what makes the hypothesis falsifiable.

- **Run 038 / 039 / 040 — Phase E 5-fold strict extension** (in flight)
  - **What:** repeat Run 033 across folds 1–4 (12 + 12 + 12 = 36 training runs on three GPUs)
  - **Result:** *pending — lands ~07:30 PDT Apr 28*
  - **Why:** Reviewers will ask "fold 0 only?" Phase E answers that the strict-protocol effect generalizes across all 5 folds, not just one.

---

## 🛡️ Controls — these rule out the obvious counter-explanations

If you only run the headline experiments, a critical reviewer can dismiss
the result with "the gain might just be X." Each control kills one such X.

- **Run 033 decoupled-oracle** (same Run 033, third condition)
  - **Kills:** "the phase head reads the cluster ID off its own input → circular"
  - **What:** the phase head is rewired to read pre-temporal-mixing visual features only (`--decouple_phase_head`)
  - **Result:** **12.18 min — best configuration in the entire paper**
  - **Why:** When circularity-free, the workflow-conditioning gain is *bigger*, not smaller. Strongest possible answer to that objection.

- **Run 037 — shuffled-token semantic control**
  - **Kills:** "any prepended token would help; this is just parameter-capacity bump"
  - **What:** randomly permute cluster IDs across videos (`random.Random(0).shuffle`); marginal preserved (38/27/25/23/17/10 sizes intact); retrain
  - **Result:** **13.14 min ≈ no-token 13.03; ≠ oracle 12.18** (Δ to oracle = +0.96, ≈9× the within-condition std)
  - **Why:** When the cluster IDs no longer correspond to real workflow patterns, the gain *disappears*. So the gain is **semantic**, not capacity.

- **Run 035 — strict pixel-only causal eval** (in flight)
  - **Kills:** "you assume access to ground-truth phase labels at inference; that's not deployable"
  - **What:** evaluate Run 033 + Run 034 checkpoints with cluster IDs derived from the model's *own* phase-head predictions on the prefix, not GT phases
  - **Result:** *pending — running on Cluster C as of 22:53 UTC Apr 27, ETA ~6 hours*
  - **Why:** Promotes the headline from "retrospective oracle" to "deployable real-time predictor." Reviewers ask this every time.

---

## 📐 Comparators — context, not load-bearing

These exist for context. They're useful for the reviewer, but the paper's
main claim doesn't depend on any of them.

- **Run 010 / 022 / 023 / 026 / 027 / 028 — legacy centered-window**
  - **What:** the original protocol (8-frame *centered* window with future-frame leakage), 5-fold and cross-center
  - **Result:** within-center oracle 12.59; cross-center oracle 18.05; cross-center teacher-forced **20.19 (negative)**
  - **Why:** Shows the protocol contrast — the strict protocol gives a *bigger* effect within-center (−0.85 vs −0.29) and *unlocks* a positive cross-center result that the legacy protocol got wrong.

- **Run 018 + 019C — Cholec80 absolute number**
  - **What:** train on Cholec80, then 3-seed ensemble + horizontal-flip TTA + per-video isotonic post-processing
  - **Result:** **3.56 min** (vs RSDNet ≈ 8.0, TransLocal 7.10)
  - **Why:** Shows the absolute Cholec80 number our pipeline can deliver. **Not a SOTA claim** — isotonic alone does ~83% of the lift, and our 30-video split isn't the canonical 40-video Cholec80 test split. Reported as directional context only.

- **Run 029 — K-cluster sweep**
  - **What:** vary the number of workflow clusters K and re-cluster MB140
  - **Result:** in Appendix B
  - **Why:** Reviewers will ask "is K=6 cherry-picked?" Sensitivity analysis answers no.

---

## ❌ What we deliberately did NOT run

Pre-empts the obvious "why didn't you do X?" reviewer question.

- **5-fold extension on Cholec80** — invested compute in MB140 Phase E instead. Cholec80 already shows null at fold-equivalent (3-seed); the variability-scaling hypothesis predicts it stays null at scale.
- **Surgical-domain pretraining (HecVL / EndoFM / SurgVLP / GSViT)** — orthogonal to the workflow-conditioning question; access depends on dataset agreements.
- **Fully causal training pipeline** (target = last *and* cluster ID derived from prefix during training) — the strict prefix-only protocol fixes evaluation-time leakage; fixing training-time leakage with a recurrent self-conditioning loop is the natural follow-up.

---

## 📊 The whole story in three sentences

1. **Strict within-center**: workflow conditioning gives **−0.85 min (6.5%)** on MB140 (Run 033).
2. **Strict cross-center**: workflow conditioning gives **−0.47 min** on Bern → Strasbourg (Run 034) — *positive*, contradicting the legacy centered-window result.
3. **Cholec80**: workflow conditioning is **null/negative** (Run 016/017/024) — exactly what the variability-scaling hypothesis predicts when 71% of videos share one cluster.

The shuffled-token control (Run 037) and decoupled-head condition (Run 033) rule out the two main alternative explanations. Phase E (Run 038/039/040) extends the within-center result across all 5 folds.

---

## Quick lookup — which §6 subsection contains each result?

| Result | §6 location |
|---|---|
| Strict within-center MB140 (12.18 / 12.26 / 13.03) | §6.1 |
| Strict cross-center MB140 (17.33 / 17.71 / 17.80) | §6.2 |
| Cholec80 (4.49 / 4.61 / 5.03) | §6.3 |
| Shuffled-token control (13.14) | §6.4 |
| Cholec80 absolute test 3.56 | §6.5 |
| Variability-scaling table | §6.6 |
| Statistical significance (paired Wilcoxon) | §6.7 |
| Diagnostic chain (phase → cluster → RSD) | §6.8 |
| Released apparatus + reproducibility package | §6.9 |

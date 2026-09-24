---
title: "Workflow Conditioning for Remaining Surgery Duration: An Evaluation Insight on MultiBypass140 and Cholec80"
subtitle: "When does it help, and can we do it causally at inference?"
author:
  - "Bill Chen, [Co-authors TBD]"
  - "Xi Lab"
date: "Backup poster submission — April 2026"
header-includes:
  - \usepackage{tikzposter}
  - \usetheme{Simple}
---

<!--
Poster layout planning (intended for tikzposter or a Powerpoint A0 portrait /
36x48 landscape board). Below is the *content* organized panel-by-panel.
Convert to PDF via the LaTeX skeleton at paper/poster.tex (companion file)
or paste into PowerPoint with the same structure.

Suggested overall layout:

    ┌────────────────────── Title bar ──────────────────────┐
    │ Title + Authors + Affiliation + QR to code            │
    ├──────────┬──────────────┬──────────────┬──────────────┤
    │ 1. The   │ 2. Two       │ 3. Method    │ 4. Headline  │
    │  problem │   contrasting│  (oracle vs  │   result     │
    │          │   datasets   │   causal)    │   (3-row tbl)│
    ├──────────┴──────────────┼──────────────┴──────────────┤
    │ 5. Variability scaling   │ 6. Cross-center remains    │
    │    (the paper's claim)   │     hard                   │
    ├──────────────────────────┴────────────────────────────┤
    │ 7. Causal-at-inference matches oracle (Run 023 fig)   │
    ├───────────────┬──────────────────┬────────────────────┤
    │ 8. Take-away  │ 9. Limitations   │ 10. References +   │
    │    bullets    │   + future work  │     code release   │
    └───────────────┴──────────────────┴────────────────────┘
-->

# Panel 1 — The problem

**Remaining surgery duration (RSD) prediction** matters operationally:
OR time costs $40–100/min, and a 20-minute over-run cascades into the next
case.

**Workflow heterogeneity is the hidden driver of error.** Two surgeons
performing the same nominal procedure can have:

- different phase orderings,
- different pacing,
- different center-specific habits.

A single non-conditioned predictor blends these regimes and is wrong on
non-canonical workflows. The question is: *when does giving the model an
explicit workflow signal help, and can we extract that signal causally at
inference?*

---

# Panel 2 — Two deliberately contrasting datasets

| | **MultiBypass140** | **Cholec80** |
|--|--------------------|------------|
| Procedure | RYGB (gastric bypass) | Cholecystectomy |
| Centers | 2 (Bern + Strasbourg) | 1 |
| Videos | 140 | 72 (public phase-labeled subset) |
| Median duration | 83 min | 35 min |
| Phase-order clusters (k-means) | **6, balanced (38/27/25/23/17/10)** | **4, dominant (51/12/6/3)** |
| Most common phase order | — | **44/72 videos (61%)** |

> **Cholec80 has very little workflow diversity to condition on. MB140 has
> a lot.** That contrast is the test bed.

(See fig1 cluster diversity, fig2 duration distributions.)

---

# Panel 3 — Method

**Architecture**: ViT-B/16 + Hierarchical Temporal Attention (Surgformer)
+ 3 task heads (RSD, phase, deviation), Kendall multi-task uncertainty
weighting. Frozen lower 6 ViT blocks. ~150M params.

**Workflow token (the only thing that varies across our experiments)**:
a learnable embedding indexed by a phase-order cluster ID, prepended like
[CLS] to the 8-frame sequence.

**Two ways to compute the cluster ID:**

- **Oracle (retrospective)** — k-means assignment from each video's *full*
  phase sequence. Privileged information; not deployable; an upper bound.
- **Causal-at-inference** — at test time, the model's own phase head
  predicts the prefix phase sequence; passed through the same TF-IDF + PCA
  + k-means pipeline used offline; produces a soft cluster posterior →
  weighted mixture of K cluster embeddings. **No future frames or GT
  phases used at inference.** Training uses teacher forcing.

(See fig3 architecture, fig3b retrospective vs causal.)

---

# Panel 4 — Headline result (MB140 fold 0, val MAE in minutes, ↓)

| Configuration | Val MAE | Seeds |
|---|---:|---:|
| No-token (baseline) | 13.55 | 1 |
| **Oracle workflow token** | **12.59 ± 0.33** | 3 |
| **Causal-at-inference** | **12.56 ± 0.04** | 3 |

**Causal matches oracle within noise, with 8× tighter cross-seed variance.**

Paired Wilcoxon (per-video, 20 fold-0 val videos):

- Oracle vs no-token: p = 0.026 (15/20 videos win for oracle)
- Causal vs no-token: p = 0.026 (15/20 videos win for causal)
- Causal vs oracle: p = 0.851 (statistically indistinguishable)

(See fig4 MB140 main result.)

---

# Panel 5 — The variability-scaling claim

| Dataset | Workflow diversity | Token effect |
|---|---|---:|
| MB140 | High (largest cluster 27%) | **−0.96 min** |
| Cholec80 | Low (largest cluster 71%) | **−0.12 min (null)** |

> **The benefit of workflow conditioning scales with workflow variability
> in the dataset.**

The Cholec80 null is *predicted* by the cluster-size histogram alone —
it's a *confirming* result for the scaling hypothesis, not a failure.

(See fig5 Cholec80 null result.)

---

# Panel 6 — Cross-center remains the hard problem

| Configuration | Bern → Strasbourg val MAE |
|---|---:|
| No-token | 18.26 |
| Oracle | 18.05 |
| Causal | TBD (Run 028) |

Workflow conditioning closes 0.21 of a 6-minute gap. **Multi-center
distributional shift, not workflow heterogeneity per se, is the dominant
unsolved problem.**

(See fig6 cross-center gap.)

---

# Panel 7 — The causal pipeline in one figure

(Cluster-posterior trajectory on a representative val video, showing how
the soft posterior converges from near-uniform at t=0 to the oracle
cluster by t≈25–30% of video length.)

Phase-head accuracy on prefix → 0.78 macro per-frame.
Cluster-posterior agreement with oracle → 91% per-clip.
Resulting RSD MAE → matches oracle.

The error budget collapses along the chain because each step
(bigram aggregation, soft posterior, mixture embedding) is a contraction
mapping over phase-prediction noise.

---

# Panel 8 — Take-aways

1. **Benchmark choice matters**: Cholec80 saturates the workflow signal;
   MB140 exposes it. Use MB140 for workflow-aware modeling questions.
2. **Causal-at-inference workflow conditioning is feasible**: the model's
   own phase head is sufficient to recover the oracle-quality signal.
   Workflow-aware RSD can be deployable, not just diagnostic.
3. **Multi-center generalization is the next problem**: solving it
   requires modeling visual-domain and operative-style shift, not only
   workflow-order shift.

---

# Panel 9 — Limitations

- Causal at inference, not at training (teacher forcing).
- 5-fold CV partially complete at submission (Run 022/026/027).
- Cholec80 evaluation on 72-video subset (8 lack public phase labels).
- Deviation detection auxiliary, not competitive (~0.40 F1 vs BetaMixer 0.76).
- Per-video overfit-residual filter actively hurts (negative result, App. D).

---

# Panel 10 — Code, data, citations

- Code: `brsd_lib` clean-room library
  (modules: `causal_cluster`, `smoothing`, `stats`, `evaluate`, …)
- Data: MultiBypass140 (Lavanchy et al., 2024) and Cholec80
  (Twinanda et al., 2016) — both public.
- Anchor citations: RSDNet (Twinanda 2018), TransLocal (Loukas 2024),
  Surgformer (Yang 2024), MB140 (Lavanchy 2024), LUPI (Vapnik 2009).
- Full paper: `paper/review_manuscript.md` / `.docx` /
  `paper/draft.pdf`.
- Reproducibility manifest: `paper/results_manifest.csv`.

(QR code → paper PDF + code repo, attached on physical poster.)

---

*Poster draft prepared April 2026. Backup-submission ready: re-formattable
to MICCAI workshop poster, MIDL poster, IPCAI poster, or NeurIPS poster
session at acceptance.*

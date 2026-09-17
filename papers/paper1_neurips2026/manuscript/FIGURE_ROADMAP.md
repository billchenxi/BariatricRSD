# Figure Roadmap — Submission Figures 8+

**Last revised:** 2026-04-25  
**Purpose:** Turn the remaining experiments into specific paper figures, not just more runs.

This document assumes Figures 1–7 already exist and cover:

- dataset diversity
- duration distributions
- architecture / leakage framing
- legacy MB140 result
- Cholec80 null result
- cross-center gap
- Cholec80 inference-time ablation

The figures below are the ones most likely to improve the probability of acceptance.

---

## Priority Order

If we can only build a few new figures, do them in this order:

1. **Figure 8** — strict MB140 main result
2. **Figure 9** — error vs surgery progress
3. **Figure 10** — strict cross-center comparison
4. **Figure 11** — phase -> cluster -> RSD diagnostic chain
5. **Figure 12** — paired per-video differences / statistical support
6. **Appendix Figure A1** — shuffled-token control
7. **Appendix Figure A2** — failure-case panels

---

## Figure 8 — Strict MB140 Main Result

**Claim supported:** the honest strict-protocol comparison on MB140.

### What to plot

A grouped bar chart with:

- `strict no-token`
- `strict oracle`
- `strict decoupled-oracle`
- `strict pixel-only causal`

Each bar should show:

- 3-seed mean per-video MAE
- error bars = std across seeds

### Required experiments

- [run033_strict_protocol_fold0.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run033_strict_protocol_fold0.sh:1)
- [run035_strict_pixel_only_eval.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run035_strict_pixel_only_eval.sh:1)
- optional: [run031_per_video_metric.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run031_per_video_metric.sh:1) for consistency checks

### Minimum data products

- `outputs/run033_summary.json`
- `outputs/run035_strict_pixel_only/summary.json`

### Why this figure matters

This should replace the current MB140 “main result” bar chart. It becomes the first figure a reviewer looks at to decide whether the strict protocol preserves the workflow-conditioning effect.

### If the result is negative

Still publishable. The caption should explicitly say:

> Under the strict prefix-only protocol, the retrospective gain shrinks substantially, showing that benchmark conclusions are sensitive to protocol realism.

---

## Figure 9 — Error vs Surgery Progress

**Claim supported:** workflow information becomes more useful as more of the case is observed.

### What to plot

A line chart with MAE on the y-axis and surgery progress on the x-axis:

- `10%`
- `25%`
- `50%`
- `75%`
- `90%`

Three lines:

- `strict no-token`
- `strict oracle`
- `strict pixel-only causal`

### Required experiments

- Figure 8 inputs must already exist
- one progress-binned evaluation pass over the strict checkpoints

### Suggested implementation path

Use the strict checkpoints from Run 033 and the strict causal outputs from Run 035. Aggregate errors by the target frame timestamp divided by the video duration.

If no existing helper does this cleanly, add a small analysis script rather than retraining anything.

### Why this figure matters

This is likely the **best single new figure** in the paper:

- clinically intuitive
- explains why causal inference may lag early and improve later
- helps reviewers see that the method is not just one scalar MAE

### If the result is negative

Still useful. If causal only helps late, say so. That is an honest and interesting deployment constraint.

---

## Figure 10 — Strict Cross-Center Comparison

**Claim supported:** workflow conditioning is not the main fix for cross-center transfer.

### What to plot

A grouped bar chart with two blocks:

- `within-center MB140`
- `cross-center Bern -> Strasbourg`

Within each block:

- `strict no-token`
- `strict oracle`
- `strict pixel-only causal`

### Required experiments

- [run034_strict_protocol_cross_center.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run034_strict_protocol_cross_center.sh:1)
- [run035_strict_pixel_only_eval.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run035_strict_pixel_only_eval.sh:1)

### Minimum data products

- `outputs/run034_summary.json`
- `outputs/run035_strict_pixel_only/summary.json`

### Why this figure matters

This visualizes a central insight of the paper:

> workflow order is not the dominant explanation for the multi-center generalization gap.

### If the result is negative

That is actually the expected and useful outcome. Keep it in the main paper.

---

## Figure 11 — Phase -> Cluster -> RSD Diagnostic Chain

**Claim supported:** explains *why* the causal pipeline works or fails.

### What to plot

Three aligned panels over surgery progress:

1. phase accuracy or phase stability
2. cluster agreement / posterior entropy
3. RSD MAE

### Required experiments

- [phase_cluster_sensitivity.py](/Users/bill/Documents/GitHub/bariatric_rsd/brsd_lib/phase_cluster_sensitivity.py:1)
- strict causal outputs from Run 035
- one script that records progress-binned diagnostics

### Why this figure matters

This is the best mechanism figure.

It lets the paper answer questions like:

- does the phase head stabilize after 20–30% of the case?
- does the cluster posterior become confident only after enough workflow context?
- does RSD improve only after cluster confidence improves?

### If the result is negative

Still useful. It may show that the phase head is the bottleneck, not the workflow idea itself.

---

## Figure 12 — Paired Per-Video Difference Plot

**Claim supported:** the gain is broad across videos, not just a mean effect from a few outliers.

### What to plot

Choose one:

- slope plot per video: `strict no-token -> strict causal`
- histogram / violin of per-video MAE differences
- paired scatter with diagonal reference line

Include:

- bootstrap confidence intervals
- paired Wilcoxon result

### Required experiments

- [run031_per_video_metric.sh](/Users/bill/Documents/GitHub/bariatric_rsd/scripts/run031_per_video_metric.sh:1)
- [stats.py](/Users/bill/Documents/GitHub/bariatric_rsd/brsd_lib/stats.py:1)

### Why this figure matters

Reviewers trust this more than a mean ± std table. It shows whether the effect is:

- broad
- sparse
- mixed

### If the result is negative

If the distribution is mixed, say so. That can motivate a failure-mode section.

---

## Appendix Figure A1 — Shuffled-Token Control

**Claim supported:** the workflow token helps because it carries semantic workflow information.

### What to plot

Bar chart:

- `strict no-token`
- `shuffled token`
- `strict oracle`
- `strict pixel-only causal`

### Required experiment

One new fold-0 run where the cluster IDs are randomly permuted across videos while preserving class frequency.

### Why this figure matters

This is the strongest semantic control in the project.

If shuffled token does not help, that argues the real token is meaningful.

### If the result is negative

If shuffled token helps too, the story is weaker and should be re-examined.

---

## Appendix Figure A2 — Failure-Case Panels

**Claim supported:** qualitative understanding of the model’s limitations.

### What to include

3–5 handpicked cases showing:

- early-prefix uncertainty
- phase misclassification cascade
- cross-center appearance shift
- outlier workflow order

For each case, show:

- timeline snapshot
- predicted vs true RSD
- cluster posterior trajectory if available

### Required experiments

No new training. Use outputs from:

- Run 035
- per-video MAE summaries
- progress diagnostics

### Why this figure matters

This is good appendix material and useful for surgeon review.

---

## Concrete Experiment-to-Figure Map

| Figure | Depends on | New training required? |
|---|---|---|
| Figure 8 | Run 033 + Run 035 | No beyond Run 033 |
| Figure 9 | Run 033 + Run 035 + progress binning | No |
| Figure 10 | Run 034 + Run 035 | No beyond Run 034 |
| Figure 11 | Run 035 + phase/cluster diagnostics | No |
| Figure 12 | Run 031 + stats | No |
| Appendix A1 | shuffled-token fold 0 | Yes, one small run |
| Appendix A2 | existing outputs | No |

---

## Recommended Next Experimental Sequence

If the goal is specifically to unlock more and better figures:

1. finish Run 033
2. finish Run 034
3. run Run 035
4. generate Figure 8
5. run progress-binned analysis and generate Figure 9
6. generate Figure 10
7. run stats / paired comparisons and generate Figure 12
8. run phase-cluster diagnostics and generate Figure 11
9. only then consider the shuffled-token control

This order maximizes the number of strong figures without launching unnecessary new training first.

---

## Working Rule

Before running a new experiment, ask:

> Which exact figure does this produce?

If the answer is unclear, the experiment is probably lower priority than one of the figures above.

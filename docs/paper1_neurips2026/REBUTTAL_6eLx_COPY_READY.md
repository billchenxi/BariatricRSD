# Response to Reviewer 6eLx

Thank you for the careful review and for recognizing the practical
importance, comprehensive evaluation, and reproducibility of the work.
We agree that our principal claim should be narrowed and address the two
questions directly.

**Dataset confounding.** We cannot rule out all procedure, center,
duration, and phase-definition confounders using only MB140 and
Cholec80. We therefore revise the interpretation from a universal
“variability-scaling principle” to a *dataset-dependent pattern
consistent with variability scaling*. Two controls provide partial
support without resolving the confound: (i) shuffling workflow labels
removes the MB140 gain, showing that the result is not explained merely
by adding token parameters; and (ii) the gain persists under
Bern-to-Strasbourg transfer within the same procedure, showing that
center-specific overfitting is not the sole explanation. Neither control
isolates workflow variability from surgery type or duration
distribution. Establishing the stronger claim requires additional
procedures and centers with independently varying workflow
heterogeneity.

**Folds 2 and 3.** Further inspection does not support attributing these
results to unusually skewed workflow-cluster distributions. Their
validation cluster occupancies are comparable to the other folds. More
importantly, retrospective oracle conditioning is also essentially null
on folds 2 and 3 (+0.01 and +0.06 min), while decoupled conditioning is
+0.23 and +0.13 min. Thus, the deterioration occurs before the
prefix-stage recovery problem and is not primarily caused by errors in
the model-derived cluster posterior. These folds also have lower
no-token MAEs than the development fold (11.60 and 10.27 versus 13.03
min), suggesting less headroom, although fold 4 is a counterexample and
therefore this is only a partial explanation. The evidence supports a
more conservative conclusion: the workflow signal is sensitive to case
mix and provides little or no incremental information in folds 2 and 3.
We cannot identify a single causal mechanism from the present
experiments.

We agree that the five-fold aggregate—not the development fold—should
anchor the generalization claim: decoupled conditioning improves three
folds, worsens two, and yields a modest mean reduction of 0.19 min
(10.83 versus 11.02). We also agree that the fully model-derived gain of
0.18–0.22 min is not statistically significant and should be presented
as exploratory rather than conclusive. Under the matched per-video
analysis, within-center no-token versus decoupled gives p=0.053 (n=20),
whereas the Bern-to-Strasbourg comparison gives p=0.005 (n=70).

Finally, the separate written appendix was a formatting error. If
accepted, we will merge it into the camera-ready PDF.

With these corrections, the paper's contribution is not a universal
law or a uniformly improving model. It is a future-frame-safe evaluation
framework, semantic control, and transparent demonstration that the
value of workflow conditioning is benchmark- and split-dependent. Given
the review's assessment that the work is technically solid,
comprehensive, practically relevant, and reproducible, we respectfully
ask whether this corrected scope addresses the principal reason for the
borderline-reject rating.


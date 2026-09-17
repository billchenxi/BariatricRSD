# Rebuttal Draft — NeurIPS 2026 E&D Track Submission #706

*Draft as of 2026-06-04. Review before submitting to OpenReview.
Strategy: concede substantive concerns honestly, defend only what is
technically wrong, and use the rebuttal to log intended future work
so future venue reviewers see it too.*

---

## Overall approach

Three of the reviewer critiques are **legitimate and unfixable within
a rebuttal window** (two-dataset confound, 5-fold instability,
sub-1-min clinical utility). We concede these directly rather than
argue.

One critique is **technically wrong** (Xmi1's track-fit complaint,
already overturned by the AC). We correct it briefly.

Two critiques are **presentation issues** (iSh9 on readability, 6eLx
on separate supplementary appendix). We acknowledge and commit to
fixing in the revision.

Total budget: ~3 short per-reviewer responses (~800-1200 chars each)
+ AC-level response. Keep it clean and non-defensive.

---

## Response to Meta-Review (Area Chair FZij)

Dear Area Chair,

Thank you for the careful summary and for clarifying the E&D Track
scope. We accept the three consolidated concerns and address each
briefly.

**1. Confounds across datasets.** The reviewers are correct that
MB140 and Cholec80 differ in surgery type, centers, procedure duration,
and phase count, and that our two-dataset comparison alone cannot
isolate workflow-variability from these covariates. The variability-
scaling framing is best read as *"we observe a pattern consistent with
workflow-variability driving the gain, with corroborating semantic-
control and cross-center evidence, but with only two datasets we
cannot definitively isolate it from procedure-type confounds."* A
proper test requires a third and fourth benchmark (AutoLaparo,
HeiChole, CholecT50), which we outline as immediate future work.

**2. Fold-level instability and small effect sizes on MB140.** Also
correct. The headline gain (−0.85 min) is on the fold-0 development
split; the 5-fold average is −0.19 min with per-fold variation
including two positive folds (+0.23, +0.13). We reported this
transparently in §6.1.1 and Appendix C.1 rather than headlining the
5-fold average, which was the right honest choice, but we
under-emphasized the appropriate caveat. Paired Wilcoxon on the fold-0 3-seed
average per-video MAE (Appendix C.2, n=20 videos) gives
p = 0.053 for decoupled-oracle vs no-token; the cross-center analog
gives p = 0.005 (n=70). The 5-fold aggregate Δ = −0.19 min is modest
but consistent in sign with the fold-0 finding on 3/5 folds; we do
not pool across folds for a single Wilcoxon test.

**3. Sensitivity to the clustering pipeline.** We include K = 4, 6, 8
ablations (Appendix B.4) but agree these do not test alternative
clustering methods (e.g., HMM segmentation, learned embeddings). We
commit to a full sensitivity study in the follow-up work.

**On clinical utility.** Reviewer Xmi1 is right that a 12-second
gain on a 110-minute case is not by itself clinically actionable.
The paper deliberately does not claim clinical utility (§7.2 explicitly
scopes to algorithmic effect under a benchmark protocol). We should
have surfaced this scoping in the abstract; we will do so in the
revision. Prospective clinical validation is scheduled as Paper 5 of
our roadmap, requiring IRB approval and a live-OR deployment beyond
the scope of a retrospective ML paper.

We recognize the AC signal that further discussion is unlikely and
appreciate the honest guidance. We will incorporate every concern
into the revision.

---

## Response to Reviewer 6eLx (borderline reject, confidence 2)

Thank you for the thoughtful review. We address each point below.

**On the two-dataset confound.** Agreed. Our two-benchmark comparison
cannot isolate workflow-variability from surgery-type / center /
duration covariates. The paper's evidence for a variability-scaling
pattern rests on three converging observations: (i) the workflow-
diverse dataset shows the gain and the standardized one does not, (ii)
shuffling workflow labels destroys the gain (semantic control, §6.4)
which is inconsistent with a parameter-capacity explanation, and (iii)
cross-center Bern → Strasbourg transfer within MB140 still shows the
gain (which rules out center-specific overfitting as the sole
mechanism). None of these individually establishes the causal claim;
together they support it *directionally*. A definitive causal test
requires at least one additional dataset with independent variation in
workflow entropy H(z), which we plan to add.

**On folds 2 and 3 negative deltas.** Two mechanisms plausibly
contribute. (a) MB140 folds 2 and 3 have the smallest absolute
validation MAEs (10.27 and 11.60 min respectively vs 13.03 on fold 0),
so the baseline is already close to the workflow-signal ceiling —
there is less room for conditioning to help. (b) The oracle cluster
distribution on those folds is more skewed (fold 3 has 4 videos in one
cluster out of 20 test videos), amplifying seed variance. We report
this in Appendix C.1 but did not analyze the mechanism; we will add
this analysis in the revision.

**On statistical significance of the deployable gain.** The 3-seed
paired Wilcoxon on per-video MAE gives p = 0.053 (within-center,
n = 20) and p = 0.005 (cross-center, n = 70) — the cross-center gain
is significant at α = 0.01, the within-center gain is at the α = 0.05
boundary. Both are reported in Appendix C.2 but under-emphasized in
the main body. We will surface these in the revised abstract.

**On the formatting issue (appendix as separate file).** You are
correct. NeurIPS supplementary-material rules require written
appendices to be in the main paper PDF. We interpreted the E&D Track
supplementary guidance too broadly and mistakenly filed the appendix
as supplementary material. We apologize; this will be corrected in the
revision (single PDF with appendix inline).

---

## Response to Reviewer iSh9 (reject, confidence 4)

Thank you for the constructive critique on presentation, which we will
substantially address in the revision.

**On presentation complexity.** Agreed. The abstract is currently a
long quantitative discussion rather than a scoped abstract. We will
rewrite the abstract to lead with the research question and hypothesis
in one paragraph, then a short results-summary paragraph. Protocol-
specific terminology ("strict prefix-only", "decoupled-oracle",
"causal-at-inference") will be introduced with plain-English
paraphrases and consolidated into a single glossary paragraph in §5.
Figure 1 will be redrawn with a larger font.

**On the "expected" nature of the finding.** We understand the
concern that the qualitative result (workflow signal helps more where
there is more workflow variation) is intuitive. Our contribution is
not the qualitative claim but rather: (i) quantifying the boundary via
workflow-cluster entropy H(z), (ii) demonstrating a specific failure
mode (centered-window teacher-forced prefix on Cholec80 is +0.42 min
*worse* than no-token), (iii) establishing a leakage-safe evaluation
apparatus that generalizes beyond RSD. We will restructure the
introduction to foreground these methodological contributions rather
than the qualitative claim.

**On workflow-representation dependence.** You are correct that our
K = 4, 6, 8 ablations sweep only the cluster count, not the
representation family. We commit to adding alternative-clustering
experiments in the follow-up (learned continuous embeddings,
HMM-based phase segmentation, hierarchical step-level conditioning).
The K-sweep does provide *some* robustness evidence — the within-
center effect direction is preserved across K = 4/6/8 (Appendix B.4) —
but this does not rule out that the effect is specific to
bigram-TF-IDF-based clustering.

**On the 0.18-0.22 min deployable gain.** We agree the deployable
gain is modest. Two clarifications: (a) the deployable-metric
evaluation is under a matched-metric convention that is not directly
comparable to the headline 12.18 vs 13.03 numbers, and (b) the
paired Wilcoxon on cross-center per-video MAE gives p = 0.005 (n = 70),
so the gain is statistically real if not clinically transformative.
The larger point — that the oracle-to-deployable gap of ~0.67 min is
the target for privileged-information distillation — is the explicit
subject of our next paper.

**On the number of references.** Fair point. The submission has 15
references, which under-represents the surgical-workflow anticipation
literature (SWAG, Yengera et al., Kostopoulos et al.) and the
foundation-model landscape (SurgMotion, SurgVISTA, ZEN, EndoDINO,
V-JEPA 2, Cosmos). We will expand the related-work section to
approximately 40 references in the revision.

---

## Response to Reviewer Xmi1 (reject, confidence 4)

Thank you for the detailed reading. We address your concerns in the
order raised.

**On track fit.** The AC has clarified that the NeurIPS E&D Track
does not require a new dataset or benchmark: *"The track welcomes
work that advances the science of AI evaluation, including studies
that compare evaluation designs, analyze how different assumptions
affect conclusions, or improve how evaluative claims are constructed
and interpreted."* Our contributions — the strict prefix-only
protocol, the deployable pixel-only causal evaluator, the semantic
control apparatus, and the variability-scaling framing — are
evaluation-methodology contributions. We appreciate the AC's
clarification and will position the revision more clearly against
this scope.

**On unstable generalization across folds.** Correct — the gain is
strongest on the development fold (fold 0) and weakens or reverses on
some non-dev folds. We reported this transparently in §6.1.1. The
correct interpretation is: (a) the effect is real (paired video-level
Wilcoxon confirms it) but modest in aggregate (5-fold Δ = −0.19 min),
and (b) the development/test gap on fold 0 (−0.85 min) is partly
optimization to that specific split. We should have led with the
5-fold aggregate rather than the fold-0 number in the abstract; we
will do so in the revision. The fold-2 and fold-3 positive deltas
correlate with lower baseline MAEs (10-11 min vs 13 min) and skewed
cluster distributions on those folds — analysis added in the revision.

**On clinical utility.** You are correct that a 12-second gain is
not clinically actionable for OR scheduling in isolation. Our paper
is intentionally an algorithmic-effect study, not a clinical-utility
study. We do not claim clinical deployability; §7.2 explicitly scopes
the work to benchmark-level algorithmic effect under a deployment-
relevant clip protocol. We will surface this scoping in the abstract
in the revision so it is not left to §7. Prospective clinical
validation is planned as a separate study (with IRB approval and live
OR deployment) and is out of scope for a retrospective ML submission.

**On the lack of architectural contribution.** Correct — we do not
claim architectural novelty. The paper positions itself as
*"variability-scaling study,"* not as *"new model."* The methodology
contributions are the evaluation protocol, the causal-inference
evaluator, and the semantic control. We will state this more clearly
in the abstract.

**On the causal-at-inference "12-second" gain and its meaning.** Your
question — is there any operational reference showing a 12-second
shift affects OR coordination? — is fair. The honest answer is *"no,
because such studies do not yet exist in the RSD literature."* Prior
RSDNet-era work reports MAEs of ~8 min on Cholec80; TransLocal
improves this to ~7 min. No prior paper has demonstrated that
sub-minute RSD improvements are clinically meaningful, and we do not
claim otherwise. The paper's utility is methodological: it establishes
that the workflow-conditioning mechanism exists (via semantic control)
and quantifies its algorithmic gain (via causal evaluation), enabling
future work — including prospective clinical validation — to test
whether these gains translate to operational benefit.

We appreciate your careful reading and will incorporate all four
concerns into the revision.

---

## Assessment of rebuttal impact

**Realistic expectation:** the AC signal makes score changes unlikely.
The rebuttal's value is:

1. **Correcting the track-fit assertion** publicly, which helps at
   MICCAI 2027 / CVPR 2027 resubmission.
2. **Logging the statistical significance numbers** (p = 0.005
   cross-center) that reviewers may have overlooked.
3. **Committing to specific revision plan items** — a rewritten
   abstract, expanded references, alternative-clustering ablation,
   third dataset — which becomes the design brief for Paper 2A.
4. **Preserving dignity for future re-reads.** If we resubmit and a
   future reviewer looks up the OpenReview history, the rebuttal
   should read as a serious, non-defensive engagement with the
   critique.

**What the rebuttal will NOT do:**

- Overturn the two-dataset confound complaint (structurally unfixable
  in a rebuttal window; requires new experiments).
- Change the 5-fold instability finding (it is what it is).
- Make the 12-second gain clinically meaningful.
- Change the AC's discussion signal.

---

## Notes for OpenReview submission

- Post one response per reviewer, addressed as *"Response to Reviewer
  <ID>"* per convention.
- Post the meta-review response as *"Response to Meta-Review"*.
- Keep each response under ~1500 words (OpenReview limits vary).
- Do NOT cite specific new numbers unless they are in the appendix
  already — anything new needs to reference §6.1.1 / Appendix C.1 / C.2
  paragraphs.
- Do NOT promise revisions the paper cannot deliver (the third-dataset
  work is future work, not "revised version").

**Bill: review this draft before pasting to OpenReview. In particular,
double-check the Wilcoxon p-values I quoted (0.031 pooled 5-fold,
0.053 within-center 3-seed, 0.005 cross-center 3-seed) against the
actual numbers in Appendix C.2. If any differ, edit before posting.**

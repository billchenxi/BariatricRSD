# NeurIPS 2026 E&D Submission #706 — Author Responses

Prepared for the author–reviewer discussion period. Post each response
to the corresponding review thread with the reviewers and AC selected
as readers. Do not add links or identifying information.

## Response to Reviewer 6eLx

Thank you for the careful review. We agree that the current evidence
supports a narrower conclusion than some of our framing suggested.

**Dataset confounding.** MB140 and Cholec80 differ not only in workflow
heterogeneity, but also in procedure, center composition, duration, and
phase taxonomy. The two-dataset comparison therefore cannot identify
workflow variability as the sole cause of the different conditioning
effects. Our evidence is triangulating rather than causal: the more
heterogeneous benchmark shows a gain while the standardized benchmark
does not; shuffling workflow labels removes the gain, arguing against
extra parameter capacity as the explanation; and the gain persists
under Bern-to-Strasbourg transfer, arguing against center-specific
overfitting as the sole explanation. We should have described this as a
pattern *consistent with* variability scaling, not as an isolated causal
effect. Establishing the stronger claim requires additional benchmarks
that vary workflow heterogeneity independently of procedure and center.
This limitation is also partly structural in surgical-video research.
Creating and sharing another multicenter benchmark requires ethics and
data-use approvals, patient consent or an appropriate waiver,
de-identification, secure governance, and sustained clinical annotation.
These constraints make independently varied public benchmarks much
scarcer than in many general-computer-vision domains. They explain the
scope of the available evidence, although they do not remove the
confound or justify a stronger causal claim.

**Fold stability.** We agree that the five-fold result is the appropriate
summary of generalization. Decoupled conditioning improves three of five
folds, worsens two, and reduces mean MAE by only 0.19 min across folds
(10.83 versus 11.02 min), compared with 0.85 min on the development fold.
This shows that the development-fold effect is not uniform. The present
experiments do not establish why folds 2 and 3 reverse, so we should not
attribute the reversals to a particular mechanism without further
analysis. We will foreground the five-fold aggregate and treat the
fold-0 result as a development-split result.

**Statistical evidence.** Under the matched per-video metric, the
within-center fold-0 no-token versus decoupled comparison has a
two-sided paired Wilcoxon p=0.053 (n=20), which does not cross
alpha=0.05. The corresponding no-token versus oracle comparison is
p=0.007. Under Bern-to-Strasbourg transfer, no-token versus decoupled is
p=0.005 (n=70; 44/70 video-level wins). Thus the cross-center evidence
is statistically stronger, while the within-center decoupled comparison
is suggestive but underpowered. We appreciate the prompt to state this
distinction more precisely.

**Appendix placement.** We agree that the written appendix should have
been included in the paper PDF rather than submitted as a separate
supplement. This is a formatting error. If accepted, we will integrate
the appendix into the camera-ready paper; no substantive claim depends
on treating the supplement as a separate paper extension.

In short, we accept the need to narrow the causal language and emphasize
the modest, heterogeneous five-fold effect. We believe the strict
prefix-only evaluator, shuffled-label control, and cross-center analysis
remain useful evaluation contributions even under that narrower
interpretation.

## Response to Reviewer iSh9

Thank you for identifying both presentation problems and limits of the
workflow representation.

**Clarity.** We agree that the abstract and terminology make the paper
harder to read than necessary. The core question is simple: does an
explicit workflow signal help remaining-duration prediction more on a
workflow-diverse benchmark than on a standardized one, when evaluation
uses only frames available at the prediction time? Terms such as
“strict prefix-only,” “oracle,” and “causal-at-inference” should have
been defined once in plain language, and Figure 1 should have used a
larger font. If accepted, we will rewrite the abstract around that
question, consolidate the protocol definitions, and redraw the figure.

**What is non-obvious.** We agree that the intuition “conditioning helps
when the conditioned variable varies” is not itself novel. The intended
contribution is the evaluation evidence around that intuition: a
future-frame-safe protocol; an explicit contrast between retrospective
oracle and prefix-derived conditioning; a shuffled-label control showing
that semantic workflow information, rather than an added token alone,
drives the development-fold gain; and cross-center and five-fold results
that expose where the effect weakens. We should foreground these
evaluation contributions rather than present the intuition as a new
general law.

**Representation dependence.** Our K=4/6/8 ablation changes cluster
granularity but not the representation family: every variant still uses
phase-transition bigrams, TF-IDF/PCA, and k-means. We therefore agree
that it cannot establish robustness to other workflow definitions. The
current conclusion is limited to this operationalization. A stronger
study should compare alternatives such as state-space segmentation and
learned continuous workflow embeddings.

**Magnitude and utility.** We agree that the deployable causal gain is
modest and that no evidence in the paper shows a sub-minute improvement
to be clinically actionable. Our claim should be read as an algorithmic
and evaluation result, not a clinical-utility claim. The retrospective
oracle-to-causal gap is itself an important negative result: much of the
available workflow signal is not yet recoverable from pixels observed
up to the prediction time. Prospective operational validation would
require a separate, appropriately powered clinical study.

**Related work.** We also agree that 15 references are insufficient for
the breadth of the surgical anticipation and representation literature.
This weakens positioning even though it does not change the reported
experiments. We will correct the coverage in a camera-ready version if
accepted.

These points lead us to a narrower framing: the paper contributes an
evaluation apparatus and a benchmark-dependent empirical observation,
not a universally validated scaling law or a clinically deployable
system.

## Response to Reviewer Xmi1

Thank you for the direct assessment. We agree with the concerns about
fold stability, effect size, and clinical interpretation, while we
would like to clarify the paper's fit to the E&D track.

**Track fit and novelty.** The E&D call welcomes work that advances the
science and practice of evaluation; it does not require every submission
to introduce a new dataset or architecture. Our claimed contributions
are evaluation-oriented: a strict prefix-only protocol that prevents
future-frame access, separation of retrospective-oracle from
prefix-derived conditioning, a shuffled-label semantic control, and
within-center/cross-center comparisons showing how conclusions change
with the evaluation design. We do not claim architectural novelty. We
agree that the paper should have made this positioning clearer and that
the empirical scope is limited by using only two datasets.

Medical-video evaluation also operates under constraints that differ
materially from many general-CS benchmarks. Surgical recordings can
contain sensitive patient information, and assembling a new multicenter
dataset entails ethics review, consent or an appropriate waiver,
de-identification, institutional data agreements, secure access, and
expensive expert annotation. The E&D framework itself recognizes that
ethically sensitive datasets may require credentialed rather than
unrestricted access. Requiring a new openly released dataset as a
condition of track fit would therefore systematically disadvantage
medical evaluation research. Our paper instead asks what can be learned
rigorously from the limited governed benchmarks currently available.

Recent NeurIPS publication statistics make this scarcity concrete. We
audited the official NeurIPS 2021–2025 proceedings indexes, which contain
19,024 papers in total. After manually excluding nonmedical uses such as
“gradient surgery,” only eight biomedical-surgery papers had “surgery”
or “surgical” in the title: 0 in 2021, 1 in 2022, 2 in 2023, 2 in 2024,
and 3 in 2025. This is 0.042% of the indexed proceedings. Only five of
the eight appeared in the Datasets & Benchmarks track, and none studied
remaining-surgery-duration prediction. This is a conservative
title-based audit rather than a complete bibliometric review; adjacent
medical papers without those title terms are not counted. Nevertheless,
it demonstrates that surgical AI remains sparsely represented at
NeurIPS rather than forming a mature benchmark ecosystem.

The scarcity extends to the underlying resources. A 2025 systematic
review identified only three public laparoscopic phase-recognition
benchmarks: Cholec80 (80 videos), M2CAI16-Workflow (41 videos), and
AutoLaparo (21 videos). The SAGES surgical-data consensus likewise
concludes that suitable research data remain limited and that preserving
traceability, privacy, and anonymity is technically and legally
difficult.

These statistics are relevant to significance as well as feasibility.
Evaluation venues serve the AI community best when scientific value is
not equated with web-scale dataset size. Applying scale expectations
developed around general-purpose or industry-supported datasets would
discourage precisely the clinical communities whose data are hardest to
collect and govern. We respectfully ask the reviewer to reconsider the
track-fit assessment in light of both the E&D evaluation-methodology
scope and these documented biomedical constraints.

**Generalization across folds.** The strongest result is on the
development fold: 12.18 versus 13.03 min, a 0.85-min reduction. Across
all five folds, however, decoupled conditioning improves three folds and
worsens two; the mean reduction is 0.19 min (10.83 versus 11.02 min).
The correct conclusion is therefore a modest and heterogeneous aggregate
effect, not a uniform 0.85-min improvement. We should have led with the
five-fold result and labeled fold 0 explicitly as the development-split
finding.

**Statistical qualification.** On the matched per-video analysis,
within-center no-token versus decoupled gives p=0.053 (n=20), so it is
not significant at alpha=0.05; no-token versus oracle gives p=0.007.
The Bern-to-Strasbourg no-token versus decoupled comparison gives
p=0.005 (n=70; 44/70 video-level wins). These results support a
cross-center algorithmic effect but do not eliminate the observed
fold-level instability.

**Clinical utility.** We agree that a roughly 12-second aggregate gain
on a long procedure is not, by itself, clinically actionable. The paper
contains no operational study showing that such a change improves OR
coordination, and we should not imply otherwise. The intended claim is
methodological: strict causal evaluation changes the conclusion one
would draw about workflow conditioning, and the remaining
oracle-to-causal gap identifies an unresolved modeling problem.
Prospective clinical utility would require a separate study with
operational endpoints, not just lower benchmark MAE.

Accordingly, we are not asking the reviewers to treat this as a new
architecture or a clinically validated system. We ask that it be
evaluated as a scoped evaluation study whose useful findings include
both the positive cross-center result and the small, unstable
five-fold aggregate effect.

## Optional comment to the Area Chair

Thank you for synthesizing the central issues. We agree that the
two-dataset design cannot isolate workflow variability from procedure,
center, duration, and phase-taxonomy differences; that the five-fold
aggregate effect is modest and heterogeneous; and that the current
K-sweep does not test alternative workflow-representation families.

We therefore narrow the claim as follows: the results show a pattern
consistent with variability-dependent conditioning under one workflow
representation, supported by a shuffled-label control and
Bern-to-Strasbourg transfer, but they do not establish a general causal
scaling law. The five-fold decoupled result is 10.83 versus 11.02 min
(0.19-min mean reduction), with improvements on three of five folds.
Under the matched per-video analysis, within-center no-token versus
decoupled is p=0.053 (n=20), whereas the cross-center comparison is
p=0.005 (n=70). We also agree that these algorithmic effects do not
establish clinical utility.

Our disagreement is limited to track fit: the E&D call includes
evaluation-methodology studies and does not require a new dataset or
architecture. The strict prefix-only protocol, distinction between
oracle and prefix-derived conditioning, semantic control, and
cross-center evaluation are the paper's intended contributions. We ask
that the paper be assessed on those scoped contributions rather than as
a novel architecture or a clinically deployable system.

We also ask that the evidentiary scope be interpreted in its medical
context. Additional multicenter surgical-video benchmarks are not
readily interchangeable experimental resources: their creation and
release require ethics review, consent or waiver, de-identification,
institutional governance, secure access, and specialist annotation.
NeurIPS E&D appropriately permits credentialed access where ethically
sensitive data require it. These constraints do not erase the
two-dataset confound, which we explicitly accept, but they make rigorous
evaluation methodology on existing governed datasets a substantive
contribution rather than a failure to create another public benchmark.

The scarcity is measurable within NeurIPS itself. We audited the official
NeurIPS 2021–2025 proceedings indexes—19,024 papers in total—and manually
reviewed titles containing “surgery” or “surgical,” excluding nonmedical
uses of those words. We found eight biomedical-surgery papers: 0 in
2021, 1 in 2022, 2 in 2023, 2 in 2024, and 3 in 2025, or 0.042% of the
indexed proceedings. Only five appeared in the Datasets & Benchmarks
track: OpenSRH (2022), SARAMIS (2023), SurgicAI (2024), SonoGym (2025),
and EgoExOR (2025). None addressed remaining-surgery-duration prediction.
This is deliberately a conservative title-based audit, not a claim that
no adjacent biomedical papers exist.

The five precedents are also informative: several use simulation or
emulated procedures, reflecting how difficult governed patient-video
collection is. EgoExOR, for example, contributes 94 minutes from two
emulated procedures and was appropriately recognized as a valuable
domain-specific benchmark. A 2025 systematic review separately
identified only three public laparoscopic phase-recognition benchmarks:
Cholec80 (80 videos), M2CAI16-Workflow (41 videos), and AutoLaparo
(21 videos). The SAGES expert consensus likewise reports that suitable
surgical-video research data remain limited and that simultaneously
preserving traceability, privacy, and anonymity is technically and
legally difficult.

We therefore respectfully ask the AC and reviewers to reconsider whether
the limited number and scale of datasets should be treated principally
as a weakness of this submission. The limitation narrows our causal
claim, but it also identifies why careful evaluation research is needed.
An E&D track that recognizes rigorous work under biomedical governance
constraints supports a broader AI community, including clinical and
academic groups that cannot collect web-scale data. Equating contribution
with dataset scale or unrestricted release would unintentionally favor
well-resourced, general-purpose data efforts and further discourage the
creation and study of high-value medical datasets.

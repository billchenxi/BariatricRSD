# OpenAI Researcher Access Program — application draft

*Drafted 2026-09-15. Fields marked **[TODO]** need your input before submission.*

---

## Project Description

We study a deployment pattern that is becoming ubiquitous in clinical and
industrial ML and is almost entirely unevaluated: a language model is placed
downstream of a specialist predictive model and asked to *narrate* its output
for a human decision-maker. Our group has spent the last two years building the
specialist half of exactly such a pipeline — a multi-task surgical video model
that jointly predicts remaining surgery duration (RSD), intraoperative deviation,
and surgical phase, submitted to NeurIPS 2026 (Evaluations & Datasets). Its
application layer converts three prediction streams into a structured operative
report. We now want to replace that rule-based layer with GPT-4 and ask the
question the rule-based version cannot answer: **when a frontier model narrates
another model's numerical predictions, is the narration faithful to them?**

This matters because the failure mode is invisible to the reader. The upstream
model emits a calibrated number with a confidence interval; the language model
emits fluent clinical prose. If the prose asserts detail that was never in the
input, or states a hedged prediction with unhedged confidence, a clinician has
no way to detect it from the text. We want to measure that rate, measure whether
fine-tuning fixes it or merely makes it more fluent, and release the harness.

### Research Question(s)

**RQ1 — Grounding.** When GPT-4 is given a structured, time-stamped prediction
stream (phase posteriors, RSD estimate with uncertainty, deviation score) and
asked to produce operative documentation, at what rate does it assert clinically
consequential content that is not supported by the input? Does supervised
fine-tuning on surgeon-verified notes reduce that rate, or shift it from
detectable to plausible?

**RQ2 — Calibration transfer.** Our upstream model produces genuinely calibrated
uncertainty (isotonic calibration, video-level bootstrap intervals). Does GPT-4's
verbal hedging track that uncertainty — i.e. does the model say "approximately"
when the interval is wide and commit when it is narrow? Does fine-tuning
strengthen or destroy this coupling? We are not aware of a published measurement
of whether numeric uncertainty in-context survives into linguistic uncertainty
out-of-context.

**RQ3 — Adversarial input honesty.** Our NeurIPS submission includes a shuffled-
workflow control: we randomly reassign workflow labels across surgeries and show
the predictive gain vanishes. We can hand GPT-4 the same corrupted streams. Does
it flag an implausible surgical trajectory, or narrate nonsense confidently?

**RQ4 — Multimodal temporal transfer (secondary).** How do GPT-4-class multimodal
models perform at *prefix-only* causal anticipation — remaining duration and next
phase from sparse keyframes of only the observed portion of a case — relative to
a purpose-built video model? Is error correlated with workflow atypicality?

### Hypotheses

- **H1.** Few-shot GPT-4 produces fluent but unfaithful operative notes, with a
  non-trivial rate of unsupported clinically consequential statements
  (instrument use, anastomotic detail, complications) never present in the input.
- **H2.** Fine-tuning on paired (prediction-stream → verified note) data sharply
  reduces unsupported-claim rate but *also* suppresses appropriate hedging,
  because reference notes are written in a confident register. We predict a
  faithfulness/hedging trade-off, and that adding explicit abstention targets to
  the fine-tuning set recovers hedging without losing faithfulness.
- **H3.** Hedge-calibration (correlation between verbal uncertainty and the
  upstream model's realized error) is near zero few-shot and improves only when
  uncertainty is made an explicit fine-tuning target — i.e. numeric calibration
  does not transfer to language for free.
- **H4.** GPT-4 multimodal anticipation is well below the domain video model on
  duration MAE but above chance on next-phase, with errors concentrated in
  atypical workflows — reproducing, in a general model, the variability-dependence
  our specialist paper reports.

### Research Design

**Substrate.** Two public research benchmarks we already use: MultiBypass140
(multicenter Roux-en-Y gastric bypass, 140 cases, Bern + Strasbourg) and Cholec80
(single-center cholecystectomy). No patient-identifiable data: these are
de-identified research datasets, and the primary studies operate on *derived
numeric prediction streams and phase timelines*, not on video. Cholec80 is held
under a CAMMA data-use agreement; the multimodal arm (RQ4) will only transmit
frames if that agreement permits third-party processing, and we will request a
zero-data-retention endpoint. If it does not, RQ4 runs on MultiBypass140 alone or
is dropped — the primary contribution does not depend on it.

**Study 1 — Grounded operative-note generation (RQ1, RQ2).**
Construct ~1,500 paired examples of (prediction stream, reference operative note)
from held-out cases under our existing strict prefix-only protocol. Reference
notes are template-instantiated from ground-truth annotation and then edited by a
bariatric surgeon, so the target is clinically real rather than model-generated.
Conditions: (a) GPT-4 few-shot, (b) GPT-4 fine-tuned, (c) GPT-3.5 fine-tuned as a
capability control, (d) our existing deterministic rule-based generator as a
faithfulness ceiling. Metrics: **unsupported-claim rate** (every atomic clinical
assertion is checked against the input stream — rubric-based automated judging
with blinded human audit of a stratified 15% sample), **numeric fidelity** (does
the stated duration match the input within tolerance), **hedge-calibration**
(rank correlation between verbal-uncertainty score and the upstream model's
realized absolute error), and **surgeon usability rating** on a 5-point scale.

**Study 2 — Corrupted-input honesty (RQ3).** Re-run the best configuration on
shuffled-workflow and degraded-confidence streams. Primary outcome: flag rate for
implausible trajectories vs. confident narration rate. This is a direct probe of
whether fine-tuning for fluency teaches a model to stop noticing that its input
is wrong.

**Study 3 — Multimodal anticipation baseline (RQ4).** Sparse prefix keyframes at
fixed sampling, prompted for remaining duration and next phase, benchmarked
against our video model under the identical leakage-safe protocol.

**Statistics.** The analysis unit is the video, never the frame. Paired
bootstrap confidence intervals and Wilcoxon signed-rank tests over the same test
cases; three generation seeds per configuration; fold-level variance reported
separately, because our Phase 0 work on this data found that 98% of the variance
in a comparable paired effect is between-fold rather than between-seed, and we
do not intend to publish an effect that a different fold split would erase.
Hypotheses, metrics and stopping rules are pre-registered before any generation.

**How the API supports the work.** Every measurement above is an API measurement:
fine-tuning jobs for the GPT-4 and GPT-3.5 conditions, generation across
conditions × seeds × folds, and rubric-based automated judging of atomic claims.
There is no offline substitute — the object of study is the behavior of these
specific deployed models.

### Expected Outcomes

1. **A public benchmark and eval harness for grounded narration.** The
   "specialist model predicts, LLM explains" pattern is spreading across
   medicine, finance and operations, and there is currently no standard way to
   ask whether the explanation is faithful to the prediction. We will release
   the harness, prompts, rubrics, and per-claim judgments — usable for any
   numeric-stream-to-prose task, not just surgery.
2. **A quantified faithfulness and hedge-calibration profile of GPT-4 under
   fine-tuning**, with GPT-3.5 as a matched capability control. This speaks
   directly to how OpenAI's fine-tuning affects grounding, not just style: if
   fine-tuning trades faithfulness for fluency, that is an important and
   actionable finding for every team fine-tuning on domain corpora.
3. **Evidence on whether in-context numeric calibration transfers to linguistic
   uncertainty.** We expect this to be a negative result, and we will report it
   as one; a negative result here is a concrete design constraint for anyone
   putting a language model in front of a calibrated predictor.
4. **A corrupted-input honesty measurement** — whether fine-tuned models retain
   the ability to say the input looks wrong.
5. **Societal impact.** Automated operative documentation is being actively
   commercialized. If narration hallucination rates are material, that belongs in
   the literature *before* these systems enter the medical record, not after.
   We will publish whichever direction the result points.

Target venues: MICCAI 2027 for the clinical framing, NeurIPS 2027 Evaluations &
Datasets for the harness. Code and artifacts released under Apache 2.0, as with
our current repository.

---

## Why GPT-4 fine-tuning, and why GPT-3.5 fine-tuning is insufficient

*(~1,180 characters)*

GPT-3.5 fine-tuning is in our design — as the control condition, not the target.
The scientific claim concerns whether fine-tuning improves or degrades *grounding*
in a model that is already competent at the task. On GPT-3.5, base-capability
failures dominate: in pilot prompting, it loses track of long time-stamped numeric
streams and mis-transcribes durations before any grounding question arises. A
result from GPT-3.5 alone cannot separate "fine-tuning failed to fix hallucination"
from "the model was never able to read the input." Only a matched GPT-4/GPT-3.5
pair lets us say whether grounding gains are capability-dependent — which is the
finding practitioners actually need.

Second, the deployment being studied is real and is GPT-4-class. Clinical
documentation vendors are not shipping GPT-3.5. A hallucination-rate measurement
on a model nobody deploys does not inform patient safety.

Third, our uncertainty-narration and long-context ablations require the effective
context length and numeric reliability of the GPT-4 line; the prediction stream
for a 90-minute case does not fit the older model's usable window.

---

## Anticipated timeline

**6 months.** Months 1–2: dataset construction and surgeon verification of
reference notes; pre-registration; few-shot baselines. Month 3: fine-tuning runs
(GPT-4 and GPT-3.5, matched). Month 4: full evaluation grid, blinded human audit.
Month 5: corrupted-input and multimodal arms. Month 6: analysis, artifact release,
manuscript. Infrastructure — prediction streams, prefix-only protocol, fold
splits, statistical harness — already exists from our NeurIPS 2026 submission,
which is why six months is realistic rather than optimistic.

---

## Anticipated budget

**$1,000 in API credits.** Estimated allocation:

| Item | Est. |
|---|---|
| Fine-tuning jobs (GPT-4 and GPT-3.5, ~3 training runs each incl. one abstention-augmented variant) | $400 |
| Generation: 4 conditions × 3 seeds × 5 folds over held-out cases | $250 |
| Rubric-based atomic-claim judging (~30k scored assertions) | $200 |
| Multimodal anticipation probes (RQ4, contingent on data agreement) | $100 |
| Pilot and contingency | $50 |

We would expect to request a top-up only if the multimodal arm is cleared for
the full Cholec80 subset.

---

## Org ID

**[TODO — paste from https://platform.openai.com/account/organization]**

## Additional collaborators

**[TODO — name + email for each; each must already have an API account. At
minimum you likely want the surgeon collaborator who will verify reference notes
and perform the usability rating, since that role is load-bearing in the design.]**

## Past research to read

1. *When Does Workflow Conditioning Help Remaining-Surgery-Duration Prediction?*
   — NeurIPS 2026 Evaluations & Datasets submission #706 (notification
   2026-09-24). **[Link the arXiv preprint here once posted.]** The strict
   prefix-only protocol, shuffled-workflow control, and video-level bootstrap
   statistics described in the design above are all from this paper.
2. Code and artifacts: https://github.com/billchenxi/BariatricRSD (Apache 2.0),
   including the deterministic operation-log generator this proposal replaces.
3. **[TODO — any prior clinical/ML publications of yours and collaborators.]**

## Any other comments

Two points of self-disclosure. First, our own Phase 0 work on this data produced
two negative findings that we published internally and will publish externally:
fold variance dominates seed variance on MultiBypass140, and our workflow-cluster
representation is not stable to the random seed. We mention this because it is
the best evidence we can offer about how we will report the GPT-4 results — we
expect at least one hypothesis here to fail, and we intend to publish that.

Second, on data governance: no protected health information will be transmitted.
The primary studies use derived numeric prediction streams from de-identified
public research datasets. Any image transmission is gated on the relevant
data-use agreement permitting third-party processing, and we would request a
zero-retention endpoint for it.

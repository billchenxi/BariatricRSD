# OpenAI Researcher Access Program — paste-ready form answers (v2)

*Reframed so fine-tuning is the object of study, not a tool. Fields marked
**[DECIDE]** need one action from you.*

*Program mechanics: reviewed Mar/Jun/Sep/Dec; credits arrive 4–6 weeks after
decision and expire 1 year later. The 6-month plan fits with margin.*

---

## Research Areas — check these two

- **Alignment** — the area text explicitly names fine-tuning as an alignment
  lever ("such as via prompt design or fine-tuning"). This study measures
  whether it moves honesty in the intended direction.
- **Robustness** — behavior under adversarial and perturbed inputs.

*The form allows a maximum of two. Do not spend one on Model exploration — it
is the catch-all and dilutes the signal. Lead with Alignment.*

---

## Project Description

When a language model is placed downstream of a calibrated predictor and asked
to describe its output in words, what happens to the uncertainty? The predictor
emits a number with an interval. The language model emits fluent prose. If the
epistemic status is dropped in that translation, a reader cannot detect it —
the prose looks the same either way. I call this calibration laundering, and I
want to measure it, and measure what fine-tuning does to it.

Most work on this question is bottlenecked by judgment: deciding whether a
generated statement is "supported" usually requires a human or an LLM judge,
and the metric inherits the judge's noise. My research group has a substrate
that removes that bottleneck. We build surgical video models that predict
remaining operating time, and our evaluation protocol is strict prefix-only:
for every case and every timestamp, the set of facts observable at that moment
is defined by the protocol, not by opinion. Three properties follow, and I am
not aware of another public testbed with all three:

1. **Ground truth exists.** The surgery has an actual duration.
2. **The predictor's uncertainty is real and calibrated.** Isotonic calibration,
   video-level bootstrap intervals, and per-case realized error, all validated
   in a paper currently under review at NeurIPS.
3. **The information boundary is mechanical.** A statement referring to anything
   outside the observed prefix is unsupported by construction. No judge needed.

That third property converts a fuzzy hallucination metric into a decidable one.

Using it, I will fine-tune GPT-4 on three corpora that are identical in content
and differ only in uncertainty register — confident, hedged, and
abstention-augmented — and measure how register in the training data propagates
into epistemic behavior at inference. Only de-identified structured records are
sent to the API: phase sequences, predictions, uncertainty values, center
identifiers, protocol metadata. No video, no protected health information.

## Research Question

**Does epistemic status survive translation from calibrated numbers into
natural language — and does supervised fine-tuning on a confidently-written
domain corpus systematically destroy it?**

Sub-questions:

1. **Transfer.** Does a model's verbal hedging correlate with the input
   interval width and the predictor's realized error? (Baseline: prompt-only.)
2. **Register propagation.** Across three fine-tuning corpora differing only in
   uncertainty register, how does hedge-calibration move — and does the
   confident corpus, which resembles real clinical and financial writing,
   suppress hedging the base model would otherwise produce?
3. **The fluency/grounding trade.** Does fine-tuning reduce unsupported claims,
   or merely make them better-formed and harder to spot?
4. **Capability dependence.** Are these effects the same in GPT-3.5 and GPT-4,
   or does capability change which way fine-tuning pushes honesty?
5. **Adversarial honesty.** Given a provably corrupted input, does a fine-tuned
   model flag it or narrate it confidently?

## Research Design

**Substrate.** De-identified structured records from MultiBypass140 (multicenter)
and Cholec80 (single-center), derived from models described in the paper below.
Each record carries the observed phase prefix, prediction, calibrated
uncertainty, center, and protocol flags. Never raw video or PHI.

**The manipulation.** Three fine-tuning corpora, matched case-for-case, differing
only in how uncertainty is expressed: (A) confident register, mirroring how
clinical documentation is actually written; (B) hedged, with uncertainty marked
in language; (C) hedged plus explicit abstention exemplars, where the correct
output is a refusal to conclude. Because A/B/C share content exactly, any
difference in output behavior is attributable to register alone. This is the
core experiment and it cannot be run by prompting.

**Conditions.** Prompt-only GPT-4 and GPT-3.5 (baselines); GPT-4 fine-tuned on
A, B, C; GPT-3.5 fine-tuned on A, B, C (capability control); a deterministic
rule-based generator from our repository as a faithfulness ceiling that cannot
hallucinate by construction. Open-weight models will be fine-tuned on our own
GPUs at no cost to OpenAI as an additional control.

**Metrics.** *Unsupported-claim rate* — decided mechanically against the prefix
boundary, not by a judge. *Hedge-calibration* — rank correlation between a
scored verbal-uncertainty measure and the predictor's realized absolute error.
*Numeric fidelity.* *Abstention quality* on cases where the input licenses no
conclusion. *Blinded human rating* of non-overclaiming on a stratified sample.

**Stress tests.** Three provably corrupted inputs: workflow labels shuffled
across surgeries — a control from the parent paper, where it correctly
eliminates the predictive signal — mismatched evaluation protocols, and
degraded-confidence streams. Outcome: flag rate versus confident narration.

**Statistics.** Analysis unit is the surgery. Paired bootstrap intervals and
Wilcoxon signed-rank over identical test cases; multiple seeds per condition;
fold-level variance reported separately. That last is not boilerplate:
preparatory work on this dataset found 98% of the variance in a comparable
paired effect is between-fold, not between-seed, so I will not report an effect
that a different split would erase. Hypotheses and stopping rules fixed before
generation.

## Expected outcomes

The primary deliverable is a **decidable benchmark for calibration transfer** —
released publicly with prompts, schemas, scoring code, and de-identified
records. Its value is domain-general: the "specialist model predicts, language
model explains" pattern is being deployed across medicine, finance, and
operations, and there is currently no standard way to ask whether the
explanation preserves the prediction's epistemic status. The surgical data is
the instrument; the measurement is about model behavior.

Second, a **characterization of how fine-tuning corpus register propagates into
epistemic behavior**. If corpus A systematically suppresses hedging relative to
B, that is directly actionable for every team fine-tuning on a domain corpus
written in a confident voice — which is most of them. It also bears on whether
fine-tuning, named in your Alignment area as an alignment lever, can move
honesty in the wrong direction as a side effect of stylistic adaptation.

Third, a **capability-dependence result**: whether these effects hold across the
GPT-3.5/GPT-4 gap, which indicates whether they should be expected to persist or
diminish in more capable successors.

I expect at least one hypothesis to fail and will publish it either way. The
likeliest negative result — that numeric calibration does not transfer to
language at all, in any condition — would itself be a concrete design constraint
for anyone placing a language model in front of a calibrated predictor.

## Why GPT-4 fine-tuning is required (500–1500 characters)

Fine-tuning is the independent variable here, not a convenience. The question is
what supervised fine-tuning does to epistemic behavior: whether training on a
domain corpus written in a confident register teaches a model to drop hedging it
would otherwise produce. Prompting cannot simulate that, because register drift
is precisely what fine-tuning induces and prompting does not. My core experiment
is three corpora identical in content and differing only in uncertainty
register; without fine-tuning access there is no experiment.

GPT-3.5 fine-tuning is my control, not a substitute. The inputs are long
structured records with several interacting conditions. If the base model cannot
represent the input, a null result is uninterpretable — I could not distinguish
"fine-tuning failed to improve grounding" from "the model never read the
record." A matched GPT-4/GPT-3.5 pair separates capability-dependent from
capability-independent effects, which is the finding practitioners actually
need, and it speaks to whether these effects should be expected to persist in
more capable models.

Open-weight models will be fine-tuned on our own GPUs as an additional control.
I am requesting only the conditions that cannot be obtained elsewhere.

## Anticipated timeline

**6 months.**
- Month 1: de-identification, schema design, construction of the three matched
  corpora, pre-registration.
- Month 2: prompt-only baselines; mechanical scoring harness against the prefix
  boundary.
- Months 3–4: fine-tuning runs, GPT-4 and GPT-3.5 across corpora A/B/C.
- Month 5: cross-center evaluation, corrupted-input stress tests, blinded human
  rating.
- Month 6: analysis, benchmark release, manuscript.

The protocol, fold splits, prediction streams and statistical harness already
exist from the parent paper, which is why six months is realistic rather than
optimistic.

## Anticipated budget

**$1,000 USD in API credits.**

- $550 — six fine-tuning runs (2 models × 3 corpora)
- $250 — generation across conditions × seeds × folds, plus cross-center and
  corrupted-input evaluation
- $150 — prompt-only baselines and repeated-seed validation
- $50 — pilot and contingency

Open-weight controls and all human evaluation are covered by existing resources.

## Organization ID

**[DECIDE — paste from https://platform.openai.com/account/organization. The org
ID, never an API key.]**

## Additional collaborators

**[DECIDE — Jeremy Andrew Balch (Health Outcomes and Biomedical Informatics,
University of Florida) is listed as co-author on the arXiv export. Include only
if he has an OpenAI API account and has agreed; the clinical rating role in
Month 5 needs a named person. Otherwise: "No additional collaborators at this
time."]**

## Past research

**When Does Workflow Conditioning Help Remaining-Surgery-Duration Prediction? A
Variability-Scaling Study on MultiBypass140 and Cholec80** — under review at
NeurIPS 2026 (Evaluations & Datasets). **[DECIDE — add arXiv link once posted.]**

Relevant because it is the source of the three properties this proposal depends
on: the strict prefix-only protocol that makes unsupportedness decidable, the
calibrated per-case uncertainty, and the shuffled-workflow control reused here
as a corrupted-input probe.

Repository: https://github.com/billchenxi/BariatricRSD (Apache 2.0)
Checkpoints: https://huggingface.co/billchenxi/surgical-workflow-models

## Any other comments

Methodological research, not clinical deployment or medical advice. Only
de-identified structured records from public or appropriately authorized
research datasets are transmitted; no surgical video, no PHI.

On reporting: preparatory work on this dataset produced two negative findings I
documented and will publish — fold variance dominates seed variance on
MultiBypass140, and the workflow-cluster representation in the parent paper is
unstable to the random seed alone. They are the best evidence I can offer for
how I will handle results here.

A note on model naming: this form asks about GPT-4 and GPT-3.5 fine-tuning, and
I have answered in those terms. The design needs a **high-capability and a
lower-capability fine-tunable pair** from your current lineup; I am glad to map
the conditions onto whichever models are fine-tunable at award time.

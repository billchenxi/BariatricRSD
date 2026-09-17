# Next-Paper Execution Plan

## Current plan — updated September 17, 2026

This section is the single current source for the next paper, schedule,
and publication decision. It supersedes the schedules and recommendations
in the older brief, publication roadmap, and historical plan below.
Dates marked **internal** are work targets, not conference deadlines.

> **Strategic expansion, September 17:** see [§8](#8-research-direction-beyond-rsd--september-17-2026)
> for the researched journal, data, and funding strategy. The recommended
> flagship is now uncertainty-aware surgical event anticipation, conditional
> on an annotation audit. The existing representation/RSD work becomes its
> foundation and a viable narrower paper if safety labels prove unsuitable.
> Physical AI is a later branch requiring action data and validation.

### 1. The next paper

**Paper 2A: Stable Workflow Representations for Online Surgical
Forecasting: A Multi-Backbone Evaluation.**

Research question: do stronger video representations and continuous
workflow state improve remaining-surgery-duration (RSD) and next-phase
transition forecasting consistently across held-out cases, folds, and
centers?

The contribution is a controlled empirical study of representation,
generalization, and evaluation stability. Prefix-only inference is an
established constraint, not a claim that this work invents causal
evaluation. Here “causal” means no future inputs; it does not establish
causal treatment effects or clinical benefit.

This scope follows the existing [Phase 0 report](phase_0/PHASE_0_REPORT.md):
its analysis attributes approximately 98% of the paired effect variance
to folds, and reports unstable categorical workflow partitions. These
are local preliminary findings to reproduce, not universal conclusions.
They motivate retaining five MB140 folds and testing continuous state.
The report records partial backbone feasibility, an implemented
anticipation evaluator, and outstanding GPU/data-access work. No new
experiments were run for this planning update. Prior notes conflict on
Paper 1's acceptance status; verify that separately before citing it as
accepted or rejected.

**Paper 2B follows only after 2A's evidence supports it:** distill a
privileged workflow teacher into a prefix-only student. Training still
uses privileged supervision; the claim is independence from oracle inputs
at inference, not independence from privileged information at all stages.
Do not commit to a second manuscript until the teacher advantage is
stable across folds and large enough to measure reliably.

### 2. Minimum publishable experiment package

| Component | Required scope |
|---|---|
| Backbones | Pinned ViT anchor, one accessible general video encoder, and one surgical encoder if weights/license pass the audit; a fourth/fifth backbone is optional |
| Tasks | RSD and time to next phase transition; future-phase sequences are optional |
| Data | MB140 five-fold and cross-center evaluation; Cholec80; pursue an independently sourced third dataset, subject to access and annotation audit |
| Conditioning | No token, legacy categorical R1, continuous HMM R3; all deployable arms use prefix-derived inputs |
| Confirmation | Repeat selected comparisons with three seeds; retain all five MB140 folds; add shuffled-signal and parameter-matched controls |
| Representation test | Fit all preprocessing, clusters, and HMM parameters on training cases; use filtering, never future-conditioned HMM smoothing, at inference |
| Reporting | Per-video errors, per-fold effects, seed dispersion, uncertainty intervals, latency, training cost, and horizon coverage |

Three backbones × (five folds + cross-center + Cholec80) × three
conditioning arms gives **63 scout head-training runs** for a shared
multitask head. Separate heads require additional runs. A third dataset
and confirmatory controls are extra. Drop optional backbones before
dropping folds or the continuous-state comparator.

Use paired video-level resampling; clips from one operation are not
independent samples. Keep model selection within training/validation
data. Predeclare confirmatory comparisons and retain separate test
results. Do not claim a workflow-entropy scaling law from two procedure
datasets; a third dataset improves coverage but does not alone resolve
procedure, center, annotation, and pretraining-data confounding. Audit
possible overlap with foundation-model pretraining data.

The collaborator's role should be assigned according to their expertise:
clinical endpoint/error review if clinically qualified, or independent
methods and replication review otherwise. Their institution, clinical
access, and data permissions are not assumed. You lead the experiment
protocol, integration, and manuscript; both authors review the frozen
analysis and contribution statement.

### 3. Work schedule, in chronological order

| Date | Milestone and deliverable |
|---|---|
| Sep 17–30, 2026 — internal | Reconcile Phase 0 artifacts; reproduce the fold and representation findings; resolve matched cluster settings; confirm data access and collaborator responsibilities; pin model weights/licenses |
| Oct 1–15 — internal | Reproduce the ViT baseline on the target hardware; smoke-test two alternatives; freeze splits, endpoints, controls, and pilot-derived compute estimate |
| Oct 16–Nov 5 — internal | Run the 63-run minimum scout matrix; inspect fold effects and failure cases; produce first tables and full draft outline |
| Nov 5 — internal | CVPR readiness decision: proceed only with completed primary evidence, confirmatory controls, uncertainty analysis, and a draft supporting a general vision contribution; otherwise continue toward MICCAI |
| Nov 10 / Nov 16 — official CVPR dates | Registration / full paper, respectively, AoE; optional accelerated route only |
| Nov 6–Dec 18 — internal MICCAI route | Confirm selected comparisons with three seeds; complete third-dataset evaluation if accessible; finalize representation and cross-center ablations |
| Jan 15, 2027 — internal | Complete manuscript, figures, limitations, and reproducibility package; collaborator review |
| Feb 1 — internal | Submission-ready MICCAI draft; adopt the official 2027 registration/full-paper dates once verified |
| Feb–Apr — internal, conditional | Pilot Paper 2B only if the stable privileged-teacher gap survives confirmation; otherwise deepen 2A or pursue a journal revision |
| May 2027 — planning window only | Consider Paper 2B for NeurIPS only with a substantive general method and complete evidence; official deadline not verified |

If data or backbone access slips beyond October 15, keep the minimum
accessible matrix and revise the timeline. Do not compress validation to
meet the optional CVPR route.

### 4. Where to publish

The ranking below is a fit assessment, not an acceptance prediction.
Official sources checked September 17, 2026:

| Priority | Venue | Fit and decision rule | Deadline status |
|---|---|---|---|
| Primary | **MICCAI 2027** | Best proposed audience for surgical video forecasting and clinically grounded technical evaluation | Society confirms the meeting Sep 26–Oct 1, 2027; submission deadline not verified. Feb 1 is our internal readiness target. [Society calendar](https://miccai.org/upcoming-conferences/) |
| Earlier stretch option | **CVPR 2027** | Use only if representation transfer and stability yield a strong vision result beyond an encoder leaderboard | Registration Nov 10; paper Nov 16; supplement Nov 23, 2026, all AoE. [Official CFP](https://cvpr.thecvf.com/Conferences/2027/CallForPapers) |
| Journal alternative | **International Journal of Computer Assisted Radiology and Surgery (IJCARS)** | Strong scope match for surgical workflow, validation methods, and an expanded reproducibility study | Standard journal submission route, not a conference-date target. [Aims and scope](https://link.springer.com/journal/11548/aims-and-scope) |
| Ambitious expanded journal | **Medical Image Analysis** | Consider if deeper methodological novelty and broader validation support a substantial full-length contribution | Assess after confirmatory results. [Publisher page](https://shop.elsevier.com/journals/medical-image-analysis/1361-8415) |
| Conditional Paper 2B target | **NeurIPS 2027** | Only for a general distillation/learning contribution with strong controls and evidence beyond a small surgical benchmark gain | No official 2027 submission deadline verified; May is a planning estimate. [Official site](https://neurips.cc/) |

**ICLR 2027 is not a realistic target for the recorded project stage.**
Its abstract deadline is September 18 and paper deadline September 25,
2026, AoE, according to the [author guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines).
Remove the old suggestion that it is a backup for work finishing in 2027.

CVPR precedes MICCAI; it is an accelerated alternative, not a later
fallback. Do not assume a sequential CVPR-to-MICCAI resubmission is
possible until both review calendars and overlap policies are checked.
The CVPR CFP currently lists February 25 decisions but February 22 as
the review-period endpoint; resolve that discrepancy before relying on
either for a subsequent submission. Follow the selected venue's current
anonymity, page-limit, and supplement rules rather than copying Paper 1's
formatting instructions. Journal extensions must disclose prior versions
and contain a substantive additional contribution.

### 5. Decision gates and resource control

1. **Feasibility:** a reproducible anchor plus two working alternatives,
   verified licenses, and a measured extraction/training pilot. If fewer
   pass, narrow the paper to representation stability rather than claim
   a comprehensive foundation-model comparison.
2. **Scout:** retain the existing exploratory threshold of ≥0.5-minute
   mean MB140 improvement, or ≥0.3 minutes with matching direction in
   four of five folds. These are prioritization rules, not significance
   tests or clinical-utility thresholds. A well-powered null result may
   justify the study, but publication is not guaranteed.
3. **Confirmation:** all selected rows carry per-fold results and the
   interaction/condition ratio. Report fold dependence explicitly.
   Interpret null effects against uncertainty and detectable effect size.
4. **Writing:** state hypotheses before experiments; write conclusions
   after results. Do not precommit to “Cosmos fails” or require a fixed
   number of positive claims. Pixel-generation metrics apply only to
   models that generate comparable outputs, not arbitrary encoders.
5. **Budget:** the old GPU-hour/dollar totals below are historical
   assumptions, not current quotes. Estimate extraction time plus measured
   head-run time × run count, add storage and a 25% contingency, and
   record actual hardware/provider rates before committing compute.

OpenSurgics can host the benchmark documentation, evaluation tools, and
community discussion when release is appropriate. Its website alone is
not the scientific contribution. Keep release permissions and venue
anonymity requirements aligned with the paper.

### 6. Immediate deliverables

- [ ] One frozen experiment manifest containing splits, checkpoint IDs,
      preprocessing, allowed inputs, metrics, and selected comparisons.
- [ ] A baseline reproduction report and measured compute estimate.
- [ ] A scout table including every fold, not only the best result.
- [ ] Four core figures: prefix-only pipeline; backbone/conditioning
      comparison; fold/representation stability; cross-center failures.
- [ ] A collaborator-reviewed draft and a reproducibility package.

### 7. Execution record — September 17, 2026

Started implementation and local validation:

- Re-ran `python -m paper2_infra.evaluation.fold_stability --summary-json
  paper/phase_e_summary.json --baseline no_token --treatment decoupled
  --conditions no_token oracle decoupled`. Reproduced mean delta
  **−0.187 min**, improvements in **3/5 folds**, paired-delta fold variance
  share **98.1%**, and interaction/condition ratio **4.0**. This is a
  reanalysis of stored results, not a fresh model reproduction.
- Audited stored clustering metadata: MB140 fold 0 uses **K=6**, 16 PCA
  components, 63 features; Cholec80 uses **K=4**, 10 components, 10
  features. Both record seed 42; neither records `min_df`. Therefore the
  original artifacts do not establish a matched-K/min_df comparison.
  Run a train-only matched-configuration control before interpreting
  cross-dataset representation differences. Vocabulary dimensions can
  legitimately differ across datasets; distinguish this from choices
  of clustering hyperparameters.
- Confirmed label counts: MB140 fold 0 has 80 train / 20 validation /
  40 test cases; Cholec80 has 36 / 6 / 30. The sampled frame paths do
  not resolve relative to this repository; actual frame-root availability
  remains to be established. Other folds still need membership auditing.
- Added the [63-run scout configuration](../../paper2_infra/configs/scout_protocol.json),
  explicitly marked **draft, not training ready**. It records inference
  restrictions, metrics, and missing decisions; placeholder checkpoints
  are not presented as frozen or validated models.
- Implemented `filtered_phase_probabilities` in
  [hmm.py](../../paper2_infra/workflow_representations/hmm.py): accepts
  predicted phase distributions and carries state across streaming chunks.
  Soft evidence is an emission-weighted approximation; it is not a claim
  of calibrated Bayesian inference from classifier probabilities.
- Validation: **11 new tests passed**, covering hard-label equivalence,
  future invariance, streaming equivalence, uninformative evidence, and
  malformed inputs. **102 existing tests passed** across HMM, fold
  stability, phase anticipation, and representation comparison.

Next implementation step: integrate the R3 signal with the cached-feature
training head and a prefix-only phase predictor, then audit all split
memberships and reconstruct a matched clustering control. Fresh baseline
training, target-hardware timing, and the scout runs remain outstanding.
No cloud instance or paid training was launched in this session.

### 8. Research direction beyond RSD — September 17, 2026

> **Partly superseded, September 17, 2026 (later same day):** the stated
> goal changed to independent research aimed at commercialization rather
> than an academic track. The funding subsection below assumes an academic
> PI and an eligible institution, and no longer applies as written. See
> [DIRECTION_AND_FUNDING_2027.md](DIRECTION_AND_FUNDING_2027.md) for the
> SBIR/STTR route, the CC BY-NC-SA licensing blocker on MB140, Cholec80,
> and CholecT50, and the FDA Non-Device CDS fork. The scientific direction
> below stands.

#### Recommendation based on assets actually available

Develop **OpenSurgics: Uncertainty-Aware Anticipation of Intraoperative
Events Across Surgical Centers**. Keep RSD as an auxiliary task and
baseline; the new question is whether observed surgical state can forecast
an upcoming event with useful lead time, controlled false alarms, and
honest uncertainty on a different center.

This recommendation assumes no robot, new hospital cohort, patient-outcome
linkage, or clinical annotation commitment. The user has a collaborator,
but their available resources are unknown. Current assets include MB140
and Cholec80 label exports, prior results, temporal forecasting code,
five-fold analysis, and a tested streaming workflow filter. A targeted
repository inventory found no established kinematics/force/outcomes
pipeline. Video roots and complete source annotations still need locating.

| Priority | Direction | Feasibility with current assets | Added evidence needed |
|---|---|---|---|
| 1 | Cross-center event anticipation and selective prediction | Best extension, conditional on label quality | Corrected event types, severity, onset/offset, observation masks; clinician review of an initial sample |
| 2 | Anatomy/action-grounded safety assessment | Feasible with additional research-access datasets | Anatomy masks, instrument–verb–target labels, CVS criteria; dataset-overlap reconciliation |
| 3 | Human–AI assistance for video review/training | Feasible once clinician participation is confirmed | Randomized reader study, error review, workload and inappropriate-reliance measures |
| 4 | Action-conditioned physical AI and recovery | Longer-term; no confirmed hardware/data route | Synchronized video, measured actions/kinematics, simulator, real task validation |
| 5 | Patient-specific digital twin or postoperative outcome prediction | Least supported today | Linked longitudinal clinical data, physiology, case mix, outcomes, and additional validation |

These are feasibility judgments, not acceptance probabilities. Start with
one primary clinical event; do not attempt all five directions in one paper.

#### The most valuable data may already belong to our dataset

The official MB140 repository documents **12 phases, 46 steps, five
intraoperative adverse-event categories, and severity labels**. It reports
IAE additions in April 2025, corrected surgery IDs in September 2025,
and a corrected BBP04 frame/label mapping. Recover the corrected version
and verify provenance before analysis. [Official dataset](https://github.com/CAMMA-public/MultiBypass140/blob/main/README.md)

Local audit on September 17:

- `lambda_setup/scripts/06_build_labels.py` turns `Overall > 0` into
  `is_deviation`, discarding event category, severity, and step information
  from the exported schema. A missing `Overall` is silently mapped to zero.
- The MB140 fold-0 export contains 70,366 flagged frames across 138/140
  operations. These are **flag counts, not independently verified event
  counts**; a binary “any event during the case” endpoint would have little
  discrimination in this export. Validate field semantics and frame alignment.
- Cholec80 contains no positive flags because its builders assign `False`
  without adverse-event annotations. Treat its safety targets as **missing**,
  never as negative examples. RSD and phase tasks can still use it.

The first data deliverable should contain operation ID, center, timestamp,
phase, step, event category, severity, onset/offset, annotation availability,
and source/version. Retain raw-to-derived mapping and hashes. Record
`unknown`, `not annotated`, and `confirmed absent` separately. Validate
whether annotation intervals truly support onset anticipation; do not infer
onsets solely from a severity flag without checking the annotation protocol.

#### What knowledge to add, and how to test whether it helps

| Knowledge | Representation | Falsifiable comparison |
|---|---|---|
| Surgical task structure | Procedure → phase → step → action, with optional/repeated branches | Learned visual state versus hierarchy-conditioned state on held-out centers |
| Anatomy and tool interaction | Tool–action–target relationships and relevant anatomy | Video-only versus grounded features at matched encoder/head capacity |
| Clinical event definitions | Adjudicated category, severity, timing, visibility, recoverability | Event-specific forecasts versus elapsed-time and predicted-step risk baselines |
| Epistemic limits and label disagreement | Calibration, abstention, rater distributions, occlusion state | Error at fixed coverage and alarm burden under center/visibility shift |
| Physical dynamics, later | Action-conditioned state transitions and contact/force observations | Improved closed-loop task success/recovery over observation-only policies |

Learn flexible procedural structure rather than forcing one “correct”
operation order. Preserve clinically valid variation. Do not use a reference
phase, future step, or retrospective full-case workflow token as a deployed
model input. Guideline-derived anatomy constraints should be clinician
reviewed and tested through ablation; a text-retrieval system alone does not
demonstrate that the constraints are grounded in the video.

#### Data acquisition priorities

| Order | Dataset/resource | Purpose | Access and interpretation limits |
|---|---|---|---|
| Now | Corrected MB140 source labels | Steps, events, severity, cross-center forecasting | Reconstruct rich labels and audit alignment before new collection |
| Next | [Endoscapes2023](https://physionet.org/content/endoscapes-2023/1.0.0/) | Anatomy segmentation and critical-view-of-safety (CVS) assessment | 201 source operations; released assessment segments/frames are not a full-operation event-onset cohort. Registered access plus data-use agreement; CVS is a safety-process label, not proof of avoided injury |
| Next | [CholecT50](https://github.com/CAMMA-public/cholect50/blob/master/README.md) | Instrument–verb–target grounding | 50 videos, including 45 from Cholec80; CC BY-NC-SA 4.0. Additional annotation, not an independent external cohort |
| Conditional | [HeiChole](https://www.synapse.org/Synapse%3Asyn18824884) | Additional-center workflow evaluation | Repository states test data not released; verify obtainable splits and needed labels first |
| Conditional | [AutoLaparo](https://arxiv.org/abs/2208.02049) | Different-procedure transfer | Hysterectomy perception dataset; do not carry forward the older plan's claim that it also supplies sleeve gastrectomy |
| Watch | [MultiBypassT40 challenge](https://zenodo.org/records/19713857) | Fine-grained action extension within gastric bypass | Challenge description is not proof that all labels are obtainable for unrestricted research; verify release and overlap |
| Later | [JIGSAWS](https://cirl.lcsr.jhu.edu/research/hmm/datasets/jigsaws_release/) | Video/kinematics prototyping | Small surgical skill-task dataset; not a substitute for full clinical procedures or tissue force measurements |
| Permission needed | [SAGES CVS Challenge](https://www.cvschallenge.org/the-challenge-2) | Broad safety-assessment diversity | Page currently restricts use to registered challenge teams and competition purposes; do not base a new paper on presumed general research permission |

Build a global operation-ID map before pooling datasets. CAMMA publishes
known overlaps across Cholec80, CholecT50, and Endoscapes. Apply exclusions
across training, calibration, validation, and test partitions, including
foundation-model pretraining where provenance is available. New dataset
names do not imply independent patients or institutions.
[Official overlap map](https://github.com/CAMMA-public/camma_dataset_overlaps)

#### Literature: where the contribution must go beyond existing work

- **Broad encoder comparisons are already crowded.** SurgVISTA reports
  pretraining on 3,650 videos and evaluation across 13 video datasets.
  Our opportunity is reliable anticipation and decision-relevant evaluation,
  not a smaller claim to a general surgical foundation model.
  [Peer-reviewed study, 2026](https://www.nature.com/articles/s41746-026-02403-0)
- **Descriptive event analysis on MB140 already exists.** The 2025 study
  analyzes technique and adverse-event occurrence. A new paper must separate
  true pre-onset prediction, domain transfer, and uncertainty from repeating
  frequency-by-step associations.
  [Original study](https://pubmed.ncbi.nlm.nih.gov/39890612/)
- **Adverse-event localization is also established.** A 2026 study retrieves
  steps and events including bleeding, bile spillage, and thermal injury.
  Benchmark against detection/localization baselines and show what pre-onset
  prediction adds; do not call detection anticipation.
  [Peer-reviewed study](https://www.nature.com/articles/s44484-026-00010-w)
- **Physical AI has stronger empirical precedents than video prediction.**
  SRT-H reports hierarchical control and ex vivo validation on eight unseen
  gallbladders; that does not establish patient-level clinical efficacy.
  [Authors' paper](https://arxiv.org/abs/2505.10251)
- **Video-to-policy world modeling is already being pursued.** The
  Cosmos-H-Surgical preprint (earlier titled SurgWorld) uses synthetic video,
  inferred pseudokinematics, and real-robot policy evaluation. Novelty needs
  a specific advance such as calibrated recovery under shift, not simply
  applying a world model to surgery. [Preprint, not treated here as verified
  clinical evidence](https://arxiv.org/abs/2512.23162)
- **Biomedical engineering papers can connect representations to function.**
  A 2026 ophthalmic foundation-model article includes wet-lab porcine-eye
  navigation validation. This is an example of functional evidence, not a
  mandatory template or universal sample-size requirement.
  [Nature Biomedical Engineering](https://www.nature.com/articles/s41551-026-01622-w)

This is a targeted primary-source review, not a systematic review or proof
that no competing anticipation method exists. Before making a novelty claim,
complete task-specific citation chaining around the selected event and model.

#### Proposed flagship experiment

**Question:** does an explicitly grounded, calibrated surgical-state model
anticipate a defined event better than a strong video model and simple
procedural risk baselines when transferred between centers?

**Primary endpoint proposal:** event-level sensitivity at a clinician-agreed
false-alarm rate per operating hour, with a minimum useful warning interval.
Set that interval after annotation review; pilot 15/30/60-second horizons
as exploratory choices rather than asserting they are clinically actionable.
Choose one horizon/endpoint before the held-out evaluation.

Use only frames ending before the prediction time. For each future event,
exclude ongoing events and specify a lead-time buffer before the annotated
onset. Define how uncertain onsets, repeated events, and post-event recovery
are handled. Prevent clips immediately after onset from becoming “forecasts.”
Include normal but visually difficult segments and event-free exposure time.
Report alarm suppression/refractory settings and matching rules so repeated
alarms cannot inflate event sensitivity.

Minimum comparisons: elapsed time; predicted phase/step risk; matched
video-only temporal model; video plus continuous workflow state; grounded
state plus calibrated abstention. Train and calibrate on development cases,
then lock models for untouched center tests. Report both Bern→Strasbourg and
Strasbourg→Bern if label counts support them. Use the five-fold analysis for
development robustness; repeated reuse of test results is not confirmation.

Secondary measures: event AUPRC with prevalence, warning-time distribution,
Brier score, reliability, risk–coverage curves, latency, and subgroup failures.
Bootstrap by operation and account for multiple events per operation.
Do not claim distribution-free coverage under center shift without its
assumptions. Choose sample size from event counts and desired precision,
not frame count. Patient complications and postoperative outcomes are separate
targets requiring separately linked labels.

If genuine pre-onset information is weak or events are too sparse, retain
honest real-time detection plus abstention or procedural anticipation. A null
anticipation result with strong evaluation can be valuable, but it is not
automatically a top-tier journal paper.

#### Publication ladder and evidence needed

These are proposed editorial-fit judgments, not journal requirements or
promises of acceptance. “Physical AI” is interpreted as a research direction.

| Target | Strongest contribution for that audience | What we still need |
|---|---|---|
| Medical Image Analysis / IEEE TMI | Generalizable technical method for surgical video and temporal risk | New method, strong ablations, independent validation and uncertainty; more than a backbone swap |
| npj Digital Medicine | Clinically meaningful assistance with convincing validation | Defined user/decision, independent cohort, reader or prospective evaluation where feasible |
| Nature Biomedical Engineering | Substantial engineering advance with compelling biomedical function | Multicenter evidence plus functional/experimental or clinical validation appropriate to the claim |
| Nature Machine Intelligence | General learning principle about uncertainty, anticipation, or embodiment | Evidence extending beyond one narrow procedure/task; a broadly useful method |
| Science Robotics | Advancement in embodied control, manipulation, recovery, or shared autonomy | Closed-loop physical task experiments, perturbations, generalization and failure recovery |
| MICCAI / IJCARS | Rigorous focused technical surgical study | Achievable intermediate publication if the larger clinical/robotics package is not ready |
| npj Digital Surgery / npj Robotics | Specialized digital-surgery or robotics contribution | Assess scope and paper strength; Nature Portfolio branding alone does not establish equivalence to flagship journals |

For clinical assistance, a controlled retrospective reader study is a useful
next layer: unaided versus AI-assisted review with randomized order and
control for case familiarity, measuring accuracy, review time, workload,
and inappropriate reliance. It is not evidence that patient complications
decrease. Prospective live evaluation should use appropriate reporting such
as [DECIDE-AI](https://www.nature.com/articles/s41591-022-01772-9).
The [npj Digital Medicine scope](https://www.nature.com/npjdigitalmed/aims)
and [npj Robotics scope](https://www.nature.com/npjrobot/aims) help distinguish
clinical digital tools from embodied systems.

#### Physical AI: a feasible bridge, after the video study

The next robotics question could be **when should a surgical robot continue,
pause, or request help under uncertain tissue/tool state?** Reuse the learned
state and uncertainty model, then add action-conditioned dynamics and recovery.
Select one bench task, such as needle transfer or suturing, with a collaborator
who can supply the platform and synchronized demonstrations.

Record camera timestamps/calibration, tool pose and gripper state, commanded
actions versus executed motion, latency, interventions, success/failure,
and contact/force if physically measured. Video alone does not reveal reliable
force; a descriptive action triplet is not a robot control command. A valid
trajectory predictor is not yet a patient-specific digital twin.

Prototype in an existing simulator rather than building one from scratch.
The dVRK documentation lists AMBF, Isaac-based environments, and SurRoL.
Simulator realism and sim-to-real validity must be measured for the task;
OpenUSD scene formatting alone contributes no validated tissue dynamics.
[dVRK simulation resources](https://dvrk.readthedocs.io/main/pages/usage/simulation.html)

Evaluate closed-loop success, recovery, contact/force violations where
measurable, latency, and human interventions on held-out variations. Image
quality metrics alone do not establish useful robot behavior. Physical AI
emphasizes action and adaptation, consistent with the recent
[Nature Machine Intelligence editorial](https://www.nature.com/articles/s42256-026-01239-3).

#### Funding strategy matched to the actual research

**Commercialization objective confirmed September 17:** the user wants to
remain an independent researcher, build a sellable product, and does not
want a postdoctoral or faculty career path. The strategy is founder-led
research → validated prototype → commercial pilots → a business capable of
selling the product. Academic appointments are not a project milestone.

**Proposed first product:** a retrospective surgical-video review tool for
research/training teams: locate steps and candidate events, attach timestamps
and evidence clips, let qualified reviewers correct outputs, and export
structured annotations. This is a product hypothesis, not verified customer
demand. First interview potential buyers about review time, current tools,
budget ownership, data access, and willingness to pay. Measure time saved
at matched review quality; do not sell an unvalidated prediction as clinical
safety guidance. Real-time anticipation remains the research contribution
and a possible later product capability.

**Commercial rights are a concrete project dependency:** the official
[MB140 repository](https://github.com/CAMMA-public/MultiBypass140) describes
its code, models, and datasets as non-commercial scientific research under
CC BY-NC-SA 4.0. Public availability is not commercial permission. Confirm
the permitted scope of company-sponsored R&D, derived models, redistribution,
and paid deployment before each use; obtain appropriate permissions or use
a commercially licensed replacement. Audit backbone weights separately.
Do not assume publishing a paper or retraining a head removes restrictions.

Maintain provenance for research versus commercial assets. Before releasing
code/checkpoints or entering a collaboration, document authorship, ownership,
licenses, and commercialization rights, including any obligations from work
performed using institutional resources. OpenSurgics can publish benchmarks,
interfaces, and selected tools while a business sells authorized software,
hosting, integrations, or support. Open-source releases cannot promise
exclusivity over rights already granted to recipients.

**Funding priorities for this founder path:**

1. Independent seed support and customer discovery now; a narrowly scoped
   paid pilot once rights and an actual buyer are established. No customer
   interest or revenue is assumed yet.
2. **NSF SBIR:** investigate a Project Pitch for a differentiated technical
   innovation with commercial potential. A full proposal requires invitation;
   an award requires an eligible small business, with ownership and PI
   employment requirements. The NSF eligibility page specifies primary
   employment of more than 50% with the company. It is not a direct
   individual grant. [Pitch process](https://seedfund.nsf.gov/apply/project-pitch-information/),
   [eligibility](https://seedfund.nsf.gov/solicitation-eligibility/).
3. **NIH SBIR:** evaluate an appropriate active small-business opportunity
   once the company, clinical problem, permissions, and prototype are ready.
   STTR is an alternative if a formal research-institution partnership is
   desirable; it is not a reason to pursue a postdoc. Confirm exact call
   rules rather than assuming either route is eligible.
   [Current NIH small-business opportunities](https://seed.nih.gov/small-business-funding/find-funding/sbir-sttr-funding-opportunities).
4. Treat open-source grants as conditional: their required releases must
   match the intended business model. NLnet's current funding page says
   Restack generally excludes AI-related projects; it is not a primary
   source for funding this surgical model.
   [Current fund descriptions](https://nlnet.nl/funding.html).

Before choosing a company-grant application, check location, ownership,
employment, and proposal requirements. Forming a company does not itself
establish grant eligibility or clinical-data rights. This plan does not
authorize incorporation, public release, outreach, or submission.

**Applicant correction, September 17, 2026:** the user is not faculty and
wants to apply as an **independent individual researcher**, with an existing
collaborator. Do not assume UCSC is the applicant or that the user has faculty
PI eligibility. The institutional programs below are conditional future
routes, not the immediate individual-applicant shortlist.

**Individual-first shortlist:**

| Route | What is verified | Fit for OpenSurgics |
|---|---|---|
| [Emergent Ventures](https://www.mercatus.org/emergent-ventures) | Grants/fellowships supporting individuals with scalable ideas; active application link | Best exploratory individual seed-grant lead among those reviewed: a bounded open surgical-AI pilot with clear public benefit. Not a dedicated biomedical funding call or a guaranteed award |
| [NLnet](https://nlnet.nl/funding.html) | Individuals can apply in principle; each fund has additional requirements | Conditional fit for reusable open-source infrastructure, interoperability, or privacy tooling. Pure surgical prediction research is not automatically within scope; verify current fund, geographic/European-dimension requirements, and eligible work before preparing an application |
| [Experiment](https://experiment.com/start) | Explicitly welcomes independent scientists | Crowdfunding a small annotation/reproducibility pilot; not a conventional grant or guaranteed funding. Account, payout-country and project-review rules apply |

**Compute nuance:** not being faculty is different from being unaffiliated.
ACCESS explicitly allows qualifying instructors/adjuncts, but excludes
unaffiliated individuals from both leading and joining allocations. The
user's UCSC teaching relationship may matter if it constitutes an eligible
current appointment; verify it without assuming faculty status. Do not
promise access through a collaborator as a workaround to user eligibility.
[Current ACCESS policy](https://allocations.access-ci.org/allocations-policy)

**Conditional organization-backed route:** NIH R21 does not itself require
a faculty title; it invites qualified individuals to work with an eligible
applicant organization. An eligible host may potentially appoint the user
as PI or include them in an agreed research role, subject to its policies.
That is different from applying directly as a private individual. A
collaborator alone does not establish the necessary organizational support.
[R21 eligibility](https://grants.nih.gov/grants/guide/pa-files/PA-25-304.html)

NVIDIA's faculty-only academic program is not a direct option under the
user's stated status. NSF/NIH institutional applications, NAIRR resource
access, and any fiscal-host arrangement require separate eligibility checks.
Do not create an entity or assume fiscal sponsorship resolves those rules.

The following table is retained as an **organization/eligible-host funding
map**, with scientific fit separated from personal eligibility:

| Priority / timing | Route | What to propose | Verified constraint |
|---|---|---|---|
| First cash-grant option; next new-app date Oct 16, 2026 or Feb 16, 2027 | NIH NIBIB Parent R21, PA-25-304 | Retrospective, uncertainty-aware event anticipation with rigorous center-transfer validation | NIBIB participates; up to $275k direct over two years, ≤$200k in one year; clinical trial not allowed. Prefer February if October would require rushing. [NOFO](https://grants.nih.gov/grants/guide/pa-files/PA-25-304.html) |
| Smaller pilot; same standard new-app cycle | NIH Parent R03, PA-25-302 | Annotation/provenance audit and a focused feasibility study | NIBIB participates; $50k direct/year, up to two years; clinical trial not allowed. [NOFO](https://grants.nih.gov/grants/guide/pa-files/PA-25-302.html) |
| Compute support; call-specific dates | NVIDIA Academic Grant Program | Measured feature-extraction/adaptation or simulation workload | In-kind resources, not salary cash. Applicant must be full-time faculty at an eligible PhD-granting institution; software/model requirements apply. Confirm current call and award schedule. [Program](https://www.nvidia.com/en-us/industries/higher-education-research/academic-grant-program/) |
| Compute support; allocation-specific | NSF NAIRR resources | Reproducible trustworthy-AI/health research workloads | Resource access rather than unrestricted cash. Program is active; current allocation dates and account eligibility must be checked at application. [NSF update](https://www.nsf.gov/cise/updates/nairr-2-years-advancing-american-artificial-intelligence) |
| March 2, 2027 | NSF PESOSE Track 1 | OpenSurgics governance, users, contributors, and sustainability around the released benchmark/tool | Up to $300k; requires an existing public open-source product. Track 1 funds ecosystem planning, not initial product development; appointment criteria apply. [Solicitation](https://www.nsf.gov/funding/opportunities/pesose-pathways-enable-secure-open-source-ecosystems/nsf26-506/solicitation) |
| Once the robotics branch is real; proposals accepted anytime | NSF Foundational Research in Robotics | General safe/shared autonomy with physical validation | Must address robotics research; a video-only risk predictor is insufficient. EAGER requires prior program-officer contact. [Program](https://www.nsf.gov/funding/opportunities/frr-foundational-research-robotics) |
| Monitor, not an active deadline commitment | NSF Smart Health | Fundamental AI plus clinical problem and interdisciplinary team | Current program page says “Waiting for new publication.” Do not reuse old solicitation dates. [Program](https://www.nsf.gov/funding/opportunities/sch-smart-health-biomedical-research-era-artificial-intelligence) |
| Longer-term team opportunity | ARPA-H AIR / subsequent relevant calls | Autonomous interventions and clinically grounded robotics | AIR already lists awardees and an Aug 2026 funding announcement; evidence of federal investment, not a verified open call for this project. [Program](https://arpa-h.gov/explore-funding/programs/air) |
| Future relevant solicitation only | CDMRP CRRP | Trauma/austere-care decision support with the necessary data and operational partners | FY26 preproposal Aug 17 has passed; Nov 18 full-app date does not reopen entry. FY27 timing and terms are unverified. [FY26 program](https://cdmrp.health.mil/funding/crrp) |

Proposed R21 aims: (1) reconstruct and validate event/step labels and a
leakage-audited benchmark; (2) develop calibrated forecasting that can abstain;
(3) test generalization and failure modes across centers. A future prospective
or randomized human study needs its clinical-trial classification assessed
before choosing a funding announcement. Do not assume a reader study is
automatically outside NIH's clinical-trial definition.

The prior OpenSurgics grant inventory includes other large opportunities;
their presence does not imply fit or readiness. Prioritize one scientific
proposal, one resource-allocation request, and a later ecosystem proposal
with distinct costs and aims. Funding direction should follow validated need,
not relabel bariatric video as military trauma or robotic control.

#### Next 90 days and compute decision

| Window | Work and decision |
|---|---|
| Sep 17–30 | Locate corrected source annotations and video roots; recover event/step fields; count event onsets, severities, and unknowns per center; establish operation-level overlap map |
| Oct 1–15 | Collaborator reviews an initial sample if clinically qualified; otherwise recruit qualified review before clinical claims. Freeze one endpoint and build elapsed-time/phase baselines |
| Oct 16–Nov 15 | Small frozen-feature pilot, calibrated on development cases; assess event counts, false alarms, and true warning time. Decide whether anticipation is identifiable before scaling |
| Nov 16–Dec 15 | Confirmatory comparisons, untouched-center evaluation where feasible, complete draft and February R21 aims; plan reader study only if participants/access exist |
| Jan–Feb 2027 | MICCAI-ready study or expanded journal submission depending on actual evidence; institutional grant preparation; public benchmark release when permitted |

No new GPU is needed for the immediate label, split, endpoint, and provenance
work. For the first video pilot, provisionally plan **one 24–48 GB GPU** for
small/frozen encoders and heads, pending a measured batch-memory test. Larger
encoders or adaptation may justify **80 GB**; do not purchase a multi-GPU
world-model run now. These are planning ranges, not benchmarked requirements.
Measure extraction time, head-training time, storage, and provider rate before
quoting total cost. Annotation quality, independent validation, and access
are more limiting than compute at this stage.

The immediate implementation priority changes from expanding the backbone
matrix to recovering richer labels and proving that one safety endpoint is
measurable. Keep the tested RSD/representation infrastructure as the baseline.
Freeze a revised experiment manifest only after that audit; the existing
63-run draft is not automatically the safety-study protocol.

## Historical execution plan — retained for reference

The material below predates the September 17 update. Its deadlines,
budgets, narrative choices, and outstanding-work lists are superseded
where they conflict with the current plan above.

*Companion to `NEXT_PAPER_BRIEF.md`. Concrete schedule, milestones,
deliverables, decision gates, and risk responses for the two-paper
program.*

---

## 0. Snapshot

| | Paper 2A | Paper 2B |
|---|---|---|
| **Working title** | *Do World Models Help Surgical Workflow Forecasting? A Causal Benchmark for Remaining Duration and Phase Anticipation* | *Closing the Oracle Gap in Workflow-Conditioned Surgical Forecasting via Privileged-Information Distillation* |
| **Thesis** | Causal evaluation under workflow variability re-ranks foundation models for surgical forecasting | A student model that learns the workflow posterior from a privileged teacher closes the oracle-to-deployable gap |
| **Primary venue** | MICCAI 2027 | NeurIPS 2027 |
| **Backup venue** | CVPR 2027 (if scout matrix ready by late-2026) | ICLR 2027 (only if essentially done by Aug 2026) / MICCAI 2027 |
| **Compute (realistic)** | ~1,500–3,200 GPU-h ($4.5K–$9.6K) | ~750–1,500 GPU-h ($2.3K–$4.5K) |
| **Submission target** | Feb/Mar 2027 (MICCAI 2027) | May 2027 (NeurIPS 2027) |

---

## 1. The four-phase plan

### Phase 0 — Foundation & feasibility (2026 Q3, Jun–Sep)

**Goal:** know exactly which backbones can run, on what hardware, with
what cost, before committing to any matrix.

**Deliverables:**

- `docs/backbone_feasibility_matrix.md` — one row per candidate model
  with weights URL, license, preprocessing, expected feature shape,
  cache size, throughput, pass/fail.
- `backbone_features` extraction interface with caching support.
- `evaluate_phase_anticipation.py` strict prefix-only evaluation for
  next-transition time and future-phase-sequence tasks.
- Reproduction of current ViT-B/16 RSD numbers from the submitted paper,
  verified against the cached checkpoints.
- Smoke test on 100 clips for each candidate backbone.

**Decision gates:**

- D0.1: Cosmos-Predict2 (or 2.5) weights obtainable and runs on GH200?
- D0.2: V-JEPA 2 / 2.1 weights obtainable and runs on GH200?
- D0.3: At least one surgical-native FM (SurgMotion, SurgVISTA, ZEN, or
  EndoMamba) has releasable weights and runs?
- D0.4: All accepted backbones produce feature tensors consumable by
  the current temporal head through a simple projection?

If <2 backbones pass, narrow the scope to "ViT vs. one stronger
backbone" and treat Paper 2A as a methodological-evaluation paper
rather than a full transfer matrix.

**Compute cost:** ~40–80 GPU-h (~$250).

### Phase 1 — Scout matrix (2026 Q4, Oct–Nov)

**Goal:** determine whether Paper 2A *exists* — i.e., does any
foundation model meaningfully change the outcome under causal
evaluation?

**Scope:**

- 4–5 accessible backbones (ViT-B/16, VideoMAE/TimeSformer, V-JEPA 2.x,
  one surgical-native FM, optionally Cosmos).
- 3 settings: **MB140 5-fold**, MB140 cross-center, Cholec80.
- **3 conditions**: no-token, decoupled-R1 (legacy k-means cluster id),
  decoupled-R3 (continuous HMM posterior).
- **1 seed** per (backbone, setting, condition, fold).
- RSD + one anticipation task (time-to-next-transition recommended for
  Phase 1).

**Total runs:** 5 × (5 folds + cross-center + Cholec80) × 3 = **105
trained-head runs**. If the budget binds, drop a backbone before dropping
folds or the R3 arm.

> **Revised 2026-08-08 following the Phase 0 fold-variance analysis**
> ([PHASE_0_FINDING_FOLD_VARIANCE.md](phase_0/PHASE_0_FINDING_FOLD_VARIANCE.md)).
> The original scope was *MB140 fold-0 × 2 seeds*. On Paper 1's own
> five-fold data, 98% of the paired effect's variance is between-fold and
> only 2% is between-seed, so a fold-0 design has SE ≈ 0.42 min on the
> effect while a 5-fold × 1-seed design has SE ≈ 0.19 min for a similar
> run count. The old design could not decide its own D1.1 gate: a 0.3-min
> threshold sat inside one standard error, so finalists would have been
> selected largely by noise and Phase 2 would have spent 250–400 runs
> confirming that selection. Seeds buy almost nothing here (3× the seeds
> reduces SE by 1%); folds are what buy power. If the budget binds, drop
> a backbone rather than drop folds.
>
> The third conditioning arm comes from the second Phase 0 finding
> ([PHASE_0_FINDING_REPRESENTATION.md](phase_0/PHASE_0_FINDING_REPRESENTATION.md)):
> Paper 1's k-means cluster id is unstable to the random seed alone
> (ARI 0.63 on MB140) and is not recovered by an independent
> representation family (ARI 0.03–0.08). Carrying a continuous HMM
> posterior alongside the legacy cluster id tests whether a stable
> conditioning signal produces a stable conditioning effect — which is
> the mechanism question underneath both findings.

**Decision gates:**

- D1.1: At least one non-ViT backbone beats the ViT baseline on causal
  RSD on MB140 by **either** ≥ 0.5 min mean across folds, **or** ≥ 0.3
  min mean with the sign consistent on ≥ 4 of 5 folds; or improves
  transition anticipation MAE by ≥ 0.5 min. → continue to Phase 2.
  *(The sign-consistency clause is the check Paper 1 failed — it costs
  nothing extra once 5 folds are being run, and it is what separates a
  real transfer effect from a fold-dependent one.)*
- D1.2: All foundation models perform similarly to ViT, but pixel-
  prediction-quality-vs-downstream correlation is informative? →
  switch to the *Cosmos-is-meh* diagnostic-paper framing as the
  primary contribution (pre-registered narrative).
- D1.3: All foundation models perform worse than ViT? → publish as a
  systematic negative-result methods paper; smaller scope.

**Reporting requirement (all gates):** every backbone's row must carry
its interaction/condition ratio from `fold_stability.py`. A ratio above
1 means the number is describing fold-dependence rather than a transfer
effect, and must be reported as such rather than as a headline gain.

**Compute cost:** ~350–600 GPU-h (~$1,050–$1,800).

### Phase 2 — Paper 2A confirmatory experiments (2026 Q4 – 2027 Q1, Nov–Feb)

**Goal:** lock the reviewer-facing matrix for Paper 2A.

**Scope:**

- 3 finalist backbones from Phase 1.
- 5-fold MB140 + cross-center + Cholec80.
- 4 conditions: no-token, retrospective oracle, decoupled-oracle,
  shuffled-token.
- 3 seeds.
- RSD + Task A (next-transition time) + Task B (future-phase-sequence).
- Task C (CholecT50 triplet anticipation) as a stretch if compute
  allows.
- Pixel-prediction-quality measurement (FVD, LPIPS, PSNR on held-out
  surgical video) for the Cosmos-meh diagnostic figure.

**Total runs:** ~250–400 trained-head runs.

**Decision gates:**

- D2.1: All four claims in Paper 2A defensible (FM ranking changes
  under causal eval; pixel ≠ downstream; variability scaling
  generalizes; cross-center robustness varies by backbone)? →
  proceed to writing.
- D2.2: Fewer than three claims defensible? → reduce scope to a
  Paper 2A-lite (3 claims, MICCAI fallback).

**Deliverables:**

- Locked transfer-matrix table.
- Pixel-quality-vs-downstream scatter plot.
- Variability-scaling curve across tasks.
- Cross-center robustness analysis.

**Compute cost:** ~700–1,400 GPU-h (~$2,100–$4,200).

### Phase 3 — Paper 2A writing + Paper 2B parallel start (2027 Q1, Jan–Mar)

**Goal:** submit Paper 2A; start Paper 2B experiments while writing.

**Paper 2A track:**

- Draft Paper 2A by mid-Feb 2027.
- Internal review by end-Feb.
- Submit to MICCAI 2027 (~Mar deadline).
- Optional CVPR 2027 backup if MICCAI rejects and CVPR deadline is open.

**Paper 2B track (parallel):**

- Implement teacher-student framework: privileged teacher producing
  oracle cluster + ground-truth phase predictions, student
  *q_φ(z | x_{≤t})* head with KL-style distillation.
- Run primary student on MB140 5-fold + cross-center + Cholec80, 3
  seeds, 3 distillation-loss variants.

**Compute cost:** ~500–1,200 GPU-h (Paper 2A adapter runs if applicable
+ Paper 2B primary distillation).

### Phase 4 — Paper 2B experiments + writing (2027 Q2, Apr–May)

**Goal:** complete Paper 2B and submit.

**Scope:**

- Primary distillation result on MB140 within-center.
- Cross-center transfer test.
- Cholec80 null preservation check.
- Calibration analysis (reliability diagrams, ECE).
- Encoder-swap ablation (ViT → V-JEPA 2.1 / SurgMotion if Phase 2 winner
  is encoder-agnostic).
- Teacher-choice and loss-variant ablations.

**Decision gates:**

- D4.1: Distillation closes ≥ 50% of the oracle-to-deployable gap on
  MB140 (i.e., ≥ −0.5 min gain vs. the deployable baseline's −0.18
  min)? → strong NeurIPS / ICLR claim.
- D4.2: Distillation closes 25–50% of the gap? → moderate claim,
  consider MICCAI 2027 fallback as primary venue.
- D4.3: No gap closing? → publish as a careful negative result; smaller
  scope, MICCAI 2027 workshop track.

**Deliverables:**

- Locked oracle-gap-closing result.
- Calibration plot.
- Variability-scaling-preserved figure.
- Ablation grid.
- Submit to NeurIPS 2027 (~May deadline).

**Compute cost:** ~250–500 GPU-h.

---

## 2. Workstreams

The plan has five parallel workstreams that touch both papers:

### Workstream A — Feature extraction infrastructure

- `backbone_features/extract.py` with one entry point per backbone.
- Feature caching to `lambda_mirror/features/{backbone}_{dataset}_{fold}/`.
- Per-clip feature tensor shape conversion to a unified format the
  temporal head can consume.
- Memory-mapped loader for fast batched training.

### Workstream B — Causal anticipation evaluators

- `evaluate_phase_anticipation.py` for next-transition-time and
  future-phase-sequence.
- `evaluate_action_anticipation.py` for CholecT50 triplets (Phase 2
  stretch).
- All evaluators must respect strict prefix-only protocol.

### Workstream C — Distillation training pipeline

- Teacher: frozen current decoupled-oracle model.
- Student: same architecture but with workflow posterior head
  *q_φ(z | x_{≤t})* derived from pixels only.
- Loss combination: RSD MSE + phase CE + KL distillation + optional
  calibration regularizer.
- YAML-configured distillation variants.

### Workstream D — Statistics and reporting

- Paired bootstrap over videos.
- Per-fold reporting with appendix table generation.
- Pixel-prediction quality (FVD/LPIPS/PSNR) computation.
- Calibration metrics (reliability diagram, ECE).

### Workstream E — Paper writing

- Paper 2A LaTeX skeleton ready by Phase 2 mid-point.
- Paper 2B LaTeX skeleton ready by Phase 4 start.
- Figure generation scripts (matplotlib) versioned with the data.

---

## 3. Milestones (Gantt-style)

```
                        2026                              2027
            Jun  Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb  Mar  Apr  May  Jun
Phase 0     |==========|
Phase 1               |==========|
Phase 2                    |================|
Paper 2A write                              |======|
Paper 2A submit                                    *MICCAI
Phase 2B prep                                |========|
Phase 4                                           |==========|
Paper 2B submit                                            *NeurIPS
```

Key dates:

- **2026 Aug 31** — feasibility audit complete; all backbone status
  documented.
- **2026 Nov 30** — Phase 1 scout matrix complete; Paper 2A go/no-go.
- **2027 Feb 15** — Phase 2 confirmatory experiments locked.
- **2027 Mar 15** — Paper 2A submitted to MICCAI 2027.
- **2027 May 15** — Paper 2B submitted to NeurIPS 2027.

---

## 4. Innovation and contribution (what makes each paper publishable)

### Paper 2A — Innovation

1. **First causal evaluation protocol for surgical-video foundation
   models.** Existing FM papers (SurgMotion, SurgVISTA, ZEN) report
   centered-window or aggregate metrics. None evaluate under strict
   prefix-only protocols that match deployment.

2. **First systematic transfer matrix that includes physical-AI world
   models alongside surgical-native FMs.** Most surgical-AI papers
   compare ImageNet vs. video-MAE; none have tested Cosmos-style
   physical-AI world models head-to-head against domain-specialized
   surgical FMs.

3. **First diagnostic showing that pixel-prediction quality is a weak
   proxy for downstream surgical forecasting.** This is a measurement
   contribution to the broader world-model field, not just surgical
   AI.

4. **First multi-task variability-scaling extension.** The current
   paper proves the *H(z)* pattern on scalar RSD; Paper 2A extends to
   phase anticipation and future-sequence prediction, demonstrating
   the pattern is task-general.

### Paper 2A — Contribution

- A reusable causal-anticipation benchmark for surgical forecasting,
  released as code + evaluation harness + leaderboard.
- A measurement protocol the surgical-AI community can adopt.
- Clear recommendations for which foundation-model family to invest in
  for surgical-forecasting research.
- A model-card-style summary of foundation-model performance on
  surgical anticipation, with strict causal scoring.

### Paper 2B — Innovation

1. **First privileged-information distillation framework for surgical
   workflow conditioning.** Existing LUPI work in medical AI focuses
   on classification or detection; none target workflow-posterior
   distillation for forecasting.

2. **Closes the oracle-to-deployable gap.** The current paper shows
   −0.85 min with oracle and only −0.18 min deployable. Paper 2B's
   target is ≥ −0.5 min deployable — a measurable, defensible advance.

3. **Encoder-agnostic.** The distillation method works on top of any
   visual backbone; tested on ViT, V-JEPA 2.1, and surgical-native
   features.

4. **Preserves variability scaling.** Distillation doesn't manufacture
   gains on workflow-homogeneous Cholec80; the *H(z)* pattern is
   preserved, demonstrating the method exploits real signal rather
   than parameter capacity.

### Paper 2B — Contribution

- A reusable distillation recipe for closing oracle gaps in workflow-
  conditioned prediction tasks.
- A calibrated workflow posterior *q_φ(z | x_{≤t})* useful for
  downstream surgical tasks beyond RSD.
- An ablation map showing which teacher signals and which loss
  formulations matter most.
- Deployable predictor that approaches the privileged-supervision
  upper bound under deployment-relevant protocols.

---

## 5. Combined contribution (what the two papers buy the field together)

| Question the field has | What the two papers answer |
|---|---|
| Do video / world FMs help surgical forecasting? | Yes/no/conditional, with quantitative evidence (Paper 2A) |
| Is generative pixel quality a good proxy for downstream surgical understanding? | No — the proxy is unreliable; use causal anticipation metrics (Paper 2A) |
| How do we measure surgical-FM transfer fairly? | Strict prefix-only protocol + workflow-variability stratification (Paper 2A) |
| Can a deployable predictor recover the oracle's workflow-conditioning gain? | Mostly yes, via privileged-information distillation (Paper 2B) |
| Does workflow conditioning still matter when we have stronger backbones? | Yes when *H(z)* is high; no when *H(z)* is low — pattern is backbone-independent (both papers) |

Together they:

- Establish a measurement protocol the surgical-AI community can adopt.
- Re-rank the FM landscape under deployment-relevant conditions.
- Provide a method that closes the gap between privileged-supervision
  upper bounds and deployable models.
- Generalize the variability-scaling thesis from the current paper.

---

## 6. Risk register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Cosmos doesn't transfer to surgical video | High | Medium | Pre-register *"pixel-prediction is a weak proxy"* diagnostic narrative (§8 of brief). Paper still ships. |
| Surgical-native FM weights unavailable | Medium | Medium | Use ZEN, EndoMamba, or pretrain a small surgical FM ourselves on combined corpora. |
| Anticipation evaluator harder than expected | Medium | Low | Defer Task C (action triplets) to a follow-up paper. Stick with Tasks A and B. |
| Compute over budget | Medium | Medium | Decision gates at end of each phase. Stop after Phase 1 if no signal. |
| Paper 2A rejected at MICCAI 2027 | Medium | Low | Backup to CVPR 2028 or MICCAI workshop; revise based on reviewer feedback. |
| Distillation gap-closing fails | Low | High | Publish as negative result; pivot to systematic study of *why* the gap is hard to close. |
| New surgical-FM paper scoops Paper 2A | High | Medium | The causal-evaluation contribution survives scooping; reposition as the diagnostic / measurement paper rather than the first-mover paper. |

---

## 7. Concrete deliverables checklist

### By end of Phase 0 (2026 Aug 31)

- [ ] `docs/backbone_feasibility_matrix.md` populated with all candidate
      backbones.
- [ ] `backbone_features/extract.py` working for ViT-B/16 and at least
      2 other backbones.
- [ ] `evaluate_phase_anticipation.py` implemented and tested.
- [ ] Reproduction of current paper's ViT-B/16 RSD numbers verified.
- [ ] Phase 0 status report committed to the repo.

### By end of Phase 1 (2026 Nov 30)

- [ ] Phase 1 scout matrix complete with all numbers in
      `paper2/scout_results.json`.
- [ ] Phase 1 status report with go/no-go recommendation.
- [ ] Pre-registered narrative selection (positive vs. Cosmos-meh
      diagnostic) committed.

### By end of Phase 2 (2027 Feb 15)

- [ ] All Paper 2A experiments complete; results in
      `paper2/confirmatory_results.json`.
- [ ] Paper 2A LaTeX draft v1 ready for internal review.
- [ ] All figures generated by versioned scripts in
      `paper2/figure_scripts/`.

### By Paper 2A submission (2027 Mar 15)

- [ ] Paper 2A submitted to MICCAI 2027 or CVPR 2027.
- [ ] Supplementary material packaged.
- [ ] Code release candidate ready.

### By end of Phase 4 (2027 May 15)

- [ ] Paper 2B experiments complete.
- [ ] Paper 2B LaTeX draft ready.
- [ ] Paper 2B submitted to NeurIPS 2027.

---

## 8. Resource summary

| Resource | Paper 2A | Paper 2B | Combined |
|---|---|---|---|
| Compute (realistic GPU-hours) | 1,500–3,200 | 750–1,500 | 2,250–4,700 |
| Compute ($ at $3/H100-h) | $4,500–$9,600 | $2,250–$4,500 | $6,750–$14,100 |
| Compute (with 25% overhead) | — | — | $8,400–$17,700 |
| Compute (full upper bound) | — | — | $15,000–$21,000 |
| Storage (feature cache + outputs) | ~3 TB | ~1 TB | ~4 TB |
| Engineer-months (one person) | 5–6 | 3–4 | 8–10 |
| Calendar months | 9 | 5 | 11–12 |

---

## 9. What to do this week

1. Read this plan + the brief, decide go/no-go on the two-paper split.
2. If go, open `docs/backbone_feasibility_matrix.md` and start
   populating with candidate backbones.
3. Reach out for surgical-FM weight access (SurgMotion, SurgVISTA, ZEN,
   EndoMamba authors via HuggingFace + GitHub if not already public).
4. Schedule the Phase 0 work (~6 weeks) with a calendar reservation
   for the Phase 1 go/no-go review.
5. Apply the UniSurg → SurgMotion correction from the brief review
   (the only factual error in the previous version).

— *End of plan.*

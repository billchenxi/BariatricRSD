# BariatricRSD — Strategy

**Single authoritative planning document.** Consolidated September 17, 2026
from seven overlapping memos: `NEXT_PAPER_BRIEF.md`, `NEXT_PAPER_PLAN.md`,
`NEXT_PUBLICATIONS.md`, `PAPER_2A_REVIEWER_HARDENING.md`,
`DIRECTION_AND_FUNDING_2027.md`, `archive/NEXT_PAPER_PHYSICAL_AI.md`,
`archive/NEXT_PAPER_REFINEMENTS.md`, and `grants/cdmrp_fy27_path.md`. The
originals are in git history at commit `58c99bc` if anything here needs to
be checked against its source.

Still separate, deliberately: `phase_0/` (evidence, cited by the README),
`SESSION_LOG.md` files (history), `paper1_neurips2026/` (closed track),
`runbooks/` (operational).

> **Reading order.** Parts I–III are the current decision. Part IV is the
> scientific program. Part V is the evidence it rests on. Part VI is
> history, retained because the reasoning is still useful, not because the
> dates or budgets are current.

---

## Unresolved conflicts — read before relying on anything here

These are genuine contradictions between source documents. They are
recorded, not resolved, because resolving them needs information not in
the repository.

| Question | Conflict | How to settle it |
|---|---|---|
| **Was Paper 1 accepted?** | `README.md` (Aug 10) says "Submitted; awaiting notification (Sept 2026)". `PAPER_2A_REVIEWER_HARDENING.md` (Jun 4) opens "immediately after the **NeurIPS 2026 rejection** of Paper 1". `NEXT_PAPER_PLAN.md` notes the conflict without resolving it. | Check the OpenReview record for submission #706. Do not cite Paper 1 as accepted or rejected until you have. |
| **PI eligibility / appointment** | `cdmrp_fy27_path.md` asserts PhD-student status categorically; a later header retracts that as unsupported; `NEXT_PAPER_PLAN.md` says teaching at UCSC establishes neither. | **Largely moot now** — see Part I. Matters only for STTR and for collaborator-held grants. |
| **MB140 phase count** | Paper 1 and the README use **14 phases**. The official CAMMA repository documents **12 phases and 46 steps**. | Recover the corrected source annotations (Part IV.1). This is part of the label audit, not a separate task. |
| **Dataset availability** | README: raw MB140/Cholec80 frames died with the Lambda filesystem June 2026. `lambda_mirror/` holds outputs, logs, labels — enough to reproduce reported *numbers*, not to retrain. | Re-acquisition required before any feature extraction. Cholec80 needs a fresh CAMMA DUA. |

---

# Part I — The goal, and what it changes

**Stated September 17, 2026: independent research, not a postdoc or
faculty track, with the eventual aim of selling a product.**

This inverts most of the planning that preceded it. Every earlier funding
memo in this repository assumed an academic PI applying through an
eligible institution. Under the new goal:

| Stops mattering | Starts mattering |
|---|---|
| Academic PI eligibility | Dataset licensing (Part III.1) |
| Fellowships, R-series, CDMRP | IP ownership (Part III.4) |
| Publication as career currency | FDA device classification (Part III.3) |
| Institutional affiliation | Who the buyer is, and their budget |

Papers are still worth writing. Their role changes: a publication is now
the **credibility asset that makes a service sellable**, not a line on a
CV. "The person who showed these benchmarks don't replicate" is a position
you can charge for; "a person with a startup" is not.

---

# Part II — Strategic context

## II.1 Bariatric surgery is a shrinking procedure

This is a market risk to the framing, and it is not written down anywhere
else in the repository.

- US metabolic/bariatric volumes fell after a 2022 peak, ending seven
  years of growth. Reported declines vary by denominator: roughly **23%
  from 2022–2024**, with some analyses reporting **~39% through Q4 2025**.
  ([ASMBS 2026 coverage](https://www.medscape.com/viewarticle/glp-1-uptake-rises-metabolic-surgery-rates-decline-2026a1000fg5),
  [Harvard Chan](https://hsph.harvard.edu/news/bariatric-surgeries-on-the-decline-as-use-of-glp-1-drugs-rises/),
  [utilization study](https://pubmed.ncbi.nlm.nih.gov/42467193/))
- GLP-1 prescribing for obesity roughly **doubled 2022–2023** and kept
  climbing through 2024.
- **Semaglutide lost patent exclusivity in March 2026.** Generic entry and
  30–50% price declines plausibly intensify the pressure on elective
  surgical demand.

**Consequences:** "improve OR throughput for gastric bypass" is a weak
2027 pitch. MB140 is a fixed historical cohort, not one that will grow.
Reviewers and investors will raise GLP-1 unprompted, so address it in one
sentence rather than waiting. Bariatric-specific funders (ASMBS, NIDDK
obesity) face the same headwind.

**The reframe that survives it:** bariatric video is the *substrate*, not
the *subject*. The scientific object is procedural-workflow measurement
and calibrated anticipation under center shift — demonstrated on gastric
bypass because MB140 is the best-annotated two-center cohort that exists.
Cholecystectomy (Cholec80, Endoscapes, CholecT50, SAGES CVS) is the
volume-stable general-surgery anchor and should carry equal framing
weight. Apply this to titles, aims, and company naming.

## II.2 The three data layers

The bottleneck is not encoder quality or compute. Every asset is in one
layer — pixels plus workflow labels. Each journal tier corresponds to
adding a layer.

```
  Layer C   Action / physics      tool pose, kinematics, force, commanded vs executed
            ─────────────────────────────────────  Science Robotics, Nature BME
  Layer B   Patient / outcome     30-day complications, reoperation, readmission
            ─────────────────────────────────────  Nature Medicine, Annals, NEJM AI
  Layer A   Context               audio, room video, device telemetry, vitals, EHR
            ─────────────────────────────────────  npj Digital Medicine
  Layer 0   Pixels + workflow     ← everything held today
            ─────────────────────────────────────  MICCAI, IJCARS, MedIA
```

### Layer B — outcome linkage (highest value, longest lead time)

The strongest precedent in this exact procedure:

- Birkmeyer et al., **NEJM 2013** — 20 Michigan bariatric surgeons, one
  representative gastric bypass video each, blinded peer skill ratings
  (2.6–4.8 on a 5-point scale). Higher skill → fewer complications,
  reoperations, readmissions, ED visits.
  ([NEJM](https://www.nejm.org/doi/full/10.1056/NEJMsa1300625))
- The **JACS 2016** follow-up: skill ratings did **not** predict 1-year
  weight loss or resolution of sleep apnea, hypertension, or
  hyperlipidemia. ([PubMed](https://pubmed.ncbi.nlm.nih.gov/27074114/))

That pair is thirteen years old, built on **20 videos and human raters**,
and nobody has replicated it with automated foundation-model-derived
workflow metrics at cohort scale.

| Asset | Gives | Access reality |
|---|---|---|
| [MBSAQIP PUF](https://asmbs.org/about/mbsaqip/) | ~775k cases, 925 hospitals, 30-day outcomes | ACS Participant-Use File request; **no video**, no case-level key to MB140 |
| ACS NSQIP PUF | Same structure, general surgery | Same route |
| Collaborator-site EHR | The only route to **video ↔ outcome on the same patient** | IRB + surgical department partner; 12–18 month lead time |

**Be honest about the join.** MBSAQIP has outcomes without video; MB140
has video without outcomes. They do not link. Registry-only ML on MBSAQIP
is already crowded (VTE, readmission, same-day discharge —
[systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC13167840/)).
The contribution exists only with case-level linkage, which means one
hospital, one IRB, one surgical partner. **Start that conversation now**;
it costs nothing and buys the option.

### Layer C — action and physics (what "physical AI" actually requires)

Video alone does not reveal force. The bar has moved:

- **Science Robotics (2025)** — surgical embodied intelligence, open
  simulator, zero-shot sim-to-real on laparoscopic robot tasks.
  ([paper](https://www.science.org/doi/10.1126/scirobotics.adt3093),
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/40668896/))
- **ORBIT-Surgical** — 14 dVRK/STAR benchmark tasks on Isaac Sim, up to
  8000 parallel envs on one RTX 3090, demonstrated sim-to-real on a
  physical dVRK. Cheapest credible on-ramp: no hospital, no IRB, one GPU.
  ([arXiv](https://arxiv.org/pdf/2404.16027), [site](https://orbit-surgical.github.io/))
- **SurgWMBench** (arXiv, Aug 2026) — already argues that FVD/CD-FVD
  generation metrics do not measure whether predicted trajectories are
  geometrically accurate, temporally coherent, or actionable, and supplies
  motion-centric metrics instead. ([arXiv](https://arxiv.org/abs/2608.08070))

**Read that last one before committing.** It is close to the
"pixel metrics are not enough" claim this project has carried since the
2026-05 Cosmos brief (Part VI.1). That position is now occupied. The
remaining differentiator is **calibration and abstention under
distribution shift** — when should the system stop and ask for help — not
"world models for surgery."

NVIDIA has shipped a healthcare-robotics stack with CMR Surgical, J&J
MedTech, and Medtronic as early adopters — good for tooling availability,
bad for novelty claims framed around the tooling.
([NVIDIA](https://blogs.nvidia.com/blog/national-robotics-week-2026/),
[CMR](https://www.surgicalroboticstechnology.com/news/cmr-surgical-advances-physical-ai-with-nvidia/))

### Layer A — OR context (cheapest genuine novelty)

Multimodal OR data acquisition (MODAL / "OR black box") integrates
equipment, physiologic monitors, EHR, and ambient audio-video. A 2026
review notes terminology and governance are still unstandardized — the
field is open. ([review](https://onlinelibrary.wiley.com/doi/10.1002/lio2.70400))

Obtainable now: **[VitalDB](https://www.nature.com/articles/s41597-022-01411-5)**
(6,388 surgical cases, high-resolution intraoperative vitals, open — no
video, but it builds the physiological arm before a linked cohort exists);
**MM-OR**; **EgoExOR**. Surgical Safety Technologies is the commercial
route, institution by institution.

**The unclaimed question:** does anticipation accuracy improve when the
model sees the *room* — staff movement, instrument requests, anesthesia
state — and not only the laparoscope? Open, clinically legible, and closer
to existing skills than robotics.

## II.3 Foundation-model crowding

This is the main reason not to run Paper 2A as a backbone comparison.

| Work | What it occupies |
|---|---|
| [SurgVISTA](https://www.nature.com/articles/s41746-026-02403-0) (npj DM 2026) | Large-scale SSL surgical video FM, broad downstream eval |
| [SurgΣ](https://arxiv.org/html/2603.16822) (Mar 2026) | 6 specialties, 18 tasks, 5.98M conversations, unified schema |
| SurgRec | Reproducible recipe, 10,535 videos / 214.5M frames, 16 datasets |
| [SurgWMBench](https://arxiv.org/abs/2608.08070) (Aug 2026) | World-model motion-planning benchmark and metrics |
| [Surg-R1](https://arxiv.org/pdf/2603.12430) | Hierarchical reasoning FM, multi-center clinical validation |
| [SurgXBench](https://arxiv.org/html/2505.10764) | Explainable surgical VLM benchmark |

An encoder leaderboard is not publishable at the top tier in this
environment.

### The contribution that is unoccupied

The Phase 0 findings are the asset, currently treated as a disclaimer
rather than a result:

- 98% of paired conditioning-effect variance is between-fold, 2%
  between-seed; effects below ~0.5 min are not resolvable on a 5-fold
  split at any seed count. ([finding](../papers/paper2_forecasting/phase_0/PHASE_0_FINDING_FOLD_VARIANCE.md))
- The k-means phase-order cluster id is seed-unstable (ARI 0.63) and not
  recovered by an independent representation family (ARI 0.03–0.08).
  ([finding](../papers/paper2_forecasting/phase_0/PHASE_0_FINDING_REPRESENTATION.md))

The field is publicly worried about exactly this: npj Digital Medicine
(2026) on *"the emerging challenge of independent validation in an
industry-led AI ecosystem"*
([link](https://www.nature.com/articles/s41746-026-03028-z)); a systematic
review finding intraoperative video AI still rarely reaches dependable
clinical use ([link](https://pubmed.ncbi.nlm.nih.gov/42496894/)); in
adjacent orthopaedic AI devices, only **8.6%** were validated by a
prospective clinical trial
([link](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12879955/)).

**A measurement-validity paper for surgical video AI** — what effect sizes
are resolvable on standard benchmarks, which reported gains sit inside
fold noise, which representations are identifiable, and what a minimum
protocol should be — is a real contribution, fully supported by assets
already held, needing no new data, with a plausible home in npj Digital
Medicine or Medical Image Analysis. **This is the one direction that could
start tomorrow with zero new access.**

## II.4 Journal tiers and their entry price

| Tier | Venue | Non-negotiable entry price | Gap |
|---|---|---|---|
| Flagship clinical | Nature Medicine, NEJM AI, JAMA Surgery, Annals of Surgery | Prospective or multicenter evidence tied to patient outcomes or clinician behavior | Layer B; ~18–24 months |
| Flagship embodied | Science Robotics | Closed-loop physical experiments, perturbation, recovery, generalization | Layer C + hardware partner |
| Flagship engineering | Nature Biomedical Engineering | Engineering advance **plus** functional/ex vivo/wet-lab validation | Layer C, or bench validation |
| Flagship ML | Nature Machine Intelligence | A general learning principle beyond one procedure | ≥3 procedures + transferable mechanism |
| Strong specialist | npj Digital Medicine | Defined user and decision, independent cohort, reader or prospective eval | **Reachable 2027** |
| Strong technical | Medical Image Analysis, IEEE TMI | New method + strong ablations + independent validation | **Reachable 2027** |
| Solid | MICCAI, IJCARS, npj Digital Surgery | Rigorous focused study | Reachable now |

**Plainly:** nothing in the current asset base reaches the top row, and no
amount of additional modeling on MB140 + Cholec80 will get it there. The
top tier is bought with linkage, prospect, or physics — not better
encoders. The realistic 2027 ceiling is npj Digital Medicine / MedIA.
Any prospective evaluation should report under
[DECIDE-AI](https://www.nature.com/articles/s41591-022-01772-9).

---

# Part III — The commercial path

## III.1 Every dataset in use is non-commercial

**The most important constraint in this document.** Verified September 17,
2026 at the source repositories.

| Dataset | License | Consequence |
|---|---|---|
| **MultiBypass140** | **CC BY-NC-SA 4.0** — "available for non-commercial scientific research purposes" ([repo](https://github.com/CAMMA-public/MultiBypass140)) | No commercial use |
| **Cholec80** | **CC BY-NC-SA 4.0** ([CAMMA](http://camma.u-strasbg.fr/datasets/)) | No commercial use |
| **CholecT50** | **CC BY-NC-SA 4.0** ([repo](https://github.com/CAMMA-public/cholect50)) | No commercial use |
| Endoscapes2023 | PhysioNet credentialed access + DUA | Terms must be read before any product use |

Two problems, the second worse:

1. **NonCommercial** — no commercial use. Not a shipped model, not an
   investor demo, not a paid hospital pilot.
2. **ShareAlike** — adaptations must carry the same license. Whether
   trained weights are an "adaptation" under CC is **legally unsettled**,
   and that is the problem: it does not need to be settled against you.
   It only needs to be an open question for an acquirer's counsel to flag.

*Not legal advice.* But the conclusion is not close: **a product cannot be
built on weights derived from MB140, Cholec80, or CholecT50.**

### Two data lineages, kept clean from today

```
  RESEARCH LINEAGE                      PRODUCT LINEAGE
  MB140, Cholec80, CholecT50            data owned or licensed commercially
  → papers, benchmarks, methods         → shipped weights
  → credibility, citations              → revenue
  ↳ never ships                         ↳ never needs the academic data
      └──────── what crosses over: the METHOD, the CODE (Apache 2.0),
                the EVALUATION PROTOCOL, and reputation ────────┘
```

**The product's data strategy must be: train on the customer's own video
under a commercial DUA.** This is what the incumbents do, it is why they
sell a capture layer first, and it means the first paying pilot is
simultaneously the first training set.

**Action:** add `DATA_LINEAGE.md` recording which checkpoints touched
which datasets, with hashes, before the next training run. Proving a
checkpoint never touched NC data retroactively is close to impossible.

## III.2 Market: the best-funded company in this space just failed

- **Caresyntax** — OR data capture and AI analytics, founded 2013,
  **$488M raised** including a $180M Series C extension in 2024 — **filed
  for bankruptcy May 2026.**
  ([Tracxn](https://tracxn.com/d/companies/caresyntax/__0AGGHuKGsKMvCnYHKFu1vdhek60PcdaaLN3ScjTJv4M),
  [CB Insights](https://www.cbinsights.com/company/caresyntax),
  [$180M round](https://www.caresyntax.com/news/caresyntax-raises-180-million-funding-to-accelerate-growth-and-adoption-of-precision-surgery-2))
  Aggregator-sourced but consistent across three trackers; confirm before
  repeating it to an investor.
- Remaining field: Theator, Surgical Safety Technologies, Proximie,
  Artisight, plus incumbents Intuitive, Medtronic, Brainlab who own the
  hardware channel.

**The failure mode was distribution, not accuracy.** OR-analytics
platforms require hardware in operating rooms, hospital IT integration,
and 12–24 month enterprise sales cycles against vendors who already own
the tower. That is the worst possible business shape for one person.

### The two wedges available to an individual

**Wedge A — software riding someone else's capture layer.** Do not sell
cameras. Sell a model consuming video and telemetry the hospital already
records (Black Box, Theator, robot logs, tower output) and returning
scheduling and throughput signal. Sell to the surgical services line, or
OEM to the capture vendor. This is where the RSD work already sits and it
needs no OR hardware.

**Wedge B — independent validation of surgical AI.** The validation crisis
in II.3 is a market. The Phase 0 findings are, commercially, a
**demonstrated capability to detect that a reported surgical-AI gain is
inside noise** — exactly what vendors will not self-report. Software-only,
sells to a budget holder who already exists (procurement, quality, risk),
no FDA exposure, billable on day one. It also inverts III.1: validation
runs on the *customer's* data, so the NC restriction never binds.

## III.3 The regulatory fork that decides product shape

FDA issued a revised final **Clinical Decision Support Software** guidance
**January 6, 2026** (re-issued January 29), replacing the September 2022
version.
([FDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software),
[Covington](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance))

Software meeting all four criteria of 21st Century Cures §520(o)(1)(E) is
**Non-Device CDS**, outside premarket review. The 2026 revision moved the
**time-critical decision making** limitation out of Criterion 3 into
**Criterion 4**, on the position that software intended for time-critical
decisions cannot let a clinician independently review its basis.

| Product | Likely status | Time to revenue |
|---|---|---|
| Real-time intraoperative RSD display, live deviation alert | **Likely a regulated device** | Years; premarket submission, clinical evidence |
| Between-case / post-hoc OR scheduling, throughput, staffing analytics | **Plausibly Non-Device CDS** | Months |
| Retrospective quality review and validation reports (Wedge B) | Furthest from device status | Immediate |

This points opposite to the research instinct. The scientifically exciting
product is the live one; the *sellable* product is the between-case one.
**Ship the boring one, fund the exciting one with it.** Get a regulatory
consultant to confirm classification before building — a few thousand
dollars that determines the entire roadmap.

## III.4 Funding: SBIR/STTR

### Why SBIR fits this situation specifically

1. **It dissolves the PI-eligibility question** that consumed the CDMRP
   memo. You are PI of your own company. The test is **primary
   employment** — more than half your time. If this is the main activity,
   it is satisfied by definition.
   ([SBIR eligibility](https://www.sbir.gov/tutorials/program-basics/tutorial-2))
2. **You keep the IP.** The small business owns and has full right and
   title to data developed under the award; the government takes a limited
   license, with data rights protection typically ~20 years. Under a
   university grant the university owns it. For someone intending to sell,
   this is the whole difference. ([data rights](https://www.sbir.gov/faq/data-rights))
3. **Non-dilutive.** No equity, no board seat.

**STTR variant:** requires a partnering research institution doing ≥30% of
the work (small business ≥40%), and the PI does **not** have to meet the
primary-employment test. This is the path that preserves a UCSC
affiliation.

### Targets

All amounts and dates below are **discovery-grade and must be verified**
at [sbir.gov](https://www.sbir.gov), [grants.gov](https://www.grants.gov),
and [seedfund.nsf.gov](https://seedfund.nsf.gov).

| Program | Fit | Amount / cadence | Notes |
|---|---|---|---|
| **NIH SBIR omnibus, PA-27-100** | Primary target | Phase I reported up to **$400k–$700k** depending on IC. Dates reported as **Sep 5 2026, Jan 5 2027, Apr 5 2027, Sep 5 2027** | Choose the IC deliberately — NIBIB for imaging/methods, NIDDK for bariatric, **AHRQ for OR-efficiency, the strongest fit for Wedge A** |
| **NSF SBIR/STTR** | Second shot; deep-tech framing | Relaunched with **$250M**; Phase I ceiling **$305k**, 6–18 months. Deadlines reported as Jul 27 2026 (passed), **Nov 4 2026**, **Mar 4 2027** | **Mandatory Project Pitch** on-ramp — low-cost, fast-feedback. Do this first regardless |
| **ARPA-H SBIR** | Ambitious; ties to AIR | Varies | [SBIR page](https://arpa-h.gov/explore-funding/sbir). AIR's main solicitation closed Mar 18 2026 ($175.3M / 5 yr), awardees announced Aug 2026 — the route in is **subaward to a funded AIR team**, which is also customer discovery. [AIR](https://arpa-h.gov/explore-funding/programs/air) |
| **NVIDIA Inception** | Compute and credits for startups | In-kind, free | Replaces the NVIDIA Academic Grant Program, which requires **full-time faculty** |

### Ruled out — do not spend time

- **Schmidt AI in Science fellowships** — explicitly do not fund AI applied
  within medical sciences, and are postdoctoral. ([Oxford](https://saiis.web.ox.ac.uk/))
- **Intuitive Foundation, SAGES, ASMBS grants** — structured for
  **non-profit institutions**; not available to a company. Available if a
  clinical collaborator holds the award — a reason to find a collaborator,
  not a funding line. (Intuitive: up to $75k, 1 yr, LOI cycles reported as
  Jan 5 / Jun 5 2026 — [page](https://www.intuitive-foundation.org/clinical-research-grants/).
  [SAGES robotic grants](https://www.sages.org/research/robotic-surgery-research-grants/).)
- **NIH R21/R03, NSF SCH/PESOSE/FRR, CDMRP** — require an eligible
  institution and give it the IP. Relevant only through a collaborator.
  See Part VI.5 for the CDMRP analysis, retained for that case.

### Registrations are the hidden deadline

SAM.gov, SBA company registry, eRA Commons, Grants.gov, and the company
itself. **Weeks**, sequential, and missing one forecloses a cycle. The
most common way people lose a year to SBIR is registration, not science.

Confirm: US for-profit, ≤500 employees, >50% owned and controlled by US
citizens or permanent residents; and that the >50% time test is met
alongside any teaching or employment held.

### NIH process change

From FY2026 NIH no longer posts notices of funding opportunities in the
NIH Guide — **Grants.gov is the single official source**. Set Grants.gov
saved searches, not Guide alerts.

---

# Part IV — Scientific program

## IV.1 Current direction: anticipation, not another backbone matrix

**Working name: OpenSurgics — Uncertainty-Aware Anticipation of
Intraoperative Events Across Surgical Centers.** RSD becomes an auxiliary
task and baseline. The new question: can observed surgical state forecast
an upcoming event with useful lead time, controlled false alarms, and
honest uncertainty at a different center?

Assumes no robot, no new hospital cohort, no outcome linkage, no clinical
annotation commitment. Current assets: MB140 and Cholec80 label exports,
prior results, temporal forecasting code, five-fold analysis, a tested
streaming workflow filter. A repository inventory found no established
kinematics/force/outcomes pipeline. Video roots and complete source
annotations still need locating.

| Priority | Direction | Feasibility with current assets | Added evidence needed |
|---|---|---|---|
| 1 | Cross-center event anticipation and selective prediction | Best extension, conditional on label quality | Corrected event types, severity, onset/offset, observation masks; clinician review of a sample |
| 2 | Anatomy/action-grounded safety assessment | Feasible with additional research-access datasets | Anatomy masks, instrument–verb–target labels, CVS criteria; dataset-overlap reconciliation |
| 3 | Human–AI assistance for video review/training | Feasible once clinician participation is confirmed | Randomized reader study, error review, workload and inappropriate-reliance measures |
| 4 | Action-conditioned physical AI and recovery | Longer-term; no confirmed hardware/data route | Synchronized video, measured actions/kinematics, simulator, real task validation |
| 5 | Patient-specific digital twin or postoperative outcome prediction | Least supported today | Linked longitudinal clinical data, physiology, case mix, outcomes |

Feasibility judgments, not acceptance probabilities. Start with **one**
clinical event.

### The most valuable data may already be in the dataset

The official MB140 repository documents **12 phases, 46 steps, five
intraoperative adverse-event categories, and severity labels** — with IAE
additions April 2025, corrected surgery IDs September 2025, and a
corrected BBP04 frame/label mapping. Recover the corrected version and
verify provenance. [Official dataset](https://github.com/CAMMA-public/MultiBypass140)

Local audit, September 17:

- `scripts/lambda_setup/scripts/06_build_labels.py` turns `Overall > 0` into
  `is_deviation`, discarding event category, severity, and step
  information. A missing `Overall` is silently mapped to zero.
- The MB140 fold-0 export contains **70,366 flagged frames across 138/140
  operations** — flag counts, not verified event counts. A binary "any
  event during the case" endpoint would have almost no discrimination.
- **Cholec80 contains no positive flags** because its builders assign
  `False` without adverse-event annotations. Treat its safety targets as
  **missing**, never as negative examples. RSD and phase tasks still work.

**First data deliverable:** operation ID, center, timestamp, phase, step,
event category, severity, onset/offset, annotation availability, and
source/version. Retain raw-to-derived mapping and hashes. Record
`unknown`, `not annotated`, and `confirmed absent` separately. Validate
whether annotation intervals actually support onset anticipation.

### What knowledge to add, and how to falsify it

| Knowledge | Representation | Falsifiable comparison |
|---|---|---|
| Surgical task structure | Procedure → phase → step → action, with optional/repeated branches | Learned visual state vs hierarchy-conditioned state on held-out centers |
| Anatomy and tool interaction | Tool–action–target relationships and relevant anatomy | Video-only vs grounded features at matched encoder/head capacity |
| Clinical event definitions | Adjudicated category, severity, timing, visibility, recoverability | Event-specific forecasts vs elapsed-time and predicted-step risk baselines |
| Epistemic limits and label disagreement | Calibration, abstention, rater distributions, occlusion state | Error at fixed coverage and alarm burden under center/visibility shift |
| Physical dynamics, later | Action-conditioned state transitions and contact/force observations | Closed-loop task success/recovery over observation-only policies |

Learn flexible procedural structure rather than forcing one "correct"
operation order; preserve clinically valid variation. Do not use a
reference phase, future step, or retrospective full-case workflow token as
a deployed model input. Guideline-derived anatomy constraints need
clinician review and ablation; text retrieval alone does not show
grounding in video.

### Data acquisition priorities

| Order | Resource | Purpose | Access and interpretation limits |
|---|---|---|---|
| Now | Corrected MB140 source labels | Steps, events, severity, cross-center forecasting | Reconstruct and audit alignment before new collection |
| Next | [Endoscapes2023](https://physionet.org/content/endoscapes-2023/1.0.0/) | Anatomy segmentation, critical-view-of-safety | 201 source operations; released segments are not a full-operation event-onset cohort. Credentialed access + DUA. CVS is a process label, not proof of avoided injury |
| Next | [CholecT50](https://github.com/CAMMA-public/cholect50) | Instrument–verb–target grounding | 50 videos, 45 from Cholec80; CC BY-NC-SA 4.0. Additional annotation, **not** an independent cohort |
| Conditional | [HeiChole](https://www.synapse.org/Synapse%3Asyn18824884) | Additional-center workflow evaluation | Test data not released; verify obtainable splits first |
| Conditional | [AutoLaparo](https://arxiv.org/abs/2208.02049) | Different-procedure transfer | Hysterectomy perception dataset. **Do not** carry forward the older claim that it also supplies sleeve gastrectomy |
| Watch | [MultiBypassT40 challenge](https://zenodo.org/records/19713857) | Fine-grained action within gastric bypass | Challenge description is not proof labels are obtainable; verify release and overlap |
| Later | [JIGSAWS](https://cirl.lcsr.jhu.edu/research/hmm/datasets/jigsaws_release/) | Video/kinematics prototyping | Small skill-task dataset; not a substitute for full procedures or force measurement |
| Permission needed | [SAGES CVS Challenge](https://www.cvschallenge.org/the-challenge-2) | Safety-assessment diversity | Page restricts use to registered challenge teams; do not assume general research permission |

**Build a global operation-ID map before pooling.** CAMMA publishes known
overlaps across Cholec80, CholecT50, and Endoscapes. Apply exclusions
across training, calibration, validation, and test — including
foundation-model pretraining data where provenance is available. New
dataset names do not imply independent patients or institutions.
[Official overlap map](https://github.com/CAMMA-public/camma_dataset_overlaps)

### Where the contribution must go beyond existing work

- **Broad encoder comparisons are crowded.** SurgVISTA pretrains on 3,650
  videos across 13 video datasets. The opportunity is reliable
  anticipation and decision-relevant evaluation, not a smaller claim to a
  general surgical FM. ([npj DM 2026](https://www.nature.com/articles/s41746-026-02403-0))
- **Descriptive event analysis on MB140 already exists** (2025, technique
  and adverse-event occurrence). A new paper must separate true pre-onset
  prediction, domain transfer, and uncertainty from repeating
  frequency-by-step associations. ([study](https://pubmed.ncbi.nlm.nih.gov/39890612/))
- **Adverse-event localization is established.** A 2026 study retrieves
  steps and events including bleeding, bile spillage, thermal injury.
  Benchmark against detection/localization and show what pre-onset
  prediction adds. **Do not call detection anticipation.**
  ([study](https://www.nature.com/articles/s44484-026-00010-w))
- **Physical AI has stronger precedents than video prediction.** SRT-H
  reports hierarchical control and ex vivo validation on eight unseen
  gallbladders — not patient-level efficacy. ([arXiv](https://arxiv.org/abs/2505.10251))
- **Video-to-policy world modeling is being pursued.** The
  Cosmos-H-Surgical preprint (formerly SurgWorld) uses synthetic video,
  inferred pseudokinematics, and real-robot policy evaluation. Novelty
  needs a specific advance such as calibrated recovery under shift.
  ([preprint](https://arxiv.org/abs/2512.23162))
- **BME papers connect representations to function.** A 2026 ophthalmic
  FM article includes wet-lab porcine-eye navigation validation — an
  example of functional evidence, not a mandatory template.
  ([Nature BME](https://www.nature.com/articles/s41551-026-01622-w))

Targeted primary-source review, not a systematic one. Complete
task-specific citation chaining before any novelty claim.

### Flagship experiment

**Question:** does an explicitly grounded, calibrated surgical-state model
anticipate a defined event better than a strong video model and simple
procedural risk baselines when transferred between centers?

**Primary endpoint proposal:** event-level sensitivity at a
clinician-agreed false-alarm rate per operating hour, with a minimum
useful warning interval. Set that interval after annotation review; pilot
15/30/60-second horizons as exploratory. Choose one horizon/endpoint
before the held-out evaluation.

Use only frames ending before the prediction time. For each future event,
exclude ongoing events and specify a lead-time buffer before annotated
onset. Define handling of uncertain onsets, repeated events, and
post-event recovery. Prevent clips immediately after onset from becoming
"forecasts." Include normal-but-visually-difficult segments and event-free
exposure time. Report alarm suppression/refractory settings and matching
rules so repeated alarms cannot inflate sensitivity.

**Minimum comparisons:** elapsed time; predicted phase/step risk; matched
video-only temporal model; video plus continuous workflow state; grounded
state plus calibrated abstention. Train and calibrate on development
cases, then lock for untouched-center tests. Report both Bern→Strasbourg
and Strasbourg→Bern if label counts support it. Use the five-fold analysis
for development robustness; repeated test reuse is not confirmation.

**Secondary:** event AUPRC with prevalence, warning-time distribution,
Brier score, reliability, risk–coverage curves, latency, subgroup
failures. Bootstrap by operation; account for multiple events per
operation. Do not claim distribution-free coverage under center shift
without its assumptions. Size from event counts, not frame counts.

If pre-onset information is weak or events too sparse, retain honest
real-time detection plus abstention, or procedural anticipation. **A null
anticipation result with strong evaluation can be valuable, but it is not
automatically a top-tier paper.**

## IV.2 Paper 2A / 2B — the experiment package

Retained because the infrastructure is built and the protocol is sound.
Under the Part I goal this is the **research lineage** (III.1): it
produces credibility, not shippable weights.

**Paper 2A: Stable Workflow Representations for Online Surgical
Forecasting: A Multi-Backbone Evaluation.** Do stronger video
representations and continuous workflow state improve RSD and next-phase
transition forecasting consistently across held-out cases, folds, and
centers? The contribution is a controlled empirical study of
representation, generalization, and evaluation stability. Prefix-only
inference is an established constraint, not an invention. "Causal" here
means no future inputs; it does not establish causal treatment effects or
clinical benefit.

**Paper 2B follows only if 2A's evidence supports it:** distill a
privileged workflow teacher into a prefix-only student. Training still
uses privileged supervision; the claim is independence from oracle inputs
**at inference**, not from privileged information at all stages. Do not
commit to a second manuscript until the teacher advantage is stable across
folds and large enough to measure.

### Minimum publishable package

| Component | Required scope |
|---|---|
| Backbones | Pinned ViT anchor, one accessible general video encoder, one surgical encoder if weights/license pass audit; fourth/fifth optional |
| Tasks | RSD and time to next phase transition; future-phase sequences optional |
| Data | MB140 five-fold + cross-center; Cholec80; pursue an independently sourced third dataset subject to access and annotation audit |
| Conditioning | No token, legacy categorical R1, continuous HMM R3; all deployable arms use prefix-derived inputs |
| Confirmation | Repeat selected comparisons with three seeds; retain all five MB140 folds; add shuffled-signal and parameter-matched controls |
| Representation test | Fit all preprocessing, clusters, HMM parameters on training cases; filtering only, never future-conditioned HMM smoothing, at inference |
| Reporting | Per-video errors, per-fold effects, seed dispersion, uncertainty intervals, latency, training cost, horizon coverage |

Three backbones × (five folds + cross-center + Cholec80) × three
conditioning arms = **63 scout head-training runs** for a shared multitask
head. Separate heads need more. A third dataset and confirmatory controls
are extra. **Drop optional backbones before dropping folds or the
continuous-state comparator.**

Use paired video-level resampling — clips from one operation are not
independent. Keep model selection within training/validation data.
Predeclare confirmatory comparisons and retain separate test results. **Do
not claim a workflow-entropy scaling law from two procedure datasets**; a
third improves coverage but does not resolve procedure, center,
annotation, and pretraining-data confounding. Audit possible overlap with
foundation-model pretraining data.

Assign the collaborator's role by expertise: clinical endpoint/error
review if clinically qualified, otherwise independent methods and
replication review. Their institution, clinical access, and data
permissions are not assumed.

### Decision gates

1. **Feasibility:** a reproducible anchor plus two working alternatives,
   verified licenses, a measured extraction/training pilot. If fewer pass,
   narrow to representation stability rather than claiming a comprehensive
   foundation-model comparison.
2. **Scout:** ≥0.5-minute mean MB140 improvement, or ≥0.3 minutes with
   matching direction in four of five folds. **Prioritization rules, not
   significance tests or clinical-utility thresholds.** A well-powered
   null may justify the study; publication is not guaranteed.
3. **Confirmation:** all selected rows carry per-fold results and the
   interaction/condition ratio. Report fold dependence explicitly.
   Interpret nulls against uncertainty and detectable effect size.
   *A ratio above 1 means the number describes fold-dependence rather than
   a transfer effect, and must be reported as such.*
4. **Writing:** state hypotheses before experiments; write conclusions
   after results. Do not precommit to "Cosmos fails" or to a fixed number
   of positive claims. Pixel-generation metrics apply only to models that
   generate comparable outputs.
5. **Budget:** historical GPU-hour/dollar totals (Part VI.3) are
   assumptions, not quotes. Estimate extraction time plus measured
   head-run time × run count, add storage and 25% contingency, and record
   actual provider rates before committing.

### Constraints inherited from the Paper 1 review

From `PAPER_2A_REVIEWER_HARDENING.md` (June 4, 2026). These constrain the
plan; they do not replace it.

| Paper 1 concern (reviewer) | Fix | Cost |
|---|---|---|
| Two-dataset confound (all three reviewers, AC lead concern) | **Add ≥1 third surgical benchmark.** Independent variation in *H(z)* | +1 dataset in extraction/eval; ~+15% compute |
| 5-fold instability (Xmi1, 6eLx) | **Fold-level analysis as a first-class result**, not an appendix. Per-fold effect sizes with paired video-level Wilcoxon inline; variance decomposition (seed vs fold vs backbone) | +0.5 pp of results; no new compute |
| Sub-1-min clinical utility (Xmi1) | **Abstract explicitly scopes as algorithmic-effect study, not clinical utility.** First sentence names it | Text only |
| Workflow-representation dependence (iSh9) | **≥3 representation variants**: TF-IDF+PCA+k-means, learned continuous embedding, HMM state-space. Report *H(z)* vs Δ across all three | +1 ablation per dataset; ~+10% compute |
| Presentation complexity (iSh9), separate supplementary (6eLx) | **Single-PDF submission**, appendix inline. Abstract leads with question → results → implications. Glossary paragraph for protocol terminology. ~40 references | Editorial |

Anticipated but unraised concerns, worth pre-empting:

- *"Your causal protocol is just standard prefix-only anticipation."* →
  Cite SWAG and Yengera 2019 explicitly. The contribution is the
  systematic multi-backbone × multi-dataset study, **not** the protocol.
- *"Your FM comparison is a leaderboard, not a benchmark."* → Frame as a
  measurement protocol + reference results, and release the eval harness.
- *"The workflow-cluster method is unchanged from Paper 1."* → 2A's
  contribution is evaluation methodology + cross-dataset variability
  testing. Keep the 2A/2B split clean.
- *"Why the complicated decoupled-oracle?"* → One sentence in the body,
  details in appendix. Paper 1's over-explanation was a readability
  complaint.

**Explicit non-goals** (the stop sign against scope creep): clinical
utility validation; prospective study; real-time deployment; new model
architecture; full VLA/action prediction; inventing a new workflow
representation.

## IV.3 Venues

Fit assessment, not acceptance prediction. Official sources checked
September 17, 2026.

| Priority | Venue | Decision rule | Deadline status |
|---|---|---|---|
| Primary | **MICCAI 2027** | Best audience for surgical video forecasting and clinically grounded technical evaluation | Society confirms meeting Sep 26–Oct 1, 2027; submission deadline **not verified**. Feb 1 is the internal readiness target. [Calendar](https://miccai.org/upcoming-conferences/) |
| Earlier stretch | **CVPR 2027** | Only if representation transfer and stability yield a strong vision result beyond an encoder leaderboard | Registration Nov 10; paper Nov 16; supplement Nov 23, 2026, AoE. [CFP](https://cvpr.thecvf.com/Conferences/2027/CallForPapers) |
| Journal | **IJCARS** | Strong scope match for surgical workflow, validation methods, expanded reproducibility | Standard journal route. [Scope](https://link.springer.com/journal/11548/aims-and-scope) |
| Ambitious journal | **Medical Image Analysis** | If methodological novelty and broader validation support a full-length contribution | Assess after confirmatory results |
| Conditional 2B target | **NeurIPS 2027** | Only for a general distillation/learning contribution with strong controls beyond a small surgical gain | No verified 2027 deadline; May is a planning estimate |

**ICLR 2027 is not realistic** — abstract September 18, paper September
25, 2026 AoE. Remove it from any backup list.
([guidelines](https://iclr.cc/Conferences/2027/AuthorGuidelines))

CVPR **precedes** MICCAI; it is an accelerated alternative, not a
fallback. Do not assume sequential CVPR→MICCAI resubmission until both
calendars and overlap policies are checked. The CVPR CFP lists February 25
decisions but February 22 as the review-period endpoint — resolve before
relying on either. Follow the selected venue's current anonymity,
page-limit, and supplement rules rather than copying Paper 1's.
Journal extensions must disclose prior versions and add substantive
contribution.

For clinical assistance, a controlled retrospective reader study is a
useful next layer: unaided vs AI-assisted review, randomized order,
controlling for case familiarity, measuring accuracy, review time,
workload, and inappropriate reliance. **It is not evidence that patient
complications decrease.** Prospective live evaluation should use
[DECIDE-AI](https://www.nature.com/articles/s41591-022-01772-9).
Scope references: [npj Digital Medicine](https://www.nature.com/npjdigitalmed/aims),
[npj Robotics](https://www.nature.com/npjrobot/aims). Nature Portfolio
branding alone does not establish equivalence to flagship journals.

## IV.4 Physical AI, after the video study

The next robotics question: **when should a surgical robot continue,
pause, or request help under uncertain tissue/tool state?** Reuse the
learned state and uncertainty model, then add action-conditioned dynamics
and recovery. Select one bench task — needle transfer, suturing — with a
collaborator who can supply the platform and synchronized demonstrations.

Record camera timestamps/calibration, tool pose and gripper state,
commanded vs executed motion, latency, interventions, success/failure, and
contact/force **if physically measured**. Video alone does not reveal
reliable force; a descriptive action triplet is not a robot control
command; a valid trajectory predictor is not a patient-specific digital
twin.

Prototype in an existing simulator rather than building one. The dVRK
documentation lists AMBF, Isaac-based environments, and SurRoL; ORBIT-
Surgical (II.2) is the most turnkey. Simulator realism and sim-to-real
validity must be **measured for the task**; OpenUSD scene formatting alone
contributes no validated tissue dynamics.
([dVRK simulation](https://dvrk.readthedocs.io/main/pages/usage/simulation.html))

Evaluate closed-loop success, recovery, contact/force violations where
measurable, latency, and human interventions on held-out variations. Image
quality metrics alone do not establish useful robot behavior. Physical AI
emphasizes action and adaptation, consistent with the
[Nature Machine Intelligence editorial](https://www.nature.com/articles/s42256-026-01239-3).

---

# Part V — Evidence base

Full documents in [`papers/paper2_forecasting/phase_0/`](../papers/paper2_forecasting/phase_0/).
Summarized here because both findings constrain everything above.

## V.1 Fold-variance dominance

On MB140, **98% of the paired conditioning effect's variance is
between-fold and 2% between-seed.** Effects below ~0.5 min are not
resolvable on a 5-fold split at any seed count.

Reproduced September 17, 2026 via
`python -m paper2_infra.evaluation.fold_stability --summary-json
papers/paper1_neurips2026/manuscript/phase_e_summary.json --baseline no_token --treatment decoupled
--conditions no_token oracle decoupled`:

- mean delta **−0.187 min**
- improvements in **3/5 folds**
- paired-delta fold variance share **98.1%**
- interaction/condition ratio **4.0**

*This is a reanalysis of stored results, not a fresh model reproduction.*

**Design consequence:** a fold-0 design has SE ≈ 0.42 min on the effect; a
5-fold × 1-seed design has SE ≈ 0.19 min for a similar run count. Tripling
seeds reduces SE by 1%. **Folds buy power; seeds buy almost nothing.** The
original fold-0 × 2-seed scout could not decide its own gate — a 0.3-min
threshold sat inside one standard error, so finalists would have been
selected by noise. If budget binds, drop a backbone, never a fold.

## V.2 Workflow-representation non-identifiability

The k-means phase-order cluster id is **unstable to the random seed alone
(ARI 0.63 on MB140)** and **is not recovered by an independent
representation family (ARI 0.03–0.08)**.

**Design consequence:** carry a continuous HMM posterior alongside the
legacy cluster id, to test whether a stable conditioning signal produces a
stable conditioning effect — the mechanism question underneath both
findings. Paper 2A moves to a continuous workflow vector.

## V.3 Stored artifact audit (September 17, 2026)

- MB140 fold 0 uses **K=6**, 16 PCA components, 63 features. Cholec80 uses
  **K=4**, 10 components, 10 features. Both record seed 42; **neither
  records `min_df`.** The original artifacts therefore **do not establish
  a matched-K/min_df comparison** — run a train-only matched-configuration
  control before interpreting cross-dataset representation differences.
  Vocabulary dimensions can legitimately differ across datasets;
  distinguish that from clustering hyperparameter choices.
- Label counts: MB140 fold 0 = 80 train / 20 val / 40 test cases;
  Cholec80 = 36 / 6 / 30. **Sampled frame paths do not resolve relative to
  this repository**; frame-root availability is unestablished. Other folds
  still need membership auditing.
- Added the [63-run scout configuration](../src/paper2_infra/configs/scout_protocol.json),
  explicitly marked **draft, not training ready**. Records inference
  restrictions, metrics, missing decisions; placeholder checkpoints are
  not frozen or validated models.
- Implemented `filtered_phase_probabilities` in
  [hmm.py](../src/paper2_infra/workflow_representations/hmm.py): accepts
  predicted phase distributions, carries state across streaming chunks.
  Soft evidence is an emission-weighted approximation, **not** calibrated
  Bayesian inference from classifier probabilities.
- Validation: **11 new tests passed** (hard-label equivalence, future
  invariance, streaming equivalence, uninformative evidence, malformed
  inputs); **102 existing tests passed** across HMM, fold stability, phase
  anticipation, representation comparison.

**Next implementation step:** integrate the R3 signal with the
cached-feature training head and a prefix-only phase predictor, then audit
all split memberships and reconstruct a matched clustering control. Fresh
baseline training, target-hardware timing, and scout runs remain
outstanding. No cloud instance or paid training has been launched.

## V.4 Headline numbers from Paper 1

Carried forward for reference; re-verify before citing.

| Quantity | Value |
|---|---|
| Retrospective decoupled-oracle gain, MB140 within-center | −0.85 min vs no-token |
| Deployable causal-at-inference gain, within-center | −0.18 min |
| Deployable causal-at-inference gain, cross-center | −0.22 min |
| MB140 | 140 RYGB videos, 2 centers (Bern/Strasbourg), 1 fps |
| Cholec80 | 72 videos, 7 phases, 36/6/30 split |

---

# Part VI — Historical record

Retained because the reasoning is still useful. **Dates, budgets, and
venue targets here are superseded** by Parts I–IV.

## VI.1 The Cosmos / physical-AI arc (May 2026)

The original concept was *"Surgical Cosmos + OpenUSD."* It was revised
twice — first to a world-model transfer benchmark
(`NEXT_PAPER_PHYSICAL_AI.md`, May 21), then to the current
representation-stability scope. The critique that drove the revision is
still worth remembering:

- **Vendor-first framing.** "NVIDIA Cosmos + OpenUSD" reads as product
  adoption before science.
- **Weak physical-AI claim.** RSD alone is not embodied control. Future-
  state or future-workflow prediction is the minimum bar for a world-model
  framing.
- **OpenUSD not load-bearing.** Encoding OR metadata in USD rather than
  JSON is not a contribution unless USD enables simulation, scene
  generation, or policy training. Keep it out of any title. An acceptable
  side experiment: store the same information as USD and as a flat vector,
  train with no prior / flat prior / USD prior, and report whether USD adds
  anything. If it doesn't beat the flat vector, cut it.
- **"First" claims are unsafe.** Claim systematic causal evaluation, not
  novelty by absence.
- **Compute risk too high.** Frozen features and parameter-efficient
  adaptation before any full fine-tune.

### The pre-registered null-result narrative

Still the right instinct, and still applicable to the anticipation study.
The most likely outcome was that Cosmos would not transfer to endoscopic
video, so the framing was fixed **before** running experiments:

> *"We propose pixel-prediction-quality-vs-downstream-utility as a
> diagnostic for surgical-video foundation models, and find that [model]
> has the highest pixel quality but is mid-pack on downstream utility."*

Three ranked narratives: (1) pixel-prediction quality is a weak proxy for
surgical forecasting — recommended primary, most surprising, least
cherry-picking; (2) domain gap dominates and surgical-native pretraining
wins; (3) the generic model as a calibration anchor — safest, requires no
model to win.

Writing tactics that generalize: decide the framing before running;
make the diagnostic measurement first-class and cheap; don't oversell
("Cosmos fails at surgery" → "Cosmos features, under our causal protocol,
do not transfer measurably better than ImageNet-pretrained ViT features on
MB140 or Cholec80, despite generating higher-PSNR pixel predictions");
cite the vendor's own framing (Cosmos is positioned as a platform *for
fine-tuning*), which makes a null result a measurement of post-training
cost rather than an indictment.

**Note (Sept 2026): SurgWMBench now occupies this diagnostic claim** —
see II.2.

## VI.2 The two-paper split rationale

| Concern | Single paper | Two papers |
|---|---|---|
| Reviewer fatigue | "Too much going on" | Each has one thesis |
| Page budget | 8 pp × 3 contributions = shallow | 8 pp × 2 = depth |
| Venue fit | Split across communities | 2A → MICCAI/CVPR, 2B → NeurIPS/ICLR |
| Risk hedging | One failure sinks the paper | 2B independent of FM transfer |
| Time-to-publish | 9–12 months | 2A in 6, 2B in 9–12 |
| Infrastructure | — | ~70% shared |

Still sound. Under the Part I goal the 2B NeurIPS target matters less than
it did.

## VI.3 Compute budget history

Three successive estimates, none measured on target hardware:

| Source | Estimate |
|---|---|
| `NEXT_PAPER_REFINEMENTS.md` (May 20) | 2A ~3,400 GPU-h / $10.2K; 2B ~2,250 / $6.8K; combined ~7,000 h / **$21K** with overhead. Built from a **672-run** grid (8 backbones × 7 settings × 4 conditions × 3 seeds) |
| `NEXT_PAPER_BRIEF.md` (May 21) | Staged: Stage 0 audit 40–80 h; Stage 1 scout 250–500 h; Stage 2 confirmatory 700–1,400 h; Stage 3 adapters 500–1,200 h; Stage 4 optional SSL 700–1,500 h. Realistic two-paper **$8.4K–$17.7K** |
| `PAPER_2A_REVIEWER_HARDENING.md` (Jun 4) | +20% for a third dataset and two extra representation families → combined upper bound **~$25K** |

**Current guidance (supersedes all three):** treat these as assumptions,
not quotes. No new GPU is needed for label, split, endpoint, and
provenance work. For the first video pilot, provisionally plan **one
24–48 GB GPU** for small/frozen encoders and heads, pending a measured
batch-memory test; 80 GB may be justified for larger encoders. **Do not
purchase a multi-GPU world-model run.** Annotation quality, independent
validation, and access are more limiting than compute.

The *staging* logic survives even though the numbers don't: the first
go/no-go decision should cost <500 GPU-hours, and each stage should be
able to kill the next one.

## VI.4 The five-paper roadmap (2026–2029)

From `NEXT_PUBLICATIONS.md`. Superseded as a commitment; the dependency
reasoning is still useful.

```
P1 (current)        P2                P3              P4              P5
"When does it       "Closing the      "Richer         "Backbone       "Prospective
 help?"             deployment gap"   conditioning"   effects"        deployment"
```

| Paper | Question | Risk | Lead time |
|---|---|---|---|
| P2 | Can privileged workflow be distilled into a fully deployable pixel-only predictor? (→ now Paper 2B) | Low | 6 mo |
| P3 | Does hierarchical procedure→phase→step conditioning beat coarse clusters? (→ now folded into IV.1) | Medium | 9 mo |
| P4 | Does surgical-domain pretraining change *when* conditioning helps? (→ now Paper 2A) | Med-high | 12 mo |
| P5 | Do offline gains survive real-time deployment? Annals/JAMA Surgery target, IRB, 50–100 prospective cases | High | 18+ mo |
| P6 | Does the conditioning recipe generalize beyond RSD? | Medium | 12 mo |

De-prioritized then and still: multi-modal RSD with text+audio+video as a
standalone axis; state-space models as a publication axis; synthetic-data
augmentation as separate work; a negative-results paper detached from the
main narrative.

**P5 remains the most important translational item and has the longest
lead time** — which is the Layer B argument in II.2 by another name. It
was worth starting early in 2026 and is worth starting now.

## VI.5 CDMRP analysis

Retained for the case where a collaborator holds the award. Under Part I
this is not a direct route. The memo's own conclusion was that CDMRP is
probably the wrong funder: the contribution is methodological, which fits
NSF SCH / AHRQ / NIBIB better than a disease-and-military-relevance
program.

Three structural blockers, as assessed September 16, 2026:

1. **PI eligibility** — CDMRP research mechanisms exclude postdoctoral and
   clinical fellows and other mentored scientists from Initiating or
   Partnering PI roles. The Partnering PI option requires a clinician
   investigator (M.D., M.D./Ph.D., D.O.) with clinical duties.
2. **Topic-area gating** — PRMRP is the largest program ($370M, 52 topic
   areas) but congressionally gated, and none of the FY26 topic areas
   covers surgery, surgical AI, obesity, bariatrics, perioperative care,
   or clinical decision support. The list changes annually; re-check each
   spring.
3. **Military relevance is scored, not asserted** — needs an MTF or VA
   collaborator and a stated military health problem.

If pursued: **CRRP** (Combat Readiness, $5M FY26) is the best conceptual
fit, **JWMRP** ($10M FY26) is less topic-gated. The reframe that would
work is *surgical readiness through operative workflow measurement* — DoD
has a documented concern that military surgeons lose operative case volume
between deployments and that readiness is hard to measure objectively. The
cross-center analysis maps to MTF-to-MTF transfer; the
workflow-variability finding maps to *when* automated assessment is
informative at all.

**Structural lesson worth keeping regardless of funder:** CDMRP requires a
pre-application weeks or months before the full application, and full
applications are accepted **only** from those who submitted one. Missing a
pre-application forecloses the entire cycle. *This is the single most
common way people lose a year* — and the same lesson applies to SBIR
registrations (III.4).

---

# Part VII — Execution

## VII.1 Three concurrent tracks

None waits on the others.

### Track 1 — Ship the measurement-validity paper (next 4 months)

The paper from II.3, built entirely on assets already held. Zero new data,
zero new access, zero licensing exposure. Target npj Digital Medicine or
Medical Image Analysis. Shares its audit work with the IV.1 anticipation
study, so it is not a detour.

Its role under Part I: **the credibility asset that makes Wedge B
sellable.**

### Track 2 — Incorporate and file a Project Pitch (next 8 weeks)

1. Form the company; begin SAM.gov / SBA / eRA Commons registration the
   same week.
2. Write `DATA_LINEAGE.md` (III.1) **before any further training run**.
3. File an **NSF Project Pitch** — days of work, fast official feedback,
   no commitment.
4. Aim at **NIH SBIR Jan 5 or Apr 5, 2027**, most likely through AHRQ
   with the OR-efficiency framing.

### Track 3 — Pick the wedge, and pick the boring one

Build **between-case OR analytics** (III.3), not the live intraoperative
product. Very likely outside FDA premarket review, sells to an existing
budget holder with explicit ROI (OR time reported up to ~$2,190/hr; OR
~42% of hospital revenue), and is the natural home for the RSD work.

Sell **Wedge B (validation)** alongside from day one: billable
immediately, requires nothing but existing expertise, and puts you in the
room with the hospitals whose video you will later need under a commercial
DUA to solve III.1.

## VII.2 Next 90 days

| Window | Work and decision |
|---|---|
| Sep 17–30 | Resolve the Paper 1 status conflict. Locate corrected MB140 annotations and video roots; recover event/step fields; count event onsets, severities, unknowns per center; establish the operation-level overlap map. Write `DATA_LINEAGE.md`. Start company registrations. |
| Oct 1–15 | Collaborator reviews an initial label sample if clinically qualified; otherwise recruit qualified review before any clinical claim. Freeze one endpoint; build elapsed-time and phase baselines. File NSF Project Pitch. |
| Oct 16–Nov 15 | Small frozen-feature pilot, calibrated on development cases; assess event counts, false alarms, true warning time. **Decide whether anticipation is identifiable before scaling.** Begin one Layer B or Layer C partnership conversation. |
| Nov 16–Dec 15 | Confirmatory comparisons; untouched-center evaluation where feasible; complete draft. Regulatory consult on Non-Device CDS classification. |
| Jan–Feb 2027 | MICCAI-ready study or expanded journal submission depending on actual evidence. NIH SBIR Jan 5 or Apr 5 application. Public benchmark release when permitted. |

**Immediate implementation priority: recovering richer labels and proving
one safety endpoint is measurable** — not expanding the backbone matrix.
Keep the tested RSD/representation infrastructure as the baseline. Freeze
a revised experiment manifest only after that audit; the existing 63-run
draft is not automatically the safety-study protocol.

## VII.3 Deliverables

- [ ] `DATA_LINEAGE.md` — checkpoint-to-dataset provenance with hashes
- [ ] One frozen experiment manifest: splits, checkpoint IDs,
      preprocessing, allowed inputs, metrics, selected comparisons
- [ ] A baseline reproduction report and measured compute estimate
- [ ] A scout table including **every** fold, not only the best result
- [ ] Four core figures: prefix-only pipeline; backbone/conditioning
      comparison; fold/representation stability; cross-center failures
- [ ] A collaborator-reviewed draft and a reproducibility package
- [ ] Company formed; SAM.gov / SBA / eRA Commons registered
- [ ] NSF Project Pitch filed

OpenSurgics can host the benchmark documentation, evaluation tools, and
community discussion when release is appropriate. **Its website alone is
not the scientific contribution.** Keep release permissions aligned with
venue anonymity requirements and with the III.1 lineage split.

---

## Provenance

Consolidated September 17, 2026. Source memos and their research dates:
`NEXT_PAPER_PHYSICAL_AI.md` (2026-05-21), `NEXT_PAPER_REFINEMENTS.md`
(2026-05-20), `NEXT_PAPER_BRIEF.md` (2026-05-21), `NEXT_PUBLICATIONS.md`,
`PAPER_2A_REVIEWER_HARDENING.md` (2026-06-04), `cdmrp_fy27_path.md`
(2026-09-16), `NEXT_PAPER_PLAN.md` §8 and `DIRECTION_AND_FUNDING_2027.md`
(both 2026-09-17). Originals at git commit `58c99bc`.

Primary sources linked inline. Web search was used for discovery; grant
aggregators and company trackers were **not** treated as authoritative and
every item sourced from them is flagged. Items marked **verify** or
**unverified** have not been confirmed at the issuing organization.

Nothing here is legal, regulatory, or financial advice. Parts III.1 and
III.3 in particular need qualified counsel before being relied on.

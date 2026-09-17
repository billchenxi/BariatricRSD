# Direction, data, and funding beyond RSD

*Researched September 17, 2026. Companion to
[NEXT_PAPER_PLAN.md §8](NEXT_PAPER_PLAN.md#8-research-direction-beyond-rsd--september-17-2026),
which covers the event-anticipation pivot, label recovery, and an academic
NIH R21 route.*

**This memo assumes a different goal than every other planning document in
this repository.** The stated intent is now: independent research, not a
postdoc or faculty track, with the eventual aim of selling a product.
That inverts most of the earlier advice. Academic PI eligibility stops
mattering; dataset licensing, IP ownership, and FDA classification start
mattering enormously. Sections 5–9 are written for that goal and
**supersede** the funding guidance in §8 of NEXT_PAPER_PLAN.md and in
[cdmrp_fy27_path.md](../grants/cdmrp_fy27_path.md).

Sections 1–4 (market risk to the bariatric framing, the three data layers,
foundation-model crowding, journal tiers) apply to either goal — papers are
still worth writing, just as credibility assets rather than career currency.

**Every date and dollar figure below must be re-verified at the source
before it is used.** Grant aggregators and company trackers were used for
discovery only, never as authority. Nothing here is legal, regulatory, or
financial advice.

---

## 1. The strategic problem nobody has written down yet

**Bariatric surgery is a shrinking procedure, and the decline is
accelerating.** This is not a minor caveat — it changes how a 2027
reviewer reads "bariatric" in a title or specific aim.

- US metabolic/bariatric surgery volumes fell after a 2022 peak,
  ending seven consecutive years of growth. Reported declines vary by
  denominator and source: roughly **23% from 2022–2024**, with some
  analyses reporting **~39% through Q4 2025** and steeper figures among
  eligible patients.
  ([ASMBS 2026 meeting coverage](https://www.medscape.com/viewarticle/glp-1-uptake-rises-metabolic-surgery-rates-decline-2026a1000fg5),
  [Harvard Chan](https://hsph.harvard.edu/news/bariatric-surgeries-on-the-decline-as-use-of-glp-1-drugs-rises/),
  [utilization study](https://pubmed.ncbi.nlm.nih.gov/42467193/))
- GLP-1 prescribing for obesity roughly **doubled 2022–2023** and kept
  climbing through 2024.
- **Semaglutide lost patent exclusivity in March 2026.** Generic entry and
  30–50% price declines are expected, which plausibly intensifies the
  pressure on elective surgical demand rather than relieving it.

### What this means concretely

| Implication | Action |
|---|---|
| "Improve OR throughput for gastric bypass" is a weak 2027 aim | Do not make bariatric throughput the headline problem |
| MB140 becomes harder to extend with new cases | Treat MB140 as a fixed historical cohort, not a growing one |
| Reviewers will ask about GLP-1 displacement unprompted | Address it in one sentence in every aim/abstract, do not wait to be asked |
| Bariatric-specific funders (ASMBS, NIDDK obesity) face the same headwind | Weight general-surgery and methods funders higher |

**The reframe that survives this:** bariatric video is your *substrate*, not
your *subject*. The scientific object is procedural-workflow measurement and
anticipation under center shift — demonstrated on gastric bypass because
MB140 is the best-annotated two-center cohort that exists, not because
bariatrics is the target market. Cholecystectomy (Cholec80, Endoscapes,
CholecT50, SAGES CVS) is the volume-stable general-surgery anchor and should
carry equal weight in the framing.

This does not argue against the §8 plan. It argues for how the §8 plan
should be *named and pitched*.

---

## 2. What knowledge to add: three layers, not more video

Your bottleneck is not encoder quality or compute. It is that every asset
you hold lives in one layer — pixels plus workflow labels. Each tier of
journal corresponds to adding a layer.

```
  Layer C   Action / physics      tool pose, kinematics, force, commanded vs executed
            ─────────────────────────────────────  Science Robotics, Nature BME
  Layer B   Patient / outcome     30-day complications, reoperation, readmission
            ─────────────────────────────────────  Nature Medicine, Annals, NEJM AI
  Layer A   Context               audio, room video, device telemetry, vitals, EHR
            ─────────────────────────────────────  npj Digital Medicine
  Layer 0   Pixels + workflow     ← everything you have today
            ─────────────────────────────────────  MICCAI, IJCARS, MedIA
```

### Layer B — outcome linkage (highest value per unit of effort)

This is the layer §8 ranks last ("least supported today") and I think that
ranking is wrong on *value*, even if right on *current feasibility*. The
single highest-impact precedent in your exact procedure is outcome linkage:

- Birkmeyer et al., **NEJM 2013** — 20 Michigan bariatric surgeons, one
  representative gastric bypass video each, blinded peer skill ratings
  (2.6–4.8 on a 5-point scale). Higher skill → fewer complications, fewer
  reoperations, readmissions, and ED visits.
  ([NEJM](https://www.nejm.org/doi/full/10.1056/NEJMsa1300625))
- The **JACS 2016** follow-up found skill ratings did *not* predict
  1-year weight loss or resolution of sleep apnea, hypertension, or
  hyperlipidemia. ([PubMed](https://pubmed.ncbi.nlm.nih.gov/27074114/))

That pair is a thirteen-year-old result built on **20 videos and human
raters**. Nobody has replicated it with automated, foundation-model-derived
workflow metrics at cohort scale, and the negative half of it (skill
predicts safety, not efficacy) is exactly the kind of nuance that a
well-powered automated study could sharpen or overturn.

**Obtainable linkage assets:**

| Asset | What it gives | Access reality |
|---|---|---|
| [MBSAQIP PUF](https://asmbs.org/about/mbsaqip/) | ~775k cases, 925 hospitals, 30-day outcomes, standardized | Participant-Use File request through ACS; **no video**, and no case-level key to MB140 |
| ACS NSQIP PUF | Same structure, general surgery | Same route |
| Institutional EHR at a collaborator site | The only way to get **video ↔ outcome on the same patient** | Requires IRB + a surgical department partner; this is the long pole |

**Be honest about the hard part.** MBSAQIP gives you outcomes with no video;
MB140 gives you video with no outcomes. They do not join. A registry-only
paper is a different (and already crowded) genre — ML on MBSAQIP tabular data
has been done repeatedly for VTE, readmission, and same-day discharge.
([systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC13167840/))
The contribution only exists if video and outcome are linked at the case
level, which means one hospital, one IRB, one surgical partner. **That
conversation is the highest-value thing you can start this quarter**, and it
has a 12–18 month lead time, so starting it now costs you nothing and buys
you the option.

### Layer C — action and physics (what "physical AI" actually requires)

§8 correctly notes video alone does not reveal force. To make any claim in
this space you need synchronized action data. The bar has moved:

- **Science Robotics (2025)** published surgical embodied intelligence with
  an open simulator and zero-shot sim-to-real transfer to laparoscopic
  robot tasks. ([paper](https://www.science.org/doi/10.1126/scirobotics.adt3093),
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/40668896/))
- **ORBIT-Surgical** gives 14 benchmark dVRK/STAR tasks on Isaac Sim, up
  to 8000 parallel envs on one RTX 3090, with demonstrated sim-to-real on a
  physical dVRK. This is the cheapest credible on-ramp — no hospital, no
  IRB, one GPU. ([arXiv](https://arxiv.org/pdf/2404.16027),
  [site](https://orbit-surgical.github.io/))
- **SurgWMBench** (arXiv, Aug 2026) already argues the exact methodological
  point you would want to make — that FVD/CD-FVD generation metrics do not
  measure whether predicted trajectories are geometrically accurate,
  temporally coherent, or actionable for planning — and supplies
  motion-centric metrics instead. ([arXiv](https://arxiv.org/abs/2608.08070))

**Read that last one carefully before committing.** It is close to the
"pixel metrics are not enough" claim in your archived Physical AI plan.
Your remaining differentiator in this layer is *calibration and abstention
under distribution shift* — when should the system stop and ask for help —
not "world models for surgery," which is now occupied.

NVIDIA has also shipped a healthcare-robotics stack (Cosmos-based
simulation, VLA models) with CMR Surgical, J&J MedTech, and Medtronic as
early adopters. That is good for tooling availability and bad for novelty
claims framed around the tooling.
([NVIDIA](https://blogs.nvidia.com/blog/national-robotics-week-2026/),
[CMR Surgical](https://www.surgicalroboticstechnology.com/news/cmr-surgical-advances-physical-ai-with-nvidia/))

### Layer A — OR context (cheapest genuine novelty)

Multimodal OR data acquisition (MODAL / "OR black box") integrates surgical
equipment, physiologic monitors, EHR, and ambient audio-video. A 2026 review
notes terminology and governance are still unstandardized — meaning the
field is open. ([review](https://onlinelibrary.wiley.com/doi/10.1002/lio2.70400))

Concretely obtainable today:
- **[VitalDB](https://www.nature.com/articles/s41597-022-01411-5)** — 6,388
  surgical cases, high-resolution intraoperative vitals, open. No video, but
  it lets you build and validate the physiological arm of a model before you
  have a linked cohort, and it is the standard citation for perioperative
  waveform work.
- **MM-OR**, **EgoExOR** — room-level multimodal OR datasets for activity
  understanding.
- Surgical Safety Technologies' Black Box platform is the commercial route;
  academic access is institution-by-institution.

**The unclaimed question in this layer:** does remaining-duration /
anticipation accuracy improve when the model sees the *room* (staff
movement, instrument requests, anesthesia state) and not only the
laparoscope? That is a genuinely open, clinically legible question, and it
is closer to your existing skill set than robotics is.

---

## 3. Crowding check: what is already taken

This is the main reason not to run Paper 2A as a backbone comparison. In the
last twelve months:

| Work | What it occupies |
|---|---|
| [SurgVISTA](https://www.nature.com/articles/s41746-026-02403-0) (npj Digital Medicine, 2026) | Large-scale self-supervised surgical video FM, broad downstream eval |
| [SurgΣ](https://arxiv.org/html/2603.16822) (arXiv, Mar 2026) | 6 specialties, 18 tasks, 5.98M conversations, unified multimodal schema |
| SurgRec | Reproducible pretraining recipe, 10,535 videos / 214.5M frames, 16 downstream datasets |
| [SurgWMBench](https://arxiv.org/abs/2608.08070) (Aug 2026) | World-model motion-planning benchmark and metrics |
| [Surg-R1](https://arxiv.org/pdf/2603.12430) | Hierarchical reasoning FM with multi-center clinical validation |
| [SurgXBench](https://arxiv.org/html/2505.10764) | Explainable surgical VLM benchmark |

An encoder leaderboard is not publishable at the top tier in this
environment. Your §8 instinct — reliable anticipation with decision-relevant
evaluation — is right.

### The contribution that is genuinely unoccupied

Your Phase 0 findings are the asset, and you are currently treating them as
an embarrassment to be disclosed rather than a result to be published:

- 98% of paired conditioning-effect variance is between-fold, 2%
  between-seed; effects below ~0.5 min are not resolvable on a 5-fold split
  at any seed count. ([finding](phase_0/PHASE_0_FINDING_FOLD_VARIANCE.md))
- The k-means phase-order cluster id is seed-unstable (ARI 0.63) and not
  recovered by an independent representation family (ARI 0.03–0.08).
  ([finding](phase_0/PHASE_0_FINDING_REPRESENTATION.md))

The field is publicly worried about exactly this. See *"Surgical scene
understanding and the emerging challenge of independent validation in an
industry-led AI ecosystem"*
([npj Digital Medicine, 2026](https://www.nature.com/articles/s41746-026-03028-z))
and the systematic review finding intraoperative video AI still rarely
reaches dependable clinical use
([PubMed](https://pubmed.ncbi.nlm.nih.gov/42496894/)); in adjacent orthopaedic
AI devices, only **8.6%** were validated by a prospective clinical trial
([review](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12879955/)).

**A measurement-validity paper for surgical video AI** — what effect sizes
are resolvable on the standard benchmarks, which reported gains are inside
fold noise, which representations are identifiable, and what a minimum
protocol should be — is a real contribution, is fully supported by assets you
already have, needs no new data, and has a plausible home in *npj Digital
Medicine* or *Medical Image Analysis*. It also makes every subsequent paper
you write harder to attack.

This is the one direction here you could start tomorrow with zero new access.

---

## 4. Journal tier: the honest mapping

§8 has a fit table. This adds the *entry price*, which is the part that
decides whether a submission is worth the months.

| Tier | Venue | Non-negotiable entry price | Your gap |
|---|---|---|---|
| Flagship clinical | Nature Medicine, NEJM AI, JAMA Surgery, Annals of Surgery | Prospective or multicenter evidence tied to **patient outcomes or clinician behavior** | Layer B; ~18–24 months |
| Flagship embodied | Science Robotics | Closed-loop physical experiments, perturbation, recovery, generalization | Layer C + hardware partner |
| Flagship engineering | Nature Biomedical Engineering | Substantial engineering advance **plus** functional/ex vivo/wet-lab validation | Layer C, or a bench validation |
| Flagship ML | Nature Machine Intelligence | A general learning principle demonstrated beyond one procedure | Needs ≥3 procedures + a transferable mechanism |
| Strong specialist | npj Digital Medicine | Defined user and decision, independent cohort, reader or prospective eval | **Reachable in 2027** via the measurement-validity or OR-context paper |
| Strong technical | Medical Image Analysis, IEEE TMI | New method + strong ablations + independent validation | **Reachable in 2027** |
| Solid | MICCAI, IJCARS, npj Digital Surgery | Rigorous focused study | Reachable now |

**Read this plainly:** nothing in your current asset base reaches the top
row, and no amount of additional modeling on MB140 + Cholec80 will get it
there. The top tier is bought with linkage, prospect, or physics — not with
better encoders. The realistic 2027 ceiling is npj Digital Medicine / MedIA,
and the way to make 2028–29 top-tier possible is to start a Layer B or
Layer C partnership *now*, in parallel with a 2027 specialist paper.

Any prospective evaluation should be reported under
[DECIDE-AI](https://www.nature.com/articles/s41591-022-01772-9).

---

## 5. The blocker on the product path: every dataset you use is non-commercial

**This is the most important finding in this memo.** Verified
September 17, 2026, at the source repositories:

| Dataset | License | Consequence |
|---|---|---|
| **MultiBypass140** | **CC BY-NC-SA 4.0** — "available for non-commercial scientific research purposes as defined in the CC BY-NC-SA 4.0" ([repo](https://github.com/CAMMA-public/MultiBypass140)) | No commercial use |
| **Cholec80** | **CC BY-NC-SA 4.0** ([CAMMA datasets](http://camma.u-strasbg.fr/datasets/)) | No commercial use |
| **CholecT50** | **CC BY-NC-SA 4.0** ([repo](https://github.com/CAMMA-public/cholect50)) | No commercial use |
| Endoscapes2023 | PhysioNet credentialed access + DUA | Terms must be read before any product use |

Two separate problems, and the second is worse than the first:

1. **NonCommercial (NC)** — you cannot use these data for commercial
   purposes. Not to train a shipped model, not for a demo to an investor,
   not for a pilot a hospital pays for.
2. **ShareAlike (SA)** — adaptations must be distributed under the same
   license. Whether trained model weights count as an "adaptation" under
   CC is **legally unsettled**, and that is precisely the problem: it does
   not need to be settled against you to hurt. It only needs to be an open
   question for an acquirer's counsel or a hospital's legal department to
   flag in diligence.

**I am not a lawyer and this is not legal advice.** But the practical
conclusion is not close: **a product cannot be built on model weights
derived from MB140, Cholec80, or CholecT50.**

### What follows from this

You need **two separate data lineages**, and you need to keep them clean
from today, because retroactively proving a model never touched NC data is
nearly impossible.

```
  RESEARCH LINEAGE                      PRODUCT LINEAGE
  MB140, Cholec80, CholecT50            data you own or license commercially
  → papers, benchmarks, methods         → shipped weights
  → credibility, citations              → revenue
  ↳ never ships                         ↳ never needs the academic data
      └──────── what crosses over: the METHOD, the CODE, the
                EVALUATION PROTOCOL, and your reputation ────────┘
```

What legitimately crosses the boundary is the part that is *not* the data:
the architecture, the training recipe, the evaluation protocol, and the
Apache-2.0 code you already own in this repository. That is real
transferable value — it is just not a trained model.

**The product's data strategy therefore has to be: train on the
customer's own video, under a commercial data-use agreement.** This is
what the incumbents do, it is why they all sell a capture layer first, and
it means your first paying pilot is simultaneously your first training set.
Plan for that, rather than hoping to ship a pretrained model.

**Action this week:** add a `DATA_LINEAGE.md` to the repo recording which
checkpoints touched which datasets, with hashes. It costs an hour now and
is the document that makes a future diligence process survivable.

---

## 6. Market reality check: the best-funded company in this space just failed

- **Caresyntax** — OR data capture and AI analytics, founded 2013,
  **$488M raised** including a $180M Series C extension in 2024 — **filed
  for bankruptcy in May 2026.**
  ([Tracxn](https://tracxn.com/d/companies/caresyntax/__0AGGHuKGsKMvCnYHKFu1vdhek60PcdaaLN3ScjTJv4M),
  [CB Insights](https://www.cbinsights.com/company/caresyntax),
  [$180M round](https://www.caresyntax.com/news/caresyntax-raises-180-million-funding-to-accelerate-growth-and-adoption-of-precision-surgery-2))
  Aggregator-sourced; confirm before repeating it in writing to an
  investor. But it is consistent across three independent trackers.
- Remaining field: Theator, Surgical Safety Technologies, Proximie,
  Artisight, plus incumbents Intuitive, Medtronic, Brainlab who own the
  hardware channel.

**Read the failure mode correctly.** Caresyntax did not fail for lack of
model accuracy or lack of capital. The OR-analytics platform business
requires putting hardware in operating rooms, integrating with hospital IT,
and surviving 12–24 month enterprise sales cycles against vendors who
already own the tower. That is a capital-intensive, distribution-bound
business, and it is the single worst possible shape of business for an
individual researcher to attempt.

### The two wedges that are actually available to one person

**Wedge A — software that rides someone else's capture layer.**
Do not sell cameras. Sell a model that consumes video and telemetry a
hospital already records (Black Box, Theator, the robot's own log, the
tower's recording output) and returns scheduling and throughput signal.
Sell it to the surgical services line, or to the capture vendor as OEM.
This is where your RSD work already sits, and it needs no OR hardware.

**Wedge B — independent validation of surgical AI. This is the one your
assets uniquely support and nobody is serving.**

The field has a publicly stated validation crisis:
- npj Digital Medicine (2026) on the "emerging challenge of independent
  validation in an **industry-led** AI ecosystem"
  ([link](https://www.nature.com/articles/s41746-026-03028-z))
- a systematic review finding intraoperative video AI still rarely reaches
  dependable clinical use ([link](https://pubmed.ncbi.nlm.nih.gov/42496894/))
- in adjacent orthopaedic AI devices, only **8.6%** were validated by a
  prospective clinical trial
  ([link](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12879955/))

Your Phase 0 findings are, in commercial terms, a **demonstrated
capability to detect that a reported surgical-AI gain is inside noise.**
Fold-variance dominance and representation non-identifiability are exactly
the failure modes vendors will not self-report. As these products
proliferate, hospitals, insurers, and device makers will need someone who
is not the vendor to check the claims — and that work is software-only,
sells to a budget holder who already exists (procurement, quality, risk),
carries no FDA exposure, and is billable on day one while the research
program continues.

It also inverts the licensing problem: validation work runs on the
*customer's* data, so the NC restriction in §5 never binds.

---

## 7. The regulatory fork that decides your product shape

FDA issued a revised final **Clinical Decision Support Software** guidance
on **January 6, 2026** (re-issued January 29, 2026), replacing the
September 2022 version.
([FDA guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software),
[Covington analysis](https://www.cov.com/en/news-and-insights/insights/2026/01/5-key-takeaways-from-fdas-revised-clinical-decision-support-cds-software-guidance))

Software meeting all four criteria of 21st Century Cures
§520(o)(1)(E) is **Non-Device CDS** and is outside FDA premarket review.
The 2026 revision moved the **time-critical decision making** limitation
out of Criterion 3 and into **Criterion 4**, on the position that software
intended for time-critical decisions cannot let a clinician independently
review the basis for its recommendation.

**Translated into your product decision:**

| Product | Likely status | Time to revenue |
|---|---|---|
| Real-time intraoperative RSD display, live deviation alert | **Likely a regulated device** — time-critical, in-the-moment | Years; premarket submission, clinical evidence |
| Between-case / post-hoc OR scheduling, throughput, staffing analytics | **Plausibly Non-Device CDS** — not time-critical, reviewable basis | Months |
| Retrospective quality review and validation reports (Wedge B) | Furthest from device status | Immediate |

This is the clearest strategic fork in the whole memo, and it points the
opposite way from where the research instinct pulls. The scientifically
exciting product is the live intraoperative one; the *sellable* product is
the boring between-case one. **Ship the boring one, fund the exciting one
with it.**

Get a regulatory consultant to confirm the classification before you build.
This is a few thousand dollars and it determines your entire roadmap.

---

## 8. Funding as an independent researcher building a product

The §8 table in NEXT_PAPER_PLAN.md is built for an academic PI. Almost none
of it fits now. **SBIR/STTR is the mechanism**, and it fits your situation
better than any academic route could.

### Why SBIR is the right instrument for you specifically

1. **It solves the PI-eligibility problem permanently.** The unresolved
   question in your CDMRP memo — whether you can be PI — disappears. In
   SBIR you are PI of your own company. The requirement is that the PI be
   **primarily employed** by the small business, meaning more than half
   your time. If this is your main activity, you satisfy it by definition.
   ([SBIR eligibility](https://www.sbir.gov/tutorials/program-basics/tutorial-2))
2. **You keep the IP.** The small business owns and has full right and
   title to data developed under the award; the government takes a limited
   license, with SBIR data rights protection typically running ~20 years.
   Under a university grant, the university owns it. For someone who
   intends to sell a product, this difference is the whole ballgame.
   ([SBIR data rights](https://www.sbir.gov/faq/data-rights))
3. **It is non-dilutive.** No equity, no board seat, no liquidation
   preference ahead of you.

**STTR variant, worth knowing:** STTR requires a partnering research
institution doing ≥30% of the work (small business ≥40%), and the PI does
**not** have to meet the primary-employment test. If you want to keep a
UCSC affiliation, STTR is the path that allows it.

### Targets

All amounts and dates below are **discovery-grade and must be verified** at
[sbir.gov](https://www.sbir.gov), [grants.gov](https://www.grants.gov), and
[seedfund.nsf.gov](https://seedfund.nsf.gov) before you act.

| Program | Fit | Amount / cadence | Notes |
|---|---|---|---|
| **NIH SBIR omnibus, PA-27-100** | Primary target. Digital health and medical software file here | Phase I reported up to **$400k–$700k** depending on the IC. Standard dates reported as **Sep 5 2026, Jan 5 2027, Apr 5 2027, Sep 5 2027** | Pick your IC deliberately — NIBIB for the imaging/methods framing, NIDDK for bariatric, **AHRQ for the OR-efficiency framing, which is the strongest fit for Wedge A** |
| **NSF SBIR/STTR** | Good second shot; deep-tech framing, less clinical burden | Relaunched with **$250M**; Phase I ceiling **$305k**, 6–18 months. Deadlines reported as Jul 27 2026 (passed), **Nov 4 2026**, **Mar 4 2027** | **Mandatory Project Pitch** on-ramp before a full proposal — a short, low-cost, fast-feedback filter. Do this first regardless; it costs days, not months |
| **ARPA-H SBIR** | Ambitious; ties to the AIR robotic-surgery program | Varies | [SBIR page](https://arpa-h.gov/explore-funding/sbir). Note AIR's main solicitation closed March 18, 2026 with awardees announced Aug 2026 — the route in now is **subaward to a funded AIR team**, which is also a customer-discovery channel |
| **NVIDIA Inception** | Compute and credits for startups | In-kind, free to join | Replaces the NVIDIA Academic Grant Program in your plan, which requires **full-time faculty** and no longer applies |

### Rule out, to save you time

- **Schmidt AI in Science fellowships** — explicitly do not fund AI applied
  within medical sciences, and are postdoctoral anyway.
  ([Oxford](https://saiis.web.ox.ac.uk/))
- **Intuitive Foundation, SAGES, ASMBS grants** — structured for
  **non-profit institutions**. Not available to a company. They remain
  available if a clinical collaborator holds the award; that is a reason to
  find a collaborator, not a funding line for you.
- **NIH R21/R03, NSF SCH/PESOSE/FRR** — require an eligible institution and
  give the IP to it. Only relevant through a collaborator.

### Registrations — start now, they are the hidden deadline

SAM.gov, SBA company registry, eRA Commons, Grants.gov, and the small
business itself. These take **weeks**, they are sequential, and missing one
forecloses a whole cycle. The most common way people lose a year to SBIR is
registration, not science.

Eligibility basics to confirm: US-based for-profit, ≤500 employees, >50%
owned and controlled by US citizens or permanent residents. Also confirm
that you personally will meet the >50% time test, since that interacts with
any teaching or employment you hold.

---

## 9. Recommendation

Three tracks, running concurrently. None waits on the others.

### Track 1 — Ship the measurement-validity paper (next 4 months)

The paper from §3, built entirely on assets you already hold. Zero new
data, zero new access, zero licensing exposure. Target npj Digital Medicine
or Medical Image Analysis.

For an independent researcher this is not career currency — it is **the
credibility asset that makes Wedge B sellable.** "The person who showed
these benchmarks don't replicate" is a position you can charge for. "A
person with a startup" is not.

### Track 2 — Incorporate and file a Project Pitch (next 8 weeks)

1. Form the company. Begin SAM.gov / SBA / eRA Commons registration the
   same week.
2. Write `DATA_LINEAGE.md` (§5) before any further training run.
3. File an **NSF Project Pitch** — days of work, fast official feedback on
   whether the framing lands, and no commitment.
4. Aim at **NIH SBIR Jan 5 or Apr 5, 2027**, most likely through AHRQ with
   the OR-efficiency framing.

### Track 3 — Pick the wedge, and pick the boring one

Build the **between-case OR analytics** product (§7), not the live
intraoperative one. It is very likely outside FDA premarket review, it
sells to an existing budget holder with an explicit ROI (OR time reported
up to ~$2,190/hr; OR ~42% of hospital revenue), and it is the natural home
for the RSD work you have already done. Fund the intraoperative version
later, out of revenue, when you can afford the regulatory path.

Sell **Wedge B (validation)** alongside it from day one. It is billable
immediately, it requires nothing but your existing expertise, and it puts
you in the room with exactly the hospitals whose video you will later need
under a commercial DUA to solve the §5 problem.

### And keep the framing change from §1

Not "bariatric RSD." Procedural workflow measurement and calibrated
anticipation under center shift. Bariatric volume is down 23–39% since 2022
and semaglutide went off-patent in March 2026 — you do not want your
company's name, your grant title, or your pitch to be attached to a
shrinking procedure.

---

## Sources

Primary sources are linked inline. Web search was used for discovery;
grant aggregators and company trackers were **not** treated as
authoritative and every item sourced from them is flagged. Nothing here is
legal, regulatory, or financial advice — §5 and §7 in particular need
qualified counsel before you rely on them.

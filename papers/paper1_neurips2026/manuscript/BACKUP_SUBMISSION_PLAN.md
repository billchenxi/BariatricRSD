# Backup Submission Plan

**Created:** 2026-04-25
**Primary target:** NeurIPS 2026, **Evaluations & Datasets** track
(submission deadline May 4 abstract / May 6 full paper, per current draft —
verify on official NeurIPS site before locking)

This document lists fallback venues if the NeurIPS 2026 submission is
rejected, withdrawn, or strategically redirected. The work is positioned
to fit several venues with minimal rewriting; this file is the rebuilding
plan for each.

---

## 1. The work, in one paragraph

A workflow-conditioned RSD predictor evaluated on MultiBypass140 (positive)
and Cholec80 (null), with a causal-at-inference variant that recovers the
retrospective oracle's gain on within-center fold 0 of MultiBypass140
(12.56 ± 0.04 min vs 12.59 ± 0.33 min, 3 seeds each). Central claim: the
benefit of explicit workflow conditioning scales with the workflow
variability in the dataset.

This positions equally well as:

- An **evaluation-and-benchmarking paper** (NeurIPS E&D, ML4H, MIDL).
- A **medical-imaging methods paper** (MICCAI, IPCAI, IJCARS, MedIA).
- A **clinical-AI / surgical-AI paper** (TMI, JBHI, npj Digital Medicine).
- A **workshop paper / poster** (NeurIPS workshops, MICCAI workshops,
  CVPR Computer Vision in Medicine workshop).

---

## 2. Venue ladder — primary → fallbacks

| Tier | Venue | Track / format | Typical deadline | Fit | Acceptance bar |
|---:|---|---|---|---|---|
| 1 (primary) | **NeurIPS 2026** | Evaluations & Datasets | early May 2026 | Strong | ~25% |
| 2 (high) | **MIDL 2026** (Medical Imaging with Deep Learning) | Full paper | typically mid-Jan, **already past for 2026** — target MIDL 2027 | Strong | ~50% |
| 2 (high) | **ML4H 2026** (Machine Learning for Health) | Proceedings track | typically mid-Sept | Strong | ~30% |
| 3 (medium) | **MICCAI 2026** | Workshop paper (e.g. SUSI / EARTH) | March–May for workshops | Good | varies |
| 3 (medium) | **CVPR 2027** | Computer Vision in Medicine workshop | late Feb 2027 | Moderate | varies |
| 3 (medium) | **IPCAI 2027** | Information Processing in CAI | typically Jan | Strong | ~50% |
| 3 (medium) | **WACV 2027** | Application track | typically July 2026 | Moderate | ~30% |
| 4 (journal) | **IEEE Transactions on Medical Imaging (TMI)** | Journal | rolling | Strong | ~25%, slow |
| 4 (journal) | **Medical Image Analysis (MedIA)** | Journal | rolling | Strong | ~25%, slow |
| 4 (journal) | **IJCARS** | Journal | rolling | Good | ~50%, faster than TMI/MedIA |
| 4 (journal) | **npj Digital Medicine** | Journal | rolling | Moderate (more clinical bent) | varies |
| 5 (workshop only) | **NeurIPS 2026 workshops** | Workshop submission ($\rightarrow$ poster) | typically Aug–Sept | Excellent fallback | ~50% |
| 5 (workshop only) | **MICCAI 2026 workshops** | Workshop submission | varies by workshop | Excellent fallback | ~50% |

---

## 3. What the poster file in `paper/poster.md` and `paper/poster.tex` is for

- **If NeurIPS accepts**: standard NeurIPS poster session (every accepted
  paper presents a poster). Use as-is, possibly tightened.
- **If NeurIPS rejects but a workshop accepts**: most workshops accept
  posters or "extended-abstract + poster" formats. Use as-is.
- **If we redirect to MIDL / MICCAI / IPCAI**: poster format is similar
  (A0 portrait or 36×48 landscape); minimal re-layout needed.
- **For Bill's lab visits / talks / departmental seminars**: also useful
  as-is.

The poster captures the same scientific content as the full manuscript
but in 10 panels, optimized for skim-reading at a 2-meter distance.

---

## 4. Concrete rebuild plan if NeurIPS rejects

### Scenario A: rejected outright, no constructive review feedback

1. **Withdraw revisions**: take the paper exactly as submitted to
   NeurIPS, no large changes.
2. **Re-target to ML4H 2026** (proceedings track): deadline typically
   mid-September. Bigger window to act.
3. **Repackage as workshop submission** (NeurIPS or MICCAI workshop)
   in parallel — workshop deadlines are typically later than the main
   conference, so this is a hedge.

### Scenario B: rejected with constructive criticism

1. **Read all reviews, write a rebuttal-style internal memo** in
   `paper/review_responses.md` for each major concern.
2. **Do the additional experiments reviewers asked for** (likely:
   surgical-domain pretraining, more folds, 5-fold causal completion,
   K-cluster sensitivity sweep — most of these are already on our
   experiment plan).
3. **Re-target to MIDL 2027** (deadline Jan 2027) or **IEEE TMI**
   (rolling). Both reward thoroughness over speed.

### Scenario C: invited for conditional acceptance / minor revisions

1. **Address all reviewer asks**, rebuild figures, re-time the
   Cholec80 numbers under the canonical 40-video split if achievable.
2. **Submit camera-ready** before deadline.

### Scenario D: paper accepted to NeurIPS

1. **Use the poster file as-is** for the NeurIPS poster session.
2. **Build a 5-minute lightning-talk slide deck** at
   `paper/slides/neurips_talk.md` for any oral component (varies by
   acceptance type).
3. **Release code** under `brsd_lib` MIT license at the camera-ready
   deadline.
4. **Plan a follow-up**: the natural successor is a *fully causal*
   training pipeline (no teacher forcing) plus surgical-domain
   pretraining. Targets MIDL 2027 or MICCAI 2027 main track.

---

## 5. Pre-built artifacts available for any submission

| Artifact | Path | Repurposes for |
|---|---|---|
| Full manuscript (markdown) | `paper/review_manuscript.md` | NeurIPS, ML4H, MIDL, TMI, MedIA |
| Full manuscript (docx) | `paper/review_manuscript.docx` | Word-based reviewers |
| Full manuscript (pdf) | `paper/draft.pdf` | Anonymized version → OpenReview |
| Poster (markdown) | `paper/poster.md` | NeurIPS, workshop, lab seminar |
| Poster (LaTeX skeleton) | `paper/poster.tex` | Compile to A0 PDF for any venue |
| Lecture deck | `paper/slides/lecture.md` / `.pptx` | Departmental talk, defense practice |
| Teaching guide | `paper/slides/lecture_teaching_guide.pdf` | Course material, lab onboarding |
| Experiment plan | `paper/EXPERIMENT_PLAN.md` | Proposal, response-to-reviewer |
| Results manifest | `paper/results_manifest.csv` | Reproducibility statement, rebuttal evidence |
| Code library | `brsd_lib/` | Open-source release |

This list is what we'd give a reviewer asking for "all your supporting
material." It's also what makes a smooth workshop fallback possible: every
artifact already exists and only needs minor format adaptation.

---

## 6. Things to NOT do under deadline pressure

- **Don't** chase a Cholec80 SOTA on the canonical 40-video split — we
  don't have phase labels for the 8 missing videos.
- **Don't** introduce a new architecture variant just to make the paper
  look more novel — the contribution is the evaluation insight, and
  making it look like an architecture paper would be a regression.
- **Don't** withdraw from NeurIPS to "polish more" — the work is
  publishable now. Submit, get reviews, iterate.
- **Don't** split this into two papers (one E&D, one Main) — it would
  fragment the contribution. One submission, one venue at a time.

---

## 7. Decision points

| If by | Decision | Action |
|---|---|---|
| 2026-05-06 | NeurIPS submitted | Wait; build poster for NeurIPS poster session |
| 2026-08 | NeurIPS reviews back | If accept: poster + camera-ready. If reject: pick scenario A/B above. |
| 2026-09 | NeurIPS rejected | ML4H 2026 deadline + NeurIPS workshop deadline both approaching; pick one. |
| 2026-12 | NeurIPS rejected, ML4H rejected | MIDL 2027 deadline mid-Jan 2027; major revision window |
| 2027-01 | MIDL submitted | Done for the year on this work; start follow-up project |

---

*This file evolves with the submission process. Update each decision row
as outcomes land.*

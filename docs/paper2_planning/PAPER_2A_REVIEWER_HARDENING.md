# Paper 2A — Hardening Against the NeurIPS 2026 Reviewer Critique

*Created 2026-06-04, immediately after the NeurIPS 2026 rejection of
Paper 1. This document maps each reviewer concern from Paper 1 to a
concrete Paper 2A design change. It is a companion to
`NEXT_PAPER_BRIEF.md` and `NEXT_PAPER_PLAN.md` — it does not replace
them, it constrains them.*

---

## Why this document exists

Paper 1's three reviewers converged on five substantive concerns.
Three are directly addressable in Paper 2A because they map onto
experiments we were already planning. Two require deliberate scope
expansion. This document locks the expansions in before Phase 0
infrastructure work starts, so we don't build an evaluation harness
that has to be rebuilt in Phase 2.

---

## Concern-to-fix map

| Paper 1 concern (source) | Paper 2A fix | Effort added |
|---|---|---|
| Two-dataset confound (all three reviewers, AC lead concern) | **Add ≥ 1 third surgical benchmark.** Primary candidate: AutoLaparo (hysterectomy + sleeve gastrectomy, phase-labeled, public). Backup: HeiChole (laparoscopic cholecystectomy, additional center). Both provide independent variation in workflow entropy *H(z)*. | +1 dataset in feature-extraction and eval loops. ~+15% Phase 1/2 compute. |
| 5-fold instability (Xmi1, 6eLx) | **Fold-level analysis as a first-class result**, not an appendix afterthought. Report per-fold effect sizes with paired video-level Wilcoxon inline in the results section. Add a **variance-decomposition** analysis: seed variance vs fold variance vs backbone variance. | +0.5 pp of the results section (dedicated fold-stability paragraph). No new compute. |
| Sub-1-min clinical utility (Xmi1) | **Abstract explicitly scopes as algorithmic-effect study, not clinical utility.** First sentence names it: *"We study when a workflow-conditioning signal exists in surgical video, not whether the resulting model is clinically deployable."* Add a paragraph in §7 pointing to Paper 5 (prospective clinical validation) as the proper venue for utility claims. | Text-only. No new experiments. |
| Workflow-representation dependence (iSh9) | **Include at least three workflow-representation variants**: (a) TF-IDF+PCA+k-means (current), (b) learned continuous embeddings (encoder projects each video to a low-dim vector, no clustering), (c) HMM-based phase segmentation (state-space rep). Report the *H(z)* vs Δ relationship across all three. | +1 workflow-rep ablation per dataset. ~+10% Phase 2 compute. |
| Presentation complexity (iSh9), separate-supplementary formatting (6eLx) | **Single-PDF submission with appendix inline.** Rewrite abstract to lead with research question, then one paragraph of results, then one paragraph of implications. Consolidate protocol terminology in a glossary paragraph in §5. Expand related-work to ~40 references. | Editorial only. No new compute. |

---

## Additional concerns worth pre-empting

Reviewers didn't raise these, but reading the critique carefully, they
plausibly would on a resubmission:

| Anticipated concern | Preemptive fix in Paper 2A |
|---|---|
| "Your causal-evaluation protocol is just standard prefix-only anticipation, dressed up in surgical vocabulary." | Cite SWAG, Yengera 2019 explicitly. Position the *strict prefix-only* protocol as building on that literature, not inventing it. Contribution is the systematic multi-backbone × multi-dataset study, not the protocol itself. |
| "Your foundation-model comparison is a leaderboard, not a benchmark." | Frame Paper 2A as a **causal transfer benchmark** — a measurement protocol + reference results, not a competition. Explicitly release the eval harness so future FM releases can be scored under the same protocol. |
| "Your workflow-cluster method is unchanged from Paper 1; where's the novelty?" | Paper 2A's contribution is the *evaluation methodology* + *cross-dataset variability-scaling test*, not a new conditioning method. The distillation method in Paper 2B is the methodological contribution. Keep the split clean. |
| "Why not just compare oracle vs no-token; why include the complicated decoupled-oracle?" | Include the decoupled-oracle mechanism paragraph but explain the necessity in ONE sentence in the main body, with details in appendix. Paper 1's over-explanation of the mechanism was one of iSh9's readability complaints. |

---

## Updated Paper 2A scope (relative to `NEXT_PAPER_BRIEF.md`)

### Confirmed changes

1. **Add AutoLaparo as a third dataset.** Extend Phase 0 feasibility
   audit to include AutoLaparo access, license, and preprocessing.
2. **Include a third workflow-representation family.** Add "learned
   continuous embedding" and "HMM-based phase segmentation" as
   alternatives to the current k-means clustering.
3. **Elevate fold-stability to a first-class results block.** Report
   per-fold Wilcoxon + variance decomposition in the main body, not
   only the appendix.
4. **Rewrite the abstract to open with scope.** *"We characterize when
   a workflow-conditioning signal exists in surgical video — an
   algorithmic-effect study, not a clinical-utility study."*
5. **Single-PDF submission** with appendix inline. No separate
   supplementary written material (only the code + data zip as
   supplementary, per NeurIPS rules).
6. **Expand references to ~40** covering surgical-FM landscape (Paper 1
   had 15).

### Unchanged from the brief

- Two-paper split (2A benchmark + 2B distillation).
- Model matrix: ViT-B/16 + VideoMAE + V-JEPA 2/2.1 + Cosmos-Predict2 +
  SurgMotion + SurgVISTA + EndoMamba + EndoDINO + ZEN.
- Anticipation tasks (RSD + next-transition + future-phase-sequence).
- Target venue: MICCAI 2027 primary, CVPR 2027 backup.
- Cosmos-meh recovery narrative (pre-registered).
- Staged compute plan.

### Compute implications

Adding AutoLaparo + 2 extra workflow-rep families changes the budget:

| Item | Original brief | With hardening |
|---|---|---|
| Datasets in Tier 1 scout | 3 (MB140 fold 0 + cross-center + Cholec80) | 4 (add AutoLaparo) |
| Workflow-rep families in Tier 2 | 1 (k-means) | 3 (k-means + learned + HMM) |
| Paper 2A compute range | ~1,500–3,200 GPU-h | ~2,000–4,000 GPU-h |
| Paper 2A $ cost range | $4,500–$9,600 | $6,000–$12,000 |
| Combined 2A + 2B upper bound | ~$21K | ~$25K |

Roughly a 20% cost increase. Worth it — the two-dataset confound
critique alone was probably enough to kill Paper 1, and it can't be
fixed without a third dataset.

---

## What this means for Phase 0 (starting 2026 Q3)

Add these items to the Phase 0 feasibility audit checklist:

- [ ] **AutoLaparo access + license + preprocessing.** Download the
      public release. Confirm phase annotations are compatible with our
      phase-bigram pipeline. Estimate video count, duration
      distribution, workflow-cluster entropy H(z).
- [ ] **Alternative workflow-representation prototypes.** Implement a
      minimal "learned continuous embedding" head (e.g., a small
      transformer that pools per-video visual features into a 128-dim
      vector) and an HMM baseline (using per-frame phase logits as
      observations). Confirm both can be trained on MB140 in a few
      hours. Document feature shapes for the temporal head.
- [ ] **Fold-stability analysis prototype.** Write the analysis code
      (per-fold effect sizes + variance decomposition) upfront using
      Paper 1's Phase E aggregate JSON. Verify it produces the right
      numbers before we generate new data.

These are additions to the checklist in `NEXT_PAPER_PLAN.md` §Phase 0.
They don't remove anything; they extend it.

---

## Timeline impact

The original Phase 0 was Jun–Sep 2026. With these additions:

- **Jun 2026:** Original Phase 0 items (backbone feasibility audit,
  feature extraction harness, phase-anticipation evaluator, ViT-B/16
  reproduction).
- **Jul 2026:** Additional Phase 0 items (AutoLaparo audit,
  alternative-representation prototypes, fold-stability analysis).
- **Aug 2026:** Buffer for anything that spills; freeze the
  infrastructure.
- **Sep 2026:** Original Phase 1 scout matrix, now scoped over 4
  datasets × 4 backbones × 3 workflow-rep families × RSD + one
  anticipation task.

Paper 2A submission target shifts by ~1 month:

- Original: MICCAI 2027 (Feb–Mar 2027 deadline).
- Hardened: still MICCAI 2027 target, with tighter margin. CVPR 2027
  (Nov 2026 deadline) is now clearly out of reach unless we cut the
  workflow-representation ablation.

If MICCAI 2027 slips, the fallback venue is **MICCAI 2027 workshop
track** or **NeurIPS 2027 D&B** (which would then compete with Paper 2B
for the primary NeurIPS slot).

---

## Explicit non-goals

Things Paper 2A will **not** do, even in the hardened version:

1. **Clinical utility validation.** That's Paper 5. Paper 2A stays
   algorithmic-effect only.
2. **Prospective study.** Retrospective evaluation only.
3. **Real-time deployment.** Discussed as future work, not tested.
4. **New model architecture.** Uses off-the-shelf FMs + our existing
   temporal head.
5. **Full VLA / action prediction.** Anticipation tasks stay at the
   phase-transition and future-phase-sequence level, not full action
   triplets (CholecT50 stretch only).
6. **Third-party clustering method invention.** We use published
   methods (k-means, learned embeddings, HMM); we do not invent a new
   workflow representation.

Explicit non-goals prevent scope creep. When a Phase 2 experiment
tempts us into any of the above, this list is the stop sign.

---

## Bottom line

The NeurIPS 2026 rejection is expensive but not wasted. Every
substantive reviewer concern maps to a Paper 2A design change that
would have needed to happen eventually. The hardening adds ~20% to the
compute budget and ~1 month to the timeline in exchange for a paper
that no longer has the two-dataset-confound structural weakness.

The two-paper split (2A benchmark + 2B distillation) also survives the
critique unchanged — because the critiques were about *Paper 1's scope*
(too narrow, two datasets, one workflow rep, no anticipation task),
which is *exactly* what 2A was already designed to broaden.

— *End of hardening document.*

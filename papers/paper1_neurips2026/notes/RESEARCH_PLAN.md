# Research plan — bariatric RSD project and beyond

*Written 2026-04-27. Living document — revise as the situation evolves.*

---

## Executive summary

The bariatric RSD work is a foundation for a **three-paper portfolio** spanning surgical-AI venues and top-tier general-ML venues:

| # | Paper | Venue (target) | Status | Headline contribution |
|---|---|---|---|---|
| **1** | "When Workflow Conditioning Helps... A Variability-Scaling Study on MB140 + Cholec80" | **NeurIPS 2026 E&D track** (deadline ~mid-May 2026) | In flight, lock by May 1 | Evaluation insight — variability-scaling hypothesis empirically demonstrated on surgical-AI |
| **2** | "Latent-regime conditioning for time-to-completion prediction: a cross-domain scaling-law study with oracle-to-causal distillation" | **NeurIPS 2027 main track** (deadline ~May 2027); backup **ICLR 2028** (Oct 2027) | New primary — start May 2026 | Cross-domain phenomenon; distillation framework that turns oracle gain into deployable gain |
| **3** | "Workflow-cluster deviation as a signal for intraoperative adverse events" | **MICCAI 2027** (deadline ~March 2027); short paper | Optional / opportunistic | Surgical-AI specific; cheap to execute if BetaMixer IAE labels accessible |

The **central method investment** for Paper 2 is **oracle-to-causal distillation under the LUPI framework** (Lopez-Paz et al. 2016), not a from-scratch SSM architecture as initially considered. Distillation gives a sharper narrative, more stable training, and stronger theoretical grounding.

The plan locks Paper 1 first (do not multi-task before submission), then begins Paper 2 in May 2026 with a clear monthly schedule. Paper 3 is opportunistic and runs only if it doesn't slow Paper 2.

---

## Paper 1: NeurIPS 2026 E&D track (current)

### What's in
- Variability-scaling hypothesis: marginal value of workflow conditioning increases with dataset workflow variability.
- Empirical evidence across three regimes: within-center MB140, cross-center MB140, Cholec80.
- Strict prefix-only protocol contrast vs. legacy centered-window.
- Shuffled-token semantic control.
- Decoupled phase head closing the phase/cluster circularity.
- Reproducibility package (HuggingFace deposit + verify scripts).

### What's pending (lands before submission)
- Phase E 5-fold strict-protocol extension (Run 038/039/040). ETA ~12:30 PDT Apr 28.
- Run 035 strict pixel-only causal evaluation. ETA ~01:00 PDT Apr 28.
- τ sweep on best within-center checkpoint (auto-fires after Run 035). ETA ~02:45 PDT Apr 28.
- Longer-context fold-0 ablation (auto-fires after Phase E on Cluster A). ETA ~14:30 PDT Apr 28.

### What's deliberately out
- Method paper architectural novelty — that's Paper 2.
- Cross-domain validation — that's Paper 2.
- A theoretical scaffolding for the scaling law — that's Paper 2.

### Action items, this week
1. Wait for Phase E + Run 035 + tier-2 results to land.
2. Propagate landed numbers into §6.1 / §6.2 / Appendix C.1.
3. Update reviewer note from "in flight" to actual numbers.
4. Final manuscript polish.
5. HuggingFace upload of 12 checkpoints (`reproducibility/upload_to_huggingface.py`).
6. Submit.

### Lockup criterion
After May 1, **do not change manuscript scope**. New experiments after submission go into Paper 2.

---

## Paper 2: NeurIPS 2027 / ICLR 2028 (the big one)

### Reframed central claim

> *"For time-to-completion prediction in structured sequential processes, the marginal value of conditioning on a discovered latent regime variable increases with the regime variability of the underlying data distribution. Below a threshold of regime diversity, latent-regime conditioning is null or harmful. We further show that a deployable, regime-oracle-free predictor can be obtained via knowledge distillation from an oracle-conditioned teacher, generalizing the LUPI framework (Lopez-Paz et al. 2016) to time-to-completion regression."*

### Why this framing wins

1. **Generalizable**: not surgical-specific. Reviewer pool is broad ML, not narrow surgical-AI.
2. **Falsifiable scaling law**: positive on high-variability domains, null on low. Clean Bayesian / mixture-of-experts shape.
3. **Distillation bridges the deployability gap**: training-time oracle is the privileged information; student deploys without it.
4. **Theoretically grounded**: directly extends LUPI; mutual-information / mixture-of-experts framing.
5. **Three-domain validation**: surgical (existing) + cooking + instructional video. Plus a synthetic dataset for controlled scaling experiment.

### Method components

| Component | What | Existing in surgical-AI? |
|---|---|---|
| **Latent-regime discovery** | TF-IDF over event-bigrams → PCA → k-means; same pipeline as MB140 generalized to non-surgical event types | New for non-surgical |
| **Oracle-conditioned teacher training** | Standard supervised training with full-sequence regime ID prepended as a token | Existing in your work |
| **Strict prefix-only student training** | Same architecture, no oracle access; learns from prefix only | New |
| **Oracle-to-causal distillation** | KL between teacher and student RSD outputs + task loss; LUPI extended to time-to-completion regression | New for surgical RSD; LUPI is established |
| **Cross-domain validation** | Surgical (MB140, Cholec80) + cooking (YouCook2 / Breakfast / EPIC-100) + instructional (COIN / HowTo100M subset) + synthetic | Genuinely new |
| **Information-theoretic framing** | $I(z; y)$ as an upper bound on the marginal value of regime conditioning; variability of $p(z)$ controls $I(z; y)$ | New angle, supported by classical theory |

### Datasets

| Dataset | Domain | Time-to-completion target | Regime structure | Access |
|---|---|---|---|---|
| MultiBypass140 | Surgical | RSD | Phase-bigram clusters (k=6) | Have |
| Cholec80 | Surgical | RSD | Phase-bigram clusters (k=4) | Have |
| YouCook2 | Cooking | Time-to-recipe-completion | Recipe / instruction-step clusters | Public |
| Breakfast | Cooking | Cook-time prediction | Recipe clusters | Public |
| EPIC-KITCHENS-100 | Cooking | Per-segment remaining time | Activity clusters | Public |
| COIN | Instructional | Task-to-completion | Task clusters | Public |
| Synthetic procedural | Controlled | Synthetic | Parameterized $K$ regimes with controllable variability | Build it |

The minimum viable subset: MB140 + Cholec80 + YouCook2 + COIN + synthetic = 5 datasets, 3 domains. Strong enough for a multi-domain claim.

### Architecture decision (revised)

**Primary**: same backbone family as Paper 1 (ViT-B/16 + HTA), with the following additions:
- Strict prefix-only training pipeline (no full-video oracle at training).
- Decoupled phase / event-prediction head (carry over from Paper 1).
- **Distillation training loop**: teacher checkpoint loaded, student trained with KL + task loss.

**Secondary** (ablation / comparison): SSM-based online workflow encoder (Mamba). Run as a comparator to show distillation matches or beats the architectural fix.

This is a *deliberate* choice to keep the architecture close to Paper 1 — the contribution is the **methodology** (distillation, cross-domain demonstration, theory), not new building blocks. Reviewers reward identifiable contributions over novel-for-novelty's-sake architecture.

### Theoretical scaffolding

- **Mixture-of-experts identifiability**: when $p(z)$ has substantial entropy, conditioning on $z$ provably reduces excess risk in mixture regression.
- **Information-theoretic bound**: $I(z; y) \leq H(z)$, where $H(z)$ is the entropy of the regime distribution (proxy for "variability"). Establishes the upper bound on conditioning benefit.
- **LUPI extension**: distillation from oracle to causal student, formal arguments about when this works (Lopez-Paz et al. 2016 framework).

You don't need a new theorem. You need to **point at an existing principle and show your empirical claim follows**.

---

## Paper 3: MICCAI 2027 short paper (opportunistic)

### Idea
Workflow-cluster distance from centroid as a *deviation score*. Test correlation with BetaMixer (Bose et al. 2025) intraoperative adverse event labels on MB140.

### Why it's cheap
- Pipeline already exists (workflow clustering from Paper 1).
- Just need to: (a) score every video by min-distance-to-centroid, (b) cross-tab with IAE labels.
- 1–2 weeks of work if BetaMixer IAE labels are accessible.

### Why it's worth doing
- Direct clinical relevance.
- Cheap publication out of existing infrastructure.
- Concretely answers reviewers' "what's this useful for?" question.
- Side paper, doesn't compete with Paper 2 for novelty.

### Decision rule
Run only if it can complete within 2 weeks of effort, in a window that doesn't slow Paper 2's monthly milestones. If BetaMixer labels aren't accessible, drop.

---

## Master timeline

| Phase | Calendar window | Activity | Milestone |
|---|---|---|---|
| **0. Lockup** | Apr 28 – May 1, 2026 | Wait for Phase E + Run 035 to land. Propagate to manuscript. Submit Paper 1. | Paper 1 submitted |
| **1. Read Tier 1** | May 2026 (M1) | Lopez-Paz 2016, Hinton 2014, Vapnik 2009, Mamba, S4. ~30 hrs of reading. | Reading log + 1-page outline of Paper 2's argument |
| **2. Distillation prototype on MB140** | May–June 2026 (M1–M2) | Take strict decoupled-oracle teacher; train strict-prefix-only student with distillation; verify it lands within 0.3 min of teacher | Working distillation pipeline + first numbers |
| **3. Cooking domain** | July–Aug 2026 (M3–M4) | YouCook2 / Breakfast: define regime, train teacher, distill student, run 3-condition experiment | First cross-domain confirmation of variability-scaling |
| **4. Instructional domain** | Sept 2026 (M5) | COIN / HowTo100M subset: same pipeline | Second cross-domain confirmation |
| **5. Synthetic + theory** | Oct 2026 (M6) | Build parameterized synthetic dataset with controllable regime variability. Develop $I(z; y)$ scaling argument. | Theoretical scaffolding + clean controlled-experiment evidence |
| **6. Polish + ablations** | Nov 2026 (M7) | SOTA comparisons, ablations (distillation vs. SSM), failure mode analysis, statistical tests, figures | Paper 2 draft v1 |
| **7. NeurIPS 2026 decision lands** | ~Sept 2026 | Incorporate Paper 1 reviewer feedback into Paper 2 framing | Cross-pollination |
| **8. (Optional) Paper 3 sprint** | Late Oct / early Nov 2026 (1-2 weeks) | If BetaMixer IAE labels accessible: deviation-score correlation. | Paper 3 draft, MICCAI 2027 short paper |
| **9. Writing + iteration** | Dec 2026 – Apr 2027 | Draft v2, v3. Internal review. Polish theory. | Paper 2 polished draft |
| **10. NeurIPS 2027 submission** | May 2027 | Submit Paper 2 to NeurIPS 2027 main track | Paper 2 submitted |
| **11. Backup window** | June–Oct 2027 | If NeurIPS rejects, polish for ICLR 2028 (deadline October 2027) with theory strengthened | ICLR 2028 submission ready |

Total: ~12 months of active work for Paper 2. Realistic, not aggressive.

---

## Reading list (prioritized)

### Tier 1 — read May 2026 first

The four papers that anchor the reframed plan:

1. **Lopez-Paz, Bottou, Schölkopf, Vapnik (ICLR 2016).** "Unifying distillation and privileged information." *Already in your refs (Ref 22). Reread as the **blueprint** for Paper 2's method, not as a one-line reference.* This is the paper your contribution extends.
2. **Hinton, Vinyals, Dean (NeurIPS 2014 workshop).** "Distilling the Knowledge in a Neural Network." arXiv:1503.02531. Foundation of distillation.
3. **Vapnik & Vashist (Neural Networks 2009).** "A new learning paradigm: Learning Using Privileged Information." Already in refs (Ref 21). The LUPI framework itself.
4. **Tishby & Zaslavsky (ITW 2015).** "Deep learning and the information bottleneck principle." arXiv:1503.02406. Gives you the mutual-information framing for "how much can conditioning on $z$ help predict $y$."

### Tier 2 — read June–July 2026

Cross-domain video + theoretical foundations:

5. **Sener et al. (ECCV 2020).** "Temporal Aggregate Representations for Long-Range Video Understanding." Cooking + instructional video; methodologically close.
6. **Damen et al. (IJCV 2022).** "EPIC-KITCHENS-100." Likely your cooking-domain dataset.
7. **Tang et al. (CVPR 2019).** "COIN: A Large-scale Dataset for Comprehensive Instructional Video Analysis."
8. **Bishop (1994 tech report).** "Mixture Density Networks." Foundation for conditioning regression on a discovered latent.

### Tier 3 — read August–October 2026

Architectural alternatives (for ablations) + scaling-law form:

9. **Gu & Dao (arXiv:2312.00752, 2023).** Mamba.
10. **Li et al. (ECCV 2024).** VideoMamba.
11. **Kaplan et al. (arXiv:2001.08361, 2020).** "Scaling Laws for Neural Language Models." Read for the *form of argument*, not the LM specifics.

### Tier 4 — supporting / optional

12. **Brown et al. (NeurIPS 2020).** GPT-3 paper. Read for the empirical-paper structure model.
13. **Yuan et al. (Med Image Anal 2025).** SurgVLP. Already in refs (Ref 18); useful if encoder swap is needed.
14. **Tong et al. (CVPR 2023).** VideoMAE V2. Stronger general video encoder.

---

## Resource plan

### Compute

| Phase | Estimated GPU-hours | Estimated cost (Lambda GH200 @ $2.29/hr) |
|---|---:|---:|
| Phase 2: distillation prototype on MB140 | ~50 hr | ~$115 |
| Phase 3: cooking domain | ~150 hr | ~$345 |
| Phase 4: instructional domain | ~150 hr | ~$345 |
| Phase 5: synthetic experiments | ~50 hr | ~$115 |
| Phase 6: ablations + SOTA | ~200 hr | ~$460 |
| **Total** | **~600 hr** | **~$1380** |

Add 30% buffer for restarts and exploratory experiments → **~$1800 budget for Paper 2 compute**.

### Data access

| Dataset | Status | Notes |
|---|---|---|
| MB140 | Have | Local mirror + Lambda NFS |
| Cholec80 | Have | Local mirror |
| YouCook2 | Public download | Free, ~80 GB |
| Breakfast | Public download | Free, ~50 GB |
| EPIC-KITCHENS-100 | Public download | Free, ~700 GB (only need a subset) |
| COIN | Public download | Free, ~50 GB |
| BetaMixer IAE labels (for Paper 3) | Apply to Bose et al. group | Required only if Paper 3 fires |

No new dataset purchases needed.

### Collaborators

| Role | Why | Where to find |
|---|---|---|
| **Surgical co-author** (clinical) | Adds clinical credibility; helps with op-note / IAE access if Paper 3 fires | Existing surgical-AI groups (CAMMA, Padoy lab, Bose group) |
| **Video understanding co-author** | Helps with non-surgical domain expertise | Berkeley AI Research, Stanford CV, FAIR, Google Research |
| **Theory co-author** | Strengthens the information-theoretic / LUPI framing | Math-leaning ML researchers |

A 2-co-author collaboration (one surgical, one video) would meaningfully accelerate Paper 2. Worth reaching out to existing contacts in May 2026.

---

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Distillation doesn't close the oracle-to-causal gap (student stays well below teacher) | Medium | Pivot the contribution to "we measure the gap and show its scaling" rather than "we close the gap." Honest framing. |
| Cross-domain experiments don't replicate variability-scaling (e.g., cooking shows different curve) | Medium | Reframe as "domain-dependent scaling shape" — still a contribution. Possibly the most interesting finding. |
| Synthetic dataset doesn't match real-world scaling (synthetic too clean) | Medium | Use synthetic to *probe theory*, real datasets to *validate*. Not load-bearing alone. |
| 12-month timeline slips by 3+ months | High | Plan around NeurIPS 2027 with ICLR 2028 backup. Don't burn down the runway with method-paper perfectionism. |
| BetaMixer IAE labels not accessible | High (uncertain) | Drop Paper 3. Plan doesn't depend on it. |
| Lambda Cloud pricing changes | Low | Negotiate with academic rate; switch to other cloud if needed. |

---

## Action items, by horizon

### This week (April 28 – May 4, 2026)
- [ ] Phase E lands; Run 035 lands; tier-2 experiments land
- [ ] Propagate landed numbers to Paper 1 manuscript
- [ ] HuggingFace upload (12 checkpoints + manifest + model card)
- [ ] Final Paper 1 polish
- [ ] Reread Lopez-Paz 2016 (Tier 1 reading #1)
- [ ] Sketch one-page outline of Paper 2 argument

### Lockup (May 1, 2026)
- [ ] Submit Paper 1
- [ ] Stop all Paper-1-specific work

### May 2026 (M1)
- [ ] Read Tier 1 reading list (4 papers, ~30 hrs)
- [ ] Build strict prefix-only training pipeline (Path B)
- [ ] First distillation prototype on MB140 (oracle teacher → causal student)
- [ ] Verify distilled student lands within 0.3 min of oracle teacher

### June 2026 (M2)
- [ ] If MB140 distillation works, start cooking-domain ramp
- [ ] Download YouCook2, set up framework
- [ ] First teacher training on YouCook2
- [ ] Read Tier 2 reading list

### Q3 2026 (M3–M5: July–September)
- [ ] Cooking experiments + cross-domain replication of variability-scaling
- [ ] COIN / instructional experiments
- [ ] Identify whether Paper 3 (deviation detection) is feasible based on label access
- [ ] If yes, sprint a 2-week Paper 3 effort

### Q4 2026 (M6–M7: October–November)
- [ ] Synthetic dataset experiments
- [ ] Theory scaffolding (information-theoretic framing)
- [ ] Paper 2 draft v1
- [ ] (If Paper 3 ready) MICCAI 2027 submission preparation

### Q1 2027 (M8–M10: December – February)
- [ ] Paper 2 ablations + SOTA comparisons
- [ ] Internal review + rewrites
- [ ] Paper 3 MICCAI 2027 submission (if applicable, deadline ~early March 2027)

### Q2 2027 (M11–M12: March – May)
- [ ] Final Paper 2 polish
- [ ] NeurIPS 2027 submission (deadline ~mid-May 2027)

---

## Open questions to revisit

1. **Co-authors**: who to bring in, and when? Decide by mid-May 2026.
2. **Synthetic dataset design**: what regime structure to parameterize? Discuss with theory co-author.
3. **MICCAI 2027 vs. CVPR 2027 for Paper 2 backup**: depends on theory development. Decide by November 2026.
4. **Whether to also pursue a journal version (Med Image Anal or similar)**: yes-by-default after Paper 2 lands. Plan in 2027.
5. **Whether Paper 3 is even worth doing**: depends on BetaMixer IAE label access; assess by August 2026.

---

## Key principles

1. **Sequential, not parallel.** Paper 1 must lock fully before Paper 2 starts. The few-day overlap is fine; weeks of overlap will compromise both.
2. **Distillation as central method, not SSM.** Cleaner narrative, more stable training, established theoretical scaffolding.
3. **Cross-domain validation is the move that lifts this to top-tier venues.** Surgical-only stays surgical-AI; cross-domain reaches NeurIPS / ICLR.
4. **Don't fall in love with architecture novelty.** The contribution is the *finding* (variability-scaling) and the *method* (distillation), not a fancy new building block.
5. **Theory does not need to be a theorem.** Point at an existing principle (LUPI, IB, MoE), show empirical claim follows. Reviewers respect this.
6. **Don't over-commit to Paper 3.** It's opportunistic. If it doesn't fall out of existing work in 2 weeks, drop it.

---

*Update log:*
- *2026-04-27: initial draft. Auto-mode-generated based on Paper-1 status, reading discussions, and venue analysis.*

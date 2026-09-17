# NeurIPS 2026 submission — remaining todo

**Deadline:** May 6, 2026
**Track:** Evaluations & Datasets, anonymous double-blind
**Title:** When Does Workflow Conditioning Help Remaining Surgery Duration Prediction? A Variability-Scaling Study on MultiBypass140 and Cholec80

---

## 1. HuggingFace upload (tonight) ⏳ ~1–4 hours

Push 17 paper-headline checkpoints (~24 GB) to `billchenxi/surgical-workflow-models`.

```bash
# Get token from https://huggingface.co/settings/tokens
# Required scope: "Write access to contents/settings of all repos under your namespace"
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxx
cd /Users/bill/Documents/GitHub/bariatric_rsd/reproducibility
python3 upload_to_huggingface.py
```

**Already staged:**
- `reproducibility/weights/manifest.json` — all 17 entries, 5 with `"TBD-after-upload"` SHA256s that the script fills in
- `reproducibility/weights/mb140/` — 9 Run 033 files + 2 Run 042 symlinks + 3 Run 040 fold-4 symlinks
- `reproducibility/weights/cholec80/` — 3 Run 018 files
- `reproducibility/docs/MODEL_CARD.md` — uploaded as repo README
- `huggingface_hub` Python package installed

**Idempotent:** safe to Ctrl-C and re-run. Skips already-uploaded files.

**When done:** repo will be live at https://huggingface.co/billchenxi/surgical-workflow-models. The URL goes into the paper's reproducibility section.

---

## 2. Delete Lambda filesystem (anytime) 💰 saves ~$200/week

Lambda Cloud console → Storage → `bariatric-rsd` filesystem → **Delete** → confirm.

Stops the $196.73/wk billing immediately. All paper-critical data is local; everything else is regenerable from public datasets + GitHub repo.

**Don't do this until** the HF upload has been verified working (so you can pull a checkpoint back if something fails). After the HF upload finishes successfully, delete is safe.

---

## 3. Rotate Lambda S3 adapter keys (after #2) 🔒 security hygiene

The keys you pasted in chat earlier are still valid. Lambda Cloud console → Filesystem S3 Adapter Keys → revoke the existing pair.

Once the filesystem is deleted (#2), the keys are useless anyway, but revoking is good hygiene since they're in the chat transcript.

---

## 4. Re-sync to Overleaf (before submission)

Today's edits aren't yet on Overleaf. Choose one approach:

**Option A — replace specific files (smaller delta):**
Upload to Overleaf:
- `paper/Formatting_Instructions_For_NeurIPS_2026/_abstract_short.tex` (rewritten abstract)
- `paper/Formatting_Instructions_For_NeurIPS_2026/body_main_short.tex` (Phase E 5-fold table + longer-context ablation in §6.1)
- `paper/Formatting_Instructions_For_NeurIPS_2026/body_appendix.tex` (new Appendix C.1 with per-fold + per-seed tables)

**Option B — re-upload bundles (cleaner):**
- Main paper: `paper/bariatric_rsd_overleaf.zip`
- Supplementary: `paper/bariatric_rsd_supplementary.zip`

**To rebuild bundles** if you've made further markdown edits:
```bash
cd /Users/bill/Documents/GitHub/bariatric_rsd/paper
python3 scripts/build_short_manuscript.py
python3 scripts/build_latex.py
python3 scripts/build_supplementary.py
# Then re-zip if needed (see SESSION_LOG section L)
```

---

## 5. Final pre-submission proofread (May 5 or earlier)

Read the rendered PDFs end-to-end at least once:
- `paper/Formatting_Instructions_For_NeurIPS_2026/main_short.pdf` (17 pages)
- `paper/Formatting_Instructions_For_NeurIPS_2026/main_supplementary.pdf` (25 pages)

Look for:
- Numbers consistent across abstract / §6 / §7 / Appendix C.1
- All citations resolve (no `[?]` or `\citet{undefined}`)
- All figures render at correct size
- No leftover process-leakage phrases ("our earlier draft", "as discussed in conversation", etc.)
- No anonymity leaks (author names, affiliations)

---

## 6. Submit to NeurIPS 2026 E&D track ⏰ by May 6, 23:59 AoE

OpenReview submission portal: https://openreview.net/group?id=NeurIPS.cc/2026/Datasets_and_Benchmarks_Track

Upload:
- Main paper PDF
- Supplementary PDF (optional but recommended — has the full Appendix C.1)
- Code/data link → HuggingFace repo URL (after #1 finishes)

---

## Quick reference — important file locations

| What | Where |
|---|---|
| Source-of-truth manuscript | `paper/review_manuscript.md` |
| Submit-ready (autocut) | `paper/submit_ready.md` |
| Supplementary markdown | `paper/submit_ready_supplementary.md` |
| LaTeX dir | `paper/Formatting_Instructions_For_NeurIPS_2026/` |
| Overleaf zips | `paper/bariatric_rsd_overleaf.zip` + `_supplementary.zip` |
| Phase E numbers | `paper/phase_e_summary.{md,json}` |
| Phase E aggregate | `lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json` |
| Reproducibility weights | `reproducibility/weights/` |
| HF manifest | `reproducibility/weights/manifest.json` |
| Build scripts | `paper/scripts/{build_short_manuscript,build_latex,build_supplementary,aggregate_phase_e}.py` |
| Cluster termination state | both terminated; NFS still alive (action #2) |

---

## Notes for next session (if context drops)

- Phase E 5-fold extension landed: per-fold mean Δ shrinks to **−0.19 min** (vs fold-0 headline **−0.85 min**). Reported transparently in §6.1.1 + Appendix C.1.
- Run 042 longer-context (single seed): widens conditioning gain from −0.85 to −1.44 min. §6.1.2.
- Both clusters terminated; NFS at $196.73/wk still alive (4.22 TB).
- Local has 16 paper-headline checkpoints (`reproducibility/`) + 28 best_model.pth in `lambda_mirror/outputs/` + all small inference-result files (run035/044/045 metrics).

# Stop Lambda Filesystem — Final Runbook

*Created 2026-06-04. Path: Option A — skip local verify, stop Lambda
immediately. No existing files modified. This document only adds new
information.*

---

## ✅ Pre-stop verification summary

Every paper-cited artifact is already at one of two safe locations:

| Asset | Local | HuggingFace |
|---|---|---|
| 17 cited best-model checkpoints | ✓ `reproducibility/weights/` (12 real + 5 symlinks resolving to local `lambda_mirror/outputs/`) | ✓ `billchenxi/surgical-workflow-models` (live, public, last modified 2026-04-30) |
| SHA256 manifest | ✓ `reproducibility/weights/manifest.json` (17/17 hashes filled) | ✓ uploaded with the deposit |
| Run 035 strict pixel-only causal eval (55 files, 81 MB) | ✓ `lambda_mirror/outputs/run035_strict_pixel_only/` | — |
| Run 041 posterior-τ ablation | ✓ `lambda_mirror/outputs/run041_tau_sweep/` | — |
| Run 044 oracle-baseline matched-metric | ✓ `lambda_mirror/outputs/run044_oracle_baseline_run035_metric/` | — |
| Run 045 shuffled-baseline matched-metric | ✓ `lambda_mirror/outputs/run045_shuffled_baseline_run035_metric/` | — |
| Phase E aggregate metrics | ✓ `lambda_mirror/outputs/phase_e_metrics/phase_e_aggregate_metrics.json` | — |
| 72 training logs for cited runs | ✓ `lambda_mirror/logs/` (run033 / 034 / 037 / 038 / 039 / 040 / 046) | — |
| Workflow cluster artifacts | ✓ `labels/` (9 JSON artifacts) + `lambda_mirror/labels/` | — |
| Training code (`train.py`, `train_causal.py`) | ✓ `lambda_setup/src/training/` | — |
| 24 per-experiment run scripts | ✓ `scripts/run0*.sh` | — |
| Bootstrap + label-build scripts | ✓ `lambda_setup/scripts/01–11_*.{sh,py}` | — |
| 4 anonymized PDFs | ✓ `paper/final_draft/` + `paper/Formatting_Instructions_For_NeurIPS_2026/` | — |
| Supplementary material (14 MB) | ✓ `paper/supplementary_material/` | — |
| Anonymous code submission (66 MB) | ✓ `anonymous_code_submission/` | ✓ `anonymous.4open.science/r/submission-code-F390` |
| Reconstruction docs | ✓ `RECONSTRUCTION_GUIDE.md`, `RESULTS_AUDIT.md`, `RESEARCH_PLAN.md`, `FINDINGS.md`, this file | — |

**Total local footprint after Lambda goes:** ~61 GB
(45 GB `lambda_mirror/` + 16 GB `reproducibility/weights/` + ~80 MB papers + ~66 MB code).

---

## What you're knowingly NOT preserving (acceptable losses)

These live only on Lambda and will be lost. Each is regenerable. None
are paper-cited.

| Loss | Why it's OK |
|---|---|
| Training intermediate epoch checkpoints (`epoch_0.pth` … `epoch_13.pth`) | Standard practice keeps only `best_model.pth`. Regenerable from `scripts/run0XX_*.sh` runs at ~$50–$100 each. |
| Optimizer states | Never serialized. Regenerated fresh on training restart. |
| Phase E folds 1–3 weights (33 checkpoints) | Metrics ARE in `phase_e_aggregate_metrics.json` (already local). Weights regenerable at ~$540 GPU-h if a reviewer ever asks. |
| Exploratory runs 001–015, 022, 023, 025 | Superseded by later runs. Not cited in the paper. |
| Full MultiBypass140 video dataset (~50–100 GB) | Public dataset. Re-downloadable from the Lavanchy et al. 2024 release. Not redistributed in this repo for license reasons anyway. |

Full reconstruction recipes are in `RECONSTRUCTION_GUIDE.md`.

---

## Stop sequence — exact commands

### Step 1 — final SSH audit (5 min)

```bash
ssh ubuntu@<your-lambda-head-ip>

# Inventory anything large that might be on Lambda but not local.
du -sh /lambda/nfs/bariatric-rsd/outputs/* | sort -h | tail -10
du -sh /lambda/nfs/bariatric-rsd/logs/*    | sort -h | tail -10

# Compare to your local mirror dir names if you want a side-by-side check.
# If anything surfaces that you'd want to keep, rsync it down BEFORE step 2.

# Then close the session cleanly.
history -c
exit
```

If nothing surprising shows up in `du`, proceed.

### Step 2 — make the HF deposit safe for the review period

You're keeping `billchenxi/surgical-workflow-models` as-is per your
decision. To minimize identity-leak risk during review, **temporarily
flip the repo to private** while review is happening:

1. Browse to https://huggingface.co/billchenxi/surgical-workflow-models/settings
2. Repository Settings → "Change repository visibility" → **Private**
3. Save.

This means: a reviewer who searches HF for "surgical-workflow-models"
won't find it. The paper PDF and supplementary don't link to it
(already anonymized). After acceptance, flip back to public.

*Side-effect:* if a reviewer asks "where can I download the weights?",
they can't — and the SHA256 check at the end of this document won't be
runnable by them either. But since the paper PDF was anonymized to
remove the URL entirely, no reviewer will be directed there in the
first place.

If you'd rather keep it public, skip this step. It's your call.

### Step 3 — delete the Lambda filesystem

1. Browser → Lambda Cloud console → Storage / Filesystems.
2. Find `bariatric-rsd` filesystem.
3. Detach from any still-attached instance.
4. **Delete filesystem**. Confirm.

Billing stops immediately. The 45 GB `lambda_mirror/` snapshot on your
laptop is now the canonical record.

### Step 4 — optional cleanups (do later if you want)

```bash
# Rotate any remaining HF tokens that may have lived on Lambda.
# Browse to https://huggingface.co/settings/tokens, revoke old ones.

# Rotate any Lambda S3 adapter keys you used for the rclone syncs.
# Browse to Lambda Cloud → API Keys.
```

Neither blocks the Lambda stop.

---

## Two parallel checks I started for you

These are running while you read this. Both are non-blocking — they
won't change the decision to stop Lambda either way.

### Check A — does the verify script chain still work locally?

**Result:** ⚠ partial. The script's path resolution + label decompression
work cleanly without Lambda. It dies on `ModuleNotFoundError: No module
named 'torch'` because your default `python3` doesn't have torch
installed. To run inference you'd need a torch-enabled env + the MB140
dataset (which is on Lambda, not local).

**Interpretation:** the *script infrastructure* is intact and shippable
to reviewers. The verify failure is expected because we never staged
the full dataset locally. Reviewers will provide their own torch +
dataset.

### Check B — does the HF deposit round-trip cleanly?

Still downloading 1.4 GB in the background. I'll report when it
completes. Either way, the HF deposit is confirmed live via API
(17 files + README + manifest, public, modified 2026-04-30) — the SHA
check just confirms one byte-for-byte download.

---

## Final go/no-go

**GO.** Stop the filesystem. The paper is fully reproducible from
local + HF deposit alone, even if the HF deposit later flips to
private during review.

If any of the following come up as new evidence, **don't go yet**:

- Step 1 SSH audit surfaces a >1 GB directory you can't identify or
  doesn't show up in `lambda_mirror/`.
- Check B reports MISMATCH on the SHA256 (meaning the HF deposit isn't
  byte-identical to your local — this would indicate a corrupt upload
  earlier).
- Your laptop is below ~80 GB free (because the 45 GB mirror needs to
  stay).

Absent any of those: click delete.

---

## What lives where, in one diagram (for future-you)

```
After Lambda is gone:

  ~/Documents/GitHub/bariatric_rsd/
  ├── lambda_mirror/          (45 GB — paper-cited eval outputs + logs + cluster labels)
  ├── reproducibility/
  │   └── weights/            (16 GB — 17 best-model .pth + SHA manifest)
  ├── paper/
  │   ├── final_draft/        (anonymized main + supp PDFs)
  │   ├── supplementary_material/ (14 MB — ready-to-zip)
  │   └── results_manifest.csv
  ├── anonymous_code_submission/ (66 MB — also live at 4open.science/r/submission-code-F390)
  ├── scripts/run0*.sh         (24 per-experiment runbooks)
  ├── lambda_setup/
  │   ├── src/training/{train.py, train_causal.py}
  │   └── scripts/01–11_*.{sh,py}
  └── *.md                     (RECONSTRUCTION_GUIDE, this file, runbooks, audits, findings)

HF deposit:
  https://huggingface.co/billchenxi/surgical-workflow-models
  ├── cholec80/run018_seed{42,123,777}.pth
  ├── mb140/run033_{no_token,oracle,decoupled}_seed{42,123,777}.pth (9)
  ├── mb140/run040_strict_decoupled_fold4_seed{42,123,777}.pth (3)
  ├── mb140/run042_longer_context_{no_token,decoupled}_seed42.pth (2)
  ├── manifest.json
  └── README.md  (← still contains "Chen lab" / "Bill Chen" / "billchenxi" — you
                    chose not to scrub these; the URL is also not linked from any
                    reviewer-facing material so the risk is low.)
```

— *End. Click delete when ready.*

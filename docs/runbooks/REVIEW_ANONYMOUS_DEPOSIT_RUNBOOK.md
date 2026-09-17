# Runbook: Anonymous Review Deposit + Lambda Filesystem Sunset

*Created 2026-06-04. Sequence: anonymize remaining files → upload weights
to fresh anonymous HF deposit → verify → audit Lambda → stop Lambda.*

---

## 0. State after this morning's prep work

The repo is now ready for an anonymous review deposit:

- **Paper PDFs** (Formatting_Instructions + final_draft `body_appendix.tex`)
  no longer reference `billchenxi/surgical-workflow-models`.
- **`reproducibility/upload_to_huggingface.py`** reads the HF handle from
  the `HF_REPO` env var instead of a hard-coded value.
- **`reproducibility/weights/manifest.json`** strips the
  `_huggingface_repo*` keys (anonymized).
- **`reproducibility/QUICKSTART.md`, `README.md`, `RUN_3.56.md`, and
  `docs/MODEL_CARD.md`** replaced all `billchenxi/...` URLs with
  `<ANONYMIZED-...-FOR-REVIEW>` placeholders.
- **`anonymous_code_submission/`** is already prepared (66 MB, 0 identity
  leaks) and contains `ANONYMOUS_HOSTING_FLOW.md`,
  `MODEL_HOSTING_FLOW.md`, and `OPENREVIEW_FORM_TEXT.md` with
  step-by-step instructions.

You'll now create three things, in this order:

1. A **fresh anonymous HuggingFace account** + model repo for the weights.
2. A **fresh anonymous GitHub repo** + `anonymous.4open.science` proxy URL
   for the code.
3. A short note in the supplementary submission with both URLs.

After that, audit and shut down the Lambda filesystem.

---

## 1. Create the new anonymous HuggingFace deposit (weights, ~16 GB)

### 1.1. Make the account

1. In a private browser window, go to https://huggingface.co/join.
2. Create a fresh account using a **non-identifying email** (e.g., an
   alias inbox you don't normally use; ProtonMail / SimpleLogin /
   Apple Hide-My-Email all work).
3. Pick a neutral handle. Suggested: `anon-rsd-neurips2026` or
   `workflow-rsd-anon`. Do **not** use any handle that maps to your
   public profiles.
4. Set the display name to something neutral (e.g., `Anonymous Author`).
5. **Do not** verify the account with any social-network linking.

### 1.2. Generate a write token

1. https://huggingface.co/settings/tokens → "New token".
2. Name: `bariatric-rsd-review-write`.
3. Token type: **fine-grained**.
4. Permissions: under "Repositories" → tick **"Write access to contents
   and settings of all repos under your personal namespace"**.
5. Copy the token. It looks like `hf_qxLb_REDACTED_ROTATE_AT_HF_SETTINGS`.
6. **Save it in your password manager.** Do not paste it into Slack,
   chat, or commit it anywhere.

### 1.3. Upload the 17 checkpoints

In a terminal in this repo:

```bash
cd /Users/bill/Documents/GitHub/bariatric_rsd/reproducibility

# Replace <YOUR_ANON_HANDLE> with the handle from step 1.1.
# Replace <hf_token_value> with the token from step 1.2.

export HF_TOKEN=<hf_token_value>
export HF_REPO=<YOUR_ANON_HANDLE>/workflow-rsd-models

python3 upload_to_huggingface.py
```

Expected output:

```
[upload] ensuring repo exists: <YOUR_ANON_HANDLE>/workflow-rsd-models
[upload] uploading .../cholec80/run018_seed42.pth ...
[upload]   done
... (17 files, each ~1.4 GB)
[upload] all done. Browse at https://huggingface.co/<YOUR_ANON_HANDLE>/workflow-rsd-models
```

Total upload time: ~45 min on a typical home connection, longer on slow
uplinks. The script is resumable in the sense that re-running uploads
the same file objects, but it's cleanest to run it through to
completion in one session.

### 1.4. Verify the upload (single-file SHA check)

```bash
# In a temp directory, fetch one checkpoint and hash-check it.
TMPDIR=$(mktemp -d)
cd "$TMPDIR"

python3 -c "
from huggingface_hub import hf_hub_download
import hashlib

path = hf_hub_download(
    repo_id='<YOUR_ANON_HANDLE>/workflow-rsd-models',
    filename='cholec80/run018_seed42.pth',
)
h = hashlib.sha256(open(path, 'rb').read()).hexdigest()
print(f'downloaded SHA256 = {h}')
print(f'expected SHA256   = 2054bc8cc7c1f1ff6ddd78e6451f2809eaf904d0d0799ae028c19424a6e6b3d5')
"

# Should match the expected SHA256 byte-for-byte.
```

### 1.5. Set the repo to **public** so reviewers can download

Browse to `https://huggingface.co/<YOUR_ANON_HANDLE>/workflow-rsd-models`
→ Settings → "Change repository visibility" → Public.

### 1.6. Record the URL

You'll need it in the OpenReview supplementary note. Save it somewhere
local for now; do not push it to git.

---

## 2. Create the new anonymous code repo (`anonymous.4open.science`)

### 2.1. Make a fresh GitHub account (or use an existing neutral one)

Same anonymization rules as §1.1.

### 2.2. Initialize the code zip as a git repo with neutral metadata

```bash
cd /Users/bill/Documents/GitHub/bariatric_rsd/anonymous_code_submission

# Strip any git metadata that may have leaked in.
rm -rf .git

# Initialize fresh with anonymous author config.
git init
git config user.name "Anonymous Author"
git config user.email "anonymous@example.com"

git add -A
git commit -m "Initial anonymized release for double-blind review"
```

### 2.3. Push to the fresh anonymous GitHub repo

```bash
# Replace with your anonymous account + chosen repo name.
git remote add origin git@github.com:<ANON_GH_HANDLE>/workflow-rsd-review.git
git branch -M main
git push -u origin main
```

### 2.4. Generate the anonymous.4open.science URL

1. Browse to https://anonymous.4open.science.
2. "Anonymize a repository" → paste the GitHub URL.
3. Accept the terms; the proxy generates a URL like
   `https://anonymous.4open.science/r/workflow-rsd-review-AB12/`.
4. Open it and verify it loads cleanly without your handle visible.
5. Save the URL alongside the HF URL from §1.6.

---

## 3. Update the OpenReview / supplementary submission

The submission already references "an anonymized HuggingFace repository";
add the two URLs to the **supplementary material** (not the paper PDF
itself, which stays unchanged):

In your OpenReview form's **"Code URL"** field:

```
https://anonymous.4open.science/r/workflow-rsd-review-AB12/
```

In your **"Supplementary Material zip"** (already prepared at
`paper/supplementary_material/`), edit `README.md` to add a small
"Anonymous deposits" section:

```markdown
## Anonymous deposits for review

- Code (proxy URL): https://anonymous.4open.science/r/workflow-rsd-review-AB12/
- Trained weights (~16 GB): https://huggingface.co/<YOUR_ANON_HANDLE>/workflow-rsd-models
- SHA256 manifest: see `manifests/weights_manifest.json` in this zip.

These URLs will be replaced by non-anonymous handles on acceptance.
```

Then re-zip the supplementary directory:

```bash
cd /Users/bill/Documents/GitHub/bariatric_rsd/paper
zip -r supplementary_material.zip supplementary_material/ \
  -x "supplementary_material/Supplementary Material.pdf"  # already in zip
```

If your conference flow lets you update the supplementary material
after submission, upload the new zip.

---

## 4. Audit the Lambda filesystem before deletion

SSH into the Lambda head node and inventory anything you might want to
keep that **isn't** already covered locally:

```bash
ssh ubuntu@<lambda-head-ip>
cd /lambda/nfs/bariatric-rsd
du -sh outputs/* | sort -h | tail -20
du -sh logs/*    | sort -h | tail -20
ls -1 outputs/ | wc -l
```

Cross-check against the local mirror. The current state I observed
this morning is:

| Asset | Local? | Notes |
|---|---|---|
| 17 cited checkpoints | ✅ in `reproducibility/weights/` | Now on HF after §1 |
| Run 035 strict pixel-only causal | ✅ `lambda_mirror/outputs/run035_strict_pixel_only/` | 81 MB |
| Run 041 τ sweep | ✅ | 24 KB |
| Run 044 oracle baseline matched-metric | ✅ | 148 KB |
| Run 045 shuffled baseline matched-metric | ✅ | 28 KB |
| Phase E aggregate metrics | ✅ | 12 KB |
| Run 033/034 strict training logs (22 files) | ✅ `lambda_mirror/logs/192.222.*/` | source of log-best MAE |
| Phase E training logs (39 files) | ✅ | covers Runs 038/039/040 |
| Run 037/046 logs (11 files) | ✅ | |
| Workflow cluster artifacts | ✅ `labels/` + `lambda_mirror/labels/` | 553 MB |
| Supplementary material | ✅ `paper/supplementary_material/` | 14 MB |
| **Phase E folds-1-3 weights** | ❌ Lambda only | metrics in JSON; weights regenerable |
| **Training intermediate epochs** | ❌ Lambda only | not cited; regenerable |
| **Optimizer states** | ❌ Lambda only | never needed for inference |

If nothing surfaces in `du` output that you'd want to keep, proceed
to §5. If something does, `rsync` it down first.

---

## 5. Stop the Lambda filesystem

### 5.1. Final SSH session — rotate any remaining credentials

```bash
# On the Lambda node, just before shutdown:
rm -f ~/.aws/credentials ~/.huggingface/token ~/.ssh/authorized_keys.lock
history -c
exit
```

### 5.2. From the Lambda console (browser)

1. Lambda Cloud → Filesystems → `bariatric-rsd`.
2. Detach from any instance still attached.
3. Confirm "Delete filesystem".

### 5.3. Optional — rotate the Lambda S3 adapter keys

This was already on your old todo list. From Lambda Cloud → API Keys,
revoke the keys you used during the `rclone` syncs.

---

## 6. Post-cutover sanity check

After Lambda is gone, verify the paper's reproducibility is intact from
local + HF only:

```bash
cd /Users/bill/Documents/GitHub/bariatric_rsd/reproducibility

# Re-run the strict MB140 verifier; it should pass without Lambda access.
bash scripts/verify_mb140_strict.sh
```

Expected: all per-condition checks pass within tolerance. If anything
fails, the SHA256s in `weights/manifest.json` should make the cause
obvious.

---

## 7. Time budget

| Step | Estimated time |
|---|---|
| §1 HF account + token + 17-file upload + SHA check | ~75 min (mostly upload bandwidth) |
| §2 GitHub anonymous account + proxy URL | ~20 min |
| §3 Supplementary update + re-zip | ~10 min |
| §4 Lambda audit | ~10 min |
| §5 Lambda stop | ~5 min |
| §6 Verification | ~15 min |
| **Total** | **~2h 15min** |

You can start §1 now, run it in the background, and do §2 in parallel
while the upload completes.

---

## 8. Identifier checklist before submission

Re-run this anonymity sweep right before resubmitting:

```bash
cd /Users/bill/Documents/GitHub/bariatric_rsd
grep -rEi "billchen|bill chen|@gmail.com|github.com/billchenxi|huggingface.co/billchen" \
  paper/ reproducibility/ anonymous_code_submission/ 2>/dev/null
echo "(no matches = clean)"
```

If grep prints nothing, the deposit and paper are ready for blind review.

— *End of runbook.*

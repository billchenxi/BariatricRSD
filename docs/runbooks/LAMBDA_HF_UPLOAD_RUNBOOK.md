# Lambda-Side HuggingFace Upload Runbook

*Created 2026-06-04. Upload your 17–25 trained checkpoints to a fresh
anonymous HuggingFace repo, **from a Lambda CPU node**, using Lambda's
fast upstream and the files that already live on the
`bariatric-rsd` NFS.*

This avoids the 16 GB local→HF transfer over home internet, and uses
Lambda bandwidth that's about to be deleted anyway.

---

## 0. Before you start

1. **Rotate the HF token you pasted in chat earlier.**
   `hf_qxLb_REDACTED_ROTATE_AT_HF_SETTINGS` should be revoked at
   https://huggingface.co/settings/tokens. Generate a fresh write token
   with the same scope: "Write access to contents and settings of all
   repos under your namespace."
2. **Pick an anonymous HF handle** if you haven't already. Suggested:
   `anon-rsd-2026` or `workflow-rsd-anon`. Create with a non-identifying
   email if needed.
3. **Pick a repo name.** Suggested: `workflow-rsd-models` or
   `surgical-workflow-models-anonsubmit`.

---

## 1. Stage the upload script on Lambda

The script `scripts/lambda_side_hf_upload.py` (in this repo) is the one
you'll run on Lambda. You need to get it onto the NFS so the Lambda
node can see it.

### Option A — push via this repo (cleanest)

If `/lambda/nfs/bariatric-rsd/` has a clone of this repo:

```bash
# On Lambda head node, in the project clone:
cd /lambda/nfs/bariatric-rsd
git pull   # picks up scripts/lambda_side_hf_upload.py
```

### Option B — scp from your laptop (one-shot)

```bash
# On your laptop:
scp /Users/bill/Documents/GitHub/bariatric_rsd/scripts/lambda_side_hf_upload.py \
    ubuntu@<lambda-ip>:/lambda/nfs/bariatric-rsd/scripts/
```

(If `scripts/` doesn't exist on Lambda, scp into `/lambda/nfs/bariatric-rsd/`
directly and adjust paths.)

---

## 2. Spin up a minimal Lambda node (CPU is enough)

The upload doesn't need a GPU. Spin up the **smallest available
instance** (typically `cpu-c2-medium` or equivalent) with the
`bariatric-rsd` filesystem attached. Cost: ~$0.10–$0.50/hour.

If you already have an instance running with the NFS mounted, just use
that.

---

## 3. SSH in and set up the upload environment

```bash
ssh ubuntu@<lambda-ip>

# Install only what we need — already there on most Lambda images.
pip install --quiet huggingface_hub

# Configure the upload target.
export HF_TOKEN=hf_<your_new_token>      # token you just generated
export HF_REPO=<your-anon-handle>/workflow-rsd-models

# Sanity check that the NFS is mounted.
ls /lambda/nfs/bariatric-rsd/outputs/ | head
```

---

## 4. Dry run — confirm the script sees the right files

```bash
cd /lambda/nfs/bariatric-rsd
python3 scripts/lambda_side_hf_upload.py --dry-run
```

Expected output (numbers will vary):

```
[lambda-upload] NFS root:    /lambda/nfs/bariatric-rsd
[lambda-upload] HF repo:     <your-anon-handle>/workflow-rsd-models
[lambda-upload] Manifest →   /lambda/nfs/bariatric-rsd/manifest_hf_upload.json
[lambda-upload] Dry run:     True

[lambda-upload] Found 22 of 25 checkpoints (33.4 GB total).
[lambda-upload] Missing on this NFS (3):
   - mb140_run034_cc_no_token_seed42: outputs/run034_strict_cc_no_token_seed42/best_model.pth
   - mb140_run034_cc_oracle_seed123: outputs/run034_strict_cc_oracle_seed123/best_model.pth
   - mb140_run042_longer_context_no_token_seed42: outputs/run042_longer_context_no_token_seed42/best_model.pth
   (These will be skipped. Re-train or symlink if needed.)

[lambda-upload] DRY RUN — no uploads performed.
```

**Read the "Missing" list carefully.** Anything listed as missing won't
end up on HF. If a missing checkpoint is needed for paper reproduction,
either:

- Find it elsewhere on the NFS (`find /lambda/nfs/bariatric-rsd -name "best_model.pth" | grep run034`)
- Symlink it into the expected path
- Or omit it (and update `reproducibility/weights/manifest.json`
  + the paper's appendix to match)

---

## 5. Real run

```bash
# Same env vars as before.
python3 scripts/lambda_side_hf_upload.py 2>&1 | tee /lambda/nfs/bariatric-rsd/hf_upload.log
```

Expected duration: **5–15 minutes** for ~30 GB at typical Lambda
upstream rates. The script streams one file at a time so it's safe to
Ctrl-C and re-run (it skips files already on HF).

The script also makes the repo public at the end so reviewers can
download without authentication.

---

## 6. Verify from anywhere (no token needed for public repos)

From your laptop, while still on Lambda, or from any machine:

```bash
python3 -c "
import urllib.request, json
repo = '<your-anon-handle>/workflow-rsd-models'
r = urllib.request.urlopen(f'https://huggingface.co/api/models/{repo}', timeout=15)
m = json.loads(r.read())
print('Files in repo:')
for f in m.get('siblings', []):
    print(' ', f['rfilename'])
"
```

You should see all the `.pth` files plus `manifest.json`.

To do a SHA-byte-level check on one file:

```bash
python3 -c "
from huggingface_hub import hf_hub_download
import hashlib
p = hf_hub_download(repo_id='<your-anon-handle>/workflow-rsd-models',
                    filename='cholec80/run018_seed42.pth')
print('sha256:', hashlib.sha256(open(p,'rb').read()).hexdigest())
"
# Compare against the value in the manifest.
```

---

## 7. Pull the manifest back to local

The Lambda-side script wrote
`/lambda/nfs/bariatric-rsd/manifest_hf_upload.json` with all 17–25
SHA256s. Get a copy locally so it survives the Lambda deletion:

```bash
# On your laptop:
scp ubuntu@<lambda-ip>:/lambda/nfs/bariatric-rsd/manifest_hf_upload.json \
    /Users/bill/Documents/GitHub/bariatric_rsd/reproducibility/weights/manifest.json.lambda
```

Then on your laptop, merge or replace `reproducibility/weights/manifest.json`
with the new entries as needed.

---

## 8. Cleanup on Lambda

Once verified:

```bash
# On Lambda:
unset HF_TOKEN
history -c   # clear shell history
exit
```

Then revoke the second token too, since it lived briefly on Lambda
shell. Generate a third for any future use (or just retire HF write
access entirely now that the deposit is done).

---

## 9. Then delete the Lambda filesystem

Now that the upload is verified and the manifest is back on your
laptop, you can detach the bariatric-rsd filesystem and delete it from
the Lambda Cloud console. See §5 of
`REVIEW_ANONYMOUS_DEPOSIT_RUNBOOK.md` for the exact UI steps.

---

## 10. Update review-facing docs with the URL

Once the deposit is public, paste the URL into:

- `paper/supplementary_material/README.md` (the "Anonymous deposits"
  section).
- The OpenReview submission form's notes (alongside the
  `anonymous.4open.science/r/submission-code-F390` URL).
- The anonymous code repo's `weights/manifest.json` — fill in
  `_huggingface_repo: <your-anon-handle>/workflow-rsd-models` so
  reviewers don't need to set an env var to use `download_weights.sh`.

---

## Time + cost summary

| Step | Time | Cost |
|---|---|---|
| Spin up CPU Lambda + SSH | ~3 min | ~$0.05 |
| Stage script + env setup | ~2 min | — |
| Dry run | ~30 sec | — |
| Upload 17–25 ckpts (~16–33 GB) | ~5–15 min | ~$0.10 |
| Verify | ~2 min | — |
| Pull manifest back to laptop | ~30 sec | — |
| **Total** | **~15 min** | **~$0.20** |

vs. uploading from home: 1–4 hours of laptop tied up, no GPU/CPU cost
but the laptop bandwidth is dedicated the whole time.

---

## Troubleshooting

- **"NFS root not found"** — the NFS isn't mounted on the instance you
  SSH'd into. Attach the `bariatric-rsd` filesystem from the Lambda UI
  and remount.
- **"HfHubHTTPError: 401 Unauthorized"** — token expired or wrong scope.
  Generate a new fine-grained token with "Write access to contents and
  settings of repos under your namespace."
- **"Found 0 of N checkpoints"** — the script expects paths like
  `outputs/run033_strict_no_token_seed42/best_model.pth`. If your NFS
  uses different names, edit the `CHECKPOINTS` list at the top of
  `lambda_side_hf_upload.py`.
- **Upload stalls** — Ctrl-C and re-run. The script skips files already
  on HF.
- **Repo set to private by default** — go to repo settings → change
  visibility → public.

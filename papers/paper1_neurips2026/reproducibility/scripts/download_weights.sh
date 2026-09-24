#!/usr/bin/env bash
# Download all model weights from HuggingFace into reproducibility/weights/.
# Reads weights/manifest.json for the file list and verifies SHA256s.
#
# Usage:
#   bash scripts/download_weights.sh [--only cholec80|mb140|all]
#
# Env vars:
#   HF_TOKEN        Optional. Required only if the HF repo is gated/private.
#                   For a public repo, leave unset.

set -euo pipefail

cd "$(dirname "$0")/.."  # cd to reproducibility/

WHICH="${1:-all}"
HF_REPO="$(python3 -c "import json; print(json.load(open('weights/manifest.json'))['_huggingface_repo'])")"

echo "[download] target HF repo: ${HF_REPO}"
echo "[download] subset: ${WHICH#--only=}"

python3 - <<PYEOF
import hashlib, json, sys
from pathlib import Path
from huggingface_hub import hf_hub_download

manifest = json.load(open("weights/manifest.json"))
which = "${WHICH}".lstrip("-").split("=")[-1] if "${WHICH}".startswith("--") else "all"
repo = manifest["_huggingface_repo"]

count_ok = 0
count_skipped = 0
count_failed = 0

for key, entry in manifest.items():
    if key.startswith("_"):
        continue
    if which == "cholec80" and not key.startswith("cholec80"):
        continue
    if which == "mb140" and not key.startswith("mb140"):
        continue

    hf_path = entry["hf_path"]
    expected_sha = entry.get("sha256", "TBD-after-upload")

    print(f"[download] {key} <- hf://{repo}/{hf_path}")
    try:
        local_path = hf_hub_download(
            repo_id=repo,
            filename=hf_path,
            local_dir="weights",
            local_dir_use_symlinks=False,
        )
    except Exception as exc:
        print(f"[download]   FAILED: {exc}")
        count_failed += 1
        continue

    if expected_sha == "TBD-after-upload":
        print(f"[download]   SHA256 not pinned in manifest yet — skipping verify")
        count_skipped += 1
        continue

    h = hashlib.sha256()
    with open(local_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    actual = h.hexdigest()

    if actual != expected_sha:
        print(f"[download]   SHA256 MISMATCH")
        print(f"[download]     expected: {expected_sha}")
        print(f"[download]     actual:   {actual}")
        count_failed += 1
    else:
        print(f"[download]   OK ({actual[:12]}...)")
        count_ok += 1

print(f"[download] done: {count_ok} verified, {count_skipped} unverified, {count_failed} failed")
sys.exit(0 if count_failed == 0 else 1)
PYEOF

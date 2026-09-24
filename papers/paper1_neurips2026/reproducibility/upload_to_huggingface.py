"""
One-time upload of reproducibility weights to HuggingFace.

Authors-only. Reviewers download via scripts/download_weights.sh.

This version is parameterized for anonymized double-blind review:
  - The HF repo handle is read from the HF_REPO env var (e.g.
    "anon-bariatric-rsd/surgical-workflow-models-2026").
  - It is no longer hard-coded in manifest.json.

Workflow:

  1. Pull weights from Lambda Cloud onto local disk (already done; see
     reproducibility/weights/ for the assembled set).

  2. Compute SHA256 for each file and update weights/manifest.json (the
     script does this if a SHA is missing or has changed).

  3. Run this script with HF_TOKEN + HF_REPO set:

       export HF_TOKEN=hf_xxx
       export HF_REPO=anon-bariatric-rsd/surgical-workflow-models-2026
       python3 upload_to_huggingface.py

     The fine-grained HF token must have "Write access to contents and
     settings of repos under your namespace" (or per-repo write scope if
     the repo already exists).

  4. Verify by downloading one file with scripts/download_weights.sh and
     checking its SHA256 against weights/manifest.json.

To create a fresh anonymous deposit (recommended for review submissions):
  - Create a new HuggingFace account with no identifying handle.
  - Generate a write token from huggingface.co/settings/tokens.
  - Pick a neutral repo name like "surgical-workflow-models-anonsubmit-<id>".
  - Set HF_REPO to "<your-anon-handle>/<repo-name>" and run this script.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi, create_repo

HERE = Path(__file__).parent
MANIFEST_PATH = HERE / "weights" / "manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    token = os.environ.get("HF_TOKEN")
    repo_id = os.environ.get("HF_REPO")

    if not token:
        print("ERROR: HF_TOKEN env var not set.", file=sys.stderr)
        print("Generate at https://huggingface.co/settings/tokens with "
              "'Write access to contents/settings of repos under your namespace'.",
              file=sys.stderr)
        sys.exit(1)

    if not repo_id:
        print("ERROR: HF_REPO env var not set.", file=sys.stderr)
        print("Set to '<anonymous-handle>/<repo-name>', e.g.:",
              file=sys.stderr)
        print("  export HF_REPO=anon-bariatric-rsd/surgical-workflow-models-2026",
              file=sys.stderr)
        sys.exit(1)

    manifest = json.load(open(MANIFEST_PATH))

    api = HfApi(token=token)

    print(f"[upload] ensuring repo exists: {repo_id}")
    create_repo(repo_id, repo_type="model", exist_ok=True, token=token)

    updated = False
    for key, entry in manifest.items():
        if key.startswith("_"):
            continue
        local_path = HERE / "weights" / entry["hf_path"]
        if not local_path.exists():
            print(f"[upload] SKIP {key}: {local_path} does not exist locally")
            continue

        actual_sha = sha256_file(local_path)
        if entry.get("sha256", "TBD-after-upload") != actual_sha:
            print(f"[upload] updating SHA256 for {key}: {actual_sha}")
            entry["sha256"] = actual_sha
            entry["size_mb"] = round(local_path.stat().st_size / (1024 * 1024), 2)
            updated = True

        print(f"[upload] uploading {local_path} -> hf://{repo_id}/{entry['hf_path']}")
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=entry["hf_path"],
            repo_id=repo_id,
            repo_type="model",
            token=token,
        )
        print(f"[upload]   done")

    # Persist any manifest changes before we upload it.
    if updated:
        json.dump(manifest, open(MANIFEST_PATH, "w"), indent=2)
        print(f"[upload] wrote updated manifest to {MANIFEST_PATH}")

    api.upload_file(
        path_or_fileobj=str(MANIFEST_PATH),
        path_in_repo="manifest.json",
        repo_id=repo_id,
        repo_type="model",
        token=token,
    )

    # README / model card.
    card_path = HERE / "docs" / "MODEL_CARD.md"
    if card_path.exists():
        api.upload_file(
            path_or_fileobj=str(card_path),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="model",
            token=token,
        )

    print(f"[upload] all done. Browse at https://huggingface.co/{repo_id}")
    print(f"[upload] Record this URL alongside the supplementary submission.")


if __name__ == "__main__":
    main()

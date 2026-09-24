"""
Lambda-side upload of paper-cited checkpoints to an anonymous HuggingFace
repository.

This script is designed to run **on a Lambda node** with the
bariatric-rsd NFS filesystem mounted at /lambda/nfs/bariatric-rsd. It
reads checkpoints directly from the original training output
directories, computes their SHA256s, uploads them to a configurable HF
repo, and writes the resulting manifest back to the NFS so it can be
synced to local later.

Why run this from Lambda instead of from your laptop:
  - Source files already live on /lambda/nfs (no laptop download needed).
  - Lambda upstream is ~5-10 Gbps vs ~50-500 Mbps at home.
  - Lambda's about to be deleted anyway. Last chance to use the bandwidth.

Usage (on a Lambda CPU node with the NFS attached):

    pip install huggingface_hub
    export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxx
    export HF_REPO=<your-anon-handle>/workflow-rsd-models
    python3 lambda_side_hf_upload.py

Optional flags:

    --dry-run         Print what would be uploaded, don't upload.
    --skip-existing   Skip files already present in the HF repo (default).
    --force           Re-upload even if HF already has the file.
    --manifest PATH   Write the SHA256 manifest here.
                      Default: /lambda/nfs/bariatric-rsd/manifest_hf_upload.json
    --extra-mb140     Also upload Phase E fold 1-3 weights (33 ckpts;
                      adds ~46 GB transfer). Default: skip.

Idempotent: re-running uploads the same files; HF de-duplicates content
hashes server-side.

Safety:
  - The HF_TOKEN is read from the env, never logged in cleartext.
  - The script does not delete or modify any local files.
  - All operations on the HF side are PUT (no destructive DELETE).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# Resolution table: (logical_name, local_path_under_NFS, hf_path_in_repo, notes)
# Mirrors papers/paper1_neurips2026/reproducibility/weights/manifest.json layout, but reads from the
# original training output dirs on NFS rather than the staging copies.
CHECKPOINTS = [
    # --- Cholec80 transfer-from-MB140 (Run 018, 3 seeds) ---
    ("cholec80_seed42",
     "outputs/run018_cholec80_transfer_from_mb140_seed42/best_model.pth",
     "cholec80/run018_seed42.pth",
     "Cholec80 transfer-from-MB140 seed=42 (3.69 min with isotonic only)"),
    ("cholec80_seed123",
     "outputs/run018_cholec80_transfer_from_mb140_seed123/best_model.pth",
     "cholec80/run018_seed123.pth",
     "Cholec80 transfer-from-MB140 seed=123"),
    ("cholec80_seed777",
     "outputs/run018_cholec80_transfer_from_mb140_seed777/best_model.pth",
     "cholec80/run018_seed777.pth",
     "Cholec80 transfer-from-MB140 seed=777"),

    # --- MB140 Run 033 within-center strict (3 conditions x 3 seeds) ---
    ("mb140_run033_no_token_seed42",
     "outputs/run033_strict_no_token_seed42/best_model.pth",
     "mb140/run033_no_token_seed42.pth", "Run 033 strict no-token seed 42"),
    ("mb140_run033_no_token_seed123",
     "outputs/run033_strict_no_token_seed123/best_model.pth",
     "mb140/run033_no_token_seed123.pth", "Run 033 strict no-token seed 123"),
    ("mb140_run033_no_token_seed777",
     "outputs/run033_strict_no_token_seed777/best_model.pth",
     "mb140/run033_no_token_seed777.pth", "Run 033 strict no-token seed 777"),
    ("mb140_run033_oracle_seed42",
     "outputs/run033_strict_oracle_seed42/best_model.pth",
     "mb140/run033_oracle_seed42.pth", "Run 033 strict oracle seed 42"),
    ("mb140_run033_oracle_seed123",
     "outputs/run033_strict_oracle_seed123/best_model.pth",
     "mb140/run033_oracle_seed123.pth", "Run 033 strict oracle seed 123"),
    ("mb140_run033_oracle_seed777",
     "outputs/run033_strict_oracle_seed777/best_model.pth",
     "mb140/run033_oracle_seed777.pth", "Run 033 strict oracle seed 777"),
    ("mb140_run033_decoupled_seed42",
     "outputs/run033_strict_decoupled_seed42/best_model.pth",
     "mb140/run033_decoupled_seed42.pth", "Run 033 strict decoupled-oracle seed 42"),
    ("mb140_run033_decoupled_seed123",
     "outputs/run033_strict_decoupled_seed123/best_model.pth",
     "mb140/run033_decoupled_seed123.pth", "Run 033 strict decoupled-oracle seed 123"),
    ("mb140_run033_decoupled_seed777",
     "outputs/run033_strict_decoupled_seed777/best_model.pth",
     "mb140/run033_decoupled_seed777.pth", "Run 033 strict decoupled-oracle seed 777"),

    # --- MB140 Run 034 cross-center strict (3 conditions x 3 seeds) ---
    ("mb140_run034_cc_no_token_seed42",
     "outputs/run034_strict_cc_no_token_seed42/best_model.pth",
     "mb140/run034_cc_no_token_seed42.pth", "Run 034 cross-center strict no-token seed 42"),
    ("mb140_run034_cc_no_token_seed123",
     "outputs/run034_strict_cc_no_token_seed123/best_model.pth",
     "mb140/run034_cc_no_token_seed123.pth", "Run 034 cross-center strict no-token seed 123"),
    ("mb140_run034_cc_no_token_seed777",
     "outputs/run034_strict_cc_no_token_seed777/best_model.pth",
     "mb140/run034_cc_no_token_seed777.pth", "Run 034 cross-center strict no-token seed 777"),
    ("mb140_run034_cc_oracle_seed42",
     "outputs/run034_strict_cc_oracle_seed42/best_model.pth",
     "mb140/run034_cc_oracle_seed42.pth", "Run 034 cross-center strict oracle seed 42"),
    ("mb140_run034_cc_oracle_seed123",
     "outputs/run034_strict_cc_oracle_seed123/best_model.pth",
     "mb140/run034_cc_oracle_seed123.pth", "Run 034 cross-center strict oracle seed 123"),
    ("mb140_run034_cc_oracle_seed777",
     "outputs/run034_strict_cc_oracle_seed777/best_model.pth",
     "mb140/run034_cc_oracle_seed777.pth", "Run 034 cross-center strict oracle seed 777"),
    ("mb140_run034_cc_decoupled_seed42",
     "outputs/run034_strict_cc_decoupled_seed42/best_model.pth",
     "mb140/run034_cc_decoupled_seed42.pth", "Run 034 cross-center strict decoupled-oracle seed 42"),
    ("mb140_run034_cc_decoupled_seed123",
     "outputs/run034_strict_cc_decoupled_seed123/best_model.pth",
     "mb140/run034_cc_decoupled_seed123.pth", "Run 034 cross-center strict decoupled-oracle seed 123"),
    ("mb140_run034_cc_decoupled_seed777",
     "outputs/run034_strict_cc_decoupled_seed777/best_model.pth",
     "mb140/run034_cc_decoupled_seed777.pth", "Run 034 cross-center strict decoupled-oracle seed 777"),

    # --- Appendix-only checkpoints (Run 040 fold 4 + Run 042 longer-context) ---
    ("mb140_run040_fold4_decoupled_seed42",
     "outputs/run040_strict_decoupled_fold4_seed42/best_model.pth",
     "mb140/run040_strict_decoupled_fold4_seed42.pth",
     "Phase E Appendix C.1 fold-4 decoupled-oracle seed 42"),
    ("mb140_run040_fold4_decoupled_seed123",
     "outputs/run040_strict_decoupled_fold4_seed123/best_model.pth",
     "mb140/run040_strict_decoupled_fold4_seed123.pth",
     "Phase E Appendix C.1 fold-4 decoupled-oracle seed 123"),
    ("mb140_run040_fold4_decoupled_seed777",
     "outputs/run040_strict_decoupled_fold4_seed777/best_model.pth",
     "mb140/run040_strict_decoupled_fold4_seed777.pth",
     "Phase E Appendix C.1 fold-4 decoupled-oracle seed 777"),
    ("mb140_run042_longer_context_no_token_seed42",
     "outputs/run042_longer_context_no_token_seed42/best_model.pth",
     "mb140/run042_longer_context_no_token_seed42.pth",
     "Longer-context (seq_len 16) ablation, no-token, seed 42"),
    ("mb140_run042_longer_context_decoupled_seed42",
     "outputs/run042_longer_context_decoupled_seed42/best_model.pth",
     "mb140/run042_longer_context_decoupled_seed42.pth",
     "Longer-context (seq_len 16) ablation, decoupled-oracle, seed 42"),
]


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(chunk), b""):
            h.update(c)
    return h.hexdigest()


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nfs-root", default="/lambda/nfs/bariatric-rsd",
                    help="Root of the bariatric-rsd NFS mount.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="Re-upload even if HF already has the file.")
    ap.add_argument("--manifest", default=None,
                    help="Path to write the SHA256 manifest. Default: "
                         "<nfs-root>/manifest_hf_upload.json")
    ap.add_argument("--extra-mb140", action="store_true",
                    help="Also try to upload Phase E folds 1-3 (rare).")
    args = ap.parse_args()

    nfs_root = Path(args.nfs_root)
    if not nfs_root.exists():
        sys.exit(f"NFS root {nfs_root} not found. Are you on a Lambda node "
                 "with the bariatric-rsd filesystem mounted?")

    token = os.environ.get("HF_TOKEN")
    repo_id = os.environ.get("HF_REPO")
    if not token:
        sys.exit("HF_TOKEN env var not set.")
    if not repo_id:
        sys.exit("HF_REPO env var not set (e.g. anon-rsd/workflow-rsd-models).")

    manifest_path = Path(args.manifest) if args.manifest else (
        nfs_root / "manifest_hf_upload.json"
    )

    print(f"[lambda-upload] NFS root:    {nfs_root}")
    print(f"[lambda-upload] HF repo:     {repo_id}")
    print(f"[lambda-upload] Manifest →   {manifest_path}")
    print(f"[lambda-upload] Dry run:     {args.dry_run}")
    print()

    # Resolve which checkpoints actually exist.
    resolved = []
    missing = []
    for logical, local_rel, hf_path, notes in CHECKPOINTS:
        local = nfs_root / local_rel
        if local.exists() and local.is_file():
            resolved.append((logical, local, hf_path, notes))
        else:
            missing.append((logical, local_rel))

    total_bytes = sum(p.stat().st_size for _, p, _, _ in resolved)
    print(f"[lambda-upload] Found {len(resolved)} of {len(CHECKPOINTS)} checkpoints "
          f"({human_size(total_bytes)} total).")
    if missing:
        print(f"[lambda-upload] Missing on this NFS ({len(missing)}):")
        for logical, rel in missing:
            print(f"   - {logical}: {rel}")
        print("   (These will be skipped. Re-train or symlink if needed.)")
    print()

    if args.dry_run:
        print("[lambda-upload] DRY RUN — no uploads performed.")
        return

    from huggingface_hub import HfApi, create_repo
    from huggingface_hub.utils import HfHubHTTPError

    api = HfApi(token=token)
    print(f"[lambda-upload] Ensuring repo exists: {repo_id}")
    create_repo(repo_id, repo_type="model", exist_ok=True, token=token, private=False)

    # Best-effort: list what's already on HF so we can skip-if-present.
    try:
        existing = set(api.list_repo_files(repo_id, repo_type="model", token=token))
    except HfHubHTTPError:
        existing = set()

    manifest = {
        "_comment": "Anonymized weight manifest. Set HF_REPO_ID in the "
                    "environment to download. Live HF URL provided via "
                    "supplementary submission.",
        "_uploaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "_huggingface_repo": repo_id,
        "_total_size_bytes": total_bytes,
    }

    for i, (logical, local, hf_path, notes) in enumerate(resolved, 1):
        size = local.stat().st_size
        if (hf_path in existing) and not args.force:
            print(f"[lambda-upload] [{i}/{len(resolved)}] SKIP (already on HF): {hf_path}")
            # Still SHA-check so the manifest is correct.
            sha = sha256_file(local)
            manifest[logical] = {
                "hf_path": hf_path, "sha256": sha,
                "size_mb": round(size / (1024 * 1024), 2),
                "notes": notes,
            }
            continue

        print(f"[lambda-upload] [{i}/{len(resolved)}] hashing {logical}...", flush=True)
        sha = sha256_file(local)
        print(f"[lambda-upload]   sha256 = {sha}")
        print(f"[lambda-upload]   uploading {human_size(size)} → hf://{repo_id}/{hf_path}",
              flush=True)
        api.upload_file(
            path_or_fileobj=str(local),
            path_in_repo=hf_path,
            repo_id=repo_id,
            repo_type="model",
            token=token,
        )
        print(f"[lambda-upload]   done.")
        manifest[logical] = {
            "hf_path": hf_path, "sha256": sha,
            "size_mb": round(size / (1024 * 1024), 2),
            "notes": notes,
        }

    # Write final manifest + upload it too.
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n[lambda-upload] Manifest written to {manifest_path}")

    print(f"[lambda-upload] Uploading manifest to HF as manifest.json")
    api.upload_file(
        path_or_fileobj=str(manifest_path),
        path_in_repo="manifest.json",
        repo_id=repo_id,
        repo_type="model",
        token=token,
    )

    # Make sure the repo is public so reviewers can download without auth.
    try:
        api.update_repo_visibility(repo_id=repo_id, private=False, token=token)
        print(f"[lambda-upload] Repo set to public.")
    except Exception as e:
        print(f"[lambda-upload] Could not set visibility (set it manually in the UI): {e}")

    print(f"\n[lambda-upload] All done.")
    print(f"[lambda-upload] Browse: https://huggingface.co/{repo_id}")
    print(f"[lambda-upload] Record this URL in your supplementary submission.")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# lambda_fs.sh — convenience wrapper for accessing the bariatric-rsd
# Lambda Cloud filesystem via rclone S3 adapter.
#
# Prerequisites:
#   - rclone installed (brew install rclone)
#   - rclone remote named "lambda" configured (run `rclone config` once;
#     see SUBMISSION_TODO.md or RESULTS_AUDIT.md for setup)
#
# The Lambda S3 adapter has a known MD5 incompatibility (April 2025+),
# so all transfer commands include --ignore-checksum.
#
# Usage:
#   ./scripts/lambda_fs.sh ls                      # top-level dirs
#   ./scripts/lambda_fs.sh ls outputs              # list outputs/
#   ./scripts/lambda_fs.sh ls 'outputs/run038*'    # glob a subdir
#   ./scripts/lambda_fs.sh tree outputs            # recursive listing
#   ./scripts/lambda_fs.sh size outputs/run038_strict_no_token_fold1_seed42
#   ./scripts/lambda_fs.sh pull outputs/run046_strict_cholec80_no_token_seed42
#                                                  # rclone copy → local mirror
#   ./scripts/lambda_fs.sh pull-glob 'outputs/run038_*/best_model.pth'
#                                                  # selective best_model.pth pull
#   ./scripts/lambda_fs.sh push labels/new_artifact.json
#                                                  # local → Lambda NFS
#   ./scripts/lambda_fs.sh status                  # connection check + bucket info

set -euo pipefail

# --- configurable bits ---
REMOTE="lambda"
BUCKET="30ee97d0-710d-4040-b643-5840b450992a"   # bariatric-rsd UUID
LOCAL_MIRROR="/Users/bill/Documents/GitHub/bariatric_rsd/lambda_mirror"
COMMON_FLAGS=(--ignore-checksum --transfers 4 --checkers 8 --progress)

# --- pretty output helpers ---
GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; RED=$'\033[0;31m'; NC=$'\033[0m'
log()  { printf "%s[lambda_fs]%s %s\n" "$GREEN" "$NC" "$*"; }
warn() { printf "%s[lambda_fs WARN]%s %s\n" "$YELLOW" "$NC" "$*" >&2; }
die()  { printf "%s[lambda_fs ERROR]%s %s\n" "$RED" "$NC" "$*" >&2; exit 1; }

require_rclone() {
  command -v rclone >/dev/null 2>&1 || die "rclone not installed (brew install rclone)"
  rclone listremotes 2>/dev/null | grep -q "^${REMOTE}:$" || \
    die "rclone remote '${REMOTE}' not configured. Run: rclone config"
}

remote_path() {
  # Convert a relative path into the full rclone S3 path
  local rel="${1:-}"
  if [[ -z "$rel" ]]; then
    echo "${REMOTE}:${BUCKET}"
  else
    echo "${REMOTE}:${BUCKET}/${rel}"
  fi
}

cmd_status() {
  require_rclone
  log "rclone version: $(rclone version | head -1)"
  log "remote: ${REMOTE}: → bucket ${BUCKET}"
  log "testing connection..."
  if rclone lsd "${REMOTE}:" --max-depth 1 >/dev/null 2>&1; then
    log "connection OK. available buckets:"
    rclone lsd "${REMOTE}:"
  else
    die "cannot reach ${REMOTE}:. Check credentials / network."
  fi
}

cmd_ls() {
  require_rclone
  local path="${1:-}"
  log "listing $(remote_path "$path")"
  rclone lsd "$(remote_path "$path")" 2>&1 || true
  echo
  rclone lsf "$(remote_path "$path")" --files-only --max-depth 1 2>&1 | head -30 || true
}

cmd_tree() {
  require_rclone
  local path="${1:-}"
  log "recursive listing of $(remote_path "$path") (max 100 entries)"
  rclone lsf "$(remote_path "$path")" --recursive 2>&1 | head -100
}

cmd_size() {
  require_rclone
  local path="${1:?path required}"
  log "size of $(remote_path "$path"):"
  rclone size "$(remote_path "$path")"
}

cmd_pull() {
  require_rclone
  local path="${1:?source path required}"
  local dest="${LOCAL_MIRROR}/${path}"
  mkdir -p "$(dirname "$dest")"
  log "pulling $(remote_path "$path") → $dest"
  rclone copy "$(remote_path "$path")" "$dest" "${COMMON_FLAGS[@]}"
  log "done. local size: $(du -sh "$dest" 2>/dev/null | cut -f1)"
}

cmd_pull_glob() {
  require_rclone
  local pattern="${1:?glob pattern required (e.g. 'outputs/run038_*/best_model.pth')}"
  log "pulling files matching '$pattern' → ${LOCAL_MIRROR}/"
  # rclone doesn't accept globs directly; use --include with --recursive
  # Strip the directory prefix so we can use it as the source root.
  local src_root
  src_root="$(dirname "$pattern")"
  if [[ "$src_root" == "." ]]; then src_root=""; fi
  rclone copy "$(remote_path "$src_root")" "${LOCAL_MIRROR}/${src_root}" \
    --include "*/$(basename "$pattern")" \
    "${COMMON_FLAGS[@]}"
}

cmd_push() {
  require_rclone
  local local_path="${1:?local path required}"
  local remote_subpath="${2:-$(basename "$local_path")}"
  [[ -e "$local_path" ]] || die "local path '$local_path' does not exist"
  log "pushing $local_path → $(remote_path "$remote_subpath")"
  if [[ -d "$local_path" ]]; then
    rclone copy "$local_path" "$(remote_path "$remote_subpath")" "${COMMON_FLAGS[@]}"
  else
    rclone copyto "$local_path" "$(remote_path "$remote_subpath")" "${COMMON_FLAGS[@]}"
  fi
}

cmd_help() {
  cat <<EOF
lambda_fs.sh — Lambda Cloud filesystem CLI wrapper

Subcommands:
  status                   Test connection + show bucket info
  ls [path]                List directories and files at <path>
  tree [path]              Recursive listing (capped at 100 entries)
  size <path>              Disk usage for <path>
  pull <remote-path>       Copy remote file/dir to lambda_mirror/
  pull-glob <pattern>      Copy files matching glob (e.g. 'outputs/run038_*/best_model.pth')
  push <local> [remote]    Copy local file/dir to remote
  help                     Show this help

Examples:
  $0 status
  $0 ls outputs
  $0 size outputs/run038_strict_no_token_fold1_seed42
  $0 pull outputs/run046_strict_cholec80_oracle_seed42
  $0 pull-glob 'outputs/run038_*/best_model.pth'
  $0 push paper/results_manifest.csv

Notes:
  - All transfers use --ignore-checksum (Lambda S3 adapter MD5 quirk)
  - LOCAL_MIRROR: ${LOCAL_MIRROR}
  - BUCKET (UUID): ${BUCKET}
  - To rotate the rclone remote, run: rclone config
EOF
}

# --- dispatch ---
sub="${1:-help}"
shift || true
case "$sub" in
  status)           cmd_status "$@" ;;
  ls)               cmd_ls "$@" ;;
  tree)             cmd_tree "$@" ;;
  size)             cmd_size "$@" ;;
  pull)             cmd_pull "$@" ;;
  pull-glob)        cmd_pull_glob "$@" ;;
  push)             cmd_push "$@" ;;
  help|-h|--help)   cmd_help ;;
  *) warn "unknown subcommand: $sub"; cmd_help; exit 1 ;;
esac

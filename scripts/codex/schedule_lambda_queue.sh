#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/ubuntu/bariatric-rsd}"
SEED="${2:-42}"
RUN_TAG="${3:-$(date -u +%Y%m%dT%H%M%SZ)}"
LOG_DIR="${ROOT}/codex_logs"

mkdir -p "$LOG_DIR"

QUEUE_LOG="${LOG_DIR}/queue_${RUN_TAG}.log"
CHOLEC_OUT="${ROOT}/outputs/codex_cholec80_causal_seed${SEED}_${RUN_TAG}"
MB140_OUT="${ROOT}/outputs/codex_mb140_causal_seed${SEED}_${RUN_TAG}"

exec >>"$QUEUE_LOG" 2>&1

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

wait_for_idle() {
  while pgrep -af "python3 -u codex_workflow/train.py" >/dev/null; do
    log "Waiting for existing codex_workflow training job to finish..."
    pgrep -af "python3 -u codex_workflow/train.py" || true
    sleep 300
  done
}

run_job() {
  local name="$1"
  shift
  local job_log="${LOG_DIR}/${name}_${RUN_TAG}.log"
  log "Starting ${name}"
  log "Command: $*"
  "$@" >"$job_log" 2>&1
  log "Finished ${name}; log=${job_log}"
}

log "Queue launched for seed=${SEED}, run_tag=${RUN_TAG}"
cd "$ROOT"

wait_for_idle

run_job "cholec80_seed${SEED}" \
  bash scripts/codex/run_cholec80_causal_workflow.sh "$ROOT" "$SEED" "$CHOLEC_OUT"

run_job "mb140_seed${SEED}" \
  bash scripts/codex/run_mb140_causal_workflow.sh "$ROOT" "$SEED" "$MB140_OUT"

log "Queue complete"

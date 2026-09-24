#!/usr/bin/env bash
set -euo pipefail

LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-ubuntu@192.222.50.14}"
REMOTE_ROOT="${REMOTE_ROOT:-/home/ubuntu/bariatric-rsd}"
SSH_KEY="${SSH_KEY:-${LOCAL_ROOT}/rsd.pem}"
SEED="${1:-42}"
RUN_TAG="${2:-$(date -u +%Y%m%dT%H%M%SZ)}"
MONITOR_INTERVAL_SECONDS="${MONITOR_INTERVAL_SECONDS:-1800}"
SSH_OPTS=(-i "$SSH_KEY" -o StrictHostKeyChecking=no)

rsync -az \
  -e "ssh ${SSH_OPTS[*]}" \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "${LOCAL_ROOT}/codex_workflow" \
  "${REMOTE_HOST}:${REMOTE_ROOT}/"

rsync -az \
  -e "ssh ${SSH_OPTS[*]}" \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "${LOCAL_ROOT}/scripts/codex/" \
  "${REMOTE_HOST}:${REMOTE_ROOT}/scripts/codex/"

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" \
  "mkdir -p '${REMOTE_ROOT}/codex_logs' && nohup bash '${REMOTE_ROOT}/scripts/codex/schedule_lambda_queue.sh' '${REMOTE_ROOT}' '${SEED}' '${RUN_TAG}' >/dev/null 2>&1 < /dev/null & echo ${RUN_TAG}"

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" \
  "nohup bash '${REMOTE_ROOT}/scripts/codex/monitor_lambda_progress.sh' '${REMOTE_ROOT}' '${RUN_TAG}' '${MONITOR_INTERVAL_SECONDS}' >/dev/null 2>&1 < /dev/null &"

echo "Scheduled Lambda queue"
echo "seed=${SEED}"
echo "run_tag=${RUN_TAG}"
echo "remote_log=${REMOTE_ROOT}/codex_logs/queue_${RUN_TAG}.log"
echo "remote_monitor_log=${REMOTE_ROOT}/codex_logs/monitor_${RUN_TAG}.log"
echo "remote_monitor_latest=${REMOTE_ROOT}/codex_logs/monitor_${RUN_TAG}_latest.txt"

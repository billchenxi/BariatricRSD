#!/usr/bin/env bash
set -euo pipefail

LOCAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST="${REMOTE_HOST:-ubuntu@192.222.50.14}"
REMOTE_ROOT="${REMOTE_ROOT:-/home/ubuntu/bariatric-rsd}"
SSH_KEY="${SSH_KEY:-${LOCAL_ROOT}/rsd.pem}"
RUN_TAG="${1:-20260424T034157Z}"
SSH_OPTS=(-i "$SSH_KEY" -o StrictHostKeyChecking=no)

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "
  echo '== Monitor =='
  cat '${REMOTE_ROOT}/codex_logs/monitor_${RUN_TAG}_latest.txt' 2>/dev/null || echo 'monitor status not available yet'
  echo
  echo '== Queue Tail =='
  tail -n 20 '${REMOTE_ROOT}/codex_logs/queue_${RUN_TAG}.log' 2>/dev/null || echo 'queue log not found'
  echo
  echo '== Active Processes =='
  pgrep -af 'schedule_lambda_queue.sh|monitor_lambda_progress.sh|python3 -u codex_workflow/train.py' || true
"

#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/ubuntu/bariatric-rsd}"
RUN_TAG="${2:?run tag required}"
INTERVAL_SECONDS="${3:-1800}"
LOG_DIR="${ROOT}/codex_logs"
QUEUE_LOG="${LOG_DIR}/queue_${RUN_TAG}.log"
MONITOR_LOG="${LOG_DIR}/monitor_${RUN_TAG}.log"
LATEST_STATUS="${LOG_DIR}/monitor_${RUN_TAG}_latest.txt"

mkdir -p "$LOG_DIR"

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$MONITOR_LOG"
}

emit_snapshot() {
  local active_line output_dir status_file
  active_line="$(pgrep -af "python3 -u codex_workflow/train.py" | head -n 1 || true)"

  {
    printf '[%s] ' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [[ -n "$active_line" ]]; then
      output_dir="$(printf '%s\n' "$active_line" | sed -n 's/.*--output-dir \([^ ]*\).*/\1/p' | head -n 1)"
      status_file="${output_dir}/status.json"
      if [[ -n "$output_dir" && -f "$status_file" ]]; then
        python3 - "$status_file" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path) as handle:
    status = json.load(handle)
metrics = status.get("latest_metrics") or {}
parts = [
    f"stage={status.get('stage')}",
    f"epoch={status.get('epoch')}/{status.get('epochs_total')}",
]
step = status.get("step")
step_total = status.get("epoch_steps_total")
if step is not None and step_total:
    parts.append(f"step={step}/{step_total}")
epoch_pct = status.get("epoch_progress_pct")
if epoch_pct is not None:
    parts.append(f"epoch_pct={epoch_pct:.1f}%")
train_pct = status.get("train_progress_pct")
if train_pct is not None:
    parts.append(f"train_pct={train_pct:.1f}%")
eta = status.get("eta_human")
if eta:
    parts.append(f"eta={eta}")
best = status.get("best_val_per_video_mae")
if best is not None:
    parts.append(f"best_val_mae={best:.3f}")
if "loss_total" in metrics:
    parts.append(f"loss={metrics['loss_total']:.4f}")
if "val_per_video_mae" in metrics:
    parts.append(f"val_mae={metrics['val_per_video_mae']:.3f}")
if "phase_accuracy" in metrics:
    parts.append(f"phase_acc={metrics['phase_accuracy']:.3f}")
print(" | ".join(parts))
PY
      else
        printf 'active_job_detected | output_dir=%s | status_file=missing\n' "${output_dir:-unknown}"
      fi
    else
      printf 'no_active_train_process\n'
    fi
  } | tee "$LATEST_STATUS" | tee -a "$MONITOR_LOG" >/dev/null
}

log "Progress monitor started for run_tag=${RUN_TAG}, interval=${INTERVAL_SECONDS}s"

while true; do
  emit_snapshot
  if [[ -f "$QUEUE_LOG" ]]; then
    tail -n 3 "$QUEUE_LOG" | sed 's/^/queue_tail: /' | tee -a "$MONITOR_LOG" >/dev/null
  fi

  if [[ -f "$QUEUE_LOG" ]] && grep -q "Queue complete" "$QUEUE_LOG" && ! pgrep -af "python3 -u codex_workflow/train.py" >/dev/null; then
    log "Progress monitor exiting after queue completion"
    break
  fi

  sleep "$INTERVAL_SECONDS"
done

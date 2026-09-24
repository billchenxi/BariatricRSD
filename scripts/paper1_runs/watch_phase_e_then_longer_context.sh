#!/bin/bash
# Watcher for Action 3 (and Action 4 chained): poll until this cluster's
# Phase E chain (Run 038/039/040) finishes, then launch Run 042
# (longer-context fold 0, 1 seed). After Run 042 finishes, evaluate the
# stop rule; if it lands a clear win, chain into Run 043 (3-seed expansion).
#
# Trigger 1: this cluster's `train_run038`, `train_run039`, or `train_run040`
#            screen no longer exists.
#
# Stop rule for Run 042 → Run 043:
#   - decoupled seed42 best val MAE < 12.10 (i.e., better than Run 033 fold 0)
#     AND no_token seed42 best val MAE not catastrophically worse
# This is a heuristic; the actual decision should ideally be reviewed by
# the user. The watcher prints the decision to its log so it can be checked.
#
# Run as a detached screen on the cluster you want the longer-context
# experiment to run on (typically the first to finish Phase E):
#   screen -dmS lc_watcher bash scripts/watch_phase_e_then_longer_context.sh
set -u
cd /lambda/nfs/bariatric-rsd

LOG=/tmp/lc_watcher.log
echo "[lc_watcher] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG

# Wait until any Phase E chain on this host has exited.
echo "[lc_watcher] waiting for local Phase E screen to exit..." | tee -a $LOG
while true; do
  if ! screen -ls 2>/dev/null | grep -qE 'train_run03[8-9]|train_run040'; then
    echo "[lc_watcher] phase E screen gone at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG
    break
  fi
  sleep 300
done

# Sanity: verify GPU is idle (no other train_run* screens) before launching.
sleep 30
if screen -ls 2>/dev/null | grep -qE 'train_run|run041|run042'; then
  echo "[lc_watcher] another job started; aborting to avoid contention" | tee -a $LOG
  exit 1
fi

echo "[lc_watcher] launching Run 042 longer-context fold 0 (1 seed)" | tee -a $LOG
bash scripts/run042_longer_context_fold0.sh

# Stop-rule evaluation.
echo "[lc_watcher] evaluating stop rule..." | tee -a $LOG
DECOUPLED_OUT=outputs/run042_longer_context_decoupled_seed42
NO_TOKEN_OUT=outputs/run042_longer_context_no_token_seed42

read_best_mae () {
  local DIR=$1
  python3 -c "
import json, os, sys
p = os.path.join('$DIR', 'metrics_history.json')
if not os.path.exists(p):
    print('NA'); sys.exit(0)
hist = json.load(open(p))
mins = [e.get('val_mae_min') for e in hist if e.get('val_mae_min') is not None]
if not mins:
    print('NA'); sys.exit(0)
print(min(mins))
"
}

DECOUPLED_MAE=$(read_best_mae "$DECOUPLED_OUT")
NO_TOKEN_MAE=$(read_best_mae "$NO_TOKEN_OUT")

echo "[lc_watcher] Run 042 results:" | tee -a $LOG
echo "  decoupled seed42 best val MAE: $DECOUPLED_MAE  (target: < 12.10 for win)" | tee -a $LOG
echo "  no_token  seed42 best val MAE: $NO_TOKEN_MAE   (target: ~ 13.03)" | tee -a $LOG

WIN=0
python3 -c "import sys; v='$DECOUPLED_MAE'; sys.exit(0 if v != 'NA' and float(v) < 12.10 else 1)" \
  && WIN=1 || true

if [ "$WIN" -eq 1 ]; then
  echo "[lc_watcher] STOP-RULE: WIN — decoupled seed42 < 12.10. Launching Run 043 (3-seed expansion)." | tee -a $LOG
  bash scripts/run043_longer_context_3seed.sh
else
  echo "[lc_watcher] STOP-RULE: NO WIN — decoupled seed42 not clearly better than 12.10. NOT expanding to 3 seeds." | tee -a $LOG
  echo "[lc_watcher] Marker file: outputs/run042_longer_context_NO_WIN" | tee -a $LOG
  touch outputs/run042_longer_context_NO_WIN
fi

echo "[lc_watcher] watcher complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG

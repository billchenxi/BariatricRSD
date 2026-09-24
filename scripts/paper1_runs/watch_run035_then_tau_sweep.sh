#!/bin/bash
# Watcher for Action 2: poll until Run 035 has ≥ 4 per-checkpoint JSONs,
# then launch Run 041 (tau sweep) on the same cluster (C).
#
# Trigger condition: ≥ 4 .json files (excluding summary.json) in
#   outputs/run035_strict_pixel_only/
#
# Run as a detached screen on Cluster C:
#   screen -dmS tau_sweep_watcher bash scripts/watch_run035_then_tau_sweep.sh
set -u
cd /lambda/nfs/bariatric-rsd

LOG=/tmp/tau_sweep_watcher.log
echo "[watcher] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG
echo "[watcher] waiting for Run 035 to have >=4 per-checkpoint JSONs..." | tee -a $LOG

while true; do
  N=$(find outputs/run035_strict_pixel_only -maxdepth 1 -name '*.json' \
        -not -name 'summary.json' 2>/dev/null | wc -l | tr -d ' ')
  if [ "$N" -ge 4 ]; then
    echo "[watcher] trigger met: $N JSONs at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG
    break
  fi
  sleep 300
done

echo "[watcher] launching Run 041 tau sweep" | tee -a $LOG
bash scripts/run041_tau_sweep.sh
echo "[watcher] tau sweep finished at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG

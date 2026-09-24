#!/bin/bash
# Run 045: re-evaluate Run 037 shuffled-token checkpoints under the
# matched metric used by Run 035 + Run 044 (per-video true-duration
# denorm, video-weighted mean), so the apples-to-apples table in the
# manuscript can include the semantic control row.
#
# Outputs:
#   outputs/run045_shuffled_baseline_run035_metric/run037_seed{42,123,777}.json
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run045_shuffled_baseline_run035_metric
mkdir -p $OUT_ROOT

echo "[run045] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run045.log

eval_one () {
  local SEED=$1
  local CKPT="outputs/run037_strict_shuffled_seed${SEED}/best_model.pth"
  local OUT="$OUT_ROOT/run037_seed${SEED}.json"
  if [ -f "$OUT" ]; then
    echo "[run045] SKIP seed=$SEED (json exists)" | tee -a /tmp/run045.log
    return
  fi
  if [ ! -f "$CKPT" ]; then
    echo "[run045] MISSING $CKPT" | tee -a /tmp/run045.log
    return
  fi
  echo "[run045] EVAL seed=$SEED at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run045.log
  python3 -m brsd_lib.evaluate \
    --checkpoint "$CKPT" \
    --label_json labels/mb140_fold0_labels_kmeans_shuffled.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --split val \
    --num_phases 14 \
    --target_position last \
    --batch_size 32 \
    --num_workers 8 \
    --out_json "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    >> $OUT_ROOT/run037_seed${SEED}.log 2>&1
  RC=$?
  echo "[run045] DONE seed=$SEED rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run045.log
}

for S in 42 123 777; do
  eval_one $S
done

echo "[run045] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run045.log

python3 - <<'PYEOF'
import json, glob, os, statistics
vals = []
for path in sorted(glob.glob("outputs/run045_shuffled_baseline_run035_metric/run037_seed*.json")):
    seed = int(os.path.basename(path).replace(".json", "").split("_seed")[-1])
    d = json.load(open(path))
    mean = d.get("mean") or d.get("mae_minutes_mean")
    vals.append({"seed": seed, "mae_min": mean})
ms = [v["mae_min"] for v in vals if v["mae_min"] is not None]
summary = {
    "rows": vals,
    "mean": float(sum(ms)/len(ms)) if ms else None,
    "std": float(statistics.pstdev(ms)) if len(ms) > 1 else 0.0,
}
with open("outputs/run045_shuffled_baseline_run035_metric/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

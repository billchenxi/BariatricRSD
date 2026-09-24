#!/bin/bash
# Run 044: re-evaluate Run 033 + Run 034 checkpoints with the Run 035 metric
# convention (per-video denorm, video-weighted mean) so the resulting numbers
# are directly comparable to Run 035's pixel-only causal numbers.
#
# Same checkpoints as Run 035, but with ORACLE cluster ID at inference (not
# pixel-only causal). The output of `brsd_lib.evaluate` already uses
# per-video denorm and video-weighted mean (it iterates per-video and
# aggregates), so re-running with the existing CLI gives us the comparator.
#
# Outputs:
#   outputs/run044_oracle_baseline_run035_metric/run0XX_<cond>_seed<S>.json
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run044_oracle_baseline_run035_metric
mkdir -p $OUT_ROOT

echo "[run044] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run044.log

eval_one () {
  local NAME=$1
  local CKPT=$2
  local LJ=$3
  local DR=$4
  local NP=$5
  local EXTRA="$6"
  local OUT=$OUT_ROOT/${NAME}.json
  if [ -f "$OUT" ]; then
    echo "[run044] SKIP $NAME (json exists)" | tee -a /tmp/run044.log
    return
  fi
  if [ ! -f "$CKPT" ]; then
    echo "[run044] MISSING $CKPT" | tee -a /tmp/run044.log
    return
  fi
  echo "[run044] EVAL $NAME at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run044.log
  python3 -m brsd_lib.evaluate \
    --checkpoint "$CKPT" \
    --label_json "$LJ" \
    --data_root "$DR" \
    --split val \
    --num_phases "$NP" \
    --target_position last \
    --batch_size 32 \
    --num_workers 8 \
    ${EXTRA} \
    --out_json "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    >> $OUT_ROOT/${NAME}.log 2>&1
  RC=$?
  echo "[run044] DONE $NAME rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run044.log
}

MB140_LJ=labels/mb140_fold0_labels_kmeans.json
MB140_DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140
CC_LJ=labels/mb140_cross_center_bern_train_stras_val_kmeans.json

for S in 42 123 777; do
  # within-center
  eval_one run033_oracle_seed${S}    outputs/run033_strict_oracle_seed${S}/best_model.pth    $MB140_LJ $MB140_DR 14 ""
  eval_one run033_decoupled_seed${S} outputs/run033_strict_decoupled_seed${S}/best_model.pth $MB140_LJ $MB140_DR 14 "--decouple_phase_head"
  eval_one run033_no_token_seed${S}  outputs/run033_strict_no_token_seed${S}/best_model.pth  $MB140_LJ $MB140_DR 14 "--no_phase_order"
  # cross-center
  eval_one run034_oracle_seed${S}    outputs/run034_strict_cc_oracle_seed${S}/best_model.pth    $CC_LJ    $MB140_DR 14 ""
  eval_one run034_decoupled_seed${S} outputs/run034_strict_cc_decoupled_seed${S}/best_model.pth $CC_LJ    $MB140_DR 14 "--decouple_phase_head"
  eval_one run034_no_token_seed${S}  outputs/run034_strict_cc_no_token_seed${S}/best_model.pth  $CC_LJ    $MB140_DR 14 "--no_phase_order"
done

echo "[run044] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run044.log

python3 - <<'PYEOF'
import json, glob, os, statistics
rows = {}
for path in sorted(glob.glob("outputs/run044_oracle_baseline_run035_metric/*.json")):
    name = os.path.basename(path).replace(".json", "")
    if name == "summary": continue
    src, seed = name.rsplit("_seed", 1)
    d = json.load(open(path))
    mae = d.get("mae_minutes_mean") or d.get("mae_min") or d.get("mae_minutes")
    rows.setdefault(src, []).append({"seed": int(seed), "mae_min": mae})
summary = {}
for src in rows:
    rows[src].sort(key=lambda r: r["seed"])
    vals = [r["mae_min"] for r in rows[src] if r["mae_min"] is not None]
    summary[src] = {
        "rows": rows[src],
        "mean": float(sum(vals)/len(vals)) if vals else None,
        "std": float(statistics.pstdev(vals)) if len(vals) > 1 else 0.0,
        "n_seeds": len(vals),
    }
with open("outputs/run044_oracle_baseline_run035_metric/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

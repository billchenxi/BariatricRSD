#!/bin/bash
# Run 035: strict pixel-only causal evaluation for the strict-protocol
# checkpoints produced by Run 033 / Run 034.
#
# This is the missing row in the earlier queue discussion. Run 033 / 034 train:
#   - strict no-token
#   - strict oracle
#   - strict decoupled-oracle
#
# None of those rows are themselves "pixel-only causal". This script evaluates
# the strict oracle and strict decoupled checkpoints under
# `brsd_lib.causal_cluster`, using:
#   - target_position=last     (strict prefix-only clips)
#   - decouple_phase_head      (for the decoupled checkpoints only)
#
# Outputs:
#   outputs/run035_strict_pixel_only/run033_{oracle,decoupled}_seed*.json
#   outputs/run035_strict_pixel_only/run034_{oracle,decoupled}_seed*.json
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run035_strict_pixel_only
mkdir -p $OUT_ROOT

echo "[run035] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run035.log

run_eval () {
  # $1 = source tag   (e.g. run033_oracle)
  # $2 = seed
  # $3 = checkpoint
  # $4 = labels json
  # $5 = artifacts json
  # $6 = data root
  # $7 = num phases
  # $8 = extra flags
  local SRC=$1; local S=$2; local CKPT=$3; local LJ=$4; local AJ=$5; local DR=$6; local NP=$7; local EXTRA="$8"
  local OUT=$OUT_ROOT/${SRC}_seed${S}.json
  if [ ! -f "$CKPT" ]; then
    echo "[run035] MISSING $CKPT — skipping $SRC seed=$S" | tee -a /tmp/run035.log
    return
  fi
  if [ -f "$OUT" ]; then
    echo "[run035] SKIP $SRC seed=$S (already done)" | tee -a /tmp/run035.log
    return
  fi
  echo "[run035] EVAL $SRC seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run035.log
  python3 -m brsd_lib.causal_cluster \
    --checkpoint "$CKPT" \
    --cluster_artifacts "$AJ" \
    --label_json "$LJ" \
    --data_root "$DR" \
    --split val \
    --num_phases "$NP" \
    --target_position last \
    --batch_size 1 \
    --output_json "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    ${EXTRA} \
    >> $OUT_ROOT/${SRC}_seed${S}.log 2>&1
  RC=$?
  echo "[run035] DONE $SRC seed=$S rc=$RC" | tee -a /tmp/run035.log
}

MB140_LJ=labels/mb140_fold0_labels_kmeans.json
MB140_AJ=labels/mb140_fold0_kmeans_artifacts.json
MB140_DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140
CC_LJ=labels/mb140_cross_center_bern_train_stras_val_kmeans.json
CC_AJ=labels/mb140_cross_center_kmeans_artifacts.json

for S in 42 123 777; do
  run_eval run033_oracle    $S outputs/run033_strict_oracle_seed${S}/best_model.pth    $MB140_LJ $MB140_AJ $MB140_DR 14 ""
  run_eval run033_decoupled $S outputs/run033_strict_decoupled_seed${S}/best_model.pth $MB140_LJ $MB140_AJ $MB140_DR 14 "--decouple_phase_head"
  run_eval run034_oracle    $S outputs/run034_strict_cc_oracle_seed${S}/best_model.pth $CC_LJ    $CC_AJ    $MB140_DR 14 ""
  run_eval run034_decoupled $S outputs/run034_strict_cc_decoupled_seed${S}/best_model.pth $CC_LJ $CC_AJ    $MB140_DR 14 "--decouple_phase_head"
done

echo "[run035] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run035.log

python3 - <<'PYEOF'
import glob, json, os, statistics

OUT_ROOT = "outputs/run035_strict_pixel_only"
groups = {}
for path in sorted(glob.glob(f"{OUT_ROOT}/*_seed*.json")):
    name = os.path.basename(path).replace(".json", "")
    src, seed = name.rsplit("_seed", 1)
    with open(path) as f:
        d = json.load(f)
    groups.setdefault(src, []).append({
        "seed": seed,
        "mae_norm_mean": d.get("mae_norm_mean"),
        "mae_minutes_mean": d.get("mae_minutes_mean"),
        "n_videos": d.get("n_videos"),
    })

summary = {}
for src, rows in groups.items():
    mm = [r["mae_minutes_mean"] for r in rows if r["mae_minutes_mean"] is not None and r["mae_minutes_mean"] == r["mae_minutes_mean"]]
    summary[src] = {
        "n_seeds": len(rows),
        "mae_minutes_mean_mean": float(sum(mm) / len(mm)) if mm else None,
        "mae_minutes_mean_std": float(statistics.pstdev(mm)) if len(mm) > 1 else 0.0,
        "rows": rows,
    }

with open(f"{OUT_ROOT}/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

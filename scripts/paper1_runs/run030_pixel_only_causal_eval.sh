#!/bin/bash
# Run 030: True pixel-only causal evaluation.
#
# Per Codex review (2026-04-25): Run 023's "causal" result is teacher-forced
# (uses ground-truth phase labels at inference via the precomputed
# prefix_cluster_map). The genuinely deployable causal evaluator is in
# brsd_lib.causal_cluster.evaluate_causal_rsd_pixel_only — uses the model's
# OWN phase-head predictions on prefix frames to compute the cluster
# posterior. This script evaluates that on every relevant existing
# checkpoint, producing JSON outputs for the manuscript's §6 table.
#
# Targets (each is a `python -m brsd_lib.causal_cluster` invocation; CPU/GPU
# light, ~5-10 min per checkpoint):
#   1. Run 010 fold-0 oracle checkpoints × 3 seeds (MB140 fold-0 val)
#   2. Run 023 fold-0 teacher-forced causal checkpoints × 3 seeds
#   3. Run 024 Cholec80 teacher-forced causal checkpoints × 3 seeds
#   4. Run 008 cross-center oracle checkpoint (Bern train, Stras val)
#   5. Run 028 cross-center teacher-forced causal × 3 seeds
#
# Output dir: outputs/run030_pixel_only_causal/<source_run>/seed<N>.json
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run030_pixel_only_causal
mkdir -p $OUT_ROOT

echo "[run030] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run030.log

run_eval () {
  # $1 = source run id (e.g. run010)
  # $2 = seed
  # $3 = checkpoint path
  # $4 = label_json
  # $5 = artifacts_json
  # $6 = data_root
  # $7 = num_phases
  local SRC=$1; local S=$2; local CKPT=$3; local LJ=$4; local AJ=$5; local DR=$6; local NP=$7
  local OUT=$OUT_ROOT/${SRC}_seed${S}.json
  if [ -f "$OUT" ]; then
    echo "[run030] SKIP $SRC seed=$S (already done)" | tee -a /tmp/run030.log
    return
  fi
  echo "[run030] EVAL $SRC seed=$S at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run030.log
  python3 -m brsd_lib.causal_cluster \
    --checkpoint "$CKPT" \
    --cluster_artifacts "$AJ" \
    --label_json "$LJ" \
    --data_root "$DR" \
    --split val \
    --num_phases "$NP" \
    --batch_size 32 \
    --output_json "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    >> $OUT_ROOT/${SRC}_seed${S}.log 2>&1
  RC=$?
  echo "[run030] DONE $SRC seed=$S rc=$RC" | tee -a /tmp/run030.log
}

# Common paths
MB140_LJ=labels/mb140_fold0_labels_kmeans.json
MB140_AJ=labels/mb140_fold0_kmeans_artifacts.json
MB140_DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140
CHOLEC_LJ=labels/cholec80_labels_kmeans.json
CHOLEC_AJ=labels/cholec80_kmeans_artifacts.json
CHOLEC_DR=/lambda/nfs/bariatric-rsd/extern/cholec80
CC_LJ=labels/mb140_cross_center_bern_train_stras_val_kmeans.json
CC_AJ=labels/mb140_cross_center_kmeans_artifacts.json

# 1. MB140 fold 0 oracle (Run 010) — does the oracle-trained model produce
#    a useful workflow signal when the cluster is recovered from prefix
#    pixels alone? If yes, oracle training + causal inference is deployable
#    without any retraining.
for S in 42 123 777; do
  run_eval run010 $S outputs/run010_mb140_fold0_seed${S}/best_model.pth \
    $MB140_LJ $MB140_AJ $MB140_DR 14
done

# 2. MB140 fold 0 teacher-forced prefix (Run 023) — the model that was
#    *trained* with prefix-clusters, evaluated under genuine pixel-only
#    inference. Compares directly to its teacher-forced 12.56 ± 0.04.
for S in 42 123 777; do
  run_eval run023 $S outputs/run023_mb140_fold0_causal_seed${S}/best_model.pth \
    $MB140_LJ $MB140_AJ $MB140_DR 14
done

# 3. Cholec80 teacher-forced prefix (Run 024).
for S in 42 123 777; do
  run_eval run024 $S outputs/run024_cholec80_causal_seed${S}/best_model.pth \
    $CHOLEC_LJ $CHOLEC_AJ $CHOLEC_DR 7
done

# 4. Cross-center teacher-forced prefix (Run 028).
for S in 42 123 777; do
  run_eval run028 $S outputs/run028_mb140_cross_center_causal_seed${S}/best_model.pth \
    $CC_LJ $CC_AJ $MB140_DR 14
done

echo "[run030] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run030.log

# Aggregate.
python3 - <<'PYEOF'
import json, glob, os, statistics
OUT_ROOT = "outputs/run030_pixel_only_causal"
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
    mn = [r["mae_norm_mean"] for r in rows if r["mae_norm_mean"] is not None]
    mm = [r["mae_minutes_mean"] for r in rows if r["mae_minutes_mean"] is not None and r["mae_minutes_mean"] == r["mae_minutes_mean"]]
    summary[src] = {
        "n_seeds": len(rows),
        "mae_norm_mean_mean": float(sum(mn)/len(mn)) if mn else None,
        "mae_norm_mean_std": float(statistics.pstdev(mn)) if len(mn) > 1 else 0.0,
        "mae_minutes_mean_mean": float(sum(mm)/len(mm)) if mm else None,
        "mae_minutes_mean_std": float(statistics.pstdev(mm)) if len(mm) > 1 else 0.0,
        "rows": rows,
    }

with open(f"{OUT_ROOT}/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

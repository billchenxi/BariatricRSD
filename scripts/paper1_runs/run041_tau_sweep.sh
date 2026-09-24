#!/bin/bash
# Run 041: temperature sweep on the strict pixel-only causal posterior.
#
# Sweeps τ ∈ {0.01, 0.05, 0.1, 0.5, 1.0} on a single best within-center
# checkpoint (run033_strict_decoupled_seed42). Each τ value re-runs the
# pixel-only causal evaluation, since τ enters the soft-cluster posterior
# inside the per-clip eval loop.
#
# Outputs:
#   outputs/run041_tau_sweep/run033_decoupled_seed42_tau{TAU}.json
#
# Wall time: ~20 min/eval × 5 = ~1.7 hr on a single GH200.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run041_tau_sweep
mkdir -p $OUT_ROOT

CKPT=outputs/run033_strict_decoupled_seed42/best_model.pth
LJ=labels/mb140_fold0_labels_kmeans.json
AJ=labels/mb140_fold0_kmeans_artifacts.json
DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140

if [ ! -f "$CKPT" ]; then
  echo "[run041] MISSING checkpoint $CKPT" >&2
  exit 1
fi

echo "[run041] tau sweep started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run041.log

for TAU in 0.01 0.05 0.1 0.5 1.0; do
  OUT=$OUT_ROOT/run033_decoupled_seed42_tau${TAU}.json
  if [ -f "$OUT" ]; then
    echo "[run041] SKIP tau=$TAU (json exists)" | tee -a /tmp/run041.log
    continue
  fi
  echo "[run041] EVAL tau=$TAU at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run041.log
  python3 -m brsd_lib.causal_cluster \
    --checkpoint "$CKPT" \
    --cluster_artifacts "$AJ" \
    --label_json "$LJ" \
    --data_root "$DR" \
    --split val \
    --num_phases 14 \
    --target_position last \
    --batch_size 1 \
    --temperature "$TAU" \
    --decouple_phase_head \
    --output_json "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    >> $OUT_ROOT/run033_decoupled_seed42_tau${TAU}.log 2>&1
  RC=$?
  echo "[run041] DONE tau=$TAU rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run041.log
done

echo "[run041] tau sweep complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run041.log

python3 - <<'PYEOF'
import json, glob, os
rows = []
for path in sorted(glob.glob("outputs/run041_tau_sweep/*.json")):
    name = os.path.basename(path).replace(".json", "")
    tau = float(name.split("_tau")[-1])
    d = json.load(open(path))
    rows.append({"tau": tau,
                 "mae_norm_mean": d.get("mae_norm_mean"),
                 "mae_minutes_mean": d.get("mae_minutes_mean"),
                 "n_videos": d.get("n_videos")})
rows.sort(key=lambda r: r["tau"])
summary = {"checkpoint": "run033_strict_decoupled_seed42", "rows": rows}
with open("outputs/run041_tau_sweep/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

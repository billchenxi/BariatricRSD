#!/bin/bash
# Run 034 (MR5 in EXPERIMENT_PLAN): strict prefix-only protocol on the
# Bern → Strasbourg cross-center setup. Three matched conditions × 3 seeds
# = 9 runs.
#
# Same recipe as Run 033 but uses the cross-center labels file. Results
# directly populate the cross-center row of the §6.2 table under the strict
# protocol.
#
# Stop-if-fails: if all three cross-center conditions are within 0.5 min of
# each other, workflow signal does not survive cross-center under the strict
# protocol — report as a clean negative E&D result. As in Run 033, the
# "decoupled" condition is still an oracle-cluster training/eval path; the
# strict pixel-only causal row comes from a separate evaluator.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run034] chain started at $STARTED" | tee -a /tmp/run034_chain.log

# Apply protocol patches if not already applied (idempotent).
python3 scripts/11_apply_protocol_patches.py 2>&1 | tee -a /tmp/run034_chain.log

CC_LJ=labels/mb140_cross_center_bern_train_stras_val_kmeans.json
DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140

run_one () {
  local NAME=$1 SEED=$2 EXTRA="$3"
  local OUTDIR="outputs/run034_strict_cc_${NAME}_seed${SEED}"
  local LOG="/tmp/run034_${NAME}_seed${SEED}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run034] SKIP $NAME seed=$SEED" | tee -a /tmp/run034_chain.log
    return
  fi
  echo "[run034] START $NAME seed=$SEED at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run034_chain.log
  python3 src/training/train.py \
    --label_json $CC_LJ \
    --data_root $DR \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${SEED} \
    --target_position last \
    ${EXTRA} \
    --wandb_run_name run034_strict_cc_${NAME}_seed${SEED} \
    >${LOG} 2>&1
  RC=$?
  echo "[run034] DONE $NAME seed=$SEED rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run034_chain.log
}

for S in 42 123 777; do
  run_one no_token       $S "--no_phase_order"
  run_one oracle         $S ""
  run_one decoupled      $S "--decouple_phase_head"
done

echo "[run034] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run034_chain.log

# Aggregate.
python3 - <<'PYEOF'
import json, glob, os, statistics, re
groups = {}
for d in sorted(glob.glob("outputs/run034_strict_cc_*_seed*")):
    m = re.match(r"outputs/run034_strict_cc_(.+)_seed(\d+)$", d)
    if not m: continue
    cond, seed = m.group(1), m.group(2)
    log = f"/tmp/run034_{cond}_seed{seed}.log"
    if not os.path.exists(log): continue
    best = None
    try:
        with open(log) as f:
            for line in f:
                if "best=" in line:
                    parts = line.split("best=")
                    if len(parts) >= 2:
                        token = parts[-1].split("min")[0].strip()
                        try: best = float(token)
                        except ValueError: pass
    except Exception:
        pass
    groups.setdefault(cond, []).append({"seed": seed, "best_val_mae_min": best})

summary = {}
for cond, rows in groups.items():
    vals = [r["best_val_mae_min"] for r in rows if r["best_val_mae_min"] is not None]
    summary[cond] = {
        "n_seeds": len(rows),
        "best_val_mae_min_mean": float(sum(vals)/len(vals)) if vals else None,
        "best_val_mae_min_std": float(statistics.pstdev(vals)) if len(vals) > 1 else 0.0,
        "rows": rows,
    }
with open("outputs/run034_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

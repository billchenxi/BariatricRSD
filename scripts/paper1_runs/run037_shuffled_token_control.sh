#!/bin/bash
# Run 037 (NH4 / Appendix Figure A1): shuffled-token control on MB140 fold 0,
# strict prefix-only protocol. 3 seeds.
#
# Cluster IDs are randomly permuted across videos (deterministic seed 0;
# marginal distribution preserved). Same recipe as Run 033 strict oracle,
# only the labels file differs.
#
# Interpretation:
#   * If shuffled-token val MAE ≈ strict no-token (12.88 ish): the workflow
#     token's gain is semantic — it carries real workflow information.
#     This is the desired outcome for the paper.
#   * If shuffled-token val MAE ≈ strict oracle: the gain is from added
#     model capacity, not from the cluster's meaning. This would weaken the
#     workflow story; report honestly.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run037] chain started at $STARTED" | tee -a /tmp/run037_chain.log

run_one () {
  local SEED=$1
  local OUTDIR="outputs/run037_strict_shuffled_seed${SEED}"
  local LOG="/tmp/run037_seed${SEED}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run037] SKIP seed=$SEED" | tee -a /tmp/run037_chain.log
    return
  fi
  echo "[run037] START seed=$SEED at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run037_chain.log
  python3 src/training/train.py \
    --label_json labels/mb140_fold0_labels_kmeans_shuffled.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${SEED} \
    --target_position last \
    --wandb_run_name run037_strict_shuffled_seed${SEED} \
    >${LOG} 2>&1
  RC=$?
  echo "[run037] DONE seed=$SEED rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run037_chain.log
}

for S in 42 123 777; do
  run_one $S
done

echo "[run037] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run037_chain.log

# Aggregate.
python3 - <<'PYEOF'
import json, glob, os, statistics, re
rows = []
for d in sorted(glob.glob("outputs/run037_strict_shuffled_seed*")):
    m = re.match(r"outputs/run037_strict_shuffled_seed(\d+)$", d)
    if not m: continue
    seed = m.group(1)
    log = f"/tmp/run037_seed{seed}.log"
    if not os.path.exists(log): continue
    best = None
    try:
        for line in open(log):
            if "best=" in line:
                t = line.split("best=")[-1].split("min")[0].strip()
                try: best = float(t)
                except: pass
    except: pass
    rows.append({"seed": seed, "best_val_mae_min": best})

vals = [r["best_val_mae_min"] for r in rows if r["best_val_mae_min"] is not None]
summary = {
    "n_seeds": len(rows),
    "best_val_mae_min_mean": float(sum(vals)/len(vals)) if vals else None,
    "best_val_mae_min_std": float(statistics.pstdev(vals)) if len(vals) > 1 else 0.0,
    "rows": rows,
    "config": "strict prefix-only protocol; cluster IDs shuffled deterministically across videos (seed 0); marginal preserved",
}
import json
with open("outputs/run037_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

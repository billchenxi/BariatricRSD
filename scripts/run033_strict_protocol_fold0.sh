#!/bin/bash
# Run 033 (Codex round 4 must-run): strict prefix-only protocol on MB140 fold 0.
#
# Three matched conditions × 3 seeds = 9 runs:
#   no-token       (control: how good is the model with no workflow signal?)
#   oracle         (upper bound: full-video cluster ID, but at the strict
#                   prefix-only target = last-frame label)
#   decoupled      (oracle + decoupled phase head: closes the
#                   phase/token circularity, but is still NOT the pixel-only
#                   causal row; that requires separate evaluation)
#
# Recipe matches Run 010 / Run 026 except for two flags:
#   --target_position last     (clip ends at prediction time; no future frames)
#   --decouple_phase_head      (only on the third condition)
#
# Stop-if-fails rule: if "no-token strict" alone is materially worse than the
# legacy 12.88 ± 0.09 (Run 026 fold 0), the centered-window leakage was a
# substantial component of our previous numbers, and we redo the 5-fold under
# the strict protocol. This run produces the strict no-token / strict oracle /
# strict decoupled-oracle rows only. The strict pixel-only causal row comes
# from a follow-up evaluator over these checkpoints.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[run033] chain started at $STARTED" | tee -a /tmp/run033_chain.log

# Apply protocol patches if not already applied. Safe re-run (skip-if-patched).
python3 scripts/11_apply_protocol_patches.py 2>&1 | tee -a /tmp/run033_chain.log

run_one () {
  local NAME=$1 SEED=$2 EXTRA="$3"
  local OUTDIR="outputs/run033_strict_${NAME}_seed${SEED}"
  local LOG="/tmp/run033_${NAME}_seed${SEED}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run033] SKIP $NAME seed=$SEED" | tee -a /tmp/run033_chain.log
    return
  fi
  echo "[run033] START $NAME seed=$SEED at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run033_chain.log
  python3 src/training/train.py \
    --label_json labels/mb140_fold0_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 14 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed ${SEED} \
    --target_position last \
    ${EXTRA} \
    --wandb_run_name run033_strict_${NAME}_seed${SEED} \
    >${LOG} 2>&1
  RC=$?
  echo "[run033] DONE $NAME seed=$SEED rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run033_chain.log
}

for S in 42 123 777; do
  run_one no_token       $S "--no_phase_order"
  run_one oracle         $S ""
  run_one decoupled      $S "--decouple_phase_head"
done

echo "[run033] chain complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run033_chain.log

# Aggregate.
python3 - <<'PYEOF'
import json, glob, os, statistics, re
OUT_ROOT = "outputs/run033_strict_*_seed*"
groups = {}
for d in sorted(glob.glob(OUT_ROOT)):
    m = re.match(r"outputs/run033_strict_(.+)_seed(\d+)$", d)
    if not m: continue
    cond, seed = m.group(1), m.group(2)
    log = f"/tmp/run033_{cond}_seed{seed}.log"
    if not os.path.exists(log): continue
    # Parse best val MAE from training log.
    best = None
    try:
        with open(log) as f:
            for line in f:
                if "best=" in line:
                    parts = line.split("best=")
                    if len(parts) >= 2:
                        token = parts[-1].split("min")[0].strip()
                        try:
                            best = float(token)
                        except ValueError:
                            pass
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
import json
with open("outputs/run033_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

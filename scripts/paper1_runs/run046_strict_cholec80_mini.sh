#!/bin/bash
# Run 046: strict Cholec80 mini-run — companion to §6.3 centered-window
# numbers, addresses "did Cholec80 survive the strict protocol?"
#
# 1 seed × 3 conditions = 3 training runs:
#   no_token (--no_phase_order)
#   oracle (default)
#   teacher_forced_prefix (--prefix_cluster_map)
#
# Same recipe as Run 016/017/024 except --target_position last for the
# strict prefix-only protocol.
#
# Wall time: Cholec80 videos are shorter than MB140 → ~30-40 min per
# training run. Total ~2 hr.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src

echo "[run046] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run046.log

run_one () {
  local NAME=$1; local EXTRA="$2"
  local OUTDIR="outputs/run046_strict_cholec80_${NAME}_seed42"
  local LOG="/tmp/run046_${NAME}.log"
  if [ -f "${OUTDIR}/best_model.pth" ]; then
    echo "[run046] SKIP $NAME (already done)" | tee -a /tmp/run046.log
    return
  fi
  echo "[run046] START $NAME at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run046.log
  python3 src/training/train.py \
    --label_json labels/cholec80_labels_kmeans.json \
    --data_root /lambda/nfs/bariatric-rsd/extern/cholec80 \
    --output_dir ${OUTDIR} \
    --epochs 15 --batch_size 64 --num_workers 16 --num_phases 7 \
    --sequence_len 8 --frame_stride 5 --lr 1e-4 --weight_decay 0.05 \
    --encoder_freeze_layers 6 --seed 42 \
    --target_position last \
    ${EXTRA} \
    --wandb_run_name run046_strict_cholec80_${NAME}_seed42 \
    >${LOG} 2>&1
  RC=$?
  echo "[run046] DONE $NAME rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run046.log
}

run_one no_token             "--no_phase_order"
run_one oracle               ""
run_one teacher_forced_prefix "--prefix_cluster_map labels/cholec80_prefix_clusters.json"

echo "[run046] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run046.log

python3 - <<'PYEOF'
import json, glob, os
rows = []
for d in sorted(glob.glob("outputs/run046_strict_cholec80_*_seed42")):
    name = os.path.basename(d).replace("run046_strict_cholec80_", "").replace("_seed42", "")
    ckpt = f"{d}/best_model.pth"
    if not os.path.exists(ckpt): continue
    import torch
    md = torch.load(ckpt, map_location="cpu", weights_only=False).get("metrics", {})
    rows.append({"condition": name, "best_val_mae_min": md.get("mae_minutes")})
print(json.dumps(rows, indent=2))
with open("outputs/run046_strict_cholec80_summary.json", "w") as f:
    json.dump({"rows": rows}, f, indent=2)
PYEOF

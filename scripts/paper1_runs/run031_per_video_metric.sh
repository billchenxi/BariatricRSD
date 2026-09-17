#!/bin/bash
# Run 031: re-evaluate every existing best_model.pth under the per-video
# MAE metric the manuscript actually claims. Codex finding #4: the trainer
# selects best checkpoints on `mae_minutes` which is clip-weighted, but
# the manuscript reports per-video MAE. This script aligns the two.
#
# For each best checkpoint we already have:
#   - run val-set inference via brsd_lib.evaluate (the per-video evaluator)
#   - dump per-video MAE (in minutes, using each video's true total_duration)
#   - aggregate across seeds → mean ± std per condition
#
# CPU/GPU light: ~5 min per checkpoint × ~25 checkpoints ≈ 2 hours.
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run031_per_video_metric
mkdir -p $OUT_ROOT
echo "[run031] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run031.log

eval_one () {
  local SRC=$1; local CKPT=$2; local LJ=$3; local DR=$4; local NP=$5
  local OUT=$OUT_ROOT/${SRC}.json
  if [ -f "$OUT" ]; then
    echo "[run031] SKIP $SRC (already done)" | tee -a /tmp/run031.log
    return
  fi
  if [ ! -f "$CKPT" ]; then
    echo "[run031] MISSING $CKPT — skipping $SRC" | tee -a /tmp/run031.log
    return
  fi
  echo "[run031] EVAL $SRC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run031.log
  python3 -m brsd_lib.evaluate \
    --checkpoint "$CKPT" \
    --label_json "$LJ" \
    --data_root "$DR" \
    --split val \
    --num_phases "$NP" \
    --out_json "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    >> $OUT_ROOT/${SRC}.log 2>&1
}

MB140_DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140
CHOLEC_DR=/lambda/nfs/bariatric-rsd/extern/cholec80

# MB140 fold 0: oracle (Run 010), teacher-forced prefix (Run 023), no-token (Run 026 fold 0)
for S in 42 123 777; do
  eval_one run010_seed${S} outputs/run010_mb140_fold0_seed${S}/best_model.pth \
    labels/mb140_fold0_labels_kmeans.json $MB140_DR 14
  eval_one run023_seed${S} outputs/run023_mb140_fold0_causal_seed${S}/best_model.pth \
    labels/mb140_fold0_labels_kmeans.json $MB140_DR 14
  eval_one run026_fold0_seed${S} outputs/run026_mb140_fold0_no_token_seed${S}/best_model.pth \
    labels/mb140_fold0_labels_kmeans.json $MB140_DR 14
done

# Cholec80: oracle (Run 016), no-token (Run 017), teacher-forced (Run 024)
for S in 42 123 777; do
  eval_one run016_seed${S} outputs/run016_cholec80_with_token_seed${S}/best_model.pth \
    labels/cholec80_labels_kmeans.json $CHOLEC_DR 7
  eval_one run017_seed${S} outputs/run017_cholec80_no_token_seed${S}/best_model.pth \
    labels/cholec80_labels_kmeans.json $CHOLEC_DR 7
  eval_one run024_seed${S} outputs/run024_cholec80_causal_seed${S}/best_model.pth \
    labels/cholec80_labels_kmeans.json $CHOLEC_DR 7
done

# Cross-center: oracle (Run 008), teacher-forced (Run 028)
for S in 42 123 777; do
  eval_one run028_seed${S} outputs/run028_mb140_cross_center_causal_seed${S}/best_model.pth \
    labels/mb140_cross_center_bern_train_stras_val_kmeans.json $MB140_DR 14
done

echo "[run031] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run031.log

# Aggregate across seeds.
python3 - <<'PYEOF'
import json, glob, os, statistics, re
OUT_ROOT = "outputs/run031_per_video_metric"
groups = {}
for path in sorted(glob.glob(f"{OUT_ROOT}/*.json")):
    name = os.path.basename(path).replace(".json", "")
    m = re.match(r"(run\d+(?:_fold\d+)?)_seed(\d+)", name)
    if not m:
        continue
    src, seed = m.group(1), m.group(2)
    with open(path) as f:
        d = json.load(f)
    pv = d.get("per_video", {})
    if pv:
        per_video_maes = [v["mae_minutes"] for v in pv.values() if "mae_minutes" in v]
        groups.setdefault(src, []).append({
            "seed": seed,
            "n_videos": len(per_video_maes),
            "mean_per_video_mae_min": float(sum(per_video_maes) / len(per_video_maes)) if per_video_maes else None,
        })

summary = {}
for src, rows in groups.items():
    means = [r["mean_per_video_mae_min"] for r in rows if r["mean_per_video_mae_min"] is not None]
    summary[src] = {
        "n_seeds": len(rows),
        "per_video_mae_min_mean": float(sum(means)/len(means)) if means else None,
        "per_video_mae_min_std": float(statistics.pstdev(means)) if len(means) > 1 else 0.0,
        "rows": rows,
    }
with open(f"{OUT_ROOT}/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

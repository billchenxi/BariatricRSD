#!/bin/bash
# Run 025: Adam-smoothing inference-time evaluation.
#
# Step 1 (GPU, ~5 min): dump per-clip val predictions from Run 010's three
#                       seed checkpoints on MB140 fold-0 val split.
# Step 2 (CPU, seconds): sweep AdamSmoother hyperparameters on each CSV,
#                       log top-10 configs + per-seed per-video MAE.
# Step 3 (CPU): combine seeds → 3-seed ensemble smoothed prediction, compute
#               per-video MAE, compare to raw / isotonic baselines.
#
# Results land in outputs/run025_adam_smooth_eval/{seed42,seed123,seed777}/
# and outputs/run025_adam_smooth_eval/summary.json
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run025_adam_smooth_eval
mkdir -p $OUT_ROOT

echo "[run025] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run025.log

for S in 42 123 777; do
  CKPT="outputs/run010_mb140_fold0_seed${S}/best_model.pth"
  if [ ! -f "$CKPT" ]; then
    echo "[run025] MISSING $CKPT — skipping seed $S" | tee -a /tmp/run025.log
    continue
  fi
  OUT_SEED=$OUT_ROOT/seed${S}
  mkdir -p $OUT_SEED
  RESID_CSV=$OUT_SEED/val_residuals.csv
  SWEEP_JSON=$OUT_SEED/adam_sweep.json
  BEST_CSV=$OUT_SEED/val_predictions_smoothed.csv

  if [ ! -f "$RESID_CSV" ]; then
    echo "[run025] dumping val residuals for seed $S" | tee -a /tmp/run025.log
    python3 -m brsd_lib.compute_residuals \
      --checkpoint "$CKPT" \
      --label_json labels/mb140_fold0_labels_kmeans.json \
      --data_root /lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140 \
      --split val \
      --output_csv "$RESID_CSV" \
      --project_src /lambda/nfs/bariatric-rsd/src \
      --num_phases 14 \
      >>$OUT_SEED/compute_residuals.log 2>&1
  fi

  echo "[run025] sweeping Adam smoother for seed $S" | tee -a /tmp/run025.log
  python3 -m brsd_lib.smoothing \
    --input_csv "$RESID_CSV" \
    --sweep \
    --output_json "$SWEEP_JSON" \
    >>$OUT_SEED/sweep.log 2>&1

  # Also apply the default (beta1=0.9 beta2=0.999 tau=0.02 monotone=True)
  # and save the smoothed predictions alongside the raw for later ensembling.
  python3 -m brsd_lib.smoothing \
    --input_csv "$RESID_CSV" \
    --output_csv "$BEST_CSV" \
    --beta1 0.9 --beta2 0.999 --tau 0.02 \
    >>$OUT_SEED/apply.log 2>&1
done

echo "[run025] all seeds done at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run025.log

# Ensemble step: average the smoothed predictions across seeds, per (video_id, frame_path),
# then compute per-video MAE. Baseline comparison: raw-only 3-seed ensemble.
python3 - <<'PYEOF'
import json, glob, os
import numpy as np
import pandas as pd
OUT_ROOT = "outputs/run025_adam_smooth_eval"
seeds = [42, 123, 777]
frames = {}
raw_frames = {}
total_min_col = None
for s in seeds:
    path = f"{OUT_ROOT}/seed{s}/val_predictions_smoothed.csv"
    if not os.path.exists(path):
        print(f"MISSING {path}")
        continue
    df = pd.read_csv(path)
    key = (df["video_id"].astype(str), df["frame_path"].astype(str))
    raw_frames[s] = df[["video_id","frame_path","target","prediction"]].copy()
    frames[s] = df[["video_id","frame_path","target","prediction_smoothed"]].copy()

if not frames:
    print("no seed CSVs found; skipping ensemble")
    raise SystemExit(0)

# Outer join on (video_id, frame_path), average smoothed + raw across seeds
merged_s = None
merged_r = None
for s in seeds:
    if s not in frames:
        continue
    fs = frames[s].rename(columns={"prediction_smoothed": f"pred_s_{s}"})
    fr = raw_frames[s].rename(columns={"prediction": f"pred_r_{s}"})
    merged_s = fs if merged_s is None else merged_s.merge(fs, on=["video_id","frame_path","target"], how="outer")
    merged_r = fr if merged_r is None else merged_r.merge(fr, on=["video_id","frame_path","target"], how="outer")
merged_s["ensemble_smoothed"] = merged_s[[c for c in merged_s.columns if c.startswith("pred_s_")]].mean(axis=1)
merged_r["ensemble_raw"] = merged_r[[c for c in merged_r.columns if c.startswith("pred_r_")]].mean(axis=1)

DEFAULT_TOTAL = 90.0  # MB140 median-ish
def per_vid(df, pred_col):
    per = {}
    for vid, grp in df.groupby("video_id", sort=False):
        err_min = np.abs(grp[pred_col] - grp["target"]) * DEFAULT_TOTAL
        per[str(vid)] = float(err_min.mean())
    return per

raw_per = per_vid(merged_r, "ensemble_raw")
s_per   = per_vid(merged_s, "ensemble_smoothed")
summary = {
    "ensemble_raw_mean": float(np.mean(list(raw_per.values()))),
    "ensemble_raw_median": float(np.median(list(raw_per.values()))),
    "ensemble_smoothed_mean": float(np.mean(list(s_per.values()))),
    "ensemble_smoothed_median": float(np.median(list(s_per.values()))),
    "note": "3-seed ensemble on MB140 fold-0 val, default smoother (beta1=0.9,beta2=0.999,tau=0.02,monotone=True). Uses fixed 90 min total duration for denorm — swap for per-video total later.",
}
with open(f"{OUT_ROOT}/summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(json.dumps(summary, indent=2))
PYEOF

echo "[run025] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run025.log

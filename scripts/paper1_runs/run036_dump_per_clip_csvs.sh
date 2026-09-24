#!/bin/bash
# Run 036: per-clip residual CSV dumps for the figures that need them.
#
# Run 030/035 emit per-video summary JSONs but not per-clip CSVs. Figures 9
# (error vs progress) and 11 (diagnostic chain) need per-clip prediction
# rows: video_id, frame_path, prediction, target. This script runs
# `brsd_lib.compute_residuals` on the strict-trained checkpoints and writes
# CSVs into the same output directories the build_fig9/build_fig11 scripts
# search.
#
# Cheap (~3 min per checkpoint × 9 checkpoints = ~30 min on a free GPU).
set -u
cd /lambda/nfs/bariatric-rsd
export PYTHONPATH=/lambda/nfs/bariatric-rsd/src:/lambda/nfs/bariatric-rsd

OUT_ROOT=outputs/run035_strict_pixel_only
mkdir -p $OUT_ROOT
echo "[run036] started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run036.log

dump_one () {
  local SRC=$1; local CKPT=$2; local LJ=$3; local DR=$4; local NP=$5; local EXTRA="$6"
  local OUT=$OUT_ROOT/${SRC}_clips.csv
  if [ -f "$OUT" ]; then
    echo "[run036] SKIP $SRC (csv exists)"; return
  fi
  if [ ! -f "$CKPT" ]; then
    echo "[run036] MISSING $CKPT"; return
  fi
  echo "[run036] DUMP $SRC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run036.log
  python3 -m brsd_lib.compute_residuals \
    --checkpoint "$CKPT" \
    --label_json "$LJ" \
    --data_root "$DR" \
    --split val \
    --num_phases "$NP" \
    --target_position last \
    --output_csv "$OUT" \
    --project_src /lambda/nfs/bariatric-rsd/src \
    ${EXTRA} \
    >> $OUT_ROOT/${SRC}_clips.log 2>&1
  RC=$?
  echo "[run036] DONE $SRC rc=$RC"
}

MB140_LJ=labels/mb140_fold0_labels_kmeans.json
MB140_DR=/lambda/nfs/bariatric-rsd/extern/MultiBypass140/datasets/MultiBypass140
CC_LJ=labels/mb140_cross_center_bern_train_stras_val_kmeans.json

for S in 42 123 777; do
  dump_one run033_no_token_seed${S}    outputs/run033_strict_no_token_seed${S}/best_model.pth   $MB140_LJ $MB140_DR 14 "--no_phase_order"
  dump_one run033_oracle_seed${S}      outputs/run033_strict_oracle_seed${S}/best_model.pth     $MB140_LJ $MB140_DR 14 ""
  dump_one run033_decoupled_seed${S}   outputs/run033_strict_decoupled_seed${S}/best_model.pth  $MB140_LJ $MB140_DR 14 "--decouple_phase_head"
  dump_one run034_no_token_seed${S}    outputs/run034_strict_cc_no_token_seed${S}/best_model.pth $CC_LJ   $MB140_DR 14 "--no_phase_order"
  dump_one run034_oracle_seed${S}      outputs/run034_strict_cc_oracle_seed${S}/best_model.pth   $CC_LJ   $MB140_DR 14 ""
done

echo "[run036] complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /tmp/run036.log

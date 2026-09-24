# brsd_lib

Fresh library for the BariatricRSD NeurIPS 2026 submission.

**Provenance:** every module here is written from scratch for this project.
No code is copied from the 2019 project, and nothing is imported from the
vendor-supplied `bariatric_rsd/` package at the repo root. Where algorithmic
concepts are inspired by prior work, the module docstring notes the source
explicitly and the implementation is independently expressed.

## Current modules

| Module | Purpose |
|--------|---------|
| [`labels.py`](labels.py) | RSD percentage conversion (seconds → [0, 1]) + labels.json audit |
| [`evaluate.py`](evaluate.py) | Test-set inference + per-video MAE aggregation |
| [`ensemble.py`](ensemble.py) | Multi-seed ensemble + horizontal-flip TTA + per-video isotonic post-processing |
| [`compute_residuals.py`](compute_residuals.py) | Dump per-clip (prediction, target, abs_residual) CSV for a trained checkpoint |
| [`overfit_filter.py`](overfit_filter.py) | Controlled per-video overfit residual selection + filtered manifest writing |
| [`causal_cluster.py`](causal_cluster.py) | **Causal (prefix-only) workflow-cluster assignment — replaces the retrospective full-video oracle cluster with a phase-head-derived soft posterior at inference** |

## Planned modules (not yet added)

- `phase_order.py` — data-driven phase-order clustering (k-means on bigram TF-IDF)
- `deviation.py` — learned + post-hoc deviation detection helpers
- `metrics.py` — paper-grade evaluation with bootstrap CIs and paired tests

## Usage

```python
from brsd_lib import (
    seconds_to_rsd_fraction,            # scalar helper
    frame_time_to_rsd_fraction,         # timestamp-based helper
    annotate_video_with_rsd_fractions,  # per-video (in place)
    normalize_labels_json,              # whole-file
    audit_labels,                       # sanity report
    standardize_residual_table,         # residual CSV normalization
    select_by_overfit_residuals,        # per-video frame selection
    write_filtered_manifest,            # train-only manifest filtering
)

# Single-frame
frac = seconds_to_rsd_fraction(remaining_seconds=600, total_seconds=3600)  # -> 0.166...

# Entire labels.json
videos = normalize_labels_json("labels/mb140_fold0_labels_kmeans.json")
report = audit_labels(videos)
print(report)
```

CLI:
```bash
python -m brsd_lib.labels labels/mb140_fold0_labels_kmeans.json --audit
python -m brsd_lib.overfit_filter outputs/overfit_residuals.csv \
  --selected-out outputs/overfit_selected.csv \
  --stats-out outputs/overfit_stats.csv \
  --labels-json lambda_mirror/labels/mb140_fold0_labels_kmeans.json \
  --manifest-out lambda_mirror/labels/mb140_fold0_labels_kmeans_overfit.json
```

## Where the old normalization logic lived in the codebase

Before this library, the same formula was inlined in four places (not deleted;
the legacy scripts still work, but new code should use `brsd_lib.labels`):

| File | Line | Context |
|------|-----:|---------|
| `lambda_setup/scripts/06_build_labels.py` | 95 | MB140 adapter |
| `lambda_setup/scripts/09_build_cholec80_labels.py` | 104 | Cholec80 adapter |
| `lambda_setup/src/data/prepare_labels.py` | 188 | generic bariatric parser |
| `lambda_setup/src/data/dataset.py` | 377 | `MultiBypass140Dataset.__getitem__` fallback |

These will be migrated to `brsd_lib.labels` in a follow-up commit.

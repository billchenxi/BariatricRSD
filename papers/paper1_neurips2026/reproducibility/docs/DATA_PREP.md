# Data preparation

Cholec80 and MultiBypass140 are the two datasets used in this paper.
Neither is shipped with this reproducibility package — both have
restrictive licenses, and the videos total ~360 GB. Reviewers download
from the official sources and run our frame-extraction script.

---

## Cholec80

### Get the data

Cholec80 is publicly available from the CAMMA group at IHU Strasbourg.
Apply for access at:
<http://camma.u-strasbg.fr/datasets>

You should receive a download link with `videos/` (80 `.mp4` files) and
`phase_annotations/` (40 `.txt` files for the canonical 40-video labeled
subset).

### Extract frames

We extract at **4 fps** (the rate used during training).

```bash
# Top-level layout expected:
#   $CHOLEC80_ROOT/videos/video01.mp4 ... video80.mp4
#   $CHOLEC80_ROOT/phase_annotations/video01-phase.txt ... video40-phase.txt
#   $CHOLEC80_ROOT/frames/video01/00000.jpg ...

CHOLEC80_ROOT=/path/to/cholec80
bash ../scripts/extract_cholec80_frames.sh "$CHOLEC80_ROOT"
```

The extraction takes ~2 hours on an SSD-backed workstation and produces
~50 GB of JPEG frames at quality 85.

### Our test split

The paper uses a **30-video public phase-labeled test split** (8 of the
40 phase-annotated videos lack reliable annotations and were dropped).
The exact video IDs are listed in
[../labels/cholec80_test_30video_labels.json](../labels/cholec80_test_30video_labels.json).

To regenerate the labels JSON from the official phase annotations:

```bash
python3 -m brsd_lib.labels \
    --dataset cholec80 \
    --data_root "$CHOLEC80_ROOT" \
    --split test \
    --output ../labels/cholec80_test_30video_labels.json
```

---

## MultiBypass140

### Get the data

MultiBypass140 is published by Lavanchy et al. (Med Image Anal 2024,
arXiv:2312.11250). Apply for access at:
<https://github.com/CAMMA-public/MultiBypass140>

The release contains 140 videos split across two centers (Bern, 70
videos; Strasbourg, 70 videos) with phase + step annotations and
official 5-fold cross-validation splits.

### Extract frames

Same 4 fps target rate as Cholec80:

```bash
MB140_ROOT=/path/to/MultiBypass140
bash ../scripts/extract_mb140_frames.sh "$MB140_ROOT"
```

Total ~280 GB of frames at quality 85.

### Folds and splits

The paper's headline results use:

- **fold 0** (the official MB140 fold 0 from the dataset release) for
  within-center §6.1 numbers
- **Bern → Strasbourg cross-center** for §6.2 numbers (training on all
  70 Bern videos, validating on all 70 Strasbourg videos)

Label JSONs:
- [../labels/mb140_fold0_labels_kmeans.json](../labels/mb140_fold0_labels_kmeans.json)
  — fold 0, oracle workflow-cluster IDs
- [../labels/mb140_cross_center_bern_to_strasbourg.json](../labels/mb140_cross_center_bern_to_strasbourg.json)
  — cross-center split
- [../labels/mb140_fold0_labels_kmeans_shuffled.json](../labels/mb140_fold0_labels_kmeans_shuffled.json)
  — shuffled-token control (for §6.4)

To regenerate cluster IDs from scratch:

```bash
python3 -m brsd_lib.labels \
    --dataset mb140 \
    --data_root "$MB140_ROOT" \
    --fold 0 \
    --num_clusters 6 \
    --output ../labels/mb140_fold0_labels_kmeans.json
```

The clustering is deterministic (`random_state=0`) so the cluster IDs
match those used in training.

---

## Storage estimate

| Item | Size |
|---|---:|
| Cholec80 videos | ~80 GB |
| Cholec80 frames @ 4 fps | ~50 GB |
| MultiBypass140 videos | ~200 GB |
| MultiBypass140 frames @ 4 fps | ~280 GB |
| Model checkpoints (12 files, this package) | ~1.2 GB |
| Labels JSONs | ~5 MB |
| **Total** for full reproduction | **~620 GB** |

For the Cholec80-only reproduction (3.56 result), you only need ~130 GB.

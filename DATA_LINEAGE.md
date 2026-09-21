# Data lineage

*Generated 2026-09-20 at commit `49f948e` by `python -m brsd_lib.data_lineage`. Do not edit by hand — regenerate it.*

This file records what every trained checkpoint and label artifact in this
repository was derived from. It exists because the licence position below
makes that question load-bearing, and because reconstructing it after the
fact is close to impossible.

**It is descriptive, not permissive.** It records provenance; it does not
establish that any particular use is lawful. Not legal advice.

## 1. Dataset licences — the governing constraint

| Dataset | Licence | Commercial use | ShareAlike | Verified |
|---|---|---|---|---|
| [Cholec80](http://camma.u-strasbg.fr/datasets/) *(in use)* | CC BY-NC-SA 4.0 | **no** | yes | 2026-09-17 |
| [CholecT50](https://github.com/CAMMA-public/cholect50) | CC BY-NC-SA 4.0 | **no** | yes | 2026-09-17 |
| [Endoscapes2023](https://physionet.org/content/endoscapes-2023/1.0.0/) | PhysioNet credentialed access + DUA | **no** | no | 2026-09-17 |
| [MultiBypass140](https://github.com/CAMMA-public/MultiBypass140) *(in use)* | CC BY-NC-SA 4.0 | **no** | yes | 2026-09-17 |

- **Cholec80** — 80 laparoscopic cholecystectomy videos; 72 carry the public phase labels used here. Requires a CAMMA data-use agreement.
- **CholecT50** — 50 videos, 45 of them drawn from Cholec80 — additional annotation, not an independent cohort. Not currently used by any artifact in this repository.
- **Endoscapes2023** — Terms must be read in full before any product use. Not currently used by any artifact in this repository.
- **MultiBypass140** — 140 RYGB videos, two centres (Bern BBP / Strasbourg SBP). Repository states: available for non-commercial scientific research purposes as defined in the CC BY-NC-SA 4.0.

Two distinct problems, and the second is the worse one:

1. **NonCommercial** forbids commercial use outright — no shipped model, no
   investor demo, no paid pilot.
2. **ShareAlike** requires adaptations to carry the same licence. Whether
   trained weights are an "adaptation" is legally unsettled, and that is
   precisely the difficulty: it does not have to be settled against us to
   cost us a diligence review.

## 2. The lineage rule

```
  RESEARCH LINEAGE                      PRODUCT LINEAGE
  MB140, Cholec80, CholecT50            data owned or licensed commercially
  -> papers, benchmarks, methods        -> shipped weights
  -> credibility, citations             -> revenue
  never ships                           never needs the academic data
      +---- crosses over: the METHOD, the Apache-2.0 CODE,
            the EVALUATION PROTOCOL, and reputation ----+
```

Of the 74 artifacts recorded below, **74 are research-lineage** (they touched a NonCommercial dataset), 0 are product-lineage, and 0 could not be classified.

> **No artifact in this repository is currently product-lineage.** A
> shippable model has to be trained on data owned or licensed
> commercially — in practice, a customer's own video under a commercial
> data-use agreement. Plan for the first paying pilot to be the first
> training set.

## 3. Integrity

- Hash mode: `manifest`
- Checkpoints re-hashed and matching their manifest entry: **17**
- Hash mismatches: **0**
- Declared in the manifest but absent from this checkout: **0**


> **5 of the reproducibility-deposit checkpoints are symlinks
> into `lambda_mirror/`, not independent copies.** `lambda_mirror/` is
> gitignored and holds 45 GB of archived run outputs; if it is pruned or
> the checkout is moved without it, these deposit entries break. Resolve
> them to real files before any external deposit or release:
>
> - `papers/paper1_neurips2026/reproducibility/weights/mb140/run040_strict_decoupled_fold4_seed123.pth`
>   → `lambda_mirror/outputs/run040_strict_decoupled_fold4_seed123/best_model.pth`
> - `papers/paper1_neurips2026/reproducibility/weights/mb140/run040_strict_decoupled_fold4_seed42.pth`
>   → `lambda_mirror/outputs/run040_strict_decoupled_fold4_seed42/best_model.pth`
> - `papers/paper1_neurips2026/reproducibility/weights/mb140/run040_strict_decoupled_fold4_seed777.pth`
>   → `lambda_mirror/outputs/run040_strict_decoupled_fold4_seed777/best_model.pth`
> - `papers/paper1_neurips2026/reproducibility/weights/mb140/run042_longer_context_decoupled_seed42.pth`
>   → `lambda_mirror/outputs/run042_longer_context_decoupled_seed42/best_model.pth`
> - `papers/paper1_neurips2026/reproducibility/weights/mb140/run042_longer_context_no_token_seed42.pth`
>   → `lambda_mirror/outputs/run042_longer_context_no_token_seed42/best_model.pth`

Re-check at any time with `python -m brsd_lib.data_lineage --verify`, which
exits non-zero on drift.

## 4. Checkpoints

| Checkpoint | Dataset | Lineage | SHA256 | Size | Reported MAE |
|---|---|---|---|---|---|
| `lambda_mirror/outputs/codex_cholec80_pilot_seed42/best_model.pth` | Cholec80 | research | — | 131.1 MB | — |
| `lambda_mirror/outputs/run001_mb140_fold0_multitask_archived/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run002_mb140_fold0_multitask_regularized_archived/best_model.pth` | MultiBypass140 | research | — | 1.2 GB | — |
| `lambda_mirror/outputs/run003_mb140_fold0_lr5e5_wd01_archived/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run004_mb140_fold0_rsd_only_archived/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run005_mb140_fold0_no_phase_order_archived/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run006_mb140_fold0_kmeans_phase_order_archived/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run007_mb140_fold0_no_phase_order_15ep/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run008_mb140_cross_center_bern_train_stras_val_kmeans/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run009_mb140_cross_center_bern_train_stras_val_no_token/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run010_mb140_fold0_seed123/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run010_mb140_fold0_seed42/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run010_mb140_fold0_seed777/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run014_cholec80_rsd_kmeans/best_model.pth` | Cholec80 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run015_cholec80_no_phase_order/best_model.pth` | Cholec80 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run016_cholec80_with_token_seed123/best_model.pth` | Cholec80 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run016_cholec80_with_token_seed777/best_model.pth` | Cholec80 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run017_cholec80_no_token_seed123/best_model.pth` | Cholec80 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run017_cholec80_no_token_seed777/best_model.pth` | Cholec80 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run018_cholec80_transfer_from_mb140_seed123/best_model.pth` | Cholec80 + MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run018_cholec80_transfer_from_mb140_seed42/best_model.pth` | Cholec80 + MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run018_cholec80_transfer_from_mb140_seed777/best_model.pth` | Cholec80 + MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run028_mb140_cross_center_causal_seed123/best_model.pth` | MultiBypass140 | research | — | 1.4 GB | — |
| `lambda_mirror/outputs/run040_strict_decoupled_fold4_seed123/best_model.pth`<br><small>↳ also at `papers/paper1_neurips2026/reproducibility/weights/mb140/run040_strict_decoupled_fold4_seed123.pth`</small> | MultiBypass140 | research | `10cd25d2d00a` | 1.4 GB | 8.74 |
| `lambda_mirror/outputs/run040_strict_decoupled_fold4_seed42/best_model.pth`<br><small>↳ also at `papers/paper1_neurips2026/reproducibility/weights/mb140/run040_strict_decoupled_fold4_seed42.pth`</small> | MultiBypass140 | research | `68a504a639a1` | 1.4 GB | 8.48 |
| `lambda_mirror/outputs/run040_strict_decoupled_fold4_seed777/best_model.pth`<br><small>↳ also at `papers/paper1_neurips2026/reproducibility/weights/mb140/run040_strict_decoupled_fold4_seed777.pth`</small> | MultiBypass140 | research | `da5db3d5673f` | 1.4 GB | 8.82 |
| `lambda_mirror/outputs/run042_longer_context_decoupled_seed42/best_model.pth`<br><small>↳ also at `papers/paper1_neurips2026/reproducibility/weights/mb140/run042_longer_context_decoupled_seed42.pth`</small> | MultiBypass140 | research | `3dbca3be2b39` | 1.4 GB | 11.02 |
| `lambda_mirror/outputs/run042_longer_context_no_token_seed42/best_model.pth`<br><small>↳ also at `papers/paper1_neurips2026/reproducibility/weights/mb140/run042_longer_context_no_token_seed42.pth`</small> | MultiBypass140 | research | `34569e90fd9d` | 1.4 GB | 12.46 |
| `papers/paper1_neurips2026/reproducibility/weights/cholec80/run018_seed123.pth` | Cholec80 + MultiBypass140 | research | `bba3354fc848` | 1.4 GB | — |
| `papers/paper1_neurips2026/reproducibility/weights/cholec80/run018_seed42.pth` | Cholec80 + MultiBypass140 | research | `2054bc8cc7c1` | 1.4 GB | 3.694 |
| `papers/paper1_neurips2026/reproducibility/weights/cholec80/run018_seed777.pth` | Cholec80 + MultiBypass140 | research | `5d98d8baf60c` | 1.4 GB | — |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_decoupled_seed123.pth` | MultiBypass140 | research | `c542fd1d07e9` | 1.4 GB | 12.19 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_decoupled_seed42.pth` | MultiBypass140 | research | `388cb192eb53` | 1.4 GB | 12.32 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_decoupled_seed777.pth` | MultiBypass140 | research | `ce60b90da157` | 1.4 GB | 12.04 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_no_token_seed123.pth` | MultiBypass140 | research | `d488e952b7b3` | 1.4 GB | 13.1 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_no_token_seed42.pth` | MultiBypass140 | research | `9c4429fd3f42` | 1.4 GB | 13.17 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_no_token_seed777.pth` | MultiBypass140 | research | `12b727f68b2f` | 1.4 GB | 12.83 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_oracle_seed123.pth` | MultiBypass140 | research | `65ccaf0ec496` | 1.4 GB | 12.23 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_oracle_seed42.pth` | MultiBypass140 | research | `b461ddde90eb` | 1.4 GB | 12.18 |
| `papers/paper1_neurips2026/reproducibility/weights/mb140/run033_oracle_seed777.pth` | MultiBypass140 | research | `d350a1de55ad` | 1.4 GB | 12.36 |

ᵐ hash taken from the manifest rather than recomputed; ⚠︎ recomputed hash disagrees with the manifest.

## 5. Label and cluster artifacts

| Artifact | Dataset | Kind | SHA256 | Declared provenance |
|---|---|---|---|---|
| `cholec80_kmeans_artifacts.json` | Cholec80 | cluster-artifact | `3325145921ed` | K=4; seed=42; n_features=10; n_components=10; source_labels=labels/cholec80_labels.json; **min_df not recorded** |
| `cholec80_labels.json` | Cholec80 | label | `28aaa47fbca1` | n_videos=72; splits={"test": 30, "train": 36, "val": 6}; video_id_prefixes={"vid": 72} |
| `cholec80_labels_kmeans.json` | Cholec80 | label | `81cf5affe531` | n_videos=72; splits={"test": 30, "train": 36, "val": 6}; video_id_prefixes={"vid": 72} |
| `cholec80_prefix_clusters.json` | Cholec80 | cluster-artifact | `dcc0b4296069` | **min_df not recorded** |
| `mb140_cross_center_bern_train_stras_val_kmeans.json` | MultiBypass140 | label | `0c31ae391247` | n_videos=140; splits={"train": 70, "val": 70}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_cross_center_kmeans_artifacts.json` | MultiBypass140 | cluster-artifact | `9283e5a6e81a` | K=6; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_cross_center_bern_train_stras_val_kmeans.json; **min_df not recorded** |
| `mb140_cross_center_prefix_clusters.json` | MultiBypass140 | cluster-artifact | `1f16e81d5e7b` | **min_df not recorded** |
| `mb140_fold0_kmeans_artifacts.json` | MultiBypass140 | cluster-artifact | `a02bd2c32f3b` | K=6; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold0_labels.json; **min_df not recorded** |
| `mb140_fold0_kmeans_artifacts_k4.json` | MultiBypass140 | cluster-artifact | `cc2a3d23c004` | K=4; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold0_labels.json; **min_df not recorded** |
| `mb140_fold0_kmeans_artifacts_k8.json` | MultiBypass140 | cluster-artifact | `9194f5f7e6a2` | K=8; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold0_labels.json; **min_df not recorded** |
| `mb140_fold0_labels.json` | MultiBypass140 | label | `191058a8ca1e` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_labels_kmeans.json` | MultiBypass140 | label | `61dfe5ac7529` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_labels_kmeans_k4.json` | MultiBypass140 | label | `f20b82dbea7d` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_labels_kmeans_k8.json` | MultiBypass140 | label | `291c37061aee` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_labels_kmeans_overfit.json` | MultiBypass140 | label | `730505d07343` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_labels_kmeans_overfit_k1.0.json` | MultiBypass140 | label | `7509fd664a4a` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_labels_kmeans_shuffled.json` | MultiBypass140 | label | `8c2ec0d50a53` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold0_prefix_clusters.json` | MultiBypass140 | cluster-artifact | `c1527e7697bf` | **min_df not recorded** |
| `mb140_fold1_kmeans_artifacts.json` | MultiBypass140 | cluster-artifact | `cbfb6690e4cb` | K=6; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold1_labels.json; **min_df not recorded** |
| `mb140_fold1_labels.json` | MultiBypass140 | label | `bbcfc9837694` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold1_labels_kmeans.json` | MultiBypass140 | label | `dfa4b25084d3` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold1_prefix_clusters.json` | MultiBypass140 | cluster-artifact | `febdf33fd133` | **min_df not recorded** |
| `mb140_fold2_kmeans_artifacts.json` | MultiBypass140 | cluster-artifact | `a86435c73f14` | K=6; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold2_labels.json; **min_df not recorded** |
| `mb140_fold2_labels.json` | MultiBypass140 | label | `34794de878e5` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold2_labels_kmeans.json` | MultiBypass140 | label | `230ed17cee5a` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold2_prefix_clusters.json` | MultiBypass140 | cluster-artifact | `eb0a4659d298` | **min_df not recorded** |
| `mb140_fold3_kmeans_artifacts.json` | MultiBypass140 | cluster-artifact | `c01cdd3f1044` | K=6; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold3_labels.json; **min_df not recorded** |
| `mb140_fold3_labels.json` | MultiBypass140 | label | `7fadc64a229a` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold3_labels_kmeans.json` | MultiBypass140 | label | `0a36caea8e72` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold3_prefix_clusters.json` | MultiBypass140 | cluster-artifact | `4787fac789e6` | **min_df not recorded** |
| `mb140_fold4_kmeans_artifacts.json` | MultiBypass140 | cluster-artifact | `468861fa6a87` | K=6; seed=42; n_features=63; n_components=16; source_labels=labels/mb140_fold4_labels.json; **min_df not recorded** |
| `mb140_fold4_labels.json` | MultiBypass140 | label | `300c27bcb471` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold4_labels_kmeans.json` | MultiBypass140 | label | `2b6bf870c376` | n_videos=140; splits={"test": 40, "train": 80, "val": 20}; video_id_prefixes={"BBP": 70, "SBP": 70} |
| `mb140_fold4_prefix_clusters.json` | MultiBypass140 | cluster-artifact | `1cab932d408b` | **min_df not recorded** |

> **`min_df` is not recorded in any cluster artifact.** As noted in
> `plans/STRATEGY.md` §V.3, the stored artifacts therefore do not
> establish a matched-K/`min_df` comparison across datasets. Run a
> train-only matched-configuration control before interpreting
> cross-dataset representation differences.

## 6. Regenerating

```bash
python -m brsd_lib.data_lineage              # rewrite this file
python -m brsd_lib.data_lineage --hash all   # also hash unlisted checkpoints
python -m brsd_lib.data_lineage --verify     # integrity check only
```

Regenerate before any release, any external deposit, and after any training
run that produces a new checkpoint.

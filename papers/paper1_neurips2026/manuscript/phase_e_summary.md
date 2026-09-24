# Phase E — Strict-protocol 5-fold × 3-seed extension

Validation MAE (minutes), best-checkpoint, all 5 folds × 3 seeds.
Fold 0 reference: Run 033 (already in §6.1 headline). Folds 1-4: Phase E.

## Per-fold mean ± std

| Fold | no-token | oracle | decoupled-oracle | Δ oracle | Δ decoupled |
|---:|---:|---:|---:|---:|---:|
| 0 | 13.03 ± 0.18 | 12.26 ± 0.09 | 12.18 ± 0.14 | -0.78 | -0.85 |
| 1 | 11.29 ± 0.13 | 11.32 ± 0.29 | 11.07 ± 0.13 | +0.03 | -0.23 |
| 2 | 11.60 ± 0.19 | 11.62 ± 0.26 | 11.84 ± 0.14 | +0.01 | +0.23 |
| 3 | 10.27 ± 0.07 | 10.32 ± 0.11 | 10.39 ± 0.13 | +0.06 | +0.13 |
| 4 | 8.90 ± 0.22 | 8.67 ± 0.13 | 8.68 ± 0.18 | -0.23 | -0.22 |
| **All** | **11.02 ± 1.44** | **10.84 ± 1.30** | **10.83 ± 1.29** | **-0.18** | **-0.19** |

Total runs: 5 folds × 3 conditions × 3 seeds = 45 (15 per condition).
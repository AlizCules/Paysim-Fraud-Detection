# Legacy results

The following values were extracted from the existing small pickle dictionaries. They are preserved for auditability only and are **not official portfolio benchmarks** because the original split, feature provenance, threshold-selection process, and environment compatibility were not fully reproducible.

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1 | Legacy threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | not stored in pickle | not stored in pickle | 0.5707 | 0.5648 | 0.5678 | 0.8396 |
| Random Forest | 0.9664 | 0.7321 | 0.7682 | 0.6372 | 0.6966 | 0.6348 |
| XGBoost | 0.9716 | 0.7635 | 0.8198 | 0.6506 | 0.7255 | 0.8257 |

The canonical branch generates a new comparison under `results/model_comparison.csv`. Legacy numbers should not be copied into the README unless the canonical run independently reproduces them.

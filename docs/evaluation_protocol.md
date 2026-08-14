# Evaluation protocol

1. Build chronological train, validation, and test periods.
2. Downsample only the training negative class when the full source is available.
3. Fit preprocessing and model parameters on the training period.
4. Select one threshold per model and feature set on validation using maximum F1 over a deterministic grid.
5. Freeze the selected threshold.
6. Evaluate each frozen model once on the untouched chronological test period.

Primary metrics are ROC-AUC and Average Precision. The report also includes precision, recall, F1, confusion matrix, fraud prevalence, alert rate, and the selected threshold. Because the training distribution can be sampled, outputs use `fraud_score` terminology rather than claiming calibrated fraud probabilities.

The official comparison is stored in `results/model_comparison.csv`. Threshold selection is recorded in `results/model_thresholds.json`, and threshold trade-offs are stored in `results/threshold_tradeoffs.csv`.

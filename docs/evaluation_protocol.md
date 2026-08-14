# Evaluation protocol

1. Build chronological train, validation, and test periods.
2. Downsample only the training negative class when the full source is available.
3. Fit preprocessing and model parameters on the training period.
4. Select one threshold per model and feature set on validation using maximum F1 over a deterministic grid.
5. Use validation F1 as the rule for selecting the highlighted model whose feature importance is reported.
6. Create `threshold_tradeoffs.csv` from validation scores only.
7. Freeze thresholds and the candidate set.
8. Evaluate each frozen candidate once on the untouched chronological test period.

Primary metrics are ROC-AUC and Average Precision. The report also includes precision, recall, F1, confusion matrix, fraud prevalence, alert rate, and the selected threshold. Because the training distribution can be sampled, outputs use `fraud_score` terminology rather than claiming calibrated fraud probabilities.

The validation artifact is stored in `results/validation_metrics.csv`. Threshold selection is recorded in `results/model_thresholds.json`, the validation-only trade-off table is stored in `results/threshold_tradeoffs.csv`, and the validation-selected highlight model is recorded in `results/selected_model.json`.

The official comparison is stored in `results/model_comparison.csv` and is explicitly marked `split=test`. Test labels are used only for final frozen performance reporting; they are not used for threshold selection, model selection, feature selection, ablation selection, or threshold trade-off exploration.

Feature importance describes model usage/association, not causal effect. In the post-transaction scope, residual and new-balance features use accounting state observed after the transaction and therefore must not be described as pre-authorization or real-time prevention features.

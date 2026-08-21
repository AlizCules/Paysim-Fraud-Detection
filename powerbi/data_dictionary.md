# Power BI Data Dictionary

These CSVs are clean, recruiter-facing copies of tracked aggregate outputs. Values are preserved from the canonical result artifacts; no row-level PaySim data is included.

## Files and sources

| Power BI file | Source artifact | Intended use |
| --- | --- | --- |
| `overall_fraud_summary.csv` | `results/sql/total_transactions.csv` | Overall fraud-rate KPI card |
| `fraud_rate_by_type.csv` | `results/sql/fraud_by_type.csv` | Fraud-rate and fraud-amount comparison by transaction type |
| `fraud_rate_by_hour.csv` | `results/sql/fraud_by_hour.csv` | Fraud-rate line chart by simulated hour |
| `fraud_rate_by_day.csv` | `results/sql/fraud_by_day.csv` | Fraud-rate comparison by simulated day |
| `fraud_rate_by_amount_band.csv` | `results/sql/fraud_by_amount_band.csv` | Fraud-rate comparison by amount band |
| `fraud_rate_by_segment.csv` | `results/sql/high_risk_segments.csv` | High-risk type/hour segment table or matrix |
| `alert_volume_selected_output.csv` | `results/sql/alert_volume.csv` | Selected scored-output alert KPI |
| `alert_volume_by_model_threshold.csv` | `results/model_comparison.csv` | Final-test alert-rate comparison by model, feature scope and frozen threshold |

The SQL `alert_volume.csv` contains the aggregate scored output for the selected run and therefore does not contain model/threshold dimensions. The model/threshold comparison is copied from the verified final-test `results/model_comparison.csv` artifact rather than inferred or recomputed.

## Columns

### Overall fraud summary

- `transactions`: total source transactions.
- `fraud_transactions`: source transactions labeled fraudulent.
- `non_fraud_transactions`: source transactions labeled non-fraudulent.
- `fraud_rate`: `fraud_transactions / transactions` as stored in the source output.

### Fraud-rate breakdowns

- `type`: transaction type (`TRANSFER`, `CASH_OUT`, `CASH_IN`, `PAYMENT`, or `DEBIT`).
- `hour`: simulated transaction hour.
- `day`: simulated transaction day.
- `amount_band`: amount range label.
- `transactions`: transactions in the grouping.
- `fraud_transactions`: fraudulent transactions in the grouping.
- `fraud_rate`: fraud rate stored for the grouping.
- `fraud_amount`: aggregate amount of fraudulent transactions by type, retained from the SQL output.

### Segment and alert outputs

- `model`: model family used for the final-test score.
- `feature_set`: `pre_transaction` or `post_transaction` feature scope.
- `split`: evaluation split; these comparison rows are `test`.
- `threshold`: frozen validation-selected threshold used for the final-test comparison.
- `alert_rate`: share of scored transactions flagged at that threshold.
- `test_rows`: final-test rows scored for the model/feature-set combination.
- `scored_transactions`: number of transactions in the selected scored output.
- `alerts`: alert count in the selected scored output.
- `mean_fraud_score`: mean score in the selected scored output.

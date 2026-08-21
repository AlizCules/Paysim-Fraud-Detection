# Power BI Data Dictionary

These CSVs are aggregate, BI-ready copies of verified repository outputs. They contain no row-level PaySim data. PaySim is simulated data, not real bank transaction data; the rates and alert outputs are for exploratory analysis and offline review-prioritization study.

## `overall_fraud_summary.csv`

Source: [`../results/sql/total_transactions.csv`](../results/sql/total_transactions.csv)

Grain: one row for the full source transaction population.

| Column | Type | Meaning |
| --- | --- | --- |
| `transactions` | integer | Total source transactions. |
| `fraud_transactions` | integer | Transactions labeled `isFraud = 1`. |
| `non_fraud_transactions` | integer | Transactions labeled `isFraud = 0`. |
| `fraud_rate` | decimal | `fraud_transactions / transactions` as stored in the SQL output. |

Caveat: this is a source-level simulated prevalence KPI, not a real-bank fraud rate.

## `fraud_rate_by_type.csv`

Source: [`../results/sql/fraud_by_type.csv`](../results/sql/fraud_by_type.csv)

Grain: one row per PaySim transaction type.

| Column | Type | Meaning |
| --- | --- | --- |
| `type` | text | PaySim transaction type, such as `TRANSFER` or `CASH_OUT`. |
| `transactions` | integer | Transactions in the type group. |
| `fraud_transactions` | integer | Fraud-labeled transactions in the type group. |
| `fraud_rate` | decimal | Average of `isFraud` within the type group. |
| `fraud_amount` | decimal | Sum of `amount` for fraud-labeled transactions in the type group; not a loss estimate. |

Caveat: type differences are simulator associations and should not be treated as causal rules.

## `fraud_rate_by_hour.csv`

Source: [`../results/sql/fraud_by_hour.csv`](../results/sql/fraud_by_hour.csv)

Grain: one row per simulated hour, calculated as `MOD(step, 24)`.

| Column | Type | Meaning |
| --- | --- | --- |
| `hour` | integer | Simulated hour bucket from 0 through 23 where present. |
| `transactions` | integer | Transactions in the hour group. |
| `fraud_transactions` | integer | Fraud-labeled transactions in the hour group. |
| `fraud_rate` | decimal | Average of `isFraud` within the hour group. |

Caveat: `hour` is a simulator-derived bucket, not a timezone-aware operational timestamp.

## `fraud_rate_by_day.csv`

Source: [`../results/sql/fraud_by_day.csv`](../results/sql/fraud_by_day.csv)

Grain: one row per simulated day bucket, calculated as `CAST(step / 24 AS INTEGER)`.

| Column | Type | Meaning |
| --- | --- | --- |
| `day` | integer | Simulated day bucket. |
| `transactions` | integer | Transactions in the day group. |
| `fraud_transactions` | integer | Fraud-labeled transactions in the day group. |
| `fraud_rate` | decimal | Average of `isFraud` within the day group. |

Caveat: day buckets show simulator patterns only and do not establish calendar or seasonal causality.

## `fraud_rate_by_amount_band.csv`

Source: [`../results/sql/fraud_by_amount_band.csv`](../results/sql/fraud_by_amount_band.csv)

Grain: one row per SQL-defined amount band.

| Column | Type | Meaning |
| --- | --- | --- |
| `amount_band` | text | SQL-defined amount range label. |
| `transactions` | integer | Transactions in the amount band. |
| `fraud_transactions` | integer | Fraud-labeled transactions in the amount band. |
| `fraud_rate` | decimal | Average of `isFraud` within the amount band. |

Caveat: amount-band differences are screening signals for further investigation, not a standalone fraud rule.

## `fraud_rate_by_segment.csv`

Source: [`../results/sql/high_risk_segments.csv`](../results/sql/high_risk_segments.csv)

Grain: one retained type/hour segment with at least 1,000 transactions, ordered by simulated fraud rate and limited by the SQL query.

| Column | Type | Meaning |
| --- | --- | --- |
| `type` | text | PaySim transaction type in the segment. |
| `hour` | integer | Simulated hour in the segment. |
| `transactions` | integer | Transactions in the type/hour segment. |
| `fraud_transactions` | integer | Fraud-labeled transactions in the segment. |
| `fraud_rate` | decimal | Average of `isFraud` within the type/hour segment. |

Caveat: this is a compact exploratory segment output, not a causal explanation or production rule list.

## `alert_volume_selected_output.csv`

Source: [`../results/sql/alert_volume.csv`](../results/sql/alert_volume.csv)

Grain: one aggregate for the scored prediction output available to the SQL query.

| Column | Type | Meaning |
| --- | --- | --- |
| `scored_transactions` | integer | Transactions present in the scored output. |
| `alerts` | integer | Rows with `fraud_flag = 1` in the scored output. |
| `alert_rate` | decimal | Share of scored rows flagged. |
| `mean_fraud_score` | decimal | Mean model score in the scored output; not a calibrated probability. |

Caveat: this SQL aggregate has no model or threshold dimension. Use `alert_volume_by_model_threshold.csv` for the verified candidate comparison; do not label this aggregate as a particular canonical model unless the scored-output provenance is separately established.

## `alert_volume_by_model_threshold.csv`

Source: [`../results/model_comparison.csv`](../results/model_comparison.csv)

Grain: one final-test row per model and feature-scope candidate.

| Column | Type | Meaning |
| --- | --- | --- |
| `model` | text | Candidate model family. |
| `feature_set` | text | `pre_transaction` or `post_transaction` feature scope. |
| `split` | text | Evaluation split; these rows are `test`. |
| `threshold` | decimal | Frozen threshold selected on validation for the candidate. |
| `alert_rate` | decimal | Share of final-test rows flagged at the frozen threshold. |
| `test_rows` | integer | Number of final-test rows scored. |

Caveat: this is a final-test comparison after validation-only selection, not a production alert threshold, staffing estimate or banking policy.

## Cross-file interpretation rules

- Format `fraud_rate` and `alert_rate` as percentages in Power BI.
- Keep counts, hours, days and `test_rows` numeric.
- Preserve the amount-band ordering `<1k`, `1k-10k`, `10k-100k`, `100k-1m`, `>=1m` when building visuals.
- Keep the PaySim simulated-data caveat visible on every dashboard page.

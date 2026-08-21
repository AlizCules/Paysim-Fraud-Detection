# Power BI Dashboard Guide

This guide assembles a compact analyst-facing dashboard from the aggregate CSVs in [`../powerbi/`](../powerbi/). The source is PaySim simulated data, not real bank transaction data. The dashboard is for exploratory fraud analytics and offline review-prioritization study, not production monitoring or real-time prevention.

## 1. Load and model the data

1. Open Power BI Desktop and choose **Get data → Text/CSV**.
2. Import the eight CSV files in [`../powerbi/`](../powerbi/): the overall KPI, five fraud-pattern tables, the SQL scored-output table and the model/threshold comparison table.
3. Use [`../powerbi/data_dictionary.md`](../powerbi/data_dictionary.md) to confirm source mapping, grain and field meanings.
4. Set `fraud_rate` and `alert_rate` to **Percentage**. Keep counts, `hour`, `day`, `threshold` and `test_rows` numeric.
5. Do not relate the aggregate tables unless needed for a visual; each table is already at its documented reporting grain.

## 2. Suggested one-page layout

### Top row — KPI cards

| Visual | Dataset | Field/value | Analytical question |
| --- | --- | --- | --- |
| Card | `overall_fraud_summary.csv` | `transactions` | How large is the source transaction population? |
| Card | `overall_fraud_summary.csv` | `fraud_rate` | What is the source fraud prevalence in PaySim? |
| Card | `overall_fraud_summary.csv` | `fraud_transactions` | How many source rows are fraud-labeled? |
| Card | `alert_volume_selected_output.csv` | `alerts` or `alert_rate` | What scored-output volume and rate are available for the SQL alert artifact? |

Label the cards as **PaySim simulated**. The SQL scored-output table has no model or threshold dimension; use `alert_volume_by_model_threshold.csv` for candidate comparisons.

### Middle row — Fraud patterns

| Visual | Dataset | Axis/category | Value | Sort/tooltip | Analytical question |
| --- | --- | --- | --- | --- | --- |
| Clustered bar chart | `fraud_rate_by_type.csv` | `type` | `fraud_rate` | Sort descending; tooltip `transactions`, `fraud_transactions`, `fraud_amount` | Which transaction types have higher simulated fraud rates and fraud amounts? |
| Column chart | `fraud_rate_by_amount_band.csv` | `amount_band` | `fraud_rate` | Sort in SQL order `<1k` → `>=1m`; tooltip `transactions`, `fraud_transactions` | How does the simulated rate vary by amount band? |
| Line chart | `fraud_rate_by_hour.csv` | `hour` | `fraud_rate` | Sort numerically; tooltip `transactions`, `fraud_transactions` | Which simulated hour buckets are worth further review? |
| Line chart | `fraud_rate_by_day.csv` | `day` | `fraud_rate` | Sort numerically; tooltip `transactions`, `fraud_transactions` | How does the simulated rate vary across day buckets? |

### Bottom row — Review prioritization and model comparison

| Visual | Dataset | Axis/category | Value | Sort/tooltip | Analytical question |
| --- | --- | --- | --- | --- | --- |
| Matrix or table | `fraud_rate_by_segment.csv` | Rows `type`, `hour` | `fraud_rate` | Sort descending; show `transactions`, `fraud_transactions` | Which retained type/hour segments warrant closer investigation in the simulator? |
| Clustered bar chart or table | `alert_volume_by_model_threshold.csv` | Category `model` + `feature_set` | `alert_rate` | Show `threshold` and `test_rows` as tooltips; keep `split=test` visible | How do frozen candidates trade off flagged volume in the final test comparison? |

## 3. Formatting and interpretation

- Display rates to two or four decimal percentage places depending on visual space; do not round the source CSV values before loading.
- Keep the amount-band order from the source instead of sorting alphabetically.
- Use a tooltip with counts whenever a rate is shown; a rate without its denominator can be misleading in imbalanced data.
- Treat type, time, amount-band and segment differences as simulator associations, not causal business rules.
- The model comparison uses thresholds selected on validation and reports the untouched chronological test once. It is not a production threshold, staffing estimate or operational cost policy.
- Post-transaction candidates include new balances and residual/accounting features and therefore describe monitoring after transaction state is available, not pre-authorization or real-time blocking.

## 4. Reproducible HTML preview

Run the repository script from the project root:

```powershell
& ".\.venv\Scripts\python.exe" scripts/build_dashboard.py
```

The script reads only the verified files under [`../powerbi/`](../powerbi/) and writes [`../reports/dashboard.html`](../reports/dashboard.html). Open that file locally to inspect the interactive HTML artifact. It is not hosted or a live production dashboard.

# Power BI Dashboard Guide

This guide assembles a compact analyst-facing dashboard from the CSVs in [`../powerbi/`](../powerbi/). The files contain aggregate outputs only; the source is the simulated PaySim project, not real bank transaction data.

## 1. Load the data

1. Open Power BI Desktop.
2. Choose **Get data → Text/CSV**.
3. Import the eight CSV files in [`../powerbi/`](../powerbi/), keeping the column names and numeric types.
4. In **Modeling**, format `fraud_rate` and `alert_rate` as percentages. Keep `hour`, `day`, `transactions`, `fraud_transactions`, `alerts` and `test_rows` numeric.
5. Use the included [`data_dictionary.md`](../powerbi/data_dictionary.md) to confirm each field and source artifact.

## 2. Suggested one-page layout

### Top row: KPI cards

- **Overall fraud rate:** use `fraud_rate` from `overall_fraud_summary.csv`.
- **Source transactions:** use `transactions` from `overall_fraud_summary.csv`.
- **Selected alert volume:** use `alerts` from `alert_volume_selected_output.csv`.
- **Selected alert rate:** use `alert_rate` from `alert_volume_selected_output.csv`.

Keep the labels explicit that the values come from simulated PaySim data.

### Middle row: operational patterns

- **Clustered column chart — Fraud rate by type:** source `fraud_rate_by_type.csv`; axis `type`, values `fraud_rate`. Add `fraud_transactions` to the tooltip.
- **Line chart — Fraud rate by hour:** source `fraud_rate_by_hour.csv`; axis `hour`, values `fraud_rate`. Sort the x-axis numerically.
- **Column chart — Fraud rate by amount band:** source `fraud_rate_by_amount_band.csv`; axis `amount_band`, values `fraud_rate`. Preserve the business order from `<1k` through `>=1m`.

### Bottom row: review prioritization

- **Table — High-risk segments:** source `fraud_rate_by_segment.csv`; show `type`, `hour`, `transactions`, `fraud_transactions` and `fraud_rate`, sorted descending by `fraud_rate`.
- **Line or clustered column chart — Fraud rate by day:** source `fraud_rate_by_day.csv`; axis `day`, values `fraud_rate`.
- **Table or bar chart — Alert-rate trade-off:** source `alert_volume_by_model_threshold.csv`; use `model` and `feature_set` as the legend/category, `threshold` in the tooltip and `alert_rate` as the value.

## 3. Interpretation notes

- Use the dashboard to surface patterns for investigation and review prioritization, not to define a real-bank alert policy.
- The model/threshold table is final-test reporting after validation-only threshold selection. It is a comparison of the verified candidates, not an operational recommendation.
- The amount-band, type/hour and day patterns are associations in the PaySim simulator. They do not establish causal explanations or generalization to real financial transactions.
- The selected aggregate alert KPI comes from `results/sql/alert_volume.csv`; the model/threshold comparison comes from `results/model_comparison.csv` because the SQL aggregate does not contain model/threshold dimensions.

## 4. Optional preview

The same layout is previewed in [`../reports/dashboard.html`](../reports/dashboard.html). It embeds the values from the Power BI CSV exports so it can be opened as a lightweight static HTML preview.

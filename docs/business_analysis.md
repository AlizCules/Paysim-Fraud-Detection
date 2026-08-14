# Business and operations analysis

This project uses simulated transactions, so the analysis describes operational trade-offs inside PaySim rather than making claims about real banking losses.

The main operational questions are:

- How concentrated are simulated fraud events by transaction type and time?
- How does a selected alert threshold trade off recall against alert volume?
- Which amount bands and transaction segments have the highest simulated fraud rate?
- How much does the post-transaction feature set improve monitoring performance relative to the pre-transaction set?

Verified aggregate answers are exported under `results/sql/`. The SQL layer uses DuckDB and is defined in `sql/fraud_analysis.sql`. No monetary loss estimate is reported because the dataset does not provide a verified loss ground truth.

## Verified findings from the source data

- Fraud is concentrated in `TRANSFER` and `CASH_OUT`: the source fraud rates are 0.7688% and 0.1840%, respectively. `PAYMENT`, `DEBIT`, and `CASH_IN` contain no positive labels in this simulator.
- The `>=1m` amount band has a 2.0715% fraud rate, versus 0.1404% for the `100k-1m` band. This is an association in the simulator, not a proposed standalone rule.
- The highest-volume SQL segments include `TRANSFER` at simulated hour 7 (164 frauds in 1,048 transactions, 15.65%) and `CASH_OUT` at hour 2 (186 frauds in 1,256 transactions, 14.81%). These small, simulator-specific segments should be treated as exploratory monitoring slices rather than causal explanations.

## Validation threshold trade-off

Threshold decisions and the multi-threshold trade-off table are based on validation only and are exported to `results/threshold_tradeoffs.csv` with `split=validation`. The selected threshold for each frozen candidate maximizes validation F1; this is a reproducible comparison rule, not an operational recommendation. A real deployment would need a reviewed cost model, calibration, human-review capacity, and drift monitoring.

## Final test reporting

The final chronological test set is used once for frozen performance reporting in `results/model_comparison.csv`. It is not used to choose a threshold, model, feature set, or alert policy. The post-transaction Logistic Regression reports the lowest frozen test alert rate (1.1663%) but recalls 72.88% of fraud at 96.52% precision. Random Forest recalls 99.94% at a 1.5438% alert rate, while XGBoost recalls 100.00% at a 1.5467% alert rate. These are simulator-specific evaluation outputs rather than recommendations for a banking operation.

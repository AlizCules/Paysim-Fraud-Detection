# PaySim Transaction Fraud Analysis

An end-to-end analysis of simulated mobile-money transactions using EDA, SQL, leakage-aware feature engineering, imbalanced classification, threshold evaluation, and reproducible model comparison.

## Project at a Glance

| Evidence | Verified value |
| --- | ---: |
| Source transactions | 6,362,620 |
| Source fraud prevalence | 0.12908% |
| Row-level data distribution | Not included in the current tree |
| Final chronological test | 103,573 transactions |
| Best canonical post-transaction F1 | 0.9997 — validation-selected Random Forest, final chronological test |

## Analytical Question

How well can transaction-level information in the PaySim simulation distinguish fraudulent transactions, and what patterns are associated with fraud within this simulated environment?

## Data Source and Scope

The project uses the simulated [PaySim dataset](https://www.kaggle.com/datasets/ealaxi/paysim1). PaySim row-level data is not distributed with this repository: the approximately 470 MB raw CSV must be obtained from a permitted source copy and kept locally outside Git. See [`data/README.md`](data/README.md), [`docs/data_sources.md`](docs/data_sources.md), and [`docs/limitations.md`](docs/limitations.md).

The official portfolio scope is **post-transaction monitoring** because it uses `newbalanceOrig` and `newbalanceDest`. The pre-transaction feature set is a screening comparison only; neither scope is presented as real-time prevention or pre-authorization prevention.

## Data Preparation

When the permitted raw source is available locally, the split is chronological:

- train: `step <= 500`;
- validation: `501 <= step <= 600`;
- final test: `step > 600`.

Negative-class downsampling occurs only in train. Validation and test retain natural source prevalence and are not downsampled. The canonical run records the split facts in [`results/data_summary.json`](results/data_summary.json) and [`results/split_summary.csv`](results/split_summary.csv).

The aggregate artifacts in this repository were generated from a local full source before the current-tree data cleanup. The pipeline requires the local raw file and does not silently fall back to a tracked sample.

## Exploratory Fraud Analysis

![Fraud prevalence in the source and working sample](figures/fraud_prevalence.png)

![Fraud rate by transaction type](figures/fraud_by_type.png)

Verified SQL and EDA findings show that fraud is concentrated in `TRANSFER` and `CASH_OUT`; the `>=1m` amount band has a higher simulated fraud rate than smaller bands. These are associations in a simulator, not standalone business rules or causal explanations. See [`docs/business_analysis.md`](docs/business_analysis.md).

## Feature Engineering

Two explicit feature contracts are maintained:

- `pre_transaction`: time, type, amount, old balances, and descriptive destination-role flags;
- `post_transaction`: the pre-transaction set plus new balances and accounting residual features.

Both contracts exclude `isFraud`, `isFlaggedFraud`, raw `nameOrig`/`nameDest` identifiers, target-informed heuristics, and aggregate/history features without a point-in-time implementation. Feature importance describes model usage/association, not causal effect; post-transaction residual features use balances observed after the transaction.

## Evaluation Protocol

Models are fit on the chronological training period. One threshold per model and feature set is selected on validation using maximum F1 over a deterministic grid. The highlighted model and [`results/feature_importance.csv`](results/feature_importance.csv) are selected using validation F1, with validation Average Precision as the tie-breaker; the decision is recorded in [`results/selected_model.json`](results/selected_model.json). Threshold trade-offs are also generated from validation only.

The test set is then evaluated once with frozen candidates and frozen validation-selected thresholds. [`results/model_comparison.csv`](results/model_comparison.csv) is explicitly the **final chronological test results** artifact; test labels are not used for threshold selection, model selection, feature selection, ablation selection, or threshold trade-off exploration. Full details are in [`docs/evaluation_protocol.md`](docs/evaluation_protocol.md).

## Model Comparison

![Average precision on the final chronological test period](figures/model_average_precision.png)

Final test results for both feature scopes:

| Feature scope | Model | ROC-AUC | Avg. Precision | Precision | Recall | F1 | Threshold | Alert rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pre | Logistic Regression | 0.9955 | 0.8423 | 0.8800 | 0.6144 | 0.7236 | 0.975 | 1.0785% |
| Pre | Random Forest | 1.0000 | 0.9999 | 1.0000 | 0.9931 | 0.9966 | 0.885 | 1.5342% |
| Pre | XGBoost | 1.0000 | 0.9996 | 0.9883 | 0.9994 | 0.9938 | 0.990 | 1.5622% |
| Post | Logistic Regression | 0.9973 | 0.9334 | 0.9652 | 0.7288 | 0.8305 | 0.985 | 1.1663% |
| Post | Random Forest | 1.0000 | 1.0000 | 1.0000 | 0.9994 | 0.9997 | 0.695 | 1.5438% |
| Post | XGBoost | 1.0000 | 1.0000 | 0.9988 | 1.0000 | 0.9994 | 0.080 | 1.5467% |

The extremely high scores are specific to PaySim's simulated transaction/accounting structure. They do not establish production banking performance, industry-grade fraud detection, or performance on real financial transaction data.

## Pre- vs Post-Transaction Analysis

Post-transaction features improve the canonical test metrics in this simulation, especially for Logistic Regression. This is an offline monitoring comparison: `newbalanceOrig`, `newbalanceDest`, and residual features are not available for a pre-authorization decision.

## Threshold and Alert Trade-offs

[`results/threshold_tradeoffs.csv`](results/threshold_tradeoffs.csv) contains validation-only threshold trade-offs with `split=validation`. It supports transparent threshold selection without using the test labels. Final test alert rates in `model_comparison.csv` are frozen performance reports, not threshold recommendations.

## SQL Analysis

The SQL layer uses DuckDB and is defined in [`sql/fraud_analysis.sql`](sql/fraud_analysis.sql). It answers questions about:

- total transactions and fraud rate;
- fraud by transaction type and fraud amount;
- fraud by simulated hour and day;
- fraud by amount band;
- high-risk type/hour segments;
- final scored alert volume.

Exported tables are available under [`results/sql/`](results/sql/).

## Repository Structure

```text
data/       raw-source instructions; no row-level data is distributed
src/        data, features, models, and evaluation modules
scripts/    preparation, training, evaluation, figures, SQL, and scoring CLIs
sql/        DuckDB analysis queries
models/     locally rebuilt canonical model outputs (ignored)
results/    validation/test metrics and aggregate artifacts
figures/    recruiter-facing charts
docs/       methodology, provenance, limitations, and audit notes
legacy/     original notebooks, reports, pickles, and outputs retained for audit
tests/      lightweight methodology and integrity tests
```

Legacy artifacts are preserved for auditability and are not the canonical workflow.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Place a permitted PaySim source copy at data/raw/ first.
python run_pipeline.py prepare
python run_pipeline.py train
python run_pipeline.py evaluate
python run_pipeline.py figures
python run_pipeline.py sql
```

If the raw source is unavailable, the pipeline stops with an explicit message explaining where to place the permitted file.

## Limitations

PaySim is simulated data, not real bank transaction data. Simulator-specific patterns can make classification unusually easy. The models have not been validated on real financial transactions, no calibrated probability or financial-loss ground truth is claimed, and the validation-F1 threshold is not an operational cost policy. Row-level dataset redistribution remains unverified, so the raw file, former working sample, and transaction-level prediction exports are excluded from the current tree. Earlier private history is not rewritten or represented as erased.

## Project Context and Attribution

The original report contains team/course context. This repository uses neutral wording and does not claim individual authorship or invent personal contributions. See [`docs/audit_findings.md`](docs/audit_findings.md) and [`legacy/reports/coursework_report.pdf`](legacy/reports/coursework_report.pdf).

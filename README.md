# PaySim Transaction Fraud Analysis

An end-to-end analysis of simulated mobile-money transactions using PaySim, covering data quality, fraud-pattern analysis, leakage-aware feature engineering, imbalanced classification, threshold evaluation, SQL analysis, and reproducible model comparison.

## Project at a glance

| Item | Verified value |
| --- | ---: |
| Source transactions | 6,362,620 |
| Source fraud prevalence | 0.12908% |
| Tracked working sample | 325,934 rows |
| Working-sample fraud prevalence | 2.51984% |
| Final test period | `step > 600` when raw source is available |
| Official model metrics | 6 canonical comparisons in `results/model_comparison.csv` |

## Analytical question

How well can transaction-level information in the PaySim simulation distinguish fraudulent transactions, and what transaction patterns are most associated with fraud within the simulated environment?

## Data source and scope

The project uses the simulated [PaySim dataset](https://www.kaggle.com/datasets/ealaxi/paysim1). The full raw CSV is intentionally kept outside Git because it is approximately 470 MB. The tracked working sample retains all fraud rows and approximately 5% of source non-fraud rows for practical development. See [`data/README.md`](data/README.md) and [`docs/data_sources.md`](docs/data_sources.md).

The official portfolio scope is post-transaction monitoring because the post-transaction feature set uses `newbalanceOrig` and `newbalanceDest`. A pre-transaction feature set is evaluated separately; neither scope is presented as production-ready prevention.

## Evaluation protocol

When the raw source is available, the split is chronological: train through step 500, validation through step 600, and final test after step 600. Negative-class downsampling occurs only in training. Thresholds are selected on validation using F1 and frozen before the single final test evaluation. Primary metrics are ROC-AUC and Average Precision, with precision, recall, F1, fraud prevalence, and alert rate reported alongside them.

### Canonical post-transaction test results

The table below reports the official monitoring scope on the untouched chronological test period. Thresholds were selected on validation only.

| Model | ROC-AUC | Avg. precision | Precision | Recall | F1 | Threshold | Alert rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.9973 | 0.9334 | 0.9652 | 0.7288 | 0.8305 | 0.985 | 1.1663% |
| Random Forest | 1.0000 | 1.0000 | 1.0000 | 0.9994 | 0.9997 | 0.695 | 1.5438% |
| XGBoost | 1.0000 | 1.0000 | 0.9988 | 1.0000 | 0.9994 | 0.080 | 1.5467% |

These unusually strong scores are specific to the PaySim simulator and its transaction/accounting fields. They are useful for demonstrating a reproducible workflow, not evidence of production performance, calibration, or real-world fraud detection capability. The Random Forest has the highest post-transaction F1 in this run; XGBoost has the highest Average Precision and recall.

## Reproduce

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Place a permitted PaySim source copy at data/raw/ when available.
python run_pipeline.py prepare
python run_pipeline.py train
python run_pipeline.py evaluate
python run_pipeline.py figures
python run_pipeline.py sql
```

If the raw source is unavailable, the pipeline falls back to `data/sample/data.csv` and records that limitation in `results/data_summary.json`.

## Analysis outputs

- `results/data_summary.json` and `results/split_summary.csv`: verified data and split facts.
- `results/model_comparison.csv`: canonical test metrics for both feature scopes.
- `results/model_thresholds.json`: validation-only threshold selection.
- `results/threshold_tradeoffs.csv`: alert-rate trade-offs.
- `results/feature_importance.csv`: feature ranking for the highest-Average-Precision post-transaction run.
- `results/sql/`: DuckDB analytical outputs.
- `figures/`: recruiter-facing charts.

## Repository structure

```text
data/       raw-source instructions and tracked sample
src/        data, features, models, and evaluation modules
scripts/    preparation, training, evaluation, figures, SQL, and scoring CLIs
sql/        DuckDB analysis queries
models/     locally rebuilt canonical model outputs (ignored)
results/    verified metrics and aggregate artifacts
figures/    presentation-ready charts
docs/       methodology, provenance, limitations, and audit notes
legacy/     original notebooks, reports, pickles, and outputs retained for audit
tests/      lightweight integrity tests
```

## Limitations and attribution

PaySim is a simulation, so findings describe the simulated environment and do not establish real-world banking behavior or financial impact. The original report contains team/course attribution; this portfolio branch uses neutral wording and does not claim individual authorship. See [`docs/limitations.md`](docs/limitations.md), [`docs/audit_findings.md`](docs/audit_findings.md), and [`docs/legacy_results.md`](docs/legacy_results.md).

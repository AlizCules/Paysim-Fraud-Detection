# Methodology audit findings

## Verified data variants

The local files were measured rather than inferred:

| Variant | Rows | Fraud | Non-fraud | Fraud rate | Step range |
| --- | ---: | ---: | ---: | ---: | --- |
| Full PaySim source | 6,362,620 | 8,213 | 6,354,407 | 0.12908% | 1-743 |
| Tracked working sample | 325,934 | 8,213 | 317,721 | 2.51984% | 1-743 |

The working sample keeps every fraud row and samples 317,721 non-fraud rows, which is 5.00001% of the source non-fraud population. Both measured files have no missing values in the 11 expected columns.

The earlier `data_description.txt` stated 517,898 rows and approximately 48 MB. That description does not match the raw file currently present, so it is retained under `legacy/` and is not used as canonical metadata.

## Existing artifacts

The repository contained three model pickle families, threshold dictionaries, evaluation dictionaries, notebooks, and PDFs. The small evaluation dictionaries contain the earlier legacy metrics documented in [`legacy_results.md`](legacy_results.md). The underlying split provenance, feature-selection process, and model-environment compatibility could not be established from those artifacts alone.

The legacy Logistic Regression evaluation notebook contains two error outputs and local machine paths. The older notebooks also contain hardcoded Windows paths and stale output cells. The course report PDF contains team/student/course attribution, so this repository uses neutral portfolio wording rather than claiming an individual project.

## Leakage and validity risks found

- The former aggregate features were calculated over a training window and could expose future or same-step transactions to a row. They are excluded from the official benchmark.
- `is_fraud_peak_hour` was chosen using fraud-oriented EDA and is excluded from the official benchmark.
- `day_bucket_risk` is target-informed and is excluded.
- `isFlaggedFraud` is a pre-existing system rule flag and is excluded.
- Raw `nameOrig` and `nameDest` identifiers are not model inputs.
- `newbalanceOrig` and `newbalanceDest` are post-transaction values. Models using them are described as post-transaction monitoring, not pre-authorization prevention.
- Legacy threshold values are not reused for the canonical test evaluation.

## Reproducibility issues addressed on this branch

- Dataset discovery uses `pathlib` and prefers the local raw source without hardcoding a user directory.
- Training, validation, and test periods are chronological.
- Negative-class downsampling occurs only in the training period when the full source is available.
- Thresholds are selected on validation and frozen before the single final test evaluation.
- Model, metric, SQL, figure, and integrity-test entry points are provided under `src/`, `scripts/`, `sql/`, `results/`, `figures/`, and `tests/`.

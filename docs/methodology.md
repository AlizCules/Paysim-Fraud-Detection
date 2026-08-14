# Canonical methodology

## Scope

The official portfolio scope is **post-transaction fraud monitoring**, with a pre-transaction feature set included as a comparison. This distinction matters because `newbalanceOrig` and `newbalanceDest` are observed after the transaction and are not appropriate for a pre-authorization claim.

## Data split

When the full local source is available:

- train: `step <= 500`;
- validation: `501 <= step <= 600`;
- final test: `step > 600`.

The split is defined before any randomization. Only training negatives are downsampled. Validation and test retain the source distribution and are never used for feature selection, hyperparameter selection, or threshold selection. If only the tracked working sample is available, the outputs explicitly state that the holdouts have working-sample prevalence.

## Features

The pre-transaction set uses time, transaction type, amount, old balances, and descriptive destination-role flags. The post-transaction set adds new balances and accounting residual features. Both sets:

- remove `isFlaggedFraud`;
- remove raw `nameOrig` and `nameDest` identifiers;
- avoid target-informed heuristics;
- avoid aggregate/history features until a point-in-time implementation is available.

The feature code does not claim that any feature has a causal effect.

## Models

The canonical comparison keeps three model families: Logistic Regression, Random Forest, and XGBoost. Preprocessing is part of each saved pipeline. Random seeds and model parameters are explicit. The canonical model artifacts are reproducible outputs of `scripts/train_models.py` and are ignored locally so a clean clone can rebuild them.

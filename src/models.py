"""Canonical, reproducible model factories."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier


def build_model(name: str, feature_frame: pd.DataFrame, random_state: int = 42) -> Pipeline:
    """Return a reproducible preprocessing + estimator pipeline."""

    if name not in {"logistic_regression", "random_forest", "xgboost"}:
        raise ValueError(f"Unknown model: {name}")
    numeric = [column for column in feature_frame.columns if is_numeric_dtype(feature_frame[column])]
    categorical = [column for column in feature_frame.columns if column not in numeric]
    preprocess = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler() if name == "logistic_regression" else "passthrough"),
                    ]
                ),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )

    if name == "logistic_regression":
        estimator = LogisticRegression(
            max_iter=500,
            class_weight="balanced",
            solver="liblinear",
            random_state=random_state,
        )
    elif name == "random_forest":
        estimator = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=random_state,
        )
    else:
        estimator = XGBClassifier(
            n_estimators=250,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="binary:logistic",
            eval_metric="logloss",
            tree_method="hist",
            n_jobs=4,
            random_state=random_state,
        )
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


def positive_score(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(frame)[:, 1]


def save_model(model: Pipeline, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, destination)


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(path)


def feature_importance(model: Pipeline, model_name: str) -> pd.DataFrame:
    preprocessor = model.named_steps["preprocess"]
    estimator = model.named_steps["model"]
    names = preprocessor.get_feature_names_out()
    if model_name == "logistic_regression":
        values = estimator.coef_[0]
        importance = np.abs(values)
    else:
        values = estimator.feature_importances_
        importance = values
    result = pd.DataFrame({"feature": names, "importance": importance, "signed_value": values})
    return result.sort_values("importance", ascending=False).reset_index(drop=True)

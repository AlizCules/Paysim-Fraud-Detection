"""Metrics and validation-only threshold selection for imbalanced classification."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def select_threshold(y_true: pd.Series, score: np.ndarray, objective: str = "f1") -> tuple[float, dict]:
    """Select a deterministic threshold on validation data only."""

    if objective != "f1":
        raise ValueError("Only validation F1 threshold selection is currently supported.")
    thresholds = np.linspace(0.01, 0.99, 197)
    best_threshold = 0.5
    best_value = -1.0
    for threshold in thresholds:
        value = f1_score(y_true, score >= threshold, zero_division=0)
        if value > best_value:
            best_value = float(value)
            best_threshold = float(threshold)
    details = {
        "selection_split": "validation",
        "selection_criterion": "max_f1",
        "validation_f1": best_value,
    }
    return best_threshold, details


def calculate_metrics(y_true: pd.Series, score: np.ndarray, threshold: float) -> dict:
    prediction = score >= threshold
    matrix = confusion_matrix(y_true, prediction, labels=[0, 1]).tolist()
    return {
        "roc_auc": float(roc_auc_score(y_true, score)),
        "average_precision": float(average_precision_score(y_true, score)),
        "precision": float(precision_score(y_true, prediction, zero_division=0)),
        "recall": float(recall_score(y_true, prediction, zero_division=0)),
        "f1": float(f1_score(y_true, prediction, zero_division=0)),
        "threshold": float(threshold),
        "fraud_prevalence": float(np.mean(y_true)),
        "alert_rate": float(np.mean(prediction)),
        "test_rows": int(len(y_true)),
        "confusion_matrix": matrix,
    }


def threshold_tradeoffs(y_true: pd.Series, score: np.ndarray, thresholds: list[float]) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        metrics = calculate_metrics(y_true, score, threshold)
        rows.append({key: metrics[key] for key in ["threshold", "precision", "recall", "f1", "alert_rate"]})
    return pd.DataFrame(rows)

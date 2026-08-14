from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.data import REQUIRED_COLUMNS, build_time_splits, downsample_training_negatives
from src.evaluation import calculate_metrics
from src.features import FEATURE_SETS, make_feature_frame


def sample_frame(rows: int = 12) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "step": np.arange(1, rows + 1),
            "type": ["TRANSFER", "CASH_OUT", "PAYMENT"] * (rows // 3) + ["PAYMENT"] * (rows % 3),
            "amount": np.linspace(100, 1200, rows),
            "nameOrig": [f"C{i}" for i in range(rows)],
            "oldbalanceOrg": np.linspace(1000, 3000, rows),
            "newbalanceOrig": np.linspace(900, 1800, rows),
            "nameDest": [f"M{i}" if i % 2 else f"C{i}" for i in range(rows)],
            "oldbalanceDest": np.linspace(300, 2500, rows),
            "newbalanceDest": np.linspace(400, 2700, rows),
            "isFraud": [0, 1] * (rows // 2) + [0] * (rows % 2),
            "isFlaggedFraud": [0] * rows,
        }
    )


def test_official_feature_contracts() -> None:
    frame = sample_frame()
    pre = make_feature_frame(frame, "pre_transaction")
    post = make_feature_frame(frame, "post_transaction")
    assert "isFraud" not in pre.columns
    assert "isFlaggedFraud" not in pre.columns
    assert "nameOrig" not in pre.columns
    assert "nameDest" not in pre.columns
    assert "newbalanceOrig" not in pre.columns
    assert "newbalanceDest" not in pre.columns
    assert "newbalanceOrig" in post.columns
    assert "newbalanceDest" in post.columns
    assert not np.isinf(post.select_dtypes(include=np.number)).any().any()
    assert not post.select_dtypes(include=np.number).isna().any().any()
    assert set(FEATURE_SETS) == {"pre_transaction", "post_transaction"}


def test_training_downsampling_keeps_all_fraud() -> None:
    frame = sample_frame(100)
    sampled = downsample_training_negatives(frame, negative_fraction=0.1, random_state=42)
    assert int(sampled["isFraud"].sum()) == int(frame["isFraud"].sum())
    assert len(sampled) < len(frame)


def test_chronological_split_does_not_overlap(tmp_path: Path) -> None:
    frame = sample_frame(30)
    csv_path = tmp_path / "transactions.csv"
    frame.to_csv(csv_path, index=False)
    splits, summary = build_time_splits(csv_path, train_end=10, validation_end=20, negative_fraction=1.0)
    assert splits["train"]["step"].max() <= 10
    assert splits["validation"]["step"].min() > 10
    assert splits["validation"]["step"].max() <= 20
    assert splits["test"]["step"].min() > 20
    assert [item["split"] for item in summary["splits"]] == ["train", "validation", "test"]


def test_metrics_schema() -> None:
    metrics = calculate_metrics(pd.Series([0, 0, 1, 1]), np.array([0.1, 0.2, 0.7, 0.8]), 0.5)
    required = {"roc_auc", "average_precision", "precision", "recall", "f1", "threshold", "fraud_prevalence", "alert_rate"}
    assert required.issubset(metrics)


def test_source_columns_are_explicit() -> None:
    assert "isFraud" in REQUIRED_COLUMNS
    assert "isFlaggedFraud" in REQUIRED_COLUMNS

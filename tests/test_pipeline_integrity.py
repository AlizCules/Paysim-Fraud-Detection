from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import data as data_module
from src.data import REQUIRED_COLUMNS, build_time_splits, downsample_training_negatives
from src.evaluation import calculate_metrics
from src.features import FEATURE_SETS, make_feature_frame

ROOT = Path(__file__).resolve().parents[1]


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
    assert "Natural source prevalence" not in summary["splits"][0]["sampling_method"]
    assert "Working-sample prevalence" in summary["splits"][1]["sampling_method"]
    assert "Working-sample prevalence" in summary["splits"][2]["sampling_method"]


def test_raw_holdouts_are_untouched(tmp_path: Path) -> None:
    csv_path = tmp_path / "PS_20174392719_1491204439457_log.csv"
    frame = sample_frame(30)
    frame.to_csv(csv_path, index=False)
    splits, summary = build_time_splits(csv_path, train_end=10, validation_end=20, negative_fraction=0.1)
    original_validation = frame.loc[frame["step"].between(11, 20)]
    original_test = frame.loc[frame["step"] > 20]
    assert len(splits["validation"]) == len(original_validation)
    assert len(splits["test"]) == len(original_test)
    assert "Natural source prevalence" in summary["splits"][1]["sampling_method"]
    assert "Natural source prevalence" in summary["splits"][2]["sampling_method"]


def test_metrics_schema() -> None:
    metrics = calculate_metrics(pd.Series([0, 0, 1, 1]), np.array([0.1, 0.2, 0.7, 0.8]), 0.5)
    required = {"roc_auc", "average_precision", "precision", "recall", "f1", "threshold", "fraud_prevalence", "alert_rate"}
    assert required.issubset(metrics)


def test_source_columns_are_explicit() -> None:
    assert "isFraud" in REQUIRED_COLUMNS
    assert "isFlaggedFraud" in REQUIRED_COLUMNS


def test_missing_default_source_has_explicit_message(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(data_module, "project_root", lambda: tmp_path)
    with pytest.raises(FileNotFoundError, match="PaySim data is not distributed"):
        data_module.resolve_dataset_path()


def test_current_tree_excludes_row_level_exports() -> None:
    assert (ROOT / "data" / "sample" / "README.md").exists()
    assert not (ROOT / "data" / "sample" / "data.csv").exists()
    assert not (ROOT / "results" / "predictions.csv").exists()
    assert not (ROOT / "legacy" / "outputs" / "data_cut_predict_legacy.csv").exists()
    assert not (ROOT / "legacy" / "outputs" / "prediction_output_legacy.csv").exists()


def test_tracked_methodology_artifacts_guard_protocol() -> None:
    thresholds = json.loads((ROOT / "results" / "model_thresholds.json").read_text(encoding="utf-8"))
    selected = json.loads((ROOT / "results" / "selected_model.json").read_text(encoding="utf-8"))
    comparison = pd.read_csv(ROOT / "results" / "model_comparison.csv")
    validation = pd.read_csv(ROOT / "results" / "validation_metrics.csv")
    tradeoffs = pd.read_csv(ROOT / "results" / "threshold_tradeoffs.csv")

    assert thresholds["thresholds_selected_on"] == "validation"
    assert selected["selection_split"] == "validation"
    assert selected["selection_metric"] == "f1"
    assert set(comparison["split"]) == {"test"}
    assert set(validation["split"]) == {"validation"}
    assert set(tradeoffs["split"]) == {"validation"}
    assert "test" not in set(tradeoffs["split"])
    assert {"model", "feature_set", "roc_auc", "average_precision", "precision", "recall", "f1", "threshold", "fraud_prevalence", "alert_rate"}.issubset(validation.columns)
    assert {"model", "feature_set", "split", "roc_auc", "average_precision", "precision", "recall", "f1", "threshold", "fraud_prevalence", "alert_rate"}.issubset(comparison.columns)


def test_readme_and_recruiter_files_are_portfolio_safe() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    summary = json.loads((ROOT / "results" / "data_summary.json").read_text(encoding="utf-8"))
    selected = json.loads((ROOT / "results" / "selected_model.json").read_text(encoding="utf-8"))
    comparison = pd.read_csv(ROOT / "results" / "model_comparison.csv")
    selected_test = comparison.loc[
        (comparison["model"] == selected["model"])
        & (comparison["feature_set"] == selected["feature_set"])
    ].iloc[0]
    assert f"{summary['source_rows']:,}" in readme
    assert f"{summary['source_fraud_rate']:.5%}" in readme
    assert "103,573" in readme
    assert f"{selected_test['f1']:.4f}" in readme
    assert selected["model"].replace("_", " ").title() in readme
    assert "data/sample/data.csv" not in readme
    assert "falls back" not in readme
    assert "not distributed" in readme
    for figure in [
        "fraud_prevalence.png",
        "fraud_by_type.png",
        "model_average_precision.png",
    ]:
        assert (ROOT / "figures" / figure).exists()

    recruiter_files = [ROOT / "README.md", *ROOT.glob("src/**/*.py"), *ROOT.glob("scripts/**/*.py"), *ROOT.glob("docs/**/*.md")]
    forbidden = [
        "C:" + "\\Users",
        "C:/" + "Users/",
        "Pycharm" + "Projects",
        "Down" + "loads",
        "Aliz" + "Culi",
        "tanphuc" + "depchai",
    ]
    for path in recruiter_files:
        text = path.read_text(encoding="utf-8")
        assert not any(marker in text for marker in forbidden), path

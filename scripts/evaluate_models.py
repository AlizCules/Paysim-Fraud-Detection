"""Evaluate frozen canonical models once on the chronological test period."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import build_time_splits, project_root, resolve_dataset_path
from src.evaluation import calculate_metrics
from src.features import FEATURE_SETS, prepare_xy
from src.models import load_model, positive_score

MODEL_NAMES = ["logistic_regression", "random_forest", "xgboost"]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--feature-sets", nargs="+", choices=list(FEATURE_SETS), default=list(FEATURE_SETS))
    parser.add_argument("--train-end", type=int, default=500)
    parser.add_argument("--validation-end", type=int, default=600)
    parser.add_argument("--negative-fraction", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    root = project_root()
    splits, split_summary = build_time_splits(
        resolve_dataset_path(args.source),
        train_end=args.train_end,
        validation_end=args.validation_end,
        negative_fraction=args.negative_fraction,
        random_state=args.seed,
    )
    y_test = None
    thresholds_file = root / "results" / "model_thresholds.json"
    threshold_data = json.loads(thresholds_file.read_text(encoding="utf-8"))
    if threshold_data.get("thresholds_selected_on") != "validation":
        raise RuntimeError("Frozen thresholds must be selected on validation before test evaluation.")
    rows: list[dict] = []

    for feature_set in args.feature_sets:
        X_test, y_test = prepare_xy(splits["test"], feature_set)
        for model_name in MODEL_NAMES:
            key = f"{feature_set}/{model_name}"
            model = load_model(root / "models" / "canonical" / feature_set / f"{model_name}.joblib")
            score = positive_score(model, X_test)
            threshold = float(threshold_data["models"][key]["threshold"])
            metrics = calculate_metrics(y_test, score, threshold)
            row = {"model": model_name, "feature_set": feature_set, "split": "test", **metrics}
            rows.append(row)
            if feature_set == "post_transaction" and model_name == "xgboost":
                pd.DataFrame({"fraud_score": score, "fraud_flag": score >= threshold}).to_csv(
                    root / "results" / "predictions.csv", index=False
                )

    comparison = pd.DataFrame(rows)
    comparison.to_csv(root / "results" / "model_comparison.csv", index=False)
    comparison.to_csv(root / "results" / "feature_set_comparison.csv", index=False)
    (root / "results" / "evaluation_protocol_run.json").write_text(
        json.dumps(
            {
                "test_evaluation": "single final evaluation after validation-only threshold selection",
                "split_summary": split_summary,
                "official_scope": "post_transaction monitoring; pre_transaction comparison included",
                "threshold_tradeoffs_split": "validation",
                "model_selection_split": "validation",
                "feature_importance_source": "validation-selected model from results/selected_model.json",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()

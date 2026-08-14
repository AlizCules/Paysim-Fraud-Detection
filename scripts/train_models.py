"""Train canonical models and select thresholds on validation only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import build_time_splits, project_root, resolve_dataset_path
from src.evaluation import calculate_metrics, select_threshold
from src.features import FEATURE_SETS, prepare_xy
from src.models import build_model, feature_importance, positive_score, save_model

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
    (root / "results").mkdir(parents=True, exist_ok=True)
    (root / "models" / "canonical").mkdir(parents=True, exist_ok=True)
    splits, split_summary = build_time_splits(
        resolve_dataset_path(args.source),
        train_end=args.train_end,
        validation_end=args.validation_end,
        negative_fraction=args.negative_fraction,
        random_state=args.seed,
    )
    thresholds: dict[str, dict] = {}
    validation_rows: list[dict] = []

    for feature_set in args.feature_sets:
        X_train, y_train = prepare_xy(splits["train"], feature_set)
        X_validation, y_validation = prepare_xy(splits["validation"], feature_set)
        for model_name in MODEL_NAMES:
            model = build_model(model_name, X_train, args.seed)
            if model_name == "xgboost":
                positives = max(int(y_train.sum()), 1)
                negatives = max(int((y_train == 0).sum()), 1)
                model.named_steps["model"].set_params(scale_pos_weight=negatives / positives)
            model.fit(X_train, y_train)
            validation_score = positive_score(model, X_validation)
            threshold, selection = select_threshold(y_validation, validation_score)
            metrics = calculate_metrics(y_validation, validation_score, threshold)
            key = f"{feature_set}/{model_name}"
            thresholds[key] = {
                "feature_set": feature_set,
                "model": model_name,
                "threshold": threshold,
                **selection,
            }
            validation_rows.append({"feature_set": feature_set, "model": model_name, **metrics})
            save_model(model, root / "models" / "canonical" / feature_set / f"{model_name}.joblib")
            feature_importance(model, model_name).assign(
                feature_set=feature_set, model=model_name
            ).to_csv(root / "results" / f"feature_importance_{feature_set}_{model_name}.csv", index=False)

    (root / "results" / "model_thresholds.json").write_text(
        json.dumps(
            {
                "thresholds_selected_on": "validation",
                "selection_criterion": "max_f1",
                "models": thresholds,
                "split_summary": split_summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(validation_rows).to_csv(root / "results" / "validation_metrics.csv", index=False)
    print(pd.DataFrame(validation_rows).to_string(index=False))


if __name__ == "__main__":
    main()

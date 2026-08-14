"""Dataset discovery, provenance summaries, and chronological splits."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd

RAW_FILENAME = "PS_20174392719_1491204439457_log.csv"
REQUIRED_COLUMNS = [
    "step",
    "type",
    "amount",
    "nameOrig",
    "oldbalanceOrg",
    "newbalanceOrig",
    "nameDest",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
    "isFlaggedFraud",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_dataset_path(path: str | Path | None = None) -> Path:
    """Resolve an explicitly supplied or locally downloaded PaySim source."""

    if path is not None:
        candidate = Path(path)
        if not candidate.exists():
            raise FileNotFoundError(f"Dataset not found: {candidate}")
        return candidate

    root = project_root()
    candidate = root / "data" / "raw" / RAW_FILENAME
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        "PaySim data is not distributed with this repository. Download a "
        "permitted copy from the documented source and place it under "
        f"data/raw/{RAW_FILENAME}."
    )


def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root()).as_posix()
    except ValueError:
        return path.as_posix()


def summarize_dataset(path: str | Path | None = None, chunksize: int = 500_000) -> dict:
    """Compute provenance and distribution facts without loading the full CSV."""

    dataset_path = resolve_dataset_path(path)
    total_rows = 0
    fraud_rows = 0
    type_counts: Counter[str] = Counter()
    missing_counts: Counter[str] = Counter()
    step_min: int | None = None
    step_max: int | None = None
    amount_min: float | None = None
    amount_max: float | None = None

    for chunk in pd.read_csv(dataset_path, usecols=REQUIRED_COLUMNS, chunksize=chunksize):
        total_rows += len(chunk)
        fraud_rows += int(chunk["isFraud"].sum())
        type_counts.update(chunk["type"].astype(str))
        for column, value in chunk.isna().sum().items():
            if int(value):
                missing_counts[column] += int(value)
        chunk_step_min = int(chunk["step"].min())
        chunk_step_max = int(chunk["step"].max())
        step_min = chunk_step_min if step_min is None else min(step_min, chunk_step_min)
        step_max = chunk_step_max if step_max is None else max(step_max, chunk_step_max)
        chunk_amount_min = float(chunk["amount"].min())
        chunk_amount_max = float(chunk["amount"].max())
        amount_min = chunk_amount_min if amount_min is None else min(amount_min, chunk_amount_min)
        amount_max = chunk_amount_max if amount_max is None else max(amount_max, chunk_amount_max)

    nonfraud_rows = total_rows - fraud_rows
    is_raw = dataset_path.name == RAW_FILENAME
    return {
        "source_dataset": "PaySim raw source" if is_raw else "tracked working sample",
        "source_path": _relative_to_root(dataset_path),
        "source_rows": total_rows,
        "source_fraud_rows": fraud_rows,
        "source_nonfraud_rows": nonfraud_rows,
        "source_fraud_rate": fraud_rows / total_rows if total_rows else None,
        "type_counts": dict(sorted(type_counts.items())),
        "missing_counts": dict(sorted(missing_counts.items())),
        "time_min": step_min,
        "time_max": step_max,
        "amount_min": amount_min,
        "amount_max": amount_max,
        "raw_source_available": is_raw,
        "sampling_method": (
            "Full PaySim source; no source-level row sampling."
            if is_raw
            else "Tracked working sample; source-level prevalence is not represented."
        ),
    }


def _read_windows(
    path: Path,
    train_end: int,
    validation_end: int,
    chunksize: int = 500_000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_parts: list[pd.DataFrame] = []
    validation_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=REQUIRED_COLUMNS, chunksize=chunksize):
        train_parts.append(chunk.loc[chunk["step"] <= train_end])
        validation_parts.append(
            chunk.loc[(chunk["step"] > train_end) & (chunk["step"] <= validation_end)]
        )
        test_parts.append(chunk.loc[chunk["step"] > validation_end])

    def combine(parts: Iterable[pd.DataFrame]) -> pd.DataFrame:
        nonempty = [part for part in parts if not part.empty]
        if not nonempty:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)
        return pd.concat(nonempty, ignore_index=True)

    return combine(train_parts), combine(validation_parts), combine(test_parts)


def downsample_training_negatives(
    frame: pd.DataFrame,
    negative_fraction: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """Keep all fraud and sample only negatives for training."""

    if not 0 < negative_fraction <= 1:
        raise ValueError("negative_fraction must be in (0, 1].")
    fraud = frame.loc[frame["isFraud"].eq(1)]
    nonfraud = frame.loc[frame["isFraud"].eq(0)]
    n_negative = max(1, int(round(len(nonfraud) * negative_fraction))) if len(nonfraud) else 0
    sampled_nonfraud = nonfraud.sample(n=n_negative, random_state=random_state) if n_negative else nonfraud
    return pd.concat([fraud, sampled_nonfraud], ignore_index=True).sample(
        frac=1, random_state=random_state
    ).reset_index(drop=True)


def summarize_frame(frame: pd.DataFrame, split: str, sampling_method: str) -> dict:
    rows = len(frame)
    fraud = int(frame["isFraud"].sum())
    return {
        "split": split,
        "rows": rows,
        "fraud": fraud,
        "non_fraud": rows - fraud,
        "fraud_rate": fraud / rows if rows else None,
        "min_step": int(frame["step"].min()) if rows else None,
        "max_step": int(frame["step"].max()) if rows else None,
        "sampling_method": sampling_method,
    }


def build_time_splits(
    path: str | Path | None = None,
    train_end: int = 500,
    validation_end: int = 600,
    negative_fraction: float = 0.05,
    random_state: int = 42,
) -> tuple[dict[str, pd.DataFrame], dict]:
    """Build train/validation/test periods without random shuffling across time."""

    dataset_path = resolve_dataset_path(path)
    train, validation, test = _read_windows(dataset_path, train_end, validation_end)
    raw_source = dataset_path.name == RAW_FILENAME
    if raw_source:
        train = downsample_training_negatives(train, negative_fraction, random_state)
        train_sampling = f"All fraud + {negative_fraction:.2%} of train-period non-fraud, seed={random_state}."
        holdout_sampling = "Natural source prevalence; untouched for model selection/evaluation."
    else:
        train_sampling = "Tracked working sample; no additional negative sampling."
        holdout_sampling = "Working-sample prevalence; natural source prevalence is unavailable."

    split_summary = {
        "source_path": _relative_to_root(dataset_path),
        "train_end_step": train_end,
        "validation_end_step": validation_end,
        "source_raw_available": raw_source,
        "threshold_selection_split": "validation",
        "final_evaluation_split": "test",
        "splits": [
            summarize_frame(train, "train", train_sampling),
            summarize_frame(validation, "validation", holdout_sampling),
            summarize_frame(test, "test", holdout_sampling),
        ],
    }
    return {"train": train, "validation": validation, "test": test}, split_summary

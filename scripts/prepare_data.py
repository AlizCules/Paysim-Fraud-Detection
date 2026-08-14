"""Prepare verified data and chronological split metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import build_time_splits, project_root, resolve_dataset_path, summarize_dataset


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--train-end", type=int, default=500)
    parser.add_argument("--validation-end", type=int, default=600)
    parser.add_argument("--negative-fraction", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    root = project_root()
    output_dir = root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = resolve_dataset_path(args.source)
    source_summary = summarize_dataset(source_path)

    _, split_summary = build_time_splits(
        source_path,
        train_end=args.train_end,
        validation_end=args.validation_end,
        negative_fraction=args.negative_fraction,
        random_state=args.seed,
    )
    canonical = {
        **source_summary,
        "working_path": source_summary["source_path"],
        "working_rows": source_summary["source_rows"],
        "working_fraud_rows": source_summary["source_fraud_rows"],
        "working_nonfraud_rows": source_summary["source_nonfraud_rows"],
        "working_fraud_rate": source_summary["source_fraud_rate"],
        "working_sampling_method": "No tracked working sample; raw source used directly.",
        "split_definition": split_summary,
    }
    (output_dir / "data_summary.json").write_text(
        json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    pd.DataFrame(split_summary["splits"]).to_csv(output_dir / "split_summary.csv", index=False)
    print(json.dumps(canonical, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

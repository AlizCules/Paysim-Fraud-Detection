"""Score new transactions with a canonical model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import project_root
from src.features import prepare_xy
from src.models import load_model, positive_score


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--feature-set", choices=["pre_transaction", "post_transaction"], default="post_transaction")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    frame = pd.read_csv(args.input)
    features, _ = prepare_xy(frame.assign(isFraud=0), args.feature_set)
    model = load_model(args.model)
    score = positive_score(model, features)
    output = pd.DataFrame({"fraud_score": score, "fraud_flag": score >= args.threshold})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(f"Wrote {len(output):,} predictions to {args.output}")


if __name__ == "__main__":
    main()

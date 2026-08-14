"""Generate compact recruiter-facing analytical figures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import project_root, resolve_dataset_path

sns.set_theme(style="whitegrid", context="notebook")


def _source_aggregates(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    type_parts = []
    hour_parts = []
    for chunk in pd.read_csv(path, usecols=["step", "type", "amount", "isFraud"], chunksize=500_000):
        chunk["hour"] = chunk["step"] % 24
        type_parts.append(chunk.groupby("type").agg(transactions=("isFraud", "size"), fraud=("isFraud", "sum"), fraud_amount=("amount", lambda x: float(x[chunk.loc[x.index, "isFraud"].eq(1)].sum()))).reset_index())
        hour_parts.append(chunk.groupby("hour").agg(transactions=("isFraud", "size"), fraud=("isFraud", "sum")).reset_index())
    by_type = pd.concat(type_parts).groupby("type", as_index=False).sum(numeric_only=True)
    by_hour = pd.concat(hour_parts).groupby("hour", as_index=False).sum(numeric_only=True)
    by_type["fraud_rate"] = by_type["fraud"] / by_type["transactions"]
    by_hour["fraud_rate"] = by_hour["fraud"] / by_hour["transactions"]
    return by_type, by_hour


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=None)
    args = parser.parse_args(argv)
    root = project_root()
    figure_dir = root / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    source_path = resolve_dataset_path(args.source)
    summary = json.loads((root / "results" / "data_summary.json").read_text(encoding="utf-8"))
    by_type, by_hour = _source_aggregates(source_path)

    prevalence = pd.DataFrame({"dataset": ["Source", "Working sample"], "fraud_rate": [summary["source_fraud_rate"], summary["working_fraud_rate"]]})
    ax = sns.barplot(data=prevalence, x="dataset", y="fraud_rate", color="#1f77b4")
    ax.set(title="Fraud prevalence: source vs working sample", ylabel="Fraud rate", xlabel="")
    ax.set_yscale("log")
    ax.set_ylabel("Fraud rate (log scale)")
    plt.tight_layout(); plt.savefig(figure_dir / "fraud_prevalence.png", dpi=180); plt.close()

    ax = sns.barplot(data=by_type.sort_values("fraud_rate", ascending=False), x="type", y="fraud_rate", color="#d95f02")
    ax.set(title="Fraud rate by transaction type in PaySim", ylabel="Fraud rate", xlabel="Transaction type")
    ax.tick_params(axis="x", rotation=20)
    plt.tight_layout(); plt.savefig(figure_dir / "fraud_by_type.png", dpi=180); plt.close()

    ax = sns.lineplot(data=by_hour, x="hour", y="fraud_rate", marker="o", color="#1b9e77")
    ax.set(title="Fraud rate by hour of simulated time", ylabel="Fraud rate", xlabel="Hour")
    plt.tight_layout(); plt.savefig(figure_dir / "fraud_by_hour.png", dpi=180); plt.close()

    sample_path = root / "data" / "sample" / "data.csv"
    sample = pd.read_csv(sample_path if sample_path.exists() else source_path, usecols=["amount", "isFraud"])
    sample["log_amount"] = (sample["amount"].clip(lower=0) + 1).map(lambda x: __import__("math").log10(x))
    ax = sns.histplot(data=sample, x="log_amount", hue="isFraud", bins=50, stat="density", common_norm=False, element="step")
    ax.set(title="Transaction amount distribution (working sample)", xlabel="log10(amount + 1)", ylabel="Density")
    plt.tight_layout(); plt.savefig(figure_dir / "amount_distribution.png", dpi=180); plt.close()

    comparison_path = root / "results" / "model_comparison.csv"
    if comparison_path.exists():
        comparison = pd.read_csv(comparison_path)
        plot_data = comparison.assign(label=comparison["model"].str.replace("_", " ").str.title() + "\n" + comparison["feature_set"].str.replace("_", " ").str.title())
        ax = sns.barplot(data=plot_data, x="average_precision", y="label", color="#7570b3")
        ax.set(title="Average precision on the chronological test period", xlabel="Average precision", ylabel="")
        plt.tight_layout(); plt.savefig(figure_dir / "model_average_precision.png", dpi=180); plt.close()

    print(f"Generated figures in {figure_dir}")


if __name__ == "__main__":
    main()

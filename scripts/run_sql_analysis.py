"""Run reproducible DuckDB analysis queries and export aggregate CSVs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import project_root, resolve_dataset_path


def _queries(sql_text: str) -> list[tuple[str, str]]:
    blocks = re.split(r"--\s*query:\s*([a-zA-Z0-9_]+)\s*\n", sql_text)
    return [(blocks[i], blocks[i + 1].strip()) for i in range(1, len(blocks), 2)]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=None)
    args = parser.parse_args(argv)
    root = project_root()
    source_path = resolve_dataset_path(args.source)
    output_dir = root / "results" / "sql"
    output_dir.mkdir(parents=True, exist_ok=True)
    escaped = source_path.resolve().as_posix().replace("'", "''")

    connection = duckdb.connect()
    connection.execute(f"CREATE VIEW transactions AS SELECT * FROM read_csv_auto('{escaped}', header=true)")
    sql_text = (root / "sql" / "fraud_analysis.sql").read_text(encoding="utf-8")
    completed = []
    for name, query in _queries(sql_text):
        if name == "alert_volume" and not (root / "results" / "predictions.csv").exists():
            continue
        if name == "alert_volume":
            prediction_path = (root / "results" / "predictions.csv").resolve().as_posix().replace("'", "''")
            connection.execute(f"CREATE OR REPLACE VIEW predictions AS SELECT * FROM read_csv_auto('{prediction_path}', header=true)")
        frame = connection.execute(query).df()
        frame.to_csv(output_dir / f"{name}.csv", index=False)
        completed.append(name)
    connection.close()
    print("Exported: " + ", ".join(completed))


if __name__ == "__main__":
    main()

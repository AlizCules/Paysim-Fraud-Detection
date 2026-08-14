"""Run the reproducible PaySim analysis stages."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


STAGES = {
    "prepare": "prepare_data.py",
    "train": "train_models.py",
    "evaluate": "evaluate_models.py",
    "figures": "generate_figures.py",
    "sql": "run_sql_analysis.py",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=[*STAGES, "all"])
    args, extra = parser.parse_known_args()
    root = Path(__file__).resolve().parent
    stages = list(STAGES) if args.stage == "all" else [args.stage]
    for stage in stages:
        subprocess.run([sys.executable, str(root / "scripts" / STAGES[stage]), *extra], check=True, cwd=root)


if __name__ == "__main__":
    main()

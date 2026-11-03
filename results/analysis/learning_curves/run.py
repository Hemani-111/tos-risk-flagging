"""Runnable entry point for group-aware learning curves analysis."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def _run_shared(protocol: str) -> None:
    rf = ROOT / "results" / "experiments"
    if not (rf / f"remaining_features_{protocol}_v1").exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_remaining_feature_experiments.py"),
             "--protocol", protocol], check=True)


def _export(protocol: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    src = ROOT / "results" / "experiments" / f"remaining_features_{protocol}_v1" / "group_learning_curves.csv"
    if src.exists():
        shutil.copy2(src, dest / "group_learning_curves.csv")
        print(f"  copied remaining_features_{protocol}_v1/group_learning_curves.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Learning curves analysis entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        _run_shared(protocol)
        dest = ROOT / "results" / "analysis" / "learning_curves" / protocol
        print(f"[{protocol}] Exporting learning curve outputs to {dest}")
        _export(protocol, dest)

        if args.smoke:
            df = pd.read_csv(dest / "group_learning_curves.csv")
            print(f"  representations: {sorted(df['representation'].unique())}")
            print(f"  fractions: {sorted(df['fraction_groups'].unique())}")
            full = df[(df["fraction_groups"] == 1.0) & (df["repeat"] == 0)]
            if not full.empty:
                for _, row in full.iterrows():
                    print(f"  {row['representation']} at 1.0: macro_f1={row['macro_f1']:.4f}, train_rows={row['train_rows']}")

    print("Done. See results/analysis/learning_curves/README.md")


if __name__ == "__main__":
    main()

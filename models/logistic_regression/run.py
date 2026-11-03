"""Thin entry point for the Logistic Regression experiment.

Routes through the canonical eight-method comparison script
(scripts/run_comparison.py), which supports Logistic Regression with sparse
word unigram/bigram TF-IDF and bounded group-respecting CV. Running this entry
point trains all eight methods; Logistic Regression artifacts are saved
alongside the others.

This is development-only. It does not touch the locked test partition and does
not change the deployed production model (models/releases/linear-svc-primary-v2/).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SEED = 20261102


def main() -> None:
    parser = argparse.ArgumentParser(description="Logistic Regression experiment entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true",
                        help="Run a subset for fast verification")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        cmd = [sys.executable, str(ROOT / "scripts" / "run_comparison.py"),
               "--protocol", protocol]
        print(f"[{protocol}] Running canonical comparison: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"[{protocol}] Logistic Regression artifacts saved under "
              f"models/logistic_regression/artifacts/{protocol}/")

    print("Done. See models/logistic_regression/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

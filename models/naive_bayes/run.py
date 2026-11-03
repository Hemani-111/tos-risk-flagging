"""Thin entry point for the Multinomial Naive Bayes experiment.

Routes through the canonical eight-method comparison script
(scripts/run_comparison.py), which supports Multinomial NB with sparse word
unigram/bigram TF-IDF and bounded group-respecting CV. Running this entry
point trains all eight methods; Naive Bayes artifacts are saved alongside
the others.

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
    parser = argparse.ArgumentParser(description="Naive Bayes experiment entry point")
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
        print(f"[{protocol}] Naive Bayes artifacts saved under "
              f"models/naive_bayes/artifacts/{protocol}/")

    print("Done. See models/naive_bayes/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

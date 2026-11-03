"""Runnable entry point for feature combination / ablation analysis.

Exports canonical word+character and lexical ablation outputs into this
analysis folder for discoverable access.
"""

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
    # Ensure shared experiments have been executed
    for script in ("scripts/run_remaining_feature_experiments.py",
                   "scripts/run_lexical_feature_ablation.py"):
        sp = ROOT / script
        if sp.exists() and not (ROOT / "results" / "experiments" / f"remaining_features_{protocol}_v1").exists():
            subprocess.run([sys.executable, str(sp), "--protocol", protocol], check=True)


def _export(protocol: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    rf = ROOT / "results" / "experiments"
    copies = {
        "primary": {
            f"remaining_features_{protocol}_v1": ["word_char_validation.csv", "word_char_group_cv.csv"],
            f"lexical_ablation_{protocol}_v1": ["cv_summary.csv", "cv_fold_metrics.csv"],
        },
        "clause": {
            f"remaining_features_{protocol}_v1": ["word_char_validation.csv", "word_char_group_cv.csv"],
            f"lexical_ablation_{protocol}_v1": ["cv_summary.csv", "cv_fold_metrics.csv"],
        },
    }[protocol]
    for src_dir, files in copies.items():
        for fname in files:
            src = rf / src_dir / fname
            if src.exists():
                shutil.copy2(src, dest / fname)
                print(f"  copied {src_dir}/{fname}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Feature combinations analysis entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        _run_shared(protocol)
        dest = ROOT / "results" / "analysis" / "feature_combinations" / protocol
        print(f"[{protocol}] Exporting feature combination outputs to {dest}")
        _export(protocol, dest)

        if args.smoke:
            df = pd.read_csv(dest / "word_char_validation.csv")
            print(f"  word_char validation rows: {len(df)}")

    print("Done. See results/analysis/feature_combinations/README.md")


if __name__ == "__main__":
    main()

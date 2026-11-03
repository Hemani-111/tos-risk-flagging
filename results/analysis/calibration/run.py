"""Runnable entry point for calibration analysis."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def _run_shared(protocol: str) -> None:
    rf = ROOT / "results" / "experiments"
    if not (rf / f"ensemble_calibration_{protocol}_v1").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_ensemble_calibration_clusters.py")],
                       check=True)


def _export(protocol: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    src_dir = ROOT / "results" / "experiments" / f"ensemble_calibration_{protocol}_v1"
    for fname in ("calibration_validation.json", "calibration_validation_probabilities.csv",
                  "risky_probability_reliability.csv", "soft_vote_validation_probabilities.csv"):
        src = src_dir / fname
        if src.exists():
            shutil.copy2(src, dest / fname)
            print(f"  copied {src_dir.name}/{fname}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibration analysis entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        _run_shared(protocol)
        dest = ROOT / "results" / "analysis" / "calibration" / protocol
        print(f"[{protocol}] Exporting calibration outputs to {dest}")
        _export(protocol, dest)

        if args.smoke:
            import json
            cal = json.loads((dest / "calibration_validation.json").read_text(encoding="utf-8"))
            print(f"  validation_macro_f1: {cal['validation_macro_f1']:.4f}")
            print(f"  risky_precision: {cal['risky_precision']:.4f}")
            print(f"  risky_recall: {cal['risky_recall']:.4f}")
            print(f"  brier_score: {cal['multiclass_brier_score']:.4f}")

    print("Done. See results/analysis/calibration/README.md")


if __name__ == "__main__":
    main()

"""Thin entry point for the Stacking Ensemble experiment.

Calls the shared ensemble/calibration script and extracts stacking-ensemble
specific results (LR meta-model on OOF margins).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _run_shared_ensemble(protocol: str) -> Path:
    out = ROOT / "results" / "experiments" / f"ensemble_calibration_{protocol}_v1"
    if not out.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_ensemble_calibration_clusters.py")],
                       check=True)
    return out


def _export_stacking_rows(protocol: str, source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("validation_ensemble_metrics.csv", "validation_ensemble_predictions.csv",
                 "oof_stacking_features.csv", "run_metadata.json"):
        src = source / name
        if src.exists():
            shutil.copy2(src, dest / name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stacking Ensemble entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        source = _run_shared_ensemble(protocol)
        dest = ROOT / "models" / "stacking_ensemble" / "results" / protocol
        _export_stacking_rows(protocol, source, dest)
        print(f"[{protocol}] Stacking ensemble results exported to {dest}")

        if args.smoke:
            import pandas as pd
            metrics_path = dest / "validation_ensemble_metrics.csv"
            df = pd.read_csv(metrics_path)
            row = df[df["model"].eq("stacking_logistic_meta")]
            if not row.empty:
                print(f"[{protocol}] SMOKE: stacking_logistic_meta validation macro_f1 = {row.iloc[0]['macro_f1']:.4f}")

    print("Done. See models/stacking_ensemble/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

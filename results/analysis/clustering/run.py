"""Runnable entry point for K-means clustering analysis."""

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
    if not (rf / f"ensemble_calibration_{protocol}_v1").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "run_ensemble_calibration_clusters.py")],
                       check=True)


def _export(protocol: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    rf = ROOT / "results" / "experiments"
    copies = {
        "primary": {
            f"ensemble_calibration_{protocol}_v1": ["kmeans_cluster_summary.csv", "kmeans_train_assignments.csv", "pca_train_coordinates.csv"],
        },
        "clause": {
            f"ensemble_calibration_{protocol}_v1": ["kmeans_cluster_summary.csv", "kmeans_train_assignments.csv", "pca_train_coordinates.csv"],
        },
    }[protocol]
    for src_dir, files in copies.items():
        for fname in files:
            src = rf / src_dir / fname
            if src.exists():
                shutil.copy2(src, dest / fname)
                print(f"  copied {src_dir}/{fname}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clustering analysis entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        _run_shared(protocol)
        dest = ROOT / "results" / "analysis" / "clustering" / protocol
        print(f"[{protocol}] Exporting clustering outputs to {dest}")
        _export(protocol, dest)

        if args.smoke:
            df = pd.read_csv(dest / "kmeans_cluster_summary.csv")
            print(f"  k values: {sorted(df['k'].unique())}")
            print(f"  silhouette range: {df['sampled_cosine_silhouette'].min():.3f} - {df['sampled_cosine_silhouette'].max():.3f}")

    print("Done. See results/analysis/clustering/README.md")


if __name__ == "__main__":
    main()

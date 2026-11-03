"""Runnable entry point for dimensionality reduction analysis (PCA on embeddings, Truncated SVD context)."""

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
    rf = ROOT / "results" / "experiments"
    copies = {
        "primary": {
            f"remaining_features_{protocol}_v1": ["embedding_group_cv.csv", "embedding_group_cv_summary.csv", "embedding_selected_validation.csv"],
        },
        "clause": {
            f"remaining_features_{protocol}_v1": ["embedding_group_cv.csv", "embedding_group_cv_summary.csv", "embedding_selected_validation.csv"],
        },
    }[protocol]
    for src_dir, files in copies.items():
        for fname in files:
            src = rf / src_dir / fname
            if src.exists():
                shutil.copy2(src, dest / fname)
                print(f"  copied {src_dir}/{fname}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dimensionality reduction analysis entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        _run_shared(protocol)
        dest = ROOT / "results" / "analysis" / "dimensionality_reduction" / protocol
        print(f"[{protocol}] Exporting dimensionality reduction outputs to {dest}")
        _export(protocol, dest)

        if args.smoke:
            df = pd.read_csv(dest / "embedding_group_cv_summary.csv")
            pca_rows = df[df["pca_components"].notna()]
            raw_rows = df[df["pca_components"].isna()]
            print(f"  PCA rows: {len(pca_rows)}, Raw (no PCA) rows: {len(raw_rows)}")
            if not raw_rows.empty:
                print(f"  Best raw macro F1: {raw_rows['cv_macro_f1_mean'].max():.4f}")
            if not pca_rows.empty:
                print(f"  Best PCA macro F1: {pca_rows['cv_macro_f1_mean'].max():.4f}")

    print("Done. See results/analysis/dimensionality_reduction/README.md")


if __name__ == "__main__":
    main()

"""Thin entry point for the Gradient Boosting (HistGradientBoosting) experiment."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102
SVD_COMPONENTS = 100

CONFIG = {
    "max_iter": 200,
    "learning_rate": 0.1,
    "max_leaf_nodes": 31,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": SEED,
}


def _run_shared_tuning(protocol: str) -> Path:
    out = ROOT / "results" / "experiments" / f"expanded_classical_{protocol}_v1"
    if not out.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_expanded_classical_tuning.py"),
             "--protocol", protocol],
            check=True,
        )
    return out


def _export_gradient_boosting_rows(protocol: str, source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("validation_selected_family_metrics.csv",
                 "validation_selected_family_predictions.csv",
                 "hist_gradient_boosting_validation_confusion.csv",
                 "cv_summary.csv", "cv_fold_metrics.csv", "run_metadata.json"):
        src = source / name
        if src.exists():
            shutil.copy2(src, dest / name)


def _save_artifact(protocol: str) -> Path:
    data, split_meta = load_development_bundle(protocol, ROOT)
    part, include = f"{protocol}_partition", f"{protocol}_include"
    train = data.loc[data[include] & data[part].eq("train")].copy().reset_index(drop=True)
    texts = train["quote_text"].fillna("").astype(str).tolist()
    y = train["label"].to_numpy()

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99,
                                 max_features=60000, sublinear_tf=True,
                                 strip_accents="unicode", dtype=np.float32)
    X = vectorizer.fit_transform(texts)
    svd = TruncatedSVD(n_components=SVD_COMPONENTS, n_iter=5, random_state=SEED)
    Z = svd.fit_transform(X).astype(np.float32, copy=False)

    model = HistGradientBoostingClassifier(**CONFIG)
    model.fit(Z, y)

    artifact_dir = ROOT / "models" / "gradient_boosting" / "artifacts" / protocol
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, artifact_dir / "vectorizer.joblib")
    joblib.dump(svd, artifact_dir / "svd.joblib")
    joblib.dump(model, artifact_dir / "model.joblib")
    meta = {
        "method": "gradient_boosting",
        "protocol": protocol,
        "seed": SEED,
        "config": CONFIG,
        "svd_components": SVD_COMPONENTS,
        "train_rows": len(train),
        "created_at_utc": datetime.now(timezone).isoformat(),
        "dataset_sha256": split_meta["dataset_sha256"],
        "split_id": split_meta["split_id"],
        "locked_test_used": False,
        "development_only": True,
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return artifact_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Gradient Boosting experiment entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        source = _run_shared_tuning(protocol)
        dest = ROOT / "models" / "gradient_boosting" / "results" / protocol
        _export_gradient_boosting_rows(protocol, source, dest)
        print(f"[{protocol}] Gradient Boosting results exported to {dest}")

        if args.save_artifact:
            artifact_dir = _save_artifact(protocol)
            print(f"[{protocol}] Fitted artifact saved to {artifact_dir}")

        if args.smoke:
            metrics_path = dest / "validation_selected_family_metrics.csv"
            df = pd.read_csv(metrics_path)
            row = df[df["family"].eq("hist_gradient_boosting")]
            if not row.empty:
                print(f"[{protocol}] SMOKE: hist_gradient_boosting validation macro_f1 = {row.iloc[0]['cv_macro_f1_mean']:.4f}")

    print("Done. See models/gradient_boosting/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

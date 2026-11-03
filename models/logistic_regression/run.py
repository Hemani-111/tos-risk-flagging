"""Thin entry point for the Logistic Regression experiment.

Calls the shared bounded group-CV tuning script and exposes logistic-regression-specific
results. Optionally persists a fitted development model/vectorizer pipeline.
"""

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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102

CONFIG = {
    "C": 1.0,
    "max_iter": 3000,
    "class_weight": None,
    "solver": "lbfgs",
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


def _export_logistic_regression_rows(protocol: str, source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("validation_selected_family_metrics.csv",
                 "validation_selected_family_predictions.csv",
                 "logistic_regression_validation_confusion.csv",
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

    model = LogisticRegression(**CONFIG)
    model.fit(X, y)

    artifact_dir = ROOT / "models" / "logistic_regression" / "artifacts" / protocol
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, artifact_dir / "vectorizer.joblib")
    joblib.dump(model, artifact_dir / "model.joblib")
    meta = {
        "method": "logistic_regression",
        "protocol": protocol,
        "seed": SEED,
        "config": CONFIG,
        "train_rows": len(train),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": split_meta["dataset_sha256"],
        "split_id": split_meta["split_id"],
        "locked_test_used": False,
        "development_only": True,
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return artifact_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Logistic Regression experiment entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true",
                        help="Run a single-fold smoke check instead of full tuning")
    parser.add_argument("--save-artifact", action="store_true",
                        help="Persist a fitted development model pipeline to artifacts/")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        source = _run_shared_tuning(protocol)
        dest = ROOT / "models" / "logistic_regression" / "results" / protocol
        _export_logistic_regression_rows(protocol, source, dest)
        print(f"[{protocol}] Logistic Regression results exported to {dest}")

        if args.save_artifact:
            artifact_dir = _save_artifact(protocol)
            print(f"[{protocol}] Fitted artifact saved to {artifact_dir}")

        if args.smoke:
            metrics_path = dest / "validation_selected_family_metrics.csv"
            df = pd.read_csv(metrics_path)
            row = df[df["family"].eq("logistic_regression")]
            if not row.empty:
                print(f"[{protocol}] SMOKE: logistic_regression validation macro_f1 = {row.iloc[0]['cv_macro_f1_mean']:.4f}")

    print("Done. See models/logistic_regression/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

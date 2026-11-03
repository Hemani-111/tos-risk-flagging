"""Thin entry point for the Complement Naive Bayes experiment.

Calls the shared first-pass benchmark script (scripts/run_model_benchmarks.py)
and exposes Complement NB-specific results. Optionally persists a fitted
development vectorizer/model pipeline.
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
from sklearn.naive_bayes import ComplementNB

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102

CONFIG = {"alpha": 0.1, "fit_prior": True, "force_alpha": True}


def _run_shared_benchmark(protocol: str) -> Path:
    out = ROOT / "results" / "experiments" / f"benchmark_{protocol}_wordtfidf_v1"
    if not out.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_model_benchmarks.py"),
             "--protocol", protocol],
            check=True,
        )
    return out


def _export_cnb_rows(protocol: str, source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("validation_metrics.csv", "validation_predictions.csv",
                 "complement_nb_confusion.csv", "run_metadata.json"):
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

    model = ComplementNB(**CONFIG)
    model.fit(X, y)

    artifact_dir = ROOT / "models" / "complement_naive_bayes" / "artifacts" / protocol
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, artifact_dir / "vectorizer.joblib")
    joblib.dump(model, artifact_dir / "model.joblib")
    meta = {
        "method": "complement_naive_bayes",
        "protocol": protocol,
        "seed": SEED,
        "config": CONFIG,
        "train_rows": len(train),
        "created_at_utc": datetime.now(timezone).isoformat(),
        "dataset_sha256": split_meta["dataset_sha256"],
        "split_id": split_meta["split_id"],
        "locked_test_used": False,
        "development_only": True,
        "note": "First-pass benchmark; no bounded group-CV tuning.",
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return artifact_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Complement Naive Bayes entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        source = _run_shared_benchmark(protocol)
        dest = ROOT / "models" / "complement_naive_bayes" / "results" / protocol
        _export_cnb_rows(protocol, source, dest)
        print(f"[{protocol}] Complement NB results exported to {dest}")

        if args.save_artifact:
            artifact_dir = _save_artifact(protocol)
            print(f"[{protocol}] Fitted artifact saved to {artifact_dir}")

        if args.smoke:
            metrics_path = dest / "validation_metrics.csv"
            df = pd.read_csv(metrics_path)
            row = df[df["model"].eq("complement_nb")]
            if not row.empty:
                print(f"[{protocol}] SMOKE: complement_nb validation macro_f1 = {row.iloc[0]['macro_f1']:.4f}")

    print("Done. See models/complement_naive_bayes/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

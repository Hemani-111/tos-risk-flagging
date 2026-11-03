"""Thin entry point for the Sentence Embeddings + Linear SVM experiment.

Calls the shared remaining-feature experiments script and extracts the
Linear SVM embedding results. Optionally persists a fitted development
classifier on cached MiniLM embeddings.
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
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102
ENCODER_NAME = "sentence-transformers/all-MiniLM-L6-v2"
ENCODER_REVISION = "b9db1e8a0d3a51769172ba8546f282a73f066e47"
ENCODER_LICENSE = "Apache-2.0"
ENCODER_DIMS = 384
ENCODER_MAX_INPUT = "256 wordpieces"

CONFIG = {"C": 1.0, "class_weight": "balanced", "random_state": SEED, "max_iter": 5000}


def _load_cached_embeddings() -> tuple[dict[int, np.ndarray], dict]:
    cache_dir = ROOT / "data" / "cache" / "embeddings"
    for meta_path in sorted(cache_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("capped_run") or meta.get("locked_test_used"):
            continue
        npz_path = meta_path.with_suffix(".npz")
        if not npz_path.exists():
            continue
        packed = np.load(npz_path)
        ids = packed["point_ids"].astype(np.int64)
        vecs = packed["embeddings"].astype(np.float32)
        if len(ids) != len(vecs) or not np.isfinite(vecs).all():
            continue
        return dict(zip(ids.tolist(), vecs)), meta
    raise FileNotFoundError("Full development-only embedding cache not found in data/cache/embeddings/")


def _run_shared_features(protocol: str) -> Path:
    out = ROOT / "results" / "experiments" / f"remaining_features_{protocol}_v1"
    if not out.exists():
        vectors, _ = _load_cached_embeddings()
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_remaining_feature_experiments.py")],
            check=True,
        )
    return out


def _export_embedding_svm_rows(protocol: str, source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("embedding_selected_validation.csv", "embedding_group_cv_summary.csv",
                 "embedding_group_cv.csv", "embedding_selected_validation_predictions.csv",
                 "run_metadata.json"):
        src = source / name
        if src.exists():
            shutil.copy2(src, dest / name)


def _save_artifact(protocol: str) -> Path:
    data, split_meta = load_development_bundle(protocol, ROOT)
    part, include = f"{protocol}_partition", f"{protocol}_include"
    train = data.loc[data[include] & data[part].eq("train")].copy().reset_index(drop=True)
    vectors, _ = _load_cached_embeddings()

    ids = train.point_id.astype(int).to_numpy()
    X = np.stack([vectors[int(i)] for i in ids])
    y = train.label.to_numpy()

    model = LinearSVC(**CONFIG)
    model.fit(X, y)

    artifact_dir = ROOT / "models" / "sentence_embeddings_linear_svm" / "artifacts" / protocol
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_dir / "model.joblib")
    meta = {
        "method": "sentence_embeddings_linear_svm",
        "protocol": protocol,
        "encoder": ENCODER_NAME,
        "encoder_revision": ENCODER_REVISION,
        "encoder_license": ENCODER_LICENSE,
        "encoder_dimensions": ENCODER_DIMS,
        "encoder_max_input": ENCODER_MAX_INPUT,
        "seed": SEED,
        "config": CONFIG,
        "pca_components": None,
        "train_rows": len(train),
        "created_at_utc": datetime.now(timezone).isoformat(),
        "dataset_sha256": split_meta["dataset_sha256"],
        "split_id": split_meta["split_id"],
        "locked_test_used": False,
        "development_only": True,
        "note": "Encoder weights not saved; cached embeddings are in data/cache/embeddings/ (Git-ignored).",
    }
    (artifact_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return artifact_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentence Embeddings + Linear SVM entry point")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--save-artifact", action="store_true")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)

    for protocol in protocols:
        source = _run_shared_features(protocol)
        dest = ROOT / "models" / "sentence_embeddings_linear_svm" / "results" / protocol
        _export_embedding_svm_rows(protocol, source, dest)
        print(f"[{protocol}] Embedding+LinearSVM results exported to {dest}")

        if args.save_artifact:
            artifact_dir = _save_artifact(protocol)
            print(f"[{protocol}] Fitted artifact saved to {artifact_dir}")

        if args.smoke:
            metrics_path = dest / "embedding_selected_validation.csv"
            df = pd.read_csv(metrics_path)
            row = df[df["family"].eq("linear_svc")]
            if not row.empty:
                print(f"[{protocol}] SMOKE: embedding+LinearSVM validation macro_f1 = {row.iloc[0]['macro_f1']:.4f}")

    print("Done. See models/sentence_embeddings_linear_svm/README.md for full results and interpretation.")


if __name__ == "__main__":
    main()

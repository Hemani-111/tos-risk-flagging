"""Run first-pass classical text model comparisons on a frozen protocol.

Models fit on the manifest's training partition and are scored on validation.
The locked test partition is never selected or transformed by this command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.decomposition import TruncatedSVD
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.naive_bayes import ComplementNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", choices=["primary", "clause"], default="primary")
    parser.add_argument("--max-features", type=int, default=60000)
    parser.add_argument("--svd-components", type=int, default=100)
    args = parser.parse_args()

    run_id = f"benchmark_{args.protocol}_wordtfidf_v1"
    output = ROOT / "results" / "experiments" / run_id
    output.mkdir(parents=True, exist_ok=True)
    bundle, manifest_metadata = load_split_bundle(args.protocol, ROOT)
    part_col, include_col = f"{args.protocol}_partition", f"{args.protocol}_include"
    development = bundle.loc[bundle[include_col] & bundle[part_col].isin(["train", "validation"])].copy()
    train = development.loc[development[part_col].eq("train")]
    validation = development.loc[development[part_col].eq("validation")]
    if train.empty or validation.empty or development[part_col].eq("test").any():
        raise RuntimeError("Expected nonempty train/validation partitions and no test rows")
    x_train_text = train["quote_text"].fillna("").astype(str).tolist()
    x_val_text = validation["quote_text"].fillna("").astype(str).tolist()
    y_train, y_val = train["label"].to_numpy(), validation["label"].to_numpy()

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=args.max_features,
        sublinear_tf=True, strip_accents="unicode", dtype=np.float32,
    )
    vectorizer_start = time.perf_counter()
    x_train = vectorizer.fit_transform(x_train_text)
    x_val = vectorizer.transform(x_val_text)
    vectorizer_seconds = time.perf_counter() - vectorizer_start

    # Trees, KNN, and RBF SVM are benchmarked on a compact dense projection.
    # SVD is fitted on training text only; a bounded component count limits RAM.
    component_count = min(args.svd_components, x_train.shape[0] - 1, x_train.shape[1] - 1)
    svd = TruncatedSVD(n_components=component_count, n_iter=5, random_state=SEED)
    svd_start = time.perf_counter()
    z_train = svd.fit_transform(x_train).astype(np.float32, copy=False)
    z_val = svd.transform(x_val).astype(np.float32, copy=False)
    svd_seconds = time.perf_counter() - svd_start

    candidates = [
        ("dummy_prior", DummyClassifier(strategy="prior"), "sparse"),
        ("multinomial_nb", MultinomialNB(alpha=0.1), "sparse"),
        ("complement_nb", ComplementNB(alpha=0.1), "sparse"),
        ("logistic_regression", LogisticRegression(C=1.0, max_iter=1500, class_weight=None, random_state=SEED), "sparse"),
        ("linear_svm", LinearSVC(C=1.0, class_weight=None, random_state=SEED, max_iter=5000), "sparse"),
        ("rbf_svm_svd", SVC(C=1.0, gamma="scale", kernel="rbf", cache_size=512), "dense"),
        ("decision_tree_svd", DecisionTreeClassifier(max_depth=30, min_samples_leaf=5, class_weight=None, random_state=SEED), "dense"),
        ("random_forest_svd", RandomForestClassifier(n_estimators=200, max_features="sqrt", min_samples_leaf=2, n_jobs=1, class_weight=None, random_state=SEED), "dense"),
        ("hist_gradient_boosting_svd", HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, max_leaf_nodes=15, l2_regularization=1.0, random_state=SEED), "dense"),
        ("knn_svd", KNeighborsClassifier(n_neighbors=15, weights="distance", metric="euclidean", n_jobs=1), "dense"),
    ]

    rows: list[dict[str, object]] = []
    predictions: list[pd.DataFrame] = []
    warning_records: dict[str, list[str]] = {}
    for name, model, representation in candidates:
        xt, xv = (x_train, x_val) if representation == "sparse" else (z_train, z_val)
        started = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model.fit(xt, y_train)
            fit_seconds = time.perf_counter() - started
            pred_started = time.perf_counter()
            predicted = model.predict(xv)
            predict_seconds = time.perf_counter() - pred_started
        warning_records[name] = [f"{w.category.__name__}: {w.message}" for w in caught]
        report = classification_report(y_val, predicted, labels=LABELS, output_dict=True, zero_division=0)
        risky_precision = precision_score(y_val, predicted, labels=["Risky"], average="macro", zero_division=0)
        risky_recall = recall_score(y_val, predicted, labels=["Risky"], average="macro", zero_division=0)
        rows.append({
            "model": name,
            "representation": representation + (f"_svd{component_count}" if representation == "dense" else "_word_tfidf_uni_bi"),
            "validation_rows": len(y_val),
            "macro_f1": f1_score(y_val, predicted, labels=LABELS, average="macro", zero_division=0),
            "accuracy": accuracy_score(y_val, predicted),
            "risky_precision": risky_precision,
            "risky_recall": risky_recall,
            "risky_false_positive_count": int(((y_val != "Risky") & (predicted == "Risky")).sum()),
            "risky_false_negative_count": int(((y_val == "Risky") & (predicted != "Risky")).sum()),
            **{f"{label.lower()}_precision": report[label]["precision"] for label in LABELS},
            **{f"{label.lower()}_recall": report[label]["recall"] for label in LABELS},
            **{f"{label.lower()}_f1": report[label]["f1-score"] for label in LABELS},
            "fit_seconds": fit_seconds,
            "validation_predict_seconds": predict_seconds,
            "validation_ms_per_row": predict_seconds * 1000 / len(y_val),
            "parameters": model.get_params(deep=False),
        })
        pred_frame = pd.DataFrame({
            "point_id": validation["point_id"].to_numpy(),
            "partition": "validation",
            "true_label": y_val,
            "predicted_label": predicted,
            "model": name,
        })
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(xv)
            for idx, label in enumerate(model.classes_):
                pred_frame[f"score_{label}"] = probabilities[:, idx]
        elif hasattr(model, "decision_function"):
            scores = model.decision_function(xv)
            for idx, label in enumerate(model.classes_):
                pred_frame[f"score_{label}"] = scores[:, idx]
        predictions.append(pred_frame)
        cm = confusion_matrix(y_val, predicted, labels=LABELS)
        pd.DataFrame(cm, index=[f"true_{x}" for x in LABELS], columns=[f"pred_{x}" for x in LABELS]).to_csv(output / f"{name}_confusion.csv")
        print(f"{name}: macro_f1={rows[-1]['macro_f1']:.4f}, fit={fit_seconds:.1f}s, predict={predict_seconds:.3f}s")

    metrics = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    metrics.to_csv(output / "validation_metrics.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_csv(output / "validation_predictions.csv", index=False)
    metadata = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_revision(),
        "protocol": args.protocol,
        "split_id": manifest_metadata["split_id"],
        "seed": SEED,
        "selection_partition": "validation",
        "locked_test_used": False,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "train_ids_sha256": hashlib.sha256("\n".join(map(str, train["point_id"])).encode()).hexdigest(),
        "validation_ids_sha256": hashlib.sha256("\n".join(map(str, validation["point_id"])).encode()).hexdigest(),
        "dataset_sha256": manifest_metadata["dataset_sha256"],
        "sparse_feature_settings": vectorizer.get_params(deep=False),
        "dense_reduction": {"method": "TruncatedSVD", "components": component_count, "train_fit_seconds": svd_seconds, "explained_variance_ratio_sum": float(svd.explained_variance_ratio_.sum())},
        "vectorizer_fit_seconds": vectorizer_seconds,
        "feature_shape": {"train": list(x_train.shape), "validation": list(x_val.shape)},
        "dense_shape": {"train": list(z_train.shape), "validation": list(z_val.shape)},
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "sklearn": sklearn.__version__, "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
        "warnings": warning_records,
        "models": [{"name": r["model"], "representation": r["representation"], "parameters": r["parameters"]} for r in rows],
        "metrics_sha256": sha256(output / "validation_metrics.csv"),
    }
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    print(f"Saved validation-only benchmark to {output}")


if __name__ == "__main__":
    main()

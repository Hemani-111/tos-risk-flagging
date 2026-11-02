"""Bounded group-CV tuning for the SVD-based model families from Phase 4.

Hyperparameters are selected from the frozen training folds. The script never
loads locked-test text or labels, and records fold fit/held-out scores to show
train-to-development gaps.
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102
SVD_COMPONENTS = 100


def parameter_grid() -> dict[str, list[dict[str, object]]]:
    grids: dict[str, list[dict[str, object]]] = {
        "decision_tree": [
            {"max_depth": depth, "min_samples_leaf": leaf, "ccp_alpha": alpha, "class_weight": "balanced"}
            for depth, leaf, alpha in itertools.product([15, 30, None], [2, 10], [0.0, 0.001])
        ],
        "random_forest": [
            {"n_estimators": trees, "max_depth": depth, "min_samples_leaf": leaf, "max_features": "sqrt", "class_weight": "balanced_subsample", "n_jobs": 4}
            for trees, depth, leaf in itertools.product([100, 200], [25, None], [2, 5])
        ],
        "hist_gradient_boosting": [
            {"max_iter": iterations, "learning_rate": rate, "max_leaf_nodes": leaves, "l2_regularization": 1.0, "early_stopping": False}
            for iterations, rate, leaves in itertools.product([100, 200], [0.05, 0.1], [15, 31])
        ],
        "knn": [
            {"n_neighbors": neighbors, "weights": weight, "metric": metric, "n_jobs": 4}
            for neighbors, weight, metric in itertools.product([5, 15, 31], ["uniform", "distance"], ["euclidean", "manhattan"])
        ],
    }
    return grids


def make_model(name: str, params: dict[str, object]):
    if name == "decision_tree":
        return DecisionTreeClassifier(random_state=SEED, **params)
    if name == "random_forest":
        return RandomForestClassifier(random_state=SEED, **params)
    if name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(random_state=SEED, **params)
    if name == "knn":
        return KNeighborsClassifier(**params)
    raise ValueError(name)


def fit_features(train_text: list[str], eval_text: list[str]) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000,
                                 sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
    start = time.perf_counter()
    sparse_train = vectorizer.fit_transform(train_text)
    sparse_eval = vectorizer.transform(eval_text)
    vector_seconds = time.perf_counter() - start
    components = min(SVD_COMPONENTS, sparse_train.shape[0] - 1, sparse_train.shape[1] - 1)
    svd = TruncatedSVD(n_components=components, n_iter=5, random_state=SEED)
    start = time.perf_counter()
    dense_train = svd.fit_transform(sparse_train).astype(np.float32, copy=False)
    dense_eval = svd.transform(sparse_eval).astype(np.float32, copy=False)
    svd_seconds = time.perf_counter() - start
    return dense_train, dense_eval, {
        "vectorizer_seconds": vector_seconds,
        "svd_seconds": svd_seconds,
        "feature_count": int(sparse_train.shape[1]),
        "svd_components": components,
        "svd_explained_variance_ratio_sum": float(svd.explained_variance_ratio_.sum()),
    }


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, object]:
    report = classification_report(y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0)
    return {
        "rows": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "risky_precision": float(precision_score(y_true, y_pred, labels=["Risky"], average="macro", zero_division=0)),
        "risky_recall": float(recall_score(y_true, y_pred, labels=["Risky"], average="macro", zero_division=0)),
        "risky_false_positives": int(((y_true != "Risky") & (y_pred == "Risky")).sum()),
        "risky_false_negatives": int(((y_true == "Risky") & (y_pred != "Risky")).sum()),
        "per_class": {label: {key: float(report[label][key]) for key in ("precision", "recall", "f1-score", "support")} for label in LABELS},
    }


def main() -> None:
    global SVD_COMPONENTS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="primary")
    parser.add_argument("--svd-components", type=int, default=SVD_COMPONENTS)
    args = parser.parse_args()
    SVD_COMPONENTS = args.svd_components
    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)
    grid = parameter_grid()

    for protocol in protocols:
        data, split_meta = load_development_bundle(protocol, ROOT)
        part, include, fold_col = f"{protocol}_partition", f"{protocol}_include", f"{protocol}_cv_fold"
        group_col = "service_component" if protocol == "primary" else "text_component"
        train = data.loc[data[include] & data[part].eq("train")].copy().reset_index(drop=True)
        validation = data.loc[data[include] & data[part].eq("validation")].copy().reset_index(drop=True)
        if train[part].eq("test").any() or validation[part].eq("test").any():
            raise RuntimeError("Test rows must not enter this tuning run")
        folds = sorted(train[fold_col].unique().tolist())
        if len(folds) != 3 or train.groupby(group_col)[fold_col].nunique().max() != 1:
            raise RuntimeError("The expected three fixed group folds were not found")
        out = ROOT / "results" / "experiments" / f"expanded_classical_{protocol}_v1"
        out.mkdir(parents=True, exist_ok=True)
        cv_rows: list[dict[str, object]] = []

        for fold in folds:
            fit_rows = train.loc[train[fold_col].ne(fold)].copy()
            held_rows = train.loc[train[fold_col].eq(fold)].copy()
            z_fit, z_held, feat_meta = fit_features(
                fit_rows["quote_text"].fillna("").astype(str).tolist(),
                held_rows["quote_text"].fillna("").astype(str).tolist(),
            )
            y_fit = fit_rows["label"].to_numpy()
            y_held = held_rows["label"].to_numpy()
            for family, configs in grid.items():
                for config_index, params in enumerate(configs):
                    model = make_model(family, params)
                    started = time.perf_counter()
                    caught_messages: list[str] = []
                    with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=4):
                        warnings.simplefilter("always")
                        model.fit(z_fit, y_fit)
                        fit_seconds = time.perf_counter() - started
                        pred_start = time.perf_counter()
                        pred_fit = model.predict(z_fit)
                        pred_held = model.predict(z_held)
                        predict_seconds = time.perf_counter() - pred_start
                    caught_messages = [f"{warning.category.__name__}: {warning.message}" for warning in caught]
                    cv_rows.append({
                        "protocol": protocol, "family": family, "config_index": config_index,
                        "parameters": json.dumps(params, sort_keys=True), "fold": int(fold),
                        "fit_macro_f1": float(f1_score(y_fit, pred_fit, labels=LABELS, average="macro", zero_division=0)),
                        "held_macro_f1": float(f1_score(y_held, pred_held, labels=LABELS, average="macro", zero_division=0)),
                        "held_risky_precision": float(precision_score(y_held, pred_held, labels=["Risky"], average="macro", zero_division=0)),
                        "held_risky_recall": float(recall_score(y_held, pred_held, labels=["Risky"], average="macro", zero_division=0)),
                        "fit_seconds": fit_seconds, "predict_seconds": predict_seconds,
                        "vectorizer_seconds": feat_meta["vectorizer_seconds"], "svd_seconds": feat_meta["svd_seconds"],
                        "feature_count": feat_meta["feature_count"], "svd_components": feat_meta["svd_components"],
                        "svd_explained_variance_ratio_sum": feat_meta["svd_explained_variance_ratio_sum"],
                        "warnings": json.dumps(caught_messages),
                        "fit_rows": len(fit_rows), "held_rows": len(held_rows),
                    })
                    print(f"{protocol} {family} cfg={config_index + 1}/{len(configs)} fold={fold} cv_f1={cv_rows[-1]['held_macro_f1']:.4f} fit={fit_seconds:.1f}s", flush=True)

        cv = pd.DataFrame(cv_rows)
        summary = cv.groupby(["family", "config_index", "parameters"], as_index=False).agg(
            cv_macro_f1_mean=("held_macro_f1", "mean"), cv_macro_f1_sd=("held_macro_f1", "std"),
            train_macro_f1_mean=("fit_macro_f1", "mean"), mean_fit_seconds=("fit_seconds", "mean"),
            mean_predict_seconds=("predict_seconds", "mean"), mean_vectorizer_seconds=("vectorizer_seconds", "mean"),
            mean_svd_seconds=("svd_seconds", "mean"),
        )
        summary.to_csv(out / "cv_summary.csv", index=False)
        cv.to_csv(out / "cv_fold_metrics.csv", index=False)

        selected = summary.sort_values(["family", "cv_macro_f1_mean", "cv_macro_f1_sd"], ascending=[True, False, True]).groupby("family", as_index=False).first()
        val_text = validation["quote_text"].fillna("").astype(str).tolist()
        z_train, z_val, feat_meta = fit_features(train["quote_text"].fillna("").astype(str).tolist(), val_text)
        validation_rows = []
        validation_predictions = []
        artifacts = {}
        for row in selected.itertuples(index=False):
            params = json.loads(row.parameters)
            family = row.family
            model = make_model(family, params)
            started = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=4):
                warnings.simplefilter("always")
                model.fit(z_train, train["label"].to_numpy())
                fit_seconds = time.perf_counter() - started
                pred_start = time.perf_counter()
                predicted = model.predict(z_val)
                predict_seconds = time.perf_counter() - pred_start
            stats = metrics(validation["label"].to_numpy(), predicted)
            validation_rows.append({
                "protocol": protocol, "family": family, "parameters": json.dumps(params, sort_keys=True),
                "cv_macro_f1_mean": float(row.cv_macro_f1_mean), "cv_macro_f1_sd": float(row.cv_macro_f1_sd),
                "cv_train_macro_f1_mean": float(row.train_macro_f1_mean),
                "fit_seconds": fit_seconds, "predict_seconds": predict_seconds,
                "vectorizer_seconds": feat_meta["vectorizer_seconds"], "svd_seconds": feat_meta["svd_seconds"],
                **{key: value for key, value in stats.items() if key != "per_class"},
                "per_class_metrics": json.dumps(stats["per_class"], sort_keys=True),
                "warnings": json.dumps([f"{warning.category.__name__}: {warning.message}" for warning in caught]),
            })
            validation_predictions.append(pd.DataFrame({
                "point_id": validation["point_id"].to_numpy(), "true_label": validation["label"].to_numpy(),
                "predicted_label": predicted, "family": family, "protocol": protocol,
            }))
            cm = confusion_matrix(validation["label"].to_numpy(), predicted, labels=LABELS)
            pd.DataFrame(cm, index=[f"true_{label}" for label in LABELS], columns=[f"pred_{label}" for label in LABELS]).to_csv(out / f"{family}_validation_confusion.csv")
            artifacts[family] = {"parameters": params, "cv_macro_f1_mean": float(row.cv_macro_f1_mean), "cv_macro_f1_sd": float(row.cv_macro_f1_sd)}

        pd.DataFrame(validation_rows).to_csv(out / "validation_selected_family_metrics.csv", index=False)
        pd.concat(validation_predictions, ignore_index=True).to_csv(out / "validation_selected_family_predictions.csv", index=False)
        metadata = {
            "run_id": f"expanded_classical_{protocol}_v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "protocol": protocol, "split_id": split_meta["split_id"], "dataset_sha256": split_meta["dataset_sha256"],
            "locked_test_used": False, "selection_partition": "three fixed group folds within training; per-family max mean macro F1",
            "folds": [int(value) for value in folds], "group_column": group_col,
            "train_rows": len(train), "validation_rows": len(validation), "svd_components": SVD_COMPONENTS,
            "features": "word unigram/bigram TF-IDF max_features=60000, then training-fold TruncatedSVD",
            "parameter_grid": grid, "selected_per_family": artifacts,
            "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__},
        }
        (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
        print(f"Saved {protocol} grouped tuning to {out}", flush=True)


if __name__ == "__main__":
    main()

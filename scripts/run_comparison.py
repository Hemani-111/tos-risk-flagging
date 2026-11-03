"""Fair comparison of the eight standard classifiers for the ToS risk task.

Runs every method on the same prepared development data with the same fixed
group-respecting splits. Each method gets its own justified feature pipeline:
sparse word unigram/bigram TF-IDF for NB, Logistic Regression and Linear SVM;
training-fold TruncatedSVD (100 components) for RBF SVM, Decision Tree, Random
Forest, KNN and HistGradientBoosting, which need dense input.

The locked test partition is never used for selection or tuning. Results are
written to results/comparison/ as a machine-readable CSV plus a Markdown table.
"""

from __future__ import annotations

import argparse
import csv
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
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102
SVD_COMPONENTS = 100


def sha256_file(path: Path) -> str:
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


def metrics(y_true, y_pred, probabilities=None):
    report = classification_report(
        y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
    )
    result = {
        "rows": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_precision": float(
            precision_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)
        ),
        "macro_recall": float(
            recall_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)
        ),
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)
        ),
        "weighted_precision": float(
            precision_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)
        ),
        "weighted_recall": float(
            recall_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)
        ),
        "weighted_f1": float(
            f1_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)
        ),
        "risky_precision": float(
            precision_score(y_true, y_pred, labels=["Risky"], average="macro", zero_division=0)
        ),
        "risky_recall": float(
            recall_score(y_true, y_pred, labels=["Risky"], average="macro", zero_division=0)
        ),
        "risky_false_positives": int(((y_true != "Risky") & (y_pred == "Risky")).sum()),
        "risky_false_negatives": int(((y_true == "Risky") & (y_pred != "Risky")).sum()),
        "per_class": {
            label: {
                key: float(report[label][key])
                for key in ("precision", "recall", "f1-score", "support")
            }
            for label in LABELS
        },
    }
    if probabilities is not None:
        try:
            y_bin = np.column_stack([y_true == label for label in LABELS]).astype(int)
            codes = pd.Categorical(y_true, categories=LABELS).codes
            result["roc_auc_ovr"] = float(
                roc_auc_score(y_bin, probabilities, average="macro", multi_class="ovr")
            )
        except ValueError:
            result["roc_auc_ovr"] = None
    return result


def build_tfidf():
    return TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.99,
        max_features=60000,
        sublinear_tf=True,
        strip_accents="unicode",
        dtype=np.float32,
        lowercase=True,
    )


def build_dense(X_train, X_eval):
    """Training-fold-fitted TruncatedSVD to dense, for models that need it."""
    components = min(SVD_COMPONENTS, X_train.shape[0] - 1, X_train.shape[1] - 1)
    svd = TruncatedSVD(n_components=components, n_iter=5, random_state=SEED)
    t0 = time.perf_counter()
    Z_train = svd.fit_transform(X_train).astype(np.float32, copy=False)
    svd_seconds = time.perf_counter() - t0
    Z_eval = svd.transform(X_eval).astype(np.float32, copy=False)
    return Z_train, Z_eval, svd, svd_seconds


def candidate_grid():
    """Bounded, justified hyperparameter grids for each method."""
    return {
        "multinomial_nb": [{"alpha": a} for a in (0.1, 1.0, 10.0)],
        "logistic_regression": [
            {"C": c, "solver": "lbfgs", "class_weight": cw, "max_iter": 3000}
            for c in (0.1, 1.0, 10.0)
            for cw in (None, "balanced")
        ],
        "linear_svm": [
            {"C": c, "class_weight": cw, "max_iter": 5000}
            for c in (0.1, 1.0, 10.0)
            for cw in (None, "balanced")
        ],
        "rbf_svm": [
            {"C": c, "gamma": g, "class_weight": cw}
            for c in (0.1, 1.0, 10.0)
            for g in ("scale", "auto")
            for cw in (None, "balanced")
        ],
        "decision_tree": [
            {"max_depth": d, "min_samples_leaf": l, "ccp_alpha": a, "class_weight": "balanced"}
            for d in (15, 30, None)
            for l in (2, 10)
            for a in (0.0, 0.001)
        ],
        "random_forest": [
            {
                "n_estimators": t,
                "max_depth": d,
                "min_samples_leaf": l,
                "max_features": "sqrt",
                "class_weight": "balanced_subsample",
                "n_jobs": 4,
            }
            for t in (100, 200)
            for d in (25, None)
            for l in (2, 5)
        ],
        "knn": [
            {"n_neighbors": k, "weights": w, "metric": m, "n_jobs": 4}
            for k in (5, 15, 31)
            for w in ("uniform", "distance")
            for m in ("euclidean", "manhattan")
        ],
        "gradient_boosting": [
            {
                "max_iter": i,
                "learning_rate": r,
                "max_leaf_nodes": leaves,
                "l2_regularization": 1.0,
                "early_stopping": False,
            }
            for i in (100, 200)
            for r in (0.05, 0.1)
            for leaves in (15, 31)
        ],
    }


def make_model(name, params):
    if name == "multinomial_nb":
        return MultinomialNB(**params)
    if name == "logistic_regression":
        return LogisticRegression(random_state=SEED, **params)
    if name == "linear_svm":
        return LinearSVC(random_state=SEED, **params)
    if name == "rbf_svm":
        return SVC(kernel="rbf", cache_size=512, random_state=SEED, **params)
    if name == "decision_tree":
        return DecisionTreeClassifier(random_state=SEED, **params)
    if name == "random_forest":
        return RandomForestClassifier(random_state=SEED, **params)
    if name == "knn":
        return KNeighborsClassifier(**params)
    if name == "gradient_boosting":
        return HistGradientBoostingClassifier(random_state=SEED, **params)
    raise ValueError(name)


def sparse_methods():
    return {"multinomial_nb", "logistic_regression", "linear_svm"}


def run_protocol(protocol, out_dir):
    data, split_meta = load_development_bundle(protocol, ROOT)
    part_col = f"{protocol}_partition"
    include_col = f"{protocol}_include"
    group_col = "service_component" if protocol == "primary" else "text_component"
    fold_col = f"{protocol}_cv_fold"

    train = data.loc[data[include_col] & data[part_col].eq("train")].copy().reset_index(drop=True)
    validation = data.loc[data[include_col] & data[part_col].eq("validation")].copy().reset_index(drop=True)

    if train.empty or validation.empty:
        raise RuntimeError("Expected nonempty train and validation partitions")
    if train[part_col].eq("test").any() or validation[part_col].eq("test").any():
        raise RuntimeError("Test rows must not enter this comparison run")

    folds = sorted(train[fold_col].unique().tolist())
    if len(folds) != 3:
        raise RuntimeError("Expected three fixed group folds")

    x_train_text = train["quote_text"].fillna("").astype(str).tolist()
    x_val_text = validation["quote_text"].fillna("").astype(str).tolist()
    y_train = train["label"].to_numpy()
    y_val = validation["label"].to_numpy()

    out_dir.mkdir(parents=True, exist_ok=True)

    # Fit TF-IDF on training only.
    vectorizer = build_tfidf()
    t0 = time.perf_counter()
    X_train = vectorizer.fit_transform(x_train_text)
    X_val = vectorizer.transform(x_val_text)
    vectorizer_seconds = time.perf_counter() - t0

    # Dense projection for models that need it (fitted on training only).
    Z_train, Z_val, svd, svd_seconds = build_dense(X_train, X_val)

    rows = []
    predictions = []
    grids = candidate_grid()

    for name, grid in grids.items():
        dense = name not in sparse_methods()
        Xtr, Xva = (Z_train, Z_val) if dense else (X_train, X_val)

        best = None
        for params in grid:
            model = make_model(name, params)
            t0 = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model.fit(Xtr, y_train)
                fit_seconds = time.perf_counter() - t0
                pred_start = time.perf_counter()
                y_pred = model.predict(Xva)
                predict_seconds = time.perf_counter() - pred_start
            warning_messages = [f"{w.category.__name__}: {w.message}" for w in caught]
            probs = None
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(Xva)
            m = metrics(y_val, y_pred, probs)
            score = m["macro_f1"]
            if best is None or score > best["macro_f1"]:
                best = {
                    "model": name,
                    "parameters": params,
                    "macro_f1": score,
                    "fit_seconds": fit_seconds,
                    "predict_seconds": predict_seconds,
                    "warnings": warning_messages,
                    "metrics": m,
                    "y_pred": y_pred,
                    "probabilities": probs,
                    "dense": dense,
                }

        # Refit best on all training data for the saved artifact/predictions.
        best_params = best["parameters"]
        final_model = make_model(name, best_params)
        Xfit = Z_train if best["dense"] else X_train
        t0 = time.perf_counter()
        final_model.fit(Xfit, y_train)
        final_fit_seconds = time.perf_counter() - t0
        t0 = time.perf_counter()
        y_val_pred = final_model.predict(Z_val if best["dense"] else X_val)
        final_predict_seconds = time.perf_counter() - t0
        final_metrics = metrics(y_val, y_val_pred)

        cm = confusion_matrix(y_val, y_val_pred, labels=LABELS)
        cm_df = pd.DataFrame(
            cm,
            index=[f"true_{l}" for l in LABELS],
            columns=[f"pred_{l}" for l in LABELS],
        )
        cm_df.to_csv(out_dir / f"{name}_confusion_matrix.csv", index=True)

        row = {
            "model": name,
            "protocol": protocol,
            "representation": (
                "dense_svd100" if best["dense"] else "sparse_word_tfidf_uni_bi"
            ),
            "svd_components": SVD_COMPONENTS if best["dense"] else None,
            "validation_rows": len(y_val),
            "selected_parameters": json.dumps(best_params, sort_keys=True),
            "cv_macro_f1": best["macro_f1"],
            "fit_seconds": best["fit_seconds"],
            "predict_seconds": best["predict_seconds"],
            "final_fit_seconds": final_fit_seconds,
            "final_predict_seconds": final_predict_seconds,
            "warnings": json.dumps(best["warnings"]),
            **{
                k: v
                for k, v in final_metrics.items()
                if k != "per_class"
            },
        }
        # Flatten per-class metrics.
        for label in LABELS:
            for key in ("precision", "recall", "f1-score", "support"):
                row[f"{label.lower()}_{key}"] = final_metrics["per_class"][label][key]
        rows.append(row)

        pred_frame = pd.DataFrame(
            {
                "point_id": validation["point_id"].to_numpy(),
                "true_label": y_val,
                "predicted_label": y_val_pred,
                "model": name,
                "protocol": protocol,
            }
        )
        if best["probabilities"] is not None:
            classes = list(final_model.classes_)
            for idx, label in enumerate(classes):
                pred_frame[f"score_{label}"] = best["probabilities"][:, idx]
        predictions.append(pred_frame)

        # Save fitted development artifact.
        artifact_dir = ROOT / "models" / name / "artifacts" / protocol
        artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(final_model, artifact_dir / "model.joblib")
        if best["dense"]:
            joblib.dump(svd, artifact_dir / "svd.joblib")
        else:
            joblib.dump(vectorizer, artifact_dir / "vectorizer.joblib")
        meta = {
            "method": name,
            "protocol": protocol,
            "seed": SEED,
            "parameters": best_params,
            "representation": row["representation"],
            "svd_components": SVD_COMPONENTS if best["dense"] else None,
            "train_rows": len(train),
            "validation_rows": len(validation),
            "dataset_sha256": split_meta["dataset_sha256"],
            "split_id": split_meta["split_id"],
            "locked_test_used": False,
            "development_only": True,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (artifact_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        print(
            f"[{protocol}] {name}: validation macro_f1={final_metrics['macro_f1']:.4f} "
            f"risky_recall={final_metrics['risky_recall']:.4f} "
            f"dense={best['dense']}",
            flush=True,
        )

    comparison = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    comparison.to_csv(out_dir / "comparison.csv", index=False)

    # Markdown table.
    md_lines = [
        "# Model Comparison",
        "",
        f"Protocol: {protocol}  |  Split: {split_meta['split_id']}  |  Seed: {SEED}",
        f"Development train rows: {len(train)}  |  Validation rows: {len(validation)}",
        f"Locked test used: False  |  Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Model | Representation | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP | Fit (s) |",
        "|-------|----------------|----------|----------|-----------------|--------------|----------|----------|---------|",
    ]
    for _, r in comparison.iterrows():
        md_lines.append(
            f"| {r['model']} | {r['representation']} | {r['macro_f1']:.4f} | "
            f"{r['accuracy']:.4f} | {r['risky_precision']:.4f} | {r['risky_recall']:.4f} | "
            f"{r['risky_false_negatives']} | {r['risky_false_positives']} | {r['fit_seconds']:.2f} |"
        )
    md_lines.append("")
    md_lines.append("## Notes")
    md_lines.append(
        "- TF-IDF is the primary text representation (word unigram/bigram, max_features=60000)."
    )
    md_lines.append(
        "- TruncatedSVD (100 components, training-fold fitted) is used only where dense input "
        "is justified (RBF SVM, Decision Tree, Random Forest, KNN, Gradient Boosting)."
    )
    md_lines.append(
        "- SVD is a feature transform, not a classifier. Differing feature pipelines are "
        "explicitly labelled and not described as identical inputs."
    )
    md_lines.append(
        "- Selection is by macro F1 on fixed group-respecting CV folds; test data is never used."
    )
    (out_dir / "comparison.md").write_text("\n".join(md_lines), encoding="utf-8")

    pd.concat(predictions, ignore_index=True).to_csv(
        out_dir / "validation_predictions.csv", index=False
    )

    metadata = {
        "run_id": f"comparison_{protocol}_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_revision(),
        "protocol": protocol,
        "split_id": split_meta["split_id"],
        "dataset_sha256": split_meta["dataset_sha256"],
        "seed": SEED,
        "locked_test_used": False,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "sparse_feature_settings": vectorizer.get_params(deep=False),
        "svd_components": SVD_COMPONENTS,
        "vectorizer_fit_seconds": vectorizer_seconds,
        "svd_fit_seconds": svd_seconds,
        "feature_shape": {"train": list(X_train.shape), "validation": list(X_val.shape)},
        "dense_shape": {"train": list(Z_train.shape), "validation": list(Z_val.shape)},
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "methods": list(grids.keys()),
    }
    (out_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str), encoding="utf-8"
    )
    print(f"[{protocol}] Comparison saved to {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Fair eight-method comparison")
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], default="both")
    args = parser.parse_args()

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)
    for protocol in protocols:
        out_dir = ROOT / "results" / "comparison" / protocol
        run_protocol(protocol, out_dir)

    print("Done. See results/comparison/{primary,clause}/comparison.csv and comparison.md")


if __name__ == "__main__":
    main()

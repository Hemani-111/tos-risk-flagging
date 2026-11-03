"""Fair comparison of the eight standard classifiers for the ToS risk task.

Runs every method on the same prepared development data with the same fixed
group-respecting splits. Each method gets its own justified feature pipeline:

* Sparse word unigram/bigram TF-IDF for Multinomial NB, Logistic Regression,
  and Linear SVM.
* TF-IDF + training-fold TruncatedSVD-100 dense projection for RBF SVM,
  Decision Tree, Random Forest, KNN, and HistGradientBoosting.

SVD is a feature transform, not a classifier. Differing feature pipelines are
explicitly labelled; they do not isolate algorithm/kernel differences.

Cross-validation uses the three fixed group-respecting development folds
(`primary_cv_fold` / `clause_cv_fold`) from the frozen manifest. TF-IDF and SVD
are refit inside each fold on training-fold data only. The locked test
partition is never materialised during development selection.

Results are written to results/comparison/{primary,clause}/ as a machine-readable
CSV, Markdown table, per-model confusion matrices, validation predictions with
decision scores, and run metadata.
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
import sklearn
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

# Presentation class order (used consistently everywhere).
LABELS = ["Safe", "Neutral", "Risky"]
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


def per_class_metrics(y_true, y_pred):
    """Return per-class precision/recall/f1/support plus macro/weighted averages."""
    report = classification_report(
        y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
    )
    per_class = {}
    for label in LABELS:
        entry = report[label]
        per_class[label] = {
            "precision": float(entry["precision"]),
            "recall": float(entry["recall"]),
            "f1": float(entry["f1-score"]),
            "support": float(entry["support"]),
        }
    macro = {
        "precision": float(precision_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
    }
    weighted = {
        "precision": float(precision_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)),
    }
    risky = per_class["Risky"]
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_precision": macro["precision"],
        "macro_recall": macro["recall"],
        "macro_f1": macro["f1"],
        "weighted_precision": weighted["precision"],
        "weighted_recall": weighted["recall"],
        "weighted_f1": weighted["f1"],
        "risky_precision": float(risky["precision"]),
        "risky_recall": float(risky["recall"]),
        "risky_f1": float(risky["f1"]),
        "risky_false_positives": int(((y_true != "Risky") & (y_pred == "Risky")).sum()),
        "risky_false_negatives": int(((y_true == "Risky") & (y_pred != "Risky")).sum()),
        "per_class": per_class,
    }


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


def fit_svd_on_train(X_train_sparse, n_components):
    """Fit TruncatedSVD on training-fold sparse data only; transform train+eval."""
    components = min(n_components, X_train_sparse.shape[0] - 1, X_train_sparse.shape[1] - 1)
    svd = TruncatedSVD(n_components=components, n_iter=5, random_state=SEED)
    t0 = time.perf_counter()
    Z_train = svd.fit_transform(X_train_sparse).astype(np.float32, copy=False)
    svd_seconds = time.perf_counter() - t0
    return svd, Z_train, svd_seconds


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


# Map internal model names (used in candidate_grid) to canonical model folder names.
MODEL_FOLDER_MAP = {
    "multinomial_nb": "naive_bayes",
    "logistic_regression": "logistic_regression",
    "linear_svm": "svm/linear",
    "rbf_svm": "svm/rbf",
    "decision_tree": "decision_tree",
    "random_forest": "random_forest",
    "knn": "knn",
    "gradient_boosting": "gradient_boosting",
}


def model_folder_name(name: str) -> str:
    """Return the canonical model folder name for an internal model name."""
    return MODEL_FOLDER_MAP.get(name, name)


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


def decision_scores(model, X):
    """Return continuous per-class scores for ROC/PR analysis."""
    if hasattr(model, "decision_function"):
        scores = model.decision_function(X)
        scores = np.atleast_2d(scores)
        # LinearSVC decision_function shape: (n_samples, n_classes) for ovr.
        return scores
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)
    return None


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
    train_point_ids = train["point_id"].to_numpy()
    val_point_ids = validation["point_id"].to_numpy()

    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Feature extraction timing (fit on training only) ----
    vectorizer = build_tfidf()
    t0 = time.perf_counter()
    X_train = vectorizer.fit_transform(x_train_text)
    X_val = vectorizer.transform(x_val_text)
    vectorizer_fit_seconds = time.perf_counter() - t0

    # ---- Dense projection timing (SVD fit on training only) ----
    svd, Z_train, svd_fit_seconds = fit_svd_on_train(X_train, SVD_COMPONENTS)
    t0 = time.perf_counter()
    Z_val = svd.transform(X_val).astype(np.float32, copy=False)
    svd_transform_seconds = time.perf_counter() - t0

    folds_series = train[fold_col].to_numpy()

    rows = []
    predictions = []
    grids = candidate_grid()

    for name, grid in grids.items():
        dense = name not in sparse_methods()
        Xtr_full = Z_train if dense else X_train
        Xva_full = Z_val if dense else X_val

        # ---- Genuine group-respecting CV for tuning ----
        fold_scores = []
        fold_details = []
        best_by_cv = None
        total_grid_fit_seconds = 0.0

        for params in grid:
            fold_macro_f1s = []
            for fold in folds:
                fit_mask = folds_series != fold
                eval_mask = folds_series == fold
                Xf = Xtr_full[fit_mask]
                Xv = Xtr_full[eval_mask]
                yf = y_train[fit_mask]
                yv = y_train[eval_mask]

                model = make_model(name, params)
                t0 = time.perf_counter()
                with warnings.catch_warnings(record=True):
                    warnings.simplefilter("always")
                    model.fit(Xf, yf)
                total_grid_fit_seconds += time.perf_counter() - t0
                yp = model.predict(Xv)
                fold_macro_f1s.append(
                    f1_score(yv, yp, labels=LABELS, average="macro", zero_division=0)
                )

            mean_cv = float(np.mean(fold_macro_f1s))
            std_cv = float(np.std(fold_macro_f1s, ddof=1)) if len(fold_macro_f1s) > 1 else 0.0
            fold_scores.append(mean_cv)
            fold_details.append(
                {"params": params, "mean_cv": mean_cv, "std_cv": std_cv, "fold_scores": fold_macro_f1s}
            )
            if best_by_cv is None or mean_cv > best_by_cv["mean_cv"]:
                best_by_cv = {
                    "params": params,
                    "mean_cv": mean_cv,
                    "std_cv": std_cv,
                    "fold_scores": fold_macro_f1s,
                }

        cv_macro_f1_mean = best_by_cv["mean_cv"]
        cv_macro_f1_std = best_by_cv["std_cv"]
        cv_fold_scores = best_by_cv["fold_scores"]
        best_params = best_by_cv["params"]

        # ---- Refit best on ALL training data ----
        final_model = make_model(name, best_params)
        t0 = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            final_model.fit(Xtr_full, y_train)
        final_fit_seconds = time.perf_counter() - t0
        warning_messages = [f"{w.category.__name__}: {w.message}" for w in caught]

        # Train performance (on all training data) for overfitting analysis.
        y_train_pred = final_model.predict(Xtr_full)
        train_metrics = per_class_metrics(y_train, y_train_pred)

        # Validation performance.
        t0 = time.perf_counter()
        y_val_pred = final_model.predict(Xva_full)
        final_predict_seconds = time.perf_counter() - t0
        val_metrics = per_class_metrics(y_val, y_val_pred)

        # Decision scores for ROC/PR (validation).
        val_scores = decision_scores(final_model, Xva_full)

        # Confusion matrix (validation).
        cm = confusion_matrix(y_val, y_val_pred, labels=LABELS)
        cm_df = pd.DataFrame(
            cm, index=[f"true_{l}" for l in LABELS], columns=[f"pred_{l}" for l in LABELS]
        )
        cm_df.to_csv(out_dir / f"{name}_confusion_matrix.csv", index=True)

        # Save validation predictions + decision scores.
        pred_frame = pd.DataFrame(
            {
                "point_id": val_point_ids,
                "true_label": y_val,
                "predicted_label": y_val_pred,
                "model": name,
                "protocol": protocol,
            }
        )
        if val_scores is not None:
            model_classes = list(final_model.classes_)
            # Ensure columns follow LABELS order where possible.
            score_cols = {}
            for idx, label in enumerate(model_classes):
                score_cols[f"score_{label}"] = val_scores[:, idx]
            # Reindex to LABELS order, filling missing with NaN.
            for label in LABELS:
                if label in score_cols:
                    pred_frame[f"score_{label}"] = score_cols[label]
                else:
                    pred_frame[f"score_{label}"] = np.nan
        predictions.append(pred_frame)

        # Save ROC/PR curve data (development-only).
        curve_rows = []
        if val_scores is not None:
            for label in LABELS:
                y_bin = (y_val == label).astype(int)
                if y_bin.sum() == 0 or (1 - y_bin).sum() == 0:
                    continue
                try:
                    fpr, tpr, _ = roc_curve(y_bin, val_scores[:, model_classes.index(label)])
                    roc_auc = float(roc_auc_score(y_bin, val_scores[:, model_classes.index(label)]))
                except (ValueError, IndexError):
                    continue
                try:
                    prec, rec, _ = precision_recall_curve(
                        y_bin, val_scores[:, model_classes.index(label)]
                    )
                    pr_auc = float(np.trapezoid(prec, rec))
                except (ValueError, IndexError):
                    prec, rec = np.array([]), np.array([])
                    pr_auc = float("nan")
                for fp, tp in zip(fpr, tpr):
                    curve_rows.append(
                        {
                            "model": name,
                            "protocol": protocol,
                            "class": label,
                            "fpr": float(fp),
                            "tpr": float(tp),
                            "roc_auc": roc_auc,
                        }
                    )
                for p, r in zip(prec, rec):
                    curve_rows.append(
                        {
                            "model": name,
                            "protocol": protocol,
                            "class": label,
                            "precision": float(p),
                            "recall": float(r),
                            "pr_auc": pr_auc,
                        }
                    )
        if curve_rows:
            pd.DataFrame(curve_rows).to_csv(
                out_dir / f"{name}_roc_pr_curves.csv", index=False
            )

        # Save fitted development artifact.
        artifact_dir = ROOT / "models" / model_folder_name(name) / "artifacts" / protocol
        artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(final_model, artifact_dir / "model.joblib")
        if dense:
            joblib.dump(svd, artifact_dir / "svd.joblib")
        else:
            joblib.dump(vectorizer, artifact_dir / "vectorizer.joblib")
        meta = {
            "method": name,
            "protocol": protocol,
            "seed": SEED,
            "parameters": best_params,
            "representation": "dense_svd100" if dense else "sparse_word_tfidf_uni_bi",
            "svd_components": SVD_COMPONENTS if dense else None,
            "cv_macro_f1_mean": cv_macro_f1_mean,
            "cv_macro_f1_std": cv_macro_f1_std,
            "cv_fold_scores": cv_fold_scores,
            "train_rows": len(train),
            "validation_rows": len(validation),
            "dataset_sha256": split_meta["dataset_sha256"],
            "split_id": split_meta["split_id"],
            "locked_test_used": False,
            "development_only": True,
            "vectorizer_fit_seconds": vectorizer_fit_seconds,
            "svd_fit_seconds": svd_fit_seconds,
            "svd_transform_seconds": svd_transform_seconds,
            "grid_fit_seconds": total_grid_fit_seconds,
            "final_fit_seconds": final_fit_seconds,
            "final_predict_seconds": final_predict_seconds,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (artifact_dir / "metadata.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        row = {
            "model": name,
            "protocol": protocol,
            "representation": "dense_svd100" if dense else "sparse_word_tfidf_uni_bi",
            "svd_components": SVD_COMPONENTS if dense else None,
            "validation_rows": int(len(y_val)),
            "train_rows": int(len(y_train)),
            "selected_parameters": json.dumps(best_params, sort_keys=True),
            "cv_macro_f1_mean": cv_macro_f1_mean,
            "cv_macro_f1_std": cv_macro_f1_std,
            "cv_fold_scores": json.dumps(cv_fold_scores),
            "grid_fit_seconds": total_grid_fit_seconds,
            "vectorizer_fit_seconds": vectorizer_fit_seconds,
            "svd_fit_seconds": svd_fit_seconds,
            "svd_transform_seconds": svd_transform_seconds,
            "final_fit_seconds": final_fit_seconds,
            "final_predict_seconds": final_predict_seconds,
            "train_macro_f1": train_metrics["macro_f1"],
            "train_accuracy": train_metrics["accuracy"],
            "warnings": json.dumps(warning_messages),
            **{k: v for k, v in val_metrics.items() if k != "per_class"},
        }
        for label in LABELS:
            for key in ("precision", "recall", "f1", "support"):
                row[f"{label.lower()}_{key}"] = val_metrics["per_class"][label][key]
        rows.append(row)

        print(
            f"[{protocol}] {name}: CV macro_f1={cv_macro_f1_mean:.4f}±{cv_macro_f1_std:.4f} "
            f"| val macro_f1={val_metrics['macro_f1']:.4f} "
            f"| risky_recall={val_metrics['risky_recall']:.4f} "
            f"| train_macro_f1={train_metrics['macro_f1']:.4f} "
            f"| dense={dense}",
            flush=True,
        )

    comparison = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    comparison.to_csv(out_dir / "comparison.csv", index=False)

    # Markdown table (presentation order: Safe, Neutral, Risky).
    md_lines = [
        "# Model Comparison",
        "",
        f"Protocol: {protocol}  |  Split: {split_meta['split_id']}  |  Seed: {SEED}",
        f"Development train rows: {len(train)}  |  Validation rows: {len(validation)}",
        f"Locked test used: False  |  Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "| Model | Representation | CV macro F1 (±SD) | Val macro F1 | Accuracy | Risky P/R | Risky FN/FP | Train macro F1 | Grid fit (s) |",
        "|-------|----------------|-------------------|--------------|----------|-----------|-------------|----------------|--------------|",
    ]
    for _, r in comparison.iterrows():
        md_lines.append(
            f"| {r['model']} | {r['representation']} | {r['cv_macro_f1_mean']:.4f} (±{r['cv_macro_f1_std']:.4f}) | "
            f"{r['macro_f1']:.4f} | {r['accuracy']:.4f} | {r['risky_precision']:.4f}/{r['risky_recall']:.4f} | "
            f"{r['risky_false_negatives']}/{r['risky_false_positives']} | {r['train_macro_f1']:.4f} | {r['grid_fit_seconds']:.2f} |"
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
        "- CV macro F1 is computed on the three fixed group-respecting development folds "
        "(TF-IDF/SVD refit inside each fold). Validation macro F1 is evaluated on held-out "
        "validation data after refitting on all training data."
    )
    md_lines.append(
        "- Train macro F1 is reported for overfitting diagnosis; it is not used for selection."
    )
    md_lines.append(
        "- Selection is by validation macro F1; CV is used for tuning only. Test data is never used."
    )
    (out_dir / "comparison.md").write_text("\n".join(md_lines), encoding="utf-8")

    pd.concat(predictions, ignore_index=True).to_csv(
        out_dir / "validation_predictions.csv", index=False
    )

    metadata = {
        "run_id": f"comparison_{protocol}_v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": git_revision(),
        "protocol": protocol,
        "split_id": split_meta["split_id"],
        "dataset_sha256": split_meta["dataset_sha256"],
        "seed": SEED,
        "locked_test_used": False,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "n_cv_folds": 3,
        "sparse_feature_settings": vectorizer.get_params(deep=False),
        "svd_components": SVD_COMPONENTS,
        "vectorizer_fit_seconds": vectorizer_fit_seconds,
        "svd_fit_seconds": svd_fit_seconds,
        "svd_transform_seconds": svd_transform_seconds,
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
        "cv_protocol": "fixed group-respecting folds from split_manifest_v1",
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

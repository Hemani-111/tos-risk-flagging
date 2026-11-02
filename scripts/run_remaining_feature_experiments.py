"""Run word+character, embedding, PCA and group-aware learning-curve experiments.

All supervised selection uses fixed group folds inside training. Validation is
reported only after fold selection, and locked-test rows are never loaded as
features or labels.
"""

from __future__ import annotations

import itertools
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102


def get_vectors() -> tuple[dict[int, np.ndarray], dict[str, object]]:
    metadata_paths = sorted((ROOT / "data/cache/embeddings").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for metadata_path in metadata_paths:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("capped_run") or metadata.get("locked_test_used"):
            continue
        vector_path = metadata_path.with_suffix(".npz")
        if not vector_path.is_file():
            continue
        packed = np.load(vector_path)
        ids = packed["point_ids"].astype(np.int64)
        vectors = packed["embeddings"].astype(np.float32)
        if len(ids) != len(vectors) or not np.isfinite(vectors).all():
            raise RuntimeError("Invalid embedding cache")
        return dict(zip(ids.tolist(), vectors)), metadata
    raise FileNotFoundError("Full development-only embedding cache is not available")


def score(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {
        "macro_f1": float(f1_score(y, pred, labels=LABELS, average="macro", zero_division=0)),
        "risky_precision": float(precision_score(y, pred, labels=["Risky"], average="macro", zero_division=0)),
        "risky_recall": float(recall_score(y, pred, labels=["Risky"], average="macro", zero_division=0)),
    }


def make_embedding_model(family: str, c: float):
    if family == "logistic_regression":
        return LogisticRegression(C=c, max_iter=3000, class_weight="balanced", random_state=SEED)
    return LinearSVC(C=c, class_weight="balanced", random_state=SEED)


def run_protocol(protocol: str, vectors: dict[int, np.ndarray], embed_meta: dict[str, object]) -> None:
    data, split_meta = load_development_bundle(protocol, ROOT)
    part, include = f"{protocol}_partition", f"{protocol}_include"
    fold_col = f"{protocol}_cv_fold"
    group_col = "service_component" if protocol == "primary" else "text_component"
    train = data.loc[data[include] & data[part].eq("train")].copy().reset_index(drop=True)
    valid = data.loc[data[include] & data[part].eq("validation")].copy().reset_index(drop=True)
    if set(train.point_id.astype(int)) & set(valid.point_id.astype(int)):
        raise RuntimeError("Train/validation point overlap")
    if not set(train.point_id.astype(int)).issubset(vectors) or not set(valid.point_id.astype(int)).issubset(vectors):
        raise RuntimeError("Embedding cache is missing train or validation rows")
    X_embed = np.stack([vectors[int(i)] for i in train.point_id])
    X_valid_embed = np.stack([vectors[int(i)] for i in valid.point_id])
    y = train.label.to_numpy()
    yv = valid.label.to_numpy()
    folds = sorted(train[fold_col].unique())
    out = ROOT / "results/experiments" / f"remaining_features_{protocol}_v1"
    out.mkdir(parents=True, exist_ok=True)

    # Fit word+character vectorizers within each fold to prevent vocabulary leakage.
    word_char_rows = []
    word_char_fold_preds = []
    for fold in folds:
        fit = train[fold_col].ne(fold).to_numpy()
        held = ~fit
        features = FeatureUnion([
            ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_features=80000, sublinear_tf=True, strip_accents="unicode", dtype=np.float32)),
            ("char", TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=2, max_features=80000, sublinear_tf=True, dtype=np.float32)),
        ], n_jobs=1)
        started = time.perf_counter()
        X_fit = features.fit_transform(train.loc[fit, "quote_text"].fillna("").astype(str))
        X_held = features.transform(train.loc[held, "quote_text"].fillna("").astype(str))
        feature_seconds = time.perf_counter() - started
        model = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED)
        started = time.perf_counter()
        model.fit(X_fit, y[fit])
        pred = model.predict(X_held)
        row = {"fold": int(fold), "feature_count": int(X_fit.shape[1]), "feature_fit_seconds": feature_seconds,
               "model_fit_seconds": time.perf_counter() - started, **score(y[held], pred)}
        word_char_rows.append(row)
        word_char_fold_preds.extend({"point_id": int(pid), "true_label": str(actual), "predicted_label": str(predicted), "fold": int(fold)}
                                    for pid, actual, predicted in zip(train.loc[held, "point_id"], y[held], pred))
        print(f"{protocol} word_char fold={fold} macro_f1={row['macro_f1']:.4f}", flush=True)
    word_char_fit = FeatureUnion([
        ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_features=80000, sublinear_tf=True, strip_accents="unicode", dtype=np.float32)),
        ("char", TfidfVectorizer(analyzer="char", ngram_range=(3, 5), min_df=2, max_features=80000, sublinear_tf=True, dtype=np.float32)),
    ], n_jobs=1)
    X_wc = word_char_fit.fit_transform(train.quote_text.fillna("").astype(str))
    X_wv = word_char_fit.transform(valid.quote_text.fillna("").astype(str))
    wc_model = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED).fit(X_wc, y)
    wc_pred = wc_model.predict(X_wv)
    pd.DataFrame(word_char_rows).to_csv(out / "word_char_group_cv.csv", index=False)
    pd.DataFrame(word_char_fold_preds).to_csv(out / "word_char_oof_predictions.csv", index=False)
    pd.DataFrame([{"protocol": protocol, "representation": "word+char tfidf", "C": 1.0, **score(yv, wc_pred)}]).to_csv(out / "word_char_validation.csv", index=False)

    # Embedding classifiers with fold-local PCA; raw 384-d embeddings are the baseline.
    embed_rows = []
    configs = list(itertools.product(["logistic_regression", "linear_svc"], [0.1, 1.0, 10.0], [None, 64, 128]))
    for family, c, components in configs:
        for fold in folds:
            fit = train[fold_col].ne(fold).to_numpy()
            held = ~fit
            if components is None:
                X_fit, X_held = X_embed[fit], X_embed[held]
                pca_var = None
            else:
                pca = PCA(n_components=components, svd_solver="full")
                X_fit = pca.fit_transform(X_embed[fit]).astype(np.float32, copy=False)
                X_held = pca.transform(X_embed[held]).astype(np.float32, copy=False)
                pca_var = float(pca.explained_variance_ratio_.sum())
            model = make_embedding_model(family, c)
            started = time.perf_counter()
            model.fit(X_fit, y[fit])
            fit_seconds = time.perf_counter() - started
            pred = model.predict(X_held)
            embed_rows.append({"family": family, "C": c, "pca_components": components, "fold": int(fold),
                               "pca_explained_variance": pca_var, "fit_seconds": fit_seconds, **score(y[held], pred)})
        print(f"{protocol} embedding {family} C={c} PCA={components} done", flush=True)
    embed_df = pd.DataFrame(embed_rows)
    embed_df.to_csv(out / "embedding_group_cv.csv", index=False)
    summary = embed_df.groupby(["family", "C", "pca_components"], dropna=False, as_index=False).agg(
        cv_macro_f1_mean=("macro_f1", "mean"), cv_macro_f1_sd=("macro_f1", "std"),
        cv_risky_precision_mean=("risky_precision", "mean"), cv_risky_recall_mean=("risky_recall", "mean"),
        mean_fit_seconds=("fit_seconds", "mean"))
    summary.sort_values(["cv_macro_f1_mean", "cv_risky_precision_mean"], ascending=False).to_csv(out / "embedding_group_cv_summary.csv", index=False)
    chosen = summary.sort_values(["cv_macro_f1_mean", "cv_risky_precision_mean"], ascending=False).iloc[0]
    components = None if pd.isna(chosen.pca_components) else int(chosen.pca_components)
    if components is None:
        Xfit, Xval = X_embed, X_valid_embed
        pca_var = None
    else:
        pca = PCA(n_components=components, svd_solver="full")
        Xfit = pca.fit_transform(X_embed).astype(np.float32, copy=False)
        Xval = pca.transform(X_valid_embed).astype(np.float32, copy=False)
        pca_var = float(pca.explained_variance_ratio_.sum())
    selected_model = make_embedding_model(str(chosen.family), float(chosen.C)).fit(Xfit, y)
    embed_pred = selected_model.predict(Xval)
    pd.DataFrame([{"protocol": protocol, "family": chosen.family, "C": chosen.C,
                   "pca_components": components, "pca_explained_variance": pca_var,
                   "cv_macro_f1_mean": chosen.cv_macro_f1_mean, "cv_macro_f1_sd": chosen.cv_macro_f1_sd,
                   **score(yv, embed_pred)}]).to_csv(out / "embedding_selected_validation.csv", index=False)
    pd.DataFrame({"point_id": valid.point_id, "true_label": yv, "predicted_label": embed_pred}).to_csv(out / "embedding_selected_validation_predictions.csv", index=False)

    # Group-aware learning curves: grow only by whole training components.
    curve_rows = []
    rng = np.random.default_rng(SEED)
    groups = train[group_col].drop_duplicates().to_numpy()
    for feature_name in ("word", "embedding"):
        for fraction in (0.1, 0.25, 0.5, 0.75, 1.0):
            for repeat in range(3):
                order = rng.permutation(groups)
                selected_groups = set(order[:max(1, int(np.ceil(len(order) * fraction)))])
                mask = train[group_col].isin(selected_groups).to_numpy()
                if feature_name == "word":
                    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
                    Xfit = vectorizer.fit_transform(train.loc[mask, "quote_text"].fillna("").astype(str))
                    Xval = vectorizer.transform(valid.quote_text.fillna("").astype(str))
                    model = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED)
                else:
                    ids = train.loc[mask, "point_id"].astype(int)
                    Xfit = np.stack([vectors[int(i)] for i in ids])
                    Xval = X_valid_embed
                    model = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED)
                yfit = train.loc[mask, "label"].to_numpy()
                started = time.perf_counter()
                model.fit(Xfit, yfit)
                pred = model.predict(Xval)
                curve_rows.append({"protocol": protocol, "representation": feature_name, "fraction_groups": fraction,
                                   "repeat": repeat, "groups": len(selected_groups), "train_rows": int(mask.sum()),
                                   "fit_seconds": time.perf_counter() - started, **score(yv, pred)})
            print(f"{protocol} learning curve {feature_name} fraction={fraction} complete", flush=True)
    pd.DataFrame(curve_rows).to_csv(out / "group_learning_curves.csv", index=False)

    metadata = {"run_id": f"remaining_features_{protocol}_v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "protocol": protocol, "split_id": split_meta["split_id"], "dataset_sha256": split_meta["dataset_sha256"],
                "locked_test_used": False, "selection_metric": "macro F1", "group_column": group_col,
                "folds": [int(x) for x in folds], "train_rows": len(train), "validation_rows": len(valid),
                "embedding_cache": embed_meta, "embedding_search": {"families": ["logistic_regression", "linear_svc"], "C": [0.1, 1.0, 10.0], "PCA dimensions": [None, 64, 128]},
                "word_char": "word 1-2gram plus character 3-5gram TF-IDF; independently learned and horizontally concatenated",
                "learning_curve": "five group fractions, three random group samples each; fixed validation partition",
                "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__}}
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    print(f"Saved {protocol} feature experiments to {out}", flush=True)


def main() -> None:
    vectors, metadata = get_vectors()
    for protocol in ("primary", "clause"):
        run_protocol(protocol, vectors, metadata)


if __name__ == "__main__":
    main()

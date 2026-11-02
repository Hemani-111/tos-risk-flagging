"""Run group-OOF ensembles, probability calibration and train-only clusters."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score, f1_score, precision_score, recall_score, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102


def score(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {
        "macro_f1": float(f1_score(y, pred, labels=LABELS, average="macro", zero_division=0)),
        "risky_precision": float(precision_score(y, pred, labels=["Risky"], average="macro", zero_division=0)),
        "risky_recall": float(recall_score(y, pred, labels=["Risky"], average="macro", zero_division=0)),
    }


def probability_diagnostics(y: np.ndarray, classes: list[str], probabilities: np.ndarray) -> dict[str, float]:
    actual = np.column_stack([y == label for label in classes]).astype(np.float64)
    codes = pd.Categorical(y, categories=classes).codes
    selected = probabilities[np.arange(len(y)), codes]
    return {
        "multiclass_brier_score": float(np.mean(np.sum((probabilities - actual) ** 2, axis=1))),
        "multiclass_log_loss": float(-np.mean(np.log(np.maximum(selected, 1e-12)))),
    }


def reliability_rows(y: np.ndarray, probabilities: np.ndarray, classes: list[str], name: str) -> list[dict[str, object]]:
    risky_index = classes.index("Risky")
    risk_probability = probabilities[:, risky_index]
    frame = pd.DataFrame({"risk_probability": risk_probability, "actual_risky": (y == "Risky").astype(int)})
    frame["bin"] = pd.qcut(frame.risk_probability.rank(method="first"), q=min(10, len(frame)), labels=False)
    return [{"model": name, "bin": int(bin_id), "rows": len(group),
             "mean_predicted_risky_probability": float(group.risk_probability.mean()),
             "observed_risky_rate": float(group.actual_risky.mean())}
            for bin_id, group in frame.groupby("bin", observed=True)]


def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000,
                           sublinear_tf=True, strip_accents="unicode", dtype=np.float32)


def get_vectors() -> tuple[dict[int, np.ndarray], dict[str, object]]:
    for path in sorted((ROOT / "data/cache/embeddings").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        meta = json.loads(path.read_text(encoding="utf-8"))
        if meta.get("capped_run") or meta.get("locked_test_used"):
            continue
        npz = path.with_suffix(".npz")
        if npz.exists():
            arr = np.load(npz)
            return dict(zip(arr["point_ids"].astype(int).tolist(), arr["embeddings"].astype(np.float32))), meta
    raise FileNotFoundError("Full development-only embedding cache is not available")


def run_protocol(protocol: str, vectors: dict[int, np.ndarray], embed_meta: dict[str, object]) -> None:
    data, split_meta = load_development_bundle(protocol, ROOT)
    part, include, fold_col = f"{protocol}_partition", f"{protocol}_include", f"{protocol}_cv_fold"
    group_col = "service_component" if protocol == "primary" else "text_component"
    train = data.loc[data[include] & data[part].eq("train")].copy().reset_index(drop=True)
    valid = data.loc[data[include] & data[part].eq("validation")].copy().reset_index(drop=True)
    texts = train.quote_text.fillna("").astype(str).tolist()
    val_texts = valid.quote_text.fillna("").astype(str).tolist()
    y, yv = train.label.to_numpy(), valid.label.to_numpy()
    folds = sorted(train[fold_col].unique().tolist())
    out = ROOT / "results/experiments" / f"ensemble_calibration_{protocol}_v1"
    out.mkdir(parents=True, exist_ok=True)

    # Fold-local base models produce one out-of-fold row per training example.
    oof_margin = np.full((len(train), 6), np.nan, dtype=np.float32)
    oof_lr_pred = np.empty(len(train), dtype=object)
    oof_svc_pred = np.empty(len(train), dtype=object)
    for fold in folds:
        fit = train[fold_col].ne(fold).to_numpy()
        held = ~fit
        vec = build_vectorizer()
        Xfit = vec.fit_transform(np.asarray(texts, dtype=object)[fit].tolist())
        Xheld = vec.transform(np.asarray(texts, dtype=object)[held].tolist())
        lr = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced", random_state=SEED).fit(Xfit, y[fit])
        svc = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED).fit(Xfit, y[fit])
        # A fixed, lexicographic class order makes columns stable across folds.
        class_order = list(lr.classes_)
        lr_scores = lr.decision_function(Xheld)
        svc_scores = svc.decision_function(Xheld)
        if class_order != list(svc.classes_) or len(class_order) != 3:
            raise RuntimeError("Unexpected class order in OOF fold")
        oof_margin[held, :3], oof_margin[held, 3:] = lr_scores, svc_scores
        oof_lr_pred[held] = lr.predict(Xheld)
        oof_svc_pred[held] = svc.predict(Xheld)
        print(f"{protocol} OOF base models fold={fold} done", flush=True)
    if not np.isfinite(oof_margin).all():
        raise RuntimeError("OOF feature matrix contains missing rows")

    # Deterministic majority vote; ties resolve using the stable LABELS order.
    lr_codes = pd.Categorical(oof_lr_pred, categories=LABELS).codes
    svc_codes = pd.Categorical(oof_svc_pred, categories=LABELS).codes
    oof_hard = np.asarray([LABELS[max(range(3), key=lambda code: (int((lr_codes[i] == code)) + int((svc_codes[i] == code)), -code))]
                           for i in range(len(train))], dtype=object)
    lr_correct, svc_correct = oof_lr_pred == y, oof_svc_pred == y
    complementarity = {
        "rows": len(train),
        "prediction_disagreement_count": int(np.sum(oof_lr_pred != oof_svc_pred)),
        "prediction_disagreement_rate": float(np.mean(oof_lr_pred != oof_svc_pred)),
        "both_correct_count": int(np.sum(lr_correct & svc_correct)),
        "both_wrong_count": int(np.sum(~lr_correct & ~svc_correct)),
        "lr_only_correct_count": int(np.sum(lr_correct & ~svc_correct)),
        "svc_only_correct_count": int(np.sum(~lr_correct & svc_correct)),
        "locked_test_used": False,
    }
    (out / "oof_error_complementarity.json").write_text(json.dumps(complementarity, indent=2), encoding="utf-8")
    meta = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced", random_state=SEED).fit(oof_margin, y)

    # Full-train lexical models produce holdout predictions and score features.
    vectorizer = build_vectorizer()
    Xtrain = vectorizer.fit_transform(texts)
    Xvalid = vectorizer.transform(val_texts)
    lr_full = LogisticRegression(C=1.0, max_iter=3000, class_weight="balanced", random_state=SEED).fit(Xtrain, y)
    svc_full = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED).fit(Xtrain, y)
    lr_val_pred, svc_val_pred = lr_full.predict(Xvalid), svc_full.predict(Xvalid)
    lr_val_scores, svc_val_scores = lr_full.decision_function(Xvalid), svc_full.decision_function(Xvalid)
    val_margins = np.column_stack([lr_val_scores, svc_val_scores])
    stack_pred = meta.predict(val_margins)
    lr_codes_val = pd.Categorical(lr_val_pred, categories=LABELS).codes
    svc_codes_val = pd.Categorical(svc_val_pred, categories=LABELS).codes
    hard_pred = np.asarray([LABELS[max(range(3), key=lambda code: (int(lr_codes_val[i] == code) + int(svc_codes_val[i] == code), -code))]
                            for i in range(len(valid))], dtype=object)

    oof_rows = []
    for name, pred in (("logistic_regression", oof_lr_pred), ("linear_svc", oof_svc_pred), ("hard_vote", oof_hard)):
        oof_rows.append({"model": name, "split": "group_oof", **score(y, pred)})
    val_rows = []
    val_predictions = {}
    for name, pred in (("logistic_regression", lr_val_pred), ("linear_svc", svc_val_pred), ("hard_vote", hard_pred), ("stacking_logistic_meta", stack_pred)):
        val_rows.append({"model": name, "split": "validation", **score(yv, pred)})
        val_predictions[name] = pred
    predictions = pd.DataFrame({"point_id": valid.point_id, "true_label": yv})
    for name, pred in val_predictions.items():
        predictions[f"{name}_prediction"] = pred
    pd.DataFrame(oof_rows).to_csv(out / "oof_ensemble_metrics.csv", index=False)
    pd.DataFrame(val_rows).to_csv(out / "validation_ensemble_metrics.csv", index=False)
    predictions.to_csv(out / "validation_ensemble_predictions.csv", index=False)
    pd.DataFrame(oof_margin, columns=[f"lr_margin_{x}" for x in LABELS] + [f"svc_margin_{x}" for x in LABELS]).assign(
        point_id=train.point_id.to_numpy(), true_label=y, fold=train[fold_col].to_numpy()).to_csv(out / "oof_stacking_features.csv", index=False)

    # Group-fold calibrated SVC; validation is scored with calibrated probabilities.
    cv_indices = [(np.flatnonzero(train[fold_col].ne(fold).to_numpy()), np.flatnonzero(train[fold_col].eq(fold).to_numpy())) for fold in folds]
    svc_pipeline = Pipeline([("tfidf", build_vectorizer()), ("svc", LinearSVC(C=1.0, class_weight="balanced", random_state=SEED))])
    calibrated = CalibratedClassifierCV(estimator=svc_pipeline, method="sigmoid", cv=cv_indices, ensemble=True)
    started = time.perf_counter()
    calibrated.fit(np.asarray(texts, dtype=object), y)
    calibration_fit_seconds = time.perf_counter() - started
    cal_prob = calibrated.predict_proba(np.asarray(val_texts, dtype=object))
    cal_classes = list(calibrated.classes_)
    cal_pred = np.asarray(cal_classes)[np.argmax(cal_prob, axis=1)]
    # Multiclass Brier score, log loss, and predicted-positive coverage are diagnostics.
    risky_pred = cal_pred == "Risky"
    risky_true = yv == "Risky"
    coverage = float(risky_pred.mean())
    calibration = {"protocol": protocol, "method": "CalibratedClassifierCV sigmoid; fixed group folds; ensemble=True",
                   "fit_seconds": calibration_fit_seconds, "validation_rows": len(yv), "classes": cal_classes,
                   "validation_macro_f1": float(f1_score(yv, cal_pred, labels=LABELS, average="macro", zero_division=0)),
                   "risky_precision": float(precision_score(yv, cal_pred, labels=["Risky"], average="macro", zero_division=0)),
                   "risky_recall": float(recall_score(yv, cal_pred, labels=["Risky"], average="macro", zero_division=0)),
                   "risky_predicted_positive_coverage": coverage,
                   "risky_true_positive_coverage": float(((risky_true) & risky_pred).sum() / max(1, risky_true.sum())),
                   "risky_missed_count": int((risky_true & ~risky_pred).sum()), "risky_false_positive_count": int((~risky_true & risky_pred).sum()),
                   **probability_diagnostics(yv, cal_classes, cal_prob),
                   "locked_test_used": False, "probability_warning": "Calibration is a validation diagnostic; not a legal-risk probability or guarantee."}
    (out / "calibration_validation.json").write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    pd.DataFrame(cal_prob, columns=[f"probability_{label}" for label in cal_classes]).assign(
        point_id=valid.point_id.to_numpy(), true_label=yv, predicted_label=cal_pred).to_csv(out / "calibration_validation_probabilities.csv", index=False)

    # Equal-frequency reliability bins and soft voting over LR and calibrated SVC.
    lr_classes = list(lr_full.classes_)
    lr_prob = lr_full.predict_proba(Xvalid)
    if lr_classes != cal_classes:
        raise RuntimeError("Class order differs between LR and calibrated SVC")
    soft_prob = 0.5 * (lr_prob + cal_prob)
    soft_pred = np.asarray(cal_classes)[np.argmax(soft_prob, axis=1)]
    soft_metrics = {"model": "soft_vote_lr_plus_sigmoid_svc", "split": "validation", **score(yv, soft_pred),
                    **probability_diagnostics(yv, cal_classes, soft_prob)}
    val_rows.append(soft_metrics)
    predictions["soft_vote_lr_plus_sigmoid_svc_prediction"] = soft_pred
    pd.DataFrame(val_rows).to_csv(out / "validation_ensemble_metrics.csv", index=False)
    predictions.to_csv(out / "validation_ensemble_predictions.csv", index=False)
    pd.DataFrame(soft_prob, columns=[f"probability_{label}" for label in cal_classes]).assign(
        point_id=valid.point_id.to_numpy(), true_label=yv, predicted_label=soft_pred).to_csv(out / "soft_vote_validation_probabilities.csv", index=False)
    reliability = reliability_rows(yv, cal_prob, cal_classes, "sigmoid_calibrated_svc")
    reliability.extend(reliability_rows(yv, lr_prob, cal_classes, "logistic_regression"))
    reliability.extend(reliability_rows(yv, soft_prob, cal_classes, "soft_vote_lr_plus_sigmoid_svc"))
    pd.DataFrame(reliability).to_csv(out / "risky_probability_reliability.csv", index=False)
    print(f"{protocol} group-fold sigmoid calibration complete", flush=True)

    # Unsupervised training-only PCA and KMeans; labels are attached only afterward for description.
    ids = train.point_id.astype(int).to_numpy()
    if not set(ids).issubset(vectors):
        raise RuntimeError("Missing embeddings for clustering")
    X = np.stack([vectors[int(i)] for i in ids])
    pca = PCA(n_components=2, svd_solver="full", random_state=SEED)
    coordinates = pca.fit_transform(X)
    pd.DataFrame({"point_id": ids, "pc1": coordinates[:, 0], "pc2": coordinates[:, 1], "label_for_description_only": y,
                  "explained_variance_ratio_pc1": pca.explained_variance_ratio_[0],
                  "explained_variance_ratio_pc2": pca.explained_variance_ratio_[1]}).to_csv(out / "pca_train_coordinates.csv", index=False)
    cluster_summaries = []
    cluster_assignments = []
    sample_rng = np.random.default_rng(SEED)
    sample_ix = np.sort(sample_rng.choice(len(X), size=min(2500, len(X)), replace=False))
    for k in (3, 5, 8, 12):
        seed_labels, seed_inertia = [], []
        for seed in (11, 29, 47):
            model = KMeans(n_clusters=k, n_init=10, random_state=seed, max_iter=300)
            labels = model.fit_predict(X)
            seed_labels.append(labels)
            seed_inertia.append(float(model.inertia_))
        ari = [adjusted_rand_score(seed_labels[0], other) for other in seed_labels[1:]]
        chosen_labels = seed_labels[0]
        sizes = pd.Series(chosen_labels).value_counts().sort_index()
        sampled_silhouette = float(silhouette_score(X[sample_ix], chosen_labels[sample_ix], metric="cosine"))
        for cluster_id, size in sizes.items():
            mask = chosen_labels == cluster_id
            values, counts = np.unique(y[mask], return_counts=True)
            label_counts = dict(zip(values.tolist(), counts.tolist()))
            example_ix = np.flatnonzero(mask)[:3]
            cluster_summaries.append({"k": k, "cluster": int(cluster_id), "rows": int(size),
                                      "risk_label_counts_descriptive_only": json.dumps(label_counts, sort_keys=True),
                                      "representative_point_ids": json.dumps(ids[example_ix].astype(int).tolist()),
                                      "representative_training_clauses": json.dumps(train.iloc[example_ix].quote_text.astype(str).tolist(), ensure_ascii=False),
                                      "mean_inertia_across_seeds": float(np.mean(seed_inertia)),
                                      "seed_inertia_sd": float(np.std(seed_inertia, ddof=1)), "mean_pairwise_ARI": float(np.mean(ari)),
                                      "sampled_cosine_silhouette": sampled_silhouette})
        cluster_assignments.append(pd.DataFrame({"point_id": ids, "k": k, "cluster": chosen_labels, "label_for_description_only": y}))
        print(f"{protocol} KMeans k={k} mean ARI={np.mean(ari):.3f}", flush=True)
    pd.DataFrame(cluster_summaries).to_csv(out / "kmeans_cluster_summary.csv", index=False)
    pd.concat(cluster_assignments, ignore_index=True).to_csv(out / "kmeans_train_assignments.csv", index=False)

    metadata = {"run_id": f"ensemble_calibration_{protocol}_v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "protocol": protocol, "split_id": split_meta["split_id"], "dataset_sha256": split_meta["dataset_sha256"],
                "locked_test_used": False, "selection_metric": "macro F1", "group_column": group_col,
                "folds": [int(fold) for fold in folds], "train_rows": len(train), "validation_rows": len(valid),
                "oof_ensemble": "fold-local word TF-IDF LR and LinearSVC margins; hard vote; LogisticRegression meta-model fitted on OOF margins",
                "calibration": "sigmoid calibrated LinearSVC with fixed group folds; validation only",
                "clustering": "MiniLM-L6-v2 normalized embeddings; training partition only; k=3,5,8,12; three independent seeds; ARI stability",
                "pca": "two-component PCA for exploratory train-only projection; supervised PCA comparisons are in remaining_feature experiment",
                "embedding_cache": embed_meta}
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    print(f"Saved {protocol} ensemble/calibration/clustering to {out}", flush=True)


def main() -> None:
    vectors, metadata = get_vectors()
    for protocol in ("primary", "clause"):
        run_protocol(protocol, vectors, metadata)


if __name__ == "__main__":
    main()

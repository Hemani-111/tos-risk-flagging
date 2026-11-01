"""Evaluate Logistic Regression probability quality and CV-derived review coverage."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102


def calibration_summary(y: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    index = {label: i for i, label in enumerate(LABELS)}
    truth = np.zeros_like(probabilities)
    truth[np.arange(len(y)), [index[value] for value in y]] = 1.0
    confidence = probabilities.max(axis=1)
    predicted = np.asarray(LABELS)[probabilities.argmax(axis=1)]
    edges = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (confidence >= lower) & ((confidence < upper) if upper < 1 else (confidence <= upper))
        if mask.any():
            ece += mask.mean() * abs(float((predicted[mask] == y[mask]).mean()) - float(confidence[mask].mean()))
    return {
        "rows": int(len(y)), "accuracy": float(accuracy_score(y, predicted)),
        "multiclass_brier_score": float(np.square(probabilities - truth).sum(axis=1).mean()),
        "log_loss": float(-np.log(np.clip(probabilities[np.arange(len(y)), [index[value] for value in y]], 1e-15, 1.0)).mean()),
        "top_label_ece_10_bins": float(ece),
        "mean_top_label_confidence": float(confidence.mean()),
    }


def main() -> None:
    data, metadata = load_split_bundle("primary", ROOT)
    train = data.loc[data["primary_include"] & data["primary_partition"].eq("train")].copy()
    validation = data.loc[data["primary_include"] & data["primary_partition"].eq("validation")].copy()
    fold_col = "primary_cv_fold"
    y_train, y_val = train["label"].to_numpy(), validation["label"].to_numpy()
    oof = np.zeros((len(train), len(LABELS)), dtype=np.float64)
    fold_timing = []
    for fold in sorted(train[fold_col].unique()):
        fit_idx = np.flatnonzero(train[fold_col].to_numpy() != fold)
        held_idx = np.flatnonzero(train[fold_col].to_numpy() == fold)
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000,
                                     sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
        start = time.perf_counter()
        x_fit = vectorizer.fit_transform(train.iloc[fit_idx]["quote_text"].fillna("").astype(str))
        x_held = vectorizer.transform(train.iloc[held_idx]["quote_text"].fillna("").astype(str))
        model = LogisticRegression(C=10.0, class_weight="balanced", max_iter=1500, random_state=SEED)
        model.fit(x_fit, y_train[fit_idx])
        fold_timing.append(time.perf_counter() - start)
        raw = model.predict_proba(x_held)
        for column, label in enumerate(model.classes_):
            oof[held_idx, LABELS.index(label)] = raw[:, column]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000,
                                 sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
    x_train = vectorizer.fit_transform(train["quote_text"].fillna("").astype(str))
    x_val = vectorizer.transform(validation["quote_text"].fillna("").astype(str))
    final_model = LogisticRegression(C=10.0, class_weight="balanced", max_iter=1500, random_state=SEED)
    final_model.fit(x_train, y_train)
    raw_val = final_model.predict_proba(x_val)
    p_val = np.zeros((len(validation), len(LABELS)), dtype=np.float64)
    for column, label in enumerate(final_model.classes_):
        p_val[:, LABELS.index(label)] = raw_val[:, column]
    oof_metrics = calibration_summary(y_train, oof)
    val_metrics = calibration_summary(y_val, p_val)

    out = ROOT / "results" / "uncertainty" / "v1"
    out.mkdir(parents=True, exist_ok=True)
    oof_frame = pd.DataFrame({"point_id": train["point_id"].to_numpy(), "true_label": y_train,
                              "predicted_label": np.asarray(LABELS)[oof.argmax(axis=1)], "confidence": oof.max(axis=1), "split": "training_oof"})
    val_frame = pd.DataFrame({"point_id": validation["point_id"].to_numpy(), "true_label": y_val,
                              "predicted_label": np.asarray(LABELS)[p_val.argmax(axis=1)], "confidence": p_val.max(axis=1), "split": "validation"})
    for idx, label in enumerate(LABELS):
        oof_frame[f"probability_{label}"] = oof[:, idx]
        val_frame[f"probability_{label}"] = p_val[:, idx]
    oof_frame.to_csv(out / "training_oof_probabilities.csv", index=False)
    val_frame.to_csv(out / "validation_probabilities.csv", index=False)

    risk_rows = []
    for target_coverage in (0.80, 0.90, 0.95):
        threshold = float(np.quantile(oof.max(axis=1), 1.0 - target_coverage))
        for split_name, y, probs in (("training_oof", y_train, oof), ("validation", y_val, p_val)):
            confidence = probs.max(axis=1)
            predicted = np.asarray(LABELS)[probs.argmax(axis=1)]
            accepted = confidence >= threshold
            coverage = float(accepted.mean())
            risk = float((predicted[accepted] != y[accepted]).mean()) if accepted.any() else float("nan")
            risk_rows.append({"target_coverage_from_oof": target_coverage, "confidence_threshold": threshold,
                              "evaluated_split": split_name, "coverage": coverage, "selective_error_rate": risk,
                              "accepted_rows": int(accepted.sum()), "total_rows": int(len(y))})
    risk_curve = pd.DataFrame(risk_rows)
    risk_curve.to_csv(out / "risk_coverage.csv", index=False)
    (out / "probability_metrics.json").write_text(json.dumps({
        "model": "balanced LogisticRegression C=10 with word unigram/bigram TF-IDF",
        "protocol": "primary unseen-service", "split_id": metadata["split_id"], "locked_test_used": False,
        "training_oof": oof_metrics, "validation": val_metrics,
        "fold_fit_seconds_including_vectorization": fold_timing,
        "probabilities_calibrated": False,
        "interpretation": "Raw probabilities are evaluated but not calibrated. Confidence cutoffs are chosen from training OOF only; validation coverage/error are an untouched development check, not a final test estimate.",
    }, indent=2), encoding="utf-8")

    # A top-label reliability diagram on the held-out validation partition.
    confidence, predicted = p_val.max(axis=1), np.asarray(LABELS)[p_val.argmax(axis=1)]
    edges = np.linspace(0.0, 1.0, 11)
    mean_conf, observed_acc, sizes = [], [], []
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (confidence >= lower) & ((confidence < upper) if upper < 1 else (confidence <= upper))
        if mask.any():
            mean_conf.append(float(confidence[mask].mean()))
            observed_acc.append(float((predicted[mask] == y_val[mask]).mean()))
            sizes.append(int(mask.sum()))
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="#888888", label="Perfect calibration")
    ax.plot(mean_conf, observed_acc, marker="o", color="#4c72b0", label="Validation")
    for x, y, n in zip(mean_conf, observed_acc, sizes):
        ax.annotate(str(n), (x, y), textcoords="offset points", xytext=(4, 4), fontsize=8)
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Mean top-label confidence", ylabel="Observed accuracy", title="Raw Logistic Regression reliability")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "validation_reliability.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"training_oof": oof_metrics, "validation": val_metrics, "outputs": str(out)}, indent=2))


if __name__ == "__main__":
    main()

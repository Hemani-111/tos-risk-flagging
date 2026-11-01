"""Refit CV-selected linear candidates on training and score validation once."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
SEED = 20261102
SELECTED = {
    "primary": [("linear_svm", 1.0), ("logistic_regression", 10.0)],
    "clause": [("linear_svm", 1.0), ("logistic_regression", 10.0)],
}


def main() -> None:
    for protocol, configurations in SELECTED.items():
        frame, metadata = load_split_bundle(protocol, ROOT)
        partition = f"{protocol}_partition"
        included = f"{protocol}_include"
        train = frame.loc[frame[included] & frame[partition].eq("train")]
        validation = frame.loc[frame[included] & frame[partition].eq("validation")]
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000,
                              sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
        started = time.perf_counter()
        x_train = vec.fit_transform(train["quote_text"].fillna("").astype(str))
        x_validation = vec.transform(validation["quote_text"].fillna("").astype(str))
        vectorizer_seconds = time.perf_counter() - started
        result_rows, prediction_frames = [], []
        for family, c_value in configurations:
            model = (LogisticRegression(C=c_value, class_weight="balanced", max_iter=1500, random_state=SEED)
                     if family == "logistic_regression" else
                     LinearSVC(C=c_value, class_weight="balanced", random_state=SEED, max_iter=5000))
            fit_start = time.perf_counter()
            model.fit(x_train, train["label"])
            fit_seconds = time.perf_counter() - fit_start
            predict_start = time.perf_counter()
            predicted = model.predict(x_validation)
            predict_seconds = time.perf_counter() - predict_start
            report = classification_report(validation["label"], predicted, labels=LABELS, output_dict=True, zero_division=0)
            result_rows.append({
                "protocol": protocol, "model": family, "C": c_value,
                "class_weight": "balanced", "representation": "word_tfidf_unigram_bigram",
                "macro_f1": f1_score(validation["label"], predicted, labels=LABELS, average="macro", zero_division=0),
                "risky_precision": precision_score(validation["label"], predicted, labels=["Risky"], average="macro", zero_division=0),
                "risky_recall": recall_score(validation["label"], predicted, labels=["Risky"], average="macro", zero_division=0),
                "risky_false_positive_count": int(((validation["label"].to_numpy() != "Risky") & (predicted == "Risky")).sum()),
                "risky_false_negative_count": int(((validation["label"].to_numpy() == "Risky") & (predicted != "Risky")).sum()),
                **{f"{label.lower()}_precision": report[label]["precision"] for label in LABELS},
                **{f"{label.lower()}_recall": report[label]["recall"] for label in LABELS},
                **{f"{label.lower()}_f1": report[label]["f1-score"] for label in LABELS},
                "fit_seconds": fit_seconds, "vectorizer_fit_seconds": vectorizer_seconds,
                "predict_seconds": predict_seconds, "predict_ms_per_row": predict_seconds * 1000 / len(validation),
                "train_rows": len(train), "validation_rows": len(validation), "locked_test_used": False,
            })
            predictions = pd.DataFrame({"point_id": validation["point_id"].to_numpy(), "true_label": validation["label"].to_numpy(),
                                        "predicted_label": predicted, "protocol": protocol, "model": family, "C": c_value})
            prediction_frames.append(predictions)
            cm = confusion_matrix(validation["label"], predicted, labels=LABELS)
            out = ROOT / "results" / "experiments" / f"benchmark_{protocol}_wordtfidf_v1"
            pd.DataFrame(cm, index=[f"true_{x}" for x in LABELS], columns=[f"pred_{x}" for x in LABELS]).to_csv(out / f"tuned_{family}_confusion.csv")
        output = ROOT / "results" / "experiments" / f"tuned_validation_{protocol}_v1"
        output.mkdir(parents=True, exist_ok=True)
        metrics = pd.DataFrame(result_rows).sort_values("macro_f1", ascending=False)
        metrics.to_csv(output / "validation_metrics.csv", index=False)
        pd.concat(prediction_frames, ignore_index=True).to_csv(output / "validation_predictions.csv", index=False)
        metadata_out = {
            "protocol": protocol, "split_id": metadata["split_id"], "dataset_sha256": metadata["dataset_sha256"],
            "selection_source": f"results/experiments/grouped_cv_{protocol}_linear_features_v1/cv_tuning_metrics.csv",
            "selection_partition": "fixed grouped CV inside train", "scoring_partition": "validation",
            "locked_test_used": False, "training_rows": len(train), "validation_rows": len(validation),
            "vectorizer_fit_seconds": vectorizer_seconds, "vocabulary_size": len(vec.vocabulary_),
            "selected_parameters": configurations,
        }
        (output / "run_metadata.json").write_text(json.dumps(metadata_out, indent=2), encoding="utf-8")
        print(protocol, metrics[["model", "C", "macro_f1", "risky_precision", "risky_recall"]].to_string(index=False))


if __name__ == "__main__":
    main()

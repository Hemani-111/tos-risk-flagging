"""Compare word TF-IDF with/without training-fold-scaled lexical descriptors."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
FEATURES = ["log_chars", "log_words", "mean_word_length", "log_sentences", "readability_heuristic", "contains_negation"]
SEED = 20261102


def describe(text: str) -> list[float]:
    tokens = re.findall(r"[^\W\d_]+|\d+", text.lower(), flags=re.UNICODE)
    words = [x for x in tokens if not x.isdigit()]
    sentences = max(1, len([s for s in re.split(r"[.!?]+", text) if s.strip()]))
    syllables = 0
    for word in words:
        groups = len(re.findall(r"[aeiouy]+", re.sub(r"[^a-z]", "", word)))
        count = groups - (word.endswith("e") and groups > 1 and not word.endswith(("le", "ye")))
        syllables += max(1, count)
    ease = 206.835 - 1.015 * (len(words) / sentences) - 84.6 * (syllables / max(1, len(words))) if words else 0
    negation = int(bool(re.search(r"\b(?:not|no|never|without|neither|nor|cannot|can't|don't|doesn't|didn't|won't|isn't|aren't|wasn't|weren't)\b", text.lower())))
    return [np.log1p(len(text)), np.log1p(len(words)), float(np.mean([len(w) for w in words])) if words else 0.0,
            np.log1p(sentences), ease, negation]


def main() -> None:
    all_results = []
    for protocol in ("primary", "clause"):
        data, _ = load_split_bundle(protocol, ROOT)
        part, include, fold = f"{protocol}_partition", f"{protocol}_include", f"{protocol}_cv_fold"
        train = data.loc[data[include] & data[part].eq("train")].copy()
        text = train["quote_text"].fillna("").astype(str).tolist()
        raw_features = np.asarray([describe(t) for t in text], dtype=np.float32)
        proto_rows = []
        prediction_frames = []
        for fold_id in sorted(train[fold].unique()):
            fit_idx = np.flatnonzero(train[fold].to_numpy() != fold_id)
            val_idx = np.flatnonzero(train[fold].to_numpy() == fold_id)
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000,
                                         sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
            x_fit = vectorizer.fit_transform([text[i] for i in fit_idx])
            x_val = vectorizer.transform([text[i] for i in val_idx])
            scaler = StandardScaler()
            lexical_fit = scaler.fit_transform(raw_features[fit_idx]).astype(np.float32)
            lexical_val = scaler.transform(raw_features[val_idx]).astype(np.float32)
            variants = {
                "word_tfidf": (x_fit, x_val),
                "lexical_only": (csr_matrix(lexical_fit), csr_matrix(lexical_val)),
                "word_tfidf_plus_lexical": (
                    hstack([x_fit, csr_matrix(lexical_fit)], format="csr"),
                    hstack([x_val, csr_matrix(lexical_val)], format="csr"),
                ),
            }
            for variant, (xtr, xva) in variants.items():
                for family, c in (("linear_svm", 1.0), ("logistic_regression", 10.0)):
                    model = LinearSVC(C=c, class_weight="balanced", random_state=SEED, max_iter=5000) if family == "linear_svm" else LogisticRegression(C=c, class_weight="balanced", max_iter=1500, random_state=SEED)
                    started = time.perf_counter()
                    model.fit(xtr, train.iloc[fit_idx]["label"])
                    fit_seconds = time.perf_counter() - started
                    pred = model.predict(xva)
                    score = f1_score(train.iloc[val_idx]["label"], pred, labels=LABELS, average="macro", zero_division=0)
                    proto_rows.append({"protocol": protocol, "fold": int(fold_id), "feature_set": variant,
                                       "model": family, "C": c, "macro_f1": float(score),
                                       "fit_seconds": fit_seconds, "feature_count": xtr.shape[1]})
                    prediction_frames.append(pd.DataFrame({"point_id": train.iloc[val_idx]["point_id"].to_numpy(),
                                                           "fold": int(fold_id), "true_label": train.iloc[val_idx]["label"].to_numpy(),
                                                           "predicted_label": pred, "feature_set": variant, "model": family}))
        result = pd.DataFrame(proto_rows)
        output = ROOT / "results" / "experiments" / f"lexical_ablation_{protocol}_v1"
        output.mkdir(parents=True, exist_ok=True)
        result.to_csv(output / "cv_fold_metrics.csv", index=False)
        pd.concat(prediction_frames, ignore_index=True).to_csv(output / "cv_predictions.csv", index=False)
        summary = result.groupby(["feature_set", "model", "C"], as_index=False).agg(mean_macro_f1=("macro_f1", "mean"), std_macro_f1=("macro_f1", "std"), mean_fit_seconds=("fit_seconds", "mean"), feature_count=("feature_count", "first"))
        summary.to_csv(output / "cv_summary.csv", index=False)
        (output / "run_metadata.json").write_text(json.dumps({"protocol": protocol, "features": FEATURES,
            "scaling": "StandardScaler fitted separately within each training fold", "text_features": "word TF-IDF unigram/bigram, min_df=2, max_features=60000",
            "locked_test_used": False, "rows": len(train), "fold_column": fold, "grouped_by": "frozen manifest folds"}, indent=2), encoding="utf-8")
        all_results.extend(summary.to_dict("records"))
        print(protocol, summary.to_string(index=False))
    pd.DataFrame(all_results).to_csv(ROOT / "results" / "experiments" / "lexical_ablation_summary_v1.csv", index=False)


if __name__ == "__main__":
    main()

"""Measure token-coefficient stability across the fixed development folds."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

SEED = 20261102
LABELS = ["Risky", "Neutral", "Safe"]


def main() -> None:
    for protocol in ("primary", "clause"):
        data, split_meta = load_development_bundle(protocol, ROOT)
        part, include, fold_col = f"{protocol}_partition", f"{protocol}_include", f"{protocol}_cv_fold"
        train = data.loc[data[include] & data[part].eq("train")].reset_index(drop=True)
        folds = sorted(train[fold_col].unique().tolist())
        if len(folds) != 3:
            raise RuntimeError("Expected three fixed training folds")
        out = ROOT / "results/experiments" / f"linear_feature_stability_{protocol}_v1"
        out.mkdir(parents=True, exist_ok=True)
        fold_features: dict[str, dict[int, list[tuple[str, float]]]] = {label: {} for label in LABELS}
        rows = []
        for fold in folds:
            fit = train[fold_col].ne(fold)
            texts = train.loc[fit, "quote_text"].fillna("").astype(str).tolist()
            y = train.loc[fit, "label"].to_numpy()
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000,
                                         sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
            X = vectorizer.fit_transform(texts)
            model = LinearSVC(C=1.0, class_weight="balanced", random_state=SEED).fit(X, y)
            names = vectorizer.get_feature_names_out()
            for class_index, label in enumerate(model.classes_):
                coefficients = model.coef_[class_index]
                top = np.argsort(np.abs(coefficients))[-200:][::-1]
                items = []
                for rank, index in enumerate(top, start=1):
                    token, coefficient = str(names[index]), float(coefficients[index])
                    items.append((token, coefficient))
                    rows.append({"protocol": protocol, "fold": int(fold), "class": str(label),
                                 "rank_by_absolute_coefficient": rank, "token": token,
                                 "coefficient": coefficient, "absolute_coefficient": abs(coefficient)})
                fold_features[str(label)][int(fold)] = items
            print(f"{protocol} coefficient fit fold={fold} done", flush=True)

        summaries = {}
        for label in LABELS:
            top_sets = [set(token for token, _ in fold_features[label][int(fold)][:100]) for fold in folds]
            pairwise_jaccard = []
            for left_index in range(len(top_sets)):
                for right_index in range(left_index + 1, len(top_sets)):
                    union = top_sets[left_index] | top_sets[right_index]
                    pairwise_jaccard.append(len(top_sets[left_index] & top_sets[right_index]) / max(1, len(union)))
            summaries[label] = {
                "top_100_pairwise_jaccard_mean": float(np.mean(pairwise_jaccard)),
                "top_100_pairwise_jaccard_sd": float(np.std(pairwise_jaccard, ddof=1)),
                "top_100_token_counts_per_fold": [len(values) for values in top_sets],
                "interpretation_limit": "Coefficient associations are not causal explanations; folds use different fitted vocabularies.",
            }
        pd.DataFrame(rows).to_csv(out / "top_200_features_per_fold.csv", index=False)
        metadata = {"run_id": f"linear_feature_stability_{protocol}_v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    "protocol": protocol, "split_id": split_meta["split_id"], "dataset_sha256": split_meta["dataset_sha256"],
                    "locked_test_used": False, "folds": [int(fold) for fold in folds], "group_column": "service_component" if protocol == "primary" else "text_component",
                    "method": "Top 200 absolute LinearSVC coefficients per class from independent fold-local word unigram/bigram TF-IDF fits; top-100 token-set Jaccard across folds.",
                    "classes": summaries}
        (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"Saved {protocol} feature stability to {out}", flush=True)


if __name__ == "__main__":
    main()

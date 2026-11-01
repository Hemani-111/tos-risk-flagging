"""Tune promising linear text models on the manifest's fixed training folds."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
CS = [0.1, 1.0, 10.0]
SEED = 20261102
REPRESENTATIONS = {
    "word_unigram": {"analyzer": "word", "ngram_range": (1, 1), "max_features": 60000, "min_df": 2},
    "word_uni_bi": {"analyzer": "word", "ngram_range": (1, 2), "max_features": 60000, "min_df": 2},
    "char_wb_3_5": {"analyzer": "char_wb", "ngram_range": (3, 5), "max_features": 80000, "min_df": 3},
}


def main() -> None:
    output_root = ROOT / "results" / "experiments"
    all_runs: list[dict[str, object]] = []
    for protocol in ("primary", "clause"):
        bundle, metadata = load_split_bundle(protocol, ROOT)
        part_col, include_col, fold_col = f"{protocol}_partition", f"{protocol}_include", f"{protocol}_cv_fold"
        group_col = "service_component" if protocol == "primary" else "text_component"
        train = bundle.loc[bundle[include_col] & bundle[part_col].eq("train")].copy()
        run_id = f"grouped_cv_{protocol}_linear_features_v1"
        output = output_root / run_id
        output.mkdir(parents=True, exist_ok=True)
        folds = sorted(train[fold_col].unique())
        if len(folds) != 3 or train.groupby(group_col)[fold_col].nunique().max() != 1:
            raise RuntimeError(f"Unexpected fixed CV fold assignment in {protocol}")
        protocol_results: list[dict[str, object]] = []
        prediction_parts: list[pd.DataFrame] = []
        for representation, vectorizer_params in REPRESENTATIONS.items():
            for family in ("logistic_regression", "linear_svm"):
                for c_value in CS:
                    fold_scores = []
                    fit_times = []
                    for fold in folds:
                        fit_rows = train.loc[train[fold_col].ne(fold)]
                        held_rows = train.loc[train[fold_col].eq(fold)]
                        vectorizer = TfidfVectorizer(
                            **vectorizer_params, max_df=0.99, sublinear_tf=True,
                            strip_accents="unicode", dtype=np.float32,
                        )
                        start = time.perf_counter()
                        x_fit = vectorizer.fit_transform(fit_rows["quote_text"].fillna("").astype(str))
                        x_held = vectorizer.transform(held_rows["quote_text"].fillna("").astype(str))
                        if family == "logistic_regression":
                            model = LogisticRegression(C=c_value, max_iter=1500, class_weight="balanced", random_state=SEED)
                        else:
                            model = LinearSVC(C=c_value, class_weight="balanced", random_state=SEED, max_iter=5000)
                        with warnings.catch_warnings(record=True) as caught:
                            warnings.simplefilter("always")
                            model.fit(x_fit, fit_rows["label"])
                        fit_seconds = time.perf_counter() - start
                        prediction = model.predict(x_held)
                        fold_f1 = f1_score(held_rows["label"], prediction, labels=LABELS, average="macro", zero_division=0)
                        fold_scores.append(float(fold_f1))
                        fit_times.append(fit_seconds)
                        prediction_parts.append(pd.DataFrame({
                            "point_id": held_rows["point_id"].to_numpy(),
                            "cv_fold": int(fold), "true_label": held_rows["label"].to_numpy(),
                            "predicted_label": prediction, "protocol": protocol,
                            "representation": representation, "model": family, "C": c_value,
                        }))
                        if caught:
                            # Preserve only actual fitting diagnostics without aborting the grid.
                            warning_text = [f"{w.category.__name__}: {w.message}" for w in caught]
                        else:
                            warning_text = []
                    protocol_results.append({
                        "protocol": protocol, "representation": representation, "model": family,
                        "C": c_value, "class_weight": "balanced", "fold_macro_f1": fold_scores,
                        "mean_macro_f1": float(np.mean(fold_scores)), "std_macro_f1": float(np.std(fold_scores, ddof=1)),
                        "mean_fit_and_vectorize_seconds": float(np.mean(fit_times)),
                        "folds": [int(f) for f in folds], "fold_warnings_last": warning_text,
                    })
                    print(f"{protocol} {representation} {family} C={c_value}: CV macro F1={np.mean(fold_scores):.4f} ± {np.std(fold_scores, ddof=1):.4f}")
        results = pd.DataFrame(protocol_results).sort_values("mean_macro_f1", ascending=False)
        results.to_csv(output / "cv_tuning_metrics.csv", index=False)
        pd.concat(prediction_parts, ignore_index=True).to_csv(output / "cv_predictions.csv", index=False)
        row = {
            "run_id": run_id, "protocol": protocol, "split_id": metadata["split_id"],
            "dataset_sha256": metadata["dataset_sha256"], "locked_test_used": False,
            "selection_partition": "fixed grouped CV folds within training only",
            "seed": SEED, "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "sklearn_version": sklearn.__version__, "training_rows": len(train),
            "training_point_ids_sha256": hashlib.sha256("\n".join(map(str, train["point_id"])).encode()).hexdigest(),
            "fold_column": fold_col, "group_column": group_col, "folds": [int(f) for f in folds],
            "grid": {"representations": REPRESENTATIONS, "families": ["logistic_regression", "linear_svm"], "C": CS, "class_weight": "balanced"},
            "best_cv_row": results.iloc[0].to_dict(),
        }
        (output / "run_metadata.json").write_text(json.dumps(row, indent=2, default=str), encoding="utf-8")
        all_runs.extend(protocol_results)
    pd.DataFrame(all_runs).to_csv(output_root / "grouped_cv_summary_v1.csv", index=False)


if __name__ == "__main__":
    main()

"""Generate frontend model-comparison data from verified canonical comparison CSV.

Single source of truth: results/comparison/{primary,clause}/comparison.csv
Outputs: frontend/lib/comparisonData.ts (importable by the research page)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "lib" / "comparisonData.ts"

# Friendly display names.
DISPLAY = {
    "linear_svm": "Linear SVM",
    "logistic_regression": "Logistic Regression",
    "rbf_svm": "SVM — RBF",
    "multinomial_nb": "Multinomial Naive Bayes",
    "gradient_boosting": "Gradient Boosting",
    "knn": "K-Nearest Neighbours",
    "random_forest": "Random Forest",
    "decision_tree": "Decision Tree",
}

STATUS = {
    "linear_svm": "Production model",
    "logistic_regression": "Baseline",
    "rbf_svm": "Baseline",
    "multinomial_nb": "Baseline",
    "gradient_boosting": "End-semester addition",
    "knn": "End-semester addition",
    "random_forest": "End-semester addition",
    "decision_tree": "End-semester addition",
}

REPR_LABEL = {
    "sparse_word_tfidf_uni_bi": "Sparse word unigram/bigram TF-IDF",
    "dense_svd100": "Dense TF-IDF + TruncatedSVD-100",
}


def fmt(x, nd=4):
    return f"{float(x):.{nd}f}"


def main():
    rows = []
    for protocol in ("primary", "clause"):
        csv_path = ROOT / "results" / "comparison" / protocol / "comparison.csv"
        df = pd.read_csv(csv_path)
        for _, r in df.iterrows():
            model = r["model"]
            rows.append({
                "protocol": protocol.title().replace("_", " "),
                "model": DISPLAY[model],
                "config": _config_summary(r),
                "representation": REPR_LABEL[r["representation"]],
                "cvMacroF1": fmt(r["cv_macro_f1_mean"]),
                "cvMacroF1Std": fmt(r["cv_macro_f1_std"]),
                "valMacroF1": fmt(r["macro_f1"]),
                "accuracy": fmt(r["accuracy"]),
                "balancedAccuracy": fmt(r["balanced_accuracy"]),
                "riskyPrecision": fmt(r["risky_precision"]),
                "riskyRecall": fmt(r["risky_recall"]),
                "riskyFP": int(r["risky_false_positives"]),
                "riskyFN": int(r["risky_false_negatives"]),
                "trainMacroF1": fmt(r["train_macro_f1"]),
                "status": STATUS[model],
                "fitSeconds": fmt(r["final_fit_seconds"]),
                "predictSeconds": fmt(r["final_predict_seconds"]),
            })

    lines = [
        "// Auto-generated from results/comparison/{primary,clause}/comparison.csv",
        "// DO NOT EDIT BY HAND — regenerate with scripts/generate_frontend_data.py",
        "",
        "export type ComparisonRow = {",
        "  protocol: string;",
        "  model: string;",
        "  config: string;",
        "  representation: string;",
        "  cvMacroF1: string;",
        "  cvMacroF1Std: string;",
        "  valMacroF1: string;",
        "  accuracy: string;",
        "  balancedAccuracy: string;",
        "  riskyPrecision: string;",
        "  riskyRecall: string;",
        "  riskyFP: number;",
        "  riskyFN: number;",
        "  trainMacroF1: string;",
        "  status: string;",
        "  fitSeconds: string;",
        "  predictSeconds: string;",
        "};",
        "",
        "export const COMPARISON_ROWS: ComparisonRow[] = " + json.dumps(rows, indent=2) + ";",
        "",
        "// Production model identity (single source of truth).",
        "export const PRODUCTION_MODEL = {",
        '  name: "Linear SVM",',
        '  version: "linear-svc-primary-v2",',
        '  path: "models/releases/linear-svc-primary-v2/",',
        '  representation: "Sparse word unigram/bigram TF-IDF",',
        '  selectionMetric: "Validation macro F1",',
        "};",
        "",
        "// Development-only note: CV is computed on fixed group-respecting folds;",
        "// validation is held-out after refitting on all training data. Test is not used.",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} with {len(rows)} rows")


def _config_summary(r) -> str:
    params = json.loads(r["selected_parameters"])
    parts = []
    if "C" in params:
        parts.append(f"C={params['C']}")
    if "class_weight" in params and params["class_weight"]:
        parts.append(f"class_weight={params['class_weight']}")
    if "alpha" in params:
        parts.append(f"alpha={params['alpha']}")
    if "gamma" in params:
        parts.append(f"gamma={params['gamma']}")
    if "max_depth" in params:
        parts.append(f"max_depth={params['max_depth']}")
    if "min_samples_leaf" in params:
        parts.append(f"min_samples_leaf={params['min_samples_leaf']}")
    if "n_estimators" in params:
        parts.append(f"n_estimators={params['n_estimators']}")
    if "n_neighbors" in params:
        parts.append(f"k={params['n_neighbors']}")
    if "max_iter" in params:
        parts.append(f"max_iter={params['max_iter']}")
    if "learning_rate" in params:
        parts.append(f"lr={params['learning_rate']}")
    if "max_leaf_nodes" in params:
        parts.append(f"leaves={params['max_leaf_nodes']}")
    if "ccp_alpha" in params:
        parts.append(f"ccp_alpha={params['ccp_alpha']}")
    if "max_features" in params:
        parts.append(f"max_features={params['max_features']}")
    if "weights" in params:
        parts.append(f"weights={params['weights']}")
    if "metric" in params:
        parts.append(f"metric={params['metric']}")
    if "early_stopping" in params:
        parts.append(f"early_stopping={params['early_stopping']}")
    if "l2_regularization" in params:
        parts.append(f"l2={params['l2_regularization']}")
    if "solver" in params:
        parts.append(f"solver={params['solver']}")
    return ", ".join(parts)


if __name__ == "__main__":
    main()

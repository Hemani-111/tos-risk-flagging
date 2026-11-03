import pandas as pd
from pathlib import Path

ROOT = Path("A:/Projects/ToS-risk-flagging")
LABELS = ["Safe", "Neutral", "Risky"]
MODEL_ORDER = [
    "linear_svm", "logistic_regression", "multinomial_nb",
    "rbf_svm", "gradient_boosting", "knn", "random_forest", "decision_tree",
]
DISPLAY = {
    "linear_svm": "Linear SVM",
    "logistic_regression": "Logistic Regression",
    "multinomial_nb": "Multinomial NB",
    "rbf_svm": "SVM — RBF",
    "gradient_boosting": "Gradient Boosting",
    "knn": "K-Nearest Neighbours",
    "random_forest": "Random Forest",
    "decision_tree": "Decision Tree",
}

def fmt(x, nd=4):
    return f"{float(x):.{nd}f}"

def generate_table(protocol):
    df = pd.read_csv(ROOT / "results" / "comparison" / protocol / "comparison.csv")
    df = df.set_index("model").loc[MODEL_ORDER].reset_index()
    lines = []
    lines.append("| Model | Rep. | CV macro F1 (±SD) | Val macro F1 | Accuracy | Risky P | Risky R | Risky FN | Risky FP | Train macro F1 | Fit (s) |")
    lines.append("|-------|------|-------------------|--------------|----------|---------|---------|----------|----------|----------------|---------|")
    for _, r in df.iterrows():
        rep = "Sparse TF-IDF" if r["representation"] == "sparse_word_tfidf_uni_bi" else "Dense SVD-100"
        lines.append(
            f"| {DISPLAY[r['model']]} | {rep} | {fmt(r['cv_macro_f1_mean'])} ± {fmt(r['cv_macro_f1_std'])} | "
            f"{fmt(r['macro_f1'])} | {fmt(r['accuracy'])} | {fmt(r['risky_precision'])} | "
            f"{fmt(r['risky_recall'])} | {int(r['risky_false_negatives'])} | {int(r['risky_false_positives'])} | "
            f"{fmt(r['train_macro_f1'])} | {fmt(r['final_fit_seconds'])} |"
        )
    return "\n".join(lines)

print(generate_table("primary"))
print()
print(generate_table("clause"))

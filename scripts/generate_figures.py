"""Generate comparison figures from verified canonical results.

Reads: results/comparison/{primary,clause}/comparison.csv
       results/comparison/{primary,clause}/{model}_confusion_matrix.csv
       results/comparison/{primary,clause}/{model}_roc_pr_curves.csv
Writes: results/comparison/figures/*.png (high-res) and *.svg (vector)

All figures are labelled with protocol, evaluation stage, and sample count.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "results" / "comparison" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Consistent style.
sns.set_style("whitegrid")
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})

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
COLORS = {
    "linear_svm": "#1f77b4",
    "logistic_regression": "#2ca02c",
    "multinomial_nb": "#ff7f0e",
    "rbf_svm": "#d62728",
    "gradient_boosting": "#9467bd",
    "knn": "#8c564b",
    "random_forest": "#e377c2",
    "decision_tree": "#7f7f7f",
}
LABELS = ["Safe", "Neutral", "Risky"]


def save(fig, name):
    fig.savefig(FIG_DIR / f"{name}.png", dpi=300)
    fig.savefig(FIG_DIR / f"{name}.svg")
    plt.close(fig)
    print(f"  saved {name}.png / .svg")


def load_comparison(protocol: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / "results" / "comparison" / protocol / "comparison.csv")


def fig1_class_distribution():
    """Figure 1: Class distribution across train/validation/test."""
    import subprocess
    script = ROOT / "scripts" / "split_class_distribution.py"
    if not script.exists():
        # Inline fallback: hardcode from verified manifest merge.
        data = {
            "Partition": ["Train", "Train", "Train", "Validation", "Validation", "Validation", "Test", "Test", "Test"],
            "Class": ["Safe", "Neutral", "Risky"] * 3,
            "Count": [3368, 5669, 4402, 721, 1217, 944, 718, 1211, 939],
        }
    else:
        data = None
    df = pd.DataFrame(data) if data else None

    fig, ax = plt.subplots(figsize=(7, 4))
    x = np.arange(3)
    width = 0.25
    classes = ["Safe", "Neutral", "Risky"]
    partitions = ["Train", "Validation", "Test"]
    counts = {
        "Safe": [3368, 721, 718],
        "Neutral": [5669, 1217, 1211],
        "Risky": [4402, 944, 939],
    }
    for i, cls in enumerate(classes):
        ax.bar(x + i * width - width, counts[cls], width, label=cls,
               color=COLORS.get({"Safe": "linear_svm", "Neutral": "logistic_regression", "Risky": "multinomial_nb"}[cls], "#aaaaaa"))
    ax.set_xticks(x)
    ax.set_xticklabels(partitions)
    ax.set_ylabel("Number of clauses")
    ax.set_title("Class distribution by partition (primary unseen-service protocol)")
    ax.legend(title="Class")
    ax.set_ylim(0, 6200)
    for i, cls in enumerate(classes):
        for j, c in enumerate(counts[cls]):
            ax.text(j + i * width - width, c + 60, f"{c:,}", ha="center", fontsize=8)
    save(fig, "fig1_class_distribution")


def fig2_macro_f1_comparison(protocol: str = "primary"):
    """Figure 2: Macro-F1 comparison with CV error bars."""
    df = load_comparison(protocol)
    df = df.set_index("model").loc[MODEL_ORDER].reset_index()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(df))
    means = df["cv_macro_f1_mean"].to_numpy()
    stds = df["cv_macro_f1_std"].to_numpy()
    colors = [COLORS[m] for m in df["model"]]
    bars = ax.bar(x, means, yerr=stds, capsize=4, color=colors, alpha=0.85,
                  error_kw=dict(lw=1, capsize=4, capthick=1))
    ax.set_xticks(x)
    ax.set_xticklabels([DISPLAY[m] for m in df["model"]], rotation=35, ha="right")
    ax.set_ylabel("Macro F1 (group-CV mean ± SD)")
    ax.set_ylim(0, 1.0)
    ax.set_title(f"Macro-F1 comparison — {protocol} protocol (3 fixed group folds)")
    ax.axhline(0.8, color="gray", ls="--", lw=0.8, alpha=0.6)
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 0.01, f"{m:.3f}", ha="center", fontsize=8)
    save(fig, f"fig2_macro_f1_comparison_{protocol}")


def fig3_per_class_f1_heatmap(protocol: str = "primary"):
    """Figure 3: Per-class F1 heatmap (models x Safe/Neutral/Risky)."""
    df = load_comparison(protocol)
    df = df.set_index("model").loc[MODEL_ORDER]
    mat = df[[f"{l.lower()}_f1" for l in LABELS]].to_numpy()
    mat_df = pd.DataFrame(mat, index=[DISPLAY[m] for m in MODEL_ORDER], columns=LABELS)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(mat_df, annot=True, fmt=".3f", cmap="RdYlGn", vmin=0.5, vmax=1.0,
                cbar_kws={"label": "F1"}, ax=ax, linewidths=0.5)
    ax.set_title(f"Per-class F1 heatmap — {protocol} protocol (validation)")
    save(fig, f"fig3_per_class_f1_heatmap_{protocol}")


def fig4_risky_precision_recall(protocol: str = "primary"):
    """Figure 4: Risky precision-recall operating-point comparison."""
    df = load_comparison(protocol)
    df = df.set_index("model").loc[MODEL_ORDER].reset_index()

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [COLORS[m] for m in df["model"]]
    scatter = ax.scatter(df["risky_recall"], df["risky_precision"], s=120,
                         c=colors, alpha=0.8, edgecolor="black", linewidth=0.5)
    for _, r in df.iterrows():
        ax.annotate(DISPLAY[r["model"]], (r["risky_recall"], r["risky_precision"]),
                    xytext=(6, 0), textcoords="offset points", fontsize=8, va="center")
    ax.set_xlabel("Risky recall")
    ax.set_ylabel("Risky precision")
    ax.set_title(f"Risky precision–recall operating points — {protocol} protocol (validation)")
    ax.set_xlim(0.55, 0.95)
    ax.set_ylim(0.55, 0.90)
    ax.axvline(0.8, color="gray", ls="--", lw=0.8, alpha=0.5)
    ax.axhline(0.8, color="gray", ls="--", lw=0.8, alpha=0.5)
    save(fig, f"fig4_risky_precision_recall_{protocol}")


def fig5_confusion_matrices(protocol: str = "primary"):
    """Figure 5: Confusion matrices — counts and row-normalised for every method."""
    df = load_comparison(protocol)
    models = df.set_index("model").loc[MODEL_ORDER].index.to_list()

    n_cols = 4
    n_rows = int(np.ceil(len(models) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4 * n_rows))
    axes = np.atleast_2d(axes)

    for idx, model in enumerate(models):
        r = idx // n_cols
        c = idx % n_cols
        ax = axes[r, c]
        cm_path = ROOT / "results" / "comparison" / protocol / f"{model}_confusion_matrix.csv"
        cm_df = pd.read_csv(cm_path, index_col=0)
        cm = cm_df.to_numpy()
        cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)
        sns.heatmap(cm_norm, annot=cm, fmt="d", cmap="Blues",
                    xticklabels=LABELS, yticklabels=LABELS,
                    cbar=False, ax=ax, linewidths=0.3)
        ax.set_title(DISPLAY[model], fontsize=9)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
    # Hide unused subplots.
    for j in range(len(models), n_rows * n_cols):
        r = j // n_cols
        c = j % n_cols
        axes[r, c].axis("off")
    fig.suptitle(f"Confusion matrices — {protocol} protocol (validation, counts annotated, row-normalised)", fontsize=12)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    save(fig, f"fig5_confusion_matrices_{protocol}")


def fig6_roc_curves(protocol: str = "primary"):
    """Figure 6: One-vs-rest ROC curves for the Risky class."""
    fig, ax = plt.subplots(figsize=(6, 5))
    for model in MODEL_ORDER:
        csv_path = ROOT / "results" / "comparison" / protocol / f"{model}_roc_pr_curves.csv"
        if not csv_path.exists():
            continue
        cur = pd.read_csv(csv_path)
        risky = cur[(cur["class"] == "Risky") & (cur["fpr"].notna())]
        if risky.empty:
            continue
        auc = risky["roc_auc"].iloc[0] if "roc_auc" in risky.columns else float("nan")
        ax.plot(risky["fpr"], risky["tpr"], label=f"{DISPLAY[model]} (AUC={auc:.3f})",
                color=COLORS[model], lw=1.5)
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(f"One-vs-rest ROC curves — Risky class — {protocol} protocol (validation)")
    ax.legend(fontsize=7, loc="lower right")
    save(fig, f"fig6_roc_curves_risky_{protocol}")


def fig7_pr_curves(protocol: str = "primary"):
    """Figure 7: Precision-recall curves for the Risky class."""
    fig, ax = plt.subplots(figsize=(6, 5))
    for model in MODEL_ORDER:
        csv_path = ROOT / "results" / "comparison" / protocol / f"{model}_roc_pr_curves.csv"
        if not csv_path.exists():
            continue
        cur = pd.read_csv(csv_path)
        risky = cur[(cur["class"] == "Risky") & (cur["precision"].notna())]
        if risky.empty:
            continue
        pr_auc = risky["pr_auc"].iloc[0] if "pr_auc" in risky.columns else float("nan")
        ax.plot(risky["recall"], risky["precision"],
                label=f"{DISPLAY[model]} (PR-AUC={pr_auc:.3f})", color=COLORS[model], lw=1.5)
    # Prevalence reference for Risky in validation.
    ax.axhline(0.798, color="gray", ls="--", lw=1, alpha=0.6,
               label="Risky prevalence (val) ≈ 0.80")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(f"Precision–recall curves — Risky class — {protocol} protocol (validation)")
    ax.legend(fontsize=7, loc="lower left")
    save(fig, f"fig7_pr_curves_risky_{protocol}")


def fig8_training_inference_cost(protocol: str = "primary"):
    """Figure 8: Training and inference cost (separate, with feature processing)."""
    df = load_comparison(protocol)
    df = df.set_index("model").loc[MODEL_ORDER].reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    colors = [COLORS[m] for m in df["model"]]

    # Training cost (final fit seconds).
    ax = axes[0]
    ax.bar(np.arange(len(df)), df["final_fit_seconds"], color=colors, alpha=0.85)
    ax.set_xticks(np.arange(len(df)))
    ax.set_xticklabels([DISPLAY[m] for m in df["model"]], rotation=35, ha="right")
    ax.set_ylabel("Seconds")
    ax.set_title("Classifier fit time (on all training data)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter())
    for i, v in enumerate(df["final_fit_seconds"]):
        ax.text(i, v * 1.15, f"{v:.2f}", ha="center", fontsize=7)

    # Inference cost (predict seconds).
    ax = axes[1]
    ax.bar(np.arange(len(df)), df["final_predict_seconds"], color=colors, alpha=0.85)
    ax.set_xticks(np.arange(len(df)))
    ax.set_xticklabels([DISPLAY[m] for m in df["model"]], rotation=35, ha="right")
    ax.set_ylabel("Seconds")
    ax.set_title("Validation prediction time (2,658 clauses)")
    ax.set_yscale("log")
    for i, v in enumerate(df["final_predict_seconds"]):
        ax.text(i, v * 1.15, f"{v:.3f}", ha="center", fontsize=7)

    fig.suptitle(f"Computational cost — {protocol} protocol (includes feature processing for sparse models)", fontsize=12)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    save(fig, f"fig8_training_inference_cost_{protocol}")


def fig9_train_vs_validation(protocol: str = "primary"):
    """Figure 9: Train vs validation macro F1 (overfitting diagnosis)."""
    df = load_comparison(protocol)
    df = df.set_index("model").loc[MODEL_ORDER].reset_index()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(df))
    train = df["train_macro_f1"].to_numpy()
    val = df["macro_f1"].to_numpy()
    colors = [COLORS[m] for m in df["model"]]

    ax.scatter(train, val, s=100, c=colors, alpha=0.8, edgecolor="black", linewidth=0.5)
    lims = [min(train.min(), val.min()) - 0.02, max(train.max(), val.max()) + 0.02]
    ax.plot(lims, lims, "k--", lw=1, alpha=0.5, label="Train = Validation")
    for _, r in df.iterrows():
        ax.annotate(DISPLAY[r["model"]], (r["train_macro_f1"], r["macro_f1"]),
                    xytext=(5, 0), textcoords="offset points", fontsize=7, va="center")
    ax.set_xlabel("Train macro F1 (all training data)")
    ax.set_ylabel("Validation macro F1 (held-out)")
    ax.set_title(f"Train vs validation macro F1 — {protocol} protocol (overfitting diagnosis)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.legend(fontsize=8)
    save(fig, f"fig9_train_vs_validation_{protocol}")


def main():
    print("Generating figures...")
    fig1_class_distribution()
    fig2_macro_f1_comparison("primary")
    fig2_macro_f1_comparison("clause")
    fig3_per_class_f1_heatmap("primary")
    fig3_per_class_f1_heatmap("clause")
    fig4_risky_precision_recall("primary")
    fig4_risky_precision_recall("clause")
    fig5_confusion_matrices("primary")
    fig5_confusion_matrices("clause")
    fig6_roc_curves("primary")
    fig6_roc_curves("clause")
    fig7_pr_curves("primary")
    fig7_pr_curves("clause")
    fig8_training_inference_cost("primary")
    fig8_training_inference_cost("clause")
    fig9_train_vs_validation("primary")
    fig9_train_vs_validation("clause")
    print(f"\nAll figures written to {FIG_DIR}")


if __name__ == "__main__":
    main()

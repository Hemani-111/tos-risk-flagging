"""Final consistency verification: all required paths exist, metrics match, checks pass."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path("A:/Projects/ToS-risk-flagging")
LABELS = ["Safe", "Neutral", "Risky"]
MODELS = [
    "naive_bayes", "logistic_regression", "svm/linear", "svm/rbf",
    "decision_tree", "random_forest", "knn", "gradient_boosting",
]
# Map internal comparison CSV model names to model folder names.
CSV_MODEL_NAMES = {
    "naive_bayes": "multinomial_nb",
    "logistic_regression": "logistic_regression",
    "svm/linear": "linear_svm",
    "svm/rbf": "rbf_svm",
    "decision_tree": "decision_tree",
    "random_forest": "random_forest",
    "knn": "knn",
    "gradient_boosting": "gradient_boosting",
}
PROTOCOLS = ["primary", "clause"]
errors = []


def check(condition, msg):
    if not condition:
        errors.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  OK: {msg}")


print("=" * 60)
print("1. MODEL FOLDER STRUCTURE")
print("=" * 60)
for m in MODELS:
    base = ROOT / "models" / m
    check(base.exists(), f"models/{m}/ exists")
    check((base / "README.md").exists(), f"models/{m}/README.md")
    check((base / "config.json").exists(), f"models/{m}/config.json")
    check((base / "code.ipynb").exists(), f"models/{m}/code.ipynb")
    # Validate notebook JSON
    if (base / "code.ipynb").exists():
        try:
            json.loads((base / "code.ipynb").read_text(encoding="utf-8"))
            check(True, f"models/{m}/code.ipynb is valid JSON")
        except Exception as e:
            check(False, f"models/{m}/code.ipynb invalid JSON: {e}")
    for p in PROTOCOLS:
        check((base / "results" / p / "metrics.csv").exists(), f"models/{m}/results/{p}/metrics.csv")
        check((base / "results" / p / "confusion_matrix.csv").exists(), f"models/{m}/results/{p}/confusion_matrix.csv")
        check((base / "artifacts" / p / "model.joblib").exists(), f"models/{m}/artifacts/{p}/model.joblib")
        check((base / "artifacts" / p / "metadata.json").exists(), f"models/{m}/artifacts/{p}/metadata.json")

print()
print("=" * 60)
print("2. COMPARISON OUTPUTS")
print("=" * 60)
for p in PROTOCOLS:
    base = ROOT / "results" / "comparison" / p
    check(base.exists(), f"results/comparison/{p}/ exists")
    check((base / "comparison.csv").exists(), f"results/comparison/{p}/comparison.csv")
    check((base / "comparison.md").exists(), f"results/comparison/{p}/comparison.md")
    check((base / "run_metadata.json").exists(), f"results/comparison/{p}/run_metadata.json")
    check((base / "validation_predictions.csv").exists(), f"results/comparison/{p}/validation_predictions.csv")
    for m in MODELS:
        csv_name = CSV_MODEL_NAMES[m]
        check((base / f"{csv_name}_confusion_matrix.csv").exists(), f"results/comparison/{p}/{csv_name}_confusion_matrix.csv")
        check((base / f"{csv_name}_roc_pr_curves.csv").exists(), f"results/comparison/{p}/{csv_name}_roc_pr_curves.csv")

print()
print("=" * 60)
print("3. FIGURES")
print("=" * 60)
fig_dir = ROOT / "results" / "comparison" / "figures"
required_figs = [
    "fig1_class_distribution",
    "fig2_macro_f1_comparison_primary", "fig2_macro_f1_comparison_clause",
    "fig3_per_class_f1_heatmap_primary", "fig3_per_class_f1_heatmap_clause",
    "fig4_risky_precision_recall_primary", "fig4_risky_precision_recall_clause",
    "fig5_confusion_matrices_primary", "fig5_confusion_matrices_clause",
    "fig6_roc_curves_risky_primary", "fig6_roc_curves_risky_clause",
    "fig7_pr_curves_risky_primary", "fig7_pr_curves_risky_clause",
    "fig8_training_inference_cost_primary", "fig8_training_inference_cost_clause",
    "fig9_train_vs_validation_primary", "fig9_train_vs_validation_clause",
]
for f in required_figs:
    check((fig_dir / f"{f}.png").exists(), f"figures/{f}.png")
    check((fig_dir / f"{f}.svg").exists(), f"figures/{f}.svg")

print()
print("=" * 60)
print("4. METRICS CONSISTENCY (comparison.csv vs per-model results)")
print("=" * 60)
for p in PROTOCOLS:
    comp = pd.read_csv(ROOT / "results" / "comparison" / p / "comparison.csv")
    comp = comp.set_index("model")
    for m in MODELS:
        csv_name = CSV_MODEL_NAMES[m]
        mrow = comp.loc[csv_name]
        mresults = pd.read_csv(ROOT / "models" / m / "results" / p / "metrics.csv")
        # Check macro f1 matches
        if abs(float(mrow["macro_f1"]) - float(mresults["macro_f1"].iloc[0])) > 1e-6:
            errors.append(f"{m}/{p}: comparison.csv macro_f1 {mrow['macro_f1']} != results metrics {mresults['macro_f1'].iloc[0]}")
            print(f"  FAIL: {m}/{p} macro_f1 mismatch")
        else:
            print(f"  OK: {m}/{p} macro_f1 consistent ({float(mrow['macro_f1']):.4f})")
        # Check CV is genuinely different from validation
        if abs(float(mrow["cv_macro_f1_mean"]) - float(mrow["macro_f1"])) < 1e-9:
            errors.append(f"{m}/{p}: cv_macro_f1_mean == validation macro_f1 (CV not genuine)")
            print(f"  FAIL: {m}/{p} CV not genuinely computed")
        else:
            print(f"  OK: {m}/{p} CV={float(mrow['cv_macro_f1_mean']):.4f}±{float(mrow['cv_macro_f1_std']):.4f} vs val={float(mrow['macro_f1']):.4f}")

print()
print("=" * 60)
print("5. PRODUCTION MODEL")
print("=" * 60)
pkg = ROOT / "models" / "releases" / "linear-svc-primary-v2"
check(pkg.exists(), "models/releases/linear-svc-primary-v2/ exists")
check((pkg / "model.joblib").exists(), "production model.joblib")
check((pkg / "vectorizer.joblib").exists(), "production vectorizer.joblib")
check((pkg / "metadata.json").exists(), "production metadata.json")
# Check models/production/ does NOT exist (canonical is releases/)
check(not (ROOT / "models" / "production").exists(), "models/production/ does NOT exist (canonical is releases/)")

print()
print("=" * 60)
print("6. DOCS")
print("=" * 60)
check((ROOT / "docs" / "FINAL_REPORT.md").exists(), "docs/FINAL_REPORT.md")
check((ROOT / "docs" / "EXPERIMENT_PROTOCOL.md").exists(), "docs/EXPERIMENT_PROTOCOL.md")
check((ROOT / "docs" / "LOCKED_TEST_EVALUATION_v1.md").exists(), "docs/LOCKED_TEST_EVALUATION_v1.md")
check((ROOT / "docs" / "archive" / "Terms & Conditions Risk Flagging Using ML.pptx").exists(), "archive mid-semester slides")
check((ROOT / "docs" / "Terms & Conditions Risk Flagging Using ML - Endsemester Provisional.pptx").exists(), "end-semester deck outside archive")
# Check removed docs don't exist
for f in ["PROJECT_CONTEXT.md", "PROJECT_COMPLETION_PLAN.md", "REMAINING_WORK_AI_IDE_PROMPT.md", "REMAINING_WORK_STATUS.md", "MIDSEM_TO_ENDSEM_PROGRESS.md", "TEAM_PREPARATION_NOTES.md", "EXPERIMENT_INVENTORY.md", "DEMO_RUN_SHEET.md", "progress/WORK_LOG.md", "frontend/AGENTS.md"]:
    check(not (ROOT / f).exists(), f"{f} removed")

print()
print("=" * 60)
print("7. SCRIPTS")
print("=" * 60)
check((ROOT / "scripts" / "run_comparison.py").exists(), "scripts/run_comparison.py")
check((ROOT / "scripts" / "check_parity.py").exists(), "scripts/check_parity.py")
check((ROOT / "scripts" / "generate_frontend_data.py").exists(), "scripts/generate_frontend_data.py")
check((ROOT / "scripts" / "generate_figures.py").exists(), "scripts/generate_figures.py")
check((ROOT / "scripts" / "audit_metrics.py").exists(), "scripts/audit_metrics.py")
# Removed scripts should not exist
for f in ["run_ensemble_calibration_clusters.py", "run_remaining_feature_experiments.py", "embed_sentence_clauses.py", "analyze_linear_feature_stability.py", "build_experiment_registry.py"]:
    check(not (ROOT / "scripts" / f).exists(), f"scripts/{f} removed")

print()
print("=" * 60)
print("RESULT")
print("=" * 60)
if errors:
    print(f"{len(errors)} ERRORS FOUND:")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL CHECKS PASSED — project is consistent and complete.")

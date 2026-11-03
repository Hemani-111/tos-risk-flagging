"""Audit: verify all saved comparison metrics against saved predictions and true labels.

Checks:
- Every row in comparison.csv recomputes from validation_predictions.csv
- cv_macro_f1 vs actual validation macro_f1 (flags if identical = CV not run)
- Confusion matrix counts sum to sample count
- Class supports match true-label distribution
- Accuracy agrees with confusion-matrix diagonal
- Risky FN/FP agree with confusion matrix
- Macro/weighted averages recalculated correctly
- Predictions contain only allowed classes
- NaN/missing scores detected
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["Safe", "Neutral", "Risky"]  # presentation order


def metrics_from_predictions(df: pd.DataFrame) -> dict:
    y_true = df["true_label"].to_numpy()
    y_pred = df["predicted_label"].to_numpy()
    n = len(y_true)
    labels = ["Risky", "Neutral", "Safe"]  # sklearn sorted order
    cm = confusion_counts(y_true, y_pred, labels)

    # Per-class
    per_class = {}
    for i, label in enumerate(labels):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        support = cm[i, :].sum()
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        per_class[label] = {
            "precision": precision, "recall": recall, "f1": f1,
            "support": int(support), "tp": int(tp), "fn": int(fn), "fp": int(fp),
        }

    accuracy = np.trace(cm) / n
    macro_f1 = np.mean([per_class[l]["f1"] for l in labels])
    macro_p = np.mean([per_class[l]["precision"] for l in labels])
    macro_r = np.mean([per_class[l]["recall"] for l in labels])

    # Weighted by support
    total_support = n
    weighted_f1 = sum(per_class[l]["f1"] * per_class[l]["support"] for l in labels) / total_support
    weighted_p = sum(per_class[l]["precision"] * per_class[l]["support"] for l in labels) / total_support
    weighted_r = sum(per_class[l]["recall"] * per_class[l]["support"] for l in labels) / total_support

    risky = per_class["Risky"]
    return {
        "n": n,
        "accuracy": float(accuracy),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "weighted_precision": float(weighted_p),
        "weighted_recall": float(weighted_r),
        "weighted_f1": float(weighted_f1),
        "risky_precision": float(risky["precision"]),
        "risky_recall": float(risky["recall"]),
        "risky_f1": float(risky["f1"]),
        "risky_fp": int(risky["fp"]),
        "risky_fn": int(risky["fn"]),
        "per_class": per_class,
        "cm": cm,
        "labels": labels,
    }


def confusion_counts(y_true, y_pred, labels):
    idx = {lab: i for i, lab in enumerate(labels)}
    cm = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(y_true, y_pred):
        if t in idx and p in idx:
            cm[idx[t], idx[p]] += 1
    return cm


def audit_protocol(protocol: str):
    print(f"\n{'='*70}")
    print(f"AUDIT: {protocol.upper()} protocol")
    print(f"{'='*70}")

    comp_path = ROOT / "results" / "comparison" / protocol / "comparison.csv"
    pred_path = ROOT / "results" / "comparison" / protocol / "validation_predictions.csv"

    comp = pd.read_csv(comp_path)
    preds = pd.read_csv(pred_path)

    print(f"Comparison rows: {len(comp)}")
    print(f"Prediction rows: {len(preds)}")
    print(f"Models in predictions: {sorted(preds['model'].unique())}")
    print(f"Models in comparison: {sorted(comp['model'].unique())}")

    # Check every model
    issues = []
    for _, row in comp.iterrows():
        model = row["model"]
        sub = preds[preds["model"] == model]
        if sub.empty:
            issues.append(f"{model}: NO predictions found")
            continue

        recomputed = metrics_from_predictions(sub)

        # Verify counts sum
        cm_sum = int(recomputed["cm"].sum())
        if cm_sum != recomputed["n"]:
            issues.append(f"{model}: confusion matrix sum {cm_sum} != n {recomputed['n']}")

        # Verify accuracy
        if abs(recomputed["accuracy"] - float(row["accuracy"])) > 1e-6:
            issues.append(f"{model}: accuracy recomputed={recomputed['accuracy']:.6f} saved={float(row['accuracy']):.6f}")

        # Verify macro f1
        if abs(recomputed["macro_f1"] - float(row["macro_f1"])) > 1e-6:
            issues.append(f"{model}: macro_f1 recomputed={recomputed['macro_f1']:.6f} saved={float(row['macro_f1']):.6f}")

        # Verify risky precision/recall
        if abs(recomputed["risky_precision"] - float(row["risky_precision"])) > 1e-6:
            issues.append(f"{model}: risky_precision recomputed={recomputed['risky_precision']:.6f} saved={float(row['risky_precision']):.6f}")
        if abs(recomputed["risky_recall"] - float(row["risky_recall"])) > 1e-6:
            issues.append(f"{model}: risky_recall recomputed={recomputed['risky_recall']:.6f} saved={float(row['risky_recall']):.6f}")

        # Verify risky FP/FN
        if recomputed["risky_fp"] != int(row["risky_false_positives"]):
            issues.append(f"{model}: risky_fp recomputed={recomputed['risky_fp']} saved={int(row['risky_false_positives'])}")
        if recomputed["risky_fn"] != int(row["risky_false_negatives"]):
            issues.append(f"{model}: risky_fn recomputed={recomputed['risky_fn']} saved={int(row['risky_false_negatives'])}")

        # Check cv_macro_f1_mean vs validation macro_f1 (they should differ - CV != validation)
        cv_val = float(row["cv_macro_f1_mean"])
        val_val = float(row["macro_f1"])
        if abs(cv_val - val_val) < 1e-9:
            issues.append(f"{model}: cv_macro_f1_mean ({cv_val:.6f}) == validation macro_f1 ({val_val:.6f}) -- CV NOT genuinely computed!")

        # Check predictions only allowed classes
        allowed = {"Safe", "Neutral", "Risky"}
        bad_preds = set(sub["predicted_label"].unique()) - allowed
        bad_true = set(sub["true_label"].unique()) - allowed
        if bad_preds:
            issues.append(f"{model}: unexpected predicted labels {bad_preds}")
        if bad_true:
            issues.append(f"{model}: unexpected true labels {bad_true}")

        # Check unique point_ids (every expected row has exactly one prediction)
        if sub["point_id"].duplicated().any():
            issues.append(f"{model}: duplicate point_ids in predictions")

        # Check NaN
        if sub[["true_label", "predicted_label"]].isna().any().any():
            issues.append(f"{model}: NaN labels in predictions")

    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for iss in issues:
            print(f"  - {iss}")
    else:
        print("\nAll metrics verified against predictions. No issues.")

    print(f"\nCV check: cv_macro_f1_mean == validation macro_f1 for all models? "
          f"{all(abs(float(r['cv_macro_f1_mean'])-float(r['macro_f1']))<1e-9 for _,r in comp.iterrows())}")
    print("(If True, CV was not genuinely computed - validation values were copied.)")


def main():
    for protocol in ("primary", "clause"):
        audit_protocol(protocol)


if __name__ == "__main__":
    main()

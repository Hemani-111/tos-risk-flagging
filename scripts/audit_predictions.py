import pandas as pd
import numpy as np
import json
from pathlib import Path

ROOT = Path("A:/Projects/ToS-risk-flagging")
LABELS = ["Safe", "Neutral", "Risky"]

# Load predictions
preds = pd.read_csv(ROOT / "results" / "comparison" / "primary" / "validation_predictions.csv")
print("Total prediction rows:", len(preds))
print("Models:", sorted(preds['model'].unique()))
print("Protocols:", preds['protocol'].unique() if 'protocol' in preds.columns else 'N/A')
print()

# Check row count per model and alignment
ref_model = "linear_svm"
ref = preds[preds['model'] == ref_model].sort_values('point_id').reset_index(drop=True)
ref_ids = set(ref['point_id'])
ref_labels = dict(zip(ref['point_id'], ref['true_label']))

print(f"Reference ({ref_model}): {len(ref)} rows, {len(ref_ids)} unique point_ids")
print(f"Reference true label dist: {ref['true_label'].value_counts().to_dict()}")
print()

all_ok = True
for m in sorted(preds['model'].unique()):
    sub = preds[preds['model'] == m].sort_values('point_id').reset_index(drop=True)
    ids = set(sub['point_id'])
    labels = dict(sub['true_label'].value_counts())
    id_match = ids == ref_ids
    # Check labels match per row when sorted by point_id
    ref_sorted = ref.set_index('point_id').loc[sub['point_id']]
    label_match = (ref_sorted['true_label'].values == sub['true_label'].values).all()
    print(f"{m}: {len(sub)} rows, unique IDs: {sub['point_id'].nunique()}, "
          f"IDs match ref: {id_match}, labels match per-row: {label_match}, "
          f"label dist: {labels}")
    if not id_match or not label_match:
        all_ok = False

print()
print("ALL MODELS ALIGNED:", all_ok)
print()

# Now recalculate metrics from predictions for each model
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, balanced_accuracy_score

print("=== RECALCULATED METRICS FROM PREDICTIONS ===")
for m in sorted(preds['model'].unique()):
    sub = preds[preds['model'] == m].sort_values('point_id')
    y_true = sub['true_label'].values
    y_pred = sub['predicted_label'].values
    n = len(y_true)
    
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    # LABELS order: Safe, Neutral, Risky
    # cm[i,j] = true i, pred j
    safe_idx = LABELS.index("Safe")
    neutral_idx = LABELS.index("Neutral")
    risky_idx = LABELS.index("Risky")
    
    # Per-class
    results = {}
    for i, label in enumerate(LABELS):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        support = cm[i, :].sum()
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        results[label] = {"tp": int(tp), "fn": int(fn), "fp": int(fp), "support": int(support),
                          "precision": prec, "recall": rec, "f1": f1}
    
    accuracy = accuracy_score(y_true, y_pred)
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    macro_p = precision_score(y_true, y_pred, labels=LABELS, average='macro', zero_division=0)
    macro_r = recall_score(y_true, y_pred, labels=LABELS, average='macro', zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, labels=LABELS, average='macro', zero_division=0)
    
    risky = results["Risky"]
    print(f"\n{m} (n={n}):")
    print(f"  Accuracy={accuracy:.6f}, BalAcc={bal_acc:.6f}")
    print(f"  Macro P={macro_p:.6f}, R={macro_r:.6f}, F1={macro_f1:.6f}")
    print(f"  Risky: TP={risky['tp']}, FN={risky['fn']}, FP={risky['fp']}, support={risky['support']}")
    print(f"         Precision={risky['precision']:.6f}, Recall={risky['recall']:.6f}, F1={risky['f1']:.6f}")
    print(f"  Confusion matrix (rows=true, cols=pred, order=Safe/Neutral/Risky):")
    print(cm)

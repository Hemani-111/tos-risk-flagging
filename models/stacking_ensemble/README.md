# Stacking Ensemble Experiment

## What this method does

Stacking trains a second-stage (meta) model on out-of-fold predictions from base learners. Base models (Logistic Regression and LinearSVC) are trained on 2 of 3 group folds and predict on the held-out fold. The meta-model (Logistic Regression) learns to combine the 6-dimensional decision margins (3 classes × 2 base models) into a final prediction. This prevents the meta-model from learning on in-sample base predictions (no group leakage).

## Why we tested it

To test whether a learned combination of base-model margins outperforms hard voting and the strongest individual base model, while respecting service/text group boundaries.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | 6-dimensional OOF margins (LR 3-class + LinearSVC 3-class decision scores) |
| Base models | LogisticRegression (C=1.0, class_weight=balanced), LinearSVC (C=1.0, class_weight=balanced) |
| Meta model | LogisticRegression (C=1.0, class_weight=balanced, max_iter=3000) |
| OOF construction | 3 fixed group folds; group-respecting; no leakage |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_ensemble_calibration_clusters.py
python models/stacking_ensemble/run.py --protocol both
python models/stacking_ensemble/run.py --protocol primary --smoke
```

## Actual results (development-only)

### Primary protocol
| Metric | Stacking | LinearSVC (baseline) |
|--------|----------|---------------------|
| Validation macro F1 | ~0.8191 | ~0.8201 |

### Clause protocol
| Metric | Stacking | LinearSVC (baseline) |
|--------|----------|---------------------|
| Validation macro F1 | ~0.8215 | ~0.8195 |

## Limitations

- No clear macro-F1 gain over LinearSVC alone.
- Stacking adds complexity without improving the primary metric.
- Meta-model trained on margins, not probabilities; margins are not calibrated confidence scores.
- Development-only diagnostic; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/stacking_ensemble/config.json` | Configuration |
| `models/stacking_ensemble/run.py` | Entry point |
| `models/stacking_ensemble/code.ipynb` | Notebook |
| `models/stacking_ensemble/results/{primary,clause}/` | Ensemble metrics, predictions, OOF features |
| `results/experiments/ensemble_calibration_{protocol}_v1/` | Canonical outputs |

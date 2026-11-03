# Gradient Boosting Experiment (HistGradientBoostingClassifier)

## What this method does

Gradient Boosting builds an additive ensemble of shallow decision trees sequentially. Each new tree fits the negative gradient (residuals) of the previous ensemble, with a learning rate controlling step size. Histogram-based binning makes it scalable to larger datasets.

## Why we tested it

To evaluate whether sequentially correcting prior errors improves over bagging (Random Forest) and the linear SVM baseline on clause-level text classification.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | Word unigram/bigram TF-IDF, max_features=60000, then training-fold TruncatedSVD to 100 dense components |
| Tuning grid | max_iter in {100, 200}, learning_rate in {0.05, 0.1}, max_leaf_nodes in {15, 31}, l2_regularization=1.0, early_stopping=False |
| Selection rule | Max mean macro F1 across 3 fixed group folds (training only) |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_expanded_classical_tuning.py --protocol both
python models/gradient_boosting/run.py --protocol both
python models/gradient_boosting/run.py --protocol primary --smoke
python models/gradient_boosting/run.py --protocol both --save-artifact
```

## Actual results (development-only)

### Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7867 |
| CV macro F1 (mean ± SD) | 0.7931 ± 0.00248 |
| Train macro F1 | ~0.999 |
| Risky precision | ~0.772 |
| Risky recall | ~0.787 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7969 |
| CV macro F1 (mean ± SD) | 0.8046 ± 0.00710 |
| Risky precision | ~0.777 |
| Risky recall | ~0.805 |

## Limitations

- Strong train fit (~0.999) but moderate held-fold performance; overfitting gap.
- Below Linear SVM baseline (0.8316 primary CV / 0.8386 clause CV).
- Dense SVD representation limits expressive power for sparse text.
- Development-only; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/gradient_boosting/config.json` | Configuration |
| `models/gradient_boosting/run.py` | Entry point |
| `models/gradient_boosting/code.ipynb` | Notebook |
| `models/gradient_boosting/results/{primary,clause}/` | Metrics, predictions, confusion matrix |
| `models/gradient_boosting/artifacts/` | Fitted development pipeline (after `--save-artifact`) |

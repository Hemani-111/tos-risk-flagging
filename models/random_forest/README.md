# Random Forest Experiment

## What this method does

Random Forest is a bagging ensemble of decision trees. Each tree is trained on a bootstrap sample of rows and a random subset of features; predictions are averaged (majority vote) across trees. This reduces variance compared to a single tree.

## Why we tested it

To compare bagging against the linear SVM baseline and to quantify whether tree ensembles can capture nonlinear interactions in clause text that a linear margin model misses.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | Word unigram/bigram TF-IDF, max_features=60000, then training-fold TruncatedSVD to 100 dense components |
| Tuning grid | n_estimators in {100, 200}, max_depth in {25, None}, min_samples_leaf in {2, 5}, max_features=sqrt, class_weight=balanced_subsample |
| Selection rule | Max mean macro F1 across 3 fixed group folds (training only) |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_expanded_classical_tuning.py --protocol both
python models/random_forest/run.py --protocol both
python models/random_forest/run.py --protocol primary --smoke
python models/random_forest/run.py --protocol both --save-artifact
```

## Actual results (development-only)

### Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7828 |
| CV macro F1 (mean ± SD) | 0.7797 ± 0.00186 |
| Train macro F1 | ~0.999 |
| Risky precision | ~0.763 |
| Risky recall | ~0.784 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7771 |
| CV macro F1 (mean ± SD) | 0.7847 ± 0.00619 |
| Risky precision | ~0.747 |
| Risky recall | ~0.787 |

## Limitations

- Large train-to-held-out gap (train ~0.999 vs validation ~0.78) indicates overfitting.
- Trailing Linear SVM baseline (0.8316 primary CV / 0.8386 clause CV).
- Dense 100-component SVD representation loses sparse text information; RF is expensive on high-dimensional text.
- Development-only; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/random_forest/config.json` | Configuration |
| `models/random_forest/run.py` | Entry point |
| `models/random_forest/code.ipynb` | Notebook |
| `models/random_forest/results/{primary,clause}/` | Metrics, predictions, confusion matrix |
| `models/random_forest/artifacts/` | Fitted development pipeline (after `--save-artifact`) |

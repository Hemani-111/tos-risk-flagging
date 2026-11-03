# Decision Tree Experiment

## What this method does

A Decision Tree classifier partitions the TF-IDF feature space through sequential if/then rules. Each split selects the feature (token or token-pair) that best separates the classes by impurity (Gini). The tree grows until a stopping criterion (max depth, min samples per leaf, or cost-complexity pruning) is met.

## Why we tested it

The mid-semester presentation covered Naive Bayes, Logistic Regression, and SVM. For end-semester we expanded to tree-based methods to study rule-based, nonlinear decision boundaries and to compare their train-to-held-out behaviour against linear models.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | Word unigram/bigram TF-IDF, max_features=60000, then training-fold TruncatedSVD to 100 dense components |
| Tuning grid | max_depth in {15, 30, None}, min_samples_leaf in {2, 10}, ccp_alpha in {0.0, 0.001}, class_weight=balanced |
| Selection rule | Max mean macro F1 across 3 fixed group folds (training only) |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

Full tuning (both protocols):
```
python scripts/run_expanded_classical_tuning.py --protocol both
```

Method-specific entry point:
```
python models/decision_tree/run.py --protocol both
```

Smoke check (single fold, fast):
```
python models/decision_tree/run.py --protocol primary --smoke
```

Persist a fitted development artifact:
```
python models/decision_tree/run.py --protocol both --save-artifact
```

## Actual results (development-only; no locked-test tuning)

### Primary protocol (unseen-service)
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.6344 |
| CV macro F1 (mean ± SD) | 0.6681 ± 0.00698 |
| Train macro F1 (fit folds) | ~0.729 |
| Risky precision | ~0.609 |
| Risky recall | ~0.675 |

### Clause protocol (duplicate-aware)
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.6920 |
| CV macro F1 (mean ± SD) | 0.6737 ± 0.00404 |
| Risky precision | ~0.642 |
| Risky recall | ~0.720 |

## Limitations

- Substantial train-to-held-out gap (train macro F1 approached 0.999 for deep trees), indicating overfitting.
- Trailing the lexical Linear SVM baseline (0.8316 primary CV / 0.8386 clause CV).
- Sparse high-dimensional text is a difficult fit for a single tree; results are unstable across folds.
- Development-only artifact; not deployed. Production release is `models/releases/linear-svc-primary-v2/`.

## Files

| Path | Contents |
|------|----------|
| `models/decision_tree/config.json` | Reproducible configuration |
| `models/decision_tree/run.py` | Runnable entry point |
| `models/decision_tree/code.ipynb` | Educational notebook |
| `models/decision_tree/results/primary/` | Primary protocol metrics, predictions, confusion matrix |
| `models/decision_tree/results/clause/` | Clause protocol metrics, predictions, confusion matrix |
| `models/decision_tree/artifacts/` | Fitted development pipeline (after `--save-artifact`) |
| `results/experiments/expanded_classical_primary_v1/` | Canonical primary outputs |
| `results/experiments/expanded_classical_clause_v1/` | Canonical clause outputs |

## Canonical result files

- `results/experiments/expanded_classical_{protocol}_v1/validation_selected_family_metrics.csv`
- `results/experiments/expanded_classical_{protocol}_v1/decision_tree_validation_confusion.csv`
- `results/experiments/expanded_classical_{protocol}_v1/cv_summary.csv`
- `results/experiments/expanded_classical_{protocol}_v1/run_metadata.json`

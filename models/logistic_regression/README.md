# Logistic Regression

## What this method does

Logistic Regression is a linear classifier that models class probabilities via the softmax function. It is regularized with an L2 penalty; `C` controls inverse regularization strength. Class weighting addresses imbalance. It outputs a linear decision boundary over the TF-IDF features.

## Why we tested it

Baseline linear method covered at mid-semester. A well-calibrated linear reference that is fast to train and predict, with interpretable coefficients.

## Input features

Sparse word unigram/bigram TF-IDF (`max_features=60000`, `min_df=2`, `max_df=0.99`, `sublinear_tf=True`). Negation tokens such as "not" and "without" are kept as ordinary tokens.

## Classifier

`sklearn.linear_model.LogisticRegression` (solver=`lbfgs`, multi-class `ovr`)

## Tuning

Bounded grid over `C` in {0.1, 1.0, 10.0} and `class_weight` in {None, balanced}, selected by mean macro F1 on fixed group-respecting CV folds (development data only).

## Actual results (development-only; test not used)

### Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8185 |
| Accuracy | 0.8243 |
| Risky precision | 0.7941 |
| Risky recall | 0.8345 |
| Risky false negatives | 143 |
| Risky false positives | 187 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8159 |
| Accuracy | 0.8197 |
| Risky precision | 0.7894 |
| Risky recall | 0.8297 |
| Risky false negatives | 147 |
| Risky false positives | 191 |

## Interpretation

Close runner-up to Linear SVM on macro F1 (0.8185 vs 0.8206 primary). Well-balanced precision/recall. ~1s fit time, fast prediction. Coefficients are associations, not legal explanations.

## Files

| Path | Contents |
|------|----------|
| `models/logistic_regression/config.json` | Reproducible configuration |
| `models/logistic_regression/code.ipynb` | Educational notebook |
| `models/logistic_regression/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/logistic_regression/results/{primary,clause}/confusion_matrix.csv` | Confusion matrix |
| `models/logistic_regression/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison row |

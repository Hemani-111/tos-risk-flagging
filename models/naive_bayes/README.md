# Multinomial Naive Bayes

## What this method does

Multinomial Naive Bayes is a probabilistic linear classifier based on Bayes' theorem with the "naive" independence assumption between features. For each class it estimates the likelihood of each token, then combines them to score a new clause. Smoothing (`alpha`) handles tokens not seen during training.

## Why we tested it

Baseline linear method covered at mid-semester. Fast to train and predict, interpretable token likelihoods, and a standard text-classification reference.

## Input features

Sparse word unigram/bigram TF-IDF (`max_features=60000`, `min_df=2`, `max_df=0.99`, `sublinear_tf=True`). Negation tokens such as "not" and "without" are kept as ordinary tokens.

## Classifier

`sklearn.naive_bayes.MultinomialNB`

## Tuning

Bounded grid over `alpha` in {0.1, 1.0, 10.0}, selected by mean macro F1 on fixed group-respecting CV folds (development data only).

## Actual results (development-only; test not used)

### Primary protocol (unseen-service)
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.7980 |
| Accuracy | 0.8002 |
| Risky precision | 0.7370 |
| Risky recall | 0.8368 |
| Risky false negatives | 141 |
| Risky false positives | 258 |

### Clause protocol (duplicate-aware)
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8033 |
| Accuracy | 0.8051 |
| Risky precision | 0.7463 |
| Risky recall | 0.8250 |
| Risky false negatives | 151 |
| Risky false positives | 242 |

## Interpretation

Strong Risky recall but modest Risky precision — NB flags many risky clauses but over-predicts Risky. Below Linear SVM on macro F1 (0.7980 vs 0.8206 primary). Fastest training of all methods (~0.04s fit).

## Files

| Path | Contents |
|------|----------|
| `models/naive_bayes/config.json` | Reproducible configuration |
| `models/naive_bayes/code.ipynb` | Educational notebook |
| `models/naive_bayes/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/naive_bayes/results/{primary,clause}/confusion_matrix.csv` | Confusion matrix |
| `models/naive_bayes/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison row |

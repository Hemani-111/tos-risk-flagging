# Support Vector Machine — Linear and RBF

## What this method does

Support Vector Machine is a large-margin classifier. Linear SVM finds a separating hyperplane in TF-IDF space. RBF SVM uses a kernel trick on dense TruncatedSVD-reduced features to capture nonlinear boundaries. `C` controls the margin/loss trade-off; `gamma` controls RBF kernel width.

## Why we tested it

Linear SVM covered at mid-semester. RBF SVM added for end-semester to test whether a nonlinear kernel improves over the linear margin on dense-reduced text features.

## Input features

- **Linear SVM**: Sparse word unigram/bigram TF-IDF (`max_features=60000`, `min_df=2`, `max_df=0.99`, `sublinear_tf=True`).
- **RBF SVM**: Dense TruncatedSVD (100 components, training-fold fitted) of the same TF-IDF. SVD is a feature transform, not a classifier.

## Classifier

- Linear: `sklearn.svm.LinearSVC` (loss=`squared_hinge`, multi-class `ovr`)
- RBF: `sklearn.svm.SVC` (kernel=`rbf`, `cache_size=512`)

## Tuning

Bounded grid over `C` in {0.1, 1.0, 10.0} and `class_weight` in {None, balanced} (plus `gamma` for RBF), selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

### Linear SVM — Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8206 |
| Accuracy | 0.8258 |
| Risky precision | 0.7886 |
| Risky recall | 0.8461 |
| Risky false negatives | 133 |
| Risky false positives | 196 |

### Linear SVM — Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8195 |
| Accuracy | 0.8236 |
| Risky precision | 0.7873 |
| Risky recall | 0.8447 |
| Risky false negatives | 134 |
| Risky false positives | 197 |

### RBF SVM — Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8064 |
| Accuracy | 0.8108 |
| Risky precision | 0.7936 |
| Risky recall | 0.8056 |
| Risky false negatives | 168 |
| Risky false positives | 181 |

## Interpretation

Linear SVM is the strongest method on macro F1 (0.8206 primary) and is the selected production model (`models/releases/linear-svc-primary-v2/`). RBF SVM is close on macro F1 (0.8064) but much slower to train (~12s vs ~0.2s) and needs dense SVD input. Linear and RBF are variants of the SVM family, not separate algorithms.

## Files

| Path | Contents |
|------|----------|
| `models/svm/config.json` | Reproducible configuration (linear + rbf) |
| `models/svm/linear/README.md` | Linear SVM details |
| `models/svm/rbf/README.md` | RBF SVM details |
| `models/svm/linear/code.ipynb` | Linear SVM notebook |
| `models/svm/rbf/code.ipynb` | RBF SVM notebook |
| `models/svm/{linear,rbf}/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/svm/{linear,rbf}/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison rows |

# SVM — RBF (SVC with RBF kernel)

## What this method does

RBF SVM applies the kernel trick to map TF-IDF-derived dense features into a higher-dimensional space where a linear separator may exist. `C` controls the margin/loss trade-off; `gamma` controls kernel width.

## Input features

Dense TruncatedSVD (100 components, training-fold fitted) of word unigram/bigram TF-IDF. SVD is a feature transform, not a classifier, and is fitted on training data only.

## Classifier

`sklearn.svm.SVC` (kernel=`rbf`, `cache_size=512`)

## Tuning

Bounded grid over `C` in {0.1, 1.0, 10.0}, `gamma` in {scale, auto}, and `class_weight` in {None, balanced}, selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

| Protocol | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP |
|----------|----------|----------|-----------------|--------------|----------|----------|
| Primary | 0.8064 | 0.8108 | 0.7936 | 0.8056 | 168 | 181 |
| Clause | 0.8060 | 0.8097 | 0.7705 | 0.8169 | 158 | 210 |

## Interpretation

Close to Linear SVM on macro F1 but ~60x slower to train and requires dense SVD input. Not selected for production; Linear SVM is faster and slightly more accurate.

## Files

| Path | Contents |
|------|----------|
| `models/svm/rbf/config.json` | Configuration |
| `models/svm/rbf/code.ipynb` | Notebook |
| `models/svm/rbf/results/{primary,clause}/metrics.csv` | Metrics |
| `models/svm/rbf/artifacts/{primary,clause}/` | Fitted pipeline (+ svd.joblib) |

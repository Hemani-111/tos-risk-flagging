# SVM — Linear (LinearSVC)

## What this method does

Linear SVM finds a maximum-margin hyperplane separating classes in sparse TF-IDF space. It uses the squared-hinge loss with one-vs-rest multi-class decoding. `C` controls the margin/loss trade-off.

## Input features

Sparse word unigram/bigram TF-IDF (`max_features=60000`, `min_df=2`, `max_df=0.99`, `sublinear_tf=True`). Kept sparse throughout — no dense conversion.

## Classifier

`sklearn.svm.LinearSVC` (loss=`squared_hinge`, multi-class `ovr`)

## Tuning

Bounded grid over `C` in {0.1, 1.0, 10.0} and `class_weight` in {None, balanced}, selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

| Protocol | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP |
|----------|----------|----------|-----------------|--------------|----------|----------|
| Primary | 0.8206 | 0.8258 | 0.7886 | 0.8461 | 133 | 196 |
| Clause | 0.8195 | 0.8236 | 0.7873 | 0.8447 | 134 | 197 |

## Interpretation

Best macro F1 of all methods on both protocols. Fast training (~0.2s) and prediction. Selected as the production candidate. Decision scores are not probabilities.

## Files

| Path | Contents |
|------|----------|
| `models/svm/linear/config.json` | Configuration |
| `models/svm/linear/code.ipynb` | Notebook |
| `models/svm/linear/results/{primary,clause}/metrics.csv` | Metrics |
| `models/svm/linear/artifacts/{primary,clause}/` | Fitted pipeline |

# K-Nearest Neighbours

## What this method does

KNN classifies a clause by the majority label of its k nearest training neighbours in feature space. Distance metric and weighting scheme are tuned. Non-parametric and instance-based.

## Why we tested it

End-semester addition; tests whether similarity-based retrieval of previously seen risky clauses is effective for this task.

## Input features

Dense TruncatedSVD (100 components, training-fold fitted) of word unigram/bigram TF-IDF.

## Classifier

`sklearn.neighbors.KNeighborsClassifier`

## Tuning

Bounded grid over `n_neighbors` in {5, 15, 31}, `weights` in {uniform, distance}, `metric` in {euclidean, manhattan}, selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

| Protocol | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP |
|----------|----------|----------|-----------------|--------------|----------|----------|
| Primary | 0.7837 | 0.7889 | 0.7843 | 0.7743 | 195 | 184 |
| Clause | 0.7831 | 0.7886 | 0.7818 | 0.7845 | 186 | 189 |

## Interpretation

Reasonable macro F1 but inference cost grows with training size (must store all training vectors and compute distances). Below Linear SVM. Distance metrics in high-dimensional reduced space are a weak signal for this task.

## Files

| Path | Contents |
|------|----------|
| `models/knn/config.json` | Reproducible configuration |
| `models/knn/run.py` | Runnable entry point |
| `models/knn/code.ipynb` | Educational notebook |
| `models/knn/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/knn/results/{primary,clause}/confusion_matrix.csv` | Confusion matrix |
| `models/knn/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison row |

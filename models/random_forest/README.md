# Random Forest

## What this method does

Random Forest is a bagging ensemble of decision trees. Each tree trains on a bootstrap sample with a random feature subset; predictions are majority-voted. Reduces variance compared to a single tree.

## Why we tested it

End-semester addition; tests whether bagging stabilizes tree predictions and improves over a single decision tree.

## Input features

Dense TruncatedSVD (100 components, training-fold fitted) of word unigram/bigram TF-IDF.

## Classifier

`sklearn.ensemble.RandomForestClassifier` (criterion=`gini`)

## Tuning

Bounded grid over `n_estimators` in {100, 200}, `max_depth` in {25, None}, `min_samples_leaf` in {2, 5}, `max_features`=`sqrt`, `class_weight`=`balanced_subsample`, selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

| Protocol | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP |
|----------|----------|----------|-----------------|--------------|----------|----------|
| Primary | 0.7828 | 0.7886 | 0.7632 | 0.7836 | 187 | 210 |
| Clause | 0.7804 | 0.7848 | 0.7475 | 0.7926 | 179 | 231 |

## Interpretation

Strong improvement over Decision Tree but still below Linear SVM on macro F1 (0.7828 vs 0.8206 primary). Large train-to-held-out gap indicates overfitting. Training is slow (~6s) due to 200 trees.

## Files

| Path | Contents |
|------|----------|
| `models/random_forest/config.json` | Reproducible configuration |
| `models/random_forest/run.py` | Runnable entry point |
| `models/random_forest/code.ipynb` | Educational notebook |
| `models/random_forest/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/random_forest/results/{primary,clause}/confusion_matrix.csv` | Confusion matrix |
| `models/random_forest/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison row |

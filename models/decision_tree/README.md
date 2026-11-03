# Decision Tree

## What this method does

A Decision Tree classifier partitions the TF-IDF feature space through sequential if/then rules. Each split selects the feature that best separates the classes by impurity (Gini). Produces an interpretable rule structure.

## Why we tested it

End-semester addition; tests whether rule-based nonlinear boundaries capture risky-clause patterns that linear models miss.

## Input features

Dense TruncatedSVD (100 components, training-fold fitted) of word unigram/bigram TF-IDF. SVD is required because trees operate poorly on raw high-dimensional sparse text. SVD is a feature transform, not a classifier.

## Classifier

`sklearn.tree.DecisionTreeClassifier` (criterion=`gini`)

## Tuning

Bounded grid over `max_depth` in {15, 30, None}, `min_samples_leaf` in {2, 10}, `ccp_alpha` in {0.0, 0.001}, `class_weight`=`balanced`, selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

| Protocol | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP |
|----------|----------|----------|-----------------|--------------|----------|----------|
| Primary | 0.6366 | 0.6411 | 0.6075 | 0.6412 | 310 | 358 |
| Clause | 0.6920 | 0.6931 | 0.6422 | 0.7196 | 242 | 346 |

## Interpretation

Weakest of the standard methods on macro F1. Large train-to-held-out gap indicates overfitting on dense-reduced text. Not selected for production; Linear SVM is clearly stronger.

## Files

| Path | Contents |
|------|----------|
| `models/decision_tree/config.json` | Reproducible configuration |
| `models/decision_tree/run.py` | Runnable entry point |
| `models/decision_tree/code.ipynb` | Educational notebook |
| `models/decision_tree/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/decision_tree/results/{primary,clause}/confusion_matrix.csv` | Confusion matrix |
| `models/decision_tree/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison row |

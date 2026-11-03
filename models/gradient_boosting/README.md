# Gradient Boosting (HistGradientBoostingClassifier)

## What this method does

Gradient Boosting builds a sequential ensemble of shallow decision trees. Each new tree fits the negative gradient (residuals) of the previous ensemble, scaled by a learning rate. Histogram-based binning makes it scalable. The implementation is sklearn's `HistGradientBoostingClassifier`; no separate boosting library is added.

## Why we tested it

End-semester addition; tests whether sequentially correcting prior errors improves over bagging and linear baselines.

## Input features

Dense TruncatedSVD (100 components, training-fold fitted) of word unigram/bigram TF-IDF.

## Classifier

`sklearn.ensemble.HistGradientBoostingClassifier` (loss=`log_loss`)

## Tuning

Bounded grid over `max_iter` in {100, 200}, `learning_rate` in {0.05, 0.1}, `max_leaf_nodes` in {15, 31}, selected by mean macro F1 on fixed group-respecting CV folds.

## Actual results (development-only; test not used)

| Protocol | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP |
|----------|----------|----------|-----------------|--------------|----------|----------|
| Primary | 0.7867 | 0.7938 | 0.7719 | 0.7870 | 184 | 201 |
| Clause | 0.7969 | 0.8009 | 0.7765 | 0.8053 | 168 | 200 |

## Interpretation

Close to Random Forest on macro F1 but still below Linear SVM (0.7867 vs 0.8206 primary). Large train-to-held-out gap indicates overfitting. No separate boosting library is used — this is sklearn's HistGradientBoosting.

## Files

| Path | Contents |
|------|----------|
| `models/gradient_boosting/config.json` | Reproducible configuration |
| `models/gradient_boosting/run.py` | Runnable entry point |
| `models/gradient_boosting/code.ipynb` | Educational notebook |
| `models/gradient_boosting/results/{primary,clause}/metrics.csv` | Validation metrics |
| `models/gradient_boosting/results/{primary,clause}/confusion_matrix.csv` | Confusion matrix |
| `models/gradient_boosting/artifacts/{primary,clause}/` | Fitted development pipeline |
| `results/comparison/{primary,clause}/comparison.csv` | Canonical comparison row |

# K-Nearest Neighbors Experiment

## What this method does

KNN classifies a clause by finding the k most similar training clauses in feature space and taking a majority vote. Similarity is measured by Euclidean or Manhattan distance over the dense SVD-reduced TF-IDF representation.

## Why we tested it

To evaluate whether a similarity-based, non-parametric method can identify risky clauses by analogy to previously seen examples, compared to linear and tree-based methods.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | Word unigram/bigram TF-IDF, max_features=60000, then training-fold TruncatedSVD to 100 dense components |
| Tuning grid | n_neighbors in {5, 15, 31}, weights in {uniform, distance}, metric in {euclidean, manhattan} |
| Selection rule | Max mean macro F1 across 3 fixed group folds (training only) |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_expanded_classical_tuning.py --protocol both
python models/knn/run.py --protocol both
python models/knn/run.py --protocol primary --smoke
python models/knn/run.py --protocol both --save-artifact
```

## Actual results (development-only)

### Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7837 |
| CV macro F1 (mean ± SD) | 0.7848 ± 0.00546 |
| Train macro F1 | ~0.999 |
| Risky precision | ~0.784 |
| Risky recall | ~0.774 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7787 |
| CV macro F1 (mean ± SD) | 0.7913 ± 0.00812 |
| Risky precision | ~0.777 |
| Risky recall | ~0.767 |

## Limitations

- High inference cost (must store all training vectors and compute distances at query time).
- Sparse lexical geometry in high-dimensional space is poorly captured by Euclidean/Manhattan distance.
- Train fit ~0.999 vs validation ~0.78 indicates overfitting/memorization.
- Below Linear SVM baseline.
- Development-only; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/knn/config.json` | Configuration |
| `models/knn/run.py` | Entry point |
| `models/knn/code.ipynb` | Notebook |
| `models/knn/results/{primary,clause}/` | Metrics, predictions, confusion matrix |
| `models/knn/artifacts/` | Fitted development pipeline (after `--save-artifact`) |

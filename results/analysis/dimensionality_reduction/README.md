# Dimensionality Reduction Analysis (PCA and Truncated SVD)

## What this analysis tests

Whether dimensionality reduction improves downstream classification:
1. **PCA on embeddings**: PCA (64 or 128 components) fitted within training folds on MiniLM 384-d embeddings, compared against raw embeddings.
2. **Truncated SVD**: 100-component training-fold SVD used as dense representation for tree/forest/boosting/KNN/RBF models.

## Important clarification

PCA and Truncated SVD are **feature transforms**, not supervised classifiers. They do not produce classification scores on their own. Results below reflect the downstream classifier combined with the transform.

## Canonical outputs

| Protocol | File | Description |
|----------|------|-------------|
| primary | `results/experiments/remaining_features_primary_v1/embedding_group_cv.csv` | Per-fold embedding CV with PCA options |
| primary | `results/experiments/remaining_features_primary_v1/embedding_group_cv_summary.csv` | PCA/embedding CV summary |
| primary | `results/experiments/remaining_features_primary_v1/embedding_selected_validation.csv` | Selected embedding validation |
| clause | `results/experiments/remaining_features_clause_v1/embedding_group_cv.csv` | Per-fold embedding CV with PCA options |
| clause | `results/experiments/remaining_features_clause_v1/embedding_group_cv_summary.csv` | PCA/embedding CV summary |
| clause | `results/experiments/remaining_features_clause_v1/embedding_selected_validation.csv` | Selected embedding validation |

## Key findings (development-only)

### PCA on embeddings (primary protocol)
| Configuration | CV Macro F1 | Notes |
|--------------|-------------|-------|
| Raw embeddings (PCA=None), LinearSVC C=1 | 0.7276 | Best among embedding configs |
| PCA=128, LinearSVC C=1 | ~0.7014 | Reduced |
| PCA=64, LinearSVC C=1 | ~0.6827 | Further reduced |
| Raw embeddings, LogisticRegression C=1 | ~0.7208 | Slightly below LinearSVC |

### Clause protocol
| Configuration | CV Macro F1 | Notes |
|--------------|-------------|-------|
| Raw embeddings (PCA=None), LinearSVC C=1 | 0.7353 | Best among embedding configs |
| PCA=128, LinearSVC C=1 | ~0.7014 | Reduced |
| PCA=64, LinearSVC C=1 | ~0.6827 | Further reduced |

## Conclusion

PCA consistently reduces embedding performance. Raw 384-d embeddings are best among embedding configs but still well below lexical TF-IDF Linear SVM (0.8316 primary / 0.8386 clause CV). PCA is not beneficial for this task.

## Runnable entry point

```
python results/analysis/dimensionality_reduction/run.py --protocol both
python results/analysis/dimensionality_reduction/run.py --protocol primary --smoke
```

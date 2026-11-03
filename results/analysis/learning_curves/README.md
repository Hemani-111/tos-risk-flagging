# Group-Aware Learning Curves Analysis

## What this analysis tests

How validation performance changes as the training set grows by whole service/text groups. Trains LinearSVC (C=1, class_weight=balanced) on 0.1, 0.25, 0.5, 0.75, 1.0 fractions of training groups (3 random samples each), evaluated on a fixed validation partition. Compares word TF-IDF vs MiniLM embeddings.

## Why we tested it

To determine whether more training data would improve the selected model, and whether the embedding model is data-limited relative to the lexical model.

## Canonical outputs

| Protocol | File | Description |
|----------|------|-------------|
| primary | `results/experiments/remaining_features_primary_v1/group_learning_curves.csv` | Learning curve rows |
| clause | `results/experiments/remaining_features_clause_v1/group_learning_curves.csv` | Learning curve rows |

## Key findings (development-only)

### Primary protocol
| Representation | Fraction | Train rows | Validation macro F1 |
|---------------|----------|------------|---------------------|
| Word | 0.1 | ~1,280 | ~0.746 |
| Word | 0.5 | ~6,538 | ~0.808 |
| Word | 1.0 | 13,439 | ~0.820 |
| Embedding | 0.1 | ~99 | ~0.660 |
| Embedding | 0.5 | ~6,732 | ~0.696 |
| Embedding | 1.0 | 13,439 | ~0.719 |

### Clause protocol
| Representation | Fraction | Train rows | Validation macro F1 |
|---------------|----------|------------|---------------------|
| Word | 0.1 | ~1,308 | ~0.750 |
| Word | 0.5 | ~6,538 | ~0.808 |
| Word | 1.0 | 13,434 | ~0.819 |
| Embedding | 0.1 | ~1,308 | ~0.674 |
| Embedding | 0.5 | ~9,807 | ~0.720 |
| Embedding | 1.0 | 13,434 | ~0.725 |

## Conclusion

Word TF-IDF improves with more data and reaches ~0.82 at full training. Embeddings plateau lower (~0.719-0.725) even with full data, confirming they are not a viable replacement for TF-IDF on this dataset.

## Runnable entry point

```
python results/analysis/learning_curves/run.py --protocol both
python results/analysis/learning_curves/run.py --protocol primary --smoke
```

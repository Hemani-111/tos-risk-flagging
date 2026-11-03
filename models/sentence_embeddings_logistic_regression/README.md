# Sentence Embeddings + Logistic Regression Experiment

## What this method does

Encodes each clause with a frozen sentence-embedding model (MiniLM-L6-v2) into a 384-dimensional dense vector, then trains a Logistic Regression classifier on top. Embeddings are computed once locally on CPU and cached by text checksum + encoder revision. PCA reduction (64 or 128 components) is optionally applied within training folds.

## Why we tested it

To evaluate whether dense semantic representations outperform sparse lexical TF-IDF for clause-level risk classification, as part of the expanded end-semester representation experiments.

## Exact configurations

| Setting | Value |
|---------|-------|
| Encoder | sentence-transformers/all-MiniLM-L6-v2 |
| Encoder revision | b9db1e8a0d3a51769172ba8546f282a73f066e47 |
| License | Apache-2.0 |
| Dimensions | 384 |
| Max input | 256 wordpieces |
| Language | English |
| Inference | Local CPU only; no remote API |
| Classifier | LogisticRegression (C in {0.1, 1.0, 10.0}, class_weight=balanced) |
| PCA options | None, 64, 128 (training-fold fitted) |
| Selection rule | Max mean macro F1 across 3 fixed group folds |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_remaining_feature_experiments.py
python models/sentence_embeddings_logistic_regression/run.py --protocol both
python models/sentence_embeddings_logistic_regression/run.py --protocol primary --smoke
python models/sentence_embeddings_logistic_regression/run.py --protocol both --save-artifact
```

## Actual results (development-only)

### Primary protocol
| Metric | Value |
|--------|-------|
| Best CV macro F1 | 0.727594 (SD 0.00136) |
| Best configuration | LinearSVC C=1.0, no PCA (LR is slightly lower) |
| Validation macro F1 (LR) | ~0.7208 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Best CV macro F1 | 0.735312 (SD 0.00511) |
| Best configuration | LinearSVC C=1.0, no PCA |
| Validation macro F1 (LR) | ~0.7244 |

## Limitations

- Below lexical TF-IDF Linear SVM baseline (0.8316 primary CV / 0.8386 clause CV).
- Zero clauses exceeded the 256-wordpiece truncation limit.
- PCA reduction lowered embedding scores further.
- Semantic similarity does not capture lexical risk signals as well as TF-IDF for this dataset.
- Encoder weights are NOT duplicated across model folders; cached locally in data/cache/embeddings/ (Git-ignored).
- Development-only; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/sentence_embeddings_logistic_regression/config.json` | Configuration (encoder revision, dims, license) |
| `models/sentence_embeddings_logistic_regression/run.py` | Entry point |
| `models/sentence_embeddings_logistic_regression/code.ipynb` | Notebook |
| `models/sentence_embeddings_logistic_regression/results/{primary,clause}/` | Embedding CV metrics, selected validation, predictions |
| `models/sentence_embeddings_logistic_regression/artifacts/` | Fitted classifier (after `--save-artifact`) |
| `data/cache/embeddings/` | Cached MiniLM embeddings (Git-ignored, not duplicated) |

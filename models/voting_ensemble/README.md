# Voting Ensemble Experiment

## What this method does

Hard voting combines predictions from two base models (Logistic Regression and LinearSVC) by majority vote. Ties are resolved using a stable label order. Soft voting (averaging predicted probabilities) is also computed as a diagnostic.

## Why we tested it

To test whether combining complementary errors from LR and LinearSVC improves over the strongest individual member. Voting is simple, interpretable, and does not require training a meta-model.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | Fold-local word unigram/bigram TF-IDF, max_features=60000 |
| Base models | LogisticRegression (C=1.0, class_weight=balanced), LinearSVC (C=1.0, class_weight=balanced) |
| Ensemble rule | Hard majority vote; ties resolved by stable label order |
| OOF construction | Fold-local training on 3 fixed group folds; no group leakage |
| Soft voting | Probability-averaged (LR + calibrated SVC), diagnostic only |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_ensemble_calibration_clusters.py
python models/voting_ensemble/run.py --protocol both
python models/voting_ensemble/run.py --protocol primary --smoke
```

## Actual results (development-only)

### Primary protocol
| Metric | Hard Vote | Soft Vote | LinearSVC (baseline) |
|--------|-----------|-----------|---------------------|
| Validation macro F1 | ~0.8170 | ~0.8199 | ~0.8201 |

### Clause protocol
| Metric | Hard Vote | Soft Vote | LinearSVC (baseline) |
|--------|-----------|-----------|---------------------|
| Validation macro F1 | ~0.8175 | ~0.8217 | ~0.8195 |

## Limitations

- No clear macro-F1 gain over LinearSVC alone.
- Hard voting shifts the Risky precision/recall trade-off (recall up, precision down) without improving the primary metric.
- Probabilities are not calibrated legal-risk likelihoods.
- Development-only diagnostic; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/voting_ensemble/config.json` | Configuration |
| `models/voting_ensemble/run.py` | Entry point |
| `models/voting_ensemble/code.ipynb` | Notebook |
| `models/voting_ensemble/results/{primary,clause}/` | Ensemble metrics, predictions, OOF metrics |
| `results/experiments/ensemble_calibration_{protocol}_v1/` | Canonical outputs |

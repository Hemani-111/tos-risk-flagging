# Complement Naive Bayes Experiment

## What this method does

Complement Naive Bayes is a variant of Multinomial NB designed for imbalanced text classification. It estimates parameters from the complement of each class (all documents NOT in the class), which helps when classes are skewed.

## Why we tested it

As a Naive Bayes variant complementary to Multinomial NB (already covered at mid-semester). Complement NB is often more robust to class imbalance than standard NB.

## Exact configurations

| Setting | Value |
|---------|-------|
| Feature representation | Sparse word unigram/bigram TF-IDF, max_features=60000, min_df=2, max_df=0.99 |
| Model | ComplementNB(alpha=0.1, fit_prior=True, force_alpha=True) |
| Tuning | First-pass benchmark only; no bounded group-CV tuning |
| Seed | 20261102 |
| Protocols | Primary (unseen-service), Clause (duplicate-aware) |
| Locked test used | No |

## How to run

```
python scripts/run_model_benchmarks.py --protocol both
python models/complement_naive_bayes/run.py --protocol both
python models/complement_naive_bayes/run.py --protocol primary --smoke
python models/complement_naive_bayes/run.py --protocol both --save-artifact
```

## Actual results (development-only, first-pass benchmark)

### Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.7936 |
| Accuracy | ~0.7957 |
| Risky precision | ~0.733 |
| Risky recall | ~0.832 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | ~0.8037 |
| Accuracy | ~0.8051 |
| Risky precision | ~0.746 |
| Risky recall | ~0.825 |

## Limitations

- First-pass only; no bounded group-CV tuning over alpha or other parameters.
- Below Linear SVM baseline (0.8316 primary CV / 0.8386 clause CV).
- Naive Bayes independence assumption is simplistic for legal language.
- Development-only; not deployed.

## Files

| Path | Contents |
|------|----------|
| `models/complement_naive_bayes/config.json` | Configuration |
| `models/complement_naive_bayes/run.py` | Entry point |
| `models/complement_naive_bayes/code.ipynb` | Notebook |
| `models/complement_naive_bayes/results/{primary,clause}/` | Metrics, predictions, confusion matrix |
| `models/complement_naive_bayes/artifacts/` | Fitted development pipeline (after `--save-artifact`) |

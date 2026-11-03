# Calibration and Review-Coverage Analysis

## What this analysis tests

Group-fold sigmoid calibration of LinearSVC decision scores. Reports multiclass Brier score, log loss, Risky precision/recall, predicted-positive coverage, and equal-frequency reliability bins. Also includes soft voting (LR + calibrated SVC probabilities) as a diagnostic.

## Important clarification

Calibration is a **validation diagnostic only**. No automated abstention, no `Needs review` status, and no confidence percentage is deployed. Probabilities are not legal-risk likelihoods.

## Canonical outputs

| Protocol | File | Description |
|----------|------|-------------|
| primary | `results/experiments/ensemble_calibration_primary_v1/calibration_validation.json` | Calibration metrics |
| primary | `results/experiments/ensemble_calibration_primary_v1/calibration_validation_probabilities.csv` | Per-row calibrated probabilities |
| primary | `results/experiments/ensemble_calibration_primary_v1/risky_probability_reliability.csv` | Equal-frequency reliability bins |
| clause | `results/experiments/ensemble_calibration_clause_v1/calibration_validation.json` | Calibration metrics |
| clause | `results/experiments/ensemble_calibration_clause_v1/calibration_validation_probabilities.csv` | Per-row calibrated probabilities |
| clause | `results/experiments/ensemble_calibration_clause_v1/risky_probability_reliability.csv` | Equal-frequency reliability bins |

## Key findings (development-only)

### Primary protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8220 |
| Risky precision | 0.8038 |
| Risky recall | 0.8299 |
| Multiclass Brier score | 0.2489 |
| Multiclass log loss | 0.4593 |

### Clause protocol
| Metric | Value |
|--------|-------|
| Validation macro F1 | 0.8213 |
| Risky precision | 0.7914 |
| Risky recall | 0.8308 |
| Multiclass Brier score | 0.2523 |
| Multiclass log loss | 0.4620 |

## Conclusion

Calibration improves probability reliability but does not change the primary macro F1 materially. No user-facing confidence or abstention is deployed. Development-only diagnostic.

## Runnable entry point

```
python results/analysis/calibration/run.py --protocol both
python results/analysis/calibration/run.py --protocol primary --smoke
```

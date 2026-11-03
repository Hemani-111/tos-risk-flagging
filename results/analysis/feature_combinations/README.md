# Feature Combinations and Ablations Analysis

## What this analysis tests

Whether adding character n-grams or hand-crafted lexical indicators to word unigram/bigram TF-IDF improves classification performance. Tests four representations:
1. Word-only TF-IDF
2. Word + character TF-IDF (concatenated)
3. Lexical-only indicators
4. Word TF-IDF + lexical indicators

## Why we tested it

To determine whether richer feature representations justify their added complexity and cost over the simple word-only baseline.

## Canonical outputs

| Protocol | File | Description |
|----------|------|-------------|
| primary | `results/experiments/remaining_features_primary_v1/word_char_validation.csv` | Word+char validation result |
| primary | `results/experiments/remaining_features_primary_v1/word_char_group_cv.csv` | Word+char group-CV fold results |
| primary | `results/experiments/lexical_ablation_primary_v1/cv_summary.csv` | Lexical ablation CV summary |
| clause | `results/experiments/remaining_features_clause_v1/word_char_validation.csv` | Word+char validation result |
| clause | `results/experiments/remaining_features_clause_v1/word_char_group_cv.csv` | Word+char group-CV fold results |
| clause | `results/experiments/lexical_ablation_clause_v1/cv_summary.csv` | Lexical ablation CV summary |

## Key findings (development-only)

### Primary protocol
| Representation | Macro F1 | Notes |
|---------------|----------|-------|
| Word-only (LinearSVC C=1) | 0.8201 | Best practical choice |
| Word + character | 0.8180 | Slightly trails word-only |
| Lexical-only | 0.4449 | Weak standalone signal |
| Word + lexical | 0.8319 | Marginal gain, 12.7s fit vs 0.2s word-only |

### Clause protocol
| Representation | Macro F1 | Notes |
|---------------|----------|-------|
| Word-only (LinearSVC C=1) | 0.8195 | Best practical choice |
| Word + character | 0.8184 | Slightly trails word-only |
| Lexical-only | 0.4437 | Weak standalone signal |
| Word + lexical | 0.8395 | Marginal gain, 15.0s fit vs 0.18s word-only |

## Conclusion

Word-only TF-IDF remains the best practical choice. Character features add negligible value at higher cost. Lexical indicators alone are weak; combined features give marginal gains at ~60x the fit time. Not selected for production.

## Runnable entry point

```
python results/analysis/feature_combinations/run.py --protocol both
python results/analysis/feature_combinations/run.py --protocol primary --smoke
```

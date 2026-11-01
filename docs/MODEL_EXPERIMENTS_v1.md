# Phase 4: Initial model and feature comparisons

These are development results from `split_manifest_v1`. The primary protocol tests generalisation to unseen service components; the secondary protocol is duplicate-aware clause evaluation. Every vectorizer and dimensionality reduction transform was fitted on the training rows available to that fit. Validation is used for model review. The locked test partitions were not used.

## First-pass model families

All models below were fitted once on the protocol's training partition and scored on its validation partition. The sparse models use word TF-IDF unigrams and bigrams (min document frequency 2, max 60,000 features). Decision Tree, Random Forest, HistGradientBoosting, KNN, and RBF SVM use a 100-component TruncatedSVD representation fitted on training TF-IDF only. Dense and sparse representations are therefore intentionally identified separately.

| Model | Primary macro F1 | Primary Risky P/R | Secondary macro F1 | Secondary Risky P/R |
|---|---:|---:|---:|---:|
| Dummy prior | 0.196 | 0.000 / 0.000 | 0.193 | 0.000 / 0.000 |
| Multinomial NB | 0.798 | 0.737 / 0.837 | 0.803 | 0.746 / 0.825 |
| Complement NB | 0.794 | 0.733 / 0.832 | 0.804 | 0.755 / 0.819 |
| Logistic Regression | 0.819 | 0.794 / 0.834 | 0.808 | 0.779 / 0.819 |
| Linear SVM | **0.820** | 0.800 / 0.826 | **0.819** | 0.784 / 0.842 |
| RBF SVM on SVD | 0.806 | 0.794 / 0.806 | 0.806 | 0.770 / 0.817 |
| Decision Tree on SVD | 0.665 | 0.646 / 0.648 | 0.683 | 0.687 / 0.693 |
| Random Forest on SVD | 0.785 | 0.764 / 0.795 | 0.783 | 0.757 / 0.793 |
| HistGradientBoosting on SVD | 0.781 | 0.761 / 0.778 | 0.786 | 0.757 / 0.796 |
| KNN on SVD | 0.784 | 0.784 / 0.774 | 0.783 | 0.782 / 0.784 |

P/R means Risky precision and recall. These are single validation estimates and are not final test results. The neural or embedding option was not run; frozen sentence embeddings remain a conditional extension and are outside this first classical baseline.

## Grouped training-fold tuning

The fixed three grouped CV folds inside training were used to compare Logistic Regression and Linear SVM with balanced class weights and C in {0.1, 1, 10}. Each fold refits its own TF-IDF vectorizer. Feature representations were word unigrams, word unigrams/bigrams, and character `char_wb` 3–5 grams. Values below are mean macro F1 ± sample standard deviation across the three fixed folds.

| Protocol | Representation | Best model/config | Mean CV macro F1 ± SD |
|---|---|---|---:|
| Primary | Word unigram | Linear SVM, C=1 | 0.811 ± 0.008 |
| Primary | Word unigram/bigram | Linear SVM, C=1 | **0.832 ± 0.003** |
| Primary | Character 3–5 grams | Linear SVM, C=1 | 0.815 ± 0.004 |
| Secondary | Word unigram | Logistic Regression, C=1 | 0.819 ± 0.006 |
| Secondary | Word unigram/bigram | Linear SVM, C=1 | **0.839 ± 0.002** |
| Secondary | Character 3–5 grams | Logistic Regression, C=10 | 0.814 ± 0.001 |

The CV-selected balanced Linear SVM and Logistic Regression configurations were refit on all training rows and scored on validation. Primary validation macro F1 was 0.820 for Linear SVM (Risky P/R 0.797/0.826) and 0.816 for Logistic Regression (0.796/0.826). Secondary validation macro F1 was 0.819 for Linear SVM (0.787/0.845) and 0.816 for Logistic Regression (0.789/0.830). These differ from the initial unweighted screen; the validation results are the relevant development comparison after grouped tuning.

## Lexical feature ablation

Added log character count, log word count, mean word length, log sentence-count proxy, approximate Flesch reading ease, and a negation-presence flag to word TF-IDF. The six numeric values were standardized using training-fold values only. They were not combined with topic/service/label metadata.

| Protocol | Model | Text only CV macro F1 ± SD | Text + lexical CV macro F1 ± SD |
|---|---|---:|---:|
| Primary | Linear SVM | 0.8316 ± 0.0026 | 0.8319 ± 0.0030 |
| Primary | Logistic Regression | 0.8293 ± 0.0023 | 0.8287 ± 0.0031 |
| Secondary | Linear SVM | 0.8386 ± 0.0021 | 0.8395 ± 0.0025 |
| Secondary | Logistic Regression | 0.8379 ± 0.0024 | 0.8353 ± 0.0036 |

The lexical-only representation reached 0.445 ± 0.006 (primary) and 0.444 ± 0.001 (secondary) for Linear SVM; Logistic Regression reached 0.449 ± 0.003 and 0.448 ± 0.004. It is substantially weaker than text features.

The tiny SVM differences are not a persuasive improvement, while the lexical SVM fits took about 14 seconds per fold compared with about 0.2 seconds for text only. Some lexical SVM fits emitted convergence warnings at 5,000 iterations. The six features are not retained in the candidate pipeline based on this evidence. The rough readability and sentence-count measures remain exploratory only.

## Interpretation and next steps

Linear sparse-text models are the strongest simple candidates in this first comparison. SVD-based tree and neighbor models provide lower-performing course-method comparisons. Unigram/bigram features beat the tested unigram-only and character-only representations in grouped training CV. There is no result here that justifies replacing the current deployed model.

Before selection, Phase 5 should inspect development errors, calibration/abstention evidence where justified, and document-level behavior. The test set remains locked until the candidate and selection procedure are frozen. All runs include validation or CV predictions, class metrics, confusion matrices, parameters, timing and protocol metadata under `results/experiments/`.

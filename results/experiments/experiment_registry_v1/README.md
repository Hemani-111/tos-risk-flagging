# Consolidated experiment registry

Generated from saved run metadata and result files. Macro F1 is the registered primary metric; Risky precision and recall are reported alongside it. Entries are development-only unless a future freeze record explicitly states otherwise.

Generated 2026-11-02T21:25:50.757797+00:00 UTC; data SHA-256 `cee557cc927d754cf17675154ed5e1e32eee2fdb9af6700c526e62cd66969f8c`.

## Development classification results

| Run | Protocol | Model | Representation | CV macro F1 | Validation macro F1 | Risky P | Risky R |
|---|---|---|---|---:|---:|---:|---:|
| ensemble_calibration_clause_v1 | clause | sigmoid_calibrated_linear_svc | word unigram/bigram TF-IDF; group-fold calib | - | 0.8213 | 0.7914 | 0.8308 |
| ensemble_calibration_primary_v1 | primary | sigmoid_calibrated_linear_svc | word unigram/bigram TF-IDF; group-fold calib | - | 0.8220 | 0.8038 | 0.8299 |
| benchmark_clause_wordtfidf_v1 | clause | decision_tree_svd | dense_svd100 | - | 0.6831 | 0.6866 | 0.6929 |
| benchmark_clause_wordtfidf_v1 | clause | hist_gradient_boosting_svd | dense_svd100 | - | 0.7865 | 0.7566 | 0.7961 |
| benchmark_clause_wordtfidf_v1 | clause | knn_svd | dense_svd100 | - | 0.7831 | 0.7818 | 0.7845 |
| benchmark_clause_wordtfidf_v1 | clause | linear_svm | sparse_word_tfidf_uni_bi | - | 0.8189 | 0.7843 | 0.8424 |
| benchmark_clause_wordtfidf_v1 | clause | logistic_regression | sparse_word_tfidf_uni_bi | - | 0.8084 | 0.7786 | 0.8192 |
| benchmark_clause_wordtfidf_v1 | clause | random_forest_svd | dense_svd100 | - | 0.7830 | 0.7575 | 0.7926 |
| ensemble_calibration_clause_v1 | clause | hard_vote | word TF-IDF; LR/LinearSVC | 0.8338 | 0.8175 | 0.7653 | 0.8691 |
| ensemble_calibration_clause_v1 | clause | linear_svc | word TF-IDF; LR/LinearSVC | 0.8386 | 0.8195 | 0.7873 | 0.8447 |
| ensemble_calibration_clause_v1 | clause | logistic_regression | word TF-IDF; LR/LinearSVC | 0.8279 | 0.8137 | 0.7823 | 0.8285 |
| ensemble_calibration_clause_v1 | clause | soft_vote_lr_plus_sigmoid_svc | word TF-IDF; LR/LinearSVC | - | 0.8217 | 0.7907 | 0.8320 |
| ensemble_calibration_clause_v1 | clause | stacking_logistic_meta | word TF-IDF; LR/LinearSVC | - | 0.8215 | 0.7952 | 0.8366 |
| expanded_classical_clause_v1 | clause | decision_tree | word TF-IDF + SVD-100 | 0.6737 | 0.6920 | 0.6422 | 0.7196 |
| expanded_classical_clause_v1 | clause | hist_gradient_boosting | word TF-IDF + SVD-100 | 0.8046 | 0.7969 | 0.7765 | 0.8053 |
| expanded_classical_clause_v1 | clause | knn | word TF-IDF + SVD-100 | 0.7913 | 0.7787 | 0.7770 | 0.7671 |
| expanded_classical_clause_v1 | clause | random_forest | word TF-IDF + SVD-100 | 0.7847 | 0.7771 | 0.7470 | 0.7868 |
| remaining_features_clause_v1 | clause | linear_svc | word 1-2gram plus character 3-5gram TF-IDF;  | 0.7353 | 0.7254 | 0.7105 | 0.7138 |
| remaining_features_clause_v1 | clause | word+char tfidf | word 1-2gram plus character 3-5gram TF-IDF;  | 0.8380 | 0.8184 | 0.7856 | 0.8366 |
| tuned_validation_clause_v1 | clause | linear_svm | word_tfidf_unigram_bigram | 0.8386 | 0.8195 | 0.7873 | 0.8447 |
| tuned_validation_clause_v1 | clause | logistic_regression | word_tfidf_unigram_bigram | - | 0.8159 | 0.7894 | 0.8297 |
| benchmark_primary_wordtfidf_v1 | primary | decision_tree_svd | dense_svd100 | - | 0.6653 | 0.6459 | 0.6481 |
| benchmark_primary_wordtfidf_v1 | primary | hist_gradient_boosting_svd | dense_svd100 | - | 0.7809 | 0.7610 | 0.7778 |
| benchmark_primary_wordtfidf_v1 | primary | knn_svd | dense_svd100 | - | 0.7837 | 0.7843 | 0.7743 |
| benchmark_primary_wordtfidf_v1 | primary | linear_svm | sparse_word_tfidf_uni_bi | - | 0.8204 | 0.7996 | 0.8264 |
| benchmark_primary_wordtfidf_v1 | primary | logistic_regression | sparse_word_tfidf_uni_bi | - | 0.8185 | 0.7941 | 0.8345 |
| benchmark_primary_wordtfidf_v1 | primary | random_forest_svd | dense_svd100 | - | 0.7851 | 0.7642 | 0.7951 |
| ensemble_calibration_primary_v1 | primary | hard_vote | word TF-IDF; LR/LinearSVC | 0.8269 | 0.8170 | 0.7724 | 0.8565 |
| ensemble_calibration_primary_v1 | primary | linear_svc | word TF-IDF; LR/LinearSVC | 0.8316 | 0.8201 | 0.7969 | 0.8264 |
| ensemble_calibration_primary_v1 | primary | logistic_regression | word TF-IDF; LR/LinearSVC | 0.8205 | 0.8113 | 0.7922 | 0.8252 |
| ensemble_calibration_primary_v1 | primary | soft_vote_lr_plus_sigmoid_svc | word TF-IDF; LR/LinearSVC | - | 0.8199 | 0.7978 | 0.8310 |
| ensemble_calibration_primary_v1 | primary | stacking_logistic_meta | word TF-IDF; LR/LinearSVC | - | 0.8191 | 0.8089 | 0.8183 |
| expanded_classical_primary_v1 | primary | decision_tree | word TF-IDF + SVD-100 | 0.6681 | 0.6344 | 0.6092 | 0.6748 |
| expanded_classical_primary_v1 | primary | hist_gradient_boosting | word TF-IDF + SVD-100 | 0.7931 | 0.7867 | 0.7719 | 0.7870 |
| expanded_classical_primary_v1 | primary | knn | word TF-IDF + SVD-100 | 0.7848 | 0.7837 | 0.7843 | 0.7743 |
| expanded_classical_primary_v1 | primary | random_forest | word TF-IDF + SVD-100 | 0.7797 | 0.7828 | 0.7632 | 0.7836 |
| remaining_features_primary_v1 | primary | linear_svc | word 1-2gram plus character 3-5gram TF-IDF;  | 0.7276 | 0.7192 | 0.7110 | 0.7060 |
| remaining_features_primary_v1 | primary | word+char tfidf | word 1-2gram plus character 3-5gram TF-IDF;  | 0.8291 | 0.8180 | 0.8009 | 0.8241 |
| tuned_validation_primary_v1 | primary | linear_svm | word_tfidf_unigram_bigram | 0.8316 | 0.8201 | 0.7969 | 0.8264 |
| tuned_validation_primary_v1 | primary | logistic_regression | word_tfidf_unigram_bigram | - | 0.8164 | 0.7960 | 0.8264 |

## Representation and unsupervised analyses

| Analysis | Protocol | Result |
|---|---|---|
| feature_stability_Neutral | clause | top-100 coefficient-token Jaccard 0.4088 |
| feature_stability_Risky | clause | top-100 coefficient-token Jaccard 0.4712 |
| feature_stability_Safe | clause | top-100 coefficient-token Jaccard 0.3643 |
| feature_stability_Neutral | primary | top-100 coefficient-token Jaccard 0.4184 |
| feature_stability_Risky | primary | top-100 coefficient-token Jaccard 0.4024 |
| feature_stability_Safe | primary | top-100 coefficient-token Jaccard 0.3483 |
| KMeans k=12 | clause | sampled cosine silhouette 0.0979; seed ARI 0.7328 |
| KMeans k=3 | clause | sampled cosine silhouette 0.0765; seed ARI 0.9967 |
| KMeans k=5 | clause | sampled cosine silhouette 0.0847; seed ARI 0.9933 |
| KMeans k=8 | clause | sampled cosine silhouette 0.0892; seed ARI 0.8821 |
| KMeans k=12 | primary | sampled cosine silhouette 0.0905; seed ARI 0.7774 |
| KMeans k=3 | primary | sampled cosine silhouette 0.0751; seed ARI 0.9983 |
| KMeans k=5 | primary | sampled cosine silhouette 0.0835; seed ARI 0.9841 |
| KMeans k=8 | primary | sampled cosine silhouette 0.0911; seed ARI 0.9786 |
| full-group learning curve: embedding | primary | validation macro F1 0.7192 (SD 0.0000, 3 group samples) |
| full-group learning curve: word | primary | validation macro F1 0.8201 (SD 0.0000, 3 group samples) |
| full-group learning curve: embedding | clause | validation macro F1 0.7254 (SD 0.0000, 3 group samples) |
| full-group learning curve: word | clause | validation macro F1 0.8195 (SD 0.0000, 3 group samples) |

## Scope and limits

- The CSV and JSON contain model-family configurations, fold/validation results, runtime fields, stability metrics, cluster summaries, artifact directories, split and dataset hashes when present.
- `results/experiments/` run folders contain fold-level predictions/confusions and raw outputs. The registry does not replace those artifacts.
- Locked-test scores are recorded separately after the committed candidate freeze in `results/locked_evaluation_v1/` and `docs/LOCKED_TEST_EVALUATION_v1.md`; the prior loader boundary incident is disclosed.
- Independent full-document evaluation remains pending two authentic human review sheets and adjudication.

## One-time locked-test evaluation after freeze

| Protocol | Test macro F1 | Accuracy | Risky precision | Risky recall | Group-bootstrap macro F1 interval |
|---|---:|---:|---:|---:|---:|
| clause | 0.8144 | 0.8190 | 0.7922 | 0.8117 | 0.7989–0.8301 |
| primary | 0.8358 | 0.8395 | 0.8229 | 0.8287 | 0.8205–0.8496 |

These are the first scored locked-test results after the documented in-memory loader boundary incident. No test metrics were used for model selection. See the freeze and locked-evaluation report for details.

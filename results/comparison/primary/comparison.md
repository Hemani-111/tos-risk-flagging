# Model Comparison

Protocol: primary  |  Split: split_manifest_v1  |  Seed: 20261102
Development train rows: 13439  |  Validation rows: 2658
Locked test used: False  |  Generated: 2026-11-03T17:47:27.696543+00:00

| Model | Representation | CV macro F1 (±SD) | Val macro F1 | Accuracy | Risky P/R | Risky FN/FP | Train macro F1 | Grid fit (s) |
|-------|----------------|-------------------|--------------|----------|-----------|-------------|----------------|--------------|
| linear_svm | sparse_word_tfidf_uni_bi | 0.8321 (±0.0009) | 0.8204 | 0.8258 | 0.7996/0.8264 | 150/179 | 0.9926 | 6.70 |
| logistic_regression | sparse_word_tfidf_uni_bi | 0.8299 (±0.0021) | 0.8164 | 0.8213 | 0.7960/0.8264 | 150/183 | 0.9948 | 11.89 |
| multinomial_nb | sparse_word_tfidf_uni_bi | 0.8085 (±0.0063) | 0.7980 | 0.8002 | 0.7370/0.8368 | 141/258 | 0.9156 | 0.16 |
| rbf_svm | dense_svd100 | 0.8040 (±0.0082) | 0.7980 | 0.8036 | 0.7864/0.7882 | 183/185 | 0.9640 | 263.72 |
| gradient_boosting | dense_svd100 | 0.7932 (±0.0028) | 0.7867 | 0.7938 | 0.7719/0.7870 | 184/201 | 0.9992 | 45.29 |
| knn | dense_svd100 | 0.7814 (±0.0067) | 0.7837 | 0.7889 | 0.7843/0.7743 | 195/184 | 0.9993 | 0.45 |
| random_forest | dense_svd100 | 0.7803 (±0.0048) | 0.7828 | 0.7886 | 0.7632/0.7836 | 187/210 | 0.9985 | 66.04 |
| decision_tree | dense_svd100 | 0.6627 (±0.0018) | 0.6344 | 0.6373 | 0.6092/0.6748 | 281/374 | 0.6953 | 39.16 |

## Notes
- TF-IDF is the primary text representation (word unigram/bigram, max_features=60000).
- TruncatedSVD (100 components, training-fold fitted) is used only where dense input is justified (RBF SVM, Decision Tree, Random Forest, KNN, Gradient Boosting).
- SVD is a feature transform, not a classifier. Differing feature pipelines are explicitly labelled and not described as identical inputs.
- CV macro F1 is computed on the three fixed group-respecting development folds (TF-IDF/SVD refit inside each fold). Validation macro F1 is evaluated on held-out validation data after refitting on all training data.
- Train macro F1 is reported for overfitting diagnosis; it is not used for selection.
- Selection is by validation macro F1; CV is used for tuning only. Test data is never used.
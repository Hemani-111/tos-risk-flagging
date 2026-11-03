# Model Comparison

Protocol: primary  |  Split: split_manifest_v1  |  Seed: 20261102
Development train rows: 13439  |  Validation rows: 2658
Locked test used: False  |  Generated: 2026-11-03T13:28:24.870756+00:00

| Model | Representation | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP | Fit (s) |
|-------|----------------|----------|----------|-----------------|--------------|----------|----------|---------|
| linear_svm | sparse_word_tfidf_uni_bi | 0.8206 | 0.8258 | 0.7886 | 0.8461 | 133 | 196 | 0.24 |
| logistic_regression | sparse_word_tfidf_uni_bi | 0.8185 | 0.8243 | 0.7941 | 0.8345 | 143 | 187 | 0.94 |
| rbf_svm | dense_svd100 | 0.8064 | 0.8108 | 0.7936 | 0.8056 | 168 | 181 | 11.89 |
| multinomial_nb | sparse_word_tfidf_uni_bi | 0.7980 | 0.8002 | 0.7370 | 0.8368 | 141 | 258 | 0.04 |
| gradient_boosting | dense_svd100 | 0.7867 | 0.7938 | 0.7719 | 0.7870 | 184 | 201 | 3.74 |
| knn | dense_svd100 | 0.7837 | 0.7889 | 0.7843 | 0.7743 | 195 | 184 | 0.02 |
| random_forest | dense_svd100 | 0.7828 | 0.7886 | 0.7632 | 0.7836 | 187 | 210 | 5.95 |
| decision_tree | dense_svd100 | 0.6366 | 0.6411 | 0.6075 | 0.6412 | 310 | 358 | 1.54 |

## Notes
- TF-IDF is the primary text representation (word unigram/bigram, max_features=60000).
- TruncatedSVD (100 components, training-fold fitted) is used only where dense input is justified (RBF SVM, Decision Tree, Random Forest, KNN, Gradient Boosting).
- SVD is a feature transform, not a classifier. Differing feature pipelines are explicitly labelled and not described as identical inputs.
- Selection is by macro F1 on fixed group-respecting CV folds; test data is never used.
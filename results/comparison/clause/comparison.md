# Model Comparison

Protocol: clause  |  Split: split_manifest_v1  |  Seed: 20261102
Development train rows: 13434  |  Validation rows: 2607
Locked test used: False  |  Generated: 2026-11-03T17:58:02.270120+00:00

| Model | Representation | CV macro F1 (±SD) | Val macro F1 | Accuracy | Risky P/R | Risky FN/FP | Train macro F1 | Grid fit (s) |
|-------|----------------|-------------------|--------------|----------|-----------|-------------|----------------|--------------|
| linear_svm | sparse_word_tfidf_uni_bi | 0.8410 (±0.0021) | 0.8195 | 0.8236 | 0.7873/0.8447 | 134/197 | 0.9938 | 6.14 |
| logistic_regression | sparse_word_tfidf_uni_bi | 0.8397 (±0.0013) | 0.8159 | 0.8197 | 0.7894/0.8297 | 147/191 | 0.9942 | 13.11 |
| multinomial_nb | sparse_word_tfidf_uni_bi | 0.8140 (±0.0029) | 0.8033 | 0.8051 | 0.7463/0.8250 | 151/242 | 0.9198 | 0.26 |
| rbf_svm | dense_svd100 | 0.8115 (±0.0069) | 0.7986 | 0.8013 | 0.7695/0.8123 | 162/210 | 0.9654 | 116.01 |
| gradient_boosting | dense_svd100 | 0.7985 (±0.0034) | 0.7969 | 0.8009 | 0.7765/0.8053 | 168/200 | 0.9996 | 43.55 |
| knn | dense_svd100 | 0.7878 (±0.0022) | 0.7787 | 0.7840 | 0.7770/0.7671 | 201/190 | 0.9996 | 0.38 |
| random_forest | dense_svd100 | 0.7849 (±0.0056) | 0.7783 | 0.7825 | 0.7483/0.7856 | 185/228 | 0.9987 | 48.97 |
| decision_tree | dense_svd100 | 0.6760 (±0.0049) | 0.6920 | 0.6931 | 0.6422/0.7196 | 242/346 | 0.7238 | 25.64 |

## Notes
- TF-IDF is the primary text representation (word unigram/bigram, max_features=60000).
- TruncatedSVD (100 components, training-fold fitted) is used only where dense input is justified (RBF SVM, Decision Tree, Random Forest, KNN, Gradient Boosting).
- SVD is a feature transform, not a classifier. Differing feature pipelines are explicitly labelled and not described as identical inputs.
- CV macro F1 is computed on the three fixed group-respecting development folds (TF-IDF/SVD refit inside each fold). Validation macro F1 is evaluated on held-out validation data after refitting on all training data.
- Train macro F1 is reported for overfitting diagnosis; it is not used for selection.
- Selection is by validation macro F1; CV is used for tuning only. Test data is never used.
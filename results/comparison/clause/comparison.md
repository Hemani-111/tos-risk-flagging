# Model Comparison

Protocol: clause  |  Split: split_manifest_v1  |  Seed: 20261102
Development train rows: 13434  |  Validation rows: 2607
Locked test used: False  |  Generated: 2026-11-03T13:35:40.938822+00:00

| Model | Representation | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FN | Risky FP | Fit (s) |
|-------|----------------|----------|----------|-----------------|--------------|----------|----------|---------|
| linear_svm | sparse_word_tfidf_uni_bi | 0.8195 | 0.8236 | 0.7873 | 0.8447 | 134 | 197 | 0.46 |
| logistic_regression | sparse_word_tfidf_uni_bi | 0.8159 | 0.8197 | 0.7894 | 0.8297 | 147 | 191 | 1.84 |
| rbf_svm | dense_svd100 | 0.8060 | 0.8097 | 0.7705 | 0.8169 | 158 | 210 | 12.92 |
| multinomial_nb | sparse_word_tfidf_uni_bi | 0.8033 | 0.8051 | 0.7463 | 0.8250 | 151 | 242 | 0.04 |
| gradient_boosting | dense_svd100 | 0.7969 | 0.8009 | 0.7765 | 0.8053 | 168 | 200 | 3.93 |
| knn | dense_svd100 | 0.7831 | 0.7886 | 0.7818 | 0.7845 | 186 | 189 | 0.02 |
| random_forest | dense_svd100 | 0.7804 | 0.7848 | 0.7475 | 0.7926 | 179 | 231 | 3.00 |
| decision_tree | dense_svd100 | 0.6920 | 0.6931 | 0.6422 | 0.7196 | 242 | 346 | 1.76 |

## Notes
- TF-IDF is the primary text representation (word unigram/bigram, max_features=60000).
- TruncatedSVD (100 components, training-fold fitted) is used only where dense input is justified (RBF SVM, Decision Tree, Random Forest, KNN, Gradient Boosting).
- SVD is a feature transform, not a classifier. Differing feature pipelines are explicitly labelled and not described as identical inputs.
- Selection is by macro F1 on fixed group-respecting CV folds; test data is never used.
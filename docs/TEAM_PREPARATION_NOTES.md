# Team preparation notes

Use these notes to explain the project's choices and limitations in a review or presentation. Replace the owner fields with the team's actual contributions; do not infer individual ownership from Git authorship alone.

## Contribution record template

| Team member | Work performed | Evidence/artifact | What they learned or would change |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

## Core concepts

### Text features and linear models

- **TF-IDF:** represents documents using token counts weighted to reduce the influence of terms common across many clauses. This project uses word unigrams and bigrams so individual terms and adjacent phrases can contribute.
- **Naive Bayes:** estimates class scores from token evidence with a conditional-independence assumption. It is fast and useful as a baseline, but the independence assumption is simplistic for language.
- **Logistic Regression:** learns a linear class boundary and maps scores to normalized probabilities. Probabilities can still be poorly calibrated, especially under distribution shift.
- **Linear SVM / LinearSVC:** learns class-separating margins in sparse TF-IDF space. It is compact and effective for this feature representation. Its decision scores are margins, not confidence percentages.
- **RBF SVM:** uses a nonlinear kernel to represent curved boundaries. It can be expensive to scale and less convenient to explain; this project keeps the older RBF artifact available for rollback while serving the frozen linear package.
- **Character n-grams:** use overlapping character sequences, helping with spelling variants and morphology. The tested word-plus-character configuration did not improve the selected word-only validation result.

### Other model families

- **Decision Tree:** partitions features through sequential rules. It can model nonlinear interactions but individual trees are prone to instability and overfitting.
- **Random Forest:** averages many trees trained with sample/feature randomness (bagging). It can reduce tree variance but dense high-dimensional text is a difficult fit and the tested results trailed the linear model.
- **Boosting:** builds a sequence of weak learners that focus on prior errors. The HistGradientBoosting run used bounded dense SVD features; its strong training fit did not translate into the best held-fold result.
- **KNN:** classifies using nearby training examples. Its behavior depends on the distance metric and neighborhood size; sparse lexical geometry and inference cost are practical concerns.
- **Hard voting:** combines class votes from separate models. It changed Risky precision/recall trade-offs but did not improve primary validation macro F1.
- **Stacking:** trains a second-stage model on out-of-fold predictions. Keeping those inputs group-fold out-of-fold prevents the meta-model from learning on in-sample base predictions.

### Representations and exploratory structure

- **Sentence embeddings:** encode text into a dense 384-dimensional vector using the pinned local MiniLM model. Semantics are represented more directly than in bag-of-words features, but in this dataset the embedding classifiers scored below lexical TF-IDF.
- **SVD/PCA:** reduce feature dimensions. SVD was used where dense classical estimators required it; PCA was tested on embeddings. Dimensionality reduction did not improve the selected scores.
- **K-means:** assigns vectors to k groups by minimizing within-cluster distance. These unsupervised clusters are not risk labels. Weak silhouette values mean the observed groupings should be treated as exploratory.

### Evaluation and uncertainty

- **Macro F1:** computes F1 per class and averages classes equally. It prevents the largest class from dominating the primary selection score. Report class-level metrics and supports alongside it.
- **Risky precision and recall:** precision describes the fraction of predicted Risky clauses that are labelled Risky; recall describes the fraction of labelled Risky clauses the model finds. Neither alone captures Safe and Neutral performance.
- **Grouped cross-validation:** keeps related service/text groups together across folds, reducing optimistic leakage from related examples. The primary protocol holds out services; the secondary protocol addresses duplicate-aware clause generalization.
- **Locked test:** used once after the written model freeze. No tuning followed the test results. The earlier loader boundary incident is disclosed; the test is therefore not called untouched.
- **Calibration:** assesses whether score magnitudes correspond to observed frequencies. It does not establish legal probabilities, identify unsupported inputs, or guarantee transfer to a new policy.
- **Bootstrap interval:** resamples whole test groups to reflect clustered clauses. It describes uncertainty under that resampling scheme, not a guarantee for future services.
- **Feature coefficients:** indicate which lexical features are associated with a linear model's class scores. Correlation, context, negation, and data provenance prevent treating them as causal or legal explanations.

## Questions the team should be ready to answer

1. What deployment situation does each split protocol approximate, and why are their scores not pooled?
2. Why is a no-flagged-clause result not evidence that a policy is safe?
3. What does the loader boundary incident mean for test-set claims?
4. Why did local embeddings not replace TF-IDF despite their semantic representation?
5. What exactly do the three manually reviewable terms documents measure, and what do they not measure?
6. Which parts can be reproduced locally, and which depend on human labels or an available Docker/presentation environment?

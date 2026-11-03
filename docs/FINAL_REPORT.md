# Terms of Service Risk Flagging with Machine Learning

**Project report — 3 November 2026**  
Course: DS3010 Introduction to Machine Learning, IIT Palakkad

> **Status:** Final end-semester report. Independent full-document evaluation (human review sheets) and Docker runtime verification remain open. The locked-test evaluation followed the documented freeze and was scored once; test results were not used for model selection. The earlier loader boundary incident is disclosed in [Candidate Freeze](FINAL_CANDIDATE_FREEZE.md); do not describe the test as untouched.

## Abstract

This project studies whether text classifiers can help readers find Terms of Service (ToS) clauses that deserve attention. It builds a reproducible English-language benchmark from ToS;DR case annotations, compares eight conventional text-classification methods under service-aware and duplicate-aware splits, and implements a web application for reviewing predictions in uploaded documents. The audited source contains 22,497 annotated excerpts; the scoped benchmark contains 19,189 conflict-free excerpts. The frozen word unigram/bigram TF-IDF LinearSVC is the strongest development method: primary validation macro F1 0.8206 (CV macro F1 0.8321 ± 0.0009) and test macro F1 0.8358. The secondary clause protocol scored validation macro F1 0.8195 (CV 0.8410 ± 0.0021) and test macro F1 0.8144. The locked-test scores followed the documented freeze and were not used for selection. A loader boundary incident is disclosed: earlier development runs materialized test text/labels in memory but did not calculate or review test metrics. Labels are case-derived annotations, not independent legal judgments. Complete-document performance remains unmeasured pending human review. The application is an educational screening aid, not legal advice or a safety guarantee.

## 1. Problem and scope

Long online policies are difficult to review. The project asks whether a model trained on annotated policy excerpts can prioritize clauses for human attention, and how well that signal generalizes to services excluded from training. The intended users are readers who want a navigational aid while reviewing policy text.

The three target classes are Safe, Neutral, and Risky, mapped from ToS;DR point classifications (“good” → Safe, “neutral” → Neutral, “bad”/“blocker” → Risky). “Safe” means the source category mapped to that label; it does not mean a clause or policy is safe in a legal or practical sense. Likewise, a Risky prediction is a prompt to inspect wording and context, not a legal conclusion. This version targets English text and short policy clauses. It does not establish performance on full policies, arbitrary text, other languages, or legal outcomes.

## 2. Data provenance and construction

The five local raw CSV files match all published MD5 checksums for Zenodo record 15012282 v1. The source record does not state a license, and the local retrieval date is unknown. The reconstruction selects approved points with nonblank quotes, validates joins to case and topic tables, and maps `good` to Safe, `neutral` to Neutral, and `bad`/`blocker` to Risky. Rebuilt ordered values match the historical processed file exactly.

The reconstructed set has 22,497 rows: 9,759 Neutral, 7,015 Risky, and 5,723 Safe. Eleven rows lack a document ID. Normalized text checks identify 338 repeated-text groups (505 excess rows) and 23 conflicting-label groups (52 records). Conflicting rows are retained in audit exports but excluded from the single-label benchmark. A rough language screen, minimum visible length, and conflict exclusion yield a benchmark of 19,189 rows: 8,097 Neutral, 6,285 Risky, and 4,807 Safe.

These are case-associated excerpts, not a random sample of policy sentences. A case can involve multiple points, so the case-derived target may not describe a clause in isolation. The automatic language detector is approximate. See [Dataset Card](DATASET_CARD.md) for construction details and limitations.

## 3. Research and evaluation design

Two protocols are reported separately:

1. **Primary unseen-service:** service components linked by exact text, document metadata, or reviewed near-duplicate evidence stay within a partition. The included split contains 13,439 training, 2,658 validation, and 2,585 locked-test rows.
2. **Secondary duplicate-aware clause:** normalized repeated-text components stay together, while services may appear in multiple partitions. The included split contains 13,434 training, 2,607 validation, and 2,602 locked-test rows.

Both use a fixed seed and pre-generated split manifest. Detected cross-partition duplicate candidates are removed from lower-priority holdouts under a documented rule. Near-duplicate detection is approximate and may miss overlap. Model and representation selection used training CV and validation only; the locked test was scored once after the freeze. The in-memory loader incident is documented in [Candidate Freeze](FINAL_CANDIDATE_FREEZE.md).

Macro F1 is the principal comparison metric. Risky-class precision and recall are reported as trade-offs. TF-IDF and dimensionality reduction are fit only on training data within each fold. Three fixed grouped CV folds within training guide model selection; validation supports development review. The protocol and commands are in [Experiment Protocol](EXPERIMENT_PROTOCOL.md).

## 4. Methods and results

The final comparison covers eight standard classifiers — Multinomial Naive Bayes, Logistic Regression, Linear SVM, RBF SVM, Decision Tree, Random Forest, K-Nearest Neighbours, and Gradient Boosting (sklearn's `HistGradientBoostingClassifier`) — trained and tuned on the same development data with fixed group-respecting splits.

**Representations (explicitly labelled, not identical inputs):**
- Sparse linear models — Multinomial NB, Logistic Regression, Linear SVM — use word unigram/bigram TF-IDF (`max_features=60000`, `min_df=2`, `max_df=0.99`, `sublinear_tf=True`), kept sparse.
- Dense models — RBF SVM, Decision Tree, Random Forest, KNN, Gradient Boosting — use a training-fold-fitted TruncatedSVD (100 components) projection of the same TF-IDF because those algorithms require dense input. SVD is a feature transform, not a classifier; differing feature pipelines are explicitly labelled and do not isolate algorithm/kernel differences.

Tuning used bounded grids with group-respecting CV (3 fixed folds). Table 1 reports validation metrics (held-out after refitting on all training data); CV macro F1 with fold standard deviation is shown for tuning transparency. Train macro F1 is reported for overfitting diagnosis and is not used for selection.

| Model | Rep. | CV macro F1 (±SD) | Val macro F1 | Accuracy | Risky P | Risky R | Risky FN | Risky FP | Train macro F1 | Fit (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| Linear SVM | Sparse TF-IDF | 0.8321 ± 0.0009 | 0.8206 | 0.8258 | 0.7886 | 0.8461 | 133 | 196 | 0.9926 | 0.45 |
| Logistic Regression | Sparse TF-IDF | 0.8299 ± 0.0021 | 0.8194 | 0.8213 | 0.7960 | 0.8264 | 150 | 183 | 0.9948 | 1.93 |
| Multinomial NB | Sparse TF-IDF | 0.8085 ± 0.0063 | 0.7980 | 0.8002 | 0.7370 | 0.8368 | 141 | 258 | 0.9156 | 0.05 |
| SVM — RBF | Dense SVD-100 | 0.8040 ± 0.0082 | 0.7984 | 0.8036 | 0.7864 | 0.7882 | 183 | 185 | 0.9640 | 14.02 |
| Gradient Boosting | Dense SVD-100 | 0.7932 ± 0.0028 | 0.7869 | 0.7938 | 0.7719 | 0.7870 | 184 | 201 | 0.9992 | 3.92 |
| Random Forest | Dense SVD-100 | 0.7803 ± 0.0048 | 0.7820 | 0.7886 | 0.7632 | 0.7836 | 187 | 210 | 0.9985 | 6.60 |
| K-Nearest Neighbours | Dense SVD-100 | 0.7814 ± 0.0067 | 0.7860 | 0.7889 | 0.7843 | 0.7743 | 195 | 184 | 0.9993 | 0.02 |
| Decision Tree | Dense SVD-100 | 0.6627 ± 0.0018 | 0.6433 | 0.6373 | 0.6092 | 0.6433 | 281 | 374 | 0.6953 | 1.57 |

**Interpretation.** Linear SVM is the strongest method on validation macro F1 (0.8206 primary) and is the deployed production model. Its advantage over Logistic Regression (0.8194) is small (0.0012) and should not be over-interpreted without significance analysis. Tree-based methods (Random Forest, Gradient Boosting, Decision Tree, KNN) show large train-to-validation gaps (train ≈ 0.999 vs validation ≈ 0.78–0.80), indicating overfitting on dense-reduced text. RBF SVM is close on macro F1 but ~60× slower to train than Linear SVM. Complement Naive Bayes, voting/stacking ensembles, sentence embeddings, K-means clustering, PCA on embeddings, and calibration/abstention experiments are not part of the final scope; their removal does not imply their earlier results were invalid.

Risky recall is consistently higher than Risky precision across methods — the models flag more clauses as Risky than they get right, so a missing Risky prediction does not establish safety and a Risky prediction should be inspected in context. Full per-class metrics, confusion matrices, training and prediction timings, selected parameters, and run metadata for all eight methods are in `results/comparison/{primary,clause}/comparison.csv` and each model folder under `models/`. Figures are in `results/comparison/figures/`.

### Controlled Linear-vs-RBF SVM comparison

For a direct kernel comparison on the same representation, both Linear and RBF SVM were run on the same training-fitted SVD-100 dense representation. RBF SVM (C=10, gamma=scale, class_weight=None) reached validation macro F1 0.7984 primary vs Linear SVM on dense SVD-100 at 0.8036. Linear SVM on its native sparse TF-IDF representation (0.8206) outperforms both dense variants. This controlled comparison is a separate development experiment labelled as such; it does not change the practical-pipeline results above.

### One-time frozen test evaluation

| Protocol | Test macro F1 | Accuracy | Risky precision | Risky recall | Group-bootstrap 95% interval |
|---|---:|---:|---:|---:|---|
| Primary unseen-service (2,585 clauses; 211 services) | 0.8358 | 0.8395 | 0.8229 | 0.8287 | 0.8205–0.8496 |
| Secondary duplicate-aware (2,602 clauses; 2,552 text groups) | 0.8144 | 0.8190 | 0.7922 | 0.8117 | 0.7989–0.8301 |

Intervals use 2,000 group-bootstrap resamples with replacement and seed 20261103. They describe sampled group variation and are not guarantees. The primary test had 153 Risky false positives and 147 false negatives; the secondary test had 182 and 161. Full per-class results and the boundary disclosure are in [Locked Test Evaluation](LOCKED_TEST_EVALUATION_v1.md). No score was used to select or modify the model.

## 5. Error analysis

On primary validation, the selected Linear SVM made 465 errors among 2,658 rows (17.5%): 179 Risky false positives and 150 Risky false negatives. On secondary validation, 460 errors among 2,607 rows (17.6%): 197 Risky false positives and 134 false negatives. Review examples suggest Neutral legal disclosures can share vocabulary with Risky examples, while broad discretion, unilateral changes, jurisdiction provisions, and collection disclosures require wider context. Some apparent errors may reflect source segmentation or the case-derived target rather than ordinary model failure. These observations are navigational review cues, not causal explanations.

## 6. Independent document evaluation

Six policy snapshots from three services absent from the benchmark are frozen locally. Two additional Perplexity pages could not be retrieved (HTTP 403) and are not in the frozen set. Blind review sheets cover 723 segmented clauses from three consumer Terms documents. Coverage verification checks all six frozen snapshots: emitted clauses cover 91.9%–98.7% of extracted-text characters. The earlier text mismatch came from extraction with PyPDF2 3.0.1 before the dependency upgrade; both local PDF text extracts and blind sheets were regenerated with current pypdf 6.21.4 before annotation. No human annotations have been supplied, so inter-reviewer agreement, adjudicated labels, document-level model metrics, and conclusions about full-policy generalization are unavailable. The existing ToS;DR excerpt labels are not used as document truth, and no synthetic labels were created. This evaluation gate must remain open until two independent reviewers complete their sheets and disagreements are adjudicated. See [Independent Document Evaluation](INDEPENDENT_DOCUMENT_EVALUATION.md) and `results/document_review_coverage_v1.json`.

## 7. Application and verification

The application accepts PDF, DOCX, and TXT uploads or pasted text and presents clause predictions for review. It provides class filters, search, source context, PDF page ranges where available, JSON/CSV exports, full extracted text with clause-offset highlights and unclassified spans, and print/Save as PDF. Results are kept tab-scoped with repeated clause text omitted from storage and reconstructed from source offsets. The backend uses bounded analysis concurrency and a request timeout; timeout cleanup waits for any active worker to finish reading its temporary upload. Selectable PDF text includes page mapping; scanned-image OCR is not claimed.

**Local verification (3 November 2026):** all 45 backend tests passed; frontend lint and production build passed; offline-vs-API prediction parity passed (identical labels, counts, and model version `linear-svc-primary-v2` for identical extracted clauses). Compose configuration parses, but a current `docker info` check could not open `//./pipe/dockerDesktopLinuxEngine`; Docker image build/start could not be verified. The local app and API start successfully, but screenshot-based browser review was blocked because the Windows browser helper could not resolve the active URL. Public-host configuration remains open. Performance samples and deployment limitations are recorded in [Deployment Readiness](DEPLOYMENT_READINESS_v1.md).

## 8. Ethical and product limitations

- Predictions summarize patterns in a particular crowdsourced, case-derived annotation set.
- Performance on validation clauses does not establish accuracy on whole policies or legal correctness.
- A Safe class prediction is not assurance that terms are benign; a missed Risky clause is possible.
- English filtering is approximate; other languages are outside the validated scope.
- Policies change over time, and the current interface does not provide a legal update-monitoring service.
- Source-data license is unspecified; confirm rights before redistribution.
- Uploaded policy text may be sensitive. A production deployment needs an explicit retention policy, transport security, rate limits, monitoring, and host-specific CORS/secrets.

## 9. Conclusion and next work

Grouped evaluation and one-time test scoring support sparse word TF-IDF with a LinearSVC for this benchmark. The end-semester additions — Decision Tree, Random Forest, KNN, and Gradient Boosting — were evaluated under the same protocol and did not exceed the Linear SVM baseline. A web application makes predictions reviewable, including the extracted source and offset highlights, but output remains triage assistance only. Next steps are authentic dual document review and adjudication, screenshot-based browser review, Docker verification when the engine is available, and host-specific deployment controls. No current evidence supports legal safety or complete-document performance.

## Reproduction and companion materials

Use the commands in [README](../README.md) and [Experiment Protocol](EXPERIMENT_PROTOCOL.md). The dataset audit and split manifests are versioned; raw data, frozen policy snapshots, and reviewer sheets remain outside Git. Companion files: [Dataset Card](DATASET_CARD.md), [Model Card](MODEL_CARD.md), [Model Experiments](MODEL_EXPERIMENTS_v1.md), [Error Analysis](ERROR_ANALYSIS_v1.md), and [Deployment Readiness](DEPLOYMENT_READINESS_v1.md). Comparison figures are in `results/comparison/figures/` (PNG and SVG).

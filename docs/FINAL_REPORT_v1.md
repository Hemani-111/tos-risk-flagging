# Terms of Service Risk Flagging with Machine Learning

**Evidence-based project report draft — 3 November 2026**  
Course: DS3010 Introduction to Machine Learning, IIT Palakkad

> **Draft status:** This report includes the frozen candidate's one-time test results. Independent full-document evaluation, Docker runtime verification, screenshot-based browser UX review, and public deployment checks remain open. The prior loader boundary incident is disclosed; do not describe the test as untouched.

## Abstract

This project studies whether text classifiers can help readers find Terms of Service (ToS) clauses that deserve attention. It builds a reproducible English-language benchmark from ToS;DR case annotations, compares conventional text-classification methods under service-aware and duplicate-aware splits, evaluates additional representations and ensembles, and implements a web application for reviewing predictions in uploaded documents. The audited source contains 22,497 annotated excerpts; the scoped benchmark contains 19,189 conflict-free excerpts. The frozen word unigram/bigram TF-IDF LinearSVC achieved primary grouped-CV macro F1 0.832 (SD 0.003), validation macro F1 0.820, and test macro F1 0.836. The secondary protocol scored 0.839 (SD 0.002), 0.819, and 0.814 respectively. The locked-test scores followed the documented freeze and were not used for selection. A loader boundary incident is disclosed: earlier development runs materialized test text and labels in memory but did not calculate or review test metrics. Labels are case-derived annotations, not independent legal judgments. Complete-document performance remains unmeasured pending human review. The application is an educational screening aid, not legal advice or a safety guarantee.

## 1. Problem and scope

Long online policies are difficult to review. The project asks whether a model trained on annotated policy excerpts can prioritize clauses for human attention, and how well that signal generalizes to services excluded from training. The intended users are readers who want a navigational aid while reviewing policy text.

The three target classes are Safe, Neutral, and Risky, mapped from ToS;DR point classifications. “Safe” means the source category mapped to that label; it does not mean a clause or policy is safe in a legal or practical sense. Likewise, a Risky prediction is a prompt to inspect wording and context, not a legal conclusion. This version targets English text and short policy clauses. It does not establish performance on full policies, arbitrary text, other languages, or legal outcomes.

## 2. Data provenance and construction

The five local raw CSV files match all published MD5 checksums for Zenodo record 15012282 v1. The source record does not state a license, and the local retrieval date is unknown. The reconstruction selects approved points with nonblank quotes, validates joins to case and topic tables, and maps `good` to Safe, `neutral` to Neutral, and `bad`/`blocker` to Risky. Rebuilt ordered values match the historical processed file exactly.

The reconstructed set has 22,497 rows: 9,759 Neutral, 7,015 Risky, and 5,723 Safe. Eleven rows lack a document ID. Normalized text checks identify 338 repeated-text groups (505 excess rows) and 23 conflicting-label groups (52 records). Conflicting rows are retained in audit exports but excluded from the single-label benchmark. A rough language screen, minimum visible length, and conflict exclusion yield a benchmark of 19,189 rows: 8,097 Neutral, 6,285 Risky, and 4,807 Safe.

These are case-associated excerpts, not a random sample of policy sentences. A case can involve multiple points, so the case-derived target may not describe a clause in isolation. The automatic language detector is approximate. See [Dataset Card](DATASET_CARD.md) for construction details and limitations.

## 3. Research and evaluation design

Two protocols are reported separately:

1. **Primary unseen-service:** service components linked by exact text, document metadata, or reviewed near-duplicate evidence stay within a partition. The included split contains 13,439 training, 2,658 validation, and 2,585 locked-test rows.
2. **Secondary duplicate-aware clause:** normalized repeated-text components stay together, while services may appear in multiple partitions. The included split contains 13,434 training, 2,607 validation, and 2,602 locked-test rows.

Both use a fixed seed and pre-generated split manifest. Detected cross-partition duplicate candidates are removed from lower-priority holdouts under a documented rule. Near-duplicate detection is approximate and may miss overlap. Candidate selection used training CV and validation only. The first scored locked-test results were produced after the freeze; the in-memory loader incident is documented in [Candidate Freeze](FINAL_CANDIDATE_FREEZE.md).

Macro F1 is the principal comparison metric. Risky-class precision and recall are reported as trade-offs. TF-IDF, scaling, and dimensionality reduction are fit only on training data within each fold. Three fixed grouped CV folds within training guide model and representation selection; validation supports development review. The protocol and commands are in [Experiment Protocol](EXPERIMENT_PROTOCOL.md).

## 4. Methods and results

The initial family screen compared Dummy, Multinomial and Complement Naive Bayes, Logistic Regression, Linear SVM, RBF SVM, Decision Tree, Random Forest, HistGradientBoosting, and KNN. Sparse linear models used word TF-IDF; selected nonlinear models used a 100-component SVD representation. The best single-pass validation macro F1 was 0.820 for Linear SVM on the primary split and 0.819 on the secondary split.

Grouped training-fold comparisons tested Logistic Regression and Linear SVM with word unigram, word unigram/bigram, and character 3–5-gram representations. The selected word unigram/bigram Linear SVM had the strongest grouped-CV result in both protocols. After refitting on all training rows, its validation results were:

| Protocol | CV macro F1 (mean ± SD) | Validation macro F1 | Risky precision | Risky recall |
|---|---:|---:|---:|---:|
| Primary unseen-service | 0.832 ± 0.003 | 0.820 | 0.797 | 0.826 |
| Secondary duplicate-aware clause | 0.839 ± 0.002 | 0.819 | 0.787 | 0.845 |

The balanced Logistic Regression validation macro F1 was 0.816 in both protocols. Lexical features added to word TF-IDF changed Linear SVM grouped-CV macro F1 only from 0.8316 to 0.8319 (primary) and 0.8386 to 0.8395 (secondary), while increasing fitting time and producing some convergence warnings. The small differences do not justify retaining that feature branch. Lexical-only models were substantially weaker (about 0.445 macro F1).

These metrics are not directly comparable to the historical ~85% RBF SVM figure in an earlier presentation: that figure's protocol is not reproduced here. Full first-pass comparisons, tuning, and ablation details are in [Model Experiments](MODEL_EXPERIMENTS_v1.md).

### Expanded representations and ensembles

The requested finite tuning searches compared Decision Tree, Random Forest, HistGradientBoosting, and KNN over 100-component SVD features under both protocols. HistGradientBoosting led these additional families, with grouped-CV/validation macro F1 of 0.793/0.787 primary and 0.805/0.797 secondary; its train-fold macro F1 was near 1.00, indicating overfit. It did not exceed the selected sparse linear model.

A pinned local `sentence-transformers/all-MiniLM-L6-v2` encoder (revision `b9db1e8a0d3a51769172ba8546f282a73f066e47`, Apache-2.0, 384 dimensions, 256 wordpieces) embedded 18,635 unique train/validation clauses on CPU in 636 seconds (29.3 clauses/second); none were truncated. The best embedding LinearSVC grouped-CV macro F1 was 0.728 primary and 0.735 secondary. PCA-reduced embeddings were lower. Word+character TF-IDF validation macro F1 was 0.818 primary and 0.818 secondary, slightly below word-only. Five group-aware learning-curve fractions, three random whole-group samples, and fold-wise coefficient stability were recorded.

Group-OOF hard voting and logistic stacking did not improve primary validation macro F1 over LinearSVC. Hard voting increased Risky recall at the expense of precision. Group-fold sigmoid calibration and a soft-vote diagnostic include Brier/log loss and Risky probability reliability bins; these remain research diagnostics and are not legal-risk likelihoods. Train-only MiniLM PCA/K-means tested k=3/5/8/12. Cosine silhouettes were weak (0.075-0.098), so clusters are exploratory. The complete registry is in `results/experiments/experiment_registry_v1/`.

### One-time frozen test evaluation

| Protocol | Test macro F1 | Accuracy | Risky precision | Risky recall | Group-bootstrap interval for macro F1 |
|---|---:|---:|---:|---:|---:|
| Primary unseen-service (2,585 clauses; 211 services) | 0.8358 | 0.8395 | 0.8229 | 0.8287 | 0.8205-0.8496 |
| Secondary duplicate-aware (2,602 clauses; 2,552 text groups) | 0.8144 | 0.8190 | 0.7922 | 0.8117 | 0.7989-0.8301 |

Intervals use 2,000 group-bootstrap resamples with replacement and seed 20261103. They describe sampled group variation and are not guarantees. The primary test had 153 Risky false positives and 147 false negatives; the secondary test had 182 and 161. Full per-class results and the boundary disclosure are in [Locked Test Evaluation](LOCKED_TEST_EVALUATION_v1.md). No score was used to select or modify the model.

## 5. Error and uncertainty analysis

On validation, the selected Linear SVM made 465 errors among 2,658 primary rows (17.5%) and 460 among 2,607 secondary rows (17.6%). Primary errors included 182 Risky false positives and 150 Risky false negatives; secondary errors included 197 and 134 respectively. Review examples suggest that Neutral legal disclosures can share vocabulary with Risky examples, while broad discretion, unilateral changes, jurisdiction provisions, and collection disclosures require wider context. Some apparent errors may reflect source segmentation or the case-derived target rather than ordinary model failure. These observations are navigational review cues, not causal explanations.

Balanced Logistic Regression (C=10) produced raw probabilities. On primary validation, accuracy was 0.821, multiclass Brier score 0.253, log loss 0.458, and top-label 10-bin ECE 0.023. Probabilities are not calibrated. Training-OOF-derived thresholds yielded 80.9%, 91.0%, and 95.7% validation coverage at target coverage levels of 80%, 90%, and 95%, with accepted-row error rates of 10.7%, 14.2%, and 16.2%. These exploratory results do not define a deployed abstention policy.

## 6. Independent document evaluation

Six policy snapshots from three services absent from the benchmark are frozen locally. Two additional Perplexity pages could not be retrieved (HTTP 403) and are not in the frozen set. Blind review sheets currently cover 719 segmented clauses from three consumer Terms documents. Coverage verification checks all six frozen snapshots: emitted clauses cover 90.9%-98.5% of extracted-text characters. The two Anthropic PDF extracts differ between the frozen review text and current API parser (29,319 vs 28,946 characters for Terms; 40,423 API-extracted characters for Privacy), so the review-sheet offsets are not claimed to match a fresh upload. No human annotations have been supplied, so inter-reviewer agreement, adjudicated labels, document-level model metrics, and conclusions about full-policy generalization are unavailable. The existing ToS;DR excerpt labels are not used as document truth, and no synthetic labels were created. This evaluation gate must remain open until two independent reviewers complete their sheets and disagreements are adjudicated. See [Independent Document Evaluation](INDEPENDENT_DOCUMENT_EVALUATION.md) and the coverage output at `results/document_review_coverage_v1.json`.

## 7. Application and verification

The application accepts PDF, DOCX, and TXT uploads or pasted text and presents clause predictions for review. It provides class filters, search, source context, PDF page ranges where available, JSON/CSV exports, full extracted text with clause-offset highlights and unclassified spans, and print/Save as PDF. Results are kept tab-scoped with repeated clause text omitted from storage and reconstructed from source offsets. The backend uses bounded analysis concurrency and a request timeout; timeout cleanup waits for any active worker to finish reading its temporary upload. Selectable PDF text includes page mapping; scanned-image OCR is not claimed.

Local verification on 3 November 2026: all 45 backend tests passed; Ruff passed for changed Python files; frontend lint and production build passed. Compose configuration parsed previously. A current `docker info` check could not open `//./pipe/dockerDesktopLinuxEngine`; Docker image build/start could not be verified. The local app and API start successfully, but screenshot-based browser review was blocked because the Windows browser helper could not resolve the active URL with enough confidence. Public-host configuration remains open. Performance samples and deployment limitations are recorded in [Deployment Readiness](DEPLOYMENT_READINESS_v1.md).

## 8. Ethical and product limitations

- Predictions summarize patterns in a particular crowdsourced, case-derived annotation set.
- Performance on validation clauses does not establish accuracy on whole policies or legal correctness.
- A Safe class prediction is not assurance that terms are benign; a missed Risky clause is possible.
- English filtering is approximate; other languages are outside the validated scope.
- Policies change over time, and the current interface does not provide a legal update-monitoring service.
- Source-data license is unspecified; confirm rights before redistribution.
- Uploaded policy text may be sensitive. A production deployment needs an explicit retention policy, transport security, rate limits, monitoring, and host-specific CORS/secrets.

## 9. Conclusion and next work

Grouped evaluation and one-time test scoring support sparse word TF-IDF with a LinearSVC for this benchmark. Added embeddings, word+character features, and ensembles did not improve the selected development comparison. A web application makes predictions reviewable, including the extracted source and offset highlights, but output remains triage assistance only. Next steps are authentic dual document review and adjudication, screenshot-based browser review, Docker verification when the engine is available, and host-specific deployment controls. No current evidence supports legal safety or complete-document performance.

## Reproduction and companion materials

Use the commands in [Project Context](../PROJECT_CONTEXT.md) and [Experiment Protocol](EXPERIMENT_PROTOCOL.md). The dataset audit and split manifests are versioned; raw data, frozen policy snapshots, and reviewer sheets remain outside Git. Companion files: [Dataset Card](DATASET_CARD.md), [Model Card](MODEL_CARD.md), [Model Experiments](MODEL_EXPERIMENTS_v1.md), [Error Analysis](ERROR_ANALYSIS_v1.md), and [Deployment Readiness](DEPLOYMENT_READINESS_v1.md).

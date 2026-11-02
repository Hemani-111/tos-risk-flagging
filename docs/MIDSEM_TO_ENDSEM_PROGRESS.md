# Midsemester to endsemester progress

**Status:** course narrative draft, 3 November 2026. Verify the course rubric and presentation requirements before submission.

## Midsemester baseline

The midsemester presentation framed the task as classifying short Terms of Service excerpts into Safe, Neutral, and Risky categories. It introduced the ToS;DR-derived dataset, a conventional text-classification pipeline, and early model comparisons. At that stage, the emphasis was on showing that standard classifiers could learn patterns from clause wording and reporting a headline accuracy figure. That figure is historical context only: the current dataset reconstruction, filtering, grouped splits, and model protocol differ, so it should not be compared directly with the final results.

## Endsemester work completed

### Dataset and evaluation design

- Reconstructed 22,497 source rows and defined a 19,189-row English, conflict-free benchmark. Conflicting normalized-text groups were quarantined.
- Established two fixed, checksummed protocols: primary unseen-service evaluation and secondary duplicate-aware clause evaluation.
- Made macro F1 the registered selection metric. Risky precision and recall accompany it; no minimum recall threshold was introduced.
- Expanded comparisons to Naive Bayes, Logistic Regression, Linear and RBF SVM, Decision Tree, Random Forest, HistGradientBoosting, KNN, word/character TF-IDF, and frozen local sentence embeddings.
- Added grouped cross-validation, validation comparison, learning curves, fold feature stability, PCA/K-means exploration, and ensemble/calibration diagnostics.
- Froze word unigram/bigram TF-IDF + class-weighted LinearSVC (C=1) before one locked-test evaluation. Primary unseen-service test macro F1 was 0.8358 (Risky precision 0.8229, recall 0.8287); secondary clause test macro F1 was 0.8144 (Risky precision 0.7922, recall 0.8117). The protocols answer different questions and their scores are not pooled.

### Application and reproducibility

- Packaged the frozen LinearSVC model with metadata and checksums and switched the local API to that version while retaining the previous RBF package for rollback.
- Added a full extracted-text view that preserves unclassified spans and highlights classified clauses by source offsets; added source export/print support and regression coverage for offset parity.
- Updated the experiment registry, model/data cards, report, deployment readiness notes, and local run instructions with actual outputs and limitations.
- Prepared a blind independent document-review pack. Three terms snapshots produce 719 clause rows per reviewer. Source-to-segment coverage is measured separately because clause sheets alone cannot reveal omitted content.

## Findings to explain in the presentation

1. The stronger result comes from lexical TF-IDF with a linear margin model; the compact MiniLM embedding experiments did not improve grouped-CV macro F1.
2. Adding character n-grams did not improve the selected development validation result. Tree, forest, boosting, KNN, voting, and stacking experiments did not displace the lexical LinearSVC.
3. Sigmoid calibration improved the availability of probability diagnostics, but those values are not legal-risk probabilities and automated abstention was not adopted.
4. PCA reduced embedding performance. Training-only K-means had weak cosine silhouette values (about 0.075–0.098), so clusters are exploratory and not deployed labels.
5. The classifier labels clauses, not whole policies. A policy with no flagged clause is not thereby shown to be safe.

## Evaluation caveat

During early development, the former shared loader materialized locked-test rows before scripts selected development folds. Those runs produced no test metrics or summaries and did not inform model choice, but the access incident means the test set must not be described as untouched. The candidate was frozen before test scoring; its scores were calculated once and did not trigger tuning. This boundary incident is disclosed in the candidate freeze and locked-evaluation report.

## Evidence still pending

- Two authentic independent reviewer sheets and adjudication; no labels have been invented. These are needed to estimate full-document extraction/segmentation and clause-label performance on the six local policy snapshots.
- Course rubric/requirements and final slide adaptation. A provisional six-slide content source is available in `PRESENTATION_STORYBOARD_v1.md`; editable PowerPoint export depends on an available presentation authoring runtime.
- Docker engine startup and mounted-model verification. Compose syntax and local backend/frontend checks pass, but container startup is not verified.
- Manual screenshot-driven browser review, because the Windows computer-use helper could not safely resolve the active browser URL. Local API, tests, lint, and production build checks remain available evidence, not a substitute for that visual review.
- Production host choice, HTTPS, rate limits, monitoring, host-specific CORS/secrets, and rollback rehearsal.

## Suggested oral defense

Explain why macro F1 is appropriate for a three-class problem with unequal class supports; why service-group separation tests a harder deployment shift than random clause splitting; why the learned linear coefficients are associations rather than legal explanations; why calibration does not prove out-of-domain detection; and why the three full-document snapshots are a small student-reviewed evaluation set rather than legal ground truth.

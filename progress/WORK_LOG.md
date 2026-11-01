# Work log

## 2026-11-02 â€” Initial data audit implementation

### Inspected

- Confirmed the working tree was clean on entry (`main`). Existing notebooks and the historical processed CSV were left unchanged.
- Local raw data exists: 31,706 points, 253 cases, 28 topics, 8,175 services, and 16,786 documents. `documents.csv` is about 268 MB.
- Read `notebooks/02_data_preprocessing.ipynb` to reconstruct its current join and label mapping.
- Branch creation was initially blocked under the earlier filesystem permission profile; after permissions changed, `project-completion` was created successfully. No reset or destructive Git operation was attempted.

### Implemented

- Added `scripts/audit_data.py`; it validates dimension-table key uniqueness, checks join cardinality, reconstructs the candidate, computes text duplicate/conflict groups, fingerprints all raw inputs, and writes separate audit/review outputs.
- Added the initial audit reports under `results/audits/` and candidate/review CSVs under `data/processed/audit_v1/`.
- Updated `.gitignore` so the versioned audit candidate/review exports can be tracked while the original processed data remains ignored as before.
- Added `PROJECT_CONTEXT.md` with the current milestone, findings, and reproduction commands.

### Evidence

- Command: `python scripts/audit_data.py` â€” completed successfully on 2 November 2026.
- Reconstructed 22,497 rows; exact ordered comparison with `data/processed/clauses_clean.csv` is true.
- Approved points: 23,968; nonblank quotes: 22,497; case/topic unmatched joins: 0/0; unknown classifications: 0.
- Labels: Neutral 9,759; Risky 7,015; Safe 5,723. Missing document IDs: 11.
- Duplicate audit: 338 normalized text groups, 505 excess rows; 23 conflicting groups, 52 records.
- Quote-quality checks: median 161 characters, 95th percentile 570, five quotes over 5,000 characters, 8,790 with HTML-like markup, two with common mojibake patterns, none with replacement characters. 245 cases have multiple quoted points; maximum 909 points for one case.
- All five local raw CSV MD5 hashes match Zenodo record 15012282 v1. The local retrieval date remains unknown; no license is stated on the record page.
- Environment used for this audit: Python 3.14.5, pandas 3.0.3.

### Initial audit outstanding items (resolved or superseded below)

- Broader quote quality/language/length and annotation context review; review all conflict rows and define benchmark treatment.
- Establish license and local retrieval date if available.
- Baseline backend/frontend setup and checks, hardware inventory, training dependency setup, and model behavior timing.
- Evaluation split protocol and manifests. No model training, app modifications, or automated test suite run in this milestone.

## 2026-11-02 â€” Phase 0 baseline complete

### Environment and dependency setup

- Created `.venv` with Python 3.11.9 (matches the backend Docker base image's Python minor version).
- Root `requirements.txt` now composes serving dependencies with pinned training/notebook requirements: pandas 2.2.3, matplotlib 3.9.4, and ipykernel 6.29.5.
- Corrected `aiofiles==23.3.1`, which does not exist on the package index, to 23.2.1.
- Changed the backend scikit-learn pin from 1.5.0 to 1.9.0. The existing artifacts emit `InconsistentVersionWarning` under 1.5.0 and SVC prediction fails (`TypeError: an integer is required`); using the saved artifact version restores predictions.
- `pip check` in `.venv`: no broken requirements. The pre-existing global environment has an unrelated `ultralytics-platform`/`httpx` conflict; it was not modified.
- Ran `npm ci` from the existing lockfile. npm reported 19 vulnerabilities (14 moderate, 4 high, 1 critical) and warned that Next.js 14.0.3 has a security advisory. Dependency remediation belongs in the planned security/deployment phase.
- Added `frontend/.eslintrc.json`, resolving the interactive first-run setup prompt. ESLint now reports no warnings or errors.

### Baseline checks

- `.venv` backend tests: `30 passed, 4 warnings`; warnings are FastAPI `on_event` and Pydantic `.dict()` deprecations.
- Frontend `npm run lint`: passed. `npm run build`: passed, including type validation and static page generation. `npm ci` preserved `package-lock.json`.
- `docker compose config --quiet`: passed; Compose notes the obsolete top-level `version` key.
- Local TestClient smoke request: HTTP 200, three clauses, outputs Risky/Safe/Risky. No document leaves the machine.
- Added `scripts/baseline_smoke.py`; `results/baseline/smoke_v1.json` records the fixture, artifact hashes, outputs, and one-run timings (about 0.005 s transform, 0.013 s prediction, 0.022 s API path). Treat as a repeatable smoke record, not a performance benchmark.
- Hardware/runtime: Windows 11; Intel i5-12450HX, 8 cores/12 logical processors, 16 GB RAM; Python 3.11.9; Node 24.15.0; npm 11.6.1; Docker 29.7.2 / Compose 5.3.1.
- Branch `project-completion` was created successfully.

### Phase 0 status

Baseline startup, dependency resolution, model loading, frontend checks, backend tests, and fixed-request behavior are now reproducible. Remaining app warnings and npm advisories are recorded for later remediation. Proceeding in order to Phase 1 data-quality/conflict review; no model experiments have started.

## 2026-11-02 â€” Phase 1 data-quality and preprocessing complete

### Data integrity and coverage

- Validated unique IDs for points, cases, topics, services, and documents. Audited pointâ†’case, pointâ†’service, pointâ†’document, and caseâ†’topic references: zero orphan references.
- Reproduced the existing 22,497-row clause table exactly. Candidate coverage is 1,781 services, 3,109 documents, 250 cases, and 27 topics; 11 rows lack `document_id`.
- Source cases contain 91 `good`, 81 `neutral`, 65 `bad`, and 16 `blocker`; approved quoted points map to Neutral 9,759, Risky 7,015, Safe 5,723. No unrecognized classification appears among usable rows.
- Original point IDs, case IDs, source classification, topic IDs/titles, service IDs, document IDs, and quote text are preserved.
- Quote audit: 304 quotes under 20 characters; median 161; 95th percentile 570; five over 5,000. HTML-like markup occurs in 8,790; replacement characters in zero; two match common mojibake markers.
- Approximate language screen (`langid` 1.1.6, visible text >=40 characters): English 19,227, French 628, Spanish 163, German 106, Chinese 114, and 527 other estimated-language rows; 1,895 short rows excluded. These are estimates, not validated language labels.
- 245 cases contain multiple approved quoted points, maximum 909. Case-level labels may summarize several issues and are not independently adjudicated sentence labels.

### Duplicate/conflict decisions

- Normalized exact-duplicate groups: 338 (843 rows, 505 excess); 281 occur within one case, 57 span cases, 295 span services, and 300 span documents (categories overlap).
- The exact-duplicate service graph connects 422 services in 66 components; the largest has 252 services. Policy: keep all source rows and keep linked services in one primary evaluation partition.
- Reviewed all 23 conflicting normalized-text groups (52 rows) with their case/topic/service metadata. Identical excerpt text has conflicting case-derived labels, so no single excerpt-only target is defensible from available fields. Quarantine all 52 from the single-label benchmark; preserve them in full candidate and review exports with rationale. The benchmark candidate has 22,445 rows.
- Initial multilingual near-duplicate audit: deterministic 32-permutation MinHash over character 4-grams, then exact Jaccard reranking; 2,455 pairs at >=0.72. The final English-benchmark audit was rerun separately in Phase 2.
- No source rows or original datasets were overwritten. Language/non-English and near-duplicate findings are limitations to report, not reasons to claim universal English-only coverage.

### Phase 1 status

Reconstruction counts reconcile, label mapping and keys are verified, conflict treatment is explicit/reproducible, and exact/high-confidence near-duplicate split constraints are recorded. Proceeding to Phase 2. No model experiment has started.

## 2026-11-02 â€” Phase 2 evaluation protocol and split manifests

### Scoped input and protocol

- Added a separate English-only benchmark of 19,189 conflict-free rows, selected by `langid` classification of visible text >=40 characters. Counts are Neutral 8,097, Risky 6,285, Safe 4,807. The full 22,497-row reconstruction and 22,445-row multilingual conflict-free benchmark remain available; no source rows were overwritten.
- Recomputed near-duplicate candidates on the English benchmark: 2,039 pairs at character 4-gram Jaccard >=0.72. Reviewed 43 pairs >=0.99 and connected their services/texts for partition isolation.
- Registered macro F1 as primary metric; Risky precision/recall, per-class metrics, confusion matrix, false positive/negative counts, runtime and resource costs as required reporting. Test set is locked; feature transforms must be fit inside training folds.
- Fixed seed: 20261102. One `StratifiedGroupKFold(20, shuffle=True)` assignment per protocol; train/validation/test are folds 0â€“13 / 14â€“16 / 17â€“19. Three-fold grouped CV is assigned only within training rows. No seed search.

### Manifests and overlap handling

- Primary protocol groups service components linked by normalized exact text, repeated document IDs, point/document service metadata mismatches, and reviewed near-duplicate pairs. Largest connected group: 29 services, 689 rows.
- Secondary protocol groups exact visible-text and reviewed near-duplicate components; services may overlap.
- For detected exact visible-text or near-duplicate links that cross partitions, keep the higher-priority partition (train, then validation, then test) and exclude matching text rows from lower-priority holdouts. Every excluded row remains in the manifest with an explicit reason.
- Five point rows have service IDs that disagree with document metadata (documents 347 and 1239); both service IDs are connected in the primary grouping.
- Primary included counts: train 13,439 (71.94%), validation 2,658 (14.23%), test 2,585 (13.84%); excluded from validation/test: 224/283.
- Secondary included counts: train 13,434 (72.06%), validation 2,607 (13.98%), test 2,602 (13.96%); excluded from validation/test: 270/276.
- Before exclusions, 870 candidate pairs crossed primary partitions and 859 crossed secondary partitions. After exclusions, exact text, service/document groups, and all detected candidate pairs have zero included partition crossings. LSH false negatives remain possible and are documented.

### Reproduction and status

- Added `scripts/create_splits.py`, `data/splits/split_manifest_v1.csv/.json`, `src/splitting.py::load_split_bundle`, `scripts/verify_split_manifest.py`, and `docs/EXPERIMENT_PROTOCOL.md`.
- The manifest passed a deterministic regeneration check; SHA-256 of `split_manifest_v1.csv` was `7DAD9EA1D242AC5BA8BEEC7128F740E73F373BF64A1631CCDC9FC4C0B08DDC6E` before and after regeneration.
- `python scripts/verify_split_manifest.py` validated dataset checksums, exact row-ID coverage, group and text isolation, CV assignments, class representation, and included counts for both protocols. `git diff --check` passed.
- No model training or result-based selection has been performed. Future experiments must load these manifests through `src/splitting.py`; do not make separate row splits.

## 2026-11-02 — Phase 3 development-only EDA

- Added `scripts/run_eda.py`; all summaries and plots use only included primary-protocol train and validation rows (16,097 clauses). The test partition was not read for EDA.
- Recorded class counts and shares (Risky 5,266/32.7%, Neutral 6,773/42.1%, Safe 4,058/25.2%); 27 topics and 1,358 services appear in development. The top 10 services contribute 4.2% of development rows.
- Saved topic/label and service/label counts, length/readability proxies, negation prevalence, and development-only class-associated word unigrams/bigrams. Negation is retained in text terms. Readability is a rough heuristic; phrase associations may reflect case-derived annotation context.
- Excluded retrospective identifiers, topic, service, and label fields from any proposed predictive features. No clustering or model error analysis was done; no model has been trained.
- Outputs: `results/eda/v1/EDA_REPORT.md`, JSON/CSV summaries, and five captioned PNG figures. Reviewed the phrase chart visually; captions state sample sizes and interpretation limits.
- First run revealed an ordering bug in topic composition plotting; corrected and reran successfully. `.venv` run completed with exit code 0. No locked-test data entered analysis.
- Phase 3 is complete. Next: Phase 4 model/feature experiments using frozen split manifests, with development-only selection and final test still locked.

## 2026-11-02 — Phase 4 model and feature experiments

### First-pass family comparison

- Added `scripts/run_model_benchmarks.py`; ran all ten planned baseline families separately under primary unseen-service and secondary duplicate-aware protocols. Fitted only on each train partition and scored only on validation. Sparse NB/LR/Linear SVM used word TF-IDF; tree, RF, HistGradientBoosting, KNN, and RBF SVM used training-fitted 100-component TruncatedSVD features. Each run saved per-class metrics, Risky precision/recall and FP/FN counts, confusion matrices, validation predictions, fit/inference timings, parameters, environment, warnings, and protocol metadata.
- Initial strongest validation macro F1 was Linear SVM: 0.820 primary and 0.819 secondary. These are one-pass development scores, not final test results. Dense baselines use a different representation, recorded in the report.

### Grouped tuning and representation comparison

- Added `scripts/run_grouped_cv_tuning.py`. It uses the manifest's three fixed training-only grouped folds and refits TF-IDF per fold. Compared Logistic Regression and Linear SVM, balanced weights, C={0.1, 1, 10}, word unigram, word unigram/bigram, and character 3–5 gram representations.
- Best grouped CV scores were word unigram/bigram Linear SVM C=1: 0.8316 ± 0.0026 primary and 0.8386 ± 0.0021 secondary. Word unigram and character-only variants were lower in both protocols.
- Added `scripts/evaluate_tuned_candidates.py`; CV-selected balanced Linear SVM C=1 and Logistic Regression C=10 were refit on the full training partition and scored once on validation. Validation Linear SVM macro F1 was 0.8201 primary (Risky P/R 0.797/0.826) and 0.8195 secondary (0.787/0.845). The locked test rows were never loaded into feature fitting or scoring.

### Numeric feature ablation and interpretation

- Added `scripts/run_lexical_feature_ablation.py`, comparing text-only, six lexical indicators only, and text plus indicators on the same fixed grouped folds. Numeric scaling was fit on each training fold. Lexical-only macro F1 was about 0.44; combined features gave 0.8319 primary and 0.8395 secondary for Linear SVM versus 0.8316 and 0.8386 for text alone. Logistic Regression decreased slightly with the combined features.
- The tiny SVM difference is not a persuasive gain; lexical SVM fits took roughly 13–15 seconds per fold versus about 0.2 seconds for text only. Some SVM fits emitted 5,000-iteration convergence warnings. Keep the simpler text representation for now; readability and sentence count remain heuristic.
- Added `docs/MODEL_EXPERIMENTS_v1.md` with first-pass family results, grouped tuning, feature ablation, and limits. Updated README, experiment protocol, and project context with reproduction commands.
- The initial benchmark's HistGradientBoosting run emits a Windows joblib physical-core detection warning but completes. It is preserved in the run metadata. No replacement model is selected and no production artifact was modified.
- Phase 4 completion gate met: all essential classical families were run or explicitly separated by representation, promising linear candidates were tuned on training folds, and tested representation/lexical comparisons are documented. Next is Phase 5 error, uncertainty, and document-level analysis.

## 2026-11-02 — Phase 5 development analysis (document review pending)

- Added `scripts/analyze_development_errors.py`; reviewed tuned Linear SVM validation predictions only. Primary protocol: 465/2,658 errors (17.5%), 182 Risky false positives and 150 false negatives. Secondary: 460/2,607 (17.6%), 197 false positives and 134 false negatives. The two linear candidates disagree on 71 primary and 80 secondary validation clauses.
- Saved full validation case tables, confusion-direction counts, deterministic human review examples, and heuristic term flags in `results/error_analysis/v1/`. Initial spot review found potential label/context mismatches and incomplete excerpts; flags are explicitly not causal explanations. No text or label was changed.
- Added `scripts/analyze_uncertainty.py` for balanced Logistic Regression C=10. It refits TF-IDF per fixed grouped training fold for OOF probabilities, then fits on train and evaluates validation. No test data was used. Validation: accuracy 0.821, multiclass Brier 0.253, log loss 0.458, top-label 10-bin ECE 0.023. Raw probabilities are not calibrated.
- Training-OOF-derived thresholds targeting 80/90/95% coverage yielded validation coverage 80.9/91.0/95.7% and selective error 10.7/14.2/16.2%. This is exploratory review-routing evidence; no threshold is enabled in the app.
- Fixed class-order handling for multiclass log loss after the first run emitted scikit-learn warnings and produced an invalid log-loss value; reran successfully without those warnings. Reliability figure was visually reviewed.
- Added `docs/ERROR_ANALYSIS_v1.md`, `docs/INDEPENDENT_DOCUMENT_EVALUATION.md`, and a blank annotation template. Full-document evidence is not complete because there are no independently sourced complete-policy snapshots or human annotations. ToSDR labels cannot be treated as complete-document truth; no synthetic/model-generated reference labels were created.
- Phase 5 remains in progress until reviewers supply and adjudicate independent document annotations. The next needed input is an annotated document set (or the team’s selected document snapshots and reviewer assignments); the final test set remains locked.
- Added `scripts/verify_document_source_candidates.py` and fixed an eight-document candidate source registry (consumer Terms and Privacy Policies for Anthropic, Mistral AI, Perplexity AI, and You.com). It verified all four services are absent from the full conflict-free ToSDR benchmark. Official source links and observed versions are recorded; no document contents were copied into the repository.
- Full-document evaluation still needs frozen local snapshots and two independent reviewers. The source list is deliberately a candidate pack, not an evaluation result. Phase 5 remains open.

## 2026-11-02 â€” Phase 5 progress: freeze sources and prepare human review

- Added `scripts/fetch_document_source_candidates.py`; froze six source snapshots and extracted text under Git-ignored `data/review/snapshots_v1/`. Registry rows include retrieval date, version metadata, content hashes, paths, and fetch status. The two Perplexity requests returned HTTP 403 and remain unfrozen; no access workaround was attempted.
- Added `scripts/prepare_document_review_sheets.py` for tracked metadata stubs and `scripts/prepare_document_review_segments.py` for blind content sheets. The initial annotation subset is the complete consumer Terms of Service for Anthropic, Mistral AI, and You.com: 951 current-segmenter clauses. Each document also has a reviewer-added-span row for material omitted by segmentation. Exact text offsets were checked against extracted snapshots during generation; these are offsets into the text extract, not PDF page positions.
- Updated the independent evaluation protocol with an operational three-class rubric, source/adaptation notes, and extraction limitations; updated the Phase 5 report, README, and project context with commands and current gate status. The privacy documents are frozen for a later review round.
- No human annotations exist yet. Phase 5 is still open pending independent reviewer sheets and adjudication; no Phase 6 work or locked-test evaluation has started.

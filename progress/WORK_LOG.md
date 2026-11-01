# Work log

## 2026-11-02 — Initial data audit implementation

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

- Command: `python scripts/audit_data.py` — completed successfully on 2 November 2026.
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

## 2026-11-02 — Phase 0 baseline complete

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

## 2026-11-02 — Phase 1 data-quality and preprocessing complete

### Data integrity and coverage

- Validated unique IDs for points, cases, topics, services, and documents. Audited point→case, point→service, point→document, and case→topic references: zero orphan references.
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

## 2026-11-02 — Phase 2 evaluation protocol and split manifests

### Scoped input and protocol

- Added a separate English-only benchmark of 19,189 conflict-free rows, selected by `langid` classification of visible text >=40 characters. Counts are Neutral 8,097, Risky 6,285, Safe 4,807. The full 22,497-row reconstruction and 22,445-row multilingual conflict-free benchmark remain available; no source rows were overwritten.
- Recomputed near-duplicate candidates on the English benchmark: 2,039 pairs at character 4-gram Jaccard >=0.72. Reviewed 43 pairs >=0.99 and connected their services/texts for partition isolation.
- Registered macro F1 as primary metric; Risky precision/recall, per-class metrics, confusion matrix, false positive/negative counts, runtime and resource costs as required reporting. Test set is locked; feature transforms must be fit inside training folds.
- Fixed seed: 20261102. One `StratifiedGroupKFold(20, shuffle=True)` assignment per protocol; train/validation/test are folds 0–13 / 14–16 / 17–19. Three-fold grouped CV is assigned only within training rows. No seed search.

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

## 2026-11-02 � Phase 3 development-only EDA

- Added `scripts/run_eda.py`; all summaries and plots use only included primary-protocol train and validation rows (16,097 clauses). The test partition was not read for EDA.
- Recorded class counts and shares (Risky 5,266/32.7%, Neutral 6,773/42.1%, Safe 4,058/25.2%); 27 topics and 1,358 services appear in development. The top 10 services contribute 4.2% of development rows.
- Saved topic/label and service/label counts, length/readability proxies, negation prevalence, and development-only class-associated word unigrams/bigrams. Negation is retained in text terms. Readability is a rough heuristic; phrase associations may reflect case-derived annotation context.
- Excluded retrospective identifiers, topic, service, and label fields from any proposed predictive features. No clustering or model error analysis was done; no model has been trained.
- Outputs: `results/eda/v1/EDA_REPORT.md`, JSON/CSV summaries, and five captioned PNG figures. Reviewed the phrase chart visually; captions state sample sizes and interpretation limits.
- First run revealed an ordering bug in topic composition plotting; corrected and reran successfully. `.venv` run completed with exit code 0. No locked-test data entered analysis.
- Phase 3 is complete. Next: Phase 4 model/feature experiments using frozen split manifests, with development-only selection and final test still locked.

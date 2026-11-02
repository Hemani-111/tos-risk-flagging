# ToS Risk Flagging: Complete Project Plan

Date: 2 November 2026  
Repository: https://github.com/kiran-8287/tos-risk-flagging  
Course: DS3010 Introduction to Machine Learning, IIT Palakkad  
Status: Phases 0–4 complete; Phase 5 development analyses and annotation workflow are prepared, with human-annotated document evaluation pending; Phase 6 backend reliability work is in progress. Later phases remain pending.

## 1. Purpose and intended outcome

Develop an educational screening application that helps people find clauses deserving attention in Terms of Service and Privacy Policies. Users upload PDF, DOCX, or TXT files, or paste text, and review clause predictions in their original context.

The academic contribution is a reproducible investigation of data quality, text representations, classification methods, generalisation, uncertainty, and model errors. The application demonstrates the validated research.

The objective is the strongest defensible performance achievable with available data and compute. Do not promise a particular accuracy, universal coverage, or legal correctness. “Safe” is a learned dataset category, not a guarantee. Start with English-language documents; expand language support only after separate validation.

Success means:

- A traceable dataset and a reproducible preprocessing pipeline.
- Fair comparisons of existing and additional course-relevant methods.
- Evidence about performance on unfamiliar services and complete documents.
- Useful analysis of patterns and failure modes.
- A polished, accessible application with reliable parsing and clear uncertainty.
- Reproducible results, a final report, presentation, and working demonstration.

## 2. Evidence available at the start

The initial audit inspected GitHub commit `e0b9801` (“Add model training script and save model artifacts”). Treat the current local code and data as authoritative if they differ. These findings are observations, not completed fixes.

| Item | Observed state |
|---|---|
| Backend | FastAPI, scikit-learn/joblib, PDF/DOCX/TXT parsing, segmentation, prediction, aggregation |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind; upload, paste text, results, about |
| Training data | 22,497 rows in `data/processed/clauses_clean.csv` |
| Labels | Neutral: 9,759; Risky: 7,015; Safe: 5,723 |
| Sources | 1,781 services and 3,109 distinct non-missing document IDs |
| Missing document IDs | 11 rows |
| Duplicate text | 505 excess rows after lowercasing and whitespace normalisation |
| Conflicting text | 23 normalised texts have more than one label |
| Existing models | Multinomial Naive Bayes, Logistic Regression, Linear SVM, RBF SVM |
| Existing split issue | NB uses a 25% test split; SVM uses a 15% test split; LR saved results are validation results |
| Production split audit | 112 of 3,375 test rows have normalised text present in combined train + validation |
| Service overlap | 3,325 of those 3,375 test rows belong to services represented in training |
| Pipeline | `src/` modules are stubs; several planned notebooks are empty |
| Raw CSVs | User confirms they exist locally in `data/raw`; GitHub excludes them through `.gitignore` |
| Tests | Full suite was not run in the audit environment because pytest was unavailable |
| Changes made during audit | None |

Targeted checks reproduced two segmentation issues: an all-caps substantive sentence was discarded as a heading, and a sentence wrapped over two lines became two separate inputs. Results currently travel in a base64 URL and the results page displays risky clauses only.

The presentation reports approximately 85% RBF SVM accuracy. Preserve this as a historical result with its protocol; do not use the existing table as a fair final comparison or claim it has been reproduced.

## 3. Working instructions for the coding agent

1. Read this plan and any applicable `AGENTS.md` or `PROJECT_CONTEXT.md` before editing.
2. Inspect the actual local repository, Git status, dependencies, and available hardware. Preserve uncommitted work and existing notebooks.
3. Work in a dedicated branch such as `project-completion`. Do not reset, delete, or overwrite unrelated work.
4. Implement in the phase order below. Finish a coherent milestone, verify it, and explain the outcome in plain language.
5. Preserve original data and historical metrics. Write revised datasets and experiment outputs separately with provenance.
6. Keep the deployed model unchanged until a replacement has passed the selection and integration checks.
7. Never fabricate metrics, labels, explanations, or experimental outcomes. Mark illustrative samples as illustrative.
8. Use the existing stack unless a specific requirement justifies a change. Do not rewrite working components unnecessarily.
9. Log commands, tests, files changed, results, blockers, and next steps in `progress/WORK_LOG.md`. Append dated entries.
10. Maintain `PROJECT_CONTEXT.md` with the current milestone and reproducible entry points.
11. Ask for clarification only when it changes scope or a consequential decision cannot be resolved from the files. Do not repeatedly ask permission for routine local implementation within this plan.
12. Treat public deployment, uploading user documents to external services, and adding paid services as explicit decisions. Local development and local experiments can proceed.
13. Use downloaded model artifacts only from trusted sources; never load arbitrary uploaded joblib/pickle files.

## 4. Scope and priorities

### Essential completion scope

- Dataset audit, conflict review, reproducible cleaning, and consistent evaluation.
- Existing models rerun fairly plus Decision Tree, Random Forest, boosting, and KNN experiments.
- Feature comparisons and pattern/error analysis.
- A selected production model with versioned metadata.
- Robust upload/paste analysis and a redesigned clause review experience.
- Tests, setup documentation, final report, slides, and demo.

### Conditional extensions

- Sentence embeddings with a classical classifier, subject to compute and course expectations.
- Calibrated uncertainty and a validated abstention rule.
- K-means or other exploratory clustering when it answers a specific question.
- Voting or stacking only if base models show complementary errors.
- Public hosting after deployment checks.

### Later work, not required for completion

- Fine-tuning large transformers, multilingual support, browser extensions, URL crawling, OCR, user accounts, persistent cloud history, and LLM-generated explanations.
- These require separate validation and should not delay the core project.
- Do not force HMMs, CCA, or regression into this task solely to cover the syllabus.

## 5. Phase 0: Establish a reproducible baseline

- [ ] Inspect local `data/raw`, file sizes, schemas, and notebook outputs.
- [ ] Confirm which raw snapshot produced the current processed CSV. Record source URL, retrieval date if known, license, and SHA-256 checksums.
- [ ] Inspect local modifications, including the Naive Bayes notebook and presentation, before editing.
- [ ] Create an isolated Python environment and record Python/package versions. Resolve dependencies required for training as well as serving.
- [ ] Install frontend dependencies using its lockfile when present; retain or generate a suitable lockfile.
- [ ] Run existing backend tests, frontend checks/build, and a representative end-to-end request. Record genuine failures separately from environment problems.
- [ ] Inspect artifact compatibility and model paths in local and Docker execution.
- [ ] Record current model outputs and timings on a fixed small regression set without calling them an accuracy benchmark.

**Completion gate:** a new contributor can reproduce baseline startup, and known failures have a recorded cause and next action.

## 6. Phase 1: Data quality and preprocessing

### 6.1 Audit original data

- [ ] Validate uniqueness of primary keys in cases, topics, services, and documents.
- [ ] Join approved points to cases and topics with explicit cardinality validation.
- [ ] Report rows before and after every filtering or joining operation.
- [ ] Check blank quotes, markup, encoding issues, missing IDs, unexpected classifications, language distribution, and unusually short or long quotes.
- [ ] Verify mapping: `good -> Safe`, `neutral -> Neutral`, `bad/blocker -> Risky`.
- [ ] Preserve original classification, case IDs, source IDs, and original quote text for traceability.
- [ ] Determine whether one quote can legitimately have multiple case annotations. Explain the limitation of mapping several issues to a single three-class target.

### 6.2 Duplicate and conflict policy

- [ ] Create a normalised text key for auditing while retaining the original text.
- [ ] Separate repeated annotations, duplicate source text, and near-duplicate boilerplate.
- [ ] Review all identified conflicting texts with their annotations and context.
- [ ] Do not silently assign majority labels or delete difficult examples to improve scores. Record the resolution policy and each manual decision.
- [ ] Unresolved conflicts may be quarantined from the single-label benchmark; report their count and retain them in an audit export.
- [ ] Prevent exact duplicates from crossing evaluation partitions. Group or exclude cross-partition duplicates with an explicit logged rule.
- [ ] Audit near duplicates using an affordable similarity method, review candidate matches, and document residual overlap.

### 6.3 Outputs

- A data audit JSON/Markdown report, class counts, and filtering summary.
- A clean, versioned dataset plus duplicate/conflict review exports.
- A script that recreates the dataset from local raw CSVs.
- A data dictionary and dataset limitations section.

**Completion gate:** counts reconcile from raw files to training rows, label mapping is verified, and duplicate/conflict policies are explicit and reproducible.

## 7. Phase 2: Freeze the evaluation protocol

Use two clearly named evaluation settings:

1. **Primary: unseen-service evaluation.** Keep each service in one partition. Audit document overlap and duplicate text across services as well. Resolve cross-service duplicate links through connected grouping or a documented exclusion policy; report large groups and resulting class balance.
2. **Secondary: clause-level evaluation.** Use duplicate-aware clause grouping for comparison with earlier work, explicitly noting that services may overlap.

Actions:

- [ ] Save row/group split manifests with a fixed seed and dataset checksum.
- [ ] Aim for roughly 70/15/15 train/validation/test, allowing group constraints to change exact sizes. Report achieved distributions.
- [ ] Keep labels represented where feasible; do not repeatedly search seeds to obtain attractive scores.
- [ ] Fit TF-IDF, feature selection, scaling, and dimensionality reduction only within training folds.
- [ ] Use grouped cross-validation within development data for the primary protocol. Start with three folds for expensive experiments; increase to five for finalists if feasible.
- [ ] Use common splits and comparable search budgets across model families.
- [ ] Register selection criteria before comparing results: macro F1 as primary, risky recall and precision as key operating trade-offs, plus latency and resource cost.
- [ ] Choose operational thresholds on development data. Do not adjust them after seeing test results.
- [ ] Evaluate the frozen selected system on the locked test set. If publishing frozen finalist comparisons, declare that set in advance and do not use test outcomes for another tuning cycle.

Required metrics: accuracy, macro/weighted F1, per-class precision/recall/F1/support, confusion matrix, risky false-negative/false-positive counts, training time, inference latency, artifact size, and peak memory where measurable.

Use one-vs-rest ROC-AUC and PR curves where meaningful scores exist. Decision scores can support ranking metrics; they are not probabilities. Report uncertainty using group-level resampling for service-grouped data. Any paired significance analysis must respect dependence between clauses from the same service and account for multiple comparisons.

**Completion gate:** all experiment code consumes the same versioned split definitions, with assertions for group and exact-text overlap.

## 8. Phase 3: EDA and pattern discovery

Answer research questions with plots, tables, and a short interpretation:

| Question | Analysis | Interpretation limit |
|---|---|---|
| Is the dataset balanced? | Counts by class, service, topic, document | Describe sample composition |
| Which topics contain risky annotations? | Topic/class distributions with sample counts | Do not equate annotation frequency with population risk |
| Does complexity matter? | Length/readability distributions and error rates | Association does not establish causation |
| What phrases distinguish classes? | Class-associated n-grams and linear coefficients | Inspect context, negation, and coefficient stability |
| Are some services overrepresented? | Service concentration and coverage | Do not rank real-world safety from selected annotations |
| What is hard to classify? | Errors by topic, length, language, ambiguity | Separate annotation issues from model errors |
| Do semantic groups emerge? | Optional embedding/SVD visualisation and clustering | Plot separation is not proof of predictive performance |

- [ ] Preserve negation and meaningful legal wording during preprocessing.
- [ ] Distinguish dataset topics available for retrospective analysis from features actually available at inference.
- [ ] Exclude classification, case-derived labels/titles, severity scores, annotation analysis, and service ratings from predictive features that would leak the target.
- [ ] Use development data for exploratory decisions; avoid inspecting locked test errors before freezing the model.
- [ ] Export readable plots and summary tables, with captions stating sample sizes and methods.

**Completion gate:** each retained analysis answers a stated question and includes its practical implication or limitation.

## 9. Phase 4: Model and feature experiments

### 9.1 Model families

| Family | Role | Initial parameters to investigate |
|---|---|---|
| Dummy classifier | Reference floor | Majority/prior strategies |
| Multinomial/Complement NB | Fast text baselines | Smoothing, representation |
| Logistic Regression | Interpretable linear model | Regularisation C, class weighting |
| Linear SVM | Strong sparse-text candidate | C, class weighting |
| RBF SVM | Existing nonlinear candidate | C, gamma; runtime budget |
| Decision Tree | Study rules and overfitting | Depth, minimum leaf size, pruning |
| Random Forest | Bagging comparison | Trees, depth, feature sampling, leaf size |
| Gradient boosting | Sequential ensemble comparison | Learning rate, trees, depth, sampling |
| KNN | Similarity-based comparison | k, distance, distance weighting |
| Voting ensemble | Conditional extension | Combine only promising complementary models |

Use suitable input formats: benchmark sparse TF-IDF where supported; use training-fitted reduced features or dense embeddings for algorithms that require or benefit from them. Do not densify a large vocabulary matrix without a memory estimate. Avoid blindly applying SMOTE to sparse text; investigate class weighting first.

Treat solver and iteration settings as optimisation/convergence controls. Do not waste the main search budget treating larger `max_iter` as increased model capacity after convergence.

### 9.2 Representation experiments

- [ ] Word TF-IDF unigrams versus unigrams + bigrams.
- [ ] Character n-grams with a controlled vocabulary budget.
- [ ] Text length, readability, negation and selected phrase features, alone and added to text features.
- [ ] Truncated SVD for sparse TF-IDF where reduction is useful. Do not call uncentred truncated SVD “PCA”.
- [ ] Optional frozen sentence embeddings + Logistic Regression/SVM; record encoder revision, license, language, maximum length, and truncation strategy.
- [ ] Optional PCA on appropriate dense features, with fitting restricted to training data.
- [ ] Optional clustering on reduced features to inspect patterns and annotation inconsistencies, not to replace supervised evaluation.

### 9.3 Experiment execution

1. Run a small smoke experiment to verify inputs, artifacts, and metrics.
2. Benchmark each essential family under a modest, declared budget.
3. Tune promising candidates using development-only cross-validation.
4. Run controlled feature ablations, changing one factor at a time where practical.
5. Inspect learning curves to assess whether more data or different regularisation is likely to help.
6. Investigate errors and refine only using development data.
7. Freeze finalist configurations and final selection procedure.

Every experiment must save: run ID, Git revision, data hash, split ID, seed, package versions, parameters, feature settings, timing, convergence warnings, metrics, and development predictions for error analysis.

**Completion gate:** all essential families have reproducible results or a specific documented feasibility blocker. The final model is selected from evidence, not assumed to be SVM or an ensemble.

## 10. Phase 5: Error analysis, uncertainty, and full-document validation

### 10.1 Structured error review

- [ ] Review representative risky false negatives, false alarms, and Safe/Neutral confusions.
- [ ] Categorise causes: negation, exceptions, missing context, ambiguous labels, rare terms, boilerplate, segmentation, or unfamiliar language/domain.
- [ ] Check clauses mentioning examples such as data sharing, deletion, unilateral changes, liability, termination, and user rights, without treating keyword presence as ground truth.
- [ ] Compare models on the same examples to identify genuine complementarity.
- [ ] Preserve difficult cases; do not optimise only for hand-picked examples.

### 10.2 Uncertainty, when supported

- [ ] Evaluate probability calibration using held-out development predictions, reliability plots, log loss and an appropriate multiclass Brier calculation.
- [ ] Calibrate a selected model if needed using a disjoint calibration set or group-respecting folds. Never calibrate on the final test set.
- [ ] Tune an abstention threshold on development data and report the trade-off between coverage and error rate.
- [ ] Represent `Needs review` as a review status while preserving the original three-class prediction, rather than inventing a fourth training label.
- [ ] Test irrelevant text, empty vocabulary inputs, gibberish, unsupported languages, and very short fragments. Low confidence alone is not a validated out-of-domain detector.
- [ ] If calibration/abstention is not validated, omit numerical confidence claims and document that limitation.

### 10.3 Independent document evaluation

- [ ] Assemble a small review set from services not used for training, with permission/source records and a fixed selection rule.
- [ ] Write a clear annotation rubric aligned with the training label meaning.
- [ ] Have two team members independently annotate where practical, reconcile disagreements, and report agreement. This is a student-reviewed reference set, not expert legal ground truth.
- [ ] Evaluate parser extraction, segmentation coverage, clause predictions, and end-to-end missed risky content separately.
- [ ] Keep document development cases separate from a final frozen document evaluation set.
- [ ] Report performance on annotated ToSDR quotes separately from complete-document performance.

**Completion gate:** the report explains where the system fails and how those limitations affect the application.

## 11. Phase 6: Backend reliability and model packaging

- [x] Repair segmentation with tests for all-caps substantive clauses, numbered headings, bullets, abbreviations, quotations, wrapped lines, short fragments, and punctuation.
- [ ] Preserve extraction text, clause offsets, and section/page metadata where reliable. Clause offsets and text are preserved; PDF page mapping remains to be added.
- [x] Distinguish headings from content; do not discard substantive language solely because it is uppercase.
- [x] Report scanned/image-only PDFs as unsupported without OCR; never present an empty extraction as a safe document.
- [ ] Handle corrupt, encrypted, empty, oversized, and unsupported documents with useful errors. Corrupt, empty, oversized, unsupported and scanned cases are covered; encrypted-file regression coverage remains.
- [ ] Enforce upload limits during reading, plus limits for pasted text, extracted length, pages/clauses, and processing time. Byte, character, page, and clause limits are implemented; a hard processing timeout remains.
- [x] Move expensive inference off the async event loop and bound concurrency; add a job queue only if measured workload needs it.
- [x] Use temporary files safely and clean them on success and failure. Do not log document contents by default.
- [x] Load a versioned model package once, validate class order and metadata, and expose readiness failures clearly.
- [x] Package preprocessing and classifier together where practical to prevent mismatched artifacts. Existing paired artifacts are versioned and checksum validated; they remain two files pending a replacement pipeline package.
- [x] Add model version, schema version, warnings, and supported uncertainty fields to API responses. No numerical uncertainty field is exposed because it is not calibrated.
- [x] Keep document summaries as counts/shares of analysed clauses. Do not label them legal compliance or a calibrated document risk probability.
- [x] Verify Docker model mounts and `MODEL_DIR` explicitly; the inspected loader's relative root calculation needs checking against the container layout.

**Completion gate:** backend tests cover observed regressions and representative error paths; local and container startup load the intended model.

## 12. Phase 7: Public application design

### 12.1 Main user journey

1. Understand the purpose and supported inputs.
2. Upload a file or paste text.
3. See honest processing status and actionable errors.
4. Read a concise findings summary.
5. Inspect flagged clauses within the extracted document.
6. Filter, search, navigate, and export results.

### 12.2 Screens

| Screen | Required content |
|---|---|
| Home | Clear purpose, supported formats/language, short example, primary upload action |
| Analyze | Accessible upload zone, paste editor, limits, privacy explanation, progress/error states |
| Results | Document viewer, clickable highlights, summary counts, label filters, text search, clause detail |
| Methodology | Dataset provenance, selected model, evaluation protocol, actual metrics and limitations |
| Research results | Versioned experiment comparisons and pattern analysis; separate from individual document results |

Desktop results should use a document pane and a clause review pane. On mobile, use a readable single-column layout or switchable views. Display all classes, not just Risky. Provide an explicit zero-detection message without implying guaranteed safety.

Design requirements:

- [ ] Consistent typography, spacing, restrained colour palette, and responsive layouts.
- [ ] Colour plus text/icons for labels; keyboard navigation, visible focus, sufficient contrast, and screen-reader labels.
- [ ] Search and filters with counts; selecting a clause scrolls to its matching context.
- [ ] Separate uncertainty status from risk category if abstention is supported.
- [ ] Explain model evidence honestly. Linear feature contributions may explain a linear model; do not present a surrogate model's coefficients as an RBF explanation.
- [ ] Topic grouping only if a topic predictor or clearly labelled heuristic is implemented and evaluated. Ground-truth dataset topics are unavailable for arbitrary uploads.
- [ ] Avoid invented plain-language legal interpretations. Generative explanations remain a separate future feature unless grounded and evaluated.
- [ ] Replace base64 results in query strings. For a simple MVP, use session-scoped browser storage with size/error handling and a clear-data control; if server storage is chosen, specify retention and isolation explicitly.
- [ ] Explain refresh/session-expiry behaviour. Do not promise persistent history unless implemented.
- [ ] Export JSON/CSV first; add a readable printable/PDF report if time permits. Include model version, counts, clauses, warnings, and method limitations.

**Completion gate:** representative users can upload, locate a flagged clause, understand its context, and export findings without guidance.

## 13. Phase 8: Verification and deployment readiness

### Required automated checks

- Data: schema, mapping, cardinality, counts, deterministic preprocessing, split overlap.
- ML: pipeline serialization, prediction shape/class order, version compatibility, deterministic split manifests, no preprocessing fit on held-out data.
- Segmentation: all-caps clauses, wrapped text, headings/lists, offsets, empty input, abbreviations.
- API: valid file/text requests, unsupported/corrupt inputs, size limits, cleanup, missing model, summary consistency.
- Frontend: upload and paste flows, filters/search, missing/expired results, export, long documents, keyboard operation.
- Integration: at least one end-to-end fixture for each supported format and representative error states.

Do not confuse passing functional tests with measured model accuracy. Use meaningful regression tests; do not require a model to agree with unreviewed hand-written labels.

### Manual and operational checks

- [ ] Run the documented setup on a clean environment.
- [ ] Measure startup, extraction, feature transformation and inference separately on representative document sizes.
- [ ] Set and document a performance budget from measured hardware and expected usage.
- [ ] Check current dependency advisories and upgrade supported versions before public deployment; rerun relevant checks.
- [ ] Configure environment-specific CORS, HTTPS at hosting, rate limits, readiness checks, and content-free operational logs.
- [ ] Verify frontend API URL behaviour for the chosen build/deployment setup.
- [ ] Confirm document retention/deletion behaviour matches the UI claims.
- [ ] Test concurrency and resource limits; maintain a rollback path to the previous model/application version.
- [ ] Keep secrets and raw uploaded documents out of Git. Confirm dataset licensing before redistributing data or trained artifacts.

**Completion gate:** local demonstration is reproducible. Public launch is a separate explicit release step after these checks, not assumed to be completed by local success.

## 14. Phase 9: Academic deliverables

### Final report

- Problem definition, intended users, and scope.
- Dataset provenance, annotation meaning, cleaning decisions, and limitations.
- EDA research questions, plots, and interpretations.
- Mathematical explanation of selected course methods and feature representations.
- Evaluation protocols, split diagrams, tuning budgets, and leakage controls.
- Fair comparison tables with uncertainty and computational costs.
- Feature ablations, learning curves, and error analysis.
- Independent complete-document evaluation.
- Application architecture, screenshots, and usage flow.
- Ethical/product limitations, conclusion, and concrete future work.
- Reproduction commands, data/model versions, and sources.

### Presentation and demonstration

- [ ] Confirm required slide count and marking rubric before creating final slides.
- [ ] Explain the problem, dataset, approach, strongest experimental evidence, application, and limitations.
- [ ] Replace historical mixed-protocol comparisons with correctly labelled results.
- [ ] Prepare a normal example, a difficult example, an uncertain case if supported, and a file-error example.
- [ ] Keep a local demonstration available even if public hosting is unavailable.
- [ ] Ensure each team member can explain preprocessing, the split policy, TF-IDF, chosen models, metrics, and major errors.

**Completion gate:** every displayed metric is traceable to a saved run and every claimed feature works in the delivered version.

## 15. Suggested repository organisation

Adapt this structure to the existing repository; avoid moving working files solely for aesthetics.

```text
PROJECT_COMPLETION_PLAN.md
PROJECT_CONTEXT.md
progress/WORK_LOG.md
configs/                     # dataset, split, feature and experiment settings
src/
  data_loader.py
  preprocessing.py
  features.py
  train.py
  evaluate.py
  splitting.py
  analysis.py
scripts/
  audit_data.py
  prepare_data.py
  create_splits.py
  run_experiments.py
  evaluate_documents.py
  export_model.py
tests/                       # data/ML regression tests
data/
  raw/                       # original local files, unchanged
  processed/                 # versioned outputs
  splits/                    # manifests, not accidental text copies
  review/                    # conflicts and reviewed evaluation annotations
results/
  audits/
  experiments/<run_id>/
  figures/
models/
  selected_model/             # current serving artifacts and metadata
  releases/<version>/
notebooks/                   # documented exploration, backed by reusable code
backend/                     # existing service and its tests
frontend/                    # existing application
docs/
  DATASET_CARD.md
  MODEL_CARD.md
  EXPERIMENT_PROTOCOL.md
  REPRODUCING.md
  DEPLOYMENT.md
```

Proposed commands should be implemented and documented before being advertised as working. Prefer a single configuration-driven experiment command over independent notebooks with divergent splits.

## 16. Milestones and effort planning

The deadline and available compute are not yet known. These are planning estimates for a student team, not delivery promises; training runtime and annotation effort are additional variables.

| Milestone | Approximate active effort | Dependency |
|---|---|---|
| M0: baseline and environment | 0.5–1 day | Local repository/data |
| M1: audit, cleaning, split protocol | 2–3 days | M0 |
| M2: EDA and expanded experiments | 3–5 days | M1 |
| M3: error review and model freeze | 2–3 days | M2 |
| M4: backend and application improvements | 3–5 days | Stable API; final integration after M3 |
| M5: verification, report, slides, demo | 2–3 days | M3 and M4 |

Team members can divide work across data/evaluation, experiments, backend, and frontend/documentation. All model work must share the same dataset and split manifests. This division does not authorise automatic sub-agent delegation.

If time is short, reduce tuning budgets, optional embeddings/ensembles, and optional visualisations first. Preserve leakage controls, fair comparisons, core parser fixes, and honest reporting.

## 17. Risks and responses

| Risk | Response |
|---|---|
| More algorithms do not improve results | Report the comparison honestly and focus on features/data/errors |
| Grouped performance drops | Treat it as evidence of the harder deployment setting, not a failed project |
| Annotation conflicts remain | Retain review records and quantify uncertainty in target construction |
| ToSDR quotes differ from arbitrary extracted sentences | Validate whole documents and improve segmentation/context |
| RBF/ensemble runtime is too high | Prefer a validated faster candidate when trade-offs warrant it |
| Features reveal annotation labels | Audit feature provenance and inference availability |
| Training consumes too much memory | Bound vocabulary, use sparse operations, estimate dense allocations |
| UI overstates reliability | Show actual coverage, warnings, and clearly defined metrics |
| Reported scores drift between runs | Version data, splits, configuration, environment and model artifacts |

## 18. Definition of complete

- [ ] Raw-to-clean preprocessing is reproducible with an audit trail.
- [ ] Duplicate/conflict decisions and evaluation splits are documented and checked.
- [ ] Existing and additional essential model families were compared fairly.
- [ ] Feature experiments and useful pattern/error analyses are complete.
- [ ] Final model selection and uncertainty behaviour are supported by saved evidence.
- [ ] Unseen-service and complete-document evaluation are reported separately.
- [ ] Upload, paste, parsing, segmentation, prediction, context review and export work.
- [ ] Observed segmentation regressions and URL-result handling are fixed.
- [ ] Tests/builds and a clean-environment demonstration pass, or material limitations are disclosed.
- [ ] Dataset/model cards, reproducibility instructions, report and presentation are complete.
- [ ] Production artifacts are versioned, and no previous work was silently overwritten.
- [ ] No claim of universal accuracy, legal safety, or expert-reviewed labels exceeds the evidence.

## 19. First task for Codex in VS Code

Read this plan and inspect the local project, including `data/raw`. Begin with Phase 0 and Phase 1: establish the baseline, verify raw CSV provenance and joins, reproduce counts, and produce a dataset audit. Preserve current notebooks, application code and production artifacts while establishing the revised pipeline. Verify the earlier audit findings against current local files. Then implement the shared split/evaluation foundation before training additional methods. Record findings and progress in `PROJECT_CONTEXT.md` and `progress/WORK_LOG.md`, explaining the ML decisions so the student team can defend them in the course assessment.

## 20. Reference material

Project-specific evidence: repository audit at `e0b9801`, supplied problem statement, and six-slide progress presentation. The local raw dataset was not inspected during the initial remote audit.

- Dataset reference in the proposal: https://zenodo.org/records/15012282 — verify against the local files before asserting snapshot identity.
- Text classification benchmark: https://scikit-learn.org/stable/auto_examples/text/plot_document_classification_20newsgroups.html
- Leakage and pipeline guidance: https://scikit-learn.org/stable/common_pitfalls.html
- Calibration guidance: https://scikit-learn.org/stable/modules/calibration.html

Check the documentation corresponding to the actual installed versions when implementing. The phases above are a proposed execution plan, not a claim that those experiments or features already exist.

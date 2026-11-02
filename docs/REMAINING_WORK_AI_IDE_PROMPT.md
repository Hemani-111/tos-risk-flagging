# ToS Risk Flagging: Remaining Work and AI IDE Execution Prompt

Prepared: 3 November 2026  
Repository: https://github.com/kiran-8287/tos-risk-flagging  
Use: Keep this file under `docs/` and ask the IDE agent to execute it from the repository root.

## 1. Mission

Complete this existing ML course project from its current state. Finish the remaining experiments, choose and integrate a validated model, deliver a polished document-review application, and complete the reproducibility and academic materials.

This is an implementation instruction, not a request to produce another plan. Inspect the repository, identify missing evidence, and implement the work below. Continue through all tasks that the available environment supports. Explain consequential ML decisions so the student team learns from the work and can defend it in assessment.

This continuation document supplements `PROJECT_COMPLETION_PLAN.md`. For future work, its expanded experiment scope and continuation order replace the original instruction to start again at Phase 0. Preserve the original plan as historical context and reconcile its status with actual evidence.

## 2. Source and current-state boundary

This prompt was prepared from the uploaded updated `PROJECT_COMPLETION_PLAN(1).md` and the user's detailed progress report. The current local repository has not been independently re-audited while preparing this file. Verify every status below against local code, saved runs, and logs before relying on it.

Revision note: checked against the six-slide uploaded `Terms & Conditions Risk Flagging Using ML(1).pptx`. Section 17 explicitly defines the mid-semester baseline, end-semester additions, and presentation evidence. This revision does not claim that any additional experiment has been executed.

Reported completed work:

- Phases 0–4 have baseline, data audit/preparation, split protocols, EDA, model comparisons, tuning, and lexical ablations.
- Historical data reconstruction has 22,497 rows; the conflict-free English benchmark has 19,189 rows.
- Both primary unseen-service and secondary duplicate-aware clause protocols have fixed checksummed manifests.
- Dummy, Naive Bayes, Logistic Regression, Linear/RBF SVM, Decision Tree, Random Forest, boosting, and KNN were compared.
- Tuned word unigram/bigram TF-IDF Linear SVM is the strongest reported development candidate.
- Primary grouped-CV macro F1 is reported as 0.832 ± 0.003 and validation macro F1 as 0.820; secondary results are 0.839 ± 0.002 and 0.819. Determine what the ± values mean from the actual experiment outputs. Do not label them confidence intervals without evidence.
- The serving model remains the earlier RBF SVC.
- Validation error analysis and exploratory, uncalibrated LR probability analyses exist.
- Six document snapshots and blind review sheets covering 719 clauses are prepared; independent annotations are pending.
- Backend handling, segmentation, limits, readiness, and artifact checks have been improved.
- UI supports all-class review, filters/search, adjacent clause context, page ranges, exports, research and methodology pages, and session-scoped results.
- The application does not yet display the full extracted document with matching highlights.
- Reported local checks include 45 backend tests, Ruff, frontend lint/build, clean-environment checks, and dependency/Compose checks. These are historical reports, not a substitute for checking the revised code.
- Docker startup/model loading, manual UX review, final document evaluation, locked tests, final report/slides, and any public release remain open.

Do not retrain completed models simply because old checkboxes are unchecked. Rerun when their saved evidence is missing, their protocol is invalid, or a material change requires it.

## 3. Operating rules

1. Read applicable `AGENTS.md`, `PROJECT_CONTEXT.md`, the original plan, experiment protocol, work log, model/data cards, and relevant reports before significant edits.
2. Check Git status and preserve uncommitted work. Work on a suitable branch without discarding another person's changes.
3. Preserve source CSVs, reviewed labels, original notebooks, historical reports, split manifests, and deployed artifacts. Version replacements.
4. Keep completed functionality and the current stack. Refactor only to support a demonstrated need.
5. Prefer existing reusable pipelines over new disconnected notebook implementations.
6. Never invent human reviews, scores, plots, timings, citations, completed tests, or model explanations. Never fill blank reviewer labels using model predictions and call them independent annotations.
7. Keep the locked test sealed until every planned development experiment, preprocessing choice, candidate, calibration rule, and selection procedure is frozen.
8. If a test has already been opened, record when and how it was used. Do not pretend it is still untouched or reshuffle data to manufacture a fresh test score.
9. Use development data for feature engineering, tuning, clustering decisions, learning curves, and error-driven improvements.
10. Do not treat lower validation performance as a reason to delete hard examples or loosen leakage controls.
11. Use reasonable finite search budgets and incremental checkpoints. Do not start unbounded grids or silently substitute tiny smoke tests for full experiments.
12. Continue independent tasks when one gate is blocked. Report concrete blockers and exact next actions; do not mark them completed.
13. Append dated work-log entries and maintain context/status files after each coherent milestone. Clearly distinguish implemented, executed, validated, and blocked.
14. Local implementation and experiments are authorised. Ask before paid resources, external transmission of uploaded documents, or public publication. Do not push or publish solely because local work is complete.

## 4. First action: reconcile status and evidence

- Locate the actual experiment runner, feature builders, model registry, manifests, artifact exporter, and evaluation scripts.
- Inventory completed runs with run IDs, configurations, protocol, data hash, metrics, and artifact paths.
- Create `docs/REMAINING_WORK_STATUS.md` with one row per task: verified state, evidence, next action, blocker, and completion gate.
- Correct stale checkboxes using evidence, preserving unresolved caveats such as Docker and human evaluation.
- Inspect available CPU/RAM/GPU, Python environment, package versions, and existing caches.
- Verify dataset/split integrity and check that none of the new experiments below opens locked test text or labels.
- Run a targeted baseline check sufficient to establish the current code state. Broaden checks after changes as appropriate.

## 5. Complete every discussed model family

The user now requests the previously conditional model extensions too. Implement and run them where feasible, preserving failed or negative results. No model is required to win. Do not mark a model complete because its import or configuration exists.

| Experiment | Required action |
|---|---|
| Dummy classifier | Verify reference results under each protocol |
| Multinomial Naive Bayes | Verify existing full comparison; tune smoothing if absent |
| Complement Naive Bayes | Add a separate comparison if not already run |
| Logistic Regression | Verify tuning and convergence evidence |
| Linear SVM | Verify leading candidate and its saved pipeline/configuration |
| RBF SVM | Verify fair comparison and computational cost |
| Decision Tree | Verify depth/pruning/leaf-size experiments and overfitting analysis |
| Random Forest | Verify bagging comparison with bounded tuning |
| Gradient boosting | Identify the concrete implementation already used; complete its justified tuning rather than treating all boosting libraries as mandatory |
| KNN | Verify neighbours/distance experiments on a feasible representation |
| Voting ensemble | Run hard voting; run soft voting only with appropriately calibrated or evaluated probabilities |
| Stacking ensemble | Run a bounded comparison with strictly out-of-fold base predictions and a simple meta-classifier |
| Sentence embeddings + Logistic Regression | Add a frozen-encoder comparison |
| Sentence embeddings + Linear SVM | Add a frozen-encoder comparison on the same folds |

Choose a small set of base models for ensembles from development evidence and error complementarity. An ensemble need not contain all models. Fit stack meta-features using group-respecting out-of-fold predictions. Do not rely on default folds that leak service groups. Fit all learned text transforms within each fold.

For embeddings:

- Choose a suitable compact encoder using current primary documentation. Record model name, exact revision, license, language scope, dimension, maximum input length, and inference cost.
- Use public training text for experiments; do not send user uploads to a remote embedding API without approval. Prefer local inference.
- Define and evaluate handling of long clauses: report truncation or use a documented chunk/pooling strategy.
- Cache deterministic frozen embeddings using dataset/text checksums and encoder revision. Fit any learned normalisation/reduction only inside training folds.
- If downloads, memory, compute, or licensing prevent execution, implement a reproducible command/configuration and record the specific blocker. Do not call an unexecuted experiment complete.

Use primary grouped-CV comparisons first. Evaluate frozen promising configurations under the secondary protocol too; if the budget permits, keep the family comparison across both protocols. Clearly distinguish full-run, sampled, failed, and pending results.

## 6. Finish representation experiments and learning analyses

Audit existing experiments and fill gaps:

- Word unigram versus unigram/bigram TF-IDF.
- Character TF-IDF and a word/character combination.
- Clause length, readability, negation, and selected phrase features, with feature ablations.
- Truncated SVD on sparse TF-IDF for appropriate models and visualisation.
- PCA on dense embeddings as an explicit experiment, compared with unreduced embeddings. Use training-fitted transformations; do not call uncentred SVD PCA.
- Group-aware learning curves for the leading lexical model and the strongest practical semantic model: use increasing training-group subsets with fixed held-out development evaluation; save sample/group counts, F1, risky recall, fit time, and variability.
- If feasible, assess feature importance stability across folds for interpretable linear models.

K-means is required as a pattern-discovery experiment in this expanded scope:

1. Fit on training/development representations and document scaling/normalisation and reduction.
2. Investigate a modest k range using internal criteria, cluster sizes, and stability.
3. Inspect representative clauses and descriptive terms; compare cluster composition with risk labels and topics after fitting.
4. Report that clusters represent similarity patterns and may mix risk categories.
5. Do not choose k from locked-test labels or use plot separation as classification evidence.

Use clear plots with axes, sample counts, and captions. Do not add HMMs, CCA, unrelated regression tasks, large-model fine-tuning, or extra algorithms just to inflate the list.

## 7. Consolidate development results and select the candidate

- Produce a machine-readable experiment table and a readable comparison report generated from saved results.
- Report protocol, representation, model, CV mean/spread, validation metrics, risky precision/recall, training/inference cost, size, and run ID.
- Preserve comparability: show resource-constrained or sampled experiments separately when they use different evaluation budgets/data.
- Analyse risky false negatives, false alarms, negation, exceptions, context dependence, rare topics, and model disagreement.
- Respect the existing registered selection rule. Document any necessary changes before final evaluation.
- Choose a deployment candidate using development evidence and practical costs. The Linear SVM is a candidate, not a preselected mandatory winner.
- Separate research-only experiments from the production pipeline and record why the chosen model is suitable.

Deliver `docs/FINAL_CANDIDATE_FREEZE.md` recording data/split checksums, code revision, feature/model parameters, class order, refit recipe, seed, calibration/review policy, evaluated final candidate set, success criteria, and exact final evaluation commands.

## 8. Calibration and review status

Complete the uncertainty investigation for the selected practical candidate and compare it with existing uncalibrated LR analyses:

- Use a disjoint development calibration set or group-respecting calibration folds.
- Compare uncalibrated scores and reasonable calibration methods using log loss, correctly defined multiclass Brier score, and reliability plots.
- Measure changes in ranking/classification performance as well as reliability.
- Choose any review threshold using development data; report coverage versus error, per-class coverage, and risky misses among accepted predictions.
- Preserve the three-class prediction. Represent `Needs review` as an additional review status, with a reason.
- Test unsupported language, irrelevant text, empty-vocabulary text, and short/gibberish inputs separately. Calibration does not prove out-of-domain detection.
- Expose numerical confidence or automated abstention only when evidence supports the particular policy. If it does not help or remains unreliable, retain warnings and explicitly report the completed negative finding.

## 9. Independent document evaluation

Inspect the six frozen snapshots and 719-clause review workflow. Verify provenance, stable clause IDs, evaluation boundaries, and independence from training services.

- Keep reviewer sheets blind to model labels and to each other's answers.
- Provide annotation guidance, import validation, missing/invalid-label checks, agreement calculation, disagreement exports, and an adjudication template.
- Ask the user for the two completed reviewer sheets when needed. Continue other work while they are pending.
- Review sheets cannot measure omitted content by themselves: check extraction/segmentation coverage against source snapshots as well.
- After genuine independent labels and adjudication are available, compute agreement, confusion matrices, per-class precision/recall/F1, macro F1, and document-level breakdowns.
- Report the reference set as student-reviewed, not expert legal ground truth. Qualify small sample size and service coverage.
- Keep final document labels out of tuning. If a snapshot is used for development debugging, label it development and maintain the integrity of the remaining final evaluation.
- Do not repeatedly retry known 403 pages. Use existing valid snapshots or document an authorised replacement and its effect on evaluation identity.

This gate remains pending until authentic reviews are returned; the agent can complete its tooling but cannot simulate the reviewers.

## 10. Locked-test evaluation

After the freeze, execute the declared locked-test procedure for the primary and secondary protocols. A missing human review does not prevent frozen clause-test evaluation; the two gates can close independently if no further tuning is planned.

- Assert training/calibration/test group and duplicate isolation.
- Refit exactly as recorded; never accidentally include test rows.
- Save predictions, labels, metrics, class supports, confusion matrices, resource measurements, data/model hashes, and evaluation timestamp.
- Report group-level uncertainty with the correct grouping for each protocol; do not assume independent clauses.
- Run score-based one-vs-rest ROC/PR analyses only where suitable scores exist; distinguish margins from probabilities.
- If final comparisons are published, evaluate only the declared frozen candidate set, then do not tune again from those results.
- Accept an honest lower test score. Do not keep selecting new models against the same test set.

Clearly distinguish historical results, CV results, validation results, locked-test results, and independently reviewed document results in every report and UI.

## 11. Package and integrate the selected model

- Build a versioned inference package containing preprocessing, classifier, any required encoder/reduction/calibration, label order, dependency/model revisions, metadata, and checksums.
- Keep the previous RBF package available for rollback. Never silently overwrite historical artifacts.
- Validate offline and API prediction parity on fixed fixtures and representative batch inputs.
- Check startup/readiness failures, schema compatibility, supported input length, batch performance, and empty/irrelevant inputs.
- Ensure the served version and methodology/research pages agree with the actual loaded artifact.
- Promote the frozen candidate according to the recorded procedure. Keep document evaluation limitations visible if that gate is still pending.
- Include review-status fields only if the policy passed its validation gate. Never display SVM decision margins as confidence percentages.

## 12. Complete full-document review and polish the application

Preserve the current design foundation; improve it as a coherent accessible product.

Implement the missing complete extracted-text viewer:

- Return or retain the exact extracted source text underlying clause offsets, with sensible size limits and documented session storage handling.
- Keep headings, unclassified fragments, and surrounding text visible. Distinguish analysed content from content that was not classified.
- Map highlights to exact source slices and test repeated phrases, Unicode, whitespace, multiline text, PDF page breaks, and merged fragments.
- Highlight using escaped text/React elements, never executable HTML from uploaded documents.
- Selecting a clause scrolls/focuses its matching source span; selecting a highlight opens the corresponding clause detail.
- Preserve filters/search and show all classes; combine label colour with text/icons. Use a usable mobile layout.
- Call this extracted-text context. Do not imply faithful PDF/DOCX page-layout reproduction unless an actual original-file viewer exists.

Complete supporting flows:

- Upload/paste, loading/progress, cancellation where feasible, errors, large-document behaviour, expiry/refresh, and clear-results controls.
- JSON/CSV export plus a readable print view that can be saved as PDF; include version, findings, warnings, and analysed coverage.
- Explain the model's evidence with a method appropriate to the serving model. Linear contributions explain linear decisions; do not use their coefficients as RBF explanations.
- Topic grouping requires a separately evaluated predictor or a visibly labelled heuristic. Complete it only with that explicit scope; never use unavailable dataset labels for user uploads.
- Keep the research dashboard backed by actual saved metrics, with protocol/representation filters, model costs, learning curves, clustering findings, and labelled evaluation stages.
- Avoid invented legal interpretations or claims that no flagged clauses guarantees safety.

## 13. Runtime, browser, and deployment verification

Run relevant checks after changes and record actual results:

- Data/ML integrity, deterministic splits, serialization, parity, class order, and calibrated-status handling.
- Backend parser/segmenter regression tests, offset checks, PDF/DOCX/TXT paths, corrupt/encrypted/scanned inputs, limits, cleanup, readiness, timeouts, and concurrency.
- Frontend type checks, lint, production build, and meaningful browser/integration tests.
- Real browser review of upload, paste, search/filter, source highlighting, export, refresh/expiry, mobile widths, keyboard focus and screen-reader labels.
- Performance on representative document sizes, separating extraction, transform/encoding, prediction, and total request time.
- Verify that timeout handling does not leave work running without a bound or release concurrency capacity while abandoned work continues unbounded.

For Docker, first check the actual daemon. If available, build, start, wait for readiness, verify mounted model/version, run real analysis requests, inspect logs, and stop cleanly. Compose syntax validation alone is not runtime verification. If the Linux engine is unavailable, record the error and exact commands for resumption, then continue other work.

Prepare production configuration, model rollback steps, retention/deletion documentation, dependency checks, CORS, build-time frontend API configuration, and operational guidance. Public HTTPS/rate limits/monitoring depend on a hosting target. Do not choose paid hosting or publish without the user's instruction. Licensing uncertainties remain explicit for dataset, snapshots, encoders, and trained-artifact redistribution; do not declare them resolved without evidence.

## 14. Final documentation and course deliverables

Update the existing report, cards, storyboard, and README rather than creating contradictory parallel documents.

- Final experiment report: methods, mathematics, representations, fair protocols, actual results, ablations, learning curves, clustering findings, error analysis, computational trade-offs, and limitations.
- Model/data cards: provenance, filtering, group splits, model version, uncertainty policy, supported language, measured performance, and unresolved limitations.
- Reproduction instructions: real working commands, dependency versions, required local data, expected output paths, and clean startup.
- Architecture and application walkthrough, current screenshots, and a normal/difficult/error-case demo script.
- Team preparation notes explaining TF-IDF, SVM kernels, NB, LR, trees, bagging, boosting, KNN, embeddings, PCA/SVD, K-means, calibration, and evaluation leakage.
- Final presentation content and editable slides. Read any available rubric/slide-count requirements. If none are available, create a clearly labelled provisional deck based on the existing six-part storyboard, and keep adaptation to the actual rubric open.
- Rehearse/document the demo and retain a local demonstration route.

Do not call the report final while key results are placeholders. Provide the best completed draft with clearly named pending evidence when a human/environment gate remains blocked.

## 15. Deliverables and completion criteria

Use existing repository conventions. Suggested deliverables, not mandatory new parallel files:

| Deliverable | Completion evidence |
|---|---|
| Remaining-work status | Checked tasks linked to artifacts/tests and explicit blockers |
| Extended experiment registry | All discussed model configurations and real runs, or specific feasibility failures |
| Feature/learning/clustering analyses | Reproducible outputs with interpretation and limitations |
| Candidate freeze | Complete reproducible selection/refit/evaluation recipe |
| Uncertainty report | Honest calibration and coverage findings; deployed policy only if supported |
| Document evaluation | Authentic reviewers, agreement/adjudication, coverage and metrics |
| Locked evaluation | Frozen reproducible results with hashes and protocol labels |
| Production release | Versioned package, offline/API parity, measured runtime, rollback |
| Finished application | Full extracted-text highlights, existing flows, exports, accessibility and browser checks |
| Runtime verification | Clean startup/build/tests and actual Docker evidence or named daemon blocker |
| Academic package | Evidence-backed report, cards, slides/storyboard, README and demo |

Update `PROJECT_CONTEXT.md`, `progress/WORK_LOG.md`, and the original plan's checkboxes as work proceeds. Do not report a single overall percentage unless a meaningful weighting scheme is declared.

## 16. Execution order

1. Verify the current state and inventory existing evidence.
2. Complete missing model extensions, features, learning curves, and K-means on development data.
3. Consolidate results, investigate errors, evaluate calibration, and freeze the candidate/procedure.
4. Evaluate locked clause tests and integrate the selected package.
5. Complete the original-text viewer and production UI, checking API parity and storage limits.
6. Import genuine reviewer returns and run document evaluation when available; do not block unrelated implementation while waiting.
7. Verify browser/runtime/Docker behaviour and finish documentation, report and slides.
8. Deliver a final status with executed commands, actual results, serving model/version, remaining human/environment blockers, and exact next actions.

Begin now by reading the local context and evidence. Implement this continuation plan through all feasible milestones. Do not stop after producing an implementation outline or completing only the first phase.

## 17. Explicit mid-semester to end-semester research requirements

### 17.1 What was presented at mid-semester

The supplied six-slide deck presented three classifier families: Multinomial Naive Bayes, Logistic Regression, and SVM. It compared both Linear SVM and RBF SVM, so its results table had four configurations, not four independent model families. It reported TF-IDF word unigrams/bigrams and identified RBF SVM as the best model under the historical comparison.

Preserve the deck as the historical submission. Its reported scores were NB accuracy 80.3%, macro F1 79.2%, risky recall 81.9%; LR 84.27%, 83.65%, 82.32%; Linear SVM 84.47%, 83.89%, 82.81%; RBF SVM 84.98%, 84.37%, 83.10%. Those numbers are historical claims, not newly verified results. The later audit found mixed evaluation stages/splits, so never place them alongside new protocol results as if directly comparable. Re-evaluate baseline configurations on the new common protocol when needed for a fair comparison.

### 17.2 Required end-semester comparison inventory

| Method or experiment | Relationship to mid-semester | Required evidence |
|---|---|---|
| Multinomial NB | Existing baseline | Comparable protocol result and smoothing settings |
| Logistic Regression | Existing baseline | Comparable result, regularisation and convergence |
| Linear SVM | Existing SVM variant | Comparable result and margin/regularisation explanation |
| RBF SVM | Existing SVM variant | Comparable result, C/gamma and runtime |
| Decision Tree | New classifier family | Depth/pruning/leaf study and train–validation behaviour |
| Random Forest | New classifier family | Bagging explanation, settings, result and cost |
| Gradient boosting | New classifier family | Name the actual algorithm/library, explain sequential fitting, provide result and cost |
| KNN | New classifier family | Representation, distance, k and measured result |
| Complement NB | New NB variant | Comparison with Multinomial NB; do not call it an entirely new family |
| Voting ensemble | New combination experiment | Members, hard/soft rule and gain/loss against strongest member |
| Stacking ensemble | Additional combination experiment | Group-aware out-of-fold construction, meta-model and gain/loss |
| Frozen sentence embeddings + LR | New representation experiment | Encoder/version, long-input handling and comparison with TF-IDF LR |
| Frozen sentence embeddings + Linear SVM | New representation experiment | Same encoder/folds and comparison with TF-IDF Linear SVM |
| K-means | New unsupervised analysis | Cluster selection/stability, representative clauses and pattern interpretation |
| PCA / Truncated SVD | Feature-extraction experiments | Correct distinction, dimensions, retained information where meaningful, effect on downstream results |
| Dummy classifier | Evaluation reference | Clearly identified baseline floor, not a project contribution |

The core classifier comparison therefore contains eight configurations across seven broad families: NB, LR, SVM, Decision Tree, Random Forest, gradient boosting, and KNN. Extensions add NB variants, ensemble strategies, and representation/classifier combinations. Avoid advertising a single inflated “number of models” that mixes classifiers, feature transforms, and clustering.

All named experiments are execution targets in this expanded prompt. Verify the reportedly completed tree/forest/boosting/KNN work and reuse valid runs. An experiment with a verified environment or compute blocker remains visibly pending; it is not silently optional and cannot appear as completed in the presentation. Stacking extends the original voting discussion and should be identified as an additional comparison rather than a method already shown at mid-semester.

### 17.3 What must be saved for each classifier or pipeline

Maintain `docs/MODEL_EXPERIMENT_INVENTORY.md` or an equivalent existing registry containing: method/family, feature representation, mid-semester/new status, implemented/run/validated status, dataset and split ID, tuned parameters, run IDs, and artifact/report links.

For every executed classifier comparison, save:

1. The research question and why the method is appropriate to try.
2. A short mathematical/intuitive explanation tied to the course.
3. Feature representation, preprocessing and hyperparameter search budget.
4. CV and validation accuracy, macro F1, risky precision/recall and class supports.
5. Per-class metrics and confusion matrix for the selected development configuration.
6. Training time, measured inference cost and resource limitations.
7. At least a short error/behaviour interpretation: what worked, what failed, and whether it improved on the comparable baseline.
8. A reproducible command/configuration and run identity.

Final locked-test reporting follows Sections 7 and 10: freeze the final comparison set before opening tests. Models outside that set may retain clearly labelled development-only results. Do not claim every method has a test score if it has not been evaluated there.

For clustering and reduction, save their own appropriate diagnostics and interpretations rather than assigning them supervised risk-classification accuracy by default.

### 17.4 Required end-semester narrative

Create `docs/MIDSEM_TO_ENDSEM_PROGRESS.md` summarising verified additions with evidence links. The final presentation must explain:

- The mid-semester starting point: three classifier families and a preliminary RBF choice.
- The stronger dataset/evaluation protocol and why unseen-service evaluation matters.
- What new classifier families and representation/ensemble experiments were completed.
- Which patterns, learning curves, clusters and errors taught us something about the dataset.
- Which model was selected and why, including a legitimate result that a simpler model remains strongest.
- How calibration/review handling and full-document evaluation affect reliability.
- The completed upload-to-review application and a live demonstration.
- Remaining limitations and any genuinely blocked experiments/evaluation gates.

Do not allocate one slide per model by default. Group methods into baselines, new classifier families, representation/ensemble experiments, evaluation findings and application. Put detailed configurations and per-model matrices in the report or an appendix, subject to the actual rubric. New methods that underperform are still useful findings when analysed honestly. A higher headline score than mid-semester is not required, and different datasets/protocols cannot establish an improvement by direct subtraction.

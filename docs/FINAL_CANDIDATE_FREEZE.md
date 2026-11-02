# Final candidate freeze

**Freeze date:** 3 November 2026  
**Branch:** `project-completion`  
**Selection status:** development candidate frozen before any locked-test metric is computed or reviewed  
**Primary selection metric:** macro F1  
**Required accompanying metrics:** Risky precision and Risky recall; report per-class results and confusion counts  
**No minimum Risky recall threshold is imposed.**

## Selected candidate

Use the existing tuned word unigram/bigram TF-IDF + class-weighted LinearSVC configuration:

- `TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_df=0.99, max_features=60000, sublinear_tf=True, strip_accents="unicode", dtype=float32)`
- `LinearSVC(C=1.0, class_weight="balanced", random_state=20261102, max_iter=5000)`
- Fit vectorizer and classifier on the included training rows for the applicable frozen protocol. Do not use validation or test text in the fit.
- Class order is determined by the fitted scikit-learn estimator and checked at export/API load.
- Primary deployment/evaluation protocol is the unseen-service primary split. The duplicate-aware clause protocol is a secondary analysis and is not pooled with primary scores.
- Inference is deterministic class prediction only. Do not expose probabilities or confidence values.

## Evidence reviewed

All scores below are from the training folds or development validation partition. Existing grouped-CV standard deviations are sample standard deviations (`ddof=1`) across three fixed group folds; they are not confidence intervals.

| Protocol | Training group-CV macro F1 (SD) | Validation macro F1 | Validation Risky precision | Validation Risky recall | Evidence |
|---|---:|---:|---:|---:|---|
| Primary unseen-service | 0.831567 (0.002640) | 0.820063 | 0.796875 | 0.826389 | `grouped_cv_primary_linear_features_v1`, `tuned_validation_primary_v1` |
| Secondary duplicate-aware clause | 0.838607 (0.002057) | 0.819472 | 0.787257 | 0.844728 | `grouped_cv_clause_linear_features_v1`, `tuned_validation_clause_v1` |

The candidate remained strongest on the primary registered metric among completed development comparisons. Word+character TF-IDF validated at 0.818029 primary and 0.818414 secondary. Frozen MiniLM embeddings with the best LinearSVC configuration scored 0.727594 primary and 0.735312 secondary in grouped CV; PCA-reduced embeddings were lower. The tuned HistGradientBoosting candidates scored 0.793059 / 0.786721 (primary CV/validation) and 0.804610 / 0.796881 (secondary). Hard voting, soft voting, and stacking did not improve primary validation macro F1. The full machine-readable comparison and artifacts are under `results/experiments/experiment_registry_v1/` and sibling run directories.

The candidate is selected based on macro F1. Risky precision and recall are disclosed to make the operational trade-off visible, but neither is a gate. No threshold was chosen by viewing test performance.

## Frozen set of choices

This freeze covers the model family, feature representation, preprocessing settings, class weighting, C value, label ordering behavior, primary/secondary protocol distinction, selection metric, and final fit recipe. No more model, feature, calibration, or threshold selection will be performed against locked-test results. If a material change becomes necessary after test scoring, treat the current test score as consumed and require a newly justified evaluation design; do not silently retune on this test.

The calibrated model/ensemble outputs remain research diagnostics and are not part of the selected application candidate. Human document-review labels are a separate evaluation source; their pending status does not change this clause-level model freeze.

## Locked-test boundary disclosure

On 3 November 2026, initial embedding and tuning runs called the former shared split loader, which loaded all dataset fields—including locked-test text and labels—into process memory before the experiment code filtered development partitions. The interrupted runs emitted only development fold results; they produced no locked-test metrics or summaries, and test information was not used in selection. This is recorded as a boundary incident. Therefore this project does **not** claim that the locked test remained untouched. No locked-test scores have been computed or reviewed.

The shared loader has since gained `load_development_bundle`, which verifies the frozen source checksum, scans CSV record boundaries using only point IDs, and parses only temporary train/validation records. All continuation experiments after the incident used that development-only loader. The evaluation script below must use it for training/validation construction, then access only the declared test partition for the single frozen scoring operation.

## Authorized evaluation procedure

After this document is committed:

1. Load the frozen train/validation records through `load_development_bundle` and verify the recorded dataset/split hashes.
2. Fit the declared vectorizer and LinearSVC from scratch on included training rows only.
3. Load the locked test partition once, predict once, and write predictions and metrics without changing any model choice.
4. Report macro F1 first; include Risky precision/recall, all-class metrics, confusion matrix, error counts, and group-aware uncertainty if the defined bootstrap is reproducible. Clearly call this the first scored test evaluation after a documented loader boundary incident.
5. Preserve the result and logs. Do not rerun selection or edit the freeze in response to a disappointing score.

The independent full-document human review remains pending authentic reviewer labels and adjudication and is not replaced by this clause-level test.

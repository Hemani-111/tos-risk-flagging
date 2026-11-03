# Experiment inventory

Evidence-backed inventory of all completed development experiments for the ToS Risk Flagging project. Every entry is drawn from `results/experiments/experiment_registry_v1/experiment_registry.csv` (run IDs, parameters, metrics, timestamps), sibling run directories, and `docs/LOCKED_TEST_EVALUATION_v1.md`. No metrics are fabricated; runs marked "not executed" are absent from the registry.

Dataset: SHA-256 `cee557cc927d754cf17675154ed5e1e32eee2fdb9af6700c526e62cd66969f8c`  
Split: `split_manifest_v1` (fixed seed 20261102)  
Primary included rows: train 13,439 / validation 2,658 / test 2,585  
Clause included rows: train 13,434 / validation 2,607 / test 2,602  
Development experiments use `src.splitting.load_development_bundle` (train/validation only); locked test text/labels are never materialized during development selection.

Registered primary selection metric: macro F1. Risky precision and recall reported alongside. No minimum-Risky-recall threshold.

---

## 1. Existing classifiers — first-pass benchmark (validation only)

Run IDs: `benchmark_primary_wordtfidf_v1` (primary), `benchmark_clause_wordtfidf_v1` (clause)  
Representation: word unigram/bigram TF-IDF (sparse) for NB/LR/Linear SVM; dense TruncatedSVD 100 components for tree/forest/HistGradientBoosting/KNN/RBF SVM  
Protocol: primary unseen-service and clause duplicate-aware, scored once on validation  
Status: completed / validated

| Model | Primary validation macro F1 | Clause validation macro F1 | Evidence |
|-------|----------------------------|---------------------------|----------|
| Dummy prior | 0.1956 | 0.1934 | registry rows benchmark_primary/benchmark_clause |
| Multinomial NB | 0.7980 | 0.8033 | registry rows |
| Complement NB | 0.7936 | 0.8037 | registry rows |
| Logistic Regression C=1 | 0.8185 | 0.8084 | registry rows |
| Linear SVM C=1 | 0.8204 | 0.8189 | registry rows |
| RBF SVM (SVD100) | 0.8064 | 0.8060 | registry rows |
| Decision Tree (SVD100) | 0.6653 | 0.6831 | registry rows |
| Random Forest (SVD100) | 0.7851 | 0.7830 | registry rows |
| HistGradientBoosting (SVD100) | 0.7809 | 0.7865 | registry rows |
| KNN (SVD100) | 0.7837 | 0.7831 | registry rows |

Directory: `results/experiments/benchmark_{primary,clause}_wordtfidf_v1/` (`validation_metrics.csv`)  
Interpretation: Linear SVM strongest of the first-pass family screen; RBF SVM below Linear SVM and more expensive. All benchmark runs excluded locked test (`locked_test_used: False`).

---

## 2. Family-specific tuning and train-versus-validation analysis

Run IDs: `expanded_classical_primary_v1`, `expanded_classical_clause_v1`  
Representation: word unigram/bigram TF-IDF max_features=60000, then training-fold TruncatedSVD to dense (required for tree/forest/boosting/KNN)  
Protocol: primary and clause; three fixed grouped folds within training only  
Status: completed / validated

Selected per-family validation results (max mean macro F1 over bounded grid):

### Primary protocol
| Family | Validation macro F1 | Tuned parameters | Train macro F1 (train→held-fold gap) | CV macro F1 (SD) |
|--------|--------------------|------------------|--------------------------------------|------------------|
| Decision Tree | 0.6344 | max_depth=30, ccp_alpha=0.001, min_samples_leaf=2, balanced | ~0.729 | 0.6681 (0.00698) |
| Random Forest | 0.7828 | max_depth=None, balanced_subsample, sqrt, min_samples_leaf=2, n_estimators=200 | ~0.998 | 0.7797 (0.00186) |
| HistGradientBoosting | 0.7867 | learning_rate=0.1, max_iter=200, max_leaf_nodes=31 | ~0.999 | 0.7931 (0.00248) |
| KNN | 0.7837 | n_neighbors=15, euclidean, distance weights, n_jobs=4 | ~0.999 | 0.7848 (0.00546) |

### Clause protocol
| Family | Validation macro F1 | Tuned parameters | CV macro F1 (SD) |
|--------|--------------------|------------------|------------------|
| Decision Tree | 0.6920 | max_depth=30, ccp_alpha=0.001, min_samples_leaf=2 | 0.6737 (0.00404) |
| Random Forest | 0.7771 | max_depth=None, balanced_subsample, sqrt, n_estimators=200 | 0.7847 (0.00619) |
| HistGradientBoosting | 0.7969 | learning_rate=0.1, max_iter=200, max_leaf_nodes=31 | 0.8046 (0.00710) |
| KNN | 0.7787 | n_neighbors=31, euclidean, distance weights | 0.7913 (0.00812) |

Directory: `results/experiments/expanded_classical_{primary,clause}_v1/` (`cv_summary.csv`, `cv_fold_metrics.csv`, `validation_selected_family_metrics.csv`, `validation_selected_family_predictions.csv`, per-family confusion CSVs, `run_metadata.json`)  
Train–validation gap: tree/forest/boosting/KNN selected fold train macro F1 approached 0.999, indicating substantial train-to-held-fold overfitting gap. None exceeded the lexical Linear SVM development baseline (0.8316 primary CV / 0.8386 clause CV). Windows joblib physical-core enumeration warning appeared during parallel tree-family fits; runs completed.

---

## 3. Voting and stacking

Run IDs: `ensemble_calibration_primary_v1`, `ensemble_calibration_clause_v1`  
Representation: fold-local word TF-IDF; LinearSVC and LogisticRegression base learners; LogisticRegression meta-model  
Protocol: primary and clause; group-fold out-of-fold construction  
Status: completed / validated

| Ensemble | Primary validation macro F1 | Clause validation macro F1 | vs LinearSVC baseline |
|----------|----------------------------|---------------------------|----------------------|
| Hard vote | 0.8170 | 0.8175 | below (LinearSVC 0.8201 / 0.8195) |
| Soft vote (calibrated) | 0.8199 | 0.8217 | near/below |
| Stacking (LR meta) | 0.8191 | 0.8215 | below/near |

Directory: `results/experiments/ensemble_calibration_{primary,clause}_v1/` (`validation_ensemble_metrics.csv`, `oof_ensemble_metrics.csv`)  
No clear macro-F1 gain over lexical LinearSVC. Hard voting changed Risky precision/recall trade-offs (recall up, precision down) without improving primary validation macro F1. Stacking OOF inputs kept group-fold out of fold to prevent meta-model learning on in-sample base predictions.

---

## 4. Frozen sentence embeddings + Logistic Regression / Linear SVM

Run IDs: `remaining_features_primary_v1`, `remaining_features_clause_v1`  
Representation: MiniLM-L6-v2 (revision b9db1e8a0d3a51769172ba8546f282a73f066e47, Apache-2.0, English, 384 dim, 256 wordpieces, local CPU inference) frozen embeddings  
Protocol: primary and clause; group-fold CV within training  
Status: completed / validated

Best embedding LinearSVC (C=1, no PCA):
- Primary grouped CV macro F1: 0.727594 (SD 0.00136)
- Clause grouped CV macro F1: 0.735312 (SD 0.00511)

Best embedding LogisticRegression (C=1, no PCA):
- Primary grouped CV macro F1: 0.720830
- Clause grouped CV macro F1: 0.724423

All embedding configurations trail lexical TF-IDF Linear SVM (0.831567 primary / 0.838607 clause CV). Zero clauses exceeded the 256-wordpiece truncation limit. Embedding cache: 18,635 unique development clauses, local CPU, 636 seconds (~29.29 clauses/sec).

Directory: `results/experiments/remaining_features_{primary,clause}_v1/` (`embedding_group_cv_summary.csv`, `embedding_selected_validation.csv`, `group_learning_curves.csv`)  
Encoder/model/tokener/cache checksums recorded in local ignored metadata.

---

## 5. Word + character TF-IDF

Run IDs: `remaining_features_primary_v1`, `remaining_features_clause_v1`, `lexical_ablation_{primary,clause}_v1`  
Representation: word 1-2gram TF-IDF (max_features=60000) independently learned and horizontally concatenated with character 3-5gram TF-IDF  
Protocol: primary and clause  
Status: completed / validated

| Config | Primary validation macro F1 | Primary CV macro F1 | Clause validation macro F1 | Clause CV macro F1 |
|--------|----------------------------|--------------------|---------------------------|-------------------|
| Word+char LinearSVC C=1 | 0.818029 | 0.829054 | 0.818414 | 0.838001 |
| Word-only LinearSVC C=1 | 0.820063 | 0.831567 | 0.819472 | 0.838607 |

Directory: `results/experiments/remaining_features_{primary,clause}_v1/` (`word_char_validation.csv`); `results/experiments/lexical_ablation_{primary,clause}_v1/` (`cv_summary.csv`)  
Word+character slightly trails word-only on both protocols; not selected.

---

## 6. PCA on embeddings, Truncated SVD, K-means, group-aware learning curves

### PCA on embeddings (remaining_features_*_v1)
PCA dimensions 64/128 tested on MiniLM embeddings for LinearSVC C=0.1/1.0/10.0 and LogisticRegression C=0.1/1.0/10.0. All PCA-reduced scores are below raw (PCA=nan) embedding scores, which are themselves below lexical TF-IDF. Example best raw embedding LinearSVC primary CV 0.727594; PCA=128 variants ~0.697–0.701.

Directory: `results/experiments/remaining_features_{primary,clause}_v1/` (`embedding_group_cv_summary.csv`)

### Truncated SVD
Used as the dense representation (100 components, training-fold fitted) for Decision Tree, Random Forest, HistGradientBoosting, KNN, and RBF SVM in benchmark and expanded-classical runs. Not applied to sparse linear models (native sparse support).

Directory: `results/experiments/benchmark_{primary,clause}_wordtfidf_v1/`, `expanded_classical_{primary,clause}_v1/`

### K-means (ensemble_calibration_*_v1)
Training-only MiniLM embeddings; k=3/5/8/12; three seeds; cosine silhouette; stability (pairwise ARI); cluster sizes; descriptive label composition; representative clauses; PCA coordinates.

| Protocol | Cosine silhouette range | Stability | Interpretation |
|----------|------------------------|-----------|----------------|
| Primary | ~0.075–0.098 | falls at larger k | exploratory only |
| Clause | ~0.075–0.098 | falls at larger k | exploratory only |

Clusters are not risk labels; descriptive label composition mixes risk categories. Not deployed.

Directory: `results/experiments/ensemble_calibration_{primary,clause}_v1/` (KMeans rows in registry)

### Group-aware learning curves (remaining_features_*_v1)
Five group fractions (0.1, 0.25, 0.5, 0.75, 1.0), three samples each, fixed held-out development evaluation. Word LinearSVC primary reaches validation macro F1 0.820063 at full training (13,439 rows / 3.0 groups fraction 1.0). Embedding curve plateaus lower (~0.719 at full). Sample/group counts, F1, risky recall, fit time, variability saved.

Directory: `results/experiments/remaining_features_{primary,clause}_v1/` (`group_learning_curves.csv`)

---

## 7. Calibration and review-coverage evaluation

Run IDs: `ensemble_calibration_primary_v1`, `ensemble_calibration_clause_v1`  
Representation: word unigram/bigram TF-IDF + LinearSVC with group-fold sigmoid calibration  
Protocol: primary and clause  
Status: completed / validated (diagnostics only; not deployed)

| Protocol | Validation macro F1 | Risky precision | Risky recall | Brier | Log loss | Risky missed |
|----------|--------------------|-----------------|--------------|-------|----------|--------------|
| Primary | 0.822045 | 0.8038 | 0.8299 | 0.2489 | 0.4593 | 147 |
| Clause | 0.821318 | 0.7914 | 0.8308 | 0.2523 | 0.4620 | 146 |

Directory: `results/experiments/ensemble_calibration_{primary,clause}_v1/` (`calibration_validation.json`)  
Calibration diagnostics did not authorize a user-facing probability or threshold policy; no `Needs review` status exposed; numerical confidence not deployed. Probabilities are not legal-risk likelihoods.

Review coverage: `scripts/verify_document_review_coverage.py` → `results/document_review_coverage_v1.json` (723 review-pack clauses across three consumer Terms; 1,557 clauses across six snapshots; character coverage 91.9%–98.7%; exact PDF/pypdf-6.21.4 parity; both blind sheets aligned, no labels).

---

## 8. Candidate freeze and locked-test evaluation

### Freeze
Document: `docs/FINAL_CANDIDATE_FREEZE.md` (commit `c68fdcef9310007477d8245508ee2e623bc364af`)  
Selected candidate: word unigram/bigram TF-IDF + class-weighted LinearSVC C=1  
- `TfidfVectorizer(analyzer="word", ngram_range=(1,2), min_df=2, max_df=0.99, max_features=60000, sublinear_tf=True, strip_accents="unicode", dtype=float32)`
- `LinearSVC(C=1.0, class_weight="balanced", random_state=20261102, max_iter=5000)`  
Primary protocol: unseen-service. Secondary: duplicate-aware clause (not pooled).  
Selection metric: macro F1; Risky precision/recall accompanying; no minimum-recall threshold.  
Freeze disclosed the loader boundary incident (old `load_split_bundle` materialized full CSV incl. locked-test text/labels before filtering; no test metrics computed/viewed; not used in selection).  
Package: `models/releases/linear-svc-primary-v2/` (metadata.json, model.joblib, vectorizer.joblib), class order [Neutral, Risky, Safe], 44,489 features, 13,439 training rows.

### Locked-test evaluation (scored once after freeze)
Evaluation commit: `1f4a5c1ac05666073e3c9105958ec07511b09302`  
Directory: `results/locked_evaluation_v1/` (`primary/`, `clause/`, `evaluation_registry.json`)

| Protocol | Test rows | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FP | Risky FN | Group-bootstrap 95% interval |
|----------|-----------|----------|----------|-----------------|--------------|----------|----------|------------------------------|
| Primary unseen-service | 2,585 | 0.8358 | 0.8395 | 0.8229 | 0.8287 | 153 | 147 | 0.8205–0.8496 |
| Clause duplicate-aware | 2,602 | 0.8144 | 0.8190 | 0.7922 | 0.8117 | 182 | 161 | 0.7989–0.8301 |

Train/test groups disjoint: true for both. Evaluation run once; registry refuses repeats for a recorded protocol. Risky false negatives remain (147 primary, 161 secondary); application must retain review framing.

---

## Promotion rationale for `linear-svc-primary-v2`

Promoted because it was the strongest development candidate on the registered primary metric (macro F1) across every completed comparison:
- Grouped CV primary macro F1 0.831567 (SD 0.002640), validation 0.820063; clause CV 0.838607 (SD 0.002057), validation 0.819472 — above all other families.
- Word+character TF-IDF slightly lower (0.8180/0.8184 validation).
- Frozen MiniLM embeddings much lower (0.7276/0.7353 CV); PCA reduced embedding scores further.
- Decision Tree/Random Forest/HistGradientBoosting/KNN all ≤0.7969 validation with large train→held-fold gaps.
- Hard voting, soft voting, stacking: no clear macro-F1 gain over LinearSVC.
- Practical considerations: deterministic class prediction only (no uncalibrated probabilities), fast inference (~0.08 ms/clause in locked eval), compact versioned artifact, coefficient stability analyzed (top-100 token Jaccard 0.35–0.47 across folds; coefficients are associations, not legal explanations).

Freeze record: `docs/FINAL_CANDIDATE_FREEZE.md`. Evaluation record: `docs/LOCKED_TEST_EVALUATION_v1.md` + `results/locked_evaluation_v1/evaluation_registry.json`.

### Offline/API prediction parity
The backend health endpoint confirms model identity (`modelVersion: linear-svc-primary-v2`, status ok) and backend tests (45 passed) load the package, transform, and predict valid labels through `TestClient`. However, there is **no dedicated offline-vs-API prediction-parity test** asserting that raw `model.predict(vectorizer.transform(X))` produces identical labels to the `/api/v1/documents/analyze` response for the same inputs. API tests use `TestClient` (real model through the API) and some monkeypatch `predict` with controlled labels. Health endpoint alone establishes model loading/identity, not prediction parity. A dedicated parity check (offline batch vs API batch on fixed fixtures) is feasible and recommended before claiming parity.

---

## Status summary by section (REMAINING_WORK_AI_IDE_PROMPT.md §5–10)

| Section | Area | Status |
|---------|------|--------|
| §5 | Existing classifiers (NB, LR, SVM, tree, forest, boosting, KNN, Complement NB, dummy) | Executed & validated (benchmark runs) |
| §5 | Family tuning & train-vs-validation (tree/forest/boosting/KNN) | Executed & validated (expanded_classical runs) |
| §5 | Voting ensemble (hard/soft) | Executed & validated; no macro-F1 gain |
| §5 | Stacking ensemble | Executed & validated; no macro-F1 gain |
| §5 | Frozen embeddings + LR / Linear SVM | Executed & validated; below lexical |
| §6 | Word unigram vs unigram/bigram | Executed (uni+bigram selected) |
| §6 | Character TF-IDF & word+char combination | Executed; word+char slightly trails word-only |
| §6 | Length/readability/negation/phrase features + ablations | Executed (lexical_ablation; lexical-only ~0.44, combined marginal) |
| §6 | Truncated SVD on sparse TF-IDF | Executed (dense models use SVD100) |
| §6 | PCA on embeddings vs unreduced | Executed; PCA lowers scores |
| §6 | Group-aware learning curves | Executed (word + embedding) |
| §6 | Feature importance stability | Executed (linear_feature_stability; Jaccard 0.35–0.47) |
| §6 | K-means k=3/5/8/12 | Executed; weak silhouette, exploratory only |
| §7 | Consolidated experiment registry | Executed (experiment_registry_v1 CSV/JSON/Markdown) |
| §7 | Candidate freeze | Executed (docs/FINAL_CANDIDATE_FREEZE.md; package built) |
| §8 | Calibration & review | Executed (diagnostics only; not deployed) |
| §8 | Unsupported/empty/gibberish/short input testing | Not formally executed as validation; covered illustratively in docs/DEMO_RUN_SHEET.md only |
| §9 | Independent document evaluation | Pending authentic reviewer labels (sheets blank) |
| §10 | Locked-test evaluation | Completed once after freeze; do not re-score |

### §17 mid-to-endsemester requirements
All eight required configurations (NB, LR, Linear SVM, RBF SVM, Decision Tree, Random Forest, gradient boosting, KNN) plus Complement NB, voting, stacking, embeddings+LR, embeddings+Linear SVM, K-means, PCA/SVD, dummy are executed with comparable-protocol evidence. `docs/MIDSEM_TO_ENDSEM_PROGRESS.md` and `docs/TEAM_PREPARATION_NOTES.md` exist. Provisional six-slide storyboard exists (`docs/PRESENTATION_STORYBOARD_v1.md`); editable PPTX not yet created — see slides note below.

---

## Slides / PowerPoint generation

`python-pptx` is **not installed** in the current environment but **is downloadable** (wheel `python_pptx-1.0.2-py3-none-any.whl`, 472 KB) from the package index. Therefore an editable PPTX can be created locally with `python-pptx`; the unavailable "Spaces/Artifact Tool runtime" does **not** by itself establish that an editable PPTX cannot be created.

Next step: `python -m pip install python-pptx` then generate a six-slide provisional deck from `docs/PRESENTATION_STORYBOARD_v1.md` content. This is independent work that does not depend on the human-review, Docker, or browser blockers.

---

## Open blockers (genuine; kept open)

1. **Human review:** two blind reviewer sheets blank under ignored `data/review/snapshots_v1/` (`reviewer_a_segments_v1.csv`, `reviewer_b_segments_v1.csv`). Await authentic labels; then run `python scripts/analyze_document_annotation_agreement.py`. Do not simulate labels.
2. **Docker:** `docker info` fails — `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.` Client 29.7.2 / Compose 5.3.1 installed; daemon unreachable. Resumption: `docker compose build` → `docker compose up -d` → `Invoke-RestMethod http://127.0.0.1:8000/api/v1/health` → verify `linear-svc-primary-v2` → `docker compose down`. Documented in `docs/DEPLOYMENT_GUIDE.md`.
3. **Browser UX:** screenshot/manual browser review incomplete; Windows helper could not resolve active browser URL safely. No visual pass claimed.
4. **Offline/API prediction parity:** no dedicated parity test (noted above); health endpoint only confirms identity/loading.
5. **Public hosting:** no host selected; HTTPS/CORS/rate limits/monitoring/rollback await a target.
6. **Course rubric:** pending; six-slide storyboard is provisional.

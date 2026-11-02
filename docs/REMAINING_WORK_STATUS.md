# Remaining work status

**Reviewed:** 3 November 2026  
**Branch:** `project-completion`  
**Purpose:** Evidence inventory for the original completion plan and `docs/REMAINING_WORK_AI_IDE_PROMPT.md`. This report replaces the deleted working-tree copy of the earlier status report after inspecting its committed contents; it preserves its verified evidence while updating the expanded scope. This is not a weighted percentage.

## Existing verified baseline

| Area | Verified state and evidence | Remaining gate |
|---|---|---|
| Environment | Root `.venv`: Python 3.11.9, scikit-learn 1.9.0; Node/npm documented in `PROJECT_CONTEXT.md`. Current free RAM was about 1.92 GiB. NVIDIA RTX 3050 has 6 GiB VRAM, but installed ONNX Runtime exposes only Azure and CPU providers. | Keep workloads bounded; use CPU for encoder unless a working compatible provider is configured. |
| Data | `scripts/audit_data.py`, `results/audits/data_audit_v1.json`, and `data/processed/audit_v1/`. Reconstructed source 22,497 rows; English conflict-free benchmark 19,189 rows. 23 conflicting normalized groups (52 rows) are quarantined. | Language filter is approximate; source data license is unspecified. |
| Splits | `data/splits/split_manifest_v1.{csv,json}`. `python scripts/verify_split_manifest.py` passed on 3 November. Primary partitions 13,439/2,658/2,585; secondary 13,434/2,607/2,602. Added `src.splitting.load_development_bundle`; it loads train/validation records only and was verified at 13,439/2,882 and 13,434/2,877 rows. | Near-duplicate detection is approximate. A loader boundary incident on 3 November means the locked test cannot be described as untouched; no test metrics were computed or reviewed. See incident record below. |
| EDA | `results/eda/v1/` includes class/topic/service summaries, complexity and negation analysis, associated n-grams, figures and report. Train-only PCA/K-means outputs are under `ensemble_calibration_{primary,clause}_v1/`. | Silhouette scores are weak; treat clusters as exploratory and label composition as descriptive only. |
| Existing model comparison | `results/experiments/benchmark_{primary,clause}_wordtfidf_v1/` contain validation metrics/predictions/confusions for Dummy, Multinomial/Complement NB, LR, Linear/RBF SVM, tree, forest, HistGradientBoosting and KNN. Expanded family tuning is under `expanded_classical_{primary,clause}_v1/`. | New tree/forest/boosting/KNN runs did not exceed the linear SVM development baseline; dense SVD families show large train-to-fold gaps. |
| Existing grouped tuning | `grouped_cv_{primary,clause}_linear_features_v1/`; lexical ablations under corresponding `lexical_ablation_*_v1/`. `±` is sample standard deviation (`ddof=1`) across three fixed grouped training folds. | Add word+character, PCA embeddings, learning curves and fold-stability evidence. |
| Production model | `models/selected_model/metadata.json` identifies existing RBF SVC C=10, gamma=0.1 and TF-IDF word uni/bi vectorizer. Hashes are recorded. | Do not replace until development comparisons, selection and freeze are complete; retain legacy package for rollback. |
| Human review | Six local snapshots and blind sheets for 719 clauses in ignored `data/review/snapshots_v1/`; rubric, generator and agreement tool exist. | No authentic reviewer annotations or adjudication. Review extraction/segmentation coverage against full source. |
| Application | PDF/DOCX/TXT and pasted text; clause list, filters, search, adjacent context, PDF page ranges, JSON/CSV. | No complete extracted-text viewer/highlights, unclassified spans, print/PDF report, or completed real-browser review. |
| Local verification | Backend 45 tests, Ruff, frontend lint/build, dependency audits, clean environment and Compose syntax are documented; split verification rerun 3 Nov. | Docker runtime/model mount unverified; browser flow review incomplete. |
| Academic materials | Dataset/model cards, protocol, initial model and error reports, report draft, storyboard, and expanded experiment registry. | Candidate freeze, mid-to-endsemester narrative, team notes, screenshots, and editable provisional slides remain open. |

## Expanded continuation tasks

| Task | Current status | Next action / gate |
|---|---|---|
| Bounded tuning of tree, forest, boosting and KNN | Completed on both protocols; fold metrics and selected validation results are under `results/experiments/expanded_classical_{primary,clause}_v1/`. The finite grids cover depth/pruning/leaf, forest size/depth/leaf, boosting iterations/rate/leaves, and KNN neighbors/weights/distance. CV/validation macro F1, Risky P/R, train fit, model costs and warnings are recorded. | Results trail the existing linear development baseline. HistGradientBoosting and KNN were strongest of these families. Inspect finalized comparison in the experiment registry/report. |
| Hard voting | Completed using fold-local group-OOF LR and LinearSVC; see `ensemble_calibration_*_v1/`. | Macro F1 below LinearSVC; Risky recall increased while precision fell. |
| Soft voting | Completed using group-fold sigmoid-calibrated SVC and LR probabilities; Brier/log loss and Risky reliability bins are saved. | Keep as internal validation diagnostics; probabilities are not legal-risk likelihoods. |
| Stacking | Completed using fixed group-OOF margin features and a LogisticRegression meta-model. | No validation macro-F1 improvement over lexical LinearSVC. |
| Frozen embeddings + LR / Linear SVM | Full 18,635-row MiniLM cache completed locally. CPU 636 seconds / 29.29 clauses/sec; zero clauses exceeded 256 wordpieces. Model, tokenizer, and cache checksums are in local ignored metadata. | Best raw embedding LinearSVC grouped macro F1 0.7276 primary / 0.7353 clause, below lexical TF-IDF. |
| Feature/learning analyses | Word+character, fold-local PCA 64/128/raw, learning curves (five group fractions, three samples), and LinearSVC coefficient stability are saved for both protocols. | Word+character slightly trails word-only; PCA reduced embedding scores; top-100 token Jaccard 0.35-0.47. Coefficients are associations, not explanations. |
| K-means | Training-only MiniLM clusters k=3/5/8/12, three seeds, cosine silhouette, stability, sizes, descriptive label composition, representative clauses and PCA coordinates are saved. | Cosine silhouettes 0.075–0.098; stability falls at larger k, so exploratory only. |
| Consolidated experiment registry | `experiment_registry_v1/` has machine-readable CSV/JSON and readable Markdown with results, configurations, hashes and artifact directories. | Refresh after freeze, locked evaluation and application verification. |
| Candidate freeze | Development evidence favors word unigram/bigram LinearSVC C=1, class_weight=balanced. Existing serving RBF package remains unchanged. | Write and commit `FINAL_CANDIDATE_FREEZE.md` with recipe, metric, evidence and loader incident disclosure before test scoring. |
| Calibration | Group-fold sigmoid calibration completed: primary validation macro F1 0.8220, Risky P/R 0.8038/0.8299, Brier 0.2489, log loss 0.4593; secondary 0.8213, P/R 0.7914/0.8308, Brier 0.2523, log loss 0.4620. | Keep probabilities internal; report per-class coverage and Risky misses; no unsupported confidence or abstention. |
| Locked tests | No locked-test metric has been calculated or reviewed. During initial continuation runs, the old shared loader materialized the entire source CSV, including locked-test text and labels, in process memory; those exploratory runs were terminated. | Keep test metrics sealed, freeze every development choice, then run the declared evaluation once. Do not claim the test was never opened. |
| Candidate package/API | Legacy paired RBF artifacts are hash checked | Version candidate pipeline, parity fixtures, metadata/checksums/dependencies; preserve RBF rollback; promote only by freeze procedure. |
| Complete text viewer | Absent | Return/retain exact extracted source within limits; render escaped React spans/highlights using offsets, preserve unclassified text and navigation; validate Unicode/whitespace/repeated text/PDF boundaries and storage limits. |
| Supporting UI flows | Partial | Cancellation where feasible, print-to-PDF report, source coverage, mobile/keyboard/screen-reader and refresh/expiry review. Keep method claims accurate. |
| Document evaluation | Tooling exists; sheets empty | Wait for two real blind sheets; validate, compute agreement, adjudicate, measure extraction/segmentation coverage and report small student-reviewed results. |
| Docker/browser | Compose syntax only; browser automation previously could not resolve browser URL | Check daemon, build/run/readiness/model mount and real requests if available; otherwise record exact daemon error. Complete local browser review. |
| Deployment | No host selected | Prepare local demo and deployment guide; HTTPS/rate limits/monitoring/host CORS/secrets/rollback remain pending until a host is chosen. |
| Course materials | Draft report/cards/storyboard exist | Update evidence after experiments/test; create provisional six-part editable deck; add `MIDSEM_TO_ENDSEM_PROGRESS.md`, method notes, screenshots and demo run sheet. Keep final rubric adaptation open. |

## Historical report preserved

The prior report (committed at `470f59c`) established the clean benchmark/split evidence, existing run inventory, legacy model identity, lack of human reviews, Docker daemon blocker, and local verification history. Its task table is carried forward above. This refreshed version clarifies the expanded prompt scope and the current available memory/ONNX provider details.

## Locked-test boundary incident and containment

On 3 November 2026, the embedding smoke/full runs and the first primary classical-tuning attempt called the pre-existing `load_split_bundle`. That function returns a dataframe containing train, validation, and excluded test rows; therefore the complete dataset text and labels were materialized in memory before the experiment scripts filtered to development partitions. The smoke run cached 128 development embeddings. The interrupted full embedding run reached about 6,400 of 18,635 development rows and wrote no cache. The interrupted tuning run emitted fold progress but wrote no result files. These scripts computed and printed only development-fold metrics; no test metric or test-label summary was produced, viewed, or used for selection.

The incident is recorded as a test-boundary breach: the split must no longer be called untouched. No reselection or test-driven tuning followed. The shared loader was corrected for future development work by adding `load_development_bundle`, which verifies the source checksum, scans CSV record boundaries while retaining only point IDs, writes only train/validation records to a temporary file, and lets pandas parse only that file. The loader returned only the expected development partition row counts under both protocols. All subsequent development experiments use this loader. The final test evaluation remains gated on a written candidate freeze and will be reported as the first scored test evaluation, with this access incident disclosed.

## Work completed during continuation

- **Classical family tuning:** full bounded grouped-fold tuning for Decision Tree, Random Forest, HistGradientBoosting, and KNN completed on primary and secondary protocols. Results: `results/experiments/expanded_classical_{primary,clause}_v1/`.
- **Embeddings and representations:** pinned MiniLM CPU inference completed on 18,635 unique development clauses in 636 seconds (29.29 clauses/second), zero inputs truncated at 256 wordpieces. Best embedding LinearSVC grouped macro F1: 0.7276 primary and 0.7353 clause, below lexical LinearSVC. Word+character validation macro F1: 0.8180 primary and 0.8184 clause. PCA reduced embedding scores. Group-aware learning curves and feature coefficient stability outputs are saved in `remaining_features_*_v1/` and `linear_feature_stability_*_v1/`.
- **Ensembles and calibration:** OOF hard voting and LogisticRegression stacking, group-fold sigmoid calibration, calibrated-probability soft voting, validation Brier/log-loss, Risky reliability bins and misses are saved in `ensemble_calibration_*_v1/`. These approaches did not produce a clear macro-F1 gain over the lexical LinearSVC.
- **Exploratory structure:** training-only PCA coordinates and MiniLM K-means k=3/5/8/12 with three-seed ARI, cosine silhouette, cluster counts and representative clauses are saved in those same ensemble folders. Silhouette scores are weak, so clusters remain exploratory.
- **Registry:** `results/experiments/experiment_registry_v1/` contains machine-readable CSV/JSON and readable Markdown summaries.

## Working tree preservation

At the start of execution, `docs/REMAINING_WORK_STATUS.md` was deleted in the working tree and `docs/REMAINING_WORK_AI_IDE_PROMPT.md` was untracked. The old status report was inspected from Git history before this replacement was authored. The continuation prompt remains under `docs/`; its usage line now reflects that location. Raw data and source snapshots remain ignored by Git.

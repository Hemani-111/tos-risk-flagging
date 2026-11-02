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
| EDA | `results/eda/v1/` includes class/topic/service summaries, complexity and negation analysis, associated n-grams, figures and report. | Expanded prompt additionally requires K-means and interpretation. |
| Existing model comparison | `results/experiments/benchmark_{primary,clause}_wordtfidf_v1/` contain validation metrics/predictions/confusions for Dummy, Multinomial/Complement NB, LR, Linear/RBF SVM, tree, forest, HistGradientBoosting and KNN. | These are first-pass runs; family-specific tuning/overfit analysis and comparable costs are incomplete. |
| Existing grouped tuning | `grouped_cv_{primary,clause}_linear_features_v1/`; lexical ablations under corresponding `lexical_ablation_*_v1/`. `±` is sample standard deviation (`ddof=1`) across three fixed grouped training folds. | Add word+character, PCA embeddings, learning curves and fold-stability evidence. |
| Production model | `models/selected_model/metadata.json` identifies existing RBF SVC C=10, gamma=0.1 and TF-IDF word uni/bi vectorizer. Hashes are recorded. | Do not replace until development comparisons, selection and freeze are complete; retain legacy package for rollback. |
| Human review | Six local snapshots and blind sheets for 719 clauses in ignored `data/review/snapshots_v1/`; rubric, generator and agreement tool exist. | No authentic reviewer annotations or adjudication. Review extraction/segmentation coverage against full source. |
| Application | PDF/DOCX/TXT and pasted text; clause list, filters, search, adjacent context, PDF page ranges, JSON/CSV. | No complete extracted-text viewer/highlights, unclassified spans, print/PDF report, or completed real-browser review. |
| Local verification | Backend 45 tests, Ruff, frontend lint/build, dependency audits, clean environment and Compose syntax are documented; split verification rerun 3 Nov. | Docker runtime/model mount unverified; browser flow review incomplete. |
| Academic materials | Dataset/model cards, protocol, initial model and error reports, report draft and six-part storyboard. | Expanded experiment inventory/results, freeze record, mid-to-endsemester narrative, team notes, current screenshots and editable provisional slides are missing. |

## Expanded continuation tasks

| Task | Current status | Next action / gate |
|---|---|---|
| Bounded tuning of tree, forest, boosting and KNN | Completed on both protocols; fold metrics and selected validation results are under `results/experiments/expanded_classical_{primary,clause}_v1/`. The finite grids cover depth/pruning/leaf, forest size/depth/leaf, boosting iterations/rate/leaves, and KNN neighbors/weights/distance. CV/validation macro F1, Risky P/R, train fit, model costs and warnings are recorded. | Results trail the existing linear development baseline. HistGradientBoosting and KNN were strongest of these families. Inspect finalized comparison in the experiment registry/report. |
| Hard voting | No run found | Compare a small development-selected set of base learners. |
| Soft voting | No run found; LR raw probabilities are uncalibrated | Run only if calibrated probabilities are supported and evaluated. |
| Stacking | No run found | Build group-aware OOF base features and evaluate the meta-model on validation. |
| Frozen embeddings + LR / Linear SVM | Full 18,635-row development cache is being generated locally using the pinned `sentence-transformers/all-MiniLM-L6-v2` revision `b9db1e8a0d3a51769172ba8546f282a73f066e47`; an earlier 128-row smoke cache is explicitly capped and is not an experiment result. | Finish CPU inference, then grouped CV for LR/Linear SVM and PCA dimensions. Cache and model files are ignored by Git. |
| Feature/learning analyses | Word unigram/bigram and char-only plus lexical ablation exist | Add word+char combination; group-aware learning curves for lexical and semantic leaders; PCA on embeddings; assess linear feature stability if feasible. |
| K-means | No run found | Fit only on training/development features; modest k, internal score, cluster size/stability and representative text/terms; labels used only to describe clusters after fitting. |
| Consolidated experiment registry | No expanded registry | Create machine-readable and readable tables with run ID, data/split hashes, protocol, model, representation, metrics, cost, status and artifacts. |
| Candidate freeze | No `FINAL_CANDIDATE_FREEZE.md` | Freeze one candidate/refit recipe and exact permitted finalist set before locked tests. Macro F1 remains primary; report Risky P/R; do not invent a recall threshold. |
| Calibration | Existing LR OOF/validation results are raw and uncalibrated | Compare group-respecting calibration for the practical candidate; Brier/log loss/reliability and classification/ranking trade-offs; per-class coverage and risky misses. Do not expose unsupported confidence/abstention. |
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

## Working tree preservation

At the start of execution, `docs/REMAINING_WORK_STATUS.md` was deleted in the working tree and `docs/REMAINING_WORK_AI_IDE_PROMPT.md` was untracked. The old status report was inspected from Git history before this replacement was authored. The continuation prompt remains under `docs/`; its usage line now reflects that location. Raw data and source snapshots remain ignored by Git.

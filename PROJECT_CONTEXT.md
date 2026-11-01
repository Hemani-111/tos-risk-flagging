# Project context

Last updated: 2 November 2026

## Current milestone

Phases 0 through 4 are complete. Phase 5 development error and uncertainty analysis is complete; its independent complete-document evaluation is prepared and awaits two human reviewers and adjudication. Six official source snapshots are frozen locally (three consumer Terms of Service and three privacy policies); the first blind review round covers 951 clauses from the three terms documents. No replacement production model has been selected. The historical processed CSV, existing model artifacts, and notebooks remain unchanged.

## Reproducible commands

Use the root `.venv` created with Python 3.11.9.

- `python scripts/audit_data.py` rebuilds and audits the raw-to-clause pipeline. It preserves the historical processed CSV and writes separate candidates and review exports.
- `python scripts/audit_near_duplicates.py` creates near-duplicate candidates and the high-similarity service-link decisions for the English benchmark.
- `python scripts/create_splits.py` regenerates the shared manifests and overlap assertions.
- `python scripts/verify_split_manifest.py` checks checksums, row-ID coverage, group isolation, exact-text isolation, CV fold assignments, and included class representation for both protocols.
- `python scripts/run_eda.py` writes development-only descriptive tables, figures, and a report to `results/eda/v1/`.
- `python scripts/run_model_benchmarks.py --protocol primary` runs the first-pass model family screen; use `clause` for the secondary protocol.
- `python scripts/run_grouped_cv_tuning.py` tunes linear models and text representations on fixed training-only grouped folds.
- `python scripts/run_lexical_feature_ablation.py` compares text-only, lexical-only, and combined features on grouped training folds.
- `python scripts/evaluate_tuned_candidates.py` scores CV-selected linear candidates on validation.
- `python scripts/analyze_development_errors.py` exports validation error counts and a deterministic human review queue.
- `python scripts/analyze_uncertainty.py` evaluates raw Logistic Regression probabilities and CV-derived review thresholds.
- `python scripts/verify_document_source_candidates.py` checks source candidates against the benchmark; `python scripts/fetch_document_source_candidates.py` freezes local snapshots where accessible.
- `python scripts/prepare_document_review_sheets.py` writes tracked metadata stubs; `python scripts/prepare_document_review_segments.py` creates blind clause annotation copies in the ignored snapshot folder. See `docs/INDEPENDENT_DOCUMENT_EVALUATION.md` for rubric and limitations.
- `python scripts/baseline_smoke.py` records selected-model outputs, artifact hashes, and one local smoke timing.

## Data and evaluation decisions

- The five raw CSVs match Zenodo record 15012282 v1 by all published MD5 hashes. Local retrieval date is unknown; the record page does not state a license.
- Raw-to-processed reconstruction exactly matches the historical 22,497-row file. Labels are Neutral 9,759, Risky 7,015, Safe 5,723; there are 11 missing document IDs.
- All primary keys and point/case/service/document/topic references pass. The candidate covers 1,781 services, 3,109 documents, 250 cases, and 27 topics.
- There are 338 normalized repeated-text groups (505 excess rows) and 23 conflicting groups (52 rows). Conflict excerpts are quarantined from the single-label benchmark with per-group rationale; source rows remain in the full candidate/review exports.
- The scoped English benchmark has 19,189 conflict-free rows automatically classified as English with at least 40 visible characters (Neutral 8,097; Risky 6,285; Safe 4,807). This approximate language screen excludes 3,256 rows from the conflict-free multilingual candidate; results from it apply only to the selected subset.
- English benchmark near-duplicate audit: 2,039 candidate pairs at character 4-gram Jaccard >=0.72; 43 pairs >=0.99 reviewed. Detected cross-partition text links are excluded from the lower-priority holdout with manifest reasons. MinHash can miss matches.
- Split artifacts are `data/splits/split_manifest_v1.csv` and `.json`, based on dataset SHA-256 `cee557cc927d754cf17675154ed5e1e32eee2fdb9af6700c526e62cd66969f8c`, fixed seed 20261102. Primary unseen-service included rows: 13,439/2,658/2,585. Secondary duplicate-aware clause rows: 13,434/2,607/2,602. Exact text/document/service isolation is asserted; detected near-pair crossings after exclusion are zero.
- Future experiment code should use `src/splitting.py::load_split_bundle`; it validates the frozen checksum and split contract. Test rows remain locked for final evaluation.

## Baseline environment

- Windows 11, Intel i5-12450HX (8 cores/12 logical processors), 16 GB RAM; Python 3.11.9; Node 24.15.0; npm 11.6.1; Docker 29.7.2 / Compose 5.3.1.
- Root dependencies include the backend requirements plus pandas 2.2.3, matplotlib 3.9.4, ipykernel 6.29.5, and langid 1.1.6. Backend pins match the model artifact's scikit-learn 1.9.0. The nonexistent aiofiles 23.3.1 pin was corrected to 23.2.1.
- Backend tests pass (30); frontend lockfile install, lint, TypeScript/build, Docker Compose configuration, and a fixed local API smoke request pass. Details and warnings are in `progress/WORK_LOG.md`.
- `npm ci` reported 19 advisories (14 moderate, 4 high, 1 critical), including a Next.js 14.0.3 security warning. Resolve in the planned deployment/security phase before public release.

## Next

Finish Phase 5 by obtaining independent complete-document annotations from two reviewers and adjudicating disagreements. The blind segment sheets are in ignored `data/review/snapshots_v1/`; send each reviewer their separate copy. Perplexity snapshot retrieval was blocked with HTTP 403, so it is excluded from the frozen set. Keep the locked test partitions untouched.

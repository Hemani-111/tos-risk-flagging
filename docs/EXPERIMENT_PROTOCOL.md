# Experiment protocol v1

## Dataset and split inputs

- Benchmark input: `data/processed/audit_v1/clauses_benchmark_english_v1.csv` (19,189 rows), SHA-256 `cee557cc927d754cf17675154ed5e1e32eee2fdb9af6700c526e62cd66969f8c`. The language screen keeps conflict-free excerpts auto-classified as English with at least 40 visible characters. Counts are Neutral 8,097; Risky 6,285; Safe 4,807.
- Conflicting normalized excerpts (52 rows across 23 groups) are quarantined as ambiguous excerpt-only targets. They remain in the source candidate and review exports.
- The English-only filter also excludes 3,256 rows from the conflict-free multilingual candidate that are non-English or too short for the language screen. Language identification is approximate; results apply to this filtered dataset and should not be presented as validated language ground truth.
- Split manifest: `data/splits/split_manifest_v1.csv`; provenance, counts, grouping and assertions: `data/splits/split_manifest_v1.json`.
- Regenerate the data and split artifacts from repository root with `python scripts/audit_data.py`, `python scripts/audit_near_duplicates.py`, then `python scripts/create_splits.py` using the project `.venv`.

## Evaluation settings

### Primary: unseen service

Each service is assigned to one partition. A connected service component groups services sharing normalized exact quote text, the same document ID, a point/document service metadata mismatch, or one of the 43 reviewed near-duplicate pairs with character 4-gram Jaccard at least 0.99. All rows in a connected component remain together. The single fixed `StratifiedGroupKFold(n_splits=20, shuffle=True, random_state=20261102)` assignment maps folds 0–13 to train, 14–16 to validation, and 17–19 to locked test.

Exact visible-text or candidate near-duplicate links that still cross partitions are handled with a predeclared exclusion rule: keep the training text and remove the matching text rows from the lower-priority holdout (validation before test). The manifest preserves excluded rows with a reason. This removed 224 validation and 283 test rows. Of the 19,189 English benchmark rows, the included primary split is train 13,439 (71.94%), validation 2,658 (14.23%), and test 2,585 (13.84%). All three labels occur in every partition. Exact text, document IDs, and service components have no included-row partition overlap. The largest connected component is 29 services and 689 rows.

The document audit found five point rows whose `service_id` disagrees with the source document's service metadata, involving documents 347 and 1239. Both service IDs are grouped together; details are in the split JSON.

### Secondary: duplicate-aware clause level

Group rows by connected normalized visible-text components (HTML-like tags removed, entities decoded, whitespace collapsed and case-folded). Exact text and the reviewed high-similarity near-duplicate decisions are grouped. Services may occur in different partitions. The same fixed 20-fold stratified-group assignment and seed yield train 13,434 (72.06%), validation 2,607 (13.98%), and test 2,602 (13.96%) included rows after excluding 270 validation and 276 test rows with detected cross-partition near-duplicate links. Exact visible text has no included-row partition overlap.

## Development and selection

Use three-fold `StratifiedGroupKFold` cross-validation inside the training partition only. Keep validation for development selection and threshold decisions. Do not use the locked test partition to tune, select features, or change thresholds. Split proportions are generated once with seed 20261102; do not search seeds for a preferred score.

Register macro F1 as the primary comparison metric. Report Risky precision and recall as operating trade-offs, plus per-class metrics, confusion matrix, risky false-positive/false-negative counts, fit time, inference latency, artifact size, and peak memory when measurable. Add one-vs-rest ROC-AUC/PR metrics only where continuous decision scores are meaningful; decision scores are not probabilities. Fit TF-IDF, feature selection, scaling and dimensionality reduction within each training fold using an sklearn `Pipeline`.

## Overlap caveats

The approximate MinHash near-duplicate audit found 2,039 pairs at Jaccard >=0.72. The 43 reviewed pairs >=0.99 are constrained to shared primary service components and secondary text components. Before exclusions, 870 candidate pairs crossed primary partitions and 859 crossed clause-level partitions. All detected crossings were removed from a lower-priority holdout; no detected pair crosses included partitions. This is not proof that all near duplicates were found: MinHash can miss matches. Report this limitation with results and avoid describing the split as completely boilerplate-independent.

Both protocols must be reported separately; neither is equivalent to full-document generalization. The manifest includes the source row IDs even when excluded, with explicit include flags for each protocol.

## Status

The manifests and split-isolation assertions are implemented and generated. Use `src/splitting.py::load_split_bundle` to load/validate the frozen inputs and `python scripts/verify_split_manifest.py` to check both protocols. Phase 4 first-pass models, grouped tuning, and feature ablations are recorded in `docs/MODEL_EXPERIMENTS_v1.md`. The locked test partitions remain unused. Future experiment commands must load these manifests rather than create independent splits.

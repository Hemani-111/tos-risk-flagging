# Dataset card: ToS;DR clause annotations

## Version and provenance

The local files in `data/raw/` match all five published MD5 checksums for [Zenodo record 15012282](https://zenodo.org/records/15012282), v1, “ToS;DR policies dataset (raw) - 21/07/2023”. The record describes cases, topics, services, points, and source documents collected and annotated by Terms of Service; Didn't Read. The local retrieval date is unknown. No license is stated on the record page; confirm redistribution rights before sharing the raw data or derived artifacts.

Raw-file byte counts and SHA-256 fingerprints are recorded in `results/audits/data_audit_v1.json`.

## Intended use

Educational research into screening policy excerpts for clauses deserving attention. The three labels represent dataset annotation categories. They are not legal judgments, guarantees of safety, or complete assessments of a policy.

## Construction

The reproducible pipeline selects points with `status == approved` and a nonblank `quote_text`, joins each point to one case and topic, and maps `good` to Safe, `neutral` to Neutral, and `bad` or `blocker` to Risky. All dimension-table joins use validated many-to-one cardinality. The current candidate has 22,497 rows and exactly matches the historical processed CSV in ordered values.

## Composition and known quality issues

- Neutral: 9,759; Risky: 7,015; Safe: 5,723.
- Eleven rows have no `document_id`.
- Normalization by Unicode case-folding and whitespace collapse finds 338 repeated-text groups (505 excess rows) and 23 conflicting-label groups (52 records).
- Repeated-text groups occur within one case (281 groups), across cases (57), across services (295), and across documents (300); these categories overlap. The exact-duplicate service graph links 422 services in 66 components, the largest with 252 services.
- Quote-length median is 161 characters (95th percentile 570); five quotes exceed 5,000 characters. 8,790 quotes contain HTML-like markup; two match common mojibake patterns and none contain the Unicode replacement character.
- 245 cases have multiple approved quoted points, with a maximum of 909 points attached to one case. A case label can summarize multiple issues and should not be read as an independently adjudicated sentence label.
- An approximate `langid` screen of visible text at least 40 characters long classifies 19,227 of 20,602 rows as English, 628 French, 163 Spanish, 106 German, 114 Chinese, and the remainder across smaller language counts. It is a rough dataset profile, not a validated language label; 1,895 short rows were excluded.
- The scoped English benchmark retains 19,189 conflict-free rows automatically classified as English with at least 40 visible characters (Neutral 8,097; Risky 6,285; Safe 4,807). It excludes 3,256 rows from the conflict-free multilingual candidate as non-English or language-unknown. The language filter is approximate; results apply to this filtered subset.
- On the English-only benchmark, character 4-gram MinHash found 2,039 candidate near-duplicate pairs at Jaccard 0.72 or higher. The 43 highest-similarity pairs (at least 0.99) were reviewed and their services are constrained to the same split component; lower-similarity candidates are an approximate overlap list.
- The full audit candidate retains all duplicates and conflicts. The single-label benchmark quarantines all 52 rows in the 23 conflicting text groups, leaving 22,445 records. Exports and per-group decisions are in `data/processed/audit_v1/`.
- These are selected points associated with reviewed cases, not a random sample of every sentence in policy documents. Their labels may encode the issue/case context and may not transfer to arbitrary extracted sentences.
- Language detection and annotation agreement are approximate/not fully adjudicated. The English benchmark is a scoped research subset, not a guarantee that every retained quote is English or that excluded rows are unsafe.

## Evaluation cautions

Keep services linked by exact repeated text, or by reviewed near-duplicate pairs at character 4-gram Jaccard >=0.99, in the same partition. For remaining detected cross-partition text links, the split manifest removes matching text rows from the lower-priority holdout and records the exclusion. Near-duplicate detection is approximate and can miss matches. Report unseen-service performance separately from duplicate-aware clause-level performance. Keep complete-document evaluation distinct from excerpt classification. Do not describe Safe as a guarantee or present historical metrics as a reproduced fair comparison.

## Reproduction

From the repository root, run `python scripts/audit_data.py`, `python scripts/audit_near_duplicates.py`, and `python scripts/create_splits.py`. See `docs/EXPERIMENT_PROTOCOL.md`, `PROJECT_CONTEXT.md`, and `progress/WORK_LOG.md` for the frozen protocol and current status.

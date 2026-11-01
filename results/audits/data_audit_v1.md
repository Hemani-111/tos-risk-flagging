# Data audit v1

Audit date: 2026-11-02

## Reconstruction

Approved points: 23,968; nonblank quote rows: 22,497; mapped candidate rows: 22,497.
Historical processed rows: 22,497; exact ordered match: True.
Unmatched case/topic rows: 0/0.

Rows after case join: 22,497; after topic join: 22,497.
All foreign-key checks passed: 0 orphan references across points, cases, services, and documents.
Candidate coverage: 1,781 services, 3,109 documents, 250 cases, 27 topics.

## Labels

| Label | Rows |
|---|---:|
| Neutral | 9,759 |
| Risky | 7,015 |
| Safe | 5,723 |

## Text review

Normalised repeated rows: 843; excess after first: 505.
Repeated-text groups within one case: 281; across cases: 57; across services: 295; across documents: 300.
Exact-duplicate service links form 66 components across 422 services; largest component has 252 services.
Conflicting text groups: 23; rows in those groups: 52.
All conflicting groups are context-reviewed and quarantined from the single-label benchmark: 22,445 rows remain in `clauses_benchmark_v1.csv`.
Source rows and per-text decisions remain in `conflict_review.csv` and `conflict_decisions.csv`; no source row was deleted.
Repeated same-label text is retained for now; split manifests must prevent duplicate text from crossing evaluation partitions.
Duplicate records are in `data/processed/audit_v1/duplicate_review.csv`.

## Quote and annotation checks

Quote character-length median: 161; 95th percentile: 570; over 5,000 characters: 5.
HTML-like markup: 8,790; replacement character: 0; common mojibake markers: 2.
Cases with multiple approved quoted points: 245; maximum points per case: 909.
Language screen (langid; visible text >=40 characters): {'af': 4, 'am': 39, 'br': 1, 'ca': 3, 'cs': 4, 'da': 3, 'de': 106, 'el': 2, 'en': 19227, 'es': 163, 'et': 29, 'fi': 1, 'fr': 628, 'gl': 1, 'he': 13, 'hr': 1, 'hu': 3, 'it': 21, 'ja': 5, 'lb': 1, 'lt': 5, 'lv': 2, 'mt': 27, 'nl': 24, 'no': 52, 'oc': 2, 'pl': 6, 'pt': 23, 'qu': 18, 'ro': 8, 'ru': 23, 'rw': 6, 'sl': 2, 'th': 18, 'tr': 17, 'zh': 114}; 1,895 short rows were excluded as unknown.
English-only conflict-free benchmark: 19,189 rows at `data/processed/audit_v1/clauses_benchmark_english_v1.csv`; approximate screen errors remain possible.

## Provenance and limitations

All five local file MD5 hashes match the Zenodo v1 record; SHA-256 hashes are retained in the JSON report. The local retrieval date is unknown and no license is stated on the record page.
The candidate preserves duplicates and conflicts pending review; it does not replace the historical processed dataset.

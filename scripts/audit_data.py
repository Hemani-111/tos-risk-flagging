"""Rebuild and audit the clause table from locally supplied ToS;DR CSVs.

This script never edits the raw inputs or the historical clauses_clean.csv.
Outputs are written to data/processed/audit_v1/ and results/audits/.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import date
from html import unescape
from pathlib import Path

import langid
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed" / "audit_v1"
REPORTS = ROOT / "results" / "audits"
LABEL_MAP = {"good": "Safe", "neutral": "Neutral", "bad": "Risky", "blocker": "Risky"}
FINAL_COLUMNS = [
    "point_id", "quote_text", "case_id", "classification", "label",
    "topic_id", "topic_title", "service_id", "document_id",
]


def normalise(text: object) -> str:
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def visible_quote(text: object) -> str:
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]*>", " ", str(text)))).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_unique(frame: pd.DataFrame, key: str, table: str) -> None:
    duplicates = int(frame[key].duplicated().sum())
    if duplicates:
        raise ValueError(f"{table}.{key} has {duplicates} duplicate keys")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    tables = {name: pd.read_csv(RAW / f"{name}.csv", low_memory=False)
              for name in ("topics", "services", "cases", "points", "documents")}
    schemas = {name: list(frame.columns) for name, frame in tables.items()}
    for name in ("topics", "services", "cases", "documents"):
        require_unique(tables[name], "id", name)

    points = tables["points"].rename(columns={"id": "point_id"})
    require_unique(points, "point_id", "points")
    approved = points.loc[points["status"].eq("approved")].copy()
    with_quotes = approved.loc[approved["quote_text"].notna()].copy()
    with_quotes = with_quotes.loc[with_quotes["quote_text"].astype(str).str.strip().ne("")].copy()

    cases = tables["cases"][["id", "classification", "topic_id"]].rename(columns={"id": "case_id"})
    joined = with_quotes.merge(cases, on="case_id", how="left", validate="many_to_one", indicator="case_join")
    case_unmatched = int(joined["case_join"].eq("left_only").sum())
    joined = joined.drop(columns="case_join")
    rows_after_case_join = int(len(joined))
    topics = tables["topics"][["id", "title"]].rename(columns={"id": "topic_id", "title": "topic_title"})
    joined = joined.merge(topics, on="topic_id", how="left", validate="many_to_one", indicator="topic_join")
    topic_unmatched = int(joined["topic_join"].eq("left_only").sum())
    joined = joined.drop(columns="topic_join")
    rows_after_topic_join = int(len(joined))
    joined["label"] = joined["classification"].map(LABEL_MAP)

    points_raw = tables["points"]
    references = {
        "point_rows_with_unknown_case_id": int((~points_raw["case_id"].isin(tables["cases"]["id"])).sum()),
        "point_rows_with_unknown_service_id": int((~points_raw["service_id"].isin(tables["services"]["id"])).sum()),
        "point_rows_with_nonnull_unknown_document_id": int((points_raw["document_id"].notna() & ~points_raw["document_id"].isin(tables["documents"]["id"])).sum()),
        "case_rows_with_unknown_topic_id": int((~tables["cases"]["topic_id"].isin(tables["topics"]["id"])).sum()),
    }

    unknown_classifications = joined.loc[joined["label"].isna(), "classification"].value_counts(dropna=False).to_dict()
    usable = joined.loc[joined["label"].notna()].copy()
    candidate = usable[FINAL_COLUMNS].reset_index(drop=True)
    historical_path = ROOT / "data" / "processed" / "clauses_clean.csv"
    historical = pd.read_csv(historical_path, low_memory=False)
    quote_lengths = candidate["quote_text"].astype(str).str.len()
    language_texts = candidate["quote_text"].map(visible_quote)
    detectable_language_texts = language_texts.loc[language_texts.str.len().ge(40)]
    language_codes = pd.Series("unknown_short", index=candidate.index, dtype="object")
    language_codes.loc[detectable_language_texts.index] = detectable_language_texts.map(lambda value: langid.classify(value)[0])
    language_counts = Counter(language_codes.loc[detectable_language_texts.index])
    annotation_counts = usable.groupby("case_id")["point_id"].size()
    point_status_counts = {str(k): int(v) for k, v in tables["points"]["status"].value_counts(dropna=False).items()}
    case_classification_counts = {str(k): int(v) for k, v in tables["cases"]["classification"].value_counts(dropna=False).items()}

    candidate["_norm"] = candidate["quote_text"].map(normalise)
    groups = candidate.groupby("_norm", dropna=False)
    duplicate_group_mask = groups["point_id"].transform("size").gt(1)
    duplicate_groups = candidate.loc[duplicate_group_mask].groupby("_norm", dropna=False)
    duplicate_parent: dict[str, str] = {}

    def duplicate_root(service_id: str) -> str:
        duplicate_parent.setdefault(service_id, service_id)
        if duplicate_parent[service_id] != service_id:
            duplicate_parent[service_id] = duplicate_root(duplicate_parent[service_id])
        return duplicate_parent[service_id]

    for _, frame in duplicate_groups:
        service_ids = sorted(set(frame["service_id"].dropna().astype(str)))
        for service_id in service_ids[1:]:
            first, current = duplicate_root(service_ids[0]), duplicate_root(service_id)
            if first != current:
                duplicate_parent[first] = current
    duplicate_components: dict[str, int] = {}
    for service_id in list(duplicate_parent):
        root = duplicate_root(service_id)
        duplicate_components[root] = duplicate_components.get(root, 0) + 1
    conflicting_norms = groups["label"].nunique()
    conflicting_keys = set(conflicting_norms[conflicting_norms.gt(1)].index)
    conflicts = candidate.loc[candidate["_norm"].isin(conflicting_keys)].copy()
    duplicates = candidate.loc[duplicate_group_mask].copy()
    decision_rows = []
    for norm, frame in candidate.loc[candidate["_norm"].isin(conflicting_keys)].groupby("_norm", sort=True):
        decision_rows.append({
            "normalized_text_sha256": hashlib.sha256(norm.encode("utf-8")).hexdigest(),
            "quote_text": frame["quote_text"].iloc[0],
            "row_count": int(len(frame)),
            "labels": "|".join(sorted(frame["label"].astype(str).unique())),
            "classifications": "|".join(sorted(frame["classification"].astype(str).unique())),
            "case_ids": "|".join(sorted(frame["case_id"].astype(str).unique())),
            "service_ids": "|".join(sorted(frame["service_id"].astype(str).unique())),
            "topic_titles": "|".join(sorted(frame["topic_title"].astype(str).unique())),
            "review_status": "context_reviewed",
            "benchmark_decision": "quarantine_all_rows_for_this_text",
            "rationale": "Identical excerpt has different case-derived labels. Available quote/annotation metadata cannot establish one defensible excerpt-only target; preserve every source row for audit and omit the normalized text from single-label benchmarking.",
        })
    decisions = pd.DataFrame(decision_rows)
    decisions.to_csv(OUT / "conflict_decisions.csv", index=False)
    candidate = candidate.drop(columns="_norm")
    conflicts.drop(columns="_norm").to_csv(OUT / "conflict_review.csv", index=False)
    duplicates.drop(columns="_norm").to_csv(OUT / "duplicate_review.csv", index=False)
    candidate.to_csv(OUT / "clauses_clean_candidate.csv", index=False)
    benchmark = candidate.loc[~candidate["quote_text"].map(normalise).isin(conflicting_keys)].copy()
    benchmark.to_csv(OUT / "clauses_benchmark_v1.csv", index=False)
    english_benchmark = benchmark.loc[language_codes.loc[benchmark.index].eq("en")].copy()
    english_benchmark.to_csv(OUT / "clauses_benchmark_english_v1.csv", index=False)

    input_files = {name: RAW / f"{name}.csv" for name in tables}
    report = {
        "audit_date": date.today().isoformat(),
        "source_identity": "Verified exact match to all five files in Zenodo record 15012282 v1 by published MD5 checksums.",
        "source_url": "https://zenodo.org/records/15012282",
        "source_version": "ToS;DR policies dataset (raw) - 21/07/2023, v1; published 2025-03-12",
        "source_retrieval_date": "Unknown for this local copy.",
        "source_license": "Not stated on the Zenodo record page; redistribution rights need confirmation.",
        "raw_files": {name: {"bytes": path.stat().st_size, "md5": md5(path), "sha256": sha256(path)}
                      for name, path in input_files.items()},
        "raw_schemas": schemas,
        "row_counts": {name: int(len(frame)) for name, frame in tables.items()},
        "foreign_key_checks": references,
        "pipeline_counts": {
            "points_total": int(len(points)), "points_approved": int(len(approved)),
            "approved_with_nonnull_quote": int(len(approved) - int(approved["quote_text"].isna().sum())),
            "approved_with_nonblank_quote": int(len(with_quotes)),
            "rows_after_case_join": rows_after_case_join,
            "rows_after_topic_join": rows_after_topic_join,
            "unmatched_case_rows": case_unmatched, "unmatched_topic_rows": topic_unmatched,
            "unknown_or_missing_classification_rows": int(usable.shape[0] * 0 + joined["label"].isna().sum()),
            "candidate_rows": int(len(candidate)), "historical_rows": int(len(historical)),
        },
        "candidate_label_counts": {str(k): int(v) for k, v in candidate["label"].value_counts(dropna=False).items()},
        "raw_classification_counts": {str(k): int(v) for k, v in joined["classification"].value_counts(dropna=False).items()},
        "all_case_classification_counts": case_classification_counts,
        "point_status_counts": point_status_counts,
        "unknown_classifications": {str(k): int(v) for k, v in unknown_classifications.items()},
        "missing_values_candidate": {str(k): int(v) for k, v in candidate.isna().sum().items()},
        "quote_quality": {
            "character_length_quantiles": {str(q): float(quote_lengths.quantile(q)) for q in (0, 0.25, 0.5, 0.75, 0.95, 0.99, 1)},
            "quotes_under_20_characters": int(quote_lengths.lt(20).sum()),
            "quotes_over_5000_characters": int(quote_lengths.gt(5000).sum()),
            "quotes_with_html_like_markup": int(candidate["quote_text"].astype(str).str.contains(r"<[^>]+>", regex=True).sum()),
            "quotes_with_replacement_character": int(candidate["quote_text"].astype(str).str.contains("\uFFFD", regex=False).sum()),
            "quotes_with_common_mojibake_markers": int(candidate["quote_text"].astype(str).str.contains(r"(?:Ã.|Â.|â€|â€™|ï¿½)", regex=True).sum()),
            "language_detector": "langid 1.1.6; HTML-like tags stripped, entities decoded; only visible text >=40 characters classified.",
            "language_classified_rows": int(len(detectable_language_texts)),
            "language_excluded_short_rows": int(len(candidate) - len(detectable_language_texts)),
            "language_counts": dict(sorted(language_counts.items())),
            "language_caveat": "Automatic estimates for dataset profiling only; short clauses and classifier errors require review.",
        },
        "english_benchmark": {
            "rows": int(len(english_benchmark)),
            "label_counts": {str(k): int(v) for k, v in english_benchmark["label"].value_counts().sort_index().items()},
            "selection": "Conflict-free rows automatically classified as English after stripping markup and requiring at least 40 visible characters.",
            "excluded_non_english_or_unknown_rows_from_conflict_free_candidate": int(len(benchmark) - len(english_benchmark)),
            "path": str((OUT / "clauses_benchmark_english_v1.csv").relative_to(ROOT)),
        },
        "annotation_shape": {
            "cases_with_multiple_approved_quoted_points": int(annotation_counts.gt(1).sum()),
            "maximum_approved_quoted_points_per_case": int(annotation_counts.max()),
            "interpretation": "Several point annotations may share one case; this pipeline retains each point as a separate row.",
        },
        "dataset_coverage": {
            "candidate_distinct_services": int(candidate["service_id"].nunique()),
            "candidate_distinct_documents": int(candidate["document_id"].nunique()),
            "candidate_distinct_cases": int(candidate["case_id"].nunique()),
            "candidate_distinct_topics": int(candidate["topic_id"].nunique()),
        },
        "key_checks": {f"{name}.id_unique": True for name in ("topics", "services", "cases", "points", "documents")},
        "text_audit": {
            "normalisation": "Unicode casefold plus whitespace collapse and trim; punctuation retained",
            "duplicate_rows_including_first": int(len(duplicates)),
            "excess_rows_after_first": int(len(duplicates) - duplicates["_norm"].nunique()),
            "normalised_duplicate_groups": int(duplicates["_norm"].nunique()),
            "duplicate_groups_within_one_case": int(sum(g["case_id"].nunique() == 1 for _, g in duplicate_groups)),
            "duplicate_groups_across_cases": int(sum(g["case_id"].nunique() > 1 for _, g in duplicate_groups)),
            "duplicate_groups_across_services": int(sum(g["service_id"].nunique() > 1 for _, g in duplicate_groups)),
            "duplicate_groups_across_documents": int(sum(g["document_id"].nunique(dropna=True) > 1 for _, g in duplicate_groups)),
            "duplicate_service_graph": {
                "connected_services": int(len(duplicate_parent)),
                "components": int(len(duplicate_components)),
                "largest_component_services": int(max(duplicate_components.values(), default=0)),
                "policy": "Join services that share a normalized exact-text group into one split component; preserve all rows.",
            },
            "conflicting_normalised_text_groups": int(len(conflicting_keys)),
            "conflict_rows": int(len(conflicts)),
            "conflict_policy": "Export for review; do not silently majority-label or drop in this candidate.",
            "conflict_groups_quarantined_from_benchmark": int(len(decisions)),
            "benchmark_candidate_rows_after_conflict_quarantine": int(len(benchmark)),
            "benchmark_exclusion_policy": "Exclude every row whose normalized text has more than one label; retain all original rows in clauses_clean_candidate.csv and conflict_review.csv.",
        },
        "historical_label_counts": {str(k): int(v) for k, v in historical["label"].value_counts(dropna=False).items()},
        "historical_matches_candidate_exact_order": bool(
            len(candidate) == len(historical) and candidate[FINAL_COLUMNS].equals(historical[FINAL_COLUMNS])
        ),
        "notes": [
            "No data is removed based on text duplication or label conflicts in the candidate export.",
            "All five file MD5s match the Zenodo v1 record; local retrieval date is unknown and the record page does not state a license.",
            "documents.csv is fingerprinted but is not joined into the clause table, matching the existing preprocessing notebook.",
        ],
    }
    report_path = REPORTS / "data_audit_v1.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown = [
        "# Data audit v1", "", f"Audit date: {report['audit_date']}", "",
        "## Reconstruction", "",
        f"Approved points: {len(approved):,}; nonblank quote rows: {len(with_quotes):,}; mapped candidate rows: {len(candidate):,}.",
        f"Historical processed rows: {len(historical):,}; exact ordered match: {report['historical_matches_candidate_exact_order']}.",
        f"Unmatched case/topic rows: {case_unmatched:,}/{topic_unmatched:,}.", "",
        f"Rows after case join: {rows_after_case_join:,}; after topic join: {rows_after_topic_join:,}.",
        f"All foreign-key checks passed: {sum(report['foreign_key_checks'].values()):,} orphan references across points, cases, services, and documents.",
        f"Candidate coverage: {report['dataset_coverage']['candidate_distinct_services']:,} services, {report['dataset_coverage']['candidate_distinct_documents']:,} documents, {report['dataset_coverage']['candidate_distinct_cases']:,} cases, {report['dataset_coverage']['candidate_distinct_topics']:,} topics.", "",
        "## Labels", "", "| Label | Rows |", "|---|---:|",
    ]
    markdown += [f"| {label} | {count:,} |" for label, count in report["candidate_label_counts"].items()]
    markdown += ["", "## Text review", "",
                 f"Normalised repeated rows: {len(duplicates):,}; excess after first: {report['text_audit']['excess_rows_after_first']:,}.",
                 f"Repeated-text groups within one case: {report['text_audit']['duplicate_groups_within_one_case']:,}; across cases: {report['text_audit']['duplicate_groups_across_cases']:,}; across services: {report['text_audit']['duplicate_groups_across_services']:,}; across documents: {report['text_audit']['duplicate_groups_across_documents']:,}.",
                 f"Exact-duplicate service links form {report['text_audit']['duplicate_service_graph']['components']:,} components across {report['text_audit']['duplicate_service_graph']['connected_services']:,} services; largest component has {report['text_audit']['duplicate_service_graph']['largest_component_services']:,} services.",
                 f"Conflicting text groups: {len(conflicting_keys):,}; rows in those groups: {len(conflicts):,}.",
                 f"All conflicting groups are context-reviewed and quarantined from the single-label benchmark: {len(benchmark):,} rows remain in `clauses_benchmark_v1.csv`.",
                 "Source rows and per-text decisions remain in `conflict_review.csv` and `conflict_decisions.csv`; no source row was deleted.",
                 "Repeated same-label text is retained for now; split manifests must prevent duplicate text from crossing evaluation partitions.",
                 "Duplicate records are in `data/processed/audit_v1/duplicate_review.csv`.", "",
                 "## Quote and annotation checks", "",
                 f"Quote character-length median: {report['quote_quality']['character_length_quantiles']['0.5']:.0f}; 95th percentile: {report['quote_quality']['character_length_quantiles']['0.95']:.0f}; over 5,000 characters: {report['quote_quality']['quotes_over_5000_characters']:,}.",
                 f"HTML-like markup: {report['quote_quality']['quotes_with_html_like_markup']:,}; replacement character: {report['quote_quality']['quotes_with_replacement_character']:,}; common mojibake markers: {report['quote_quality']['quotes_with_common_mojibake_markers']:,}.",
                 f"Cases with multiple approved quoted points: {report['annotation_shape']['cases_with_multiple_approved_quoted_points']:,}; maximum points per case: {report['annotation_shape']['maximum_approved_quoted_points_per_case']:,}.",
                 f"Language screen (langid; visible text >=40 characters): {report['quote_quality']['language_counts']}; {report['quote_quality']['language_excluded_short_rows']:,} short rows were excluded as unknown.",
                 f"English-only conflict-free benchmark: {len(english_benchmark):,} rows at `data/processed/audit_v1/clauses_benchmark_english_v1.csv`; approximate screen errors remain possible.", "",
                 "## Provenance and limitations", "",
                 "All five local file MD5 hashes match the Zenodo v1 record; SHA-256 hashes are retained in the JSON report. The local retrieval date is unknown and no license is stated on the record page.",
                 "The candidate preserves duplicates and conflicts pending review; it does not replace the historical processed dataset.", ""]
    (REPORTS / "data_audit_v1.md").write_text("\n".join(markdown), encoding="utf-8")
    print(f"Wrote {report_path}")
    print(f"Candidate rows: {len(candidate):,}; historical rows: {len(historical):,}; exact ordered match: {report['historical_matches_candidate_exact_order']}")
    print(f"Duplicate groups: {report['text_audit']['normalised_duplicate_groups']:,}; conflict groups: {len(conflicting_keys):,}")


if __name__ == "__main__":
    main()

"""Verify frozen policy snapshot and blind review-sheet coverage without labels."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.clause_segmenter import ClauseSegmenter  # noqa: E402
from app.services.document_parser import PdfParser, TxtParser  # noqa: E402

REGISTRY = ROOT / "data/review/document_sources_candidates_v1.csv"
SNAPSHOTS = ROOT / "data/review/snapshots_v1"
OUTPUT = ROOT / "results/document_review_coverage_v1.json"
SELECTED = {"anthropic_consumer_terms", "mistral_consumer_terms_row", "you_com_terms"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def coverage(text: str, clauses: list) -> dict:
    previous_end = 0
    overlap_chars = 0
    covered_chars = 0
    gaps: list[tuple[int, int]] = []
    for clause in clauses:
        start, end = clause.start_offset, clause.end_offset
        if start < previous_end:
            overlap_chars += max(0, previous_end - start)
        if start > previous_end:
            gaps.append((previous_end, start))
        if not (0 <= start <= end <= len(text)) or text[start:end] != clause.text:
            raise ValueError(f"Offset/text mismatch for {clause.clause_id}")
        covered_chars += end - start
        previous_end = max(previous_end, end)
    if previous_end < len(text):
        gaps.append((previous_end, len(text)))
    gap_chars = sum(end - start for start, end in gaps)
    gap_words = sum(len(text[start:end].split()) for start, end in gaps)
    return {
        "source_characters": len(text),
        "source_words": len(text.split()),
        "clause_count": len(clauses),
        "covered_clause_characters": covered_chars,
        "covered_character_fraction": round(covered_chars / max(1, len(text)), 6),
        "unsegmented_gap_characters": gap_chars,
        "unsegmented_gap_words": gap_words,
        "unsegmented_gap_count": len(gaps),
        "overlap_characters": overlap_chars,
    }


def main() -> None:
    sources = read_csv(REGISTRY)
    source_by_id = {row["document_id"]: row for row in sources}
    if not SELECTED.issubset(source_by_id):
        raise SystemExit("Review source registry is missing a selected document")

    segmenter = ClauseSegmenter()
    document_reports = []
    expected: dict[str, tuple[str, list]] = {}
    available_ids = sorted(
        row["document_id"] for row in sources
        if row["review_status"] == "snapshot_frozen_review_pending"
    )
    for document_id in available_ids:
        row = source_by_id[document_id]
        text_path = ROOT / row["text_snapshot_path"]
        binary_path = ROOT / row["snapshot_path"]
        if not text_path.is_file() or not binary_path.is_file():
            raise FileNotFoundError(f"Missing frozen snapshot for {document_id}")
        text = TxtParser().parse(str(text_path))
        clauses = segmenter.segment(text)
        expected[document_id] = (text, clauses)
        source_parity = None
        if binary_path.suffix.lower() == ".pdf":
            parsed_source = PdfParser().parse(str(binary_path))
            source_parity = {
                "pdf_parser_character_count": len(parsed_source),
                "pdf_parser_matches_review_text_exactly": parsed_source == text,
            }
            if parsed_source != text:
                raise ValueError(f"PDF text snapshot differs from the current application parser for {document_id}")
        document_reports.append({
            "document_id": document_id,
            "review_pack_member": document_id in SELECTED,
            "text_extraction_engine": row.get("text_extraction_engine", ""),
            "text_extraction_version": row.get("text_extraction_version", ""),
            "binary_sha256_matches_registry": sha256(binary_path) == row["snapshot_sha256"],
            "text_sha256_matches_registry": hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest() == row["text_sha256"],
            "text_file_byte_sha256": sha256(text_path),
            "pdf_text_parity": source_parity,
            **coverage(text, clauses),
        })

    sheets = {}
    canonical_ids = None
    expected_review_clause_count = sum(
        len(clauses) for doc_id, (_text, clauses) in expected.items() if doc_id in SELECTED
    )
    for reviewer in ("reviewer_a", "reviewer_b"):
        path = SNAPSHOTS / f"{reviewer}_segments_v1.csv"
        rows = read_csv(path)
        clause_rows = [r for r in rows if r["annotation_type"] == "current_segmenter_clause"]
        ids = [r["segment_id"] for r in clause_rows]
        if canonical_ids is None:
            canonical_ids = ids
        sheet_errors = []
        if ids != canonical_ids:
            sheet_errors.append("segment_id_order_differs_from_other_reviewer")
        if len(ids) != expected_review_clause_count:
            sheet_errors.append(
                f"expected_{expected_review_clause_count}_clause_rows_got_{len(ids)}"
            )
        if len(set(ids)) != len(ids):
            sheet_errors.append("duplicate_segment_id")
        if any(row["reviewer_id"] != reviewer for row in rows):
            sheet_errors.append("reviewer_id_mismatch")
        if any(any(row.get(field, "").strip() for field in (
            "reference_label", "risk_type", "uncertainty_note", "rationale",
            "adjudicated_label", "adjudication_note"
        )) for row in rows):
            sheet_errors.append("labels_or_notes_already_present")
        for row in clause_rows:
            doc_id = row["document_id"]
            if doc_id not in expected:
                sheet_errors.append(f"unexpected_document:{doc_id}")
                continue
            text, _ = expected[doc_id]
            start, end = int(row["start_offset"]), int(row["end_offset"])
            if not (0 <= start <= end <= len(text)) or text[start:end] != row["exact_text"]:
                sheet_errors.append(f"offset_text_mismatch:{row['segment_id']}")
        sheets[reviewer] = {
            "row_count_including_added_span_slots": len(rows),
            "clause_row_count": len(clause_rows),
            "reviewer_added_span_slots": sum(r["annotation_type"] == "reviewer_added_span_if_any" for r in rows),
            "sha256": sha256(path),
            "errors": sheet_errors,
        }

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "source extraction and clause segmentation coverage; no model predictions or reviewer labels",
        "review_pack_clause_count": sum(item["clause_count"] for item in document_reports if item["review_pack_member"]),
        "all_available_snapshot_clause_count": sum(item["clause_count"] for item in document_reports),
        "documents": document_reports,
        "reviewer_sheets": sheets,
        "reviewer_sheets_identical_segment_id_order": bool(
            sheets["reviewer_a"]["clause_row_count"] == sheets["reviewer_b"]["clause_row_count"]
            and not sheets["reviewer_a"]["errors"] and not sheets["reviewer_b"]["errors"]
        ),
        "snapshot_registry_document_count": len(sources),
        "snapshot_registry_failed_fetches": [
            {"document_id": row["document_id"], "status": row["review_status"], "error": row["fetch_error"]}
            for row in sources if row["review_status"].startswith("snapshot_fetch_failed")
        ],
        "limitations": [
            "Character coverage counts only text inside emitted clauses; gaps include headings, short fragments, and whitespace.",
            "Parser text changes can invalidate review offsets; regenerate and revalidate both blind sheets before labels are added.",
            "The pack has three terms documents; privacy snapshots in the registry are not included in reviewer sheets.",
            "Coverage is an extraction/segmentation diagnostic and does not establish legal accuracy or reviewer agreement.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if any(not item["binary_sha256_matches_registry"] or not item["text_sha256_matches_registry"] for item in document_reports):
        raise SystemExit("Snapshot hash mismatch")
    if any(value["errors"] for value in sheets.values()):
        raise SystemExit("Review sheet validation failed")


if __name__ == "__main__":
    main()

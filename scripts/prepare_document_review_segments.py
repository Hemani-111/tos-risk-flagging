"""Build blind clause review sheets from the three frozen consumer ToS snapshots."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.clause_segmenter import ClauseSegmenter  # noqa: E402
from app.services.document_parser import TxtParser  # noqa: E402

REGISTRY = ROOT / "data" / "review" / "document_sources_candidates_v1.csv"
OUT = ROOT / "data" / "review" / "snapshots_v1"
SELECTED = {"anthropic_consumer_terms", "mistral_consumer_terms_row", "you_com_terms"}
ANNOTATION_FIELDS = (
    "reference_label", "risk_type", "uncertainty_note", "rationale",
    "adjudicated_label", "adjudication_note",
)
FIELDS = [
    "document_id", "service_name", "document_type", "official_source_url", "retrieved_date",
    "document_version_or_effective_date", "source_sha256", "local_snapshot_path", "text_snapshot_path",
    "reviewer_id", "annotation_type", "segment_id", "section", "start_offset", "end_offset",
    "exact_text", "reference_label", "risk_type", "uncertainty_note", "rationale",
    "adjudicated_label", "adjudication_note",
]


def main() -> None:
    for reviewer in ("reviewer_a", "reviewer_b"):
        existing = OUT / f"{reviewer}_segments_v1.csv"
        if existing.is_file():
            prior = pd.read_csv(existing, dtype=str).fillna("")
            if any(prior[field].str.strip().ne("").any() for field in ANNOTATION_FIELDS):
                raise SystemExit(
                    f"Refusing to overwrite annotations in {existing.name}; preserve the completed review sheet."
                )
    source_rows = pd.read_csv(REGISTRY, dtype=str).fillna("")
    chosen = source_rows.loc[
        source_rows["document_id"].isin(SELECTED)
        & source_rows["review_status"].eq("snapshot_frozen_review_pending")
    ]
    if set(chosen["document_id"]) != SELECTED:
        raise SystemExit("The frozen three-service consumer ToS set is incomplete; fetch snapshots first.")
    segmenter = ClauseSegmenter()
    base_rows: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    for source in chosen.to_dict("records"):
        text_path = ROOT / Path(source["text_snapshot_path"])
        # Match the application's TXT extraction behavior (including BOM handling)
        # so review offsets refer to the exact string the backend segments.
        text = TxtParser().parse(str(text_path))
        clauses = segmenter.segment(text)
        counts[source["document_id"]] = len(clauses)
        for ordinal, clause in enumerate(clauses, start=1):
            if text[clause.start_offset:clause.end_offset] != clause.text:
                raise RuntimeError(f"Offset mismatch in {source['document_id']} {clause.clause_id}")
            base_rows.append({
                "document_id": source["document_id"],
                "service_name": source["service_name"],
                "document_type": source["document_type"],
                "official_source_url": source["official_source_url"],
                "retrieved_date": source["retrieved_date"],
                "document_version_or_effective_date": source["document_version_or_effective_date"],
                "source_sha256": source["snapshot_sha256"],
                "local_snapshot_path": source["local_snapshot_path"],
                "text_snapshot_path": source["text_snapshot_path"],
                "annotation_type": "current_segmenter_clause",
                "segment_id": f"{source['document_id']}::clause_{ordinal:04d}",
                "section": clause.section or "",
                "start_offset": clause.start_offset,
                "end_offset": clause.end_offset,
                "exact_text": clause.text,
                "reference_label": "",
                "risk_type": "",
                "uncertainty_note": "",
                "rationale": "",
            })
        # Leave a row for independently noticed risky material missed by segmentation.
        base_rows.append({
            "document_id": source["document_id"],
            "service_name": source["service_name"],
            "document_type": source["document_type"],
            "official_source_url": source["official_source_url"],
            "retrieved_date": source["retrieved_date"],
            "document_version_or_effective_date": source["document_version_or_effective_date"],
            "source_sha256": source["snapshot_sha256"],
            "local_snapshot_path": source["local_snapshot_path"],
            "text_snapshot_path": source["text_snapshot_path"],
            "annotation_type": "reviewer_added_span_if_any",
        })
    OUT.mkdir(parents=True, exist_ok=True)
    for reviewer in ("reviewer_a", "reviewer_b"):
        path = OUT / f"{reviewer}_segments_v1.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for row in base_rows:
                writer.writerow({**row, "reviewer_id": reviewer})
    print(f"Prepared blind sheets for {counts}; total current-segmenter clauses={sum(counts.values()):,}")
    print("No model predictions are included. Offsets refer to the local .txt snapshot character positions.")


if __name__ == "__main__":
    main()

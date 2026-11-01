"""Create independent annotation-sheet copies for two human reviewers."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "review" / "document_sources_candidates_v1.csv"
OUTPUTS = [
    ROOT / "data" / "review" / "annotator_a_sheet_v1.csv",
    ROOT / "data" / "review" / "annotator_b_sheet_v1.csv",
]
FIELDS = [
    "document_id", "service_name", "document_type", "official_source_url", "retrieved_date",
    "document_version_or_effective_date", "source_sha256", "local_snapshot_path", "text_snapshot_path",
    "reviewer_id", "segment_id", "start_offset", "end_offset", "exact_text", "reference_label",
    "risk_type", "uncertainty_note", "rationale", "adjudicated_label", "adjudication_note",
]


def main() -> None:
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as stream:
        sources = list(csv.DictReader(stream))
    frozen = [r for r in sources if r.get("review_status") == "snapshot_frozen_review_pending"]
    if not frozen:
        raise SystemExit("No frozen snapshots found. Run scripts/fetch_document_source_candidates.py first.")
    for output, reviewer in zip(OUTPUTS, ("reviewer_a", "reviewer_b")):
        with output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for source in frozen:
                writer.writerow({
                    "document_id": source["document_id"],
                    "service_name": source["service_name"],
                    "document_type": source["document_type"],
                    "official_source_url": source["official_source_url"],
                    "retrieved_date": source["retrieved_date"],
                    "document_version_or_effective_date": source["document_version_or_effective_date"],
                    "source_sha256": source["snapshot_sha256"],
                    "local_snapshot_path": source["local_snapshot_path"],
                    "text_snapshot_path": source["text_snapshot_path"],
                    "reviewer_id": reviewer,
                })
        print(f"Wrote {len(frozen)} document stubs to {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Refresh local PDF review text to match the current application parser.

Raw policy PDFs remain unchanged and ignored by Git. This command is intended
only before reviewers enter labels; rerun the blind sheet generator afterward.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/review/document_sources_candidates_v1.csv"
SNAPSHOTS = ROOT / "data/review/snapshots_v1"
ANNOTATION_FIELDS = (
    "reference_label", "risk_type", "uncertainty_note", "rationale",
    "adjudicated_label", "adjudication_note",
)

sys.path.insert(0, str(ROOT / "backend"))
from app.services.document_parser import PdfParser  # noqa: E402


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def refuse_labeled_sheets() -> None:
    for reviewer in ("reviewer_a", "reviewer_b"):
        path = SNAPSHOTS / f"{reviewer}_segments_v1.csv"
        if not path.is_file():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            if any(any((row.get(field) or "").strip() for field in ANNOTATION_FIELDS) for row in csv.DictReader(stream)):
                raise RuntimeError(
                    f"{path.name} contains reviewer annotations; refusing to change source offsets."
                )


def main() -> None:
    refuse_labeled_sheets()
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
        fields = list(rows[0])
    for field in ("text_extraction_engine", "text_extraction_version"):
        if field not in fields:
            fields.append(field)

    parser = PdfParser()
    pypdf_version = importlib.metadata.version("pypdf")
    refreshed = 0
    for row in rows:
        if not row.get("snapshot_path", "").lower().endswith(".pdf"):
            if row.get("review_status", "").startswith("snapshot_frozen"):
                row["text_extraction_engine"] = "stdlib.html.parser (VisibleText)"
                row["text_extraction_version"] = sys.version.split()[0]
            continue
        if not row.get("review_status", "").startswith("snapshot_frozen"):
            continue
        raw_path = ROOT / row["snapshot_path"]
        text_path = ROOT / row["text_snapshot_path"]
        if sha256(raw_path.read_bytes()) != row["snapshot_sha256"]:
            raise RuntimeError(f"Frozen source PDF hash mismatch: {row['document_id']}")
        text = parser.parse(str(raw_path))
        # Preserve exact LF offsets returned by the API parser on Windows.
        with text_path.open("w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        row["text_sha256"] = sha256(text.encode("utf-8"))
        row["text_extraction_engine"] = "pypdf"
        row["text_extraction_version"] = pypdf_version
        refreshed += 1

    temporary = REGISTRY.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(REGISTRY)
    print(f"Refreshed {refreshed} PDF review text extracts with pypdf {pypdf_version}.")
    print("Raw PDFs were unchanged. Regenerate both blind sheets before any human annotations.")


if __name__ == "__main__":
    main()

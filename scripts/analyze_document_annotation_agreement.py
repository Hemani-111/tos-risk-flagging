"""Compare two blind document-review sheets and prepare an adjudication queue.

Input and output CSVs contain source text; keep them under the ignored review folder.
This script reports reviewer agreement only. It never creates reference labels.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("Risky", "Neutral", "Safe")
REVIEW_DIR = ROOT / "data" / "review" / "snapshots_v1"


def read_sheet(path: Path) -> dict[str, dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"{path} is empty")
    required = {"segment_id", "reference_label", "exact_text", "annotation_type"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    keyed: dict[str, dict[str, str]] = {}
    for row in rows:
        # Reviewer-added spans are reported separately because they are not
        # pre-aligned between reviewers and do not have shared segment IDs.
        if row.get("annotation_type") == "reviewer_added_span_if_any":
            continue
        segment_id = row.get("segment_id", "").strip()
        if not segment_id:
            raise ValueError(f"{path} has a current segment without segment_id")
        if segment_id in keyed:
            raise ValueError(f"{path} repeats segment_id {segment_id}")
        label = row.get("reference_label", "").strip()
        if label not in LABELS:
            raise ValueError(
                f"{path}: {segment_id} has label {label!r}; fill every current segment "
                f"with one of {', '.join(LABELS)} before comparing."
            )
        keyed[segment_id] = row
    if not keyed:
        raise ValueError(f"{path} has no aligned current-segmenter rows")
    return keyed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-a", type=Path, default=REVIEW_DIR / "reviewer_a_segments_v1.csv")
    parser.add_argument("--reviewer-b", type=Path, default=REVIEW_DIR / "reviewer_b_segments_v1.csv")
    parser.add_argument("--output-dir", type=Path, default=REVIEW_DIR)
    args = parser.parse_args()

    a = read_sheet(args.reviewer_a)
    b = read_sheet(args.reviewer_b)
    if a.keys() != b.keys():
        only_a, only_b = sorted(a.keys() - b.keys()), sorted(b.keys() - a.keys())
        raise ValueError(
            "Reviewer sheets do not contain the same pre-segmented rows. "
            f"Only A: {only_a[:5]}; only B: {only_b[:5]}"
        )

    ids = sorted(a)
    labels_a = [a[key]["reference_label"].strip() for key in ids]
    labels_b = [b[key]["reference_label"].strip() for key in ids]
    agreements = sum(x == y for x, y in zip(labels_a, labels_b))
    counts = Counter(labels_a)
    counts_b = Counter(labels_b)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    disagreement_path = args.output_dir / "document_adjudication_queue_v1.csv"
    fields = ["segment_id", "document_id", "service_name", "section", "start_offset", "end_offset",
              "exact_text", "reviewer_a_label", "reviewer_b_label", "adjudicated_label", "adjudication_note"]
    with disagreement_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for segment_id, label_a, label_b in zip(ids, labels_a, labels_b):
            if label_a == label_b:
                continue
            row = a[segment_id]
            writer.writerow({
                "segment_id": segment_id,
                "document_id": row.get("document_id", ""),
                "service_name": row.get("service_name", ""),
                "section": row.get("section", ""),
                "start_offset": row.get("start_offset", ""),
                "end_offset": row.get("end_offset", ""),
                "exact_text": row.get("exact_text", ""),
                "reviewer_a_label": label_a,
                "reviewer_b_label": label_b,
                "adjudicated_label": "",
                "adjudication_note": "",
            })

    summary = {
        "n_aligned_presegmented_clauses": len(ids),
        "raw_agreement_count": agreements,
        "raw_agreement": agreements / len(ids),
        "cohen_kappa": float(cohen_kappa_score(labels_a, labels_b, labels=LABELS)),
        "label_order": list(LABELS),
        "reviewer_a_label_counts": {label: counts.get(label, 0) for label in LABELS},
        "reviewer_b_label_counts": {label: counts_b.get(label, 0) for label in LABELS},
        "disagreement_count": len(ids) - agreements,
        "disagreement_queue": disagreement_path.name,
        "interpretation": "Agreement is descriptive for this reviewed sample, not proof of expert legal correctness.",
    }
    report_path = args.output_dir / "document_annotation_agreement_v1.json"
    report_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Adjudication queue: {disagreement_path}")
    print(f"Agreement report: {report_path}")


if __name__ == "__main__":
    main()

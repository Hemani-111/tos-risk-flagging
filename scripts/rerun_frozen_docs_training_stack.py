#!/usr/bin/env python3
"""Rerun the seven frozen document inputs through the training-stack API
(Python 3.11, scikit-learn 1.9.0, numpy 2.4.6, joblib 1.4.2) and compare
against real_document_eval_v2 results.

Usage:
    .venv-training-stack/bin/python scripts/rerun_frozen_docs_training_stack.py
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "review" / "real_document_eval_v2"
CLEAN_DIR = EVAL_DIR / "cleaned"
V2_API_DIR = EVAL_DIR / "api_outputs"
RUN_ID = f"rerun_training_stack_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
OUT_DIR = EVAL_DIR / "aggregate" / f"rerun_{RUN_ID}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "http://127.0.0.1:8001/api/v1"

# Seven documents that had successful API runs in v2
DOCUMENTS = [
    "discord_tos",
    "discord_privacy",
    "spotify_tos_in",
    "spotify_privacy",
    "reddit_user_agreement",
    "github_tos",
    "github_privacy",
]


def load_v2_output(doc_id: str) -> dict:
    path = V2_API_DIR / f"{doc_id}.json"
    wrapped = json.loads(path.read_text(encoding="utf-8"))
    # v2 outputs nest the actual API response under "api_first"
    return wrapped.get("api_first", wrapped)


def analyze_text(text: str, filename: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/documents/analyze-text",
        json={"text": text, "filename": filename},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def compare_clauses(v2: dict, new: dict, doc_id: str) -> list[dict]:
    """Compare clause-by-clause between v2 and new run. Returns list of discrepancies."""
    discrepancies = []
    v2_clauses = {c["id"]: c for c in v2.get("clauses", [])}
    new_clauses = {c["id"]: c for c in new.get("clauses", [])}

    v2_ids = set(v2_clauses.keys())
    new_ids = set(new_clauses.keys())

    # Missing / extra clause IDs
    for cid in sorted(v2_ids - new_ids):
        discrepancies.append({
            "document_id": doc_id,
            "clause_id": cid,
            "type": "missing_in_rerun",
            "v2_text": v2_clauses[cid].get("text"),
            "v2_label": v2_clauses[cid].get("label"),
            "v2_startOffset": v2_clauses[cid].get("startOffset"),
            "v2_endOffset": v2_clauses[cid].get("endOffset"),
        })
    for cid in sorted(new_ids - v2_ids):
        discrepancies.append({
            "document_id": doc_id,
            "clause_id": cid,
            "type": "extra_in_rerun",
            "new_text": new_clauses[cid].get("text"),
            "new_label": new_clauses[cid].get("label"),
            "new_startOffset": new_clauses[cid].get("startOffset"),
            "new_endOffset": new_clauses[cid].get("endOffset"),
        })

    # Common clause IDs: compare text, label, offsets
    for cid in sorted(v2_ids & new_ids):
        v2c = v2_clauses[cid]
        newc = new_clauses[cid]
        diff = {}
        if v2c.get("text") != newc.get("text"):
            diff["text"] = {"v2": v2c.get("text"), "new": newc.get("text")}
        if v2c.get("label") != newc.get("label"):
            diff["label"] = {"v2": v2c.get("label"), "new": newc.get("label")}
        if v2c.get("startOffset") != newc.get("startOffset"):
            diff["startOffset"] = {"v2": v2c.get("startOffset"), "new": newc.get("startOffset")}
        if v2c.get("endOffset") != newc.get("endOffset"):
            diff["endOffset"] = {"v2": v2c.get("endOffset"), "new": newc.get("endOffset")}
        if v2c.get("section") != newc.get("section"):
            diff["section"] = {"v2": v2c.get("section"), "new": newc.get("section")}
        if diff:
            discrepancies.append({
                "document_id": doc_id,
                "clause_id": cid,
                "type": "field_mismatch",
                "differences": diff,
            })

    return discrepancies


def main():
    print(f"Run ID: {RUN_ID}")
    print(f"Output dir: {OUT_DIR}")
    print(f"API base: {API_BASE}")
    print()

    # Verify health
    health = requests.get(f"{API_BASE}/health", timeout=10)
    print(f"Health: {health.json()}")
    print()

    all_discrepancies = []
    run_results = []

    for doc_id in DOCUMENTS:
        print(f"=== {doc_id} ===")
        clean_path = CLEAN_DIR / f"{doc_id}.txt"
        text = clean_path.read_text(encoding="utf-8")
        filename = f"{doc_id}.txt"

        # Run through training-stack API
        new_result = analyze_text(text, filename)
        new_result["_run_id"] = RUN_ID
        new_result["_document_id"] = doc_id

        # Save individual response
        out_path = OUT_DIR / f"{doc_id}.json"
        out_path.write_text(json.dumps(new_result, indent=2, ensure_ascii=False), encoding="utf-8")

        # Load v2 result
        v2_result = load_v2_output(doc_id)

        # Compare summary counts
        v2_counts = {
            "totalClauses": v2_result["totalClauses"],
            "riskyCount": v2_result["riskyCount"],
            "neutralCount": v2_result["neutralCount"],
            "safeCount": v2_result["safeCount"],
        }
        new_counts = {
            "totalClauses": new_result["totalClauses"],
            "riskyCount": new_result["riskyCount"],
            "neutralCount": new_result["neutralCount"],
            "safeCount": new_result["safeCount"],
        }

        print(f"  v2 counts:      {v2_counts}")
        print(f"  rerun counts:   {new_counts}")

        count_match = v2_counts == new_counts
        print(f"  counts match:   {count_match}")

        # Compare clauses
        discrepancies = compare_clauses(v2_result, new_result, doc_id)
        print(f"  discrepancies:  {len(discrepancies)}")
        for d in discrepancies[:5]:
            print(f"    - {d['clause_id']}: {d['type']}")
            if d["type"] == "field_mismatch":
                for field, vals in d["differences"].items():
                    print(f"        {field}: v2={vals['v2']!r} new={vals['new']!r}")
        if len(discrepancies) > 5:
            print(f"    ... and {len(discrepancies) - 5} more")

        all_discrepancies.extend(discrepancies)

        run_results.append({
            "document_id": doc_id,
            "run_id": RUN_ID,
            "v2_counts": v2_counts,
            "new_counts": new_counts,
            "counts_match": count_match,
            "discrepancy_count": len(discrepancies),
            "discrepancies": discrepancies,
        })

    # Save comparison report
    report = {
        "run_id": RUN_ID,
        "api_base": API_BASE,
        "training_stack": {
            "python": "3.11",
            "scikit_learn": "1.9.0",
            "numpy": "2.4.6",
            "joblib": "1.4.2",
        },
        "compared_at_utc": datetime.now(timezone.utc).isoformat(),
        "documents": run_results,
        "total_discrepancies": len(all_discrepancies),
        "all_discrepancies": all_discrepancies,
    }
    report_path = OUT_DIR / "comparison_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"=== SUMMARY ===")
    print(f"Run ID: {RUN_ID}")
    print(f"Total discrepancies: {len(all_discrepancies)}")
    print(f"Report saved: {report_path}")
    for r in run_results:
        status = "MATCH" if r["counts_match"] and r["discrepancy_count"] == 0 else "DIFFERS"
        print(f"  {r['document_id']}: {status} (counts_match={r['counts_match']}, discrepancies={r['discrepancy_count']})")


if __name__ == "__main__":
    main()

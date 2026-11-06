#!/usr/bin/env python3
"""Inspect all unclassified Spotify Privacy spans.

Reconciles total gap characters with reported coverage (4,311 = 10% of 43,114).
Separates whitespace/navigation from meaningful policy content.
Does NOT classify data-category lists as irrelevant solely because they are lists.
Preserves gap excerpts and inspection findings locally.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "review" / "real_document_eval_v2"
CLEAN_PATH = EVAL_DIR / "cleaned" / "spotify_privacy.txt"
API_OUTPUT_PATH = EVAL_DIR / "api_outputs" / "spotify_privacy.json"
OUT_DIR = EVAL_DIR / "aggregate" / "spotify_gap_inspection"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_CHARS = 43114
REPORTED_UNCLASSIFIED = 4311
REPORTED_PCT = 10.00


def load_cleaned_text() -> str:
    return CLEAN_PATH.read_text(encoding="utf-8")


def load_clause_offsets() -> list[dict]:
    wrapped = json.loads(API_OUTPUT_PATH.read_text(encoding="utf-8"))
    api_resp = wrapped.get("api_first", wrapped)
    return api_resp.get("clauses", [])


def find_gaps(text: str, clauses: list[dict]) -> list[dict]:
    """Find text spans not covered by any clause offset."""
    # Sort clauses by start offset
    sorted_clauses = sorted(clauses, key=lambda c: c["startOffset"])

    gaps = []
    prev_end = 0

    for clause in sorted_clauses:
        start = clause["startOffset"]
        end = clause["endOffset"]

        if start > prev_end:
            gap_text = text[prev_end:start]
            gaps.append({
                "start": prev_end,
                "end": start,
                "length": start - prev_end,
                "text": gap_text,
                "preceding_clause_end": prev_end,
                "following_clause_start": start,
                "following_clause_id": clause.get("id"),
                "following_clause_text_preview": clause.get("text", "")[:80],
            })

        prev_end = max(prev_end, end)

    # Trailing gap
    if prev_end < len(text):
        gap_text = text[prev_end:]
        gaps.append({
            "start": prev_end,
            "end": len(text),
            "length": len(text) - prev_end,
            "text": gap_text,
            "preceding_clause_end": prev_end,
            "following_clause_start": None,
            "following_clause_id": None,
            "following_clause_text_preview": None,
        })

    return gaps


def categorize_gap(gap: dict) -> str:
    """Categorize a gap into: whitespace, navigation/TOC, table_header, data_category_list, meaningful_content, mixed."""
    text = gap["text"].strip()

    if not text:
        return "whitespace"

    # Check if it's mostly whitespace/newlines
    if len(text.strip()) == 0:
        return "whitespace"

    # Check for TOC patterns (numbered sections like "1. About this Policy … 12. How to contact us")
    if re.search(r"\d+\.\s+.*\.\s*\d+", text) or re.search(r"\d+\.\s+.*\s+\d+\s*$", text):
        if "About this Policy" in text or "How to contact us" in text:
            return "navigation_toc"

    # Check for table headers
    if "Categories of data" in text or "Reason for sharing" in text or "Service providers" in text:
        return "table_header"

    # Check for data-category lists (substantive policy content formatted as lists)
    data_category_keywords = [
        "Personal Data", "Contact Data", "Identity Data", "Technical Data",
        "Usage Data", "Voice Data", "Message Data", "Street Address Data",
        "Payment Data", "Location Data", "Device Data", "Cookie Data",
    ]
    keyword_count = sum(1 for kw in data_category_keywords if kw in text)
    if keyword_count >= 2:
        return "data_category_list"

    # Check for short structural lines (headings, nav remnants)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) <= 3 and all(len(l) < 80 for l in lines):
        # Could be heading or nav - check for nav-like content
        nav_keywords = ["Skip to", "footer", "header", "nav", "menu", "cookie", "consent"]
        if any(kw.lower() in text.lower() for kw in nav_keywords):
            return "navigation_remnant"
        return "structural_heading"

    # Default: meaningful content
    return "meaningful_content"


def main():
    text = load_cleaned_text()
    clauses = load_clause_offsets()

    print(f"Total cleaned text chars: {len(text)}")
    print(f"Total clauses: {len(clauses)}")
    print(f"Reported unclassified: {REPORTED_UNCLASSIFIED} ({REPORTED_PCT}%)")
    print()

    gaps = find_gaps(text, clauses)
    total_gap_chars = sum(g["length"] for g in gaps)
    print(f"Total gaps found: {len(gaps)}")
    print(f"Total gap characters: {total_gap_chars}")
    print(f"Gap percentage: {total_gap_chars / len(text) * 100:.2f}%")
    print(f"Reconciliation with reported {REPORTED_UNCLASSIFIED}: {'MATCH' if total_gap_chars == REPORTED_UNCLASSIFIED else 'MISMATCH'}")
    print()

    # Categorize gaps
    categories = {}
    for gap in gaps:
        cat = categorize_gap(gap)
        gap["category"] = cat
        categories.setdefault(cat, []).append(gap)

    print("=== GAP CATEGORIES ===")
    for cat, cat_gaps in sorted(categories.items()):
        cat_chars = sum(g["length"] for g in cat_gaps)
        print(f"\n{cat}: {len(cat_gaps)} gaps, {cat_chars} chars ({cat_chars/len(text)*100:.2f}% of total)")
        for g in cat_gaps[:3]:  # Show first 3 examples
            preview = repr(g["text"][:120])
            print(f"  [{g['start']}-{g['end']}] {g['length']} chars: {preview}")
        if len(cat_gaps) > 3:
            print(f"  ... and {len(cat_gaps) - 3} more")

    # Identify meaningful content gaps (not whitespace/nav/table headers)
    meaningful = categories.get("meaningful_content", []) + categories.get("data_category_list", [])
    print(f"\n=== MEANINGFUL CONTENT GAPS ===")
    print(f"Count: {len(meaningful)}")
    print(f"Total chars: {sum(g['length'] for g in meaningful)}")
    for g in meaningful:
        print(f"\n[{g['start']}-{g['end']}] {g['length']} chars, category={g['category']}")
        print(f"  Text: {repr(g['text'][:300])}")
        if g["following_clause_id"]:
            print(f"  Next clause: {g['following_clause_id']} - {repr(g['following_clause_text_preview'])}")

    # Save findings
    findings = {
        "inspection_id": f"spotify_gap_inspection_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "document_id": "spotify_privacy",
        "total_text_chars": len(text),
        "total_clauses": len(clauses),
        "reported_unclassified_chars": REPORTED_UNCLASSIFIED,
        "reported_unclassified_pct": REPORTED_PCT,
        "actual_gap_count": len(gaps),
        "actual_gap_chars": total_gap_chars,
        "actual_gap_pct": total_gap_chars / len(text) * 100,
        "reconciliation": total_gap_chars == REPORTED_UNCLASSIFIED,
        "categories": {
            cat: {
                "count": len(cat_gaps),
                "chars": sum(g["length"] for g in cat_gaps),
                "gaps": [
                    {
                        "start": g["start"],
                        "end": g["end"],
                        "length": g["length"],
                        "text": g["text"],
                        "following_clause_id": g.get("following_clause_id"),
                        "following_clause_text_preview": g.get("following_clause_text_preview"),
                    }
                    for g in cat_gaps
                ],
            }
            for cat, cat_gaps in categories.items()
        },
        "meaningful_content_gaps": [
            {
                "start": g["start"],
                "end": g["end"],
                "length": g["length"],
                "category": g["category"],
                "text": g["text"],
                "following_clause_id": g.get("following_clause_id"),
            }
            for g in meaningful
        ],
        "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    findings_path = OUT_DIR / "spotify_privacy_gap_findings.json"
    findings_path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFindings saved: {findings_path}")


if __name__ == "__main__":
    main()

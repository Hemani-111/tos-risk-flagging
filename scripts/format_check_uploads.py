#!/usr/bin/env python3
"""PDF/DOCX/TXT format checks through the real upload API.

Uses identical frozen content (spotify_tos_in cleaned text) converted to
PDF, DOCX, and TXT. Uploads each through POST /api/v1/documents/analyze on
the training-stack backend (port 8001). Compares extraction, segmentation,
and predictions across formats.

Generated conversions are labeled "format conversion from frozen snapshot" —
they are NOT official source PDFs/DOCXs.

Usage:
    .venv-training-stack/bin/python scripts/format_check_uploads.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "review" / "real_document_eval_v2"
CLEAN_DIR = EVAL_DIR / "cleaned"
OUT_DIR = EVAL_DIR / "api_outputs" / "format_check"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_BASE = "http://127.0.0.1:8001/api/v1"
DOC_ID = "spotify_tos_in"  # representative cleaned policy text
RUN_ID = f"format_check_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def read_cleaned_text(doc_id: str) -> str:
    path = CLEAN_DIR / f"{doc_id}.txt"
    return path.read_text(encoding="utf-8")


def make_txt(text: str) -> bytes:
    return text.encode("utf-8")


def make_docx(text: str) -> bytes:
    doc = Document()
    # Split into paragraphs on double newlines to preserve structure
    for para in text.split("\n\n"):
        if para.strip():
            doc.add_paragraph(para)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def make_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    for para in text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para, styles["Normal"]))
            story.append(Spacer(1, 6))
    doc.build(story)
    return buf.getvalue()


def upload_file(filename: str, content: bytes, content_type: str) -> dict:
    files = {"file": (filename, content, content_type)}
    resp = requests.post(
        f"{API_BASE}/documents/analyze",
        files=files,
        timeout=120,
    )
    if resp.status_code >= 400:
        return {
            "error": True,
            "status_code": resp.status_code,
            "detail": resp.text,
        }
    return resp.json()


def main():
    print(f"Run ID: {RUN_ID}")
    print(f"API base: {API_BASE}")
    print(f"Source document: {DOC_ID} (format conversion from frozen snapshot)")
    print()

    text = read_cleaned_text(DOC_ID)
    print(f"Source text length: {len(text)} characters")
    print()

    formats = [
        ("txt", f"{DOC_ID}_format_conversion.txt", make_txt(text), "text/plain"),
        ("docx", f"{DOC_ID}_format_conversion.docx", make_docx(text), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("pdf", f"{DOC_ID}_format_conversion.pdf", make_pdf(text), "application/pdf"),
    ]

    results = {}

    for fmt, filename, content, content_type in formats:
        print(f"=== {fmt.upper()} ===")
        print(f"  File: {filename} ({len(content)} bytes)")
        result = upload_file(filename, content, content_type)
        result["_format"] = fmt
        result["_filename"] = filename
        result["_run_id"] = RUN_ID
        results[fmt] = result

        # Save individual response
        out_path = OUT_DIR / f"{DOC_ID}_{fmt}.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

        if result.get("error"):
            print(f"  ERROR: status={result['status_code']} detail={result['detail'][:200]}")
        else:
            print(f"  totalClauses: {result.get('totalClauses')}")
            print(f"  risky: {result.get('riskyCount')}, neutral: {result.get('neutralCount')}, safe: {result.get('safeCount')}")
            print(f"  extractedText length: {len(result.get('extractedText', ''))}")
            print(f"  modelVersion: {result.get('modelVersion')}")
            print(f"  warnings: {result.get('warnings')}")
        print()

    # Compare TXT (baseline) against PDF and DOCX
    print("=== COMPARISON ===")
    txt_result = results.get("txt", {})
    for fmt in ["pdf", "docx"]:
        fmt_result = results.get(fmt, {})
        if txt_result.get("error") or fmt_result.get("error"):
            print(f"{fmt}: cannot compare (error in one or both)")
            continue

        txt_clauses = {c["id"]: c for c in txt_result.get("clauses", [])}
        fmt_clauses = {c["id"]: c for c in fmt_result.get("clauses", [])}

        txt_count = txt_result.get("totalClauses", 0)
        fmt_count = fmt_result.get("totalClauses", 0)
        txt_text_len = len(txt_result.get("extractedText", ""))
        fmt_text_len = len(fmt_result.get("extractedText", ""))

        print(f"\n{fmt.upper()} vs TXT:")
        print(f"  Clause count: TXT={txt_count}, {fmt.upper()}={fmt_count}, match={txt_count == fmt_count}")
        print(f"  Extracted text length: TXT={txt_text_len}, {fmt.upper()}={fmt_text_len}, ratio={fmt_text_len/txt_text_len:.3f}" if txt_text_len else f"  Extracted text length: TXT={txt_text_len}, {fmt.upper()}={fmt_text_len}")

        # Clause ID comparison
        txt_ids = set(txt_clauses.keys())
        fmt_ids = set(fmt_clauses.keys())
        missing = txt_ids - fmt_ids
        extra = fmt_ids - txt_ids
        if missing:
            print(f"  Clause IDs missing in {fmt.upper()}: {len(missing)} (e.g., {sorted(missing)[:5]})")
        if extra:
            print(f"  Clause IDs extra in {fmt.upper()}: {len(extra)} (e.g., {sorted(extra)[:5]})")

        # Label comparison for common IDs
        common = txt_ids & fmt_ids
        label_diffs = 0
        text_diffs = 0
        offset_diffs = 0
        for cid in sorted(common):
            tc = txt_clauses[cid]
            fc = fmt_clauses[cid]
            if tc.get("label") != fc.get("label"):
                label_diffs += 1
            if tc.get("text") != fc.get("text"):
                text_diffs += 1
            if tc.get("startOffset") != fc.get("startOffset") or tc.get("endOffset") != fc.get("endOffset"):
                offset_diffs += 1
        print(f"  Common clauses: {len(common)}")
        print(f"  Label differences: {label_diffs}")
        print(f"  Text differences: {text_diffs}")
        print(f"  Offset differences: {offset_diffs}")

    # Save comparison summary
    summary = {
        "run_id": RUN_ID,
        "source_document": DOC_ID,
        "source_note": "format conversion from frozen snapshot — not an official source document",
        "source_text_chars": len(text),
        "api_base": API_BASE,
        "results": results,
        "compared_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = OUT_DIR / "format_check_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary saved: {summary_path}")


if __name__ == "__main__":
    main()

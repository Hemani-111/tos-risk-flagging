#!/usr/bin/env python3
"""PDF vs TXT extracted text alignment analysis.

Compares TXT and PDF extracted text from format_check outputs using explicit
text alignment. Classifies differences as: unchanged, merged, split, altered,
or missing. Tests the page-separator hypothesis directly.

Usage:
    .venv-training-stack/bin/python scripts/pdf_txt_alignment_analysis.py
"""
from __future__ import annotations

import difflib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "data" / "review" / "real_document_eval_v2"
FORMAT_DIR = EVAL_DIR / "api_outputs" / "format_check"
OUT_DIR = EVAL_DIR / "aggregate" / "pdf_txt_alignment"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_extracted_text(fmt: str) -> str:
    path = FORMAT_DIR / f"spotify_tos_in_{fmt}.json"
    wrapped = json.loads(path.read_text(encoding="utf-8"))
    return wrapped.get("extractedText", ""), wrapped.get("clauses", [])


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs to single spaces, strip leading/trailing."""
    return re.sub(r"\s+", " ", text).strip()


def classify_difference(t_segment: str, p_segment: str) -> str:
    """Classify a difference between TXT and PDF segments."""
    t_norm = normalize_whitespace(t_segment)
    p_norm = normalize_whitespace(p_segment)

    if t_norm == p_norm:
        return "unchanged"

    # Check if it's purely whitespace difference
    t_stripped = t_segment.strip()
    p_stripped = p_segment.strip()
    if t_stripped == p_stripped:
        return "whitespace_only"

    # Check if PDF segment is a subset (deletion in PDF)
    if p_norm in t_norm:
        return "deletion_in_pdf"

    # Check if TXT segment is a subset (insertion in PDF)
    if t_norm in p_norm:
        return "insertion_in_pdf"

    # Check for word break / line wrap differences
    t_words = t_norm.split()
    p_words = p_norm.split()
    if t_words == p_words:
        return "word_break_only"

    return "altered"


def main():
    txt_text, txt_clauses = load_extracted_text("txt")
    pdf_text, pdf_clauses = load_extracted_text("pdf")

    print(f"TXT extracted text length: {len(txt_text)}")
    print(f"PDF extracted text length: {len(pdf_text)}")
    print(f"Length difference: {len(txt_text) - len(pdf_text)}")
    print(f"TXT clauses: {len(txt_clauses)}")
    print(f"PDF clauses: {len(pdf_clauses)}")
    print()

    # === Test 1: Page-separator hypothesis ===
    # Count \n\n occurrences in each
    txt_double_newlines = txt_text.count("\n\n")
    pdf_double_newlines = pdf_text.count("\n\n")
    print("=== PAGE-SEPARATOR HYPOTHESIS TEST ===")
    print(f"TXT \\n\\n count: {txt_double_newlines}")
    print(f"PDF \\n\\n count: {pdf_double_newlines}")
    print(f"Difference: {txt_double_newlines - pdf_double_newlines}")
    print()

    # Count single newlines
    txt_single_nl = txt_text.count("\n")
    pdf_single_nl = pdf_text.count("\n")
    print(f"TXT total \\n count: {txt_single_nl}")
    print(f"PDF total \\n count: {pdf_single_nl}")
    print()

    # === Test 2: Character-level diff using difflib ===
    print("=== CHARACTER-LEVEL DIFF (difflib) ===")
    sm = difflib.SequenceMatcher(None, txt_text, pdf_text, autojunk=False)

    diff_categories = {
        "unchanged": 0,
        "whitespace_only": 0,
        "word_break_only": 0,
        "deletion_in_pdf": 0,
        "insertion_in_pdf": 0,
        "altered": 0,
    }

    diff_details = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        t_segment = txt_text[i1:i2]
        p_segment = pdf_text[j1:j2]

        if tag == "equal":
            diff_categories["unchanged"] += 1
            continue

        category = classify_difference(t_segment, p_segment)
        diff_categories[category] += 1

        diff_details.append({
            "tag": tag,
            "txt_start": i1,
            "txt_end": i2,
            "pdf_start": j1,
            "pdf_end": j2,
            "txt_segment": t_segment[:200],
            "pdf_segment": p_segment[:200],
            "category": category,
        })

    print("Diff opcode categories:")
    for cat, count in sorted(diff_categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # === Test 3: Whitespace-normalized comparison ===
    print("\n=== WHITESPACE-NORMALIZED COMPARISON ===")
    txt_norm = normalize_whitespace(txt_text)
    pdf_norm = normalize_whitespace(pdf_text)
    print(f"TXT normalized length: {len(txt_norm)}")
    print(f"PDF normalized length: {len(pdf_norm)}")
    print(f"Normalized length difference: {len(txt_norm) - len(pdf_norm)}")

    sm_norm = difflib.SequenceMatcher(None, txt_norm, pdf_norm, autojunk=False)
    norm_diff_categories = {}
    for tag, i1, i2, j1, j2 in sm_norm.get_opcodes():
        norm_diff_categories[tag] = norm_diff_categories.get(tag, 0) + 1
    print(f"Normalized diff opcodes: {norm_diff_categories}")

    # === Test 4: Check for spaces before punctuation in PDF ===
    print("\n=== SPACES BEFORE PUNCTUATION (PDF-specific) ===")
    pdf_space_before_punct = re.findall(r"\s+[.,;:)]", pdf_text)
    print(f"PDF segments with space before punctuation: {len(pdf_space_before_punct)}")
    for m in pdf_space_before_punct[:10]:
        print(f"  {repr(m)}")

    txt_space_before_punct = re.findall(r"\s+[.,;:)]", txt_text)
    print(f"TXT segments with space before punctuation: {len(txt_space_before_punct)}")

    # === Test 5: Extra spaces around quoted terms in PDF ===
    print("\n=== EXTRA SPACES AROUND QUOTED TERMS ===")
    pdf_quoted_with_spaces = re.findall(r'"\s+\w', pdf_text)
    print(f"PDF quoted terms with leading space inside quotes: {len(pdf_quoted_with_spaces)}")
    for m in pdf_quoted_with_spaces[:10]:
        print(f"  {repr(m)}")

    # === Test 6: Clause alignment by content ===
    print("\n=== CLAUSE ALIGNMENT BY CONTENT ===")
    # Build normalized text -> clause mapping for TXT
    txt_clause_map = {}
    for c in txt_clauses:
        norm = normalize_whitespace(c["text"])
        if norm not in txt_clause_map:
            txt_clause_map[norm] = []
        txt_clause_map[norm].append(c)

    pdf_clause_map = {}
    for c in pdf_clauses:
        norm = normalize_whitespace(c["text"])
        if norm not in pdf_clause_map:
            pdf_clause_map[norm] = []
        pdf_clause_map[norm].append(c)

    txt_norms = set(txt_clause_map.keys())
    pdf_norms = set(pdf_clause_map.keys())

    matched = txt_norms & pdf_norms
    txt_only = txt_norms - pdf_norms
    pdf_only = pdf_norms - txt_norms

    print(f"TXT unique normalized clause texts: {len(txt_norms)}")
    print(f"PDF unique normalized clause texts: {len(pdf_norms)}")
    print(f"Matched (same normalized text): {len(matched)}")
    print(f"TXT-only clauses: {len(txt_only)}")
    print(f"PDF-only clauses: {len(pdf_only)}")

    # Label disagreements for matched clauses
    label_disagreements = 0
    for norm in sorted(matched):
        txt_c = txt_clause_map[norm][0]
        pdf_c = pdf_clause_map[norm][0]
        if txt_c["label"] != pdf_c["label"]:
            label_disagreements += 1
            print(f"  LABEL DISAGREEMENT: '{norm[:80]}...' TXT={txt_c['label']} PDF={pdf_c['label']}")

    print(f"\nLabel disagreements among matched clauses: {label_disagreements}")

    # === Test 7: Classify TXT-only and PDF-only clauses ===
    print("\n=== TXT-ONLY CLAUSES (by normalized text) ===")
    for norm in sorted(txt_only)[:20]:
        c = txt_clause_map[norm][0]
        print(f"  {c['id']}: label={c['label']} text={repr(norm[:100])}")

    print("\n=== PDF-ONLY CLAUSES (by normalized text) ===")
    for norm in sorted(pdf_only)[:20]:
        c = pdf_clause_map[norm][0]
        print(f"  {c['id']}: label={c['label']} text={repr(norm[:100])}")

    # === Save detailed findings ===
    findings = {
        "analysis_id": f"pdf_txt_alignment_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "source_document": "spotify_tos_in",
        "txt_text_length": len(txt_text),
        "pdf_text_length": len(pdf_text),
        "length_difference": len(txt_text) - len(pdf_text),
        "txt_clauses": len(txt_clauses),
        "pdf_clauses": len(pdf_clauses),
        "page_separator_test": {
            "txt_double_newlines": txt_double_newlines,
            "pdf_double_newlines": pdf_double_newlines,
            "double_newline_difference": txt_double_newlines - pdf_double_newlines,
            "txt_total_newlines": txt_single_nl,
            "pdf_total_newlines": pdf_single_nl,
        },
        "whitespace_normalized": {
            "txt_normalized_length": len(txt_norm),
            "pdf_normalized_length": len(pdf_norm),
            "normalized_length_difference": len(txt_norm) - len(pdf_norm),
        },
        "diff_opcode_categories": diff_categories,
        "diff_details": diff_details[:50],  # Limit for size
        "clause_alignment": {
            "txt_unique_normalized": len(txt_norms),
            "pdf_unique_normalized": len(pdf_norms),
            "matched": len(matched),
            "txt_only": len(txt_only),
            "pdf_only": len(pdf_only),
            "label_disagreements_matched": label_disagreements,
        },
        "pdf_specific_issues": {
            "space_before_punctuation_count": len(pdf_space_before_punct),
            "space_before_punctuation_examples": [repr(m) for m in pdf_space_before_punct[:10]],
            "quoted_terms_with_leading_space_count": len(pdf_quoted_with_spaces),
            "quoted_terms_with_leading_space_examples": [repr(m) for m in pdf_quoted_with_spaces[:10]],
        },
        "analyzed_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    findings_path = OUT_DIR / "pdf_txt_alignment_findings.json"
    findings_path.write_text(json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFindings saved: {findings_path}")


if __name__ == "__main__":
    main()

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts"))
from compare_pdf_extraction import clause_alignment, diff_summary, normalize_for_comparison
from app.services.clause_segmenter import Clause


def c(text, index):
    return Clause(f"c{index}", text, None, 0, len(text))


def test_comparison_normalization_is_diagnostic_and_preserves_unicode():
    assert normalize_for_comparison(" café\r\n\r\n  data  ") == "café\n\ndata"


def test_diff_reports_whitespace_and_text_edits():
    result = diff_summary("A clause.\nNext.", "A clause. Next!")
    assert result["similarity_ratio"] < 1
    assert result["excerpts"]


def test_clause_alignment_detects_exact_duplicates_and_split_merge():
    pdf = [c("We may collect account data.", 1), c("We may share usage data.", 2)]
    baseline = [c("We may collect account data. We may share usage data.", 1)]
    result = clause_alignment(pdf, baseline)
    assert result["possible_splits_or_merges"]
    assert result["unmatched_pdf"] == [0, 1]
    assert result["unmatched_baseline"] == [0]


def test_duplicate_exact_clauses_are_explicitly_flagged():
    pdf = [c("We may retain account records.", 1), c("We may retain account records.", 2)]
    baseline = [c("We may retain account records.", 3), c("We may retain account records.", 4)]
    result = clause_alignment(pdf, baseline)
    assert len(result["matches"]) == 2
    assert result["duplicate_notes"]

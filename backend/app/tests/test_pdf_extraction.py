from app.services.document_parser import _page_separator, _repeated_margin_lines
from app.services.clause_segmenter import ClauseSegmenter


def test_page_boundary_sentence_continuation_uses_single_newline():
    assert _page_separator("We may collect personal information", "to provide the service.") == "\n"


def test_page_boundary_completed_paragraph_uses_blank_line():
    assert _page_separator("We may collect personal information.", "We may share it with providers.") == "\n\n"


def test_page_boundary_does_not_remove_real_hyphen():
    assert _page_separator("The service is inter-", "national in scope.") == "\n"


def test_repeated_margin_detection_is_conservative():
    pages = [
        (i, f"TERMS OF SERVICE\n\nBody content page {i}\n\nPage {i}", False, False)
        for i in range(1, 6)
    ]
    found = _repeated_margin_lines(pages)
    assert "terms of service" in found
    assert "body content page 1" not in found


def test_clause_offsets_match_exact_source_with_unicode_lists_and_paragraphs():
    text = (
        "DATA WE COLLECT\n\n"
        "1. Account information – name, email, and address.\n"
        "2. Device information — identifiers and usage.\n\n"
        "• We retain records for legal purposes.\n"
        "The policy also covers café and naïve-user data."
    )
    clauses = ClauseSegmenter().segment(text)
    assert clauses
    for clause in clauses:
        assert text[clause.start_offset:clause.end_offset] == clause.text
    assert "café" in text
    assert "naïve" in text


def test_wrapped_line_and_sentence_continuation_keep_offsets():
    text = "We may collect data for the service\nand use it to improve reliability. You may opt out."
    clauses = ClauseSegmenter().segment(text)
    assert clauses
    assert all(text[c.start_offset:c.end_offset] == c.text for c in clauses)


def test_genuine_hyphenated_word_is_not_rewritten():
    text = "We provide end-to-end encryption for account information."
    clauses = ClauseSegmenter().segment(text)
    assert clauses[0].text == text

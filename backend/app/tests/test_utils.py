import pytest
import os
import tempfile


class TestTextUtils:
    def test_normalize_whitespace(self):
        from app.utils.text import normalize_whitespace
        text = "Hello   world\n\n\n\nFoo"
        result = normalize_whitespace(text)
        assert "   " not in result
        assert "\n\n\n" not in result
    
    def test_truncate(self):
        from app.utils.text import truncate
        text = "This is a long text that should be truncated"
        result = truncate(text, 20)
        assert len(result) <= 23  # 20 + "..."
        assert result.endswith("...")
    
    def test_truncate_short(self):
        from app.utils.text import truncate
        text = "Short text"
        result = truncate(text, 100)
        assert result == text
    
    def test_sanitize_filename(self):
        from app.utils.text import sanitize_filename
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result


class TestTxtParser:
    def setup_method(self):
        from app.services.document_parser import TxtParser
        self.parser = TxtParser()
    
    def test_parse_txt(self):
        content = "This is test content.\n\nSecond paragraph."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            assert "test content" in result
            assert "Second paragraph" in result
        finally:
            os.remove(temp_path)
    
    def test_parse_nonexistent(self):
        with pytest.raises(Exception):
            self.parser.parse("/nonexistent/path.txt")

    def test_parse_oversized_text_rejects_early(self, tmp_path):
        from app.services.document_parser import DocumentLimitError, TxtParser
        path = tmp_path / "large.txt"
        path.write_text("x" * 101, encoding="utf-8")
        with pytest.raises(DocumentLimitError):
            TxtParser(max_chars=100).parse(str(path))


class TestPdfParser:
    def test_blank_pdf_is_reported_as_unsupported_scanned_content(self, tmp_path):
        from PyPDF2 import PdfWriter
        from app.services.document_parser import PdfParser, UnsupportedScannedPDFError
        path = tmp_path / "blank.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        with path.open("wb") as stream:
            writer.write(stream)
        with pytest.raises(UnsupportedScannedPDFError, match="OCR is not enabled"):
            PdfParser().parse(str(path))

    def test_corrupt_pdf_has_actionable_parse_error(self, tmp_path):
        from app.services.document_parser import DocumentParsingError, PdfParser
        path = tmp_path / "corrupt.pdf"
        path.write_bytes(b"not a pdf")
        with pytest.raises(DocumentParsingError, match="corrupt"):
            PdfParser().parse(str(path))


class TestClauseSegmenterEdgeCases:
    def setup_method(self):
        from app.services.clause_segmenter import ClauseSegmenter
        self.segmenter = ClauseSegmenter()
    
    def test_segment_whitespace_only(self):
        clauses = self.segmenter.segment("   \n\n   ")
        assert clauses == []
    
    def test_segment_single_line(self):
        text = "This is a single line of text."
        clauses = self.segmenter.segment(text)
        assert len(clauses) >= 1
    
    def test_segment_very_short_merged(self):
        text = "1. INTRO\n\nThis is some introductory text about the service.\n\n2. BODY\n\nThis is body text with more content."
        clauses = self.segmenter.segment(text)
        assert len(clauses) >= 1
        for clause in clauses:
            assert len(clause.text) >= 20

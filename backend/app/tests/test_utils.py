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

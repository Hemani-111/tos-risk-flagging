import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


class TestDocumentParser:
    def test_pdf_parser_import(self):
        from app.services.document_parser import PdfParser
        assert PdfParser is not None
    
    def test_docx_parser_import(self):
        from app.services.document_parser import DocxParser
        assert DocxParser is not None
    
    def test_txt_parser_import(self):
        from app.services.document_parser import TxtParser
        assert TxtParser is not None
    
    def test_get_parser(self):
        from app.services.document_parser import get_parser
        parser = get_parser(".txt")
        assert parser is not None
    
    def test_get_parser_unsupported(self):
        from app.services.document_parser import get_parser
        with pytest.raises(ValueError):
            get_parser(".unsupported")


class TestClauseSegmenter:
    def setup_method(self):
        from app.services.clause_segmenter import ClauseSegmenter
        self.segmenter = ClauseSegmenter()
    
    def test_segment_empty_text(self):
        clauses = self.segmenter.segment("")
        assert clauses == []
    
    def test_segment_simple_text(self):
        text = "This is the first paragraph.\n\nThis is the second paragraph."
        clauses = self.segmenter.segment(text)
        assert len(clauses) >= 1
    
    def test_segment_with_headings(self):
        text = "1. INTRODUCTION\n\nThis is some introductory text about the service.\n\n2. DATA COLLECTION\n\nWe collect data to improve our service."
        clauses = self.segmenter.segment(text)
        assert len(clauses) >= 1
        sections = [c.section for c in clauses if c.section]
        assert len(sections) > 0

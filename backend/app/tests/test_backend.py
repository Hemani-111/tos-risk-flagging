import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"
        assert data["modelVersion"] == "linear-svc-primary-v2"

    def test_cors_allows_configured_local_frontend(self):
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "access-control-allow-credentials" not in response.headers


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

    def test_splits_sentences_inside_a_paragraph_and_preserves_text(self):
        text = ("We collect account data to provide the service. "
                "We share data with service providers. You can delete your account. "
                "We retain records as required by law. We may change these terms. "
                "You may contact support with questions.")
        clauses = self.segmenter.segment(text)
        assert len(clauses) == 6
        assert all(text[c.start_offset:c.end_offset] == c.text for c in clauses)

    def test_all_caps_substantive_sentence_is_not_discarded(self):
        text = "WE MAY TERMINATE YOUR ACCOUNT AT ANY TIME WITHOUT NOTICE."
        clauses = self.segmenter.segment(text)
        assert len(clauses) == 1
        assert clauses[0].text == text

    def test_numbered_heading_and_bullet_content_keep_section(self):
        text = "1. DATA USE\n\n- We may share personal data with service providers.\n"
        clauses = self.segmenter.segment(text)
        assert len(clauses) == 1
        assert clauses[0].section == "1. DATA USE"
        assert clauses[0].text == "We may share personal data with service providers."
        assert text[clauses[0].start_offset:clauses[0].end_offset] == clauses[0].text

    def test_wrapped_lines_are_joined_and_abbreviation_is_preserved(self):
        text = "We may collect data, e.g. account details and usage records,\n"
        text += "to provide and improve our service. You may delete your account."
        clauses = self.segmenter.segment(text)
        assert len(clauses) == 2
        assert clauses[0].text.startswith("We may collect data, e.g. account details")
        assert text[clauses[0].start_offset:clauses[0].end_offset] == clauses[0].text

    def test_quoted_sentence_boundaries_and_short_fragment(self):
        text = '"We may retain account records for legal reasons." You may request deletion.'
        clauses = self.segmenter.segment(text)
        assert len(clauses) == 2
        assert clauses[0].text.startswith('"We may retain')

    def test_unpunctuated_all_caps_heading_is_section(self):
        text = "DATA SHARING\n\nWe share data with processors to operate the service."
        clauses = self.segmenter.segment(text)
        assert len(clauses) == 1
        assert clauses[0].section == "DATA SHARING"

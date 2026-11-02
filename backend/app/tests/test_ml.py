import os
import sys
import time
from io import BytesIO
from threading import Event

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestModelLoading:
    def test_model_loader_import(self):
        from app.ml.model_loader import model_loader
        assert model_loader is not None

    def test_model_and_vectorizer_load(self):
        from app.ml.model_loader import model_loader
        model, vectorizer = model_loader.load()
        assert model is not None
        assert vectorizer is not None
        from app.ml.model_loader import model_loader
        assert model_loader.metadata["model_version"] == "legacy-selected-model-v1"
        assert model_loader.package_info()["schemaVersion"] == "1.1"

    def test_vectorizer_transform_shape(self):
        from app.ml.model_loader import model_loader
        _, vectorizer = model_loader.load()
        X = vectorizer.transform(["This is a test clause."])
        assert X.shape[0] == 1
        assert X.shape[1] > 0

    def test_model_predict_returns_valid_labels(self):
        from app.ml.model_loader import model_loader
        model, vectorizer = model_loader.load()
        X = vectorizer.transform(["This is a test clause.", "Another test clause."])
        preds = model.predict(X)
        assert len(preds) == 2
        for label in preds:
            assert label in {"Safe", "Neutral", "Risky"}


class TestAnalysisEndpoint:
    def test_sentence_level_predictions_and_risky_clause_filter(self, monkeypatch):
        from app.api.routes import analysis

        labels = ["Safe", "Risky", "Neutral", "Risky", "Safe", "Neutral"]
        seen = {}
        def controlled_predict(clauses):
            seen["texts"] = [c.text for c in clauses]
            return [{"id": c.clause_id, "text": c.text, "label": label,
                     "section": c.section, "startOffset": c.start_offset,
                     "endOffset": c.end_offset}
                    for c, label in zip(clauses, labels)]

        monkeypatch.setattr(analysis.predictor, "predict", controlled_predict)
        text = ("We collect account data to provide the service. "
                "We share data with service providers. You can delete your account. "
                "We retain records as required by law. We may change these terms. "
                "You may contact support with questions.")
        response = client.post("/api/v1/documents/analyze-text", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        assert len(seen["texts"]) == len(data["clauses"]) == 6
        assert all(c["label"] in {"Safe", "Neutral", "Risky"} for c in data["clauses"])
        assert data["riskyCount"] == sum(c["label"] == "Risky" for c in data["clauses"]) == 2
        assert data["riskyClauses"] == [c for c in data["clauses"] if c["label"] == "Risky"]
        assert data["totalClauses"] == data["safeCount"] + data["neutralCount"] + data["riskyCount"]
        assert data["modelVersion"]
        assert data["schemaVersion"] == "1.1"
        assert isinstance(data["warnings"], list)

    def test_analyze_txt_file(self):
        content = b"This is the first clause.\n\nThis is the second clause."
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("test.txt", content, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "filename" in data
        assert "totalClauses" in data
        assert "clauses" in data
        assert data["filename"] == "test.txt"

    def test_analyze_docx_file(self):
        from docx import Document
        document = Document()
        document.add_paragraph("We may change these terms after providing notice to account holders.")
        buffer = BytesIO()
        document.save(buffer)
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("terms.docx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert response.status_code == 200
        assert response.json()["totalClauses"] == 1

    def test_analyze_text_pdf_file(self):
        from app.tests.test_utils import make_text_pdf
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("terms.pdf", make_text_pdf("We may retain your account information to meet legal obligations."), "application/pdf")},
        )
        assert response.status_code == 200
        assert response.json()["totalClauses"] == 1
        assert response.json()["clauses"][0]["pageStart"] == 1
        assert response.json()["clauses"][0]["pageEnd"] == 1

    def test_analyze_empty_file(self):
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 422

    def test_upload_size_limit_is_enforced(self, monkeypatch):
        from app.api.routes import analysis
        monkeypatch.setattr(analysis.settings, "UPLOAD_MAX_SIZE", 8)
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("large.txt", b"x" * 9, "text/plain")},
        )
        assert response.status_code == 413

    def test_clause_count_limit_is_enforced(self, monkeypatch):
        from app.api.routes import analysis
        monkeypatch.setattr(analysis.settings, "MAX_CLAUSES", 1)
        text = "We collect personal information for service delivery. We may share data with processors."
        response = client.post("/api/v1/documents/analyze-text", json={"text": text})
        assert response.status_code == 413

    def test_analysis_timeout_returns_gateway_timeout_and_cleans_upload(self, monkeypatch, tmp_path):
        from app.api.routes import analysis
        real_named_temp = analysis.tempfile.NamedTemporaryFile
        created_paths = []
        finished = Event()
        cleaned = Event()

        def tracked_temp_file(*args, **kwargs):
            kwargs["dir"] = tmp_path
            temp_file = real_named_temp(*args, **kwargs)
            created_paths.append(temp_file.name)
            return temp_file

        original_predict = analysis.predictor.predict

        def slow_predict(clauses):
            try:
                time.sleep(0.5)
                return original_predict(clauses)
            finally:
                finished.set()

        original_remove = analysis._remove_temp_file

        def tracked_remove(path):
            original_remove(path)
            cleaned.set()

        monkeypatch.setattr(analysis.tempfile, "NamedTemporaryFile", tracked_temp_file)
        monkeypatch.setattr(analysis, "_remove_temp_file", tracked_remove)
        monkeypatch.setattr(analysis.predictor, "predict", slow_predict)
        monkeypatch.setattr(analysis.settings, "ANALYSIS_TIMEOUT_SECONDS", 0.2)
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("slow.txt", b"This is a sufficiently long clause for timeout verification.", "text/plain")},
        )
        assert response.status_code == 504
        assert finished.wait(timeout=2)
        assert cleaned.wait(timeout=2)
        assert len(created_paths) == 1
        assert not os.path.exists(created_paths[0])

    def test_analyze_unsupported_extension(self):
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("doc.zip", b"PK\x03\x04", "application/zip")},
        )
        assert response.status_code == 400

    def test_analyze_no_file(self):
        response = client.post("/api/v1/documents/analyze", files={})
        assert response.status_code == 422

    def test_analyze_result_labels(self):
        content = b"We reserve the right to change these terms at any time.\n\nYou can delete your account at any time."
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("test.txt", content, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        for clause in data["clauses"]:
            assert clause["label"] in {"Safe", "Neutral", "Risky"}
            assert "text" in clause
            assert "id" in clause

    def test_analyze_result_structure(self):
        content = b"Clause one is a longer clause with enough text.\n\nClause two is also a longer clause with enough text."
        response = client.post(
            "/api/v1/documents/analyze",
            files={"file": ("test.txt", content, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "safeCount" in data
        assert "neutralCount" in data
        assert "riskyCount" in data
        assert "overallAssessment" in data
        assert data["totalClauses"] == len(data["clauses"])

"""Record deterministic outputs and local timings for a fixed small fixture."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402
from app.ml.model_loader import model_loader  # noqa: E402


FIXTURE = (
    "We may share your personal information with our partners. "
    "You can delete your account at any time. "
    "We retain records as required by law."
)
CLAUSES = [
    "We may share your personal information with our partners.",
    "You can delete your account at any time.",
    "We retain records as required by law.",
]


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> None:
    model, vectorizer = model_loader.load()
    start = time.perf_counter()
    matrix = vectorizer.transform(CLAUSES)
    transform_seconds = time.perf_counter() - start
    start = time.perf_counter()
    labels = model.predict(matrix).tolist()
    predict_seconds = time.perf_counter() - start

    start = time.perf_counter()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/documents/analyze-text",
            json={"text": FIXTURE, "filename": "baseline.txt"},
        )
    api_seconds = time.perf_counter() - start
    response.raise_for_status()
    payload = response.json()

    artifacts = ROOT / "models" / "selected_model"
    record = {
        "date": date.today().isoformat(),
        "fixture": FIXTURE,
        "labels": labels,
        "feature_count": int(matrix.shape[1]),
        "timings_seconds_single_run": {
            "tfidf_transform": transform_seconds,
            "model_predict": predict_seconds,
            "analysis_api_including_test_client": api_seconds,
        },
        "api": {
            "status_code": response.status_code,
            "total_clauses": payload["totalClauses"],
            "risky_count": payload["riskyCount"],
            "labels": [clause["label"] for clause in payload["clauses"]],
        },
        "model_classes": model.classes_.tolist(),
        "artifact_sha256": {
            name: digest(artifacts / name)
            for name in ("model.joblib", "vectorizer.joblib")
        },
        "caveat": "Single local smoke run for reproducibility; timings are not a performance benchmark.",
    }
    output = ROOT / "results" / "baseline" / "smoke_v1.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()

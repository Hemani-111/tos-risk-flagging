"""Offline vs API prediction parity test.

Loads the production model package directly (offline path), segments and predicts on
sample clauses, then sends the same text through the FastAPI TestClient and compares
labels. A healthy /health endpoint only proves readiness; this test proves the offline
pipeline and backend produce identical labels for identical extracted clauses.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.model_loader import model_loader  # noqa: E402
from app.services.clause_segmenter import ClauseSegmenter  # noqa: E402
from app.services.predictor import Predictor  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]

SAMPLE_TEXTS = [
    "We may share your personal information with third-party advertisers for targeted marketing and you cannot opt out.",
    "You may access and correct your personal data by contacting our support team at any time.",
    "We reserve the right to terminate your account without notice for any reason.",
    "This service is provided as is and we disclaim all warranties to the fullest extent permitted by law.",
    "Your data will be encrypted in transit and at rest using industry-standard protocols.",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def offline_predict(clauses):
    """Direct offline prediction using the production model package + vectorizer."""
    package_dir = ROOT / "models" / "releases" / "linear-svc-primary-v2"
    vectorizer = joblib.load(package_dir / "vectorizer.joblib")
    model = joblib.load(package_dir / "model.joblib")
    texts = [c.text for c in clauses]
    tfidf = vectorizer.transform(texts)
    predictions = model.predict(tfidf)
    results = []
    for clause, label in zip(clauses, predictions):
        results.append(
            {
                "id": clause.clause_id,
                "text": clause.text,
                "label": str(label),
                "startOffset": clause.start_offset,
                "endOffset": clause.end_offset,
            }
        )
    return results, vectorizer, model


def api_predict(client, full_text):
    """API prediction via FastAPI TestClient."""
    resp = client.post("/api/v1/documents/analyze-text", json={"text": full_text, "filename": "parity-test.txt"})
    assert resp.status_code == 200, f"API returned {resp.status_code}: {resp.text}"
    return resp.json()


def main():
    # 1. Verify the production package loads and checksums match offline.
    package_dir = ROOT / "models" / "releases" / "linear-svc-primary-v2"
    metadata = json.loads((package_dir / "metadata.json").read_text(encoding="utf-8"))
    model_hash = sha256_file(package_dir / "model.joblib")
    vec_hash = sha256_file(package_dir / "vectorizer.joblib")
    assert model_hash == metadata["classifier"]["sha256"], "Model checksum mismatch"
    assert vec_hash == metadata["vectorizer"]["sha256"], "Vectorizer checksum mismatch"
    print(f"Offline package verified: {metadata['model_version']}")
    print(f"  model sha256: {model_hash[:16]}...")
    print(f"  vectorizer sha256: {vec_hash[:16]}...")
    print(f"  class order: {metadata['classifier']['class_order']}")

    # 2. Offline predictions on sample clauses.
    segmenter = ClauseSegmenter()
    full_text = "\n".join(SAMPLE_TEXTS)
    all_clauses = segmenter.segment(full_text)

    offline_results, vectorizer, model = offline_predict(all_clauses)
    print(f"\nOffline predictions on {len(all_clauses)} clauses:")
    for r in offline_results:
        print(f"  [{r['label']:7s}] {r['text'][:70]}")

    # 3. API predictions via TestClient on the same full text.
    client = TestClient(app)
    t0 = time.perf_counter()
    api_response = api_predict(client, full_text)
    api_seconds = time.perf_counter() - t0

    print(f"\nAPI predictions on {api_response['totalClauses']} clauses ({api_seconds:.3f}s):")
    for c in api_response["clauses"]:
        print(f"  [{c['label']:7s}] {c['text'][:70]}")

    # 4. Compare labels clause by clause (align by text + offsets).
    offline_by_offset = {(r["startOffset"], r["endOffset"]): r["label"] for r in offline_results}
    api_by_offset = {(c["startOffset"], c["endOffset"]): c["label"] for c in api_response["clauses"]}

    offsets_offline = set(offline_by_offset)
    offsets_api = set(api_by_offset)
    only_offline = offsets_offline - offsets_api
    only_api = offsets_api - offsets_offline
    common = offsets_offline & offsets_api

    mismatches = []
    for off in common:
        if offline_by_offset[off] != api_by_offset[off]:
            mismatches.append((off, offline_by_offset[off], api_by_offset[off]))

    print(f"\n=== Parity result ===")
    print(f"Offline clauses: {len(offsets_offline)}")
    print(f"API clauses:     {len(offsets_api)}")
    print(f"Common clauses:  {len(common)}")
    print(f"Only offline:    {len(only_offline)}")
    print(f"Only API:        {len(only_api)}")
    print(f"Label mismatches: {len(mismatches)}")
    for off, o, a in mismatches:
        print(f"  MISMATCH at {off}: offline={o} api={a}")

    ok = (len(only_offline) == 0 and len(only_api) == 0 and len(mismatches) == 0)
    print(f"PARITY: {'PASS' if ok else 'FAIL'}")

    # 5. Aggregate counts match.
    offline_counts = {label: 0 for label in LABELS}
    for r in offline_results:
        offline_counts[r["label"]] += 1
    api_counts = {
        "safe": api_response["safeCount"],
        "neutral": api_response["neutralCount"],
        "risky": api_response["riskyCount"],
    }
    print(f"\nOffline counts: {offline_counts}")
    print(f"API counts:     risky={api_counts['risky']}, neutral={api_counts['neutral']}, safe={api_counts['safe']}")
    print(f"Model version reported by API: {api_response['modelVersion']}")

    return ok


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)

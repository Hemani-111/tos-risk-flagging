# Local demonstration and deployment guide

## Run the complete local demo on Windows

Prerequisites: Python 3.11, Node.js/npm, the repository checkout, and the versioned model files under `models/releases/linear-svc-primary-v2/`. The application runs locally without downloading an encoder or fetching policy snapshots.

Open two PowerShell terminals from the repository root.

### Terminal 1: backend

```powershell
.\.venv\Scripts\Activate.ps1
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check readiness in a third terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

The response should have `status: ok` and `modelVersion: linear-svc-primary-v2`.

### Terminal 2: frontend

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:3000`. Keep both terminals running during the demonstration. Stop each process with Ctrl+C afterward.

## Demonstration path

1. Open Analyze and paste a short policy excerpt or upload a local selectable-text PDF, DOCX, or TXT file.
2. Review the predicted clauses and class filters/search.
3. Select a clause and inspect its highlighted span in the extracted source. The source view preserves text that was not segmented and reports analysed coverage.
4. Export JSON/CSV or use Print / Save PDF.
5. Explain that this is clause triage: a document with no Risky prediction is not established as safe. Scanned/image-only PDFs are unsupported because OCR is not enabled.

Use only approved development examples for a live demo. Never present locked-test clauses as examples for tuning or as model-selected cases.

## Model package and rollback

The API loads `models/releases/linear-svc-primary-v2` by default. The directory contains the serialized vectorizer/model and `metadata.json` with artifact checksums and model identity. `MODEL_DIR` can point to another complete package for a controlled local run. The earlier RBF artifacts remain under `models/selected_model/` as historical rollback material; switching to them requires setting `MODEL_DIR` explicitly and checking the expected package schema/version.

Do not replace individual package files in place. Build a new versioned release, verify hashes and API predictions, then update the package directory reference together. Keep the prior complete release until rollback is checked.

## Local data and privacy

Policy snapshots under `data/review/snapshots_v1/`, embedding caches, and source datasets are local-only and excluded from Git. Analysis results are scoped to browser session storage. Clear the browser tab/session after a demonstration when you do not want the results retained in that session. Do not upload confidential or personal policy text to a public host unless the hosting, retention, and consent terms are reviewed.

## Container deployment status

Compose syntax has passed `docker compose config --quiet`; Docker image build, startup, mounted model loading, and real container analysis have not been verified because the Docker Desktop Linux engine was unavailable in the recorded environment.

When Docker is available, resume with:

```powershell
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
docker compose logs --tail 100 backend frontend
```

Confirm the health response names `linear-svc-primary-v2`, run one permitted analysis request, inspect logs, and stop with `docker compose down`. Record observed output before calling container deployment verified.

## Public hosting gate

No public hosting target is selected. Before exposing the service, configure HTTPS, host-specific CORS and frontend API URL, rate limits, request/body limits, secrets, monitoring, retention/deletion, and rollback. Re-run dependency and integration checks against the actual deployment. Do not commit policy snapshots, user documents, credentials, or model caches. Dataset licensing and redistribution rights remain unresolved; review them before publishing trained artifacts or datasets.

See [DEPLOYMENT_READINESS_v1.md](DEPLOYMENT_READINESS_v1.md) for recorded checks and environment-specific blockers.

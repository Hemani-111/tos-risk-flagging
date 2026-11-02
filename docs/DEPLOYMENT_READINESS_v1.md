# Deployment readiness review

Date: 3 November 2026  
Status: local verification passed; container startup and public hosting are unverified.

## Reproducibility checks

- Installed root `requirements.txt` in a new Python 3.11 virtual environment and ran the backend suite: **45 passed**. Ruff reported no issues in the backend app and source-fetch/review-segment scripts.
- `pip-audit -r requirements.txt`: **no known vulnerabilities**.
- Ran `npm ci`, `npm audit`, `npm run lint`, and `npm run build` from the frontend: clean install completed, audit reported **0 vulnerabilities**, lint passed, and the Next.js 16 production build passed.
- `docker compose config --quiet` passed and resolves `MODEL_DIR=/app/models/selected_model`, the read-only model mount, the CORS origin list, and the frontend build-time API URL argument. Docker image build/start was attempted but could not connect to the Docker Desktop Linux engine.
- The API tests cover PDF, DOCX, and TXT upload, pasted text, malformed/empty/scanned/encrypted PDFs, byte/character/page/clause limits, readiness, CORS, request timeout and temporary-file cleanup.

## Local performance sample

One local run on the Phase 0 machine (Windows 11, Intel i5-12450HX, 16 GB RAM, Python 3.11.9) used three frozen consumer Terms of Service text snapshots. The text files were already extracted; extraction timing below measures UTF-8 TXT reading, not PDF/DOCX parsing. This is a small engineering sample, not a service-level objective or a p95 estimate.

| Document | Characters | Clauses | TXT read (s) | Segmentation (s) | TF-IDF transform (s) | Prediction (s) | Total (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Anthropic consumer terms | 29,319 | 188 | 0.0028 | 0.0017 | 0.0137 | 0.6835 | 0.7016 |
| Mistral AI ROW consumer terms | 42,572 | 263 | 0.0025 | 0.0017 | 0.0071 | 0.9300 | 0.9412 |
| You.com terms | 43,099 | 268 | 0.0021 | 0.0013 | 0.0077 | 0.9998 | 1.0109 |

A cold subprocess import plus model integrity checks and load took 1.80 seconds (1.99 seconds measured wall time). The current request budget is 45 seconds with at most two active analyses, 10 MB upload size, 2,000,000 extracted characters, 200 PDF pages, and 5,000 clauses. The CPU-heavy classifier prediction dominates these short samples. Measure representative PDF/DOCX extraction and concurrent load before revising these limits.

## Operational configuration and open deployment work

- `MODEL_DIR` is explicit in Compose; metadata records the model and vectorizer hashes, class order, schema/model versions, and required scikit-learn version. The existing RBF SVC artifact remains deployed.
- CORS origins are configurable through `CORS_ORIGINS_STR`, default to local frontend origins, and do not allow credentials. Operational logs avoid document text. Upload temp files are deleted after normal processing, errors, and when timed-out worker processing finishes.
- The frontend requires Node.js 20.9 or newer; the container uses Node 22. The client API URL is supplied at build time through `NEXT_PUBLIC_API_URL`.
- The frontend uses tab-scoped session storage and offers a clear action. The backend stores no analysis history.
- No hosting provider/domain was selected. HTTPS termination, production origin values, edge rate limiting, monitoring/alerting and secret injection must be configured at the chosen host before public use. They have not been configured here.
- Docker Desktop was unavailable in this environment, so image builds, container readiness, and the actual mounted model load remain unverified.
- Dataset licensing is still unspecified in the upstream source record. No dataset or complete-document snapshots were added to the application image; local source snapshots and review text remain Git-ignored.
- The final independent document evidence gate still needs two human annotation sheets and adjudication. The locked benchmark test partitions remain unused.

## Dependency notes

The previous frontend pinned Next.js 14.0.3, which was outside the currently supported release lines and produced a critical npm advisory. The frontend is now on Next.js 16.4.4 / React 19.3.1. The backend stack was refreshed, and PyPDF2 was replaced with its maintained successor `pypdf`. The existing scikit-learn pin remains 1.9.0 because the deployed serialized model package requires that exact version. Both package audits returned no known vulnerabilities on 3 November 2026. npm reports an upstream deprecation notice for ESLint 9.39.5; the current Next.js ESLint config and its plugins do not declare ESLint 10 compatibility, so lint remains pinned to the supported peer range used by this stack.

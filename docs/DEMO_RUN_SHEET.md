# Local demonstration run sheet

**Status:** provisional course demonstration materials. All sample inputs below are illustrative and synthetic. They are not locked-test rows, not ground truth, and not evaluation evidence. Never present locked-test clauses as demo examples.

**Running services:** backend `127.0.0.1:8000`, frontend `127.0.0.1:3000`. Model identity: `linear-svc-primary-v2` (verify via `http://127.0.0.1:8000/api/v1/health`).

## Before presenting

1. Start from the repository root. Confirm the Python environment and frontend dependencies are installed.
2. Start API and frontend per `docs/DEPLOYMENT_GUIDE.md`; verify API health returns `status: ok` and `modelVersion: linear-svc-primary-v2`.
3. Keep policy source snapshots local; they are ignored by Git. Do not paste real user or confidential policy text into the demo.
4. Use only the illustrative inputs below or a short local sample you created yourself. Never use a locked-test row.
5. Prepare a selectable-text PDF only if you need to show PDF page ranges.

## Illustrative demo inputs (synthetic, illustrative only)

These short excerpts are written for demonstration. They are not drawn from the benchmark, are not labeled ground truth, and must not be described as model-selected cases.

### A. Normal example — expected Risky flag

Paste this into the Analyze page:

> "We may share your personal information with third-party advertising partners for targeted marketing purposes, and you cannot opt out of this sharing."

Expected behavior: one or more clauses are classified; at least one clause receives a Risky prediction. Show the class filter and search box, then select a Risky clause to inspect its highlighted span in the extracted source.

### B. Difficult example — ambiguous / mixed signal

Paste this into the Analyze page:

> "You may request access to your data by contacting our support team, subject to applicable law and our verification procedures."

Expected behavior: the clause may land in Neutral or Safe territory depending on wording. Use this to show that the model flags clauses for human review rather than deciding legality, and that a borderline clause is legitimately uncertain. Explain that a no-flagged-clause result does not mean the document is safe.

### C. Short fragment / minimal input

Paste this into the Analyze page:

> "Contact us."

Expected behavior: the app handles a very short fragment without crashing; it may return zero clauses or a single Neutral clause. Show the explicit zero-detection / no-match state without implying guaranteed safety.

## Error-case instructions (illustrative, do not use real documents)

Show each error case once, then move on. These demonstrate graceful handling, not model performance.

| Case | What to do | Expected result |
|------|-----------|-----------------|
| Empty paste | Submit an empty text field | Validation error; no analysis started |
| Unsupported file type | Upload an `.exe`, `.zip`, or image file | Rejected unsupported-format error |
| Scanned / image-only PDF | Upload a PDF with no selectable text | Unsupported-document error; never presented as safe |
| Encrypted / corrupt PDF | Upload a password-protected or damaged PDF | Corrupt/encrypted error; temporary file cleaned up |
| Oversized upload | Upload a file above the documented limit | Size-limit error before processing |

## Live flow

1. Paste or upload a document. Explain that the model classifies extracted clauses, not whole-policy legality.
2. Show the full extracted-text view: highlighted clauses, unclassified gaps, and analysed coverage.
3. Filter/search findings and select one to navigate between clause result and source excerpt.
4. Export JSON/CSV or print/save the readable report as PDF.
5. If time permits, show one clear unsupported-input error (scanned or encrypted PDF) and explain the limitation.
6. End with test-stage results and the authentic human-review gate. Do not frame a missing Risky prediction as proof of safety.

## Evidence status

Recorded passes: backend suite, changed-file Ruff, frontend lint/build, split verification, local API startup reporting `linear-svc-primary-v2`, registry generation.

Unverified: Docker startup/container model mount (`//./pipe/dockerDesktopLinuxEngine` unavailable), screenshot-driven browser/accessibility review (Windows helper could not resolve active URL), editable slide export (presentation authoring runtime unavailable).

Public hosting: not selected. HTTPS, rate limits, monitoring, host CORS/secrets, and rollback require a host decision before any public use.

## Human-review gate (pending)

Two authentic independent reviewer sheets (`reviewer_a_segments_v1.csv`, `reviewer_b_segments_v1.csv`) under ignored `data/review/snapshots_v1/` are blank. Do not fill them with model outputs. When returned, run `python scripts/analyze_document_annotation_agreement.py` to validate and build an adjudication queue; report as student-reviewed, not expert legal truth.

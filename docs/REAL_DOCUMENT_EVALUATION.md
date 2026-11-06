# Real-Document Evaluation — TermsGuard / `tos-risk-flagging`

**Evaluation ID:** `real_document_eval_v2`  
**Date (UTC):** 2026-11-06  
**Candidate:** [`linear-svc-primary-v2`](models/releases/linear-svc-primary-v2/metadata.json:1) (frozen package; no tuning/threshold/segmentation/artifact changes during collection)  
**Freeze record:** [`data/review/real_document_eval_v2/candidate_freeze.json`](data/review/real_document_eval_v2/candidate_freeze.json:1)  
**Working-tree patch:** [`data/review/real_document_eval_v2/working_tree.patch`](data/review/real_document_eval_v2/working_tree.patch:1) (SHA-256 `821f173374bd9d5c86e476ff2482cd7e0f52ed6c25fefbf966554a1bf1f726b9`, 872 lines)

## 1. Scope and constraints

This evaluation measures: (1) end-to-end application reliability on real policy documents, (2) clause prediction behavior on complete real documents, (3) classification performance **only where authentic independent human annotations exist**. No authentic adjudicated human labels were produced in this run; therefore **no real-document accuracy/F1/confusion-matrix classification metrics are reported**. Results below are operational, extraction/segmentation, and prediction-distribution evidence only.

## 2. Evaluation freeze (actual)

| Item | Value |
|---|---|
| Git HEAD | `e693bfc582afbb8d54c4bb17870d610f13defa6d` (2026-11-04 16:30:26 +0530) |
| Working-tree patch | `data/review/real_document_eval_v2/working_tree.patch` (SHA-256 `821f173374bd9d5c86e476ff2482cd7e0f52ed6c25fefbf966554a1bf1f726b9`, 872 lines) |
| Working-tree changes | `M backend/app/api/routes/analysis.py` (typing compatibility), `M backend/app/ml/model_loader.py` (sklearn version mismatch warn+proceed), `M models/releases/linear-svc-primary-v2/metadata.json` (line-ending normalization; artifact hashes unchanged) |
| Serving model | `linear-svc-primary-v2`, schema `1.1` |
| Class mapping / label space | `Safe`, `Neutral`, `Risky` (model `class_order`: `["Neutral","Risky","Safe"]`) |
| Feature pipeline | [`TfidfVectorizer`](backend/app/services/predictor.py:17) word 1–2 ngrams, `min_df=2`, `max_df=0.99`, `max_features=60000`, `sublinear_tf=true`, `strip_accents=unicode`, `dtype=float32` → `LinearSVC(C=1.0, class_weight=balanced, random_state=20261102, max_iter=5000)` |
| Artifact checksums (verified) | `model.joblib` `7f332e1d02a866e39084ad508023ce2927a1bdd1f6576bfb783dffdd641fc5c8`; `vectorizer.joblib` `e8ee8d0dfe057bc9a79fd533ccc3d91d6ba8cd4e743e0a0af9cf0b20b7a88e58` (match metadata-declared hashes) |
| Runtime (venv) | Python 3.9.25, scikit-learn 1.5.2, joblib 1.5.3, numpy 2.0.2, fastapi 0.128.8, uvicorn 0.39.0, pydantic 2.13.5, pypdf 6.21.4, python-docx 1.2.0 |
| pip freeze | `data/review/real_document_eval_v2/pip_freeze.txt` |
| API/limits | [`/api/v1/documents/analyze-text`](backend/app/api/routes/analysis.py:204), [`/api/v1/documents/analyze`](backend/app/api/routes/analysis.py:161); `MAX_EXTRACTED_CHARS=2,000,000`, `MAX_CLAUSES=5,000`, `ANALYSIS_TIMEOUT=45s`, `MAX_CONCURRENT=2` |
| API health (observed) | `{"status":"ok","version":"1.0.0","modelVersion":"linear-svc-primary-v2"}` at `http://127.0.0.1:8000/api/v1/health` |
| Historical locked-test results | **Not modified**. Prior results remain under [`docs/LOCKED_TEST_EVALUATION_v1.md`](docs/LOCKED_TEST_EVALUATION_v1.md:1), [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md:1), and model `results/` directories. |

### Artifact/runtime mismatch (documented, not suppressed)

The artifact metadata declares scikit-learn 1.9.0 / numpy 2.4.6 / joblib 1.4.2 / python 3.11. The actual serving runtime is scikit-learn 1.5.2 / numpy 2.0.2 / joblib 1.5.3 / python 3.9.25. The model loader emits a warning and proceeds with a compatibility load:

> `Model package declares scikit-learn 1.9.0; runtime has 1.5.2. Proceeding with compatibility load.`

This warning is logged at [`backend/app/ml/model_loader.py`](backend/app/ml/model_loader.py:47-52). The loader previously raised a hard `RuntimeError` on version mismatch; the working-tree patch changes it to a warning+proceed. Artifact checksums match metadata-declared hashes, so artifacts are intact. However, scikit-learn version drift between training and serving environments is a known compatibility risk and is documented here, not suppressed silently. Suppressing the warning does **not** establish compatibility.

## 3. Document selection and collection

Target: 12 documents (6 services × Terms/User Agreement + Privacy Policy), English, official sources, different categories. Starting candidates included as specified: Discord ToS, Spotify India EULA, Reddit User Agreement. Collection used `urllib` (no access-block bypass). Snapshots/raw HTML and cleaned text saved locally under ignored [`data/review/real_document_eval_v2/`](data/review/real_document_eval_v2/candidate_freeze.json:1) (see `.gitignore`); source manifest kept as [`data/review/real_document_sources_v2.csv`](data/review/real_document_sources_v2.csv:1) (metadata/checksums/URLs/status; no unnecessary full source text).

| document_id | Service | Category | Type | Region/Jurisdiction | URL | Collection | Snapshot bytes | Cleaned chars | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `discord_tos` | Discord | messaging | Terms of Service | global/US | https://discord.com/terms | snapshot_frozen | 134,707 | 59,754 | HTML cleaned via stdlib VisibleText+heuristics |
| `discord_privacy` | Discord | messaging | Privacy Policy | global/US | https://discord.com/privacy | snapshot_frozen | 111,872 | 35,705 | HTML cleaned |
| `spotify_tos_in` | Spotify | streaming | EULA | **India (IN)** | https://www.spotify.com/in-en/legal/end-user-agreement/ | snapshot_frozen | 160,862 | 42,388 | India link used as specified |
| `spotify_privacy` | Spotify | streaming | Privacy Policy | region-specific presentation | https://www.spotify.com/in-en/legal/privacy-policy/ | snapshot_frozen | 196,868 | 43,114 | HTML cleaned |
| `reddit_user_agreement` | Reddit | social media | User Agreement | global/US | https://www.redditinc.com/policies/user-agreement | snapshot_frozen | 548,292 | 47,188 | Initial extraction thin; re-extracted from `<main>` |
| `reddit_privacy` | Reddit | social media | Privacy Policy | global/US | https://www.reddit.com/policies/privacy-policy | **thin/JS shell** | 8,429 | 6 | Alternative URL redirected to same shell; manual official save/PDF-text needed |
| `github_tos` | GitHub | developer tools | Terms of Service | global/US | https://docs.github.com/en/site-policy/github-terms/github-terms-of-service | snapshot_frozen | 366,687 | 46,051 | HTML cleaned |
| `github_privacy` | GitHub | developer tools | Privacy Statement | global | https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement | snapshot_frozen | 304,835 | 40,524 | HTML cleaned |
| `notion_tos` | Notion | productivity | Terms (consumer page) | global/US | https://www.notion.so/terms | **thin/JS shell** | 22,478 | 6 | Redirected to app shell; alternative `notion.com/terms` also app shell; manual save needed |
| `notion_privacy` | Notion | productivity | Privacy Policy | global | https://www.notion.so/privacy | **thin/JS shell** | 22,478 | 6 | Alternative returned HTTP 401; manual save needed |
| `etsy_tos` | Etsy | shopping/marketplace | Terms of Use | global/region-specific | https://www.etsy.com/legal/terms-of-use | **fetch_failed:403** | — | — | Access blocked; no bypass; manual official save supported |
| `etsy_privacy` | Etsy | shopping/marketplace | Privacy Policy | global/region-specific | https://www.etsy.com/legal/privacy/ | **fetch_failed:403** | — | — | Access blocked; no bypass |

**Overlap note:** The training split manifest uses anonymized `service_component` hashes; no direct name-to-hash mapping was found in reviewed manifests. Candidate names were checked against [`data/raw/services.csv`](data/raw/services.csv:1) (ToSDR-derived registry): all selected service names appear or have related entries. Overlap is recorded as **known-registry/potential-overlap**; exact clause-level training overlap cannot be ruled out. **No temporal generalization and no unseen-service generalization are claimed.**

## 4. Source completeness vs clause-span coverage

Character-span coverage (clause offsets within cleaned text) is **not** source completeness. Source completeness asks whether the cleaned text captures the full official policy; clause-span coverage asks what fraction of cleaned text is assigned to a clause.

| document_id | Snapshot bytes | Cleaned chars | Clause-span coverage | Unclassified chars | Unclassified % | Unclassified content (top gaps) |
|---|---|---|---|---|---|---|
| `discord_tos` | 134,707 | 59,754 | 97.82% | 1,302 | 2.18% | Footer nav (122), TOC/headings (100, 59), section headings |
| `discord_privacy` | 111,872 | 35,705 | 97.50% | 892 | 2.50% | Footer nav (122), TOC/headings (40, 31), address (30) |
| `spotify_tos_in` | 160,862 | 42,388 | 97.10% | 1,231 | 2.90% | TOC (207), section headings (58, 57, 46) |
| `spotify_privacy` | 196,868 | 43,114 | 90.00% | 4,311 | **10.00%** | TOC (374), table headers (127), data-category lists (74, 68×6) |
| `reddit_user_agreement` | 548,292 | 47,188 | 96.00% | 1,888 | 4.00% | Language lists (100, 81, 53), section headings (54×2, 48×2, 43) |
| `github_tos` | 366,687 | 46,051 | 95.33% | 2,152 | 4.67% | Sidebar "Skip to content" (49), section headings (44, 42, 41, 40×2, 36×2) |
| `github_privacy` | 304,835 | 40,524 | 97.81% | 886 | 2.19% | Sidebar (49), table headers (38, 26), section headings (19×2, 18×2) |

**Spotify Privacy unclassified spans (~10%):** The largest unclassified gap is a table of contents (374 chars: "1. About this Policy … 12. How to contact us"). The next largest are table headers (127 chars: "Categories of data / Reason for sharing / Service providers / User Data / Street Address Data / Usage Data / Voice Data / Message Data") and repeated data-category lists (68 chars each, appearing 6 times). These are **navigation/TOC/table-header material**, not substantive policy paragraphs. No substantive body paragraphs were found in the unclassified spans for Spotify Privacy. However, source completeness cannot be fully confirmed from automated checks alone — manual review of the cleaned text against the official source is recommended to confirm no substantive sections were dropped by the HTML cleaner.

**Key distinction:** High character-span coverage (90–98%) does **not** prove accurate extraction or useful segmentation. It only shows that most cleaned-text characters fall within clause offsets. Unclassified spans are predominantly TOC, headings, table headers, and navigation remnants — not missing substantive content — but this requires manual confirmation per document.

## 5. Real-application execution (actual)

Documents with usable cleaned text were submitted to the **running** API via [`POST /api/v1/documents/analyze-text`](backend/app/api/routes/analysis.py:204) (curl `--data-binary`, 180s timeout). Raw per-document responses saved under ignored `data/review/real_document_eval_v2/api_outputs/`. Repeat timing = 3 requests total per document (first + 2 repeats), **curl wall-clock including HTTP/JSON transfer; local loopback; not a production capacity benchmark**.

**API status by document:** 7/12 `ok`, 3/12 API error `No analyzable clauses were found in the document` (thin extraction inputs), 2/12 skipped (Etsy 403/no usable snapshot). **No truncation/size/clause-limit errors** observed for successful docs.

### Required table

| Service | Policy | Region | Training overlap | API status | Clause count | Risky/Neutral/Safe (pred.) | Extraction issues | Human evaluation status |
|---|---|---|---|---:|---:|---|---|---|
| Discord | Terms of Service | global/US | known-registry/potential-overlap | ok | 369 | 115/181/73 (31.17%/49.05%/19.78%) | cov 97.82%, 0 offset/span errors; nav/cookie heuristic cleanup applied to HTML extract | representative+targeted blind sheets prepared; **no authentic labels/adjudication** |
| Discord | Privacy Policy | global/US | known-registry/potential-overlap | ok | 324 | 116/63/145 (35.8%/19.44%/44.75%) | cov 97.5%, 0 errors | blind sheets prepared; no authentic labels |
| Spotify | EULA (IN) | India (IN) | known-registry/potential-overlap | ok | 243 | 52/134/57 (21.4%/55.14%/23.46%) | cov 97.1%, 0 errors | blind sheets prepared; no authentic labels |
| Spotify | Privacy Policy | region-specific | known-registry/potential-overlap | ok | 518 | 195/126/197 (37.64%/24.32%/38.03%) | cov 90.0% (lower character coverage; unclassified spans are TOC/table headers, not body paragraphs) | blind sheets prepared; no authentic labels |
| Reddit | User Agreement | global/US | known-registry/potential-overlap | ok | 316 | 43/211/62 (13.61%/66.77%/19.62%) | cov 96.0%; initial nav-heavy extract fixed by `<main>`-targeted re-extraction | blind sheets prepared; no authentic labels |
| Reddit | Privacy Policy | global/US | known-registry/potential-overlap | error (no analyzable clauses) | — | — | JS shell/thin extraction (6 chars cleaned); official manual save needed | **blocked pending snapshot** |
| GitHub | Terms of Service | global/US | known-registry/potential-overlap | ok | 358 | 37/191/130 (10.34%/53.35%/36.31%) | cov 95.33%, 0 errors | blind sheets prepared; no authentic labels |
| GitHub | Privacy Statement | global | known-registry/potential-overlap | ok | 327 | 114/54/159 (34.86%/16.51%/48.62%) | cov 97.81%, 0 errors | blind sheets prepared; no authentic labels |
| Notion | Terms (consumer page) | global/US | known-registry/potential-overlap | error (no analyzable clauses) | — | — | JS app shell; redirect to `app.notion.com`; manual save needed | **blocked pending snapshot** |
| Notion | Privacy Policy | global | known-registry/potential-overlap | error (no analyzable clauses) | — | — | JS/401 on alternative; manual save needed | **blocked pending snapshot** |
| Etsy | Terms of Use | global/region-specific | known-registry/potential-overlap | skipped | — | — | HTTP 403 on collection (no bypass) | **blocked pending manual snapshot** |
| Etsy | Privacy Policy | global/region-specific | known-registry/potential-overlap | skipped | — | — | HTTP 403 on collection (no bypass) | **blocked pending manual snapshot** |

Totals (successful API runs): **2,455 clauses** across 7 documents; predicted **672 Risky / 960 Neutral / 823 Safe**. Counts and percentages were validated against returned clause totals in saved outputs; label set restricted to `Safe|Neutral|Risky`; all checked offsets in range with **0 span/text mismatches** on successful docs (automated check in [`data/review/real_document_eval_v2/aggregate/extraction_segmentation_inspection.json`](data/review/real_document_eval_v2/aggregate/extraction_segmentation_inspection.json:1)).

## 6. Extraction and segmentation inspection

**Automated checks (7 successful docs):** offset errors 0, span/text mismatches 0, labels valid. Character-span coverage 90.0%–97.82% (Spotify Privacy lowest). *High character coverage does not prove accurate extraction or useful segmentation.*

**Manual/qualitative findings (inspected via saved outputs):**
- HTML cleaning is heuristic (`VisibleText` + cookie/consent short-line filter). Residual navigation/banner text can remain if not matched by heuristics; policy-body targeting improved for Reddit UA by `<main>` extraction.
- Reddit UA initially produced nav-heavy/short extraction (14 chars from strict cleaner); corrected by targeted re-extraction and recorded in manifest notes. Reddit Privacy and Notion pages are JS-rendered shells in collected form; the app/API cannot analyze text that was not extracted.
- Spotify Privacy’s lower coverage (90%) warrants manual review for omitted sections/tables/bullets in the cleaned snapshot. Unclassified spans are TOC/table headers/data-category lists, not body paragraphs.
- Segmentation follows existing [`ClauseSegmenter`](backend/app/services/clause_segmenter.py:15) behavior (paragraph runs + sentence splitting, heading detection, list markers, min clause length). Some headings/short structural lines may be classified as clauses depending on text form; sentence splitting can separate context/qualifiers — examples should be reviewed in blind human evaluation.
- No model/segmentation/threshold fixes were applied during this run (frozen candidate). Incorrect behavior preserved as evidence.

## 7. Prediction examples (model predictions — **not** human-verified)

Examples below are **predictions** from the frozen model on real extracted text. They illustrate behavior and do **not** establish legal risk ground truth. Items marked "suspected error" are unverified and pending independent annotation.

| document_id | section | clause_id | prediction | exact clause text (excerpt) | source context (excerpt) | status |
|---|---|---|---|---|---|---|
| `discord_tos` | — | `clause_15` | **Risky** | “Discord enables you to build meaningful connections around the joy of playing games through voice, video and text features.” | “Welcome! Discord enables you to build meaningful connections…” | suspected error (generic welcome text labeled Risky) |
| `discord_tos` | — | `clause_21` | **Neutral** | “When we say ‘Discord,’ ‘we,’ ‘us,’ and ‘our’ in these terms, we mean Discord Inc., its subsidiaries, and its related companies.” | definitional context | — |
| `discord_tos` | — | `clause_24` | **Safe** | “If you’re accessing our services on behalf of a legal entity…” (authority/binding language as extracted) | account/entity context | — |
| `spotify_tos_in` | 1. Introduction | `clause_12` | **Risky** | “You also promise that any registration information that you submit to Spotify is true, accurate, and complete…” | registration/obligation context | — |
| `reddit_user_agreement` | — | `clause_18` | **Risky** | “Reddit User Agreement if you live in the United States or outside the EEA, United Kingdom, and Switzerland” | navigational/label-like text | **suspected error** (structural fragment labeled Risky) |
| `github_privacy` | — | `clause_26` | **Risky** | “When you use third-party extensions, integrations, or follow references and links…” (third-party privacy policies apply) | third-party data/protection context | — |
| `github_privacy` | — | `clause_7` | **Safe** | “This is where we describe how we handle your ‘Personal Data’…” | privacy-statement intro/context | — |
| `spotify_privacy` | 1. About this Policy | `clause_16` | **Risky** | “These include Spotify websites, Customer Service and the Community Site .” | service-definition context | — |

Full example set: [`data/review/real_document_eval_v2/aggregate/prediction_examples.json`](data/review/real_document_eval_v2/aggregate/prediction_examples.json:1). All items are **predictions unless verified by human adjudication**; “suspected error” items require independent reviewer confirmation.

## 8. Human evaluation materials (prepared; **not scored**)

Authentic reviewer labels are **unavailable** in this environment. Classification scoring was **stopped at that boundary** (per protocol). Blind materials prepared under ignored `data/review/real_document_eval_v2/review_sheets/`:

### Representative sample (n=250)
- **Strata:** 7 documents with usable cleaned text (discord_tos, discord_privacy, spotify_tos_in, spotify_privacy, reddit_user_agreement, github_tos, github_privacy).
- **Population:** 2,455 total clauses across the 7 analyzed documents.
- **Sampling design:** Stratified by document with approximately equal per-document allocation (250 / 7 ≈ 36 clauses per document, rounded), then random fill within each document using seed `20261106`. Model predictions were **not** used for inclusion.
- **Sampling probabilities:** Each clause within a document had equal probability of selection within that document’s stratum. Per-document stratum weight = document_clause_count / 2,455.
- **Intended estimand:** Pooled accuracy/F1 over the sampled 250 clauses estimates performance for that sampling design only. A pooled score does **not** automatically estimate performance across all 2,455 clauses or across all 12 documents. Document-level results should be reported separately; any population-level estimate would require inverse-probability weighting by stratum (document_clause_count / sampled_clause_count_per_document).
- **Blind CSVs:** [`reviewer_A_blind_representative_v2.csv`](data/review/real_document_eval_v2/review_sheets/reviewer_A_blind_representative_v2.csv:1), [`reviewer_B_blind_representative_v2.csv`](data/review/real_document_eval_v2/review_sheets/reviewer_B_blind_representative_v2.csv:1) — no prediction/confidence/explanation columns.

### Targeted challenge set (n=120, separate — do not mix)
- Categories: arbitration, liability, content license, term changes, termination, data sharing, protective provisions, ordinary clauses.
- Blind CSV: [`targeted_challenge_set_v2_DO_NOT_MIX_WITH_REPRESENTATIVE.csv`](data/review/real_document_eval_v2/review_sheets/targeted_challenge_set_v2_DO_NOT_MIX_WITH_REPRESENTATIVE.csv:1).
- Scores from this set must **not** be mixed with the representative sample.

### Sampling metadata
- [`review_sampling_meta.json`](data/review/real_document_eval_v2/review_sheets/review_sampling_meta.json:1): seed `20261106`, target range [150, 250], representative count 250, targeted count 120, sampling method documented.

**When completed sheets exist:** validate IDs/labels, measure agreement before adjudication, produce disagreement queue, keep original annotations, adjudicate, then compute accuracy/macro+weighted F1/per-class metrics/balanced accuracy/confusion matrix/Risky FP-FN on adjudicated labels. Do not populate labels from model predictions.

## 9. Figures (generated from saved outputs)

- [`data/review/real_document_eval_v2/figures/predicted_composition_by_document.png`](data/review/real_document_eval_v2/figures/predicted_composition_by_document.png:1) — predicted label composition (no human labels).
- [`data/review/real_document_eval_v2/figures/extraction_issue_indicators.png`](data/review/real_document_eval_v2/figures/extraction_issue_indicators.png:1) — extraction/segmentation issue indicators.
- [`data/review/real_document_eval_v2/figures/first_request_timing.png`](data/review/real_document_eval_v2/figures/first_request_timing.png:1) — first-request curl wall-clock timing (local, not production benchmark). No confusion-matrix/per-class metric figures generated because **no human labels exist**.

## 10. Frontend review

**Browser automation unavailable in this environment; visual verification not performed.** HTTP/source checks: frontend responded `HTTP 200` at `http://127.0.0.1:3000/` during evaluation; backend health OK. UI flows (upload/paste, long-document layout, search/filter, clause-to-source jump, exact highlights, page refs, CSV/JSON export, print, error states) require manual browser verification with screenshots. Existing frontend implementation references: [`frontend/src/pages/AnalyzePage.jsx`](frontend/src/pages/AnalyzePage.jsx:1), [`frontend/src/pages/ReviewPage.jsx`](frontend/src/pages/ReviewPage.jsx:1), [`frontend/src/lib/api.js`](frontend/src/lib/api.js:1).

## 11. Format check (PDF/DOCX/TXT) — planned, not yet executed

A format check through the real upload endpoint ([`POST /api/v1/documents/analyze`](backend/app/api/routes/analysis.py:161)) using the same frozen content across PDF/DOCX/TXT is **planned but not yet executed**. When executed:
- Use one representative cleaned policy text (e.g., `spotify_tos_in`) converted to PDF, DOCX, and TXT.
- Label generated conversions clearly as “format conversion from frozen snapshot” — **do not** describe a generated PDF as an official source PDF.
- Do not count format conversions as additional independent policy documents.
- Compare extraction and segmentation across formats; report any differences.
- Saved under `data/review/real_document_eval_v2/api_outputs/` with format suffix.

## 12. Retrieval failures — plan for manual completion

| document_id | Failure | Manual save path | New snapshot ID if content changes |
|---|---|---|---|
| `reddit_privacy` | JS shell (6 chars) | Save official PDF/text from https://www.reddit.com/policies/privacy-policy | `reddit_privacy_v2` if content differs from frozen |
| `notion_tos` | JS app shell | Save official PDF/text from https://www.notion.so/terms | `notion_tos_v2` if content differs |
| `notion_privacy` | JS/401 | Save official PDF/text from https://www.notion.so/privacy | `notion_privacy_v2` if content differs |
| `etsy_tos` | HTTP 403 | Manually save official PDF/text from https://www.etsy.com/legal/terms-of-use | `etsy_tos_v2` if content differs |
| `etsy_privacy` | HTTP 403 | Manually save official PDF/text from https://www.etsy.com/legal/privacy/ | `etsy_privacy_v2` if content differs |

Failed attempts are preserved in the manifest. Do not bypass access controls. New snapshot IDs assigned only when source content changes from the frozen version.

## 13. Conclusions and boundaries

- **What ran:** frozen candidate loaded and served; 12 official sources targeted; 10/12 snapshots fetched (2 blocked 403), 7/12 produced usable cleaned text and successful API analyses (2,455 clauses total). Saved raw responses, checksums, manifest, aggregate outputs, inspection, blind review sheets, and figures.
- **What passed (operational):** API returned structured responses with valid labels/counts/offsets and 0 span mismatches for all 7 successful analyses; timing recorded with definitions.
- **What failed/limited:** Reddit Privacy, Notion ToS/Privacy thin/JS extraction; Etsy ToS/Privacy blocked (403). No genuine PDF uploads exercised in this run (all collected as HTML/cleaned text submitted to `analyze-text`); format-conversion parser checks not executed as independent tests. Browser UI not visually verified.
- **Cannot yet conclude:** real-document classification accuracy, macro/weighted F1, per-class metrics, confusion, or Risky FP/FN — **requires authentic independent/adjudicated human labels**. Cannot claim legal risk ground truth, temporal generalization, unseen-service generalization, or production capacity from local timings. Do not rank companies by predicted Risky %.

## 14. Deliverables (this run)

- Reusable runner: [`scripts/run_real_document_evaluation_v2.py`](scripts/run_real_document_evaluation_v2.py:1)
- Source manifest: [`data/review/real_document_sources_v2.csv`](data/review/real_document_sources_v2.csv:1)
- Local ignored artifacts: `data/review/real_document_eval_v2/{snapshots,cleaned,api_outputs,review_sheets,figures,aggregate}/` (gitignored)
- Aggregate outputs: [`data/review/real_document_eval_v2/aggregate/run_summary.csv`](data/review/real_document_eval_v2/aggregate/run_summary.csv:1), [`run_summary.json`](data/review/real_document_eval_v2/aggregate/run_summary.json:1), [`extraction_segmentation_inspection.csv`](data/review/real_document_eval_v2/aggregate/extraction_segmentation_inspection.csv:1)
- This report: [`docs/REAL_DOCUMENT_EVALUATION.md`](docs/REAL_DOCUMENT_EVALUATION.md:1)

## 15. Exact commands to repeat

```bash
# from repo root; use frozen-serving venv
cd /home/142401034/tos-risk-flagging

# 0) (if needed) start backend on 8000 with frozen package
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
cd backend && nohup ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/termsguard-backend.log 2>&1 & cd ..

# 1) verify health / freeze context
curl -sS http://127.0.0.1:8000/api/v1/health
sha256sum models/releases/linear-svc-primary-v2/model.joblib models/releases/linear-svc-primary-v2/vectorizer.joblib

# 2) run full evaluation pipeline (collect → analyze → inspect → review-sheets → figures)
./.venv/bin/python scripts/run_real_document_evaluation_v2.py collect
./.venv/bin/python scripts/run_real_document_evaluation_v2.py analyze
./.venv/bin/python scripts/run_real_document_evaluation_v2.py inspect
./.venv/bin/python scripts/run_real_document_evaluation_v2.py review-sheets
python3 scripts/run_real_document_evaluation_v2.py figures   # or ./.venv/bin/python if matplotlib installed

# 3) inspect outputs
cat data/review/real_document_eval_v2/aggregate/run_summary.json
cat data/review/real_document_eval_v2/aggregate/extraction_segmentation_inspection.json
```

**Manual snapshot support (for blocked/thin docs):** place official HTML/PDF/text at `data/review/real_document_eval_v2/snapshots/reddit_privacy.*`, `notion_tos.*`, `notion_privacy.*`, `etsy_tos.*`, `etsy_privacy.*` and corresponding cleaned text in `data/review/real_document_eval_v2/cleaned/<document_id>.txt`, update [`data/review/real_document_sources_v2.csv`](data/review/real_document_sources_v2.csv:1) status/checksums, then rerun `analyze/inspect/review-sheets`. Do not bypass access controls.

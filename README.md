# TermsGuard

Review clause classifications in Terms of Service and Privacy Policies.

---

## Download

```bash
git clone <repository-url>
cd ToS-risk-flagging
```

---

## Start

### Python environment

From the repository root, create the project environment and install the shared training and serving dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

To run the backend regression suite:

```powershell
Set-Location backend
python -m pytest app\tests -q
```

To record the current selected-model outputs and a single local smoke timing:

```powershell
Set-Location ..
python scripts\baseline_smoke.py
```

To regenerate the data-quality and near-duplicate audits:

```powershell
python scripts\audit_data.py
python scripts\audit_near_duplicates.py
python scripts\create_splits.py
python scripts\verify_split_manifest.py
```

To regenerate the reproducible data audit and near-duplicate candidate list:

```powershell
python scripts\audit_data.py
python scripts\audit_near_duplicates.py
```

To regenerate the development-only EDA outputs (locked test rows are excluded):

```powershell
python scripts\run_eda.py
```

To reproduce the Phase 4 development-only comparisons:

```powershell
python scripts\run_model_benchmarks.py --protocol primary
python scripts\run_model_benchmarks.py --protocol clause
python scripts\run_grouped_cv_tuning.py
python scripts\run_lexical_feature_ablation.py
python scripts\evaluate_tuned_candidates.py
```

See [docs/MODEL_EXPERIMENTS_v1.md](docs/MODEL_EXPERIMENTS_v1.md) for methods, results, and limitations. These commands do not evaluate the locked test partition.

Development error and probability analyses use validation and grouped training folds only:

```powershell
python scripts\analyze_development_errors.py
python scripts\analyze_uncertainty.py
python scripts\verify_document_source_candidates.py
python scripts\fetch_document_source_candidates.py
python scripts\prepare_document_review_sheets.py
python scripts\prepare_document_review_segments.py
```

The fetch step stores raw snapshots and extracted review text under ignored `data/review/snapshots_v1/`; it records HTTP failures in the source registry. The segment preparation step creates blind reviewer copies for the initial three-service Terms of Service round. Independent full-document evaluation requires two human annotations and adjudication; see [docs/INDEPENDENT_DOCUMENT_EVALUATION.md](docs/INDEPENDENT_DOCUMENT_EVALUATION.md).

After both reviewers complete their separate sheets, compare agreement and create an adjudication queue with:

```powershell
python scripts\analyze_document_annotation_agreement.py
```

### Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Frontend runs at `http://localhost:3000`

Results are scoped to the current browser tab, with search, label filters, adjacent-clause context, and JSON/CSV export. The Methodology and Research Results pages describe the deployed model, development evidence, data limits, and intended use. This is educational screening, not legal advice.

---

## Notes

- No virtual environment required
- The ML model is integrated. Upload a document on the Analyze page to get clause-level risk predictions.
- This is an educational screening tool and does not provide legal advice.

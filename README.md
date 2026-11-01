# project name

Understand what you're agreeing to.

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
```

Independent full-document evaluation requires human annotations; see [docs/INDEPENDENT_DOCUMENT_EVALUATION.md](docs/INDEPENDENT_DOCUMENT_EVALUATION.md).

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

---

## Notes

- No virtual environment required
- The ML model is integrated. Upload a document on the Analyze page to get clause-level risk predictions.
- This is an educational screening tool and does not provide legal advice.

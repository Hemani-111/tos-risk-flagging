# TermsGuard

Review clause classifications in Terms of Service and Privacy Policies.

TermsGuard extracts clauses from a policy document and classifies each clause as Safe, Neutral, or
Risky using a trained machine-learning model. It is an educational screening tool, not legal advice,
and a missing Risky prediction does not establish that a document is safe.

---

## Project structure

```
README.md
requirements.txt
requirements-experiments.txt
docker-compose.yml

data/                  raw / processed / splits / review  (raw data and snapshots are Git-ignored)
src/                   data_loader, preprocessing, features, splitting, evaluation
models/
  naive_bayes/         Multinomial Naive Bayes
  logistic_regression/ Logistic Regression
  svm/                 Linear SVM (+ RBF SVM variant)
  decision_tree/       Decision Tree
  random_forest/       Random Forest
  knn/                 K-Nearest Neighbours
  gradient_boosting/   HistGradientBoosting
  production/          linear-svc-primary-v2 serving package
results/
  comparison/          eight-method comparison (CSV, Markdown, confusion matrices)
  experiments/         canonical run evidence
  locked_evaluation_v1/# one-time locked test evaluation (frozen)
notebooks/
  data_preparation.ipynb
  exploratory_analysis.ipynb
  model_comparison.ipynb
scripts/
  prepare_data.py
  run_comparison.py
  export_model.py
  check_parity.py
backend/               FastAPI application + tests
frontend/              Next.js application
tests/
docs/                  DATASET.md, EXPERIMENT_PROTOCOL.md, FINAL_REPORT.md, MODEL_CARD.md, archive/
```

---

## Start

### Python environment

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Backend

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://127.0.0.1:8000`. Model readiness:
`http://127.0.0.1:8000/api/v1/health`

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Frontend runs at `http://127.0.0.1:3000`.

---

## Run the eight-method comparison

```powershell
python scripts\run_comparison.py --protocol both
```

Writes per-protocol results to `results/comparison/{primary,clause}/`:
- `comparison.csv` — machine-readable metrics for all eight methods
- `comparison.md` — readable comparison table
- `{model}_confusion_matrix.csv` — per-model confusion matrices
- `run_metadata.json` — run identity, data/split identity, environment

Each model folder under `models/` contains `README.md`, `config.json`, `code.ipynb`,
`results/{primary,clause}/`, and `artifacts/` (fitted development pipeline).

---

## Verify

```powershell
# Backend tests
Set-Location backend
python -m pytest app\tests -q

# Offline vs API prediction parity
Set-Location ..
python scripts\check_parity.py

# Data / split integrity
python scripts\verify_split_manifest.py
```

---

## Model scope

Compared fairly on the same development data and splits:

1. Multinomial Naive Bayes
2. Logistic Regression
3. Linear SVM (production model)
4. RBF SVM
5. Decision Tree
6. Random Forest
7. K-Nearest Neighbours
8. Gradient Boosting (HistGradientBoosting)

Not in scope: Complement Naive Bayes, voting/stacking ensembles, sentence embeddings,
K-means clustering, PCA on embeddings, calibration/abstention experiments.

---

## Academic deliverables

- `docs/FINAL_REPORT.md` — final report
- `docs/MODEL_CARD.md` — model card
- `docs/DATASET.md` — dataset documentation
- `docs/EXPERIMENT_PROTOCOL.md` — experiment protocol
- `docs/archive/` — historical mid-semester submission materials
- Frontend pages: Home, Analyze, Results, Research (model comparison), About (methodology)

This is an educational project. Model labels are predictions from case-derived annotations,
not legal judgments.

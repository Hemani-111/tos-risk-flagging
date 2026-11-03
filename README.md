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

Backend runs at `http://127.0.0.1:8000`. Check model readiness at `http://127.0.0.1:8000/api/v1/health`.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Frontend runs at `http://127.0.0.1:3000`

Results are scoped to the current browser tab, with search, label filters, adjacent-clause context, full extracted-text highlights, unclassified source text, and JSON/CSV export. Use **Print / Save PDF** to print the review report. The Methodology and Research Results pages describe the deployed model, development evidence, data limits, and intended use. This is educational screening, not legal advice.

See [docs/DEPLOYMENT_READINESS_v1.md](docs/DEPLOYMENT_READINESS_v1.md) for clean-environment verification, dependency audit status, local performance samples, and deployment items that require a hosting target.
See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for the local course demonstration, model rollback, and container resumption steps.

---

## Notes

- Use the Python environment above; Python 3.11 is required for the pinned project dependencies.
- The ML model is integrated. Upload a document on the Analyze page to get clause-level risk predictions.
- This is an educational screening tool and does not provide legal advice.
# Reproduce expanded experiments and frozen package

Install optional local encoder dependencies when reproducing the embedding experiment:

```powershell
python -m pip install -r requirements-experiments.txt
python scripts\embed_sentence_clauses.py --batch-size 16
python scripts\run_expanded_classical_tuning.py --protocol both
python scripts\run_remaining_feature_experiments.py
python scripts\run_ensemble_calibration_clusters.py
python scripts\analyze_linear_feature_stability.py
python scripts\build_experiment_registry.py
```

These experiment scripts use only included train/validation records through `load_development_bundle`. The checked-in registry records the completed one-time locked evaluation. Do not rerun the locked evaluation for model selection; see [Candidate Freeze](docs/FINAL_CANDIDATE_FREEZE.md) and [Locked Test Evaluation](docs/LOCKED_TEST_EVALUATION_v1.md).

## Find each model

Each classifier and analysis experiment has a clearly named folder with a runnable entry point, configuration, notebook, results, and (where practical) a saved artifact:

| Method | Folder | Entry point |
|--------|--------|-------------|
| Decision Tree | `models/decision_tree/` | `python models/decision_tree/run.py --protocol both` |
| Random Forest | `models/random_forest/` | `python models/random_forest/run.py --protocol both` |
| Gradient Boosting | `models/gradient_boosting/` | `python models/gradient_boosting/run.py --protocol both` |
| KNN | `models/knn/` | `python models/knn/run.py --protocol both` |
| Complement Naive Bayes | `models/complement_naive_bayes/` | `python models/complement_naive_bayes/run.py --protocol both` |
| Voting Ensemble | `models/voting_ensemble/` | `python models/voting_ensemble/run.py --protocol both` |
| Stacking Ensemble | `models/stacking_ensemble/` | `python models/stacking_ensemble/run.py --protocol both` |
| Sentence Embeddings + Logistic Regression | `models/sentence_embeddings_logistic_regression/` | `python models/sentence_embeddings_logistic_regression/run.py --protocol both` |
| Sentence Embeddings + Linear SVM | `models/sentence_embeddings_linear_svm/` | `python models/sentence_embeddings_linear_svm/run.py --protocol both` |

Each folder contains `README.md` (what/why/results/limitations), `run.py` (thin entry point calling shared code), `config.json` (reproducible settings), `code.ipynb` (educational notebook), `results/{primary,clause}/` (metrics, predictions, confusion matrices), and `artifacts/` (fitted development pipeline after `--save-artifact`).

Analysis experiments are under `results/analysis/{feature_combinations,dimensionality_reduction,clustering,learning_curves,calibration}/` with the same structure.

The consolidated experiment inventory is in `docs/EXPERIMENT_INVENTORY.md` with exact paths, scores, and status for every method.

To rebuild the serving package:
```powershell
python scripts\build_frozen_model_package.py
```

To rebuild the serving package after a source or environment change, follow the committed freeze and inspect the new hashes before switching runtime configuration:

```powershell
python scripts\build_frozen_model_package.py
```

# Academic deliverables

[Final Report Draft](docs/FINAL_REPORT_v1.md), [Model Card](docs/MODEL_CARD.md), [Candidate Freeze](docs/FINAL_CANDIDATE_FREEZE.md), [Locked Test Evaluation](docs/LOCKED_TEST_EVALUATION_v1.md), and [Presentation/Demo Storyboard](docs/PRESENTATION_STORYBOARD_v1.md). Independent complete-document evaluation remains pending authentic reviewer labels and adjudication.

Blind review setup and source coverage are described in [Independent Document Evaluation](docs/INDEPENDENT_DOCUMENT_EVALUATION.md). Run `python scripts\verify_document_review_coverage.py` to verify available snapshot hashes, clause offsets, segmentation coverage, and reviewer-sheet alignment. It writes non-source-text metrics to `results/document_review_coverage_v1.json`; policy snapshots and reviewer content remain ignored.

For the provisional course narrative, see [Midsemester to Endsemester Progress](docs/MIDSEM_TO_ENDSEM_PROGRESS.md) and [Team Preparation Notes](docs/TEAM_PREPARATION_NOTES.md). Local startup and demonstration instructions are in [Deployment Guide](docs/DEPLOYMENT_GUIDE.md).

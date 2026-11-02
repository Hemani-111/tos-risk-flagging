# Model card: current serving classifier

## Model identity

The application loads `linear-svc-primary-v2` from `models/releases/linear-svc-primary-v2/`. It is word unigram/bigram TF-IDF followed by `sklearn.svm.LinearSVC(C=1, class_weight="balanced")`. The prior RBF SVC remains at `models/selected_model/` as a rollback artifact and can be selected with `MODEL_DIR`.

## Intended use

Educational triage of English Terms of Service and Privacy Policy clauses. Predictions can help a reader decide what to inspect. They are not legal advice, a legal-risk determination, or a guarantee that a policy is safe.

## Labels and training data

The project benchmark derives Safe, Neutral, and Risky labels from ToS;DR case-associated point annotations. The raw source reconstructs to 22,497 rows; the scoped English conflict-free benchmark contains 19,189 rows. Labels may reflect case context beyond the quoted excerpt. See [Dataset Card](DATASET_CARD.md).

## Evaluation status

The model was selected on fixed grouped training folds and validation under the primary unseen-service protocol, then frozen before test scoring. The one-time locked-test results are macro F1 0.8358 / Risky precision 0.8229 / Risky recall 0.8287 on the 2,585-row primary test; the secondary duplicate-aware test reports 0.8144 / 0.7922 / 0.8117 on 2,602 rows. Group-bootstrap intervals, per-class metrics and the loader boundary disclosure are in [Locked Test Evaluation](LOCKED_TEST_EVALUATION_v1.md). The test is not described as untouched: earlier development runs materialized its text/labels in memory via the old shared loader, without calculating or reviewing test metrics. The test scores were not used for selection.

Independent complete-document evaluation still awaits two authentic reviewer sheets and adjudication; clause-level test results do not establish whole-policy performance.

## Limitations and risks

- Arbitrary sentences, whole-policy performance, and non-English text are not independently validated.
- A Safe prediction is not assurance of benign terms; false positives and false negatives occur.
- Source labels are not expert legal judgments and can be context-dependent.
- Policies change, and no update-monitoring or legal interpretation is supplied.
- Raw probabilities from the experimental Logistic Regression are not calibrated and are not a confidence feature of this model card.

## Versioning and reproducibility

The package metadata pins artifact SHA-256 values, Python/scikit-learn/NumPy/joblib versions, training data/split hashes, freeze commit, and training point-ID/text hashes. Training used 13,439 included primary training rows and 44,489 TF-IDF features. Prediction is deterministic and emits a class label only. The package is built with `python scripts/build_frozen_model_package.py`; see [Project Context](../PROJECT_CONTEXT.md). The dataset source license is unspecified; confirm rights before redistribution.

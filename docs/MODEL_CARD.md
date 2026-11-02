# Model card: current serving classifier

## Model identity

The application currently loads the pre-existing serialized classifier and vectorizer from the repository's model artifacts. Phase 4 experiments did not select or promote a replacement. The tuned Linear SVM described in [Model Experiments](MODEL_EXPERIMENTS_v1.md) is an offline development candidate, not the model currently served by the application.

## Intended use

Educational triage of English Terms of Service and Privacy Policy clauses. Predictions can help a reader decide what to inspect. They are not legal advice, a legal-risk determination, or a guarantee that a policy is safe.

## Labels and training data

The project benchmark derives Safe, Neutral, and Risky labels from ToS;DR case-associated point annotations. The raw source reconstructs to 22,497 rows; the scoped English conflict-free benchmark contains 19,189 rows. Labels may reflect case context beyond the quoted excerpt. See [Dataset Card](DATASET_CARD.md).

## Evaluation status

Development experiments use fixed service-aware and duplicate-aware splits. The locked test partitions remain unevaluated. Validation metrics in [Model Experiments](MODEL_EXPERIMENTS_v1.md) refer to the offline tuned candidate and must not be attributed to this existing serving artifact. Independent complete-document evaluation has no human labels yet.

## Limitations and risks

- Arbitrary sentences, whole-policy performance, and non-English text are not independently validated.
- A Safe prediction is not assurance of benign terms; false positives and false negatives occur.
- Source labels are not expert legal judgments and can be context-dependent.
- Policies change, and no update-monitoring or legal interpretation is supplied.
- Raw probabilities from the experimental Logistic Regression are not calibrated and are not a confidence feature of this model card.

## Versioning and reproducibility

The serving artifact files remain unchanged. Record their hashes and the runtime package versions with each future release. Reproduction scripts and split provenance are listed in [Project Context](../PROJECT_CONTEXT.md). The dataset source license is unspecified; confirm rights before redistribution.

# Phase 5 development error review

## Scope and candidate

This review uses validation predictions only. It examines the tuned, balanced Linear SVM (C=1, word unigram/bigram TF-IDF) under both frozen protocols. It does not inspect the locked test rows. The dataset target is case-derived; a mismatch with an excerpt is not necessarily a model error against independent legal judgment.

| Protocol | Validation rows | Errors | Error rate | Risky false positives | Risky false negatives | SVM/LR disagreements |
|---|---:|---:|---:|---:|---:|---:|
| Primary unseen service | 2,658 | 465 | 17.5% | 182 | 150 | 71 |
| Secondary duplicate-aware clause | 2,607 | 460 | 17.6% | 197 | 134 | 80 |

Largest primary confusion directions were Neutral→Risky (107), Risky→Safe (83), and Safe→Risky (75). The secondary directions were Neutral→Risky (113), Safe→Risky (84), and Risky→Neutral (72). Full confusion counts, prediction rows and deterministic review examples are in `results/error_analysis/v1/`.

## Initial qualitative observations

The deterministic review queue contains examples for each true/predicted class pair. A first inspection suggests several distinct issues for human review:

- Neutral clauses describing legal disclosure, non-personal partner sharing, platform moderation, or limited service operation can contain words associated with risky annotations.
- Risky examples include broad discretion, unilateral changes, jurisdiction/class-action restrictions, and collection disclosures that are not always obvious from local words alone.
- Some excerpts look structurally incomplete or like headings/references (for example, a cookie-policy cross-reference). This may reflect source segmentation or the case-level annotation target rather than ordinary classification.
- Linear SVM and Logistic Regression disagree on 71 primary and 80 secondary validation examples; these are useful side-by-side review candidates, not proof that either is correct.

Keyword taxonomy flags are navigation aids only. They do not explain causality or validate a label. Reviewers should read context and record whether each apparent error is actually a case-derived target mismatch, missing context, ambiguous wording, segmentation, or model behavior. No examples were relabeled or removed.

## Probability and selective review analysis

Balanced Logistic Regression (C=10) was evaluated because it provides class scores. Probability fitting uses TF-IDF fitted on training only; grouped out-of-fold predictions are generated from the three fixed training folds. The raw probabilities are not calibrated.

| Split | Accuracy | Multiclass Brier (lower better) | Log loss (lower better) | Top-label ECE, 10 bins |
|---|---:|---:|---:|---:|
| Training out-of-fold | 0.835 | 0.240 | 0.437 | 0.007 |
| Validation | 0.821 | 0.253 | 0.458 | 0.023 |

ECE is a top-label summary and can hide class-specific calibration problems; the validation reliability plot shows some middle-confidence bins below the diagonal. Do not present these estimates as validated confidence for arbitrary documents.

Confidence thresholds were selected from training out-of-fold predictions to target coverage and then evaluated on validation:

| Target OOF coverage | Threshold | Validation coverage | Validation error among accepted |
|---:|---:|---:|---:|
| 80% | 0.672 | 80.9% | 10.7% |
| 90% | 0.551 | 91.0% | 14.2% |
| 95% | 0.494 | 95.7% | 16.2% |

This is a development trade-off for review routing, not a deployed abstention policy. Coverage and error can shift for new services, complete documents, and fragments outside the benchmark.

## Independent document set status

No frozen local snapshots or human annotations are available yet. The ToSDR excerpt labels cannot stand in for complete-document ground truth. Eight official source candidates from four services absent from the full benchmark are listed in `data/review/document_sources_candidates_v1.csv`. `docs/INDEPENDENT_DOCUMENT_EVALUATION.md` defines the review procedure and `data/review/document_annotations_template_v1.csv` is a blank annotation template. Full-document performance remains unmeasured pending snapshots and human annotations.

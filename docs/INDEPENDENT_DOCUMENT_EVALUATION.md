# Independent complete-document evaluation protocol

## Purpose

Measure extraction, segmentation, clause predictions, and missed risky material on complete Terms of Service or Privacy Policy documents from services absent from the training data. This evaluation is separate from the ToSDR clause benchmark and must not be described as expert legal ground truth.

## Selection and provenance

1. Use the eight candidate sources in `data/review/document_sources_candidates_v1.csv`: consumer terms and privacy policies for Anthropic, Mistral AI, Perplexity AI, and You.com. These services were checked and do not appear in the full conflict-free ToSDR benchmark. The fixed candidate list was chosen without model results.
2. Record the official source URL, document title/type, retrieval date, version/effective date if shown, local snapshot path, and SHA-256. Keep raw documents out of Git unless redistribution rights are confirmed.
3. Freeze the source list and snapshots before annotation. Keep a development document subset separate from any final document evaluation subset.
4. Do not select documents based on model predictions or known model successes.

The official sources were checked on 2 November 2026: [Anthropic Legal Center](https://www.anthropic.com/legal), [Mistral AI consumer terms](https://legal.mistral.ai/terms/row-consumer-terms/) and [privacy policy](https://legal.mistral.ai/terms/privacy-policy/), [Perplexity terms](https://www.perplexity.ai/hub/legal/terms-of-service) and [privacy policy](https://www.perplexity.ai/hub/legal/privacy-policy), and [You.com terms](https://about.you.com/legal/terms) and [privacy policy](https://you.com/privacy). Anthropic listed Consumer Terms dated 8 October 2025 and Privacy Policy dated 10 September 2026; Mistral listed rest-of-world consumer terms effective 12 October 2026 and privacy policy effective 3 September 2026; Perplexity listed Terms updated 23 January 2026 and Privacy Notice updated 23 October 2026; You.com showed 27 August 2024 on the terms page and a Privacy Policy updated 22 September 2026. Record versions again when local snapshots are obtained because these pages can change.

## Annotation

- Two reviewers independently examine the same document text and identify policy clauses that merit attention under the project's three-class rubric. Preserve exact source spans and surrounding context. Record reviewer ID, label, risk type, uncertainty, and rationale in `data/review/document_annotations_template_v1.csv`.
- Use only `Risky`, `Neutral`, or `Safe` when the rubric supports one; use `Needs adjudication` in the annotation note for unresolved cases, not as a model class.
- Compare reviewer agreement before reconciliation. Reconcile disagreements with a written decision and preserve both original judgments. Report agreement and the number of adjudicated spans.
- The annotation is a student-reviewed reference. It is not legal advice or a claim of expert legal correctness.

## Evaluation and reporting

Report separately: extraction completeness (including pages/sections skipped), segmentation coverage, clause-level precision/recall/F1 on adjudicated spans, missed annotated risky spans, and document-level false alarms. Manually review missed risky sections. Do not interpret an aggregate document score as a probability of legal compliance.

Do not tune model features or thresholds against a frozen final document set. If development documents reveal a parser issue, fix it using development examples and retain an untouched final set.

## Current status

The repository has a fixed candidate source list but no frozen local snapshots or human annotations. Confirm the correct consumer-facing product/region, save the documents locally, and fill snapshot version/hash fields before annotation. Do not generate synthetic labels or use model predictions as reference labels. Document-level evaluation remains pending until reviewers supply completed annotations and source records.

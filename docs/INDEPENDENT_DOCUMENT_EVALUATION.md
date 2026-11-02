# Independent complete-document evaluation protocol

## Purpose

Measure extraction, segmentation, clause predictions, and missed risky material on complete Terms of Service or Privacy Policy documents from services absent from the training data. This evaluation is separate from the ToSDR clause benchmark and must not be described as expert legal ground truth.

## Selection and provenance

1. The frozen set currently has six documents: consumer terms and privacy policies for Anthropic, Mistral AI, and You.com. These services were checked and do not appear in the full conflict-free ToSDR benchmark. Perplexity terms/privacy remain in the source registry but this environment returned HTTP 403 for both snapshots; they are not part of the frozen set.
2. Record the official source URL, document title/type, retrieval date, version/effective date if shown, local snapshot path, and SHA-256. Keep raw documents out of Git unless redistribution rights are confirmed.
3. Freeze the source list and snapshots before annotation. Keep a development document subset separate from any final document evaluation subset.
4. Do not select documents based on model predictions or known model successes.

The official sources were checked on 2 November 2026: [Anthropic Legal Center](https://www.anthropic.com/legal), [Mistral AI consumer terms](https://legal.mistral.ai/terms/row-consumer-terms/) and [privacy policy](https://legal.mistral.ai/terms/privacy-policy/), [Perplexity terms](https://www.perplexity.ai/hub/legal/terms-of-service) and [privacy policy](https://www.perplexity.ai/hub/legal/privacy-policy), and [You.com terms](https://about.you.com/legal/terms) and [privacy policy](https://you.com/privacy). Anthropic listed Consumer Terms dated 8 October 2025 and Privacy Policy dated 10 September 2026; Mistral listed rest-of-world consumer terms effective 12 October 2026 and privacy policy effective 3 September 2026; Perplexity listed Terms updated 23 January 2026 and Privacy Notice updated 23 October 2026; You.com showed 27 August 2024 on the terms page and a Privacy Policy updated 22 September 2026. Record versions again when local snapshots are obtained because these pages can change.

## Annotation

- For the initial annotation round, two reviewers independently examine the same three consumer Terms of Service documents (Anthropic, Mistral AI, and You.com). Privacy snapshots are frozen for a later round. Review the complete text and identify policy clauses that merit attention; the prepared clause rows are navigation aids and do not replace a full-document pass. A reviewer-added-span row is provided for material the segmenter missed.
- Use the blind content sheets `reviewer_a_segments_v1.csv` and `reviewer_b_segments_v1.csv` under the ignored `data/review/snapshots_v1/` folder. `data/review/annotator_a_sheet_v1.csv` and `_b_...` are tracked metadata stubs only. The content sheets include no model predictions and are excluded from Git because they reproduce source text.
- Offsets refer to character positions in each extracted `.txt` snapshot, not PDF page coordinates. `scripts/verify_document_review_coverage.py` checks all six available snapshot hashes, sheet alignment, exact clause slices, and segmentation coverage. Clause-character coverage is 90.9% for Anthropic terms, 98.5% for Anthropic privacy, 96.5% for Mistral terms, 91.9% for Mistral privacy, 98.1% for You.com terms, and 97.0% for You.com privacy; unsegmented gaps remain part of the full-document review. The current API PDF parser extracts 28,946 characters from the Anthropic terms PDF while the frozen review text has 29,319 characters; the strings differ. Anthropic privacy also differs (40,423 parser-extracted characters). Blind-sheet offsets apply to the frozen review text, not a fresh API PDF extraction; investigate these discrepancies before claiming PDF upload parity. HTML review text is also a frozen visible-text extraction. Preserve exact spans and surrounding context. Record reviewer ID, label, risk type, uncertainty, and rationale.
- Apply this operational adaptation of the project’s three classes: **Risky** when the clause materially limits user rights, privacy, control, or fair treatment; **Safe** when it affirmatively provides a user-protective right or safeguard; **Neutral** when it is informational or does not support either judgment. Consider the full clause and context, not isolated terms. ToS;DR's source case ratings include good, neutral, bad, and blocker; this project collapses material adverse cases into Risky and protective cases into Safe for clause-level review. See the [ToS;DR rating definitions](https://github.com/tosdr/docs/blob/master/phoenix/README.md). This rubric is for consistent student review, not legal advice.
- Use only `Risky`, `Neutral`, or `Safe` when the rubric supports one; use `Needs adjudication` in the annotation note for unresolved cases, not as a model class.
- Compare reviewer agreement before reconciliation. Reconcile disagreements with a written decision and preserve both original judgments. Report agreement and the number of adjudicated spans.
- Once both sheets are complete, run `python scripts/analyze_document_annotation_agreement.py`. It validates aligned pre-segmented rows, reports raw agreement and Cohen's kappa, and writes a text-bearing disagreement queue under the ignored review folder. Adjudicate that queue manually; the script does not assign adjudicated labels or measure model performance.
- The annotation is a student-reviewed reference. It is not legal advice or a claim of expert legal correctness.

## Evaluation and reporting

Report separately: extraction completeness (including pages/sections skipped), segmentation coverage, clause-level precision/recall/F1 on adjudicated spans, missed annotated risky spans, and document-level false alarms. Manually review missed risky sections. Do not interpret an aggregate document score as a probability of legal compliance.

Do not tune model features or thresholds against a frozen final document set. If development documents reveal a parser issue, fix it using development examples and retain an untouched final set.

## Current status

Six local snapshots and text extracts are available under the ignored `data/review/snapshots_v1/` folder. Their hashes, extraction paths, and retrieval dates are in the source registry. Two blind annotation sheets covering 719 current-segmenter clauses across the three consumer ToS are generated there; tracked metadata stubs cover all six frozen documents. The snapshots and content sheets are omitted from Git because they may be copyrighted. `results/document_review_coverage_v1.json` records source coverage and verifies both reviewer sheets have identical clause IDs, valid offsets, and no labels. Do not generate synthetic labels or use model predictions as reference labels. Document-level evaluation remains pending until reviewers return completed sheets and adjudication notes.

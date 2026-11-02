# Presentation and demonstration storyboard

**Working draft for Phase 9.** The course slide count and marking rubric are not yet recorded, so this is a content storyboard, not a final slide deck. Adapt it once those constraints are known.

## Suggested narrative

1. **Problem and intended use** — long policies are hard to scan; the tool helps prioritize human attention. State plainly that it does not provide legal advice.
2. **What the labels mean** — show the Safe/Neutral/Risky mapping and explain that labels come from ToS;DR case-associated excerpts, not independent legal judgments.
3. **Data quality and split design** — 22,497 reconstructed rows; 19,189 in the scoped benchmark; duplicates/conflicts; contrast unseen-service with duplicate-aware splits. Keep the locked test sealed.
4. **Methods and strongest evidence** — grouped CV and validation results for Linear SVM word unigram/bigram TF-IDF, with macro F1 and Risky precision/recall. Mention lexical ablation did not materially improve results.
5. **Errors, uncertainty, and limits** — show false positives/negatives and raw-probability caveat. Explicitly state the document-review study has no human labels yet, so full-policy performance is unknown.
6. **Application and next work** — demonstrate upload/paste, filters, clause context/page ranges, and export; end with annotation, locked-test evaluation, Docker, and deployment gates.

This ordering is a suggestion, not an assertion of the required deck length. Do not display historical 85% accuracy as a comparable result or label validation metrics as test metrics.

## Local demonstration run sheet

1. Start the backend and frontend using the documented local setup; confirm the health endpoint and model load before presenting.
2. Paste a short, prepared normal example and show predictions, class filters, context, and export.
3. Upload a selectable-text PDF and point out page ranges. Avoid a scanned PDF because OCR is not implemented.
4. Show a difficult or ambiguous example from the prepared development review queue, explain that model output is a prompt for review, and avoid calling its reference label legal truth.
5. If showing probabilities or uncertainty, identify them as raw exploratory estimates; no calibrated confidence or automatic abstention is deployed.
6. Show a supported file-error case (for example, an encrypted PDF) to demonstrate a clear failure response.
7. Close with what is and is not verified: local test/build checks pass, but Docker startup and production hosting are unverified; independent full-document labels are pending.

Choose specific examples only from approved local fixtures or validation review exports, never from the locked test set. Rehearse the flow after the final environment is available.

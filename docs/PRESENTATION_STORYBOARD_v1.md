# Provisional six-slide presentation storyboard

**Provisional:** no course rubric or final slide-count requirement is recorded. This is six-slide content ready to adapt when the rubric arrives; the test results below are actual post-freeze results. Do not describe the test set as untouched: the loader boundary incident is disclosed on slide 5.

## Slide 1 — The problem and intended use

**Title:** Terms of Service Risk Flagging Using Machine Learning

**Message:** Long policies are difficult to scan. This tool highlights clauses for human review; it does not decide whether a policy is legally safe.

**Visual:** one policy page excerpt alongside a highlighted clause and the three labels: Safe, Neutral, Risky.

**Speaker notes:** Labels come from ToS;DR case-associated excerpts, not independent legal judgments. The system classifies clauses, not whole-policy legality.

## Slide 2 — Data and quality controls

**Message:** A larger reconstructed source was narrowed into a documented benchmark, with conflicts and related examples handled explicitly.

**Evidence:** 22,497 reconstructed rows; 19,189-row scoped English conflict-free benchmark; 23 conflicting normalized groups (52 rows) quarantined.

**Visual:** source → language/conflict filtering → two grouped split protocols.

**Speaker notes:** Primary is unseen-service generalization; secondary is duplicate-aware clause generalization. Their results answer different questions and should not be pooled.

## Slide 3 — Methods and selection

**Message:** Sparse lexical features with a linear SVM were strongest among the tested practical options.

**Evidence:** Word unigram/bigram TF-IDF + class-weighted LinearSVC, C=1; primary grouped-CV macro F1 0.832 (fold SD 0.003), validation macro F1 0.820; secondary grouped-CV macro F1 0.839 (SD 0.002), validation macro F1 0.819. Macro F1 is the registered primary metric; Risky precision and recall are reported with it.

**Visual:** concise grouped-CV and validation comparison across both protocols, clearly labelled by stage.

**Speaker notes:** Character features, MiniLM embeddings, dense-reduction classical models, ensembles, and stacking did not displace lexical TF-IDF. The embedding encoder was local and revision-pinned. CV spread is standard deviation across fixed grouped folds, not a confidence interval.

## Slide 4 — Locked-test results

**Message:** After freezing the candidate, each protocol was scored once on its locked partition.

| Protocol | Test macro F1 | Risky precision | Risky recall |
|---|---:|---:|---:|
| Primary unseen-service | 0.8358 | 0.8229 | 0.8287 |
| Secondary duplicate-aware clause | 0.8144 | 0.7922 | 0.8117 |

**Visual:** the table plus primary/secondary labels; do not combine values into one score.

**Speaker notes:** These are annotated-clause results, not whole-policy results or legal accuracy. Risky false negatives remain: 147 primary and 161 secondary.

## Slide 5 — Errors, uncertainty, and limits

**Message:** Results support a clause-triage aid with clear limits, not automated legal conclusions.

**Evidence/caveats:** sigmoid calibration was evaluated as an internal diagnostic; no automated abstention or confidence percentage is deployed. Three frozen Terms snapshots have 723 blind clause rows and no reviewer labels yet. Segment coverage ranges from 93.3% to 98.1% of extracted-text characters; gaps remain visible and unclassified.

**Required disclosure:** early development code loaded the full source table before filtering development partitions in memory. It produced no test metric or summary and did not inform selection. This loader boundary incident means the test is not described as untouched. The candidate was frozen before its one-time test scoring, and no tuning followed.

## Slide 6 — Application and next steps

**Message:** The local app keeps the full extracted text visible and maps clause findings back to source offsets.

**Demo:** paste text → analyze → filter/search clauses → select a finding to inspect its highlighted source → export/print. Optionally upload a selectable-text PDF and show page ranges; OCR for scanned PDFs is not enabled.

**Close with gates:** collect two independent human review sheets and adjudication; perform Docker startup verification when the engine is available; adapt slides to the rubric; complete manual browser accessibility review and choose a production host only if needed.

## Local demonstration run sheet

### Before presenting

1. Start from the repository root and confirm the local Python environment and frontend dependencies are installed.
2. Start API and frontend using [the local deployment guide](DEPLOYMENT_GUIDE.md); verify API health at `http://127.0.0.1:8000/health` and frontend at `http://127.0.0.1:3000`.
3. Confirm the API reports model version `linear-svc-primary-v2`. Keep policy source snapshots local; they are ignored by Git.
4. Use an approved short input or local sample, not a locked-test row. Prepare a selectable-text PDF only if you need to show PDF page ranges.

### Live flow

1. Paste or upload a document and explain that the model classifies extracted clauses.
2. Show the full extracted-text view: highlighted clauses, unclassified gaps, and coverage.
3. Filter/search findings and select one to navigate between clause result and source excerpt.
4. Export JSON/CSV or print/save the readable report as PDF.
5. If time permits, show a clear unsupported-input error (encrypted or scanned PDF) and explain the limitation.
6. End with test-stage results and the authentic human-review gate. Do not frame a missing Risky prediction as proof of safety.

### Evidence status

Backend suite, changed-file Ruff, frontend lint/build, split verification, local API startup, and registry generation have passed in recorded runs. Docker startup and screenshot-driven browser review remain unverified. The computer-use helper stopped because it could not resolve the active Windows browser URL safely. See `REMAINING_WORK_STATUS.md` for the loader incident and other gates.

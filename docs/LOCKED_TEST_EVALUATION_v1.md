# Frozen candidate evaluation

**Evaluated:** 3 November 2026  
**Candidate freeze:** commit `c68fdcef9310007477d8245508ee2e623bc364af` (`docs/FINAL_CANDIDATE_FREEZE.md`)  
**Evaluation code commit:** `1f4a5c1`  
**Dataset SHA-256:** `cee557cc927d754cf17675154ed5e1e32eee2fdb9af6700c526e62cd66969f8c`  
**Candidate:** word unigram/bigram TF-IDF + `LinearSVC(C=1, class_weight="balanced")`  
**Primary metric:** macro F1; Risky precision and recall are reported alongside it.

## Test results

| Protocol | Test clauses | Macro F1 | Accuracy | Risky precision | Risky recall | Risky FP | Risky FN | Group-bootstrap 95% percentile interval for macro F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Primary unseen-service | 2,585 | 0.8358 | 0.8395 | 0.8229 | 0.8287 | 153 | 147 | 0.8205–0.8496 |
| Secondary duplicate-aware clause | 2,602 | 0.8144 | 0.8190 | 0.7922 | 0.8117 | 182 | 161 | 0.7989–0.8301 |

The primary test contained 211 service groups; the secondary test contained 2,552 normalized text groups. Intervals use 2,000 non-stratified cluster-bootstrap replicates, sampling whole test groups with replacement (seed 20261103). These intervals describe variation across sampled test groups; they are not guarantees for future deployment or legal decisions.

Per-class precision/recall/F1/support, confusion matrices, row-level predictions, fit and inference timings, split hashes, and evaluation registry are stored under `results/locked_evaluation_v1/`. The evaluator refuses a repeat for a protocol already recorded in that registry.

## Boundary disclosure and interpretation

The test scores were first calculated after the written candidate freeze and were not used for tuning or candidate selection. As disclosed in the freeze, earlier development attempts loaded the full source CSV through the old shared loader before selecting only development folds in memory. Those attempts produced no test metric or summary and did not inform selection, but this is a loader boundary incident. Accordingly, the test is not described as untouched. The final score is reported transparently as the first scored test evaluation after that incident.

Primary test performance is higher than its validation macro F1 (0.8201); the secondary test score (0.8144) is slightly below its validation score (0.8195). Both test protocols measure annotated clause classification, not complete-policy understanding. The corpus is case-derived and the two protocols answer different generalization questions; do not pool their scores. Risky misses remain (147 primary, 161 secondary), so the application must retain review framing and must not claim that a policy is safe.

This evaluation does not replace independent full-document evaluation. Two authentic reviewer annotations and adjudication remain pending for the six frozen local policy snapshots.

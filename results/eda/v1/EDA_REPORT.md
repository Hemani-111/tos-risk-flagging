# Phase 3 EDA v1

**Scope:** included primary-protocol training and validation rows only (N=16,097); locked test rows were excluded.

## Questions and observations

- **Is the sample balanced?** Risky: 5,266 (32.7%), Neutral: 6,773 (42.1%), Safe: 4,058 (25.2%). This is the curated English excerpt sample, not population prevalence.
- **Which topics carry which annotations?** `topic_label_counts.csv` and `topic_label_composition.png` report counts and within-topic shares. Topic labels are attached retrospectively and cannot be used for arbitrary uploads.
- **Does excerpt complexity vary by label?** `complexity_by_label.csv` reports length, word/sentence proxies, and a rough readability score. These are descriptive associations, not causal effects; the syllable estimate is heuristic.
- **Which phrases are associated with labels?** `class_associated_ngrams.csv` and `class_associated_phrases.png` rank development-only word unigrams/bigrams by smoothed log odds. Negation was retained. Association reflects case-derived annotation and context.
- **Are some services overrepresented?** 1,358 services appear in development. Top 1/10/50 services contribute 0.5%/4.2%/16.7% of rows. The concentration curve describes sample collection, not real-world service risk.
- **What is hard to classify?** No model is trained, so error analysis is deferred; do not infer error rates from descriptive counts.
- **Do semantic groups emerge?** No clustering was run: it is optional and not needed to answer the current research questions.

## Outputs

CSV tables: `dev_class_counts.csv`, `topic_label_counts.csv`, `topic_label_rates.csv`, `service_label_counts.csv`, `complexity_by_label.csv`, `negation_by_label.csv`, `class_associated_ngrams.csv`.
Figures: class balance, topic composition, word-count distribution, service concentration, and associated phrases. Figure captions state sample sizes and interpretation limits.

## Feature and leakage decisions

Only quote text is available for prediction. Dataset topic titles, services, case IDs, and labels are retrospective audit fields and must not be predictive features. Preserve negation and legal wording; remove markup only in the descriptive phrase-count representation, not by altering the source quote. Fit future vectorizers and feature transforms inside each training fold.

## Limitations

The label target is case-derived rather than an independently adjudicated excerpt judgment. The English screen and readability score are approximate. There are no model errors yet, and no locked-test text was included in these analyses. Results describe only the included development subset.

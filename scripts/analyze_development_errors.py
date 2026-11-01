"""Prepare development-only error summaries and a review queue."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_split_bundle  # noqa: E402

TAXONOMY = {
    "negation": r"\b(?:not|no|never|without|neither|nor|cannot|can't|don't|doesn't|didn't|won't|isn't|aren't|wasn't|weren't)\b",
    "exception_or_qualification": r"\b(?:except|unless|provided that|subject to|however|only if|although)\b",
    "permission_or_discretion": r"\b(?:may|might|can|could|reserve the right|at our discretion|we may)\b",
    "third_party_sharing": r"\b(?:share|disclose|transfer|third parties|partners|affiliates|vendors)\b",
    "deletion_or_retention": r"\b(?:delete|deletion|erase|retain|retention|storage)\b",
    "liability_or_indemnity": r"\b(?:liability|liable|indemnify|indemnification|damages|warranty)\b",
    "termination_or_changes": r"\b(?:terminate|termination|suspend|modify|change|update|amend)\b",
    "user_rights_or_access": r"\b(?:access|correct|portability|request|right|consent|object)\b",
}


def main() -> None:
    output = ROOT / "results" / "error_analysis" / "v1"
    output.mkdir(parents=True, exist_ok=True)
    all_rows, summaries = [], {}
    for protocol in ("primary", "clause"):
        frame, _ = load_split_bundle(protocol, ROOT)
        part, include = f"{protocol}_partition", f"{protocol}_include"
        validation = frame.loc[frame[include] & frame[part].eq("validation"),
                               ["point_id", "quote_text", "label", "topic_title", "case_id", "service_id"]]
        predictions = pd.read_csv(ROOT / "results" / "experiments" / f"tuned_validation_{protocol}_v1" / "validation_predictions.csv")
        predictions = predictions.loc[predictions["model"].eq("linear_svm")]
        joined = predictions.merge(validation, on="point_id", validate="many_to_one")
        if joined["true_label"].ne(joined["label"]).any():
            raise AssertionError(f"Saved predictions do not align with {protocol} validation labels")
        joined["is_error"] = joined["predicted_label"].ne(joined["label"])
        joined["error_type"] = joined.apply(lambda r: f"{r['label']}__as__{r['predicted_label']}" if r["is_error"] else "correct", axis=1)
        for category, pattern in TAXONOMY.items():
            joined[f"tag_{category}"] = joined["quote_text"].fillna("").str.contains(pattern, case=False, regex=True)
        joined["protocol"] = protocol
        joined.to_csv(output / f"{protocol}_linear_svm_validation_cases.csv", index=False)
        errors = joined.loc[joined["is_error"]].copy()
        summary = errors.groupby(["label", "predicted_label"]).size().rename("errors").reset_index()
        summary["protocol"] = protocol
        summaries[protocol] = {
            "validation_rows": int(len(joined)), "errors": int(len(errors)),
            "error_rate": float(len(errors) / len(joined)),
            "confusion_errors": summary.to_dict("records"),
            "error_taxonomy_tag_shares": {category: float(errors[f"tag_{category}"].mean()) if len(errors) else 0.0 for category in TAXONOMY},
            "taxonomy_is_heuristic": True,
        }
        # A deterministic 20-row review sample per true/predicted error direction.
        for _, group in errors.groupby(["label", "predicted_label"], sort=True):
            all_rows.append(group.sort_values("point_id").head(20))
        # Include cases where the two tuned model families disagree for side-by-side review.
        disagreement = pd.read_csv(ROOT / "results" / "experiments" / f"tuned_validation_{protocol}_v1" / "validation_predictions.csv")
        disagreement = disagreement.pivot(index="point_id", columns="model", values="predicted_label").reset_index()
        disagreement = disagreement.loc[disagreement["linear_svm"].ne(disagreement["logistic_regression"])]
        disagreement.to_csv(output / f"{protocol}_model_disagreements.csv", index=False)
        summaries[protocol]["linear_svm_logistic_disagreements"] = int(len(disagreement))
        summary.to_csv(output / f"{protocol}_confusion_error_counts.csv", index=False)
    review = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    review.to_csv(output / "manual_review_queue.csv", index=False)
    (output / "error_summary.json").write_text(json.dumps({
        "scope": "validation rows only; locked test excluded", "candidate": "balanced LinearSVC C=1, word unigram/bigram TF-IDF",
        "taxonomy_note": "keyword flags are navigation aids, not verified causal explanations",
        "protocols": summaries,
    }, indent=2), encoding="utf-8")
    print(json.dumps({k: {"validation_rows": v["validation_rows"], "errors": v["errors"], "error_rate": v["error_rate"], "disagreements": v["linear_svm_logistic_disagreements"]} for k, v in summaries.items()}, indent=2))


if __name__ == "__main__":
    main()

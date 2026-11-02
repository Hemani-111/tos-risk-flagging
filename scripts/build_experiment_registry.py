"""Consolidate saved development experiment evidence into CSV, JSON and Markdown."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/experiments"
OUTPUT = RESULTS / "experiment_registry_v1"
DATASET_SHA = "cee557cc927d754cf17675154ed5e1e32eee2fdb9af6700c526e62cd66969f8c"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def base_row(run_dir: Path, meta: dict, protocol: str, model: str, representation: str, **metrics) -> dict:
    return {
        "run_id": meta.get("run_id", run_dir.name), "protocol": protocol,
        "model": model, "representation": representation,
        "split_id": meta.get("split_id", "split_manifest_v1"),
        "dataset_sha256": meta.get("dataset_sha256", DATASET_SHA),
        "selection_metric": meta.get("selection_metric", "macro F1"),
        "selection_partition": meta.get("selection_partition", "development only; see run metadata"),
        "locked_test_used": meta.get("locked_test_used", "not_recorded"),
        "status": "completed", "artifact_directory": str(run_dir.relative_to(ROOT)), **metrics,
    }


def add_frame(rows: list[dict], run_dir: Path, meta: dict, filename: str, model_col: str,
              representation_col: str | None = None, protocol: str | None = None) -> None:
    path = run_dir / filename
    if not path.is_file():
        return
    frame = pd.read_csv(path)
    for record in frame.to_dict(orient="records"):
        model = str(record.pop(model_col, run_dir.name))
        representation = str(record.pop(representation_col, "unspecified")) if representation_col else str(
            meta.get("features") or meta.get("representation") or meta.get("word_char") or meta.get("oof_ensemble")
            or (f"{meta.get('embedding_cache', {}).get('repository')} frozen embeddings" if meta.get("embedding_cache") else "unspecified")
        )
        this_protocol = str(record.pop("protocol", protocol or meta.get("protocol", "unknown")))
        rows.append(base_row(run_dir, meta, this_protocol, model, representation,
                             artifact_file=filename, **record))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for run_dir in sorted(path for path in RESULTS.iterdir() if path.is_dir() and path != OUTPUT):
        meta = read_json(run_dir / "run_metadata.json")
        inferred_protocol = str(meta.get("protocol", "unknown"))
        if inferred_protocol == "unknown":
            inferred_protocol = "primary" if "primary" in run_dir.name else "clause" if "clause" in run_dir.name else "unknown"

        add_frame(rows, run_dir, meta, "validation_metrics.csv", "model", "representation", inferred_protocol)
        add_frame(rows, run_dir, meta, "validation_selected_family_metrics.csv", "family", protocol=inferred_protocol)
        add_frame(rows, run_dir, meta, "word_char_validation.csv", "representation", protocol=inferred_protocol)
        add_frame(rows, run_dir, meta, "embedding_selected_validation.csv", "family", protocol=inferred_protocol)
        add_frame(rows, run_dir, meta, "validation_ensemble_metrics.csv", "model", protocol=inferred_protocol)
        add_frame(rows, run_dir, meta, "oof_ensemble_metrics.csv", "model", protocol=inferred_protocol)

        cv_path = run_dir / "cv_summary.csv"
        if cv_path.is_file():
            for record in pd.read_csv(cv_path).to_dict(orient="records"):
                model = str(record.pop("family", record.pop("model", "unknown")))
                rows.append(base_row(run_dir, meta, inferred_protocol, model,
                                     str(meta.get("features", "SVD of word unigram/bigram TF-IDF")),
                                     artifact_file="cv_summary.csv", **record))
        embedding_summary = run_dir / "embedding_group_cv_summary.csv"
        if embedding_summary.is_file():
            for record in pd.read_csv(embedding_summary).to_dict(orient="records"):
                model = f"{record.pop('family')} C={record.pop('C')} PCA={record.pop('pca_components')}"
                rows.append(base_row(run_dir, meta, inferred_protocol, model, "MiniLM-L6-v2 embeddings",
                                     artifact_file="embedding_group_cv_summary.csv", **record))
        learning_curve = run_dir / "group_learning_curves.csv"
        if learning_curve.is_file():
            curve = pd.read_csv(learning_curve)
            grouped = curve.groupby(["protocol", "representation", "fraction_groups"], as_index=False).agg(
                repeats=("repeat", "count"), groups_mean=("groups", "mean"), train_rows_mean=("train_rows", "mean"),
                validation_macro_f1_mean=("macro_f1", "mean"), validation_macro_f1_sd=("macro_f1", "std"),
                risky_precision_mean=("risky_precision", "mean"), risky_recall_mean=("risky_recall", "mean"),
                mean_fit_seconds=("fit_seconds", "mean"))
            for record in grouped.to_dict(orient="records"):
                proto, rep = str(record.pop("protocol")), str(record.pop("representation"))
                rows.append(base_row(run_dir, meta, proto, "group_learning_curve", rep,
                                     artifact_file="group_learning_curves.csv", **record))
        stability_path = run_dir / "run_metadata.json"
        if run_dir.name.startswith("linear_feature_stability_") and stability_path.is_file():
            for label, summary in meta.get("classes", {}).items():
                rows.append(base_row(run_dir, meta, inferred_protocol, f"feature_stability_{label}",
                                     "word unigram/bigram LinearSVC", **summary))
        cluster_path = run_dir / "kmeans_cluster_summary.csv"
        if cluster_path.is_file():
            clusters = pd.read_csv(cluster_path).drop_duplicates("k")
            for record in clusters.to_dict(orient="records"):
                rows.append(base_row(run_dir, meta, inferred_protocol, f"KMeans k={int(record['k'])}",
                                     "MiniLM-L6-v2 train-only embeddings", **record))
        calibration_path = run_dir / "calibration_validation.json"
        if calibration_path.is_file():
            record = read_json(calibration_path)
            rows.append(base_row(run_dir, meta, inferred_protocol, "sigmoid_calibrated_linear_svc",
                                 "word unigram/bigram TF-IDF; group-fold calibration",
                                 validation_macro_f1=record.get("validation_macro_f1"),
                                 risky_precision=record.get("risky_precision"), risky_recall=record.get("risky_recall"),
                                 multiclass_brier_score=record.get("multiclass_brier_score"),
                                 multiclass_log_loss=record.get("multiclass_log_loss"),
                                 risky_missed_count=record.get("risky_missed_count"),
                                 risky_false_positive_count=record.get("risky_false_positive_count"),
                                 risky_predicted_positive_coverage=record.get("risky_predicted_positive_coverage"),
                                 artifact_file="calibration_validation.json"))
        primary_meta = meta.get("best_cv_row", {})
        if primary_meta:
            rows.append(base_row(run_dir, meta, inferred_protocol,
                                 str(primary_meta.get("model", "best development candidate")),
                                 str(primary_meta.get("representation", "unspecified")),
                                 cv_macro_f1_mean=primary_meta.get("mean_macro_f1"),
                                 cv_macro_f1_sd=primary_meta.get("std_macro_f1"),
                                 cv_risky_precision=None, cv_risky_recall=None,
                                 mean_fit_seconds=primary_meta.get("mean_fit_and_vectorize_seconds"),
                                 artifact_file="run_metadata.json"))

    # Explicit gates are included so an absent metric cannot be mistaken for a run.
    rows.extend([
        {"run_id": "locked_test_evaluation_pending_freeze", "protocol": "primary+clause", "model": "frozen finalist", "representation": "to be set by FINAL_CANDIDATE_FREEZE.md", "status": "pending candidate freeze", "locked_test_used": "no test metric opened"},
        {"run_id": "independent_document_evaluation_pending_labels", "protocol": "six local policy snapshots", "model": "selected frozen candidate", "representation": "full-document extraction and clause mapping", "status": "pending authentic reviewer labels", "locked_test_used": "not applicable"},
    ])
    frame = pd.DataFrame(rows)
    if not frame.empty:
        # Add fold-based scores beside validation rows where the same run saved
        # both an OOF and a validation record for that exact model.
        for index, row in frame.iterrows():
            if row.get("split") != "validation":
                continue
            match = frame.loc[(frame["run_id"] == row["run_id"])
                              & (frame["model"] == row["model"])
                              & (frame.get("split", pd.Series(index=frame.index)).eq("group_oof"))]
            if not match.empty:
                frame.at[index, "cv_macro_f1_mean"] = match.iloc[0].get("macro_f1")
        # The tuned LinearSVC validation row corresponds to the best fixed-fold
        # candidate in the adjacent grouped-CV run.
        for protocol in ("primary", "clause"):
            cv_meta = read_json(RESULTS / f"grouped_cv_{protocol}_linear_features_v1" / "run_metadata.json").get("best_cv_row", {})
            tuned_mask = ((frame["run_id"] == f"tuned_validation_{protocol}_v1")
                          & (frame["model"].astype(str) == "linear_svm"))
            if cv_meta and tuned_mask.any():
                frame.loc[tuned_mask, "cv_macro_f1_mean"] = cv_meta.get("mean_macro_f1")
                frame.loc[tuned_mask, "cv_macro_f1_sd"] = cv_meta.get("std_macro_f1")
        # Attach the shared word+character CV summary to its validation result.
        for protocol in ("primary", "clause"):
            run_dir = RESULTS / f"remaining_features_{protocol}_v1"
            cv_file = run_dir / "word_char_group_cv.csv"
            if cv_file.is_file():
                values = pd.read_csv(cv_file).macro_f1
                mask = ((frame["run_id"] == run_dir.name)
                        & (frame["model"].astype(str) == "word+char tfidf"))
                frame.loc[mask, "cv_macro_f1_mean"] = float(values.mean())
                frame.loc[mask, "cv_macro_f1_sd"] = float(values.std(ddof=1))
    frame = frame.sort_values(["protocol", "status", "run_id", "model"], kind="stable")
    frame.to_csv(OUTPUT / "experiment_registry.csv", index=False)
    registry = {
        "registry_id": "experiment_registry_v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dataset_sha256": DATASET_SHA, "primary_selection_metric": "macro F1",
        "report_alongside": ["Risky precision", "Risky recall"],
        "locked_test_access_incident": "See docs/REMAINING_WORK_STATUS.md; no test metric was calculated or reviewed.",
        "experiment_count": len(rows),
        "records": frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records"),
    }
    (OUTPUT / "experiment_registry.json").write_text(json.dumps(registry, indent=2, default=str, allow_nan=False), encoding="utf-8")
    selected = frame.loc[frame.get("validation_macro_f1", pd.Series(index=frame.index, dtype=float)).notna()]
    # Some sources use macro_f1 as the validation field.
    if "macro_f1" in frame:
        validation_only = frame.loc[frame["macro_f1"].notna()]
        if "split" in validation_only:
            validation_only = validation_only.loc[validation_only["split"].isna() | validation_only["split"].eq("validation")]
        selected = pd.concat([selected, validation_only], ignore_index=True).drop_duplicates()
    if "split" in selected:
        selected = selected.loc[selected["split"].ne("group_oof")]
    lines = [
        "# Consolidated experiment registry",
        "",
        "Generated from saved run metadata and result files. Macro F1 is the registered primary metric; Risky precision and recall are reported alongside it. Entries are development-only unless a future freeze record explicitly states otherwise.",
        "",
        f"Generated {registry['created_at_utc']} UTC; data SHA-256 `{DATASET_SHA}`.",
        "",
        "## Development classification results",
        "",
        "| Run | Protocol | Model | Representation | CV macro F1 | Validation macro F1 | Risky P | Risky R |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    preferred = selected.loc[selected["model"].astype(str).str.contains("linear|word|hard_vote|soft_vote|stack|hist_gradient|knn|decision_tree|random_forest|logistic|sigmoid", case=False, regex=True)] if not selected.empty else selected
    for row in preferred.to_dict(orient="records"):
        cv_value = row.get("cv_macro_f1_mean")
        val_value = row.get("validation_macro_f1")
        if pd.isna(val_value):
            val_value = row.get("macro_f1")
        def fmt(value):
            try:
                if pd.isna(value):
                    return "-"
                return f"{float(value):.4f}"
            except (TypeError, ValueError):
                return "-"
        rep = str(row.get("representation", "-"))
        if "fold-local word TF-IDF" in rep:
            rep = "word TF-IDF; LR/LinearSVC"
        elif "max_features=60000, then training-fold TruncatedSVD" in rep:
            rep = "word TF-IDF + SVD-100"
        lines.append("| {run} | {protocol} | {model} | {representation} | {cv} | {val} | {p} | {r} |".format(
            run=str(row.get("run_id", "-"))[:42], protocol=row.get("protocol", "-"), model=row.get("model", "-"),
            representation=rep.replace("|", "/")[:44], cv=fmt(cv_value), val=fmt(val_value),
            p=fmt(row.get("risky_precision")), r=fmt(row.get("risky_recall"))))
    lines += ["", "## Representation and unsupervised analyses", "",
              "| Analysis | Protocol | Result |", "|---|---|---|"]
    for row in frame.loc[frame["model"].astype(str).str.contains("feature_stability", case=False)].to_dict(orient="records"):
        lines.append(f"| {row.get('model')} | {row.get('protocol')} | top-100 coefficient-token Jaccard {fmt(row.get('top_100_pairwise_jaccard_mean'))} |")
    for row in frame.loc[frame["model"].astype(str).str.startswith("KMeans")].to_dict(orient="records"):
        lines.append(f"| {row.get('model')} | {row.get('protocol')} | sampled cosine silhouette {fmt(row.get('sampled_cosine_silhouette'))}; seed ARI {fmt(row.get('mean_pairwise_ARI'))} |")
    for protocol in ("primary", "clause"):
        curves = RESULTS / f"remaining_features_{protocol}_v1" / "group_learning_curves.csv"
        if curves.is_file():
            curve = pd.read_csv(curves)
            full = curve.loc[curve["fraction_groups"].eq(1.0)].groupby("representation").macro_f1.agg(["mean", "std"])
            for representation, values in full.iterrows():
                lines.append(f"| full-group learning curve: {representation} | {protocol} | validation macro F1 {fmt(values['mean'])} (SD {fmt(values['std'])}, 3 group samples) |")
    lines += [
        "",
        "## Scope and limits",
        "",
        "- The CSV and JSON contain model-family configurations, fold/validation results, runtime fields, stability metrics, cluster summaries, artifact directories, split and dataset hashes when present.",
        "- `results/experiments/` run folders contain fold-level predictions/confusions and raw outputs. The registry does not replace those artifacts.",
        "- The locked test has no recorded score. Its prior in-memory loader incident is disclosed in the status report; scoring remains gated on a written candidate freeze.",
        "- Independent full-document evaluation remains pending two authentic human review sheets and adjudication.",
        "",
    ]
    (OUTPUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(rows)} registry records to {OUTPUT}")


if __name__ == "__main__":
    main()

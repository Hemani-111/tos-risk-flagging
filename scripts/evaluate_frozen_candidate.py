"""Score the frozen candidate once on each locked test partition.

This is not a tuning script. It refuses to run before a committed candidate
freeze exists, builds train/validation data through the development-only
loader, and reads only the requested protocol's test records after fitting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

LABELS = ["Risky", "Neutral", "Safe"]
FREEZE_PATH = ROOT / "docs/FINAL_CANDIDATE_FREEZE.md"
SPLIT_PATH = ROOT / "data/splits/split_manifest_v1.csv"
RESULT_ROOT = ROOT / "results/locked_evaluation_v1"
RESULTS_SHA = RESULT_ROOT / "evaluation_registry.json"


def get_git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def get_freeze_commit() -> str:
    status = subprocess.check_output(["git", "status", "--porcelain", "--", str(FREEZE_PATH)], cwd=ROOT, text=True)
    if status.strip():
        raise SystemExit("Candidate freeze has uncommitted changes; commit the freeze before test evaluation")
    return subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(FREEZE_PATH)], cwd=ROOT, text=True).strip()


def source_metadata() -> dict[str, object]:
    manifest = json.loads((ROOT / "data/splits/split_manifest_v1.json").read_text(encoding="utf-8"))
    return manifest


def fit_recipe(train: pd.DataFrame):
    vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_df=0.99,
                                 max_features=60000, sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
    start = time.perf_counter()
    x_train = vectorizer.fit_transform(train.quote_text.fillna("").astype(str))
    model = LinearSVC(C=1.0, class_weight="balanced", random_state=20261102, max_iter=5000)
    model.fit(x_train, train.label.to_numpy())
    return vectorizer, model, time.perf_counter() - start


def group_bootstrap_macro_f1(test: pd.DataFrame, predictions: np.ndarray, group_column: str, seed: int = 20261103) -> dict[str, object]:
    """Percentile interval by resampling test groups, keeping clauses grouped."""
    groups = test[group_column].astype(str).to_numpy()
    unique_groups = np.unique(groups)
    if len(unique_groups) < 2:
        return {"groups": int(len(unique_groups)), "replicates": 0, "macro_f1_percentile_95": None}
    members = {group: np.flatnonzero(groups == group) for group in unique_groups}
    rng = np.random.default_rng(seed)
    values = np.empty(2000, dtype=np.float64)
    for replicate in range(len(values)):
        sampled_groups = rng.choice(unique_groups, size=len(unique_groups), replace=True)
        indices = np.concatenate([members[group] for group in sampled_groups])
        values[replicate] = f1_score(test.label.to_numpy()[indices], predictions[indices],
                                     labels=LABELS, average="macro", zero_division=0)
    return {
        "method": "non-stratified cluster bootstrap; resample unique test groups with replacement and include all their clauses",
        "seed": seed, "groups": int(len(unique_groups)), "replicates": len(values),
        "macro_f1_percentile_95": [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))],
        "interpretation": "Uncertainty over sampled test groups; not a confidence guarantee for legal risk or future deployment.",
    }


def summarize(protocol: str, dev: pd.DataFrame, test: pd.DataFrame, vectorizer, model, fit_seconds: float, split_meta: dict) -> dict:
    y_true = test.label.to_numpy()
    started = time.perf_counter()
    predictions = model.predict(vectorizer.transform(test.quote_text.fillna("").astype(str)))
    predict_seconds = time.perf_counter() - started
    report = classification_report(y_true, predictions, labels=model.classes_, output_dict=True, zero_division=0)
    confusion = confusion_matrix(y_true, predictions, labels=LABELS)
    group = "service_component" if protocol == "primary" else "text_component"
    assert not set(dev[group].astype(str)) & set(test[group].astype(str)), "train/test group leakage detected"
    output = RESULT_ROOT / protocol
    output.mkdir(parents=True, exist_ok=True)
    predictions_frame = pd.DataFrame({
        "point_id": test.point_id.to_numpy(), "group_id": test[group].astype(str).to_numpy(),
        "true_label": y_true, "predicted_label": predictions,
    })
    predictions_frame.to_csv(output / "predictions.csv", index=False)
    pd.DataFrame(confusion, index=[f"true_{label}" for label in LABELS], columns=[f"pred_{label}" for label in LABELS]).to_csv(output / "confusion.csv")
    metrics = {
        "protocol": protocol, "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze_commit": get_freeze_commit(), "evaluation_commit": get_git_head(), "dataset_sha256": split_meta["dataset_sha256"],
        "split_id": split_meta["split_id"], "test_rows": len(test), "train_rows": len(dev),
        "training_fit_seconds_including_vectorizer": fit_seconds, "prediction_seconds": predict_seconds,
        "prediction_ms_per_clause": predict_seconds * 1000 / max(1, len(test)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "macro_f1": float(f1_score(y_true, predictions, labels=LABELS, average="macro", zero_division=0)),
        "risky_precision": float(precision_score(y_true, predictions, labels=["Risky"], average="macro", zero_division=0)),
        "risky_recall": float(recall_score(y_true, predictions, labels=["Risky"], average="macro", zero_division=0)),
        "risky_false_positives": int(((y_true != "Risky") & (predictions == "Risky")).sum()),
        "risky_false_negatives": int(((y_true == "Risky") & (predictions != "Risky")).sum()),
        "per_class": {label: {key: float(report[label][key]) for key in ("precision", "recall", "f1-score", "support")} for label in LABELS},
        "group_column": group, "test_group_count": int(test[group].nunique()),
        "group_bootstrap": group_bootstrap_macro_f1(test, predictions, group),
        "train_test_groups_disjoint": True, "freeze_recipe": "word 1-2gram TF-IDF; LinearSVC C=1 class_weight=balanced",
        "locked_test_used": True, "evaluation_run_once": True,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", choices=["primary", "clause", "both"], required=True)
    args = parser.parse_args()
    if not FREEZE_PATH.is_file():
        raise SystemExit("Candidate freeze document is missing")
    freeze_commit = get_freeze_commit()
    if not RESULTS_SHA.is_file():
        print("No previous locked evaluation registry found; first scored evaluation may proceed.")
    else:
        prior = json.loads(RESULTS_SHA.read_text(encoding="utf-8"))
        requested = {"primary", "clause"} if args.protocol == "both" else {args.protocol}
        done = {record["protocol"] for record in prior["evaluations"]}
        if requested & done:
            raise SystemExit(f"Refusing repeat test evaluation for: {sorted(requested & done)}")

    protocols = ("primary", "clause") if args.protocol == "both" else (args.protocol,)
    eval_records = []
    for protocol in protocols:
        dev, split_meta = load_development_bundle(protocol, ROOT)
        part, include = f"{protocol}_partition", f"{protocol}_include"
        train = dev.loc[dev[include] & dev[part].eq("train")].copy().reset_index(drop=True)
        vectorizer, model, fit_seconds = fit_recipe(train)

        # Only now load test records for the selected protocol. No test fitting
        # or selection follows this point.
        manifest = pd.read_csv(SPLIT_PATH, low_memory=False)
        test_ids = set(manifest.loc[manifest[f"{protocol}_partition"].eq("test") & manifest[f"{protocol}_include"], "point_id"].astype(int))
        raw_path = ROOT / split_meta["dataset"]
        dev_ids = set(dev.point_id.astype(int))
        if test_ids & dev_ids:
            raise RuntimeError("Development and locked test IDs overlap")
        # Parse the locked test only after model fit, and select only the
        # requested protocol's included test point IDs.
        full_test = pd.read_csv(raw_path, low_memory=False)
        test = full_test.loc[full_test.point_id.astype(int).isin(test_ids)].merge(
            manifest, on="point_id", how="inner", validate="one_to_one")
        expected = manifest.loc[manifest[f"{protocol}_partition"].eq("test") & manifest[f"{protocol}_include"]]
        if len(test) != len(expected) or set(test.point_id.astype(int)) != test_ids:
            raise RuntimeError("Test partition does not match frozen manifest")
        del full_test
        result = summarize(protocol, train, test, vectorizer, model, fit_seconds, split_meta)
        result["freeze_sha256"] = hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest()
        eval_records.append(result)
        print(json.dumps({key: result[key] for key in ("protocol", "test_rows", "macro_f1", "risky_precision", "risky_recall", "risky_false_positives", "risky_false_negatives")}, indent=2), flush=True)

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    prior = json.loads(RESULTS_SHA.read_text(encoding="utf-8")) if RESULTS_SHA.is_file() else {"evaluations": []}
    prior["evaluation_registry"] = "locked_evaluation_v1"
    prior["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    prior["freeze_document"] = str(FREEZE_PATH.relative_to(ROOT))
    prior["freeze_commit"] = freeze_commit
    prior["dataset_sha256"] = source_metadata()["dataset_sha256"]
    prior["incident_disclosure"] = "Locked test text/labels were previously materialized by the old shared loader during development-only runs; no test metrics were computed or viewed. This is not an untouched test claim."
    prior["evaluations"] = prior.get("evaluations", []) + eval_records
    RESULTS_SHA.write_text(json.dumps(prior, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

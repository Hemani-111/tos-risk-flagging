"""Build the frozen primary LinearSVC package from included training rows."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.splitting import load_development_bundle  # noqa: E402

FREEZE = ROOT / "docs/FINAL_CANDIDATE_FREEZE.md"
OUTPUT = ROOT / "models/releases/linear-svc-primary-v2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", str(FREEZE)], cwd=ROOT, text=True)
    if dirty.strip():
        raise SystemExit("Commit the candidate freeze before packaging")
    freeze_commit = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(FREEZE)], cwd=ROOT, text=True).strip()
    dev, split = load_development_bundle("primary", ROOT)
    train = dev.loc[dev.primary_include & dev.primary_partition.eq("train")].copy().reset_index(drop=True)
    vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_df=0.99,
                                 max_features=60000, sublinear_tf=True, strip_accents="unicode", dtype=np.float32)
    X = vectorizer.fit_transform(train.quote_text.fillna("").astype(str))
    model = LinearSVC(C=1.0, class_weight="balanced", random_state=20261102, max_iter=5000).fit(X, train.label.to_numpy())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    model_path, vectorizer_path = OUTPUT / "model.joblib", OUTPUT / "vectorizer.joblib"
    joblib.dump(model, model_path, compress=3)
    joblib.dump(vectorizer, vectorizer_path, compress=3)
    freeze_hash = sha256(FREEZE)
    training_id_hash = hashlib.sha256("\n".join(train.point_id.astype(str)).encode("utf-8")).hexdigest()
    training_text_hash = hashlib.sha256("\n".join(
        f"{row.point_id}\t{row.quote_text}" for row in train.itertuples(index=False)
    ).encode("utf-8")).hexdigest()
    metadata = {
        "model_version": "linear-svc-primary-v2",
        "schema_version": "1.1",
        "status": "frozen candidate selected on development; primary unseen-service recipe",
        "freeze_document": "docs/FINAL_CANDIDATE_FREEZE.md",
        "freeze_commit": freeze_commit,
        "freeze_sha256": freeze_hash,
        "selection_metric": "macro F1",
        "training": {"protocol": "primary", "split_id": split["split_id"], "partition": "included training only",
                     "rows": len(train), "point_ids_sha256": training_id_hash,
                     "point_id_order": "split order", "training_texts_sha256": training_text_hash,
                     "dataset_sha256": split["dataset_sha256"]},
        "classifier": {"class": "sklearn.svm.LinearSVC", "C": 1.0, "class_weight": "balanced",
                       "random_state": 20261102, "max_iter": 5000, "class_order": [str(x) for x in model.classes_],
                       "artifact": model_path.name, "sha256": sha256(model_path)},
        "vectorizer": {"class": "sklearn.feature_extraction.text.TfidfVectorizer", "analyzer": "word",
                       "ngram_range": [1, 2], "min_df": 2, "max_df": 0.99, "max_features": 60000,
                       "sublinear_tf": True, "strip_accents": "unicode", "dtype": "float32",
                       "lowercase": True, "feature_count": len(vectorizer.vocabulary_),
                       "artifact": vectorizer_path.name, "sha256": sha256(vectorizer_path)},
        "runtime": {"python": f"{sys.version_info.major}.{sys.version_info.minor}", "scikit_learn": sklearn.__version__,
                    "numpy": np.__version__, "joblib": joblib.__version__},
        "limitations": [
            "Predictions are clause-level labels from an English, case-derived benchmark; they are not legal advice.",
            "A Risky prediction can be false and a Risky clause can be missed; inspect source context.",
            "No calibrated probabilities or confidence scores are exposed.",
            "The locked-test evaluation followed the freeze; the earlier loader boundary incident is disclosed in the candidate freeze and evaluation report.",
        ],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUTPUT / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"package": str(OUTPUT.relative_to(ROOT)), "model_sha256": metadata["classifier"]["sha256"],
                      "vectorizer_sha256": metadata["vectorizer"]["sha256"], "train_rows": len(train),
                      "feature_count": metadata["vectorizer"]["feature_count"], "classes": model.classes_.tolist()}, indent=2))


if __name__ == "__main__":
    main()

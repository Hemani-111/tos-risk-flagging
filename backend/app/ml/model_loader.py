import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Tuple

import joblib
import sklearn

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = Path(os.environ.get("MODEL_DIR", PROJECT_ROOT / "models" / "selected_model"))
MODEL_PATH = MODEL_DIR / "model.joblib"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.joblib"
METADATA_PATH = MODEL_DIR / "metadata.json"


class ModelLoader:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.metadata = None

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def load(self) -> Tuple[object, object]:
        if self.model is not None and self.vectorizer is not None:
            return self.model, self.vectorizer

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(f"Vectorizer artifact not found at {VECTORIZER_PATH}")
        if not METADATA_PATH.exists():
            raise FileNotFoundError(f"Model package metadata not found at {METADATA_PATH}")

        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        expected_runtime = metadata.get("runtime", {}).get("scikit_learn")
        if expected_runtime != sklearn.__version__:
            raise RuntimeError(
                f"Model requires scikit-learn {expected_runtime}; found {sklearn.__version__}."
            )
        for path, section in ((MODEL_PATH, "classifier"), (VECTORIZER_PATH, "vectorizer")):
            expected_hash = metadata.get(section, {}).get("sha256")
            actual_hash = self._sha256(path)
            if not expected_hash or actual_hash != expected_hash:
                raise RuntimeError(f"Model package checksum mismatch for {path.name}.")

        vectorizer = joblib.load(VECTORIZER_PATH)
        model = joblib.load(MODEL_PATH)
        expected_classes = metadata.get("classifier", {}).get("class_order")
        actual_classes = [str(label) for label in getattr(model, "classes_", [])]
        if actual_classes != expected_classes:
            raise RuntimeError(
                f"Model class order mismatch: expected {expected_classes}, found {actual_classes}."
            )
        if not hasattr(vectorizer, "transform") or not hasattr(model, "predict"):
            raise RuntimeError("Model package is missing the expected transform/predict interface.")

        self.vectorizer = vectorizer
        self.model = model
        self.metadata = metadata
        logger.info("Loaded model package %s", metadata.get("model_version", "unknown"))
        return self.model, self.vectorizer

    def package_info(self) -> dict:
        if self.metadata is None:
            self.load()
        return {
            "modelVersion": self.metadata["model_version"],
            "schemaVersion": self.metadata["schema_version"],
            "warnings": list(self.metadata.get("limitations", [])),
        }


model_loader = ModelLoader()

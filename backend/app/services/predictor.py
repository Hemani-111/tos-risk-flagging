from typing import List, Dict, Optional
from app.ml.model_loader import model_loader
from app.services.clause_segmenter import Clause


class Predictor:
    def __init__(self):
        # Keep app import/startup alive when packaging is broken so readiness
        # can report the failure and operators receive a useful response.
        self._model = None
        self._vectorizer = None

    def predict(self, clauses: List[Clause]) -> List[Dict]:
        if self._model is None or self._vectorizer is None:
            self._model, self._vectorizer = model_loader.load()
        texts = [c.text for c in clauses]
        tfidf = self._vectorizer.transform(texts)
        predictions = self._model.predict(tfidf)

        results = []
        for clause, label in zip(clauses, predictions):
            results.append(
                {
                    "id": clause.clause_id,
                    "text": clause.text,
                    "label": label,
                    "section": clause.section,
                    "startOffset": clause.start_offset,
                    "endOffset": clause.end_offset,
                }
            )
        return results

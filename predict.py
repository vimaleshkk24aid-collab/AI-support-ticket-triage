"""
Loads the trained classifier + vectorizer + label encoder ONCE and exposes
`predictor.predict(text)`. Imported by the FastAPI backend at startup; the
model is never retrained or reloaded per request.
"""

import os
import sys

import joblib
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import config  # noqa: E402
from backend.services.text_processor import preprocess  # noqa: E402


class TicketCategoryPredictor:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.loaded = False
        self.load_error = None
        self._load()

    def _load(self):
        try:
            paths = (config.CLASSIFIER_PATH, config.VECTORIZER_PATH, config.LABEL_ENCODER_PATH)
            if not all(os.path.exists(p) for p in paths):
                raise FileNotFoundError("Model artifacts not found. Run `python ml/train.py` first.")
            self.model = joblib.load(config.CLASSIFIER_PATH)
            self.vectorizer = joblib.load(config.VECTORIZER_PATH)
            self.label_encoder = joblib.load(config.LABEL_ENCODER_PATH)
            self.loaded = True
        except Exception as exc:  # noqa: BLE001
            self.loaded = False
            self.load_error = str(exc)

    def predict(self, text: str):
        """Returns (category, confidence, {category: probability})."""
        if not self.loaded:
            raise RuntimeError(f"Category model is not loaded: {self.load_error}")

        features = self.vectorizer.transform([preprocess(text)])
        classes = self.label_encoder.classes_

        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(features)[0]
        elif hasattr(self.model, "decision_function"):
            # LinearSVC has no predict_proba -> softmax of decision scores (display only).
            scores = np.atleast_1d(self.model.decision_function(features)[0])
            exp = np.exp(scores - np.max(scores))
            probs = exp / exp.sum()
        else:
            probs = np.zeros(len(classes))
            probs[int(self.model.predict(features)[0])] = 1.0

        idx = int(np.argmax(probs))
        return str(classes[idx]), float(probs[idx]), {str(classes[i]): float(probs[i]) for i in range(len(classes))}


predictor = TicketCategoryPredictor()

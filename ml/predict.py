
from __future__ import annotations

from pathlib import Path
import math
from typing import Any, Dict

import joblib

try:
    from .text_utils import (
        PURPOSES,
        blend_probabilities,
        keyword_scores,
        normalize_text,
        sorted_candidates,
        strong_keyword_override,
        to_probabilities,
    )
except ImportError:
    from text_utils import (
        PURPOSES,
        blend_probabilities,
        keyword_scores,
        normalize_text,
        sorted_candidates,
        strong_keyword_override,
        to_probabilities,
    )


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"

_model = None
ACCEPTANCE_THRESHOLD = 0.70
MARGIN_THRESHOLD = 0.10


def load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def _softmax(values: list[float]) -> list[float]:
    max_value = max(values)
    exps = [math.exp(value - max_value) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def _model_probabilities(model, text: str) -> Dict[str, float]:
    if hasattr(model, "predict_proba"):
        labels = list(model.classes_)
        probs = model.predict_proba([text])[0]
        return {str(label): float(prob) for label, prob in zip(labels, probs)}

    if hasattr(model, "decision_function"):
        labels = list(model.classes_)
        raw = model.decision_function([text])[0]
        if not isinstance(raw, (list, tuple)):
            raw = [raw]
        probs = _softmax([float(v) for v in raw])
        return {str(label): float(prob) for label, prob in zip(labels, probs)}

    predicted = str(model.predict([text])[0])
    return {label: (1.0 if label == predicted else 0.0) for label in PURPOSES}


def predict_purpose(text: str) -> dict:
    model = load_model()

    if not text or not text.strip():
        return {
            "purpose": None,
            "raw_purpose": None,
            "confidence": 0.0,
            "accepted": False,
            "alternatives": [],
            "matched_keywords": {},
            "normalized_text": "",
        }

    cleaned_text = normalize_text(text)

    model_probs = _model_probabilities(model, cleaned_text)
    raw_keyword_scores, matched_keywords = keyword_scores(cleaned_text)
    keyword_probs = to_probabilities(raw_keyword_scores)
    final_probs = blend_probabilities(model_probs, keyword_probs)

    override_label, override_confidence = strong_keyword_override(raw_keyword_scores)
    ranked = sorted_candidates(final_probs)

    predicted_label = ranked[0][0]
    confidence = float(ranked[0][1]) if ranked else 0.0
    second_confidence = float(ranked[1][1]) if len(ranked) > 1 else 0.0
    margin = confidence - second_confidence

    if override_label is not None:
        predicted_label = override_label
        confidence = max(confidence, float(override_confidence or 0.0))
        ranked = [(label, conf) for label, conf in ranked if label != override_label]
        ranked.insert(0, (override_label, confidence))
        second_confidence = float(ranked[1][1]) if len(ranked) > 1 else 0.0
        margin = confidence - second_confidence

    accepted = confidence >= ACCEPTANCE_THRESHOLD and margin >= MARGIN_THRESHOLD

    alternatives = [
        {"purpose": label, "confidence": round(float(prob), 4)}
        for label, prob in ranked[:3]
    ]

    matched_keywords = {
        label: values[:6]
        for label, values in matched_keywords.items()
        if values
    }

    return {
        "purpose": predicted_label if accepted else None,
        "raw_purpose": predicted_label,
        "confidence": round(float(confidence), 4),
        "accepted": accepted,
        "alternatives": alternatives,
        "matched_keywords": matched_keywords,
        "normalized_text": cleaned_text,
        "model_confidence": round(float(model_probs.get(predicted_label, 0.0)), 4),
        "keyword_confidence": round(float(keyword_probs.get(predicted_label, 0.0)), 4),
        "margin": round(float(margin), 4),
    }


if __name__ == "__main__":
    test_queries = [
        "Потрібен ПК для гри в доту 2",
        "хочу комп для cs2 і valorant",
        "потрібен комп для word excel і браузера",
        "потрібен комп для бухгалтера, excel і medoc",
        "пк для навчання zoom і python",
        "комп'ютер для blender і premiere pro",
        "хочу пк для blender, maya і рендеру сцен",
    ]

    for query in test_queries:
        print(query, "->", predict_purpose(query))

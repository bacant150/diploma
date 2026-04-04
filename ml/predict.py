from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

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

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / 'model.joblib'

_model = None
_model_load_error: str | None = None

# Пороги прийняття рішення:
# - AUTO_ACCEPT_THRESHOLD: одразу переходимо до конфігуратора.
# - CONFIRM_THRESHOLD: показуємо припущення і просимо підтвердити.
# - MARGIN_THRESHOLD: додатковий захист від «впевнених, але хибних» рішень.
ACCEPTANCE_THRESHOLD = 0.35
AUTO_ACCEPT_THRESHOLD = 0.55
CONFIRM_THRESHOLD = 0.35
MARGIN_THRESHOLD = 0.12

# Додаткові rule-based сигнали поверх ML і keyword scoring.
# Це не замінює модель, а підсилює очевидні сценарії.
RULE_HINTS: dict[str, list[tuple[str, tuple[str, ...], float]]] = {
    'gaming': [
        ('esports_bundle', ('cs2', 'valorant', 'fortnite', 'dota2', 'warzone', 'apex'), 2.4),
        ('gaming_request', ('gaming', 'ігров', 'гри', 'fps', 'stream'), 1.8),
        ('high_fps', ('144 fps', '240 fps', 'esports'), 1.6),
    ],
    'office': [
        ('accounting_bundle', ('excel', 'medoc', 'bas', 'clientbank'), 2.6),
        ('office_bundle', ('word', 'excel', 'powerpoint', 'pdf', 'crm', 'email'), 1.7),
        ('business_docs', ('бухгалтер', 'договор', 'накладн', 'рахунк', 'звіт'), 1.8),
    ],
    'study': [
        ('education_bundle', ('study', 'zoom', 'meet', 'classroom', 'moodle'), 2.4),
        ('coding_study_bundle', ('python', 'java', 'cpp', 'vscode', 'programming'), 1.8),
        ('student_bundle', ('студент', 'навчан', 'лекці', 'урок', 'курсов'), 1.7),
    ],
    'creator': [
        ('video_bundle', ('premierepro', 'aftereffects', 'davinciresolve', 'videoedit'), 2.8),
        ('three_d_bundle', ('blender', 'maya', 'max3d', 'autocad', 'solidworks', '3d'), 2.9),
        ('design_bundle', ('photoshop', 'illustrator', 'lightroom', 'figma'), 1.7),
        ('render_bundle', ('render', 'creator', 'рендер', 'монтаж', 'анімац'), 1.8),
    ],
}


class ModelUnavailableError(RuntimeError):
    """Raised when the local ML model cannot be loaded."""


def _format_exception(exc: Exception) -> str:
    return f'{type(exc).__name__}: {exc}'


def load_model(force_reload: bool = False) -> Any:
    global _model, _model_load_error

    if force_reload:
        _model = None
        _model_load_error = None

    if _model is not None:
        return _model

    if not MODEL_PATH.exists():
        _model_load_error = f'Файл моделі не знайдено: {MODEL_PATH}'
        raise ModelUnavailableError(_model_load_error)

    try:
        _model = joblib.load(MODEL_PATH)
        _model_load_error = None
        return _model
    except Exception as exc:
        _model_load_error = _format_exception(exc)
        logger.exception('Не вдалося завантажити ML-модель з %s', MODEL_PATH)
        raise ModelUnavailableError(
            'Не вдалося завантажити локальну ML-модель. Перевір model.joblib і залежності.'
        ) from exc


def warmup_model() -> None:
    load_model()


def get_model_status(*, probe: bool = False) -> dict[str, Any]:
    if probe and _model is None:
        try:
            load_model()
        except ModelUnavailableError:
            pass

    model_exists = MODEL_PATH.exists()
    available = _model is not None

    reason = None
    if not model_exists:
        reason = f'Файл моделі не знайдено: {MODEL_PATH.name}'
    elif _model_load_error:
        reason = _model_load_error

    return {
        'available': available,
        'loaded': available,
        'model_exists': model_exists,
        'model_path': str(MODEL_PATH),
        'reason': reason,
    }


def _softmax(values: list[float]) -> list[float]:
    max_value = max(values)
    exps = [math.exp(value - max_value) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def _model_probabilities(model: Any, text: str) -> dict[str, float]:
    if hasattr(model, 'predict_proba'):
        labels = list(model.classes_)
        probs = model.predict_proba([text])[0]
        return {str(label): float(prob) for label, prob in zip(labels, probs)}

    if hasattr(model, 'decision_function'):
        labels = list(model.classes_)
        raw = model.decision_function([text])

        if hasattr(raw, 'tolist'):
            raw = raw.tolist()

        if isinstance(raw, list) and raw and not isinstance(raw[0], (list, tuple)):
            scalar = float(raw[0])
            if len(labels) == 2:
                probs = _softmax([-scalar, scalar])
            else:
                probs = [1.0]
        else:
            row = raw[0]
            probs = _softmax([float(v) for v in row])

        return {str(label): float(prob) for label, prob in zip(labels, probs)}

    predicted = str(model.predict([text])[0])
    return {label: (1.0 if label == predicted else 0.0) for label in PURPOSES}


def _rule_scores(cleaned_text: str) -> tuple[dict[str, float], dict[str, list[str]]]:
    scores: dict[str, float] = {label: 0.0 for label in PURPOSES}
    matched: dict[str, list[str]] = {label: [] for label in PURPOSES}

    for label, rules in RULE_HINTS.items():
        for rule_name, tokens, weight in rules:
            hits = [token for token in tokens if token in cleaned_text]
            if not hits:
                continue
            scaled_weight = weight
            if len(hits) > 1:
                scaled_weight += min(1.2, 0.35 * (len(hits) - 1))
            scores[label] += scaled_weight
            matched[label].append(f"{rule_name}: {', '.join(hits[:4])}")

    return scores, matched


def _merge_raw_scores(*score_maps: dict[str, float]) -> dict[str, float]:
    merged = {label: 0.0 for label in PURPOSES}
    for score_map in score_maps:
        for label in PURPOSES:
            merged[label] += float(score_map.get(label, 0.0))
    return merged


def _decision_mode(confidence: float, margin: float) -> str:
    if confidence >= AUTO_ACCEPT_THRESHOLD and margin >= MARGIN_THRESHOLD:
        return 'auto'
    if confidence >= CONFIRM_THRESHOLD:
        return 'confirm'
    return 'manual'


def predict_purpose(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return {
            'purpose': None,
            'raw_purpose': None,
            'confidence': 0.0,
            'accepted': False,
            'decision_mode': 'manual',
            'alternatives': [],
            'matched_keywords': {},
            'matched_rule_signals': {},
            'normalized_text': '',
            'margin': 0.0,
        }

    model = load_model()
    cleaned_text = normalize_text(text)

    model_probs = _model_probabilities(model, cleaned_text)
    raw_keyword_scores, matched_keywords = keyword_scores(cleaned_text)
    raw_rule_scores, matched_rule_signals = _rule_scores(cleaned_text)

    combined_hint_scores = _merge_raw_scores(raw_keyword_scores, raw_rule_scores)
    combined_hint_probs = to_probabilities(combined_hint_scores)
    final_probs = blend_probabilities(
        model_probs,
        combined_hint_probs,
        model_weight=0.70,
        keyword_weight=0.30,
    )

    override_label, override_confidence = strong_keyword_override(combined_hint_scores)
    ranked = sorted_candidates(final_probs)

    predicted_label = ranked[0][0] if ranked else None
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

    decision_mode = _decision_mode(confidence, margin)
    accepted = decision_mode == 'auto'

    alternatives = [
        {'purpose': label, 'confidence': round(float(prob), 4)}
        for label, prob in ranked[:3]
    ]

    matched_keywords = {
        label: values[:6]
        for label, values in matched_keywords.items()
        if values
    }
    matched_rule_signals = {
        label: values[:4]
        for label, values in matched_rule_signals.items()
        if values
    }

    return {
        'purpose': predicted_label if accepted else None,
        'raw_purpose': predicted_label,
        'confidence': round(float(confidence), 4),
        'accepted': accepted,
        'decision_mode': decision_mode,
        'needs_confirmation': decision_mode == 'confirm' and bool(predicted_label),
        'alternatives': alternatives,
        'matched_keywords': matched_keywords,
        'matched_rule_signals': matched_rule_signals,
        'normalized_text': cleaned_text,
        'model_confidence': round(float(model_probs.get(predicted_label, 0.0)), 4)
        if predicted_label
        else 0.0,
        'keyword_confidence': round(float(combined_hint_probs.get(predicted_label, 0.0)), 4)
        if predicted_label
        else 0.0,
        'margin': round(float(margin), 4),
        'second_confidence': round(float(second_confidence), 4),
    }


if __name__ == '__main__':
    test_queries = [
        'Потрібен ПК для гри в доту 2',
        'хочу комп для cs2 і valorant',
        'потрібен комп для word excel і браузера',
        'потрібен комп для бухгалтера, excel і medoc',
        'пк для навчання zoom і python',
        "комп'ютер для blender і premiere pro",
        'хочу пк для blender, maya і рендеру сцен',
    ]

    for query in test_queries:
        print(query, '->', predict_purpose(query))

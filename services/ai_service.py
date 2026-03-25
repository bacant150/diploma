from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import Request
from pydantic import ValidationError

from config import PURPOSE_TITLES
from schemas import PurposeDetectionFormSchema
from utils.validation import ai_refinement_tips, confidence_to_percent

logger = logging.getLogger('pcbuilder.ai')

try:
    from ml.predict import (
        ACCEPTANCE_THRESHOLD as AI_ACCEPTANCE_THRESHOLD,
        ModelUnavailableError,
        get_model_status,
        predict_purpose,
        warmup_model,
    )
    AI_IMPORT_ERROR: str | None = None
except Exception as exc:
    AI_IMPORT_ERROR = f'{type(exc).__name__}: {exc}'
    logger.exception('Не вдалося імпортувати AI-модуль.')

    AI_ACCEPTANCE_THRESHOLD = 0.30

    class ModelUnavailableError(RuntimeError):
        """Raised when the local AI model is unavailable."""

    def get_model_status(*, probe: bool = False) -> dict[str, Any]:
        return {
            'available': False,
            'loaded': False,
            'model_exists': False,
            'model_path': str(Path(__file__).resolve().parent.parent / 'ml' / 'model.joblib'),
            'reason': AI_IMPORT_ERROR or 'Не вдалося імпортувати модуль ml.predict.',
        }

    def warmup_model() -> None:
        return None

    def predict_purpose(text: str) -> dict[str, Any]:
        raise ModelUnavailableError(
            'AI-модуль недоступний: не вдалося імпортувати модуль або його залежності.'
        )


def ai_status_message(ai_status: dict[str, Any]) -> str:
    if ai_status.get('available'):
        return 'Локальна ML-модель успішно завантажена.'

    reason = ai_status.get('reason')
    if reason:
        return f'Локальна ML-модель недоступна: {reason}'

    return 'Локальна ML-модель тимчасово недоступна.'


def get_ai_health_status(*, probe: bool = False) -> dict[str, Any]:
    return get_model_status(probe=probe)


def run_ai_startup_check() -> None:
    try:
        warmup_model()
        logger.info('Локальна ML-модель успішно завантажена.')
    except ModelUnavailableError as exc:
        logger.warning('AI-модель недоступна під час старту: %s', exc)
    except Exception:
        logger.exception('Неочікувана помилка під час стартової перевірки AI-модуля.')


def build_choose_purpose_context(request: Request) -> dict[str, Any]:
    ai_status = get_ai_health_status(probe=True)
    return {
        'request': request,
        'purpose_titles': PURPOSE_TITLES,
        'ai_threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
        'ai_available': bool(ai_status.get('available')),
        'ai_status_message': ai_status_message(ai_status),
        'ai_status_reason': ai_status.get('reason'),
    }


def _prepared_prediction_alternatives(prediction: dict[str, Any]) -> list[dict[str, Any]]:
    alternatives = prediction.get('alternatives') or []
    prepared_alternatives: list[dict[str, Any]] = []

    for item in alternatives:
        if not isinstance(item, dict):
            continue

        alt_purpose = item.get('purpose')
        alt_conf = item.get('confidence')
        if alt_purpose is None or alt_conf is None:
            continue

        prepared_alternatives.append(
            {
                'purpose': PURPOSE_TITLES.get(str(alt_purpose), str(alt_purpose)),
                'confidence': confidence_to_percent(float(alt_conf)),
            }
        )

    return prepared_alternatives


def detect_purpose_from_description(raw_description: Any) -> tuple[dict[str, Any], int]:
    ai_status = get_ai_health_status(probe=True)

    try:
        detect_form = PurposeDetectionFormSchema.model_validate({'description': raw_description})
    except ValidationError:
        return (
            {
                'ok': False,
                'accepted': False,
                'ai_available': bool(ai_status.get('available')),
                'message': 'Опиши потреби трохи детальніше, щоб ШІ міг коректно визначити тип ПК.',
                'tips': [
                    'Наприклад: ПК для CS2 і Dota 2 у Full HD.',
                    "Або: комп\'ютер для Excel, M.E.Doc, браузера і документів.",
                ],
                'threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            200,
        )

    description = detect_form.description

    if not ai_status.get('available'):
        return (
            {
                'ok': False,
                'accepted': False,
                'ai_available': False,
                'message': 'AI-модуль тимчасово недоступний. Автоматичне визначення типу ПК зараз вимкнене.',
                'details': ai_status_message(ai_status),
                'tips': [
                    'Обери тип ПК вручну — це працює без AI-модуля.',
                    'Перевір, чи існує файл ml/model.joblib.',
                    'Перевір, чи встановлені scikit-learn і joblib.',
                ],
                'manual_url': '/choose-purpose#manual-purpose-grid',
                'threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            503,
        )

    try:
        prediction = predict_purpose(description)
    except ModelUnavailableError as exc:
        logger.warning('AI-модель стала недоступною під час запиту: %s', exc)
        return (
            {
                'ok': False,
                'accepted': False,
                'ai_available': False,
                'message': 'AI-модуль тимчасово недоступний. Автоматичне визначення типу ПК зараз вимкнене.',
                'details': str(exc),
                'tips': [
                    'Обери тип ПК вручну — це працює без AI-модуля.',
                    'Перевір, чи існує файл ml/model.joblib.',
                    'Перевір, чи встановлені scikit-learn і joblib.',
                ],
                'manual_url': '/choose-purpose#manual-purpose-grid',
                'threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            503,
        )
    except Exception:
        logger.exception('Помилка під час AI-визначення типу ПК.')
        return (
            {
                'ok': False,
                'accepted': False,
                'ai_available': True,
                'message': 'Не вдалося обробити опис через помилку AI-модуля. Спробуй ще раз або обери тип ПК вручну.',
                'tips': ai_refinement_tips(None),
                'manual_url': '/choose-purpose#manual-purpose-grid',
                'threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            500,
        )

    raw_purpose = prediction.get('raw_purpose')
    confidence = prediction.get('confidence')
    accepted = bool(prediction.get('accepted'))
    confidence_percent = confidence_to_percent(confidence)

    purpose_title = PURPOSE_TITLES.get(raw_purpose, 'Невизначений тип') if raw_purpose else 'Невизначений тип'
    prepared_alternatives = _prepared_prediction_alternatives(prediction)
    matched_keywords = prediction.get('matched_keywords') or {}

    if accepted and raw_purpose:
        return (
            {
                'ok': True,
                'accepted': True,
                'ai_available': True,
                'purpose': raw_purpose,
                'purpose_title': purpose_title,
                'confidence': confidence,
                'confidence_percent': confidence_percent,
                'redirect_url': f'/builder/{raw_purpose}',
                'message': f'ШІ визначив сценарій: {purpose_title}. Переходимо до конфігуратора.',
                'threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
                'alternatives': prepared_alternatives,
                'matched_keywords': matched_keywords,
            },
            200,
        )

    message = 'ШІ поки не впевнений у виборі сценарію. Напиши, будь ласка, конкретніше, для чого потрібен ПК.'
    if raw_purpose and confidence_percent is not None:
        message = (
            f'ШІ припускає, що це {purpose_title.lower()}, але впевненість лише '
            f'{confidence_percent}%. Опиши потреби конкретніше, і тоді система зможе '
            'точніше визначити тип ПК.'
        )

    return (
        {
            'ok': True,
            'accepted': False,
            'ai_available': True,
            'purpose': raw_purpose,
            'purpose_title': purpose_title,
            'confidence': confidence,
            'confidence_percent': confidence_percent,
            'message': message,
            'tips': ai_refinement_tips(raw_purpose),
            'threshold_percent': int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            'alternatives': prepared_alternatives,
            'matched_keywords': matched_keywords,
        },
        200,
    )

from __future__ import annotations

import importlib


def test_detect_purpose_returns_503_when_ai_is_unavailable(monkeypatch):
    ai_service = importlib.import_module('services.ai_service')

    monkeypatch.setattr(
        ai_service,
        'get_ai_health_status',
        lambda probe=False: {'available': False, 'reason': 'model missing'},
    )

    payload, status_code = ai_service.detect_purpose_from_description('ПК для CS2 і Dota 2 у Full HD')

    assert status_code == 503
    assert payload['ai_available'] is False
    assert payload['accepted'] is False
    assert payload['manual_url'].endswith('#manual-purpose-grid')


def test_detect_purpose_accepts_prediction_and_uses_30_percent_threshold(monkeypatch):
    ai_service = importlib.import_module('services.ai_service')

    monkeypatch.setattr(
        ai_service,
        'get_ai_health_status',
        lambda probe=False: {'available': True, 'reason': None},
    )
    monkeypatch.setattr(
        ai_service,
        'predict_purpose',
        lambda text: {
            'raw_purpose': 'gaming',
            'confidence': 0.34,
            'accepted': True,
            'alternatives': [
                {'purpose': 'gaming', 'confidence': 0.34},
                {'purpose': 'creator', 'confidence': 0.21},
            ],
            'matched_keywords': {'gaming': ['cs2', 'dota 2']},
        },
    )

    payload, status_code = ai_service.detect_purpose_from_description('Потрібен ПК для CS2 і Dota 2')

    assert status_code == 200
    assert payload['accepted'] is True
    assert payload['purpose'] == 'gaming'
    assert payload['redirect_url'] == '/builder/gaming'
    assert payload['threshold_percent'] == 30

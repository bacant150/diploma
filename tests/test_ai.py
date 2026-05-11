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
    assert payload['decision_mode'] == 'manual'
    assert payload['manual_url'].endswith('#manual-purpose-grid')


def test_detect_purpose_auto_accepts_only_high_confidence_prediction(monkeypatch):
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
            'confidence': 0.78,
            'accepted': True,
            'decision_mode': 'auto',
            'margin': 0.22,
            'alternatives': [
                {'purpose': 'gaming', 'confidence': 0.78},
                {'purpose': 'creator', 'confidence': 0.19},
            ],
            'matched_keywords': {'gaming': ['cs2', 'dota2']},
            'matched_rule_signals': {'gaming': ['esports_bundle: cs2, dota2']},
        },
    )

    payload, status_code = ai_service.detect_purpose_from_description('Потрібен ПК для CS2 і Dota 2')

    assert status_code == 200
    assert payload['accepted'] is True
    assert payload['decision_mode'] == 'auto'
    assert payload['purpose'] == 'gaming'
    assert payload['redirect_url'] == '/builder/gaming'
    assert payload['auto_accept_percent'] == 70
    assert payload['confirm_percent'] == 35


def test_predict_decision_mode_requires_70_percent_for_auto_accept():
    predict_module = importlib.import_module('ml.predict')

    assert predict_module._decision_mode(0.69, 0.20) == 'confirm'
    assert predict_module._decision_mode(0.70, 0.20) == 'auto'
    assert predict_module._decision_mode(0.80, 0.05) == 'confirm'


def test_detect_purpose_requests_confirmation_for_medium_confidence(monkeypatch):
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
            'raw_purpose': 'creator',
            'confidence': 0.44,
            'accepted': False,
            'decision_mode': 'confirm',
            'margin': 0.08,
            'alternatives': [
                {'purpose': 'creator', 'confidence': 0.44},
                {'purpose': 'gaming', 'confidence': 0.39},
            ],
            'matched_keywords': {'creator': ['premierepro', 'blender']},
            'matched_rule_signals': {'creator': ['video_bundle: premierepro', 'three_d_bundle: blender']},
        },
    )

    payload, status_code = ai_service.detect_purpose_from_description('Потрібен ПК для Blender і Premiere Pro')

    assert status_code == 200
    assert payload['accepted'] is False
    assert payload['decision_mode'] == 'confirm'
    assert payload['requires_confirmation'] is True
    assert payload['suggested_purpose'] == 'creator'
    assert payload['confirm_url'] == '/builder/creator'


def test_detect_purpose_falls_back_to_manual_for_low_confidence(monkeypatch):
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
            'raw_purpose': 'study',
            'confidence': 0.24,
            'accepted': False,
            'decision_mode': 'manual',
            'margin': 0.03,
            'alternatives': [
                {'purpose': 'study', 'confidence': 0.24},
                {'purpose': 'office', 'confidence': 0.21},
            ],
            'matched_keywords': {},
            'matched_rule_signals': {},
        },
    )

    payload, status_code = ai_service.detect_purpose_from_description('Потрібен універсальний комп')

    assert status_code == 200
    assert payload['accepted'] is False
    assert payload['decision_mode'] == 'manual'
    assert payload['requires_confirmation'] is False
    assert payload['purpose'] is None
    assert payload['manual_url'].endswith('#manual-purpose-grid')


def test_load_model_is_thread_safe(monkeypatch):
    import time
    from concurrent.futures import ThreadPoolExecutor

    predict_module = importlib.import_module('ml.predict')
    sentinel_model = object()
    calls = []

    monkeypatch.setattr(predict_module, '_model', None)
    monkeypatch.setattr(predict_module, '_model_load_error', None)

    def fake_load(path):
        calls.append(path)
        time.sleep(0.02)
        return sentinel_model

    monkeypatch.setattr(predict_module.joblib, 'load', fake_load)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: predict_module.load_model(force_reload=False), range(8)))

    assert results == [sentinel_model] * 8
    assert calls == [predict_module.MODEL_PATH]

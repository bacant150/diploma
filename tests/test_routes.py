from __future__ import annotations

import importlib


def test_health_ai_route_returns_json(client, monkeypatch):
    web_routes = importlib.import_module('routes.web')

    monkeypatch.setattr(
        web_routes,
        'get_ai_health_status',
        lambda probe=True: {'available': True, 'loaded': True, 'model_exists': True, 'reason': None},
    )

    response = client.get('/health/ai')

    assert response.status_code == 200
    assert response.json()['available'] is True


def test_choose_purpose_page_opens(client, monkeypatch):
    web_routes = importlib.import_module('routes.web')

    monkeypatch.setattr(
        web_routes,
        'build_choose_purpose_context',
        lambda request: {'request': request, 'ai_available': True, 'ai_threshold_percent': 30},
    )

    response = client.get('/choose-purpose')

    assert response.status_code == 200
    assert 'choose-purpose.html' in response.text


def test_build_route_returns_result_page_without_500(client, monkeypatch):
    web_routes = importlib.import_module('routes.web')

    monkeypatch.setattr(
        web_routes,
        'build_configuration_from_form',
        lambda form: (
            {'purpose': 'office', 'budget_mode': 'manual'},
            {
                'parts': {'CPU': {'name': 'Test CPU', 'price': 5000}},
                'notes': ['ok'],
                'tier': 'budget',
                'total': 5000,
            },
        ),
    )
    monkeypatch.setattr(
        web_routes,
        'result_page_context',
        lambda request, inputs, result: {'request': request, 'inputs': inputs, 'result': result},
    )

    response = client.post('/build', data={'purpose': 'office'})

    assert response.status_code == 200
    assert 'result.html' in response.text


def test_saved_builds_page_opens(client, monkeypatch):
    saved_routes = importlib.import_module('routes.saved_builds')

    monkeypatch.setattr(saved_routes.saved_builds_repository, 'load_all', lambda: [])

    response = client.get('/saved-builds')

    assert response.status_code == 200
    assert 'saved-builds.html' in response.text

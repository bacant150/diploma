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
    monkeypatch.setattr(
        web_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: ({'id': 'profile-1', 'name': 'Тестовий профіль'}, profile_id != 'profile-1'),
    )

    response = client.get('/choose-purpose')

    assert response.status_code == 200



def test_build_route_returns_result_page_without_500_and_sets_profile_cookie(client, monkeypatch):
    web_routes = importlib.import_module('routes.web')
    monkeypatch.setattr(
        web_routes,
        'build_configuration_from_form',
        lambda form: (
            {'purpose': 'office', 'budget_mode': 'manual', 'priority': 'balanced'},
            {
                'parts': {'CPU': {'name': 'Test CPU', 'price': 5000}},
                'notes': ['ok'],
                'tier': 'budget',
                'total_price': 5000,
            },
        ),
    )
    monkeypatch.setattr(
        web_routes,
        'result_page_context',
        lambda request, inputs, result, **kwargs: {'request': request, 'inputs': inputs, 'result': result, **kwargs},
    )
    monkeypatch.setattr(
        web_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: ({'id': 'profile-1', 'name': 'Тестовий профіль'}, profile_id != 'profile-1'),
    )
    monkeypatch.setattr(
        web_routes.user_profiles_repository,
        'add_query',
        lambda profile_id, inputs, result, source='builder_form': {'id': 'query-1'},
    )

    response = client.post('/build', data={'purpose': 'office'})

    assert response.status_code == 200
    assert response.cookies.get('pcoll_profile_id') == 'profile-1'



def test_build_route_handles_failure_result_without_500(client, monkeypatch):
    web_routes = importlib.import_module('routes.web')
    monkeypatch.setattr(
        web_routes,
        'build_configuration_from_form',
        lambda form: (
            {'purpose': 'gaming', 'budget_mode': 'manual', 'priority': 'balanced'},
            {
                'parts': {},
                'notes': ['Не вдалося зібрати конфігурацію за заданими параметрами та бюджетом.'],
                'tier': None,
                'total_price': None,
                'alternatives': [],
            },
        ),
    )
    monkeypatch.setattr(
        web_routes,
        'result_page_context',
        lambda request, inputs, result, **kwargs: {'request': request, 'inputs': inputs, 'result': result, **kwargs},
    )
    monkeypatch.setattr(
        web_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: ({'id': 'profile-1', 'name': 'Тестовий профіль'}, profile_id != 'profile-1'),
    )
    monkeypatch.setattr(
        web_routes.user_profiles_repository,
        'add_query',
        lambda profile_id, inputs, result, source='builder_form': {'id': 'query-failure'},
    )

    response = client.post('/build', data={'purpose': 'gaming'})

    assert response.status_code == 200
    assert response.cookies.get('pcoll_profile_id') == 'profile-1'



def test_saved_builds_page_opens(client, monkeypatch):
    saved_routes = importlib.import_module('routes.saved_builds')
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: (
            {
                'id': 'profile-1',
                'name': 'Тестовий профіль',
                'created_at': '2026-03-31T10:00:00',
                'last_seen_at': '2026-03-31T10:00:00',
                'saved_build_ids': [],
                'query_history': [],
            },
            profile_id != 'profile-1',
        ),
    )
    monkeypatch.setattr(saved_routes.saved_builds_repository, 'load_by_profile', lambda profile_id: [])
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'prepare_for_dashboard',
        lambda profile, saved_builds_by_id=None: {
            **profile,
            'created_at_display': '31.03.2026 10:00',
            'last_seen_at_display': '31.03.2026 10:00',
            'saved_build_count': 0,
            'query_count': 0,
            'query_history': [],
        },
    )

    response = client.get('/saved-builds')

    assert response.status_code == 200



def test_profile_history_route_opens_snapshot_result(client, monkeypatch):
    saved_routes = importlib.import_module('routes.saved_builds')
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: ({'id': 'profile-1', 'name': 'Тестовий профіль'}, profile_id != 'profile-1'),
    )
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'find_query',
        lambda profile_id, query_id: {
            'id': query_id,
            'inputs': {'purpose': 'study', 'budget_mode': 'manual', 'budget': 20000, 'resolution': '1080p', 'wifi': False},
            'result_snapshot': {
                'parts': {'CPU': {'name': 'Test CPU', 'price': 5000}},
                'tier': 'budget',
                'total_price': 5000,
                'notes': [],
            },
            'saved_build_id': None,
        },
    )
    monkeypatch.setattr(
        saved_routes,
        'result_page_context',
        lambda request, inputs, result, **kwargs: {'request': request, 'inputs': inputs, 'result': result, **kwargs},
    )

    response = client.get('/profile/history/query-1')

    assert response.status_code == 200



def test_delete_profile_history_entry_redirects_and_clears_saved_build_link(client, monkeypatch):
    saved_routes = importlib.import_module('routes.saved_builds')
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: ({'id': 'profile-1', 'name': 'Тестовий профіль'}, profile_id != 'profile-1'),
    )
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'delete_query',
        lambda profile_id, query_id: {'id': query_id, 'saved_build_id': 'build-1'},
    )
    called = {'ok': False}

    def _clear_query_reference(build_id, *, profile_id=None):
        called['ok'] = build_id == 'build-1' and profile_id == 'profile-1'
        return True

    monkeypatch.setattr(saved_routes.saved_builds_repository, 'clear_query_reference', _clear_query_reference)

    response = client.post('/profile/history/query-1/delete', follow_redirects=False)

    assert response.status_code == 303
    assert response.headers['location'] == '/saved-builds?status=history_deleted'
    assert called['ok'] is True



def test_clear_profile_history_redirects_and_clears_query_references(client, monkeypatch):
    saved_routes = importlib.import_module('routes.saved_builds')
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'get_or_create',
        lambda profile_id: ({'id': 'profile-1', 'name': 'Тестовий профіль'}, profile_id != 'profile-1'),
    )
    monkeypatch.setattr(
        saved_routes.user_profiles_repository,
        'clear_query_history',
        lambda profile_id: [
            {'id': 'query-1'},
            {'id': 'query-2'},
        ],
    )
    called = {'query_ids': None}

    def _clear_query_references_for_profile(profile_id, *, query_ids=None):
        called['query_ids'] = list(query_ids or [])
        return 2

    monkeypatch.setattr(saved_routes.saved_builds_repository, 'clear_query_references_for_profile', _clear_query_references_for_profile)

    response = client.post('/profile/history/clear', follow_redirects=False)

    assert response.status_code == 303
    assert response.headers['location'] == '/saved-builds?status=history_cleared'
    assert called['query_ids'] == ['query-1', 'query-2']

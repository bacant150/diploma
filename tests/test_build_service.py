from __future__ import annotations

import importlib


class FakeForm:
    def __init__(self, data: dict[str, object] | None = None, list_data: dict[str, list[str]] | None = None):
        self._data = data or {}
        self._list_data = list_data or {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def getlist(self, key: str) -> list[str]:
        return list(self._list_data.get(key, []))


def test_validate_build_result_maps_total_to_total_price():
    build_service = importlib.import_module('services.build_service')

    result = build_service.validate_build_result(
        {
            'parts': {
                'CPU': {'name': 'Test CPU', 'price': 12000},
                'RAM': {'name': 'Test RAM', 'price': 3000},
            },
            'total': 15000,
            'tier': 'mid',
            'notes': ['ok'],
        }
    )

    assert result['parts']['CPU']['name'] == 'Test CPU'
    assert result.get('total_price') == 15000


def test_validate_build_result_calculates_total_price_from_parts_when_missing():
    build_service = importlib.import_module('services.build_service')

    result = build_service.validate_build_result(
        {
            'parts': {
                'CPU': {'name': 'Test CPU', 'price': 7000},
                'RAM': {'name': 'Test RAM', 'price': 2500},
                'SSD': {'name': 'Test SSD', 'price': 1800},
            },
            'tier': 'budget',
            'notes': [],
        }
    )

    assert result.get('total_price') == 11300


def test_build_configuration_from_form_returns_failure_state_for_empty_build(monkeypatch):
    build_service = importlib.import_module('services.build_service')

    monkeypatch.setattr(
        build_service,
        'extract_user_inputs',
        lambda form: {'purpose': 'gaming', 'budget_mode': 'manual', 'budget': 25000, 'priority': 'balanced'},
    )
    monkeypatch.setattr(build_service, 'build_pc_payload', lambda inputs: {'purpose': 'gaming', 'budget': 25000, 'priority': 'balanced'})
    monkeypatch.setattr(
        build_service,
        '_run_primary_build',
        lambda payload, *, budget_mode: {
            'parts': {},
            'tier': 'budget',
            'notes': ['Не вдалося зібрати ПК у межах бюджету.'],
        },
    )

    called = {'alternatives': False}

    def _run_alts(*args, **kwargs):
        called['alternatives'] = True
        return []

    monkeypatch.setattr(build_service, '_run_alternative_builds', _run_alts)
    monkeypatch.setattr(build_service, 'attach_part_images', lambda result: result)

    inputs, result = build_service.build_configuration_from_form(FakeForm())

    assert inputs['purpose'] == 'gaming'
    assert result.get('parts') == {}
    assert result.get('tier') is None
    assert result.get('total_price') in (None, 0)
    assert result.get('alternatives') == []
    assert any('Не вдалося' in note for note in result.get('notes', []))
    assert called['alternatives'] is False


def test_build_configuration_from_form_keeps_valid_build_with_parts_and_total(monkeypatch):
    build_service = importlib.import_module('services.build_service')

    monkeypatch.setattr(
        build_service,
        'extract_user_inputs',
        lambda form: {'purpose': 'study', 'budget_mode': 'manual', 'budget': 30000, 'priority': 'balanced'},
    )
    monkeypatch.setattr(build_service, 'build_pc_payload', lambda inputs: {'purpose': 'study', 'budget': 30000, 'priority': 'balanced'})
    monkeypatch.setattr(
        build_service,
        '_run_primary_build',
        lambda payload, *, budget_mode: {
            'parts': {
                'CPU': {'name': 'Test CPU', 'price': 5000},
                'Motherboard': {'name': 'Test MB', 'price': 3500},
            },
            'total': 8500,
            'tier': 'budget',
            'notes': ['ok'],
        },
    )
    monkeypatch.setattr(
        build_service,
        '_run_alternative_builds',
        lambda result, payload, *, budget_mode: [
            {
                'is_primary': True,
                'title': 'Основна',
                '_result': {
                    'parts': {
                        'CPU': {'name': 'Test CPU', 'price': 5000},
                        'Motherboard': {'name': 'Test MB', 'price': 3500},
                    },
                    'total': 8500,
                    'tier': 'budget',
                    'notes': ['ok'],
                },
            }
        ],
    )
    monkeypatch.setattr(build_service, 'attach_part_images', lambda result: result)

    _, result = build_service.build_configuration_from_form(FakeForm())

    assert result.get('tier') == 'budget'
    assert result.get('total_price') == 8500
    assert result.get('parts', {}).get('CPU', {}).get('name') == 'Test CPU'
    assert isinstance(result.get('alternatives'), list)
    assert result['alternatives']
    assert result['alternatives'][0]['result_payload']['total_price'] == 8500


def test_build_configuration_from_form_auto_budget_keeps_recommended_budget_note(monkeypatch):
    build_service = importlib.import_module('services.build_service')

    monkeypatch.setattr(
        build_service,
        'extract_user_inputs',
        lambda form: {'purpose': 'study', 'budget_mode': 'auto', 'budget': 0, 'priority': 'balanced'},
    )
    monkeypatch.setattr(build_service, 'build_pc_payload', lambda inputs: {'purpose': 'study', 'budget': 0, 'priority': 'balanced'})
    monkeypatch.setattr(
        build_service,
        '_run_primary_build',
        lambda payload, *, budget_mode: {
            'parts': {
                'CPU': {'name': 'Study CPU', 'price': 6500},
                'RAM': {'name': 'Study RAM', 'price': 2600},
                'SSD': {'name': 'Study SSD', 'price': 1900},
            },
            'tier': 'mid',
            'notes': [
                'Бюджет підібрано автоматично. Рекомендований бюджет: 20000 грн.',
                'Конфігурація добре підходить для навчання.',
            ],
        },
    )
    monkeypatch.setattr(build_service, '_run_alternative_builds', lambda *args, **kwargs: [])
    monkeypatch.setattr(build_service, 'attach_part_images', lambda result: result)

    _, result = build_service.build_configuration_from_form(FakeForm())

    assert result.get('total_price') == 11000
    assert any('Рекомендований бюджет' in note for note in result.get('notes', []))

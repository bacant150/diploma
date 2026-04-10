from __future__ import annotations

import importlib
import logging

import pytest
from fastapi import HTTPException

from builder_engine.common import _pick_motherboard, _pick_psu, _pick_ram
from parts_db import Part


class FakeForm:
    def __init__(self, data: dict[str, object] | None = None, list_data: dict[str, list[str]] | None = None):
        self._data = data or {}
        self._list_data = list_data or {}

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def getlist(self, key: str) -> list[str]:
        return list(self._list_data.get(key, []))


def test_build_pc_logs_warning_for_too_small_budget(caplog: pytest.LogCaptureFixture) -> None:
    builder = importlib.import_module('builder')

    with caplog.at_level(logging.WARNING, logger='pcbuilder.builder.core'):
        result = builder.build_pc(
            budget=6000,
            purpose='gaming',
            resolution='1080p',
            wifi=False,
        )

    assert result['tier'] == 'budget'
    assert 'надто малим бюджетом' in caplog.text


def test_build_configuration_logs_warning_for_failed_result(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
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
    monkeypatch.setattr(build_service, '_run_alternative_builds', lambda *args, **kwargs: [])
    monkeypatch.setattr(build_service, 'attach_part_images', lambda result: result)

    with caplog.at_level(logging.WARNING, logger='pcbuilder.services.build'):
        _, result = build_service.build_configuration_from_form(FakeForm())

    assert result['parts'] == {}
    assert 'завершилася без валідного складу' in caplog.text


def test_build_configuration_logs_validation_failure(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    build_service = importlib.import_module('services.build_service')

    def _raise_validation_error(_form):
        from pydantic import ValidationError
        from schemas import BuildInputsSchema

        raise ValidationError.from_exception_data(
            BuildInputsSchema.__name__,
            [
                {
                    'type': 'value_error',
                    'loc': ('budget',),
                    'msg': 'Budget invalid',
                    'input': 'abc',
                    'ctx': {'error': 'Budget invalid'},
                }
            ],
        )

    monkeypatch.setattr(build_service, 'extract_user_inputs', _raise_validation_error)

    with caplog.at_level(logging.WARNING, logger='pcbuilder.services.build'):
        with pytest.raises(HTTPException) as excinfo:
            build_service.build_configuration_from_form(FakeForm())

    assert excinfo.value.status_code == 400
    assert 'Валідація форми побудови конфігурації не пройдена' in caplog.text


def test_detect_purpose_logs_unavailable_ai(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    ai_service = importlib.import_module('services.ai_service')
    monkeypatch.setattr(
        ai_service,
        'get_ai_health_status',
        lambda probe=False: {'available': False, 'reason': 'model missing'},
    )

    with caplog.at_level(logging.WARNING, logger='pcbuilder.ai'):
        payload, status_code = ai_service.detect_purpose_from_description('ПК для CS2 і Dota 2 у Full HD')

    assert status_code == 503
    assert payload['ai_available'] is False
    assert 'AI-модуль недоступний під час запиту визначення сценарію' in caplog.text


def test_pick_motherboard_logs_wifi_fallback(caplog: pytest.LogCaptureFixture) -> None:
    cpu = Part('cpu', 'Test CPU', 5000, {'socket': 'LGA1700'})

    with caplog.at_level(logging.INFO, logger='pcbuilder.builder.selection'):
        selected = _pick_motherboard(cpu, wifi=True, max_price=4700)

    assert selected is not None
    assert 'fallback без Wi-Fi' in caplog.text


def test_pick_ram_logs_size_fallback(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger='pcbuilder.builder.selection'):
        selected = _pick_ram('DDR4', [999, 8], 5000)

    assert selected is not None
    assert selected.meta.get('size_gb') == 8
    assert 'RAM підібрано через fallback за обсягом' in caplog.text


def test_pick_psu_logs_wattage_fallback(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger='pcbuilder.builder.selection'):
        selected = _pick_psu(5000, 10000)

    assert selected is not None
    assert 'БЖ потрібної потужності не знайдено, використовується fallback' in caplog.text

from __future__ import annotations

from builder import build_pc, build_pc_alternatives


def _office_payload(**overrides):
    payload = {
        'budget': 22000,
        'purpose': 'office',
        'resolution': '1080p',
        'wifi': False,
        'games': [],
        'graphics_quality': 'high',
        'target_fps': 60,
        'gpu_mode': 'auto',
        'cpu_brand': 'auto',
        'gpu_brand': 'auto',
        'ram_size': 'auto',
        'ssd_size': 'auto',
        'memory_platform': 'auto',
        'office_apps': [],
        'office_tabs': 'auto',
        'office_monitors': 'auto',
        'study_apps': [],
        'study_tabs': 'auto',
        'study_monitors': 'auto',
        'creator_apps': [],
        'creator_project_complexity': 'auto',
        'creator_monitors': 'auto',
        'priority': 'balanced',
    }
    payload.update(overrides)
    return payload


def test_build_pc_office_returns_core_structure():
    result = build_pc(**_office_payload())

    assert isinstance(result, dict)
    assert isinstance(result.get('parts'), dict)
    assert result['parts']

    for required_key in ['CPU', 'Motherboard', 'RAM', 'SSD', 'PSU', 'Case']:
        assert required_key in result['parts']

    total_value = result.get('total_price') or result.get('total') or 0
    assert total_value > 0
    assert isinstance(result.get('notes'), list)
    assert result.get('tier') in {'budget', 'mid', 'upper'}


def test_build_pc_alternatives_returns_cards_for_manual_budget():
    payload = _office_payload(priority='balanced')
    primary_result = build_pc(**payload)
    alternatives = build_pc_alternatives(primary_result, budget_mode='manual', **payload)

    assert isinstance(alternatives, list)
    assert alternatives

    first_card = alternatives[0]
    assert isinstance(first_card, dict)
    assert first_card.get('is_primary') is True
    assert first_card.get('title') or first_card.get('label') or first_card.get('name')
    assert isinstance(first_card.get('_result'), dict)

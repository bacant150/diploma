from __future__ import annotations

from builder import build_pc, build_pc_alternatives, build_pc_auto_budget


def _payload(**overrides):
    payload = {
        'budget': 60000,
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


def _total_value(result: dict) -> int | float:
    return result.get('total_price') or result.get('total') or 0


def test_build_pc_office_returns_core_structure():
    result = build_pc(**_payload(purpose='office', budget=30000))

    assert isinstance(result, dict)
    assert isinstance(result.get('parts'), dict)
    assert result['parts']
    for required_key in ['CPU', 'Motherboard', 'RAM', 'SSD', 'PSU', 'Case']:
        assert required_key in result['parts']
    assert _total_value(result) > 0
    assert isinstance(result.get('notes'), list)
    assert result.get('tier') in {'budget', 'mid', 'upper'}


def test_build_pc_alternatives_returns_cards_for_manual_budget():
    payload = _payload(purpose='office', budget=30000, priority='balanced')
    primary_result = build_pc(**payload)
    alternatives = build_pc_alternatives(primary_result, budget_mode='manual', **payload)

    assert isinstance(alternatives, list)
    assert alternatives
    first_card = alternatives[0]
    assert isinstance(first_card, dict)
    assert first_card.get('is_primary') is True
    assert first_card.get('title') or first_card.get('label') or first_card.get('name')
    assert isinstance(first_card.get('_result'), dict)


def test_build_pc_study_default_payload_returns_non_empty_parts():
    result = build_pc(**_payload(purpose='study', budget=40000))

    assert isinstance(result, dict)
    assert result.get('parts')
    assert _total_value(result) > 0



def test_build_pc_gaming_default_payload_returns_non_empty_parts():
    result = build_pc(**_payload(purpose='gaming', budget=80000, games=[], graphics_quality='high', target_fps=60))

    assert isinstance(result, dict)
    assert result.get('parts')
    assert 'GPU' in result.get('parts', {})
    assert _total_value(result) > 0



def test_build_pc_creator_with_premiere_does_not_crash():
    result = build_pc(
        **_payload(
            purpose='creator',
            budget=120000,
            creator_apps=['premiere'],
            creator_project_complexity='auto',
            creator_monitors='auto',
        )
    )

    assert isinstance(result, dict)
    assert result.get('parts')
    assert _total_value(result) > 0



def test_build_pc_auto_budget_returns_real_total():
    result = build_pc_auto_budget(
        purpose='study',
        resolution='1080p',
        wifi=False,
        games=[],
        graphics_quality='high',
        target_fps=60,
        gpu_mode='auto',
        cpu_brand='auto',
        gpu_brand='auto',
        ram_size='auto',
        ssd_size='auto',
        memory_platform='auto',
        office_apps=[],
        office_tabs='auto',
        office_monitors='auto',
        study_apps=[],
        study_tabs='auto',
        study_monitors='auto',
        creator_apps=[],
        creator_project_complexity='auto',
        creator_monitors='auto',
        priority='balanced',
    )

    assert isinstance(result, dict)
    assert result.get('parts')
    assert _total_value(result) > 0


def test_build_pc_alternatives_office_low_budget_keeps_primary_card():
    payload = _payload(purpose='office', budget=16500, priority='balanced', office_apps=['excel'])
    primary_result = build_pc(**payload)

    alternatives = build_pc_alternatives(primary_result, budget_mode='manual', **payload)

    assert alternatives
    assert alternatives[0].get('is_primary') is True
    assert alternatives[0].get('_result', {}).get('parts')



def test_build_pc_gaming_returns_psu_without_power_error():
    result = build_pc(**_payload(purpose='gaming', budget=85000, priority='best', games=['cs2', 'cyberpunk_2077']))

    compatibility = result.get('compatibility') or {}
    psu_errors = [item for item in compatibility.get('errors', []) if 'БЖ' in item or 'потужн' in item]

    assert result.get('parts')
    assert not psu_errors

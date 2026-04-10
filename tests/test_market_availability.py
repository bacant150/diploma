from __future__ import annotations

from parts_db import Part
from builder_engine.common import _pick_best, _pick_cheapest, _result
from builder_engine.recommendations import _auto_budget_candidate_score, _market_summary_from_parts
from utils.assets import attach_part_images


def test_pick_best_prefers_in_stock_part_when_affordable():
    unavailable = Part('gpu', 'Unavailable GPU', 12000, {'in_stock': False, 'vram': 8, 'tier': 'mid'})
    available = Part('gpu', 'Available GPU', 11500, {'in_stock': True, 'vram': 8, 'tier': 'mid'})

    selected = _pick_best([unavailable, available], max_price=13000)

    assert selected is not None
    assert selected.name == 'Available GPU'


def test_pick_cheapest_prefers_known_available_part():
    unknown = Part('ssd', 'Unknown SSD', 2000, {'in_stock': None, 'size_gb': 1000})
    available = Part('ssd', 'Available SSD', 2200, {'in_stock': True, 'size_gb': 1000})

    selected = _pick_cheapest([unknown, available], max_price=2500)

    assert selected is not None
    assert selected.name == 'Available SSD'


def test_result_includes_market_metadata_for_parts():
    cpu = Part('cpu', 'CPU Test', 5000, {
        'store': 'Rozetka',
        'source_used': 'rozetka',
        'availability': 'Є в наявності',
        'in_stock': True,
        'checked_at': '2026-04-07T12:00:00',
        'product_url': 'https://example.com/cpu',
    })

    result = _result({'CPU': cpu}, ['ok'], 'budget', 7000)
    cpu_payload = result['parts']['CPU']

    assert cpu_payload['store'] == 'Rozetka'
    assert cpu_payload['in_stock'] is True
    assert cpu_payload['product_url'] == 'https://example.com/cpu'


def test_auto_budget_candidate_score_penalizes_out_of_stock_build():
    in_stock_result = {
        'parts': {
            'CPU': {'name': 'A', 'price': 5000, 'in_stock': True},
            'RAM': {'name': 'B', 'price': 2500, 'in_stock': True},
        },
        'total': 7500,
        'office_requirement': {},
    }
    out_of_stock_result = {
        'parts': {
            'CPU': {'name': 'A', 'price': 5000, 'in_stock': False},
            'RAM': {'name': 'B', 'price': 2500, 'in_stock': True},
        },
        'total': 7500,
        'office_requirement': {},
    }

    assert _auto_budget_candidate_score(in_stock_result, 'office') > _auto_budget_candidate_score(out_of_stock_result, 'office')


def test_attach_part_images_formats_market_metadata_without_losing_fields():
    result = attach_part_images({
        'parts': {
            'CPU': {
                'name': 'CPU Test',
                'price': 5000,
                'source_used': 'local',
                'availability': 'Наявність невідома',
                'in_stock': None,
                'checked_at': '2026-04-07T12:00:00',
            }
        }
    })

    cpu = result['parts']['CPU']
    assert cpu['store'] == 'Локальна база'
    assert cpu['checked_at_display'] == '07.04.2026 12:00'
    assert cpu['availability'] == 'Наявність невідома'


def test_market_summary_counts_stock_states():
    summary = _market_summary_from_parts({
        'CPU': {'in_stock': True},
        'GPU': {'in_stock': False},
        'SSD': {'in_stock': None},
    })

    assert summary['total'] == 3
    assert summary['in_stock'] == 1
    assert summary['out_of_stock'] == 1
    assert summary['unknown'] == 1

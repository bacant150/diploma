from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from config import STATIC_DIR


def slugify_part_name(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug or 'part'


def part_image_path(part_name: str) -> str | None:
    filename = f'{slugify_part_name(part_name)}.webp'
    image_file = STATIC_DIR / 'images' / 'parts' / filename
    if image_file.exists():
        return f'/static/images/parts/{filename}'
    return None


def attach_part_images(result: dict[str, Any]) -> dict[str, Any]:
    parts = result.get('parts', {})
    if isinstance(parts, dict):
        for part_data in parts.values():
            if not isinstance(part_data, dict):
                continue
            _normalize_part_market_meta(part_data)
            name = part_data.get('name')
            if name:
                part_data['image'] = part_image_path(name)
                part_data['image_filename'] = f'{slugify_part_name(name)}.webp'

    alternatives = result.get('alternatives', [])
    if isinstance(alternatives, list):
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                continue
            alternative_parts = alternative.get('parts', [])

            if isinstance(alternative_parts, dict):
                iterable_parts = alternative_parts.values()
            elif isinstance(alternative_parts, list):
                iterable_parts = alternative_parts
            else:
                continue

            for part_data in iterable_parts:
                if not isinstance(part_data, dict):
                    continue
                _normalize_part_market_meta(part_data)
                name = part_data.get('name')
                if name:
                    part_data['image'] = part_image_path(name)
                    part_data['image_filename'] = f'{slugify_part_name(name)}.webp'
    return result


def _format_checked_at(value: Any) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
        return dt.strftime('%d.%m.%Y %H:%M')
    except ValueError:
        return text



def _normalize_part_market_meta(part_data: dict[str, Any]) -> None:
    store = str(part_data.get('store') or '').strip()
    source_used = str(part_data.get('source_used') or '').strip().lower()
    if source_used == 'rozetka' and (not store or store.lower() == 'rozetka'):
        store = 'Rozetka'
    elif source_used == 'local' and (not store or store.lower() == 'local'):
        store = 'Локальна база'
    elif not store and source_used:
        store = source_used
    if store:
        part_data['store'] = store

    if 'product_url' not in part_data and part_data.get('rozetka_url'):
        part_data['product_url'] = part_data.get('rozetka_url')

    checked_at_display = _format_checked_at(part_data.get('checked_at'))
    if checked_at_display:
        part_data['checked_at_display'] = checked_at_display

    availability = part_data.get('availability')
    if availability is None and part_data.get('in_stock') is True:
        availability = 'Є в наявності'
    elif availability is None and part_data.get('in_stock') is False:
        availability = 'Немає в наявності'
    if availability:
        part_data['availability'] = availability

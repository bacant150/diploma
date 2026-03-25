from __future__ import annotations

import re
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
                name = part_data.get('name')
                if name:
                    part_data['image'] = part_image_path(name)
                    part_data['image_filename'] = f'{slugify_part_name(name)}.webp'
    return result

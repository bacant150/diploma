from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError


def validation_error_messages(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        location = '.'.join(str(part) for part in error.get('loc', []))
        message = str(error.get('msg', 'Некоректне значення.'))
        messages.append(f'{location}: {message}' if location else message)
    return messages


def extract_json_object(value: Any, *, field_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or '{}'))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f'Поле {field_name} містить невалідний JSON.') from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail=f'Поле {field_name} має містити JSON-об’єкт.')

    return payload


def serialize_for_template(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def confidence_to_percent(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value * 100))


def ai_refinement_tips(purpose: str | None) -> list[str]:
    if purpose == 'gaming':
        return [
            'Вкажи конкретні ігри, наприклад Dota 2, CS2, GTA 5 або Fortnite.',
            'Додай бажаний FPS або роздільну здатність, якщо це важливо.',
        ]
    if purpose == 'office':
        return [
            'Перелічи офісні програми: Word, Excel, M.E.Doc, BAS, CRM, браузер.',
            'Уточни, чи потрібні бухгалтерські задачі, багато вкладок або два монітори.',
        ]
    if purpose == 'study':
        return [
            'Напиши, чи потрібні Zoom, Google Meet, VS Code, Python або інші навчальні програми.',
            'Уточни, чи це навчання, програмування чи дистанційні заняття.',
        ]
    if purpose == 'creator':
        return [
            'Вкажи програми: Blender, Premiere Pro, Photoshop, AutoCAD, Maya тощо.',
            'Уточни, чи потрібен монтаж відео, 3D-моделювання, дизайн або рендер.',
        ]
    return [
        'Опиши, для чого потрібен ПК: ігри, офіс, навчання чи монтаж / 3D.',
        'Додай конкретні ігри або програми, з якими будеш працювати.',
    ]

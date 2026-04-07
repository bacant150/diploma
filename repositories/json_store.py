from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def _write_empty_list(file_path: Path) -> None:
    _ensure_parent_dir(file_path)
    file_path.write_text("[]\n", encoding="utf-8")


def _backup_broken_file(file_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = file_path.with_name(
        f"{file_path.stem}.broken-{timestamp}{file_path.suffix}.bak"
    )
    file_path.replace(backup_path)
    return backup_path


def read_json_list(file_path: Path, *, logger: Any, label: str) -> list[Any]:
    """Safely read a JSON list, auto-recovering missing or broken files."""
    if not file_path.exists():
        _write_empty_list(file_path)
        logger.info("Створено порожній JSON-файл для %s: %s", label, file_path)
        return []

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        try:
            backup_path = _backup_broken_file(file_path)
            logger.exception(
                "Пошкоджений JSON для %s. Створено резервну копію: %s",
                label,
                backup_path,
            )
        except OSError:
            logger.exception(
                "Пошкоджений JSON для %s, але не вдалося створити резервну копію: %s",
                label,
                file_path,
            )
        _write_empty_list(file_path)
        return []
    except OSError:
        logger.exception("Не вдалося прочитати файл %s: %s", label, file_path)
        return []

    if isinstance(payload, list):
        return payload

    try:
        backup_path = _backup_broken_file(file_path)
        logger.warning(
            "%s має неочікувану структуру. Очікувався список. Файл перенесено в %s",
            label,
            backup_path,
        )
    except OSError:
        logger.exception(
            "%s має неочікувану структуру і не вдалося створити резервну копію: %s",
            label,
            file_path,
        )
    _write_empty_list(file_path)
    return []


def write_json_list(file_path: Path, payload: list[Any], *, logger: Any, label: str) -> None:
    _ensure_parent_dir(file_path)
    try:
        file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        logger.exception("Не вдалося записати файл %s: %s", label, file_path)
        raise

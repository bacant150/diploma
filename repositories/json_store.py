from __future__ import annotations

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

_FILE_LOCKS_GUARD = threading.Lock()
_FILE_LOCKS: dict[Path, threading.RLock] = {}


def _normalized_path(file_path: Path) -> Path:
    return Path(file_path).resolve()


def _get_file_lock(file_path: Path) -> threading.RLock:
    normalized_path = _normalized_path(file_path)
    with _FILE_LOCKS_GUARD:
        lock = _FILE_LOCKS.get(normalized_path)
        if lock is None:
            lock = threading.RLock()
            _FILE_LOCKS[normalized_path] = lock
        return lock


@contextmanager
def locked_json_file(file_path: Path) -> Iterator[None]:
    """Lock all read-modify-write operations for one JSON file inside the process."""
    lock = _get_file_lock(file_path)
    with lock:
        yield


def _ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def _write_text_atomic(file_path: Path, text: str) -> None:
    _ensure_parent_dir(file_path)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(text)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)
        os.replace(temp_path, file_path)
    except Exception:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def _write_empty_list_unlocked(file_path: Path) -> None:
    _write_text_atomic(file_path, "[]\n")


def _backup_broken_file(file_path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = file_path.with_name(
        f"{file_path.stem}.broken-{timestamp}{file_path.suffix}.bak"
    )
    file_path.replace(backup_path)
    return backup_path


def _read_json_list_unlocked(file_path: Path, *, logger: Any, label: str) -> list[Any]:
    """Safely read a JSON list, auto-recovering missing or broken files."""
    if not file_path.exists():
        _write_empty_list_unlocked(file_path)
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
        _write_empty_list_unlocked(file_path)
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
    _write_empty_list_unlocked(file_path)
    return []


def read_json_list(file_path: Path, *, logger: Any, label: str) -> list[Any]:
    with locked_json_file(file_path):
        return _read_json_list_unlocked(file_path, logger=logger, label=label)


def _write_json_list_unlocked(
    file_path: Path,
    payload: list[Any],
    *,
    logger: Any,
    label: str,
) -> None:
    try:
        _write_text_atomic(
            file_path,
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        )
    except OSError:
        logger.exception("Не вдалося записати файл %s: %s", label, file_path)
        raise


def write_json_list(file_path: Path, payload: list[Any], *, logger: Any, label: str) -> None:
    with locked_json_file(file_path):
        _write_json_list_unlocked(file_path, payload, logger=logger, label=label)

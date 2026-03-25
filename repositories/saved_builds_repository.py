from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from config import PURPOSE_TITLES, SAVED_BUILDS_FILE, TIER_TITLES
from schemas import SavedBuildRecordSchema
from utils.validation import validation_error_messages

logger = logging.getLogger('pcbuilder.saved_builds')


class SavedBuildsRepository:
    def __init__(self, file_path=SAVED_BUILDS_FILE):
        self.file_path = file_path

    def load_all(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            return []

        try:
            raw_saved_builds = json.loads(self.file_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(raw_saved_builds, list):
            logger.warning('saved_builds.json має неочікувану структуру. Очікувався список.')
            return []

        validated_builds: list[dict[str, Any]] = []
        for raw_build in raw_saved_builds:
            if not isinstance(raw_build, dict):
                continue
            try:
                build = SavedBuildRecordSchema.model_validate(raw_build)
            except Exception as exc:
                message = str(exc)
                if hasattr(exc, 'errors'):
                    message = '; '.join(validation_error_messages(exc))
                logger.warning('Пропущено некоректну збережену збірку: %s', message)
                continue
            validated_builds.append(build.model_dump(mode='json'))

        return validated_builds

    def write_all(self, saved_builds: list[dict[str, Any]]) -> None:
        normalized_builds: list[dict[str, Any]] = []
        for raw_build in saved_builds:
            build = SavedBuildRecordSchema.model_validate(raw_build)
            normalized_builds.append(build.model_dump(mode='json'))

        self.file_path.write_text(
            json.dumps(normalized_builds, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def find_by_id(self, build_id: str) -> dict[str, Any] | None:
        for build in self.load_all():
            if build.get('id') == build_id:
                return build
        return None

    def prepare_for_list(self, build: dict[str, Any]) -> dict[str, Any]:
        prepared = dict(build)
        inputs = prepared.get('inputs', {})
        result = prepared.get('result', {})
        prepared['purpose_title'] = PURPOSE_TITLES.get(inputs.get('purpose', ''), inputs.get('purpose', 'Збірка'))
        prepared['tier_title'] = TIER_TITLES.get(result.get('tier', ''), result.get('tier', '—'))

        saved_at = prepared.get('saved_at')
        try:
            prepared['saved_at_display'] = datetime.fromisoformat(saved_at).strftime('%d.%m.%Y %H:%M') if saved_at else 'Без дати'
        except ValueError:
            prepared['saved_at_display'] = saved_at or 'Без дати'

        return prepared


saved_builds_repository = SavedBuildsRepository()

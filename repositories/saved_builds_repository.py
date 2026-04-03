from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from config import PRIORITY_TITLES, PURPOSE_TITLES, SAVED_BUILDS_FILE, TIER_TITLES
from schemas import SavedBuildRecordSchema
from utils.validation import validation_error_messages

logger = logging.getLogger('pcbuilder.saved_builds')


class SavedBuildsRepository:
    def __init__(self, file_path=SAVED_BUILDS_FILE):
        self.file_path = file_path

    def load_all(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            logger.info('Файл збережених збірок ще не існує: %s', self.file_path)
            return []

        try:
            raw_saved_builds = json.loads(self.file_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            logger.exception('Не вдалося прочитати saved_builds.json через JSONDecodeError.')
            return []
        except OSError:
            logger.exception('Не вдалося прочитати файл збережених збірок: %s', self.file_path)
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

        logger.info('Завантажено збережені збірки: count=%s', len(validated_builds))
        return validated_builds

    def load_by_profile(self, profile_id: str) -> list[dict[str, Any]]:
        normalized_profile_id = str(profile_id or '').strip()
        if not normalized_profile_id:
            logger.warning('Спроба завантажити збірки без profile_id.')
            return []
        builds = [
            build
            for build in self.load_all()
            if build.get('profile_id') in {None, '', normalized_profile_id}
        ]
        logger.info('Завантажено збірки профілю: profile_id=%s count=%s', normalized_profile_id, len(builds))
        return builds

    def write_all(self, saved_builds: list[dict[str, Any]]) -> None:
        normalized_builds: list[dict[str, Any]] = []
        for raw_build in saved_builds:
            build = SavedBuildRecordSchema.model_validate(raw_build)
            normalized_builds.append(build.model_dump(mode='json'))

        self.file_path.write_text(
            json.dumps(normalized_builds, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        logger.info('Записано збережені збірки у файл: path=%s count=%s', self.file_path, len(normalized_builds))

    def find_by_id(self, build_id: str, *, profile_id: str | None = None) -> dict[str, Any] | None:
        normalized_profile_id = str(profile_id or '').strip()
        for build in self.load_all():
            if build.get('id') != build_id:
                continue
            build_profile_id = str(build.get('profile_id') or '').strip()
            if normalized_profile_id and build_profile_id and build_profile_id != normalized_profile_id:
                logger.warning(
                    'Збірку знайдено, але доступ до неї заборонено іншим profile_id: requested=%s actual=%s build_id=%s',
                    normalized_profile_id,
                    build_profile_id,
                    build_id,
                )
                continue
            logger.info('Знайдено збережену збірку: build_id=%s profile_id=%s', build_id, build_profile_id or 'legacy')
            return build
        logger.info('Збережену збірку не знайдено: build_id=%s profile_id=%s', build_id, normalized_profile_id or 'any')
        return None

    def clear_query_reference(self, build_id: str, *, profile_id: str | None = None) -> bool:
        normalized_build_id = str(build_id or '').strip()
        normalized_profile_id = str(profile_id or '').strip()
        if not normalized_build_id:
            return False

        builds = self.load_all()
        updated = False
        for build in builds:
            if str(build.get('id') or '').strip() != normalized_build_id:
                continue
            build_profile_id = str(build.get('profile_id') or '').strip()
            if normalized_profile_id and build_profile_id and build_profile_id != normalized_profile_id:
                continue
            if build.get('query_id') is None:
                logger.info('У збірки вже очищено query reference: build_id=%s', normalized_build_id)
                return True
            build['query_id'] = None
            updated = True
            break

        if updated:
            self.write_all(builds)
            logger.info('Очищено query reference у збереженої збірки: build_id=%s profile_id=%s', normalized_build_id, normalized_profile_id or 'any')
        return updated

    def clear_query_references_for_profile(self, profile_id: str, *, query_ids: list[str] | None = None) -> int:
        normalized_profile_id = str(profile_id or '').strip()
        normalized_query_ids = {str(query_id or '').strip() for query_id in (query_ids or []) if str(query_id or '').strip()}
        if not normalized_profile_id:
            return 0

        builds = self.load_all()
        updated_count = 0
        updated = False
        for build in builds:
            build_profile_id = str(build.get('profile_id') or '').strip()
            if build_profile_id and build_profile_id != normalized_profile_id:
                continue
            query_id = str(build.get('query_id') or '').strip()
            if not query_id:
                continue
            if normalized_query_ids and query_id not in normalized_query_ids:
                continue
            build['query_id'] = None
            updated = True
            updated_count += 1

        if updated:
            self.write_all(builds)
            logger.info(
                'Очищено query references для профілю: profile_id=%s cleared=%s filter_count=%s',
                normalized_profile_id,
                updated_count,
                len(normalized_query_ids),
            )
        return updated_count

    def prepare_for_list(self, build: dict[str, Any]) -> dict[str, Any]:
        prepared = dict(build)
        inputs = prepared.get('inputs', {})
        result = prepared.get('result', {})
        prepared['purpose_title'] = PURPOSE_TITLES.get(inputs.get('purpose', ''), inputs.get('purpose', 'Збірка'))
        prepared['tier_title'] = TIER_TITLES.get(result.get('tier', ''), result.get('tier', '—'))
        prepared['priority_title'] = PRIORITY_TITLES.get(inputs.get('priority', ''), inputs.get('priority', '—'))
        prepared['total_display'] = result.get('total') or result.get('total_price') or 0

        saved_at = prepared.get('saved_at')
        try:
            prepared['saved_at_display'] = datetime.fromisoformat(saved_at).strftime('%d.%m.%Y %H:%M') if saved_at else 'Без дати'
        except ValueError:
            prepared['saved_at_display'] = saved_at or 'Без дати'

        return prepared


saved_builds_repository = SavedBuildsRepository()

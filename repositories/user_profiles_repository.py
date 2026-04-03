from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from config import PRIORITY_TITLES, PURPOSE_TITLES, TIER_TITLES, USER_PROFILES_FILE
from schemas import BuildResultSchema, QueryHistoryRecordSchema, QueryResultSummarySchema, UserProfileRecordSchema
from utils.validation import validation_error_messages

logger = logging.getLogger('pcbuilder.user_profiles')

MAX_HISTORY_ITEMS = 50


class UserProfilesRepository:
    def __init__(self, file_path=USER_PROFILES_FILE):
        self.file_path = file_path

    def load_all(self) -> list[dict[str, Any]]:
        if not self.file_path.exists():
            logger.info('Файл профілів ще не існує: %s', self.file_path)
            return []

        try:
            raw_profiles = json.loads(self.file_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            logger.exception('Не вдалося прочитати user_profiles.json через JSONDecodeError.')
            return []
        except OSError:
            logger.exception('Не вдалося прочитати файл профілів: %s', self.file_path)
            return []

        if not isinstance(raw_profiles, list):
            logger.warning('user_profiles.json має неочікувану структуру. Очікувався список.')
            return []

        validated_profiles: list[dict[str, Any]] = []
        for raw_profile in raw_profiles:
            if not isinstance(raw_profile, dict):
                continue
            try:
                profile = UserProfileRecordSchema.model_validate(raw_profile)
            except Exception as exc:
                message = str(exc)
                if hasattr(exc, 'errors'):
                    message = '; '.join(validation_error_messages(exc))
                logger.warning('Пропущено некоректний профіль: %s', message)
                continue
            validated_profiles.append(profile.model_dump(mode='json'))

        logger.info('Завантажено профілі користувачів: count=%s', len(validated_profiles))
        return validated_profiles

    def write_all(self, profiles: list[dict[str, Any]]) -> None:
        normalized_profiles: list[dict[str, Any]] = []
        for raw_profile in profiles:
            profile = UserProfileRecordSchema.model_validate(raw_profile)
            normalized_profiles.append(profile.model_dump(mode='json'))

        self.file_path.write_text(
            json.dumps(normalized_profiles, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        logger.info('Записано профілі користувачів у файл: path=%s count=%s', self.file_path, len(normalized_profiles))

    def _default_profile_name(self, now: datetime) -> str:
        return f'Профіль від {now.strftime("%d.%m.%Y %H:%M")}'

    def get_or_create(self, profile_id: str | None) -> tuple[dict[str, Any], bool]:
        normalized_profile_id = str(profile_id or '').strip()
        profiles = self.load_all()
        now = datetime.now()

        for profile in profiles:
            if profile.get('id') == normalized_profile_id:
                profile['last_seen_at'] = now.isoformat(timespec='seconds')
                self.write_all(profiles)
                logger.info('Використано наявний профіль: profile_id=%s', normalized_profile_id)
                return profile, False

        profile = UserProfileRecordSchema.model_validate(
            {
                'id': uuid4().hex,
                'name': self._default_profile_name(now),
                'created_at': now.isoformat(timespec='seconds'),
                'last_seen_at': now.isoformat(timespec='seconds'),
                'saved_build_ids': [],
                'query_history': [],
            }
        ).model_dump(mode='json')
        profiles.append(profile)
        self.write_all(profiles)
        logger.info('Створено новий профіль користувача: profile_id=%s', profile.get('id'))
        return profile, True

    def find_by_id(self, profile_id: str) -> dict[str, Any] | None:
        normalized_profile_id = str(profile_id or '').strip()
        for profile in self.load_all():
            if profile.get('id') == normalized_profile_id:
                logger.info('Знайдено профіль: profile_id=%s', normalized_profile_id)
                return profile
        logger.info('Профіль не знайдено: profile_id=%s', normalized_profile_id)
        return None

    def rename(self, profile_id: str, profile_name: str) -> dict[str, Any] | None:
        normalized_profile_id = str(profile_id or '').strip()
        cleaned_name = str(profile_name or '').strip()[:120]
        if not normalized_profile_id or not cleaned_name:
            logger.warning('Спроба перейменування профілю з невалідними даними: profile_id=%s', normalized_profile_id or 'missing')
            return None

        profiles = self.load_all()
        for profile in profiles:
            if profile.get('id') != normalized_profile_id:
                continue
            profile['name'] = cleaned_name
            profile['last_seen_at'] = datetime.now().isoformat(timespec='seconds')
            self.write_all(profiles)
            logger.info('Перейменовано профіль: profile_id=%s new_name=%s', normalized_profile_id, cleaned_name)
            return profile
        logger.warning('Не знайдено профіль для перейменування: profile_id=%s', normalized_profile_id)
        return None

    def add_query(self, profile_id: str, inputs: dict[str, Any], result: dict[str, Any], *, source: str = 'builder_form') -> dict[str, Any]:
        normalized_profile_id = str(profile_id or '').strip()
        profiles = self.load_all()
        now = datetime.now()

        summary = QueryResultSummarySchema.model_validate(
            {
                'tier': result.get('tier'),
                'total_price': result.get('total') if result.get('total') is not None else result.get('total_price'),
                'recommended_budget': result.get('recommended_budget'),
                'parts_count': len(result.get('parts', {}) or {}),
            }
        ).model_dump(mode='json')

        query_record = QueryHistoryRecordSchema.model_validate(
            {
                'id': uuid4().hex,
                'created_at': now.isoformat(timespec='seconds'),
                'source': source,
                'inputs': inputs,
                'result_summary': summary,
                'result_snapshot': BuildResultSchema.model_validate(result).model_dump(mode='json'),
            }
        ).model_dump(mode='json')

        for profile in profiles:
            if profile.get('id') != normalized_profile_id:
                continue
            history = list(profile.get('query_history', []))
            history.append(query_record)
            profile['query_history'] = history[-MAX_HISTORY_ITEMS:]
            profile['last_seen_at'] = now.isoformat(timespec='seconds')
            self.write_all(profiles)
            logger.info(
                'Додано запис в історію профілю: profile_id=%s query_id=%s purpose=%s tier=%s total=%s history_size=%s',
                normalized_profile_id,
                query_record.get('id'),
                inputs.get('purpose'),
                summary.get('tier'),
                summary.get('total_price'),
                len(profile['query_history']),
            )
            return query_record

        logger.error('Профіль не знайдено для додавання історії запитів: profile_id=%s', normalized_profile_id)
        raise ValueError('Профіль не знайдено для додавання історії запитів.')

    def find_query(self, profile_id: str, query_id: str) -> dict[str, Any] | None:
        normalized_profile_id = str(profile_id or '').strip()
        normalized_query_id = str(query_id or '').strip()
        if not normalized_profile_id or not normalized_query_id:
            return None

        profile = self.find_by_id(normalized_profile_id)
        if not profile:
            return None

        for query in profile.get('query_history', []):
            if str(query.get('id') or '').strip() == normalized_query_id:
                logger.info('Знайдено запис історії: profile_id=%s query_id=%s', normalized_profile_id, normalized_query_id)
                return query
        logger.info('Запис історії не знайдено: profile_id=%s query_id=%s', normalized_profile_id, normalized_query_id)
        return None

    def delete_query(self, profile_id: str, query_id: str) -> dict[str, Any] | None:
        normalized_profile_id = str(profile_id or '').strip()
        normalized_query_id = str(query_id or '').strip()
        if not normalized_profile_id or not normalized_query_id:
            return None

        profiles = self.load_all()
        for profile in profiles:
            if profile.get('id') != normalized_profile_id:
                continue

            history = list(profile.get('query_history', []))
            remaining_history: list[dict[str, Any]] = []
            deleted_entry: dict[str, Any] | None = None
            for entry in history:
                if str(entry.get('id') or '').strip() == normalized_query_id and deleted_entry is None:
                    deleted_entry = entry
                    continue
                remaining_history.append(entry)

            if deleted_entry is None:
                logger.warning('Не знайдено запис історії для видалення: profile_id=%s query_id=%s', normalized_profile_id, normalized_query_id)
                return None

            profile['query_history'] = remaining_history
            profile['last_seen_at'] = datetime.now().isoformat(timespec='seconds')
            self.write_all(profiles)
            logger.info(
                'Видалено запис історії профілю: profile_id=%s query_id=%s remaining=%s',
                normalized_profile_id,
                normalized_query_id,
                len(remaining_history),
            )
            return deleted_entry

        return None

    def clear_query_history(self, profile_id: str) -> list[dict[str, Any]]:
        normalized_profile_id = str(profile_id or '').strip()
        if not normalized_profile_id:
            return []

        profiles = self.load_all()
        for profile in profiles:
            if profile.get('id') != normalized_profile_id:
                continue

            removed_history = list(profile.get('query_history', []))
            profile['query_history'] = []
            profile['last_seen_at'] = datetime.now().isoformat(timespec='seconds')
            self.write_all(profiles)
            logger.info('Очищено історію профілю: profile_id=%s removed=%s', normalized_profile_id, len(removed_history))
            return removed_history

        return []

    def link_saved_build(self, profile_id: str, build_id: str, *, query_id: str | None = None) -> None:
        normalized_profile_id = str(profile_id or '').strip()
        normalized_build_id = str(build_id or '').strip()
        normalized_query_id = str(query_id or '').strip()
        if not normalized_profile_id or not normalized_build_id:
            return

        profiles = self.load_all()
        for profile in profiles:
            if profile.get('id') != normalized_profile_id:
                continue

            saved_build_ids = list(profile.get('saved_build_ids', []))
            if normalized_build_id not in saved_build_ids:
                saved_build_ids.append(normalized_build_id)
            profile['saved_build_ids'] = saved_build_ids

            if normalized_query_id:
                for query in profile.get('query_history', []):
                    if query.get('id') == normalized_query_id:
                        query['saved_build_id'] = normalized_build_id
                        break

            profile['last_seen_at'] = datetime.now().isoformat(timespec='seconds')
            self.write_all(profiles)
            logger.info(
                'Прив’язано збережену збірку до профілю: profile_id=%s build_id=%s query_id=%s',
                normalized_profile_id,
                normalized_build_id,
                normalized_query_id or 'none',
            )
            return

    def unlink_saved_build(self, profile_id: str, build_id: str) -> None:
        normalized_profile_id = str(profile_id or '').strip()
        normalized_build_id = str(build_id or '').strip()
        if not normalized_profile_id or not normalized_build_id:
            return

        profiles = self.load_all()
        for profile in profiles:
            if profile.get('id') != normalized_profile_id:
                continue

            profile['saved_build_ids'] = [
                existing_id
                for existing_id in profile.get('saved_build_ids', [])
                if existing_id != normalized_build_id
            ]
            for query in profile.get('query_history', []):
                if query.get('saved_build_id') == normalized_build_id:
                    query['saved_build_id'] = None

            profile['last_seen_at'] = datetime.now().isoformat(timespec='seconds')
            self.write_all(profiles)
            logger.info('Відв’язано збережену збірку від профілю: profile_id=%s build_id=%s', normalized_profile_id, normalized_build_id)
            return

    def prepare_for_dashboard(self, profile: dict[str, Any], *, saved_builds_by_id: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        prepared = dict(profile)
        prepared['created_at_display'] = self._format_datetime(profile.get('created_at'))
        prepared['last_seen_at_display'] = self._format_datetime(profile.get('last_seen_at'))
        prepared['saved_build_count'] = len(profile.get('saved_build_ids', []))
        prepared['query_count'] = len(profile.get('query_history', []))

        builds_by_id = saved_builds_by_id or {}
        prepared['query_history'] = [
            self.prepare_history_entry(entry, builds_by_id)
            for entry in reversed(profile.get('query_history', []))
        ]
        return prepared

    def prepare_history_entry(self, entry: dict[str, Any], builds_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
        prepared = dict(entry)
        inputs = prepared.get('inputs', {})
        summary = prepared.get('result_summary', {})
        linked_build = builds_by_id.get(str(prepared.get('saved_build_id') or '').strip())

        prepared['created_at_display'] = self._format_datetime(prepared.get('created_at'))
        prepared['purpose_title'] = PURPOSE_TITLES.get(inputs.get('purpose', ''), inputs.get('purpose', 'Запит'))
        prepared['priority_title'] = PRIORITY_TITLES.get(inputs.get('priority', ''), inputs.get('priority', '—'))
        prepared['tier_title'] = TIER_TITLES.get(summary.get('tier', ''), summary.get('tier', '—'))
        prepared['total_display'] = summary.get('total_price') or 0
        prepared['budget_label'] = (
            f"Автоматичний підбір (орієнтир {summary.get('recommended_budget') or '—'} грн)"
            if inputs.get('budget_mode') == 'auto'
            else f"{inputs.get('budget') or 0} грн"
        )

        selected_titles = []
        for key in ('games_titles', 'office_apps_titles', 'study_apps_titles', 'creator_apps_titles'):
            selected_titles.extend(inputs.get(key, []) or [])
        prepared['selected_titles'] = selected_titles[:6]

        prepared['linked_build_name'] = linked_build.get('name') if linked_build else None
        prepared['linked_build_id'] = linked_build.get('id') if linked_build else None
        prepared['has_snapshot'] = isinstance(prepared.get('result_snapshot'), dict) and bool(prepared.get('result_snapshot'))
        prepared['open_url'] = f"/profile/history/{prepared.get('id')}" if prepared.get('id') else None
        prepared['delete_url'] = f"/profile/history/{prepared.get('id')}/delete" if prepared.get('id') else None
        return prepared

    def _format_datetime(self, value: Any) -> str:
        try:
            return datetime.fromisoformat(str(value)).strftime('%d.%m.%Y %H:%M')
        except Exception:
            return str(value or 'Без дати')


user_profiles_repository = UserProfilesRepository()

from __future__ import annotations

from pathlib import Path

from repositories.saved_builds_repository import SavedBuildsRepository
from repositories.user_profiles_repository import UserProfilesRepository


def _valid_inputs() -> dict[str, object]:
    return {
        "budget_mode": "manual",
        "budget": 22000,
        "purpose": "office",
        "resolution": "1080p",
        "wifi": False,
        "games": [],
        "graphics_quality": "high",
        "target_fps": 60,
        "gpu_mode": "auto",
        "cpu_brand": "auto",
        "gpu_brand": "auto",
        "ram_size": "auto",
        "ssd_size": "auto",
        "memory_platform": "auto",
        "office_apps": [],
        "office_tabs": "auto",
        "office_monitors": "auto",
        "study_apps": [],
        "study_tabs": "auto",
        "study_monitors": "auto",
        "creator_apps": [],
        "creator_complexity": "auto",
        "creator_monitors": "auto",
        "priority": "balanced",
    }


def _valid_result() -> dict[str, object]:
    return {
        "tier": "budget",
        "total_price": 18000,
        "recommended_budget": 22000,
        "parts": {},
        "alternatives": [],
        "notes": [],
    }


def _valid_saved_build() -> dict[str, object]:
    return {
        "id": "build-1",
        "profile_id": "profile-1",
        "query_id": "query-1",
        "name": "Тестова збірка",
        "saved_at": "2026-04-05T12:00:00",
        "inputs": _valid_inputs(),
        "result": _valid_result(),
    }


def test_saved_builds_repository_recovers_from_broken_json(tmp_path: Path) -> None:
    file_path = tmp_path / "saved_builds.json"
    file_path.write_text("{", encoding="utf-8")

    repository = SavedBuildsRepository(file_path=file_path)
    assert repository.load_all() == []
    assert file_path.read_text(encoding="utf-8").strip() == "[]"
    backups = list(tmp_path.glob("saved_builds.broken-*.json.bak"))
    assert backups


def test_saved_builds_repository_can_save_rename_and_delete(tmp_path: Path) -> None:
    repository = SavedBuildsRepository(file_path=tmp_path / "saved_builds.json")

    saved = repository.save_record(_valid_saved_build())
    assert saved["id"] == "build-1"
    assert len(repository.load_all()) == 1

    renamed = repository.rename_build("build-1", "Оновлена збірка", profile_id="profile-1")
    assert renamed is not None
    assert renamed["name"] == "Оновлена збірка"

    deleted = repository.delete_build("build-1", profile_id="profile-1")
    assert deleted is not None
    assert repository.load_all() == []


def test_user_profiles_repository_recovers_from_broken_json(tmp_path: Path) -> None:
    file_path = tmp_path / "user_profiles.json"
    file_path.write_text("not-json", encoding="utf-8")

    repository = UserProfilesRepository(file_path=file_path)
    assert repository.load_all() == []
    assert file_path.read_text(encoding="utf-8").strip() == "[]"
    backups = list(tmp_path.glob("user_profiles.broken-*.json.bak"))
    assert backups


def test_user_profiles_repository_adds_query_and_prepares_dashboard(tmp_path: Path) -> None:
    repository = UserProfilesRepository(file_path=tmp_path / "user_profiles.json")
    profile, created = repository.get_or_create(None)
    assert created is True

    query = repository.add_query(profile["id"], _valid_inputs(), _valid_result())
    assert query["id"]

    loaded_profile = repository.find_by_id(profile["id"])
    assert loaded_profile is not None
    dashboard = repository.prepare_for_dashboard(loaded_profile, saved_builds_by_id={})
    assert dashboard["query_count"] == 1
    assert dashboard["query_history"]
    assert dashboard["query_history"][0]["has_snapshot"] is True

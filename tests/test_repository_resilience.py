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


def test_saved_builds_repository_isolates_builds_by_profile(tmp_path: Path) -> None:
    repository = SavedBuildsRepository(file_path=tmp_path / "saved_builds.json")

    own_build = _valid_saved_build()
    own_build["id"] = "own-build"
    own_build["profile_id"] = "profile-1"

    other_build = _valid_saved_build()
    other_build["id"] = "other-build"
    other_build["profile_id"] = "profile-2"

    legacy_build = _valid_saved_build()
    legacy_build["id"] = "legacy-build"
    legacy_build["profile_id"] = None

    repository.write_all([own_build, other_build, legacy_build])

    visible_builds = repository.load_by_profile("profile-1")
    assert [build["id"] for build in visible_builds] == ["own-build"]

    assert repository.find_by_id("own-build", profile_id="profile-1") is not None
    assert repository.find_by_id("other-build", profile_id="profile-1") is None
    assert repository.find_by_id("legacy-build", profile_id="profile-1") is None

    assert repository.rename_build("other-build", "Заборонена зміна", profile_id="profile-1") is None
    assert repository.delete_build("legacy-build", profile_id="profile-1") is None
    assert repository.clear_query_reference("legacy-build", profile_id="profile-1") is False

    assert len(repository.load_all()) == 3


def test_saved_builds_repository_clears_only_exact_profile_references(tmp_path: Path) -> None:
    repository = SavedBuildsRepository(file_path=tmp_path / "saved_builds.json")

    own_build = _valid_saved_build()
    own_build["id"] = "own-build"
    own_build["profile_id"] = "profile-1"
    own_build["query_id"] = "query-1"

    other_build = _valid_saved_build()
    other_build["id"] = "other-build"
    other_build["profile_id"] = "profile-2"
    other_build["query_id"] = "query-2"

    legacy_build = _valid_saved_build()
    legacy_build["id"] = "legacy-build"
    legacy_build["profile_id"] = None
    legacy_build["query_id"] = "query-3"

    repository.write_all([own_build, other_build, legacy_build])

    assert repository.clear_query_references_for_profile("profile-1") == 1

    builds = {build["id"]: build for build in repository.load_all()}
    assert builds["own-build"]["query_id"] is None
    assert builds["other-build"]["query_id"] == "query-2"
    assert builds["legacy-build"]["query_id"] == "query-3"


def test_json_store_lock_preserves_concurrent_saved_build_writes(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    repository = SavedBuildsRepository(file_path=tmp_path / "saved_builds.json")
    repository.write_all([])

    def save_build(index: int) -> None:
        build = _valid_saved_build()
        build["id"] = f"build-{index}"
        build["profile_id"] = f"profile-{index}"
        repository.save_record(build)

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(save_build, range(24)))

    saved_ids = {build["id"] for build in repository.load_all()}
    assert saved_ids == {f"build-{index}" for index in range(24)}


def test_json_store_lock_preserves_concurrent_profile_history_writes(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    repository = UserProfilesRepository(file_path=tmp_path / "user_profiles.json")
    profile, _ = repository.get_or_create(None)

    def add_query(index: int) -> None:
        inputs = _valid_inputs()
        inputs["budget"] = 22000 + index
        repository.add_query(profile["id"], inputs, _valid_result())

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(add_query, range(24)))

    loaded_profile = repository.find_by_id(profile["id"])
    assert loaded_profile is not None
    assert len(loaded_profile["query_history"]) == 24

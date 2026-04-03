from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from fastapi import HTTPException
from pydantic import ValidationError

from config import BUDGET_LIMITS, FPS_LIMITS, PRIORITY_TITLES, PURPOSE_TITLES
from parts_db import CREATOR_APPS_DB, GAMES_DB, OFFICE_APPS_DB, STUDY_APPS_DB
from schemas import (
    BuildInputsSchema,
    BuildInputsViewSchema,
    BuildPayloadSchema,
    BuildResultSchema,
)
from utils.assets import attach_part_images
from utils.validation import serialize_for_template, validation_error_messages


logger = logging.getLogger("pcbuilder.services.build")


# =========================
# Каталоги та контекст форми
# =========================
def build_option_list(db: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [{"key": key, "title": value["title"]} for key, value in db.items()]


def normalize_purpose(purpose: str) -> str:
    return purpose if purpose in PURPOSE_TITLES else "gaming"


def budget_limits_for_purpose(purpose: str) -> dict[str, int]:
    normalized_purpose = normalize_purpose(purpose)
    return BUDGET_LIMITS.get(normalized_purpose, {"min": 15000, "max": 150000})


def builder_template_context(purpose: str) -> dict[str, Any]:
    normalized_purpose = normalize_purpose(purpose)
    budget_limits = budget_limits_for_purpose(normalized_purpose)
    return {
        "selected_purpose": normalized_purpose,
        "purpose_title": PURPOSE_TITLES[normalized_purpose],
        "games_list": build_option_list(GAMES_DB),
        "office_apps_list": build_option_list(OFFICE_APPS_DB),
        "study_apps_list": build_option_list(STUDY_APPS_DB),
        "creator_apps_list": build_option_list(CREATOR_APPS_DB),
        "budget_min": budget_limits["min"],
        "budget_max": budget_limits["max"],
        "fps_min": FPS_LIMITS["min"],
        "fps_max": FPS_LIMITS["max"],
        "selected_priority": "balanced",
        "priority_titles": PRIORITY_TITLES,
    }


# =========================
# Вхідні дані форми
# =========================
def extract_user_inputs(form: Any) -> dict[str, Any]:
    raw_inputs = {
        "budget_mode": form.get("budget_mode", "manual"),
        "budget": form.get("budget", 0),
        "purpose": form.get("purpose", "gaming"),
        "resolution": form.get("resolution", "1080p"),
        "wifi": form.get("wifi", "no"),
        "games": form.getlist("games"),
        "graphics_quality": form.get("graphics_quality", "high"),
        "target_fps": form.get("target_fps", 60),
        "gpu_mode": form.get("gpu_mode", "auto"),
        "cpu_brand": form.get("cpu_brand", "auto"),
        "gpu_brand": form.get("gpu_brand", "auto"),
        "ram_size": form.get("ram_size", "auto"),
        "ssd_size": form.get("ssd_size", "auto"),
        "memory_platform": form.get("memory_platform", "auto"),
        "office_apps": form.getlist("office_apps"),
        "office_tabs": form.get("office_tabs", "auto"),
        "office_monitors": form.get("office_monitors", "auto"),
        "study_apps": form.getlist("study_apps"),
        "study_tabs": form.get("study_tabs", "auto"),
        "study_monitors": form.get("study_monitors", "auto"),
        "creator_apps": form.getlist("creator_apps"),
        "creator_complexity": form.get("creator_complexity", "auto"),
        "creator_monitors": form.get("creator_monitors", "auto"),
        "priority": form.get("priority", "balanced"),
    }

    purpose = str(raw_inputs.get("purpose", "gaming") or "gaming")
    budget_limits = budget_limits_for_purpose(purpose)

    validated_inputs = BuildInputsSchema.model_validate(
        raw_inputs,
        context={"budget_limits": budget_limits, "fps_limits": FPS_LIMITS},
    )

    inputs = validated_inputs.model_dump(mode="json")
    inputs["games"] = [game for game in inputs.get("games", []) if game in GAMES_DB]
    inputs["office_apps"] = [
        app for app in inputs.get("office_apps", []) if app in OFFICE_APPS_DB
    ]
    inputs["study_apps"] = [
        app for app in inputs.get("study_apps", []) if app in STUDY_APPS_DB
    ]
    inputs["creator_apps"] = [
        app for app in inputs.get("creator_apps", []) if app in CREATOR_APPS_DB
    ]

    inputs["games_titles"] = [GAMES_DB[game]["title"] for game in inputs["games"]]
    inputs["office_apps_titles"] = [
        OFFICE_APPS_DB[app]["title"] for app in inputs["office_apps"]
    ]
    inputs["study_apps_titles"] = [
        STUDY_APPS_DB[app]["title"] for app in inputs["study_apps"]
    ]
    inputs["creator_apps_titles"] = [
        CREATOR_APPS_DB[app]["title"] for app in inputs["creator_apps"]
    ]

    validated_view = BuildInputsViewSchema.model_validate(
        inputs,
        context={"budget_limits": budget_limits, "fps_limits": FPS_LIMITS},
    )
    return validated_view.model_dump(mode="json")


def build_pc_payload(inputs: dict[str, Any]) -> dict[str, Any]:
    return BuildPayloadSchema.from_inputs(inputs).model_dump(mode="json")


# =========================
# Валідація та результат
# =========================
def validate_build_result(result: dict[str, Any]) -> dict[str, Any]:
    normalized_result = dict(result or {})

    if normalized_result.get("total_price") is None and normalized_result.get("total") is not None:
        normalized_result["total_price"] = normalized_result.get("total")

    parts = normalized_result.get("parts")
    if normalized_result.get("total_price") is None and isinstance(parts, dict) and parts:
        computed_total = 0
        has_prices = False
        for part in parts.values():
            price = None
            if isinstance(part, dict):
                price = part.get("price")
            else:
                price = getattr(part, "price", None)
            if isinstance(price, (int, float)):
                computed_total += price
                has_prices = True
        if has_prices:
            normalized_result["total_price"] = computed_total

    return BuildResultSchema.model_validate(normalized_result).model_dump(mode="json")


def default_build_name(inputs: dict[str, Any]) -> str:
    purpose_title = PURPOSE_TITLES.get(inputs.get("purpose", "gaming"), "Збірка ПК")
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f"{purpose_title} — {timestamp}"


def normalize_build_name(build_name: str | None, inputs: dict[str, Any]) -> str:
    cleaned_name = (build_name or "").strip()
    return cleaned_name[:120] if cleaned_name else default_build_name(inputs)


def result_page_context(
    request: Any,
    inputs: dict[str, Any],
    result: dict[str, Any],
    *,
    saved_build_name: str | None = None,
    profile_query_id: str | None = None,
    profile_name: str | None = None,
    is_saved_build_view: bool = False,
) -> dict[str, Any]:
    return {
        "request": request,
        "inputs": inputs,
        "result": result,
        "inputs_json": serialize_for_template(inputs),
        "result_json": serialize_for_template(result),
        "saved_build_name": saved_build_name,
        "profile_query_id": profile_query_id,
        "profile_name": profile_name,
        "is_saved_build_view": is_saved_build_view,
    }


def _prepare_public_alternatives(
    raw_alternatives: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    public_alternatives: list[dict[str, Any]] = []
    primary_result: dict[str, Any] | None = None

    for alternative in raw_alternatives:
        if not isinstance(alternative, dict):
            continue

        raw_result = alternative.get("_result")
        if alternative.get("is_primary") and isinstance(raw_result, dict):
            primary_result = raw_result

        public_card = dict(alternative)
        public_card.pop("_result", None)

        if isinstance(raw_result, dict):
            result_payload = dict(raw_result)
            result_payload.pop("alternatives", None)
            result_payload = validate_build_result(result_payload)
            result_payload = attach_part_images(result_payload)
            public_card["result_payload"] = result_payload

        public_alternatives.append(public_card)

    return public_alternatives, primary_result


def _merge_primary_result_with_alternatives(
    result: dict[str, Any],
    public_alternatives: list[dict[str, Any]],
    primary_result: dict[str, Any] | None,
) -> dict[str, Any]:
    if primary_result and primary_result.get("parts"):
        normalized_primary = dict(primary_result)
        normalized_primary["alternatives"] = public_alternatives
        return validate_build_result(normalized_primary)

    normalized_result = dict(result)
    normalized_result["alternatives"] = public_alternatives
    return normalized_result


def _is_successful_build_result(result: dict[str, Any]) -> bool:
    parts = result.get("parts")
    total_price = result.get("total_price")

    has_parts = False
    if isinstance(parts, dict):
        has_parts = bool(parts)
    elif isinstance(parts, list):
        has_parts = bool(parts)

    if not has_parts:
        return False

    if total_price in (None, "", 0):
        return False

    try:
        return float(total_price) > 0
    except (TypeError, ValueError):
        return False


def _normalize_failed_build_result(
    result: dict[str, Any],
    *,
    purpose: str,
) -> dict[str, Any]:
    normalized_result = dict(result)
    notes = list(normalized_result.get("notes") or [])

    if not notes:
        purpose_title = PURPOSE_TITLES.get(purpose, "конфігурацію")
        notes.append(
            f"Не вдалося зібрати {purpose_title.lower()} за заданими параметрами та бюджетом."
        )

    normalized_result["parts"] = {}
    normalized_result["total_price"] = None
    normalized_result["alternatives"] = []
    normalized_result["notes"] = notes
    normalized_result["tier"] = None

    return attach_part_images(normalized_result)


# =========================
# Побудова конфігурації
# =========================
def _run_primary_build(payload: dict[str, Any], *, budget_mode: str) -> dict[str, Any]:
    # Локальний імпорт прибирає циклічну залежність під час pytest/app startup.
    from builder import build_pc, build_pc_auto_budget

    normalized_payload = dict(payload)

    if budget_mode == "auto":
        normalized_payload.pop("budget", None)
        logger.info(
            "Запуск автоматичної побудови конфігурації: purpose=%s priority=%s",
            normalized_payload.get("purpose"),
            normalized_payload.get("priority"),
        )
        return build_pc_auto_budget(**normalized_payload)

    logger.info(
        "Запуск ручної побудови конфігурації: purpose=%s budget=%s priority=%s",
        normalized_payload.get("purpose"),
        normalized_payload.get("budget"),
        normalized_payload.get("priority"),
    )
    return build_pc(**normalized_payload)


def _run_alternative_builds(
    result: dict[str, Any],
    payload: dict[str, Any],
    *,
    budget_mode: str,
) -> list[dict[str, Any]]:
    # Локальний імпорт прибирає циклічну залежність під час pytest/app startup.
    from builder import build_pc_alternatives

    if not _is_successful_build_result(result):
        return []

    logger.info(
        "Побудова альтернативних конфігурацій: purpose=%s budget_mode=%s base_tier=%s",
        payload.get("purpose"),
        budget_mode,
        result.get("tier"),
    )
    return build_pc_alternatives(result, budget_mode=budget_mode, **payload)


def build_configuration_from_form(form: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        inputs = extract_user_inputs(form)
    except ValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail="; ".join(validation_error_messages(exc)),
        ) from exc

    logger.info(
        "Підготовлено вхідні параметри збірки: purpose=%s budget_mode=%s budget=%s "
        "priority=%s games=%s office_apps=%s study_apps=%s creator_apps=%s",
        inputs.get("purpose"),
        inputs.get("budget_mode"),
        inputs.get("budget"),
        inputs.get("priority"),
        len(inputs.get("games", [])),
        len(inputs.get("office_apps", [])),
        len(inputs.get("study_apps", [])),
        len(inputs.get("creator_apps", [])),
    )

    payload = build_pc_payload(inputs)
    budget_mode = inputs.get("budget_mode", "manual")

    logger.info(
        "Сформовано payload для builder: purpose=%s budget=%s budget_mode=%s priority=%s",
        payload.get("purpose"),
        payload.get("budget"),
        budget_mode,
        payload.get("priority"),
    )

    try:
        primary_result = _run_primary_build(payload, budget_mode=budget_mode)
        validated_result = validate_build_result(primary_result)

        logger.info(
            "Результат збірки провалідовано: tier=%s total=%s parts=%s alternatives=%s",
            validated_result.get("tier"),
            validated_result.get("total_price"),
            len(validated_result.get("parts") or {}),
            len(validated_result.get("alternatives") or []),
        )

        if not _is_successful_build_result(validated_result):
            logger.warning(
                "Побудова конфігурації завершилася без валідного складу: purpose=%s "
                "budget_mode=%s budget=%s notes=%s",
                inputs.get("purpose"),
                budget_mode,
                inputs.get("budget"),
                validated_result.get("notes") or [],
            )
            return inputs, _normalize_failed_build_result(
                validated_result,
                purpose=inputs.get("purpose", "gaming"),
            )

        raw_alternatives = _run_alternative_builds(
            validated_result,
            payload,
            budget_mode=budget_mode,
        )
        logger.info("Альтернативні конфігурації побудовано: count=%s", len(raw_alternatives))

        public_alternatives, alternative_primary_result = _prepare_public_alternatives(
            raw_alternatives
        )
        logger.info(
            "Підготовлено публічні альтернативи: count=%s",
            len(public_alternatives),
        )

        final_result = _merge_primary_result_with_alternatives(
            validated_result,
            public_alternatives,
            alternative_primary_result,
        )
        final_result = attach_part_images(final_result)

        logger.info(
            "Побудову конфігурації завершено: purpose=%s tier=%s total=%s alternatives=%s",
            inputs.get("purpose"),
            final_result.get("tier"),
            final_result.get("total_price"),
            len(final_result.get("alternatives") or []),
        )

        return inputs, final_result

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Неочікувана помилка під час побудови конфігурації: purpose=%s "
            "budget_mode=%s priority=%s",
            inputs.get("purpose"),
            budget_mode,
            inputs.get("priority"),
        )
        raise


__all__ = [
    "build_configuration_from_form",
    "build_option_list",
    "build_pc_payload",
    "budget_limits_for_purpose",
    "builder_template_context",
    "default_build_name",
    "extract_user_inputs",
    "normalize_build_name",
    "normalize_purpose",
    "result_page_context",
    "validate_build_result",
]

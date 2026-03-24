from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
import json
import logging
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from builder import build_pc, build_pc_alternatives, build_pc_auto_budget
from parts_db import CREATOR_APPS_DB, GAMES_DB, OFFICE_APPS_DB, STUDY_APPS_DB
from schemas import (
    BuildInputsSchema,
    BuildInputsViewSchema,
    BuildPayloadSchema,
    BuildResultSchema,
    PurposeDetectionFormSchema,
    SavedBuildRecordSchema,
)

logger = logging.getLogger("pcbuilder.app")

try:
    from ml.predict import (
        ACCEPTANCE_THRESHOLD as AI_ACCEPTANCE_THRESHOLD,
        ModelUnavailableError,
        get_model_status,
        predict_purpose,
        warmup_model,
    )
    AI_IMPORT_ERROR: str | None = None
except Exception as exc:
    AI_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    logger.exception("Не вдалося імпортувати AI-модуль.")

    AI_ACCEPTANCE_THRESHOLD = 0.70

    class ModelUnavailableError(RuntimeError):
        """Raised when the local AI model is unavailable."""

    def get_model_status(*, probe: bool = False) -> dict[str, Any]:
        return {
            "available": False,
            "loaded": False,
            "model_exists": False,
            "model_path": str(Path(__file__).resolve().parent / "ml" / "model.joblib"),
            "reason": AI_IMPORT_ERROR or "Не вдалося імпортувати модуль ml.predict.",
        }

    def warmup_model() -> None:
        return None

    def predict_purpose(text: str) -> dict[str, Any]:
        raise ModelUnavailableError(
            "AI-модуль недоступний: не вдалося імпортувати модуль або його залежності."
        )


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
SAVED_BUILDS_FILE = BASE_DIR / "saved_builds.json"

PURPOSE_TITLES = {
    "gaming": "Ігровий ПК",
    "office": "Офісний ПК",
    "study": "ПК для навчання",
    "creator": "ПК для монтажу / 3D",
}

TIER_TITLES = {
    "budget": "Бюджетний",
    "mid": "Середній",
    "upper": "Високий",
}

PRIORITY_TITLES = {
    "budget": "Бюджетний",
    "balanced": "Ціна / якість",
    "best": "Максимальна продуктивність",
}

STATUS_MESSAGES = {
    "saved": "Збірку успішно збережено.",
    "renamed": "Назву збірки оновлено.",
    "deleted": "Збірку видалено.",
}

BUDGET_LIMITS = {
    "gaming": {"min": 12500, "max": 225000},
    "office": {"min": 15000, "max": 110000},
    "study": {"min": 15000, "max": 120000},
    "creator": {"min": 42500, "max": 235000},
}

FPS_LIMITS = {"min": 30, "max": 500}


def _ai_status_message(ai_status: dict[str, Any]) -> str:
    if ai_status.get("available"):
        return "Локальна ML-модель успішно завантажена."

    reason = ai_status.get("reason")
    if reason:
        return f"Локальна ML-модель недоступна: {reason}"

    return "Локальна ML-модель тимчасово недоступна."


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        warmup_model()
        logger.info("Локальна ML-модель успішно завантажена.")
    except ModelUnavailableError as exc:
        logger.warning("AI-модель недоступна під час старту: %s", exc)
    except Exception:
        logger.exception("Неочікувана помилка під час стартової перевірки AI-модуля.")
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _slugify_part_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "part"


def _part_image_path(part_name: str) -> str | None:
    filename = f"{_slugify_part_name(part_name)}.webp"
    image_file = STATIC_DIR / "images" / "parts" / filename
    if image_file.exists():
        return f"/static/images/parts/{filename}"
    return None


def _attach_part_images(result: dict[str, Any]) -> dict[str, Any]:
    parts = result.get("parts", {})
    if isinstance(parts, dict):
        for part_data in parts.values():
            if not isinstance(part_data, dict):
                continue
            name = part_data.get("name")
            if name:
                part_data["image"] = _part_image_path(name)
                part_data["image_filename"] = f"{_slugify_part_name(name)}.webp"

    alternatives = result.get("alternatives", [])
    if isinstance(alternatives, list):
        for alternative in alternatives:
            if not isinstance(alternative, dict):
                continue
            alternative_parts = alternative.get("parts", [])

            if isinstance(alternative_parts, dict):
                iterable_parts = alternative_parts.values()
            elif isinstance(alternative_parts, list):
                iterable_parts = alternative_parts
            else:
                continue

            for part_data in iterable_parts:
                if not isinstance(part_data, dict):
                    continue
                name = part_data.get("name")
                if name:
                    part_data["image"] = _part_image_path(name)
                    part_data["image_filename"] = f"{_slugify_part_name(name)}.webp"
    return result


def _build_option_list(db: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [{"key": key, "title": value["title"]} for key, value in db.items()]


def _normalize_purpose(purpose: str) -> str:
    return purpose if purpose in PURPOSE_TITLES else "gaming"


def _budget_limits_for_purpose(purpose: str) -> dict[str, int]:
    normalized_purpose = _normalize_purpose(purpose)
    return BUDGET_LIMITS.get(normalized_purpose, {"min": 15000, "max": 150000})


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _builder_template_context(purpose: str) -> dict[str, Any]:
    normalized_purpose = _normalize_purpose(purpose)
    budget_limits = _budget_limits_for_purpose(normalized_purpose)
    return {
        "selected_purpose": normalized_purpose,
        "purpose_title": PURPOSE_TITLES[normalized_purpose],
        "games_list": _build_option_list(GAMES_DB),
        "office_apps_list": _build_option_list(OFFICE_APPS_DB),
        "study_apps_list": _build_option_list(STUDY_APPS_DB),
        "creator_apps_list": _build_option_list(CREATOR_APPS_DB),
        "budget_min": budget_limits["min"],
        "budget_max": budget_limits["max"],
        "fps_min": FPS_LIMITS["min"],
        "fps_max": FPS_LIMITS["max"],
        "selected_priority": "balanced",
        "priority_titles": PRIORITY_TITLES,
    }


def _choose_purpose_context(request: Request) -> dict[str, Any]:
    ai_status = get_model_status(probe=True)

    return {
        "request": request,
        "purpose_titles": PURPOSE_TITLES,
        "ai_threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
        "ai_available": bool(ai_status.get("available")),
        "ai_status_message": _ai_status_message(ai_status),
        "ai_status_reason": ai_status.get("reason"),
    }


def _validation_error_messages(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []))
        message = str(error.get("msg", "Некоректне значення."))
        messages.append(f"{location}: {message}" if location else message)
    return messages


def _load_saved_builds() -> list[dict[str, Any]]:
    if not SAVED_BUILDS_FILE.exists():
        return []

    try:
        raw_saved_builds = json.loads(SAVED_BUILDS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(raw_saved_builds, list):
        logger.warning("saved_builds.json має неочікувану структуру. Очікувався список.")
        return []

    validated_builds: list[dict[str, Any]] = []
    for raw_build in raw_saved_builds:
        if not isinstance(raw_build, dict):
            continue
        try:
            build = SavedBuildRecordSchema.model_validate(raw_build)
        except ValidationError as exc:
            logger.warning("Пропущено некоректну збережену збірку: %s", "; ".join(_validation_error_messages(exc)))
            continue
        validated_builds.append(build.model_dump(mode="json"))

    return validated_builds


def _write_saved_builds(saved_builds: list[dict[str, Any]]) -> None:
    normalized_builds: list[dict[str, Any]] = []
    for raw_build in saved_builds:
        build = SavedBuildRecordSchema.model_validate(raw_build)
        normalized_builds.append(build.model_dump(mode="json"))

    SAVED_BUILDS_FILE.write_text(
        json.dumps(normalized_builds, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_json_object(value: Any, *, field_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Поле {field_name} містить невалідний JSON.") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail=f"Поле {field_name} має містити JSON-об’єкт.")

    return payload


def _extract_user_inputs(form: Any) -> dict[str, Any]:
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
    budget_limits = _budget_limits_for_purpose(purpose)

    validated_inputs = BuildInputsSchema.model_validate(
        raw_inputs,
        context={"budget_limits": budget_limits, "fps_limits": FPS_LIMITS},
    )
    inputs = validated_inputs.model_dump(mode="json")

    inputs["games"] = [game for game in inputs.get("games", []) if game in GAMES_DB]
    inputs["office_apps"] = [app for app in inputs.get("office_apps", []) if app in OFFICE_APPS_DB]
    inputs["study_apps"] = [app for app in inputs.get("study_apps", []) if app in STUDY_APPS_DB]
    inputs["creator_apps"] = [app for app in inputs.get("creator_apps", []) if app in CREATOR_APPS_DB]

    inputs["games_titles"] = [GAMES_DB[game]["title"] for game in inputs["games"]]
    inputs["office_apps_titles"] = [OFFICE_APPS_DB[app]["title"] for app in inputs["office_apps"]]
    inputs["study_apps_titles"] = [STUDY_APPS_DB[app]["title"] for app in inputs["study_apps"]]
    inputs["creator_apps_titles"] = [CREATOR_APPS_DB[app]["title"] for app in inputs["creator_apps"]]

    validated_view = BuildInputsViewSchema.model_validate(
        inputs,
        context={"budget_limits": budget_limits, "fps_limits": FPS_LIMITS},
    )
    return validated_view.model_dump(mode="json")


def _build_pc_payload(inputs: dict[str, Any]) -> dict[str, Any]:
    return BuildPayloadSchema.from_inputs(inputs).model_dump(mode="json")


def _validate_build_result(result: dict[str, Any]) -> dict[str, Any]:
    return BuildResultSchema.model_validate(result).model_dump(mode="json")


def _default_build_name(inputs: dict[str, Any]) -> str:
    purpose_title = PURPOSE_TITLES.get(inputs.get("purpose", "gaming"), "Збірка ПК")
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f"{purpose_title} — {timestamp}"


def _normalize_build_name(build_name: str | None, inputs: dict[str, Any]) -> str:
    cleaned_name = (build_name or "").strip()
    return cleaned_name[:120] if cleaned_name else _default_build_name(inputs)


def _serialize_for_template(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def _prepare_saved_build_for_list(build: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(build)
    inputs = prepared.get("inputs", {})
    result = prepared.get("result", {})
    prepared["purpose_title"] = PURPOSE_TITLES.get(inputs.get("purpose", ""), inputs.get("purpose", "Збірка"))
    prepared["tier_title"] = TIER_TITLES.get(result.get("tier", ""), result.get("tier", "—"))

    saved_at = prepared.get("saved_at")
    try:
        prepared["saved_at_display"] = datetime.fromisoformat(saved_at).strftime("%d.%m.%Y %H:%M") if saved_at else "Без дати"
    except ValueError:
        prepared["saved_at_display"] = saved_at or "Без дати"

    return prepared


def _find_saved_build(build_id: str) -> dict[str, Any] | None:
    for build in _load_saved_builds():
        if build.get("id") == build_id:
            return build
    return None


def _result_page_context(request: Request, inputs: dict[str, Any], result: dict[str, Any], *, saved_build_name: str | None = None) -> dict[str, Any]:
    return {
        "request": request,
        "inputs": inputs,
        "result": result,
        "inputs_json": _serialize_for_template(inputs),
        "result_json": _serialize_for_template(result),
        "saved_build_name": saved_build_name,
    }


def _confidence_to_percent(value: float | None) -> int | None:
    if value is None:
        return None
    return int(round(value * 100))


def _ai_refinement_tips(purpose: str | None) -> list[str]:
    if purpose == "gaming":
        return [
            "Вкажи конкретні ігри, наприклад Dota 2, CS2, GTA 5 або Fortnite.",
            "Додай бажаний FPS або роздільну здатність, якщо це важливо.",
        ]
    if purpose == "office":
        return [
            "Перелічи офісні програми: Word, Excel, M.E.Doc, BAS, CRM, браузер.",
            "Уточни, чи потрібні бухгалтерські задачі, багато вкладок або два монітори.",
        ]
    if purpose == "study":
        return [
            "Напиши, чи потрібні Zoom, Google Meet, VS Code, Python або інші навчальні програми.",
            "Уточни, чи це навчання, програмування чи дистанційні заняття.",
        ]
    if purpose == "creator":
        return [
            "Вкажи програми: Blender, Premiere Pro, Photoshop, AutoCAD, Maya тощо.",
            "Уточни, чи потрібен монтаж відео, 3D-моделювання, дизайн або рендер.",
        ]
    return [
        "Опиши, для чого потрібен ПК: ігри, офіс, навчання чи монтаж / 3D.",
        "Додай конкретні ігри або програми, з якими будеш працювати.",
    ]


@app.get("/debug-paths", response_class=PlainTextResponse)
def debug_paths() -> str:
    return (
        f"APP FILE: {Path(__file__).resolve()}\n"
        f"BASE_DIR: {BASE_DIR}\n"
        f"STATIC_DIR: {STATIC_DIR}\n"
        f"STYLE_CSS: {STATIC_DIR / 'style.css'}\n"
        f"TEMPLATES_DIR: {TEMPLATES_DIR}\n"
        f"CHOOSE_TEMPLATE: {TEMPLATES_DIR / 'choose-purpose.html'}\n"
    )


@app.get("/health/ai", response_class=JSONResponse)
def ai_health() -> JSONResponse:
    status = get_model_status(probe=True)
    return JSONResponse(status, status_code=200 if status.get("available") else 503)


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/choose-purpose", response_class=HTMLResponse)
def choose_purpose(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("choose-purpose.html", _choose_purpose_context(request))


@app.post("/detect-purpose", response_class=JSONResponse)
async def detect_purpose(request: Request) -> JSONResponse:
    form = await request.form()
    ai_status = get_model_status(probe=True)

    try:
        detect_form = PurposeDetectionFormSchema.model_validate({"description": form.get("description", "")})
    except ValidationError:
        return JSONResponse(
            {
                "ok": False,
                "accepted": False,
                "ai_available": bool(ai_status.get("available")),
                "message": "Опиши потреби трохи детальніше, щоб ШІ міг коректно визначити тип ПК.",
                "tips": [
                    "Наприклад: ПК для CS2 і Dota 2 у Full HD.",
                    "Або: комп'ютер для Excel, M.E.Doc, браузера і документів.",
                ],
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            status_code=200,
        )

    description = detect_form.description

    if not ai_status.get("available"):
        return JSONResponse(
            {
                "ok": False,
                "accepted": False,
                "ai_available": False,
                "message": "AI-модуль тимчасово недоступний. Автоматичне визначення типу ПК зараз вимкнене.",
                "details": _ai_status_message(ai_status),
                "tips": [
                    "Обери тип ПК вручну — це працює без AI-модуля.",
                    "Перевір, чи існує файл ml/model.joblib.",
                    "Перевір, чи встановлені scikit-learn і joblib.",
                ],
                "manual_url": "/choose-purpose#manual-purpose-grid",
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            status_code=503,
        )

    try:
        prediction = predict_purpose(description)
    except ModelUnavailableError as exc:
        logger.warning("AI-модель стала недоступною під час запиту: %s", exc)
        return JSONResponse(
            {
                "ok": False,
                "accepted": False,
                "ai_available": False,
                "message": "AI-модуль тимчасово недоступний. Автоматичне визначення типу ПК зараз вимкнене.",
                "details": str(exc),
                "tips": [
                    "Обери тип ПК вручну — це працює без AI-модуля.",
                    "Перевір, чи існує файл ml/model.joblib.",
                    "Перевір, чи встановлені scikit-learn і joblib.",
                ],
                "manual_url": "/choose-purpose#manual-purpose-grid",
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            status_code=503,
        )
    except Exception:
        logger.exception("Помилка під час AI-визначення типу ПК.")
        return JSONResponse(
            {
                "ok": False,
                "accepted": False,
                "ai_available": True,
                "message": "Не вдалося обробити опис через помилку AI-модуля. Спробуй ще раз або обери тип ПК вручну.",
                "tips": _ai_refinement_tips(None),
                "manual_url": "/choose-purpose#manual-purpose-grid",
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            status_code=500,
        )

    raw_purpose = prediction.get("raw_purpose")
    confidence = prediction.get("confidence")
    accepted = bool(prediction.get("accepted"))
    confidence_percent = _confidence_to_percent(confidence)

    purpose_title = (
        PURPOSE_TITLES.get(raw_purpose, "Невизначений тип")
        if raw_purpose
        else "Невизначений тип"
    )

    alternatives = prediction.get("alternatives") or []
    prepared_alternatives = []

    for item in alternatives:
        if not isinstance(item, dict):
            continue

        alt_purpose = item.get("purpose")
        alt_conf = item.get("confidence")

        if alt_purpose is None or alt_conf is None:
            continue

        prepared_alternatives.append(
            {
                "purpose": PURPOSE_TITLES.get(str(alt_purpose), str(alt_purpose)),
                "confidence": _confidence_to_percent(float(alt_conf)),
            }
        )

    matched_keywords = prediction.get("matched_keywords") or {}

    if accepted and raw_purpose:
        return JSONResponse(
            {
                "ok": True,
                "accepted": True,
                "ai_available": True,
                "purpose": raw_purpose,
                "purpose_title": purpose_title,
                "confidence": confidence,
                "confidence_percent": confidence_percent,
                "redirect_url": f"/builder/{raw_purpose}",
                "message": f"ШІ впевнено визначив сценарій: {purpose_title}. Переходимо до конфігуратора.",
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
                "alternatives": prepared_alternatives,
                "matched_keywords": matched_keywords,
            }
        )

    message = "ШІ поки не впевнений у виборі сценарію. Напиши, будь ласка, конкретніше, для чого потрібен ПК."
    if raw_purpose and confidence_percent is not None:
        message = (
            f"ШІ припускає, що це {purpose_title.lower()}, але впевненість лише "
            f"{confidence_percent}%. Опиши потреби конкретніше, і тоді система зможе "
            "точніше визначити тип ПК."
        )

    return JSONResponse(
        {
            "ok": True,
            "accepted": False,
            "ai_available": True,
            "purpose": raw_purpose,
            "purpose_title": purpose_title,
            "confidence": confidence,
            "confidence_percent": confidence_percent,
            "message": message,
            "tips": _ai_refinement_tips(raw_purpose),
            "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            "alternatives": prepared_alternatives,
            "matched_keywords": matched_keywords,
        }
    )


@app.get("/builder/{purpose}", response_class=HTMLResponse)
def builder_page(request: Request, purpose: str) -> HTMLResponse:
    context = {"request": request, **_builder_template_context(purpose)}
    return templates.TemplateResponse("index.html", context)


@app.post("/build", response_class=HTMLResponse)
async def build(request: Request) -> HTMLResponse:
    form = await request.form()
    inputs = _extract_user_inputs(form)
    payload = _build_pc_payload(inputs)

    if inputs.get("budget_mode") == "auto":
        payload.pop("budget", None)
        result = build_pc_auto_budget(**payload)
    else:
        result = build_pc(**payload)

    result = _validate_build_result(result)
    raw_alternatives = build_pc_alternatives(result, budget_mode=inputs.get("budget_mode", "manual"), **payload)
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
            result_payload = _validate_build_result(result_payload)
            result_payload = _attach_part_images(result_payload)
            public_card["result_payload"] = result_payload

        public_alternatives.append(public_card)

    if primary_result and primary_result.get("parts"):
        primary_result = dict(primary_result)
        primary_result["alternatives"] = public_alternatives
        result = _validate_build_result(primary_result)
    else:
        result["alternatives"] = public_alternatives

    result = _attach_part_images(result)
    return templates.TemplateResponse("result.html", _result_page_context(request, inputs, result))


@app.get("/saved-builds", response_class=HTMLResponse)
def saved_builds_page(request: Request) -> HTMLResponse:
    status = request.query_params.get("status", "")
    saved_builds = [_prepare_saved_build_for_list(build) for build in reversed(_load_saved_builds())]
    return templates.TemplateResponse(
        "saved-builds.html",
        {
            "request": request,
            "saved_builds": saved_builds,
            "status_message": STATUS_MESSAGES.get(status, ""),
        },
    )


@app.get("/saved-builds/view", response_class=HTMLResponse)
def saved_build_view_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("saved-build-view.html", {"request": request})


@app.post("/saved-builds/save")
async def save_build(request: Request) -> RedirectResponse:
    form = await request.form()
    raw_inputs = _extract_json_object(form.get("inputs_json", "{}"), field_name="inputs_json")
    raw_result = _extract_json_object(form.get("result_json", "{}"), field_name="result_json")

    purpose = str(raw_inputs.get("purpose", "gaming") or "gaming")
    budget_limits = _budget_limits_for_purpose(purpose)
    inputs = BuildInputsViewSchema.model_validate(
        raw_inputs,
        context={"budget_limits": budget_limits, "fps_limits": FPS_LIMITS},
    ).model_dump(mode="json")
    result = BuildResultSchema.model_validate(raw_result).model_dump(mode="json")

    build_name = _normalize_build_name(str(form.get("build_name", "")), inputs)

    saved_builds = _load_saved_builds()
    saved_builds.append(
        SavedBuildRecordSchema.model_validate(
            {
                "id": uuid4().hex,
                "name": build_name,
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "inputs": inputs,
                "result": result,
            }
        ).model_dump(mode="json")
    )
    _write_saved_builds(saved_builds)
    return RedirectResponse(url="/saved-builds?status=saved", status_code=303)


@app.get("/saved-builds/{build_id}", response_class=HTMLResponse)
def open_saved_build(request: Request, build_id: str) -> HTMLResponse:
    saved_build = _find_saved_build(build_id)
    if not saved_build:
        raise HTTPException(status_code=404, detail="Збірку не знайдено.")

    inputs = saved_build.get("inputs", {})
    result = _attach_part_images(saved_build.get("result", {}))
    return templates.TemplateResponse(
        "result.html",
        _result_page_context(request, inputs, result, saved_build_name=saved_build.get("name")),
    )


@app.post("/saved-builds/{build_id}/rename")
def rename_saved_build(build_id: str, build_name: str = Form(...)) -> RedirectResponse:
    saved_builds = _load_saved_builds()
    for build in saved_builds:
        if build.get("id") == build_id:
            build["name"] = _normalize_build_name(build_name, build.get("inputs", {}))
            _write_saved_builds(saved_builds)
            return RedirectResponse(url="/saved-builds?status=renamed", status_code=303)
    raise HTTPException(status_code=404, detail="Збірку не знайдено.")


@app.post("/saved-builds/{build_id}/delete")
def delete_saved_build(build_id: str) -> RedirectResponse:
    saved_builds = _load_saved_builds()
    filtered_builds = [build for build in saved_builds if build.get("id") != build_id]
    if len(filtered_builds) == len(saved_builds):
        raise HTTPException(status_code=404, detail="Збірку не знайдено.")

    _write_saved_builds(filtered_builds)
    return RedirectResponse(url="/saved-builds?status=deleted", status_code=303)

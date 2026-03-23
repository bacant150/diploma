from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from builder import build_pc, build_pc_auto_budget
from parts_db import CREATOR_APPS_DB, GAMES_DB, OFFICE_APPS_DB, STUDY_APPS_DB

try:
    from ml.predict import ACCEPTANCE_THRESHOLD as AI_ACCEPTANCE_THRESHOLD, predict_purpose
except Exception:
    AI_ACCEPTANCE_THRESHOLD = 0.70

    def predict_purpose(text: str) -> dict[str, Any]:
        return {
            "purpose": None,
            "raw_purpose": None,
            "confidence": 0.0,
            "accepted": False,
            "alternatives": [],
            "matched_keywords": {},
            "normalized_text": text.strip(),
        }


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

app = FastAPI()
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
    for part_data in parts.values():
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
    }


def _choose_purpose_context(request: Request) -> dict[str, Any]:
    return {
        "request": request,
        "purpose_titles": PURPOSE_TITLES,
        "ai_threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
    }


def _load_saved_builds() -> list[dict[str, Any]]:
    if not SAVED_BUILDS_FILE.exists():
        return []
    try:
        return json.loads(SAVED_BUILDS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write_saved_builds(saved_builds: list[dict[str, Any]]) -> None:
    SAVED_BUILDS_FILE.write_text(json.dumps(saved_builds, ensure_ascii=False, indent=2), encoding="utf-8")


def _form_str(form: Any, key: str, default: str = "") -> str:
    return str(form.get(key, default))


def _form_int(form: Any, key: str, default: int = 0) -> int:
    try:
        return int(form.get(key, default))
    except (TypeError, ValueError):
        return default


def _form_yes_no(form: Any, key: str, default: str = "no") -> bool:
    return _form_str(form, key, default) == "yes"


def _extract_user_inputs(form: Any) -> dict[str, Any]:
    games = form.getlist("games")
    office_apps = form.getlist("office_apps")
    study_apps = form.getlist("study_apps")
    creator_apps = form.getlist("creator_apps")

    purpose = _normalize_purpose(_form_str(form, "purpose", "gaming"))
    budget_mode = _form_str(form, "budget_mode", "manual")
    budget_limits = _budget_limits_for_purpose(purpose)

    budget = _form_int(form, "budget", budget_limits["min"])
    if budget_mode == "manual":
        budget = _clamp_int(budget, budget_limits["min"], budget_limits["max"])
    else:
        budget = 0

    target_fps = _clamp_int(_form_int(form, "target_fps", 60), FPS_LIMITS["min"], FPS_LIMITS["max"])

    inputs: dict[str, Any] = {
        "budget_mode": budget_mode,
        "budget": budget,
        "purpose": purpose,
        "resolution": _form_str(form, "resolution", "1080p"),
        "wifi": _form_yes_no(form, "wifi", "no"),
        "games": games,
        "graphics_quality": _form_str(form, "graphics_quality", "high"),
        "target_fps": target_fps,
        "gpu_mode": _form_str(form, "gpu_mode", "auto"),
        "cpu_brand": _form_str(form, "cpu_brand", "auto"),
        "gpu_brand": _form_str(form, "gpu_brand", "auto"),
        "ram_size": _form_str(form, "ram_size", "auto"),
        "ssd_size": _form_str(form, "ssd_size", "auto"),
        "memory_platform": _form_str(form, "memory_platform", "auto"),
        "office_apps": office_apps,
        "office_tabs": _form_str(form, "office_tabs", "auto"),
        "office_monitors": _form_str(form, "office_monitors", "auto"),
        "study_apps": study_apps,
        "study_tabs": _form_str(form, "study_tabs", "auto"),
        "study_monitors": _form_str(form, "study_monitors", "auto"),
        "creator_apps": creator_apps,
        "creator_complexity": _form_str(form, "creator_complexity", "auto"),
        "creator_monitors": _form_str(form, "creator_monitors", "auto"),
        "priority": _form_str(form, "priority", "auto"),
    }

    inputs["games_titles"] = [GAMES_DB[g]["title"] for g in games if g in GAMES_DB]
    inputs["office_apps_titles"] = [OFFICE_APPS_DB[a]["title"] for a in office_apps if a in OFFICE_APPS_DB]
    inputs["study_apps_titles"] = [STUDY_APPS_DB[a]["title"] for a in study_apps if a in STUDY_APPS_DB]
    inputs["creator_apps_titles"] = [CREATOR_APPS_DB[a]["title"] for a in creator_apps if a in CREATOR_APPS_DB]
    return inputs


def _build_pc_payload(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "budget": inputs["budget"],
        "purpose": inputs["purpose"],
        "resolution": inputs["resolution"],
        "wifi": inputs["wifi"],
        "games": inputs["games"],
        "graphics_quality": inputs["graphics_quality"],
        "target_fps": inputs["target_fps"],
        "gpu_mode": inputs["gpu_mode"],
        "cpu_brand": inputs["cpu_brand"],
        "gpu_brand": inputs["gpu_brand"],
        "ram_size": inputs["ram_size"],
        "ssd_size": inputs["ssd_size"],
        "memory_platform": inputs["memory_platform"],
        "office_apps": inputs["office_apps"],
        "office_tabs": inputs["office_tabs"],
        "office_monitors": inputs["office_monitors"],
        "study_apps": inputs["study_apps"],
        "study_tabs": inputs["study_tabs"],
        "study_monitors": inputs["study_monitors"],
        "creator_apps": inputs["creator_apps"],
        "creator_project_complexity": inputs["creator_complexity"],
        "creator_monitors": inputs["creator_monitors"],
        "priority": inputs["priority"],
    }


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


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/choose-purpose", response_class=HTMLResponse)
def choose_purpose(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("choose-purpose.html", _choose_purpose_context(request))


@app.post("/detect-purpose", response_class=JSONResponse)
async def detect_purpose(request: Request) -> JSONResponse:
    form = await request.form()
    description = _form_str(form, "description", "").strip()

    if len(description) < 8:
        return JSONResponse(
            {
                "ok": False,
                "accepted": False,
                "message": "Опиши потреби трохи детальніше, щоб ШІ міг коректно визначити тип ПК.",
                "tips": [
                    "Наприклад: ПК для CS2 і Dota 2 у Full HD.",
                    "Або: комп'ютер для Excel, M.E.Doc, браузера і документів.",
                ],
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            status_code=200,
        )

    try:
        prediction = predict_purpose(description)
    except Exception:
        return JSONResponse(
            {
                "ok": False,
                "accepted": False,
                "message": "Не вдалося обробити опис через помилку AI-модуля. Спробуй ще раз або обери тип ПК вручну.",
                "tips": _ai_refinement_tips(None),
                "threshold_percent": int(round(AI_ACCEPTANCE_THRESHOLD * 100)),
            },
            status_code=500,
        )

    raw_purpose = prediction.get("raw_purpose")
    confidence = prediction.get("confidence")
    accepted = bool(prediction.get("accepted"))
    confidence_percent = _confidence_to_percent(confidence)
    purpose_title = PURPOSE_TITLES.get(raw_purpose, "Невизначений тип") if raw_purpose else "Невизначений тип"

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
            f"ШІ припускає, що це {purpose_title.lower()}, але впевненість лише {confidence_percent}%. "
            "Опиши потреби конкретніше, і тоді система зможе точніше визначити тип ПК."
        )

    return JSONResponse(
        {
            "ok": True,
            "accepted": False,
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
    inputs = json.loads(str(form.get("inputs_json", "{}")))
    result = json.loads(str(form.get("result_json", "{}")))
    build_name = _normalize_build_name(str(form.get("build_name", "")), inputs)

    saved_builds = _load_saved_builds()
    saved_builds.append(
        {
            "id": uuid4().hex,
            "name": build_name,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "inputs": inputs,
            "result": result,
        }
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

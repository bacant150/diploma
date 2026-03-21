"""FastAPI-застосунок для інтелектуального підбору конфігурації ПК.

У цьому файлі:
- описані маршрути сторінок;
- зібрані допоміжні функції для читання форми;
- підготовлені дані для шаблонів Jinja2;
- додана логіка збереження, перейменування та видалення збірок;
- викликається основна логіка підбору з builder.py.
"""

from __future__ import annotations

from zoneinfo import ZoneInfo
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from builder import build_pc
from parts_db import CREATOR_APPS_DB, GAMES_DB, OFFICE_APPS_DB, STUDY_APPS_DB

KYIV_TZ = ZoneInfo("Europe/Kyiv")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
SAVED_BUILDS_FILE = BASE_DIR / "saved_builds.json"

# Єдина мапа назв сценаріїв. Вона використовується і для маршруту builder,
# і для шаблонів, щоб не дублювати однакові значення в кількох місцях.
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

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ===== Допоміжні функції для шаблонів і статичних файлів =====

def _slugify_part_name(name: str) -> str:
    """Перетворює назву комплектуючої на безпечну назву файлу зображення."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "part"


def _part_image_path(part_name: str) -> str | None:
    """Повертає шлях до зображення комплектуючої, якщо файл існує."""
    filename = f"{_slugify_part_name(part_name)}.webp"
    image_file = STATIC_DIR / "images" / "parts" / filename
    if image_file.exists():
        return f"/static/images/parts/{filename}"
    return None


def _attach_part_images(result: dict[str, Any]) -> dict[str, Any]:
    """Додає до кожної комплектуючої шлях до картинки для сторінки результату."""
    parts = result.get("parts", {})
    for part_data in parts.values():
        name = part_data.get("name")
        if name:
            part_data["image"] = _part_image_path(name)
            part_data["image_filename"] = f"{_slugify_part_name(name)}.webp"
    return result


def _build_option_list(db: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Готує список елементів формату {key, title} для чекбоксів у шаблоні."""
    return [{"key": key, "title": value["title"]} for key, value in db.items()]


def _normalize_purpose(purpose: str) -> str:
    """Повертає коректний сценарій або значення за замовчуванням."""
    return purpose if purpose in PURPOSE_TITLES else "gaming"


def _builder_template_context(purpose: str) -> dict[str, Any]:
    """Формує контекст для сторінки конфігуратора."""
    normalized_purpose = _normalize_purpose(purpose)
    return {
        "selected_purpose": normalized_purpose,
        "purpose_title": PURPOSE_TITLES[normalized_purpose],
        "games_list": _build_option_list(GAMES_DB),
        "office_apps_list": _build_option_list(OFFICE_APPS_DB),
        "study_apps_list": _build_option_list(STUDY_APPS_DB),
        "creator_apps_list": _build_option_list(CREATOR_APPS_DB),
    }


# ===== Допоміжні функції для читання та нормалізації форми =====

def _form_str(form: Any, key: str, default: str = "") -> str:
    """Безпечно дістає рядкове значення з форми."""
    return str(form.get(key, default))


def _form_int(form: Any, key: str, default: int = 0) -> int:
    """Безпечно дістає числове значення з форми."""
    try:
        return int(form.get(key, default))
    except (TypeError, ValueError):
        return default


def _form_yes_no(form: Any, key: str, default: str = "no") -> bool:
    """Перетворює yes/no зі форми у boolean-значення."""
    return _form_str(form, key, default) == "yes"


def _extract_user_inputs(form: Any) -> dict[str, Any]:
    """Збирає всі значення форми у словник для показу на сторінці результату."""
    games = form.getlist("games")
    office_apps = form.getlist("office_apps")
    study_apps = form.getlist("study_apps")
    creator_apps = form.getlist("creator_apps")

    inputs: dict[str, Any] = {
        "budget": _form_int(form, "budget", 0),
        "purpose": _normalize_purpose(_form_str(form, "purpose", "gaming")),
        "resolution": _form_str(form, "resolution", "1080p"),
        "wifi": _form_yes_no(form, "wifi", "no"),
        "games": games,
        "graphics_quality": _form_str(form, "graphics_quality", "high"),
        "target_fps": _form_int(form, "target_fps", 60),
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

    # Заздалегідь підготовлені назви потрібні лише для красивого відображення у шаблоні.
    inputs["games_titles"] = [GAMES_DB[g]["title"] for g in games if g in GAMES_DB]
    inputs["office_apps_titles"] = [OFFICE_APPS_DB[a]["title"] for a in office_apps if a in OFFICE_APPS_DB]
    inputs["study_apps_titles"] = [STUDY_APPS_DB[a]["title"] for a in study_apps if a in STUDY_APPS_DB]
    inputs["creator_apps_titles"] = [CREATOR_APPS_DB[a]["title"] for a in creator_apps if a in CREATOR_APPS_DB]
    return inputs


def _build_pc_payload(inputs: dict[str, Any]) -> dict[str, Any]:
    """Перетворює дані форми у payload для builder.build_pc(...)."""
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
        # Назва ключа тут має збігатися з підписом build_pc(...).
        "creator_project_complexity": inputs["creator_complexity"],
        "creator_monitors": inputs["creator_monitors"],
        "priority": inputs["priority"],
    }


# ===== Допоміжні функції для збережених збірок =====

def _ensure_saved_builds_file() -> None:
    """Створює JSON-файл для збережених збірок, якщо його ще не існує."""
    if not SAVED_BUILDS_FILE.exists():
        SAVED_BUILDS_FILE.write_text("[]", encoding="utf-8")


def _load_saved_builds() -> list[dict[str, Any]]:
    """Читає всі збережені збірки з JSON-файлу."""
    _ensure_saved_builds_file()
    try:
        raw = json.loads(SAVED_BUILDS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raw = []
    return raw if isinstance(raw, list) else []


def _write_saved_builds(saved_builds: list[dict[str, Any]]) -> None:
    """Повністю перезаписує файл зі збереженими збірками."""
    SAVED_BUILDS_FILE.write_text(
        json.dumps(saved_builds, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _default_build_name(inputs: dict[str, Any]) -> str:
    """Формує назву за замовчуванням, якщо користувач не ввів свою."""
    purpose_title = PURPOSE_TITLES.get(inputs.get("purpose", "gaming"), "Збірка ПК")
    timestamp = datetime.now(KYIV_TZ).strftime("%d.%m.%Y %H:%M")
    return f"{purpose_title} — {timestamp}"


def _normalize_build_name(build_name: str | None, inputs: dict[str, Any]) -> str:
    """Очищає назву збірки від зайвих пробілів і ставить дефолтну, якщо потрібно."""
    cleaned_name = (build_name or "").strip()
    return cleaned_name[:120] if cleaned_name else _default_build_name(inputs)


def _serialize_for_template(data: dict[str, Any]) -> str:
    """Серіалізує словник у JSON для передачі назад через hidden textarea."""
    return json.dumps(data, ensure_ascii=False)


def _prepare_saved_build_for_list(build: dict[str, Any]) -> dict[str, Any]:
    """Додає до збереженої збірки зручні поля для шаблону списку."""
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
    """Шукає одну збірку за її унікальним ідентифікатором."""
    for build in _load_saved_builds():
        if build.get("id") == build_id:
            return build
    return None


def _result_page_context(request: Request, inputs: dict[str, Any], result: dict[str, Any], *, saved_build_name: str | None = None) -> dict[str, Any]:
    """Готує контекст для шаблону result.html як для нової, так і для збереженої збірки."""
    return {
        "request": request,
        "inputs": inputs,
        "result": result,
        "inputs_json": _serialize_for_template(inputs),
        "result_json": _serialize_for_template(result),
        "saved_build_name": saved_build_name,
    }


# ===== Маршрути FastAPI =====

@app.get("/debug-paths", response_class=PlainTextResponse)
def debug_paths() -> str:
    """Допоміжний маршрут для швидкої перевірки шляхів до шаблонів і static-файлів."""
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
    """Головна сторінка лендингу."""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/choose-purpose", response_class=HTMLResponse)
def choose_purpose(request: Request) -> HTMLResponse:
    """Сторінка вибору типу ПК."""
    return templates.TemplateResponse("choose-purpose.html", {"request": request})


@app.get("/builder/{purpose}", response_class=HTMLResponse)
def builder_page(request: Request, purpose: str) -> HTMLResponse:
    """Відкриває сторінку конфігуратора для вибраного сценарію."""
    context = {"request": request, **_builder_template_context(purpose)}
    return templates.TemplateResponse("index.html", context)


@app.post("/build", response_class=HTMLResponse)
async def build(request: Request) -> HTMLResponse:
    """Обробляє форму, запускає підбір комплектуючих і повертає сторінку результату."""
    form = await request.form()
    inputs = _extract_user_inputs(form)
    result = build_pc(**_build_pc_payload(inputs))
    result = _attach_part_images(result)
    return templates.TemplateResponse("result.html", _result_page_context(request, inputs, result))


@app.get("/saved-builds", response_class=HTMLResponse)
def saved_builds_page(request: Request) -> HTMLResponse:
    """Показує список усіх збережених збірок."""
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


@app.post("/saved-builds/save")
async def save_build(request: Request) -> RedirectResponse:
    """Зберігає поточну збірку разом з її входом і результатом."""
    form = await request.form()
    inputs = json.loads(str(form.get("inputs_json", "{}")))
    result = json.loads(str(form.get("result_json", "{}")))
    build_name = _normalize_build_name(str(form.get("build_name", "")), inputs)

    saved_builds = _load_saved_builds()
    saved_builds.append(
        {
            "id": uuid4().hex,
            "name": build_name,
            "saved_at": datetime.now(KYIV_TZ).isoformat(timespec="seconds"),
            "inputs": inputs,
            "result": result,
        }
    )
    _write_saved_builds(saved_builds)
    return RedirectResponse(url="/saved-builds?status=saved", status_code=303)


@app.get("/saved-builds/{build_id}", response_class=HTMLResponse)
def open_saved_build(request: Request, build_id: str) -> HTMLResponse:
    """Відкриває окрему збережену збірку на тій самій сторінці результату."""
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
    """Оновлює назву вже збереженої збірки."""
    saved_builds = _load_saved_builds()
    for build in saved_builds:
        if build.get("id") == build_id:
            build["name"] = _normalize_build_name(build_name, build.get("inputs", {}))
            _write_saved_builds(saved_builds)
            return RedirectResponse(url="/saved-builds?status=renamed", status_code=303)
    raise HTTPException(status_code=404, detail="Збірку не знайдено.")


@app.post("/saved-builds/{build_id}/delete")
def delete_saved_build(build_id: str) -> RedirectResponse:
    """Видаляє збірку зі сховища."""
    saved_builds = _load_saved_builds()
    filtered_builds = [build for build in saved_builds if build.get("id") != build_id]
    if len(filtered_builds) == len(saved_builds):
        raise HTTPException(status_code=404, detail="Збірку не знайдено.")

    _write_saved_builds(filtered_builds)
    return RedirectResponse(url="/saved-builds?status=deleted", status_code=303)

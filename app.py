from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from builder import build_pc, build_pc_auto_budget
from parts_db import CREATOR_APPS_DB, GAMES_DB, OFFICE_APPS_DB, STUDY_APPS_DB


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Єдина мапа назв сценаріїв. Вона використовується і для маршруту builder,
# і для шаблонів, щоб не дублювати однакові значення в кількох місцях.
PURPOSE_TITLES = {
    "gaming": "Ігровий ПК",
    "office": "Офісний ПК",
    "study": "ПК для навчання",
    "creator": "ПК для монтажу / 3D",
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
        "budget_mode": _form_str(form, "budget_mode", "manual"),
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



def _serialize_for_template(data: dict[str, Any]) -> str:
    """Серіалізує словник у JSON для передачі в JavaScript через hidden textarea."""
    return json.dumps(data, ensure_ascii=False)


def _result_page_context(request: Request, inputs: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """Готує контекст для шаблону result.html для нової збірки."""
    return {
        "request": request,
        "inputs": inputs,
        "result": result,
        "inputs_json": _serialize_for_template(inputs),
        "result_json": _serialize_for_template(result),
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
    """Показує сторінку зі списком збережених збірок із localStorage браузера."""
    status = request.query_params.get("status", "")
    return templates.TemplateResponse(
        "saved-builds.html",
        {
            "request": request,
            "status_message": STATUS_MESSAGES.get(status, ""),
        },
    )


@app.get("/saved-builds/view", response_class=HTMLResponse)
def saved_build_view_page(request: Request) -> HTMLResponse:
    """Показує окрему сторінку перегляду збереженої збірки з localStorage."""
    return templates.TemplateResponse("saved-build-view.html", {"request": request})

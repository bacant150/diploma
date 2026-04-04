from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
SAVED_BUILDS_FILE = BASE_DIR / "saved_builds.json"
USER_PROFILES_FILE = BASE_DIR / "user_profiles.json"

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
    "history_deleted": "Запис видалено з історії.",
    "history_cleared": "Історію запитів очищено.",
}

# Нижні межі зроблені консервативнішими, щоб стартовий бюджет у формі
# давав робочий результат для типового сценарію без додаткових налаштувань.
BUDGET_LIMITS = {
    "gaming": {"min": 25000, "max": 250000},
    "office": {"min": 15500, "max": 120000},
    "study": {"min": 16500, "max": 150000},
    "creator": {"min": 35000, "max": 300000},
}

FPS_LIMITS = {"min": 30, "max": 500}

SHOW_DEBUG_ROUTES = os.getenv("APP_SHOW_DEBUG_ROUTES", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").strip().upper()

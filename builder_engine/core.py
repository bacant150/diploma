from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .common import _fail, _rebuild_parts_from_result
from .explanations import _enrich_result_with_component_explanations
from .postprocess import finalize_build_result
from .scenarios import build_creator_pc, build_gaming_pc, build_office_pc, build_study_pc

logger = logging.getLogger("pcbuilder.builder.core")


# ===== Головна точка входу =====
def build_pc(
    budget: int,
    purpose: str,
    resolution: str,
    wifi: bool,
    games: Optional[List[str]] = None,
    graphics_quality: str = "high",
    target_fps: int = 60,
    gpu_mode: str = "auto",
    cpu_brand: str = "auto",
    gpu_brand: str = "auto",
    ram_size: str = "auto",
    ssd_size: str = "auto",
    memory_platform: str = "auto",
    office_apps: Optional[List[str]] = None,
    office_tabs: str = "auto",
    office_monitors: str = "auto",
    study_apps: Optional[List[str]] = None,
    study_tabs: str = "auto",
    study_monitors: str = "auto",
    creator_apps: Optional[List[str]] = None,
    creator_project_complexity: str = "auto",
    creator_monitors: str = "auto",
    priority: str = "auto",
) -> Dict[str, object]:
    """
    Єдина публічна точка входу для підбору конфігурації.

    На основі `purpose` делегує логіку в окремий сценарій і повертає уніфікований
    словник результату для шаблону FastAPI.
    """
    if budget < 7000:
        logger.warning(
            "Спроба побудови конфігурації з надто малим бюджетом: budget=%s purpose=%s",
            budget,
            purpose,
        )
        return _fail("Бюджет занадто малий для збирання ПК.", "budget")

    context: Dict[str, Any] = {
        "resolution": resolution,
        "graphics_quality": graphics_quality,
        "target_fps": target_fps,
        "gpu_mode": gpu_mode,
        "cpu_brand": cpu_brand,
        "gpu_brand": gpu_brand,
        "ram_size": ram_size,
        "ssd_size": ssd_size,
        "memory_platform": memory_platform,
        "office_tabs": office_tabs,
        "office_monitors": office_monitors,
        "study_tabs": study_tabs,
        "study_monitors": study_monitors,
        "creator_project_complexity": creator_project_complexity,
        "creator_monitors": creator_monitors,
        "priority": priority,
    }

    logger.info(
        "Старт підбору конфігурації: purpose=%s budget=%s priority=%s gpu_mode=%s cpu_brand=%s gpu_brand=%s",
        purpose,
        budget,
        priority,
        gpu_mode,
        cpu_brand,
        gpu_brand,
    )

    if purpose == "gaming":
        result = build_gaming_pc(
            budget,
            resolution,
            wifi,
            games or [],
            graphics_quality,
            target_fps,
            gpu_mode,
            cpu_brand,
            gpu_brand,
            ram_size,
            ssd_size,
            memory_platform,
            priority,
        )
    elif purpose == "office":
        result = build_office_pc(
            budget,
            wifi,
            office_apps or [],
            office_tabs,
            office_monitors,
            gpu_mode,
            cpu_brand,
            ram_size,
            ssd_size,
            memory_platform,
            priority,
        )
    elif purpose == "study":
        result = build_study_pc(
            budget,
            wifi,
            study_apps or [],
            study_tabs,
            study_monitors,
            gpu_mode,
            cpu_brand,
            ram_size,
            ssd_size,
            memory_platform,
            priority,
        )
    elif purpose == "creator":
        result = build_creator_pc(
            budget,
            resolution,
            wifi,
            creator_apps or [],
            creator_project_complexity,
            creator_monitors,
            gpu_mode,
            cpu_brand,
            gpu_brand,
            ram_size,
            ssd_size,
            memory_platform,
            priority,
        )
    else:
        logger.error("Отримано невідоме призначення ПК: purpose=%s", purpose)
        return _fail("Невідоме призначення ПК.", "unknown")

    rebuilt_parts = _rebuild_parts_from_result(result)
    if rebuilt_parts:
        result = _enrich_result_with_component_explanations(
            result,
            rebuilt_parts,
            purpose,
            context,
        )
        result = finalize_build_result(
            result,
            parts=rebuilt_parts,
            purpose=purpose,
            context=context,
        )
        logger.info(
            "Побудову завершено: purpose=%s tier=%s total=%s parts=%s",
            purpose,
            result.get("tier"),
            result.get("total") or result.get("total_price"),
            len(rebuilt_parts),
        )
    else:
        logger.warning(
            "Не вдалося перебудувати parts з результату конфігурації: purpose=%s tier=%s",
            purpose,
            result.get("tier"),
        )

    return result

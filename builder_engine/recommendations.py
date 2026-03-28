from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .common import *  # noqa: F401,F403
from .core import build_pc
from .explanations import _part_label
from .scoring import *  # noqa: F401,F403

def _is_result_acceptable_for_auto_budget(result: Dict[str, object], purpose: str) -> bool:
    """Перевіряє, чи підходить знайдена збірка як мінімально достатня для авто-бюджету."""
    if not result.get("parts"):
        return False

    parts = _rebuild_parts_from_result(result)

    if purpose == "gaming":
        requirement = result.get("game_requirement", {})
        match_info = result.get("match_info", {})

        gpu = parts.get("GPU")
        cpu = parts.get("CPU")
        resolution = str(result.get("resolution", "1080p"))
        graphics_quality = str(result.get("graphics_quality", "high"))
        target_fps = int(result.get("target_fps", 60) or 60)
        gpu_mode = str(result.get("gpu_mode", "auto"))

        # Якщо користувач не просив лише вбудовану графіку, не рекомендуємо авто-бюджетом
        # ігрові збірки без дискретної відеокарти для вимогливих сценаріїв.
        demanding_scenario = (
            resolution in {"1440p", "4k"}
            or graphics_quality in {"high", "ultra"}
            or target_fps >= 100
        )
        if gpu_mode != "integrated" and demanding_scenario and gpu is None:
            return False

        if isinstance(requirement, dict) and requirement.get("is_active"):
            status = str(match_info.get("match_status"))
            gpu_ratio = float(match_info.get("gpu_ratio") or 0)
            cpu_ratio = float(match_info.get("cpu_ratio") or 0)

            # Для автоматичного бюджету беремо лише ті збірки, які реально покривають ціль,
            # а не просто "близькі" до неї.
            if status not in {"excellent", "good"}:
                return False

            if gpu_ratio < 0.97 or cpu_ratio < 0.97:
                return False

            # Додатковий захист від занадто слабких iGPU/low-end сценаріїв.
            if demanding_scenario:
                if gpu is None:
                    return False
                if resolution == "1440p" and int(gpu.meta.get("vram", 0)) < 8:
                    return False
                if resolution == "4k" and int(gpu.meta.get("vram", 0)) < 12:
                    return False

            return True

        # Якщо конкретні ігри не вибрані, все одно відсікаємо явно нелогічні сценарії.
        if demanding_scenario and gpu is None:
            return False
        if demanding_scenario and gpu is not None:
            if resolution == "1440p" and int(gpu.meta.get("vram", 0)) < 8:
                return False
            if resolution == "4k" and int(gpu.meta.get("vram", 0)) < 12:
                return False
        return True

    if purpose == "office":
        requirement = result.get("office_requirement", {})
        if isinstance(requirement, dict):
            return _office_match_status(parts, requirement) in {"excellent", "good"}
        return True

    if purpose == "study":
        requirement = result.get("study_requirement", {})
        if isinstance(requirement, dict):
            return _study_match_status(parts, requirement) in {"excellent", "good"}
        return True

    if purpose == "creator":
        requirement = result.get("creator_requirement", {})
        if isinstance(requirement, dict):
            return _creator_match_status(parts, requirement) in {"excellent", "good"}
        return True

    return bool(result.get("parts"))


def _auto_budget_settings(purpose: str, gpu_mode: str = "auto") -> Dict[str, int]:
    """Повертає діапазон і крок пошуку бюджету для різних сценаріїв."""
    if purpose == "gaming":
        if gpu_mode == "integrated":
            return {"start": 9000, "stop": 50000, "coarse_step": 3000, "fine_step": 500}
        return {"start": 14000, "stop": 250000, "coarse_step": 5000, "fine_step": 1000}
    if purpose == "office":
        return {"start": 8000, "stop": 120000, "coarse_step": 3000, "fine_step": 500}
    if purpose == "study":
        return {"start": 9000, "stop": 150000, "coarse_step": 3000, "fine_step": 500}
    if purpose == "creator":
        return {"start": 22000, "stop": 300000, "coarse_step": 8000, "fine_step": 2000}
    return {"start": 7000, "stop": 150000, "coarse_step": 3000, "fine_step": 500}


def _status_rank(status: str) -> float:
    return {
        "weak": 10.0,
        "near": 45.0,
        "good": 80.0,
        "excellent": 100.0,
        "standard": 30.0,
        "integrated": 20.0,
    }.get(status, 0.0)


def _auto_budget_candidate_score(result: Dict[str, object], purpose: str) -> float:
    """Оцінює, наскільки конфігурація близька до цілі, якщо точний збіг не знайдено."""
    parts = result.get("parts", {})
    if not isinstance(parts, dict) or not parts:
        return -1_000_000.0

    total = float(result.get("total", 0) or 0)

    if purpose == "gaming":
        match_info = result.get("match_info", {}) if isinstance(result.get("match_info"), dict) else {}
        requirement = result.get("game_requirement", {}) if isinstance(result.get("game_requirement"), dict) else {}
        gpu = parts.get("GPU") if isinstance(parts, dict) else None
        resolution = str(result.get("resolution", result.get("target_resolution", "1080p")) or "1080p")
        graphics_quality = str(result.get("graphics_quality", "high") or "high")
        target_fps = int(result.get("target_fps", 60) or 60)
        gpu_mode = str(result.get("gpu_mode", "auto") or "auto")

        score = _status_rank(str(match_info.get("match_status", "weak")))
        gpu_ratio = float(match_info.get("gpu_ratio") or 0)
        cpu_ratio = float(match_info.get("cpu_ratio") or 0)
        min_ratio = min(gpu_ratio, cpu_ratio) if gpu_ratio and cpu_ratio else 0.0
        score += min_ratio * 100.0

        demanding_scenario = (
            resolution in {"1440p", "4k"}
            or graphics_quality in {"high", "ultra"}
            or target_fps >= 100
        )

        if demanding_scenario and gpu_mode != "integrated" and gpu is None:
            score -= 200.0

        if gpu is not None:
            gpu_name = str(gpu.get("name", ""))
            gpu_obj = next((p for p in _cat("gpu") if p.name == gpu_name), None)
            vram = int(gpu_obj.meta.get("vram", 0)) if gpu_obj else 0
            if resolution == "1440p":
                score += 8.0 if vram >= 8 else -25.0
            elif resolution == "4k":
                score += 12.0 if vram >= 12 else -50.0
        elif demanding_scenario:
            score -= 160.0

        if isinstance(requirement, dict) and requirement.get("is_active") and min_ratio < 0.75:
            score -= 80.0

        return score + min(total / 10000.0, 20.0)

    if purpose == "office":
        requirement = result.get("office_requirement", {}) if isinstance(result.get("office_requirement"), dict) else {}
        parts_obj = {}
        if isinstance(parts, dict):
            for key, data in parts.items():
                if isinstance(data, dict):
                    name = data.get("name")
                    part = next((p for p in PARTS if p.name == name), None)
                    if part:
                        parts_obj[key] = part
        if parts_obj and requirement:
            status = _office_match_status(parts_obj, requirement)
            return _status_rank(status) + min(total / 10000.0, 20.0)
        return min(total / 10000.0, 20.0)

    if purpose == "study":
        requirement = result.get("study_requirement", {}) if isinstance(result.get("study_requirement"), dict) else {}
        parts_obj = {}
        if isinstance(parts, dict):
            for key, data in parts.items():
                if isinstance(data, dict):
                    name = data.get("name")
                    part = next((p for p in PARTS if p.name == name), None)
                    if part:
                        parts_obj[key] = part
        if parts_obj and requirement:
            status = _study_match_status(parts_obj, requirement)
            return _status_rank(status) + min(total / 10000.0, 20.0)
        return min(total / 10000.0, 20.0)

    if purpose == "creator":
        requirement = result.get("creator_requirement", {}) if isinstance(result.get("creator_requirement"), dict) else {}
        parts_obj = {}
        if isinstance(parts, dict):
            for key, data in parts.items():
                if isinstance(data, dict):
                    name = data.get("name")
                    part = next((p for p in PARTS if p.name == name), None)
                    if part:
                        parts_obj[key] = part
        if parts_obj and requirement:
            status = _creator_match_status(parts_obj, requirement)
            return _status_rank(status) + min(total / 10000.0, 20.0)
        return min(total / 10000.0, 20.0)

    return min(total / 10000.0, 20.0)


def build_pc_auto_budget(
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
    Автоматично підбирає мінімально достатній бюджет і повертає готову збірку.
    Пошук іде від меншого бюджету до більшого у два етапи: грубий і уточнювальний.
    """
    settings = _auto_budget_settings(purpose, gpu_mode=gpu_mode)
    start = settings["start"]
    stop = settings["stop"]
    coarse_step = settings["coarse_step"]
    fine_step = settings["fine_step"]

    common_kwargs = {
        "purpose": purpose,
        "resolution": resolution,
        "wifi": wifi,
        "games": games or [],
        "graphics_quality": graphics_quality,
        "target_fps": target_fps,
        "gpu_mode": gpu_mode,
        "cpu_brand": cpu_brand,
        "gpu_brand": gpu_brand,
        "ram_size": ram_size,
        "ssd_size": ssd_size,
        "memory_platform": memory_platform,
        "office_apps": office_apps or [],
        "office_tabs": office_tabs,
        "office_monitors": office_monitors,
        "study_apps": study_apps or [],
        "study_tabs": study_tabs,
        "study_monitors": study_monitors,
        "creator_apps": creator_apps or [],
        "creator_project_complexity": creator_project_complexity,
        "creator_monitors": creator_monitors,
        "priority": priority,
    }

    first_budget: Optional[int] = None
    first_result: Optional[Dict[str, object]] = None
    best_fallback_budget: Optional[int] = None
    best_fallback_result: Optional[Dict[str, object]] = None
    best_fallback_score = -1_000_000.0

    for budget in range(start, stop + coarse_step, coarse_step):
        result = build_pc(budget=budget, **common_kwargs)
        result["resolution"] = resolution
        result["graphics_quality"] = graphics_quality
        result["target_fps"] = target_fps
        result["gpu_mode"] = gpu_mode
        candidate_score = _auto_budget_candidate_score(result, purpose)
        if candidate_score > best_fallback_score:
            best_fallback_score = candidate_score
            best_fallback_budget = budget
            best_fallback_result = result

        if _is_result_acceptable_for_auto_budget(result, purpose):
            first_budget = budget
            first_result = result
            break

    if first_budget is None or first_result is None:
        if best_fallback_budget is None or best_fallback_result is None or not best_fallback_result.get("parts"):
            failed = _fail("Не вдалося автоматично підібрати бюджет для заданих параметрів.", "unknown")
            failed["recommended_budget"] = None
            failed["budget_mode"] = "auto"
            return failed

        fallback_notes = list(best_fallback_result.get("notes", []))
        fallback_notes.insert(0, "Точна конфігурація під задану ціль не знайдена. Підібрано найближчий доступний варіант.")
        fallback_notes.insert(1, f"Орієнтовний бюджет для найближчої доступної конфігурації: {best_fallback_budget} грн.")
        if purpose == "gaming":
            fallback_notes.insert(2, "Для повного досягнення цілі може знадобитися зниження FPS, графічних налаштувань або роздільної здатності.")

        best_fallback_result["notes"] = fallback_notes[:5]
        best_fallback_result["recommended_budget"] = best_fallback_budget
        best_fallback_result["budget_mode"] = "auto"
        best_fallback_result["resolution"] = resolution
        best_fallback_result["graphics_quality"] = graphics_quality
        best_fallback_result["target_fps"] = target_fps
        best_fallback_result["gpu_mode"] = gpu_mode
        best_fallback_result["auto_budget_exact_match"] = False
        return best_fallback_result

    refine_start = max(start, first_budget - coarse_step + fine_step)
    chosen_budget = first_budget
    chosen_result = first_result

    for budget in range(refine_start, first_budget + fine_step, fine_step):
        result = build_pc(budget=budget, **common_kwargs)
        result["resolution"] = resolution
        result["graphics_quality"] = graphics_quality
        result["target_fps"] = target_fps
        result["gpu_mode"] = gpu_mode
        if _is_result_acceptable_for_auto_budget(result, purpose):
            chosen_budget = budget
            chosen_result = result
            break

    notes = list(chosen_result.get("notes", []))
    notes.insert(0, f"Бюджет підібрано автоматично. Рекомендований бюджет: {chosen_budget} грн.")
    chosen_result["notes"] = notes
    chosen_result["recommended_budget"] = chosen_budget
    chosen_result["budget_mode"] = "auto"
    chosen_result["resolution"] = resolution
    chosen_result["graphics_quality"] = graphics_quality
    chosen_result["target_fps"] = target_fps
    chosen_result["gpu_mode"] = gpu_mode
    chosen_result["auto_budget_exact_match"] = True
    return chosen_result

TIER_TITLES = {
    "budget": "Бюджетний",
    "mid": "Середній",
    "upper": "Високий",
    "unknown": "Невизначений",
}


def _priority_card_title(priority: str) -> str:
    return {
        "auto": "Автоматичний підбір",
        "budget": "Бюджетний",
        "balanced": "Ціна / якість",
        "best": "Максимальна продуктивність",
    }.get(priority, "Автоматичний підбір")

def _changed_part_keys(primary_result: Dict[str, object], variant_result: Dict[str, object]) -> List[str]:
    primary_parts = primary_result.get("parts", {})
    variant_parts = variant_result.get("parts", {})
    if not isinstance(primary_parts, dict) or not isinstance(variant_parts, dict):
        return []

    ordered_roles = ["CPU", "GPU", "Motherboard", "RAM", "SSD", "PSU", "Case"]
    extra_roles = sorted((set(primary_parts.keys()) | set(variant_parts.keys())) - set(ordered_roles))
    all_roles = ordered_roles + extra_roles

    changed: List[str] = []
    for role in all_roles:
        primary_name = primary_parts.get(role, {}).get("name") if isinstance(primary_parts.get(role), dict) else None
        variant_name = variant_parts.get(role, {}).get("name") if isinstance(variant_parts.get(role), dict) else None
        if primary_name != variant_name:
            changed.append(role)
    return changed


def _round_budget_up(value: int, step: int = 500) -> int:
    if value <= 0:
        return 0
    return ((value + step - 1) // step) * step


def _result_signature(result: Dict[str, object]) -> Tuple[Tuple[str, str], ...]:
    raw_parts = result.get("parts", {})
    if not isinstance(raw_parts, dict):
        return tuple()

    signature: List[Tuple[str, str]] = []
    for role, part_data in raw_parts.items():
        if not isinstance(part_data, dict):
            continue
        signature.append((str(role), str(part_data.get("name", ""))))
    return tuple(sorted(signature))


def _parts_excerpt_from_result(result: Dict[str, object], purpose: str) -> List[Dict[str, str]]:
    raw_parts = result.get("parts", {})
    if not isinstance(raw_parts, dict):
        return []

    ordered_roles = ["CPU", "GPU", "RAM", "SSD"]
    excerpt: List[Dict[str, str]] = []

    for role in ordered_roles:
        part_data = raw_parts.get(role)
        if isinstance(part_data, dict) and part_data.get("name"):
            excerpt.append({"label": _part_label(role), "name": str(part_data.get("name", ""))})

    if purpose in {"office", "study", "gaming", "creator"} and "GPU" not in raw_parts:
        excerpt.insert(1 if excerpt else 0, {"label": "Відеокарта", "name": "Вбудована графіка процесора"})

    return excerpt[:4]


def _delta_text(total: int, primary_total: int, is_primary: bool) -> str:
    if is_primary or primary_total <= 0:
        return "Базова рекомендація системи"

    delta = total - primary_total
    if delta < 0:
        return f"Економія {abs(delta)} грн відносно основної рекомендації"
    if delta > 0:
        return f"Дорожче на {delta} грн відносно основної рекомендації"
    return "Така сама ціна, але інший акцент підбору"


PRIORITY_VARIANT_META = {
    "budget": {
        "title": "Бюджетна конфігурація",
        "description": "Акцент на економнішому підборі без виходу за межі сценарію використання.",
    },
    "balanced": {
        "title": "Збалансована конфігурація",
        "description": "Оптимальний компроміс між ціною, якістю та запасом продуктивності.",
    },
    "best": {
        "title": "Конфігурація максимальної продуктивності",
        "description": "Максимально продуктивний варіант у межах заданих параметрів.",
    },
}


def _priority_display_order(selected_priority: str) -> List[str]:
    base_order = ["budget", "balanced", "best"]
    normalized = selected_priority if selected_priority in base_order else "balanced"
    return [normalized] + [item for item in base_order if item != normalized]


def _requested_budget_for_result(result: Dict[str, object], budget_mode: str, fallback_budget: int) -> int:
    if budget_mode == "auto":
        return int(result.get("recommended_budget", 0) or result.get("total", 0) or fallback_budget)
    return int(fallback_budget or result.get("total", 0) or 0)



def _priority_budget_step(purpose: str) -> int:
    return {
        "office": 2000,
        "study": 2500,
        "gaming": 6000,
        "creator": 8000,
    }.get(purpose, 2500)



def _unique_budget_sequence(values: List[int]) -> List[int]:
    result: List[int] = []
    seen: set[int] = set()
    for value in values:
        normalized = _round_budget_up(int(value), step=500)
        if normalized < 7000 or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result



def _manual_priority_targets(max_budget: int, purpose: str) -> Dict[str, int]:
    if max_budget <= 0:
        return {"budget": 0, "balanced": 0, "best": 0}

    budget_factor, balanced_factor = {
        "office": (0.82, 0.92),
        "study": (0.84, 0.93),
        "gaming": (0.78, 0.90),
        "creator": (0.80, 0.90),
    }.get(purpose, (0.82, 0.92))

    step = max(1000, _priority_budget_step(purpose) // 2)
    best_target = _round_budget_up(max_budget, step=500)
    balanced_target = min(best_target, _round_budget_up(int(max_budget * balanced_factor), step=500))
    budget_target = min(best_target, _round_budget_up(int(max_budget * budget_factor), step=500))

    if balanced_target >= best_target:
        balanced_target = max(7000, best_target - step)
    if budget_target >= balanced_target:
        budget_target = max(7000, balanced_target - step)

    return {
        "budget": max(7000, budget_target),
        "balanced": max(7000, balanced_target),
        "best": max(7000, best_target),
    }



def _auto_priority_targets(base_result: Dict[str, object], common_kwargs: Dict[str, Any], purpose: str) -> Dict[str, int]:
    current_budget = int(base_result.get("recommended_budget", 0) or base_result.get("total", 0) or 0)
    gpu_mode = str(common_kwargs.get("gpu_mode", "auto"))
    settings = _auto_budget_settings(purpose, gpu_mode=gpu_mode)
    stop = settings["stop"]
    step = _priority_budget_step(purpose)
    bump = max(1000, step // 2)

    minimum_search_kwargs = dict(common_kwargs)
    minimum_search_kwargs["priority"] = "budget"
    min_budget, _ = _find_minimum_viable_config(max(current_budget, 7000), minimum_search_kwargs)

    budget_target = int(min_budget or current_budget or settings["start"])
    budget_target = min(stop, max(7000, _round_budget_up(budget_target, step=500)))

    balanced_target = _round_budget_up(max(budget_target + bump, int(budget_target * 1.12)), step=500)
    best_target = _round_budget_up(max(balanced_target + bump, int(budget_target * 1.28)), step=500)

    if balanced_target <= budget_target:
        balanced_target = budget_target + bump
    if best_target <= balanced_target:
        best_target = balanced_target + bump

    return {
        "budget": min(stop, budget_target),
        "balanced": min(stop, balanced_target),
        "best": min(stop, best_target),
    }



def _priority_variant_kwargs(common_kwargs: Dict[str, Any], priority: str, purpose: str, target_budget: int) -> Dict[str, Any]:
    variant_kwargs = dict(common_kwargs)
    variant_kwargs["priority"] = priority

    if variant_kwargs.get("memory_platform") == "auto":
        if purpose in {"office", "study"}:
            if priority == "budget":
                variant_kwargs["memory_platform"] = "ddr4"
            elif priority == "best" and target_budget >= 26000:
                variant_kwargs["memory_platform"] = "ddr5"
        elif purpose == "gaming":
            if priority == "budget" and target_budget < 60000:
                variant_kwargs["memory_platform"] = "ddr4"
            elif priority == "best" and target_budget >= 55000:
                variant_kwargs["memory_platform"] = "ddr5"
        elif purpose == "creator":
            if priority == "budget" and target_budget < 70000:
                variant_kwargs["memory_platform"] = "ddr4"
            elif priority == "best" and target_budget >= 70000:
                variant_kwargs["memory_platform"] = "ddr5"

    if variant_kwargs.get("ram_size") == "auto":
        if purpose in {"office", "study"}:
            variant_kwargs["ram_size"] = "16" if priority != "best" or target_budget < 26000 else "32"
        elif purpose == "gaming":
            if priority == "budget":
                variant_kwargs["ram_size"] = "16"
            elif priority == "balanced":
                variant_kwargs["ram_size"] = "16" if target_budget < 70000 else "32"
            else:
                variant_kwargs["ram_size"] = "32"
        elif purpose == "creator":
            variant_kwargs["ram_size"] = "32" if priority != "best" else "64"

    if variant_kwargs.get("ssd_size") == "auto":
        if purpose in {"office", "study"}:
            if priority == "budget":
                variant_kwargs["ssd_size"] = "512"
            elif priority == "balanced":
                variant_kwargs["ssd_size"] = "1000"
            else:
                variant_kwargs["ssd_size"] = "1000" if target_budget < 32000 else "2000"
        elif purpose == "gaming":
            if priority == "budget":
                variant_kwargs["ssd_size"] = "512"
            elif priority == "balanced":
                variant_kwargs["ssd_size"] = "1000"
            else:
                variant_kwargs["ssd_size"] = "1000" if target_budget < 85000 else "2000"
        elif purpose == "creator":
            if priority == "budget":
                variant_kwargs["ssd_size"] = "1000"
            elif priority == "balanced":
                variant_kwargs["ssd_size"] = "2000"
            else:
                variant_kwargs["ssd_size"] = "2000" if target_budget < 110000 else "4000"

    if variant_kwargs.get("gpu_mode") == "auto":
        if purpose in {"office", "study"} and priority == "budget":
            variant_kwargs["gpu_mode"] = "integrated"

    return variant_kwargs



def _build_variant_result(
    common_kwargs: Dict[str, Any],
    *,
    budget_mode: str,
    target_budget: int,
    priority: str,
) -> Dict[str, object]:
    purpose = str(common_kwargs.get("purpose", "gaming") or "gaming")
    variant_kwargs = _priority_variant_kwargs(common_kwargs, priority, purpose, target_budget)
    result = build_pc(budget=target_budget, **variant_kwargs)

    if result.get("parts"):
        result["priority"] = priority
        result["requested_budget"] = target_budget
        if budget_mode == "auto":
            notes = result.get("notes", [])
            if not isinstance(notes, list):
                notes = []
            auto_note = f"Орієнтир бюджету для режиму «{_priority_card_title(priority)}»: {target_budget} грн."
            if auto_note not in notes:
                notes.insert(0, auto_note)
            result["notes"] = notes[:5]
            result["recommended_budget"] = target_budget
            result["budget_mode"] = "auto"
    return result



def _candidate_budgets_for_variant(
    *,
    initial_budget: int,
    budget_mode: str,
    priority: str,
    purpose: str,
    manual_budget_cap: int,
) -> List[int]:
    step = max(500, _priority_budget_step(purpose) // 2)

    if budget_mode == "auto":
        budgets = [initial_budget]
        if priority == "budget":
            budgets += [max(7000, initial_budget - step), initial_budget + step, initial_budget + step * 2]
        elif priority == "balanced":
            budgets += [initial_budget + step, max(7000, initial_budget - step), initial_budget + step * 2]
        else:
            budgets += [initial_budget + step, initial_budget + step * 2, initial_budget + step * 3]
        return _unique_budget_sequence(budgets)

    cap = max(manual_budget_cap, initial_budget)
    budgets = [initial_budget]
    if priority == "budget":
        budgets += [max(7000, initial_budget - step), max(7000, initial_budget - step * 2), min(cap, initial_budget + step)]
    elif priority == "balanced":
        budgets += [min(cap, initial_budget + step), max(7000, initial_budget - step), cap]
    else:
        budgets += [cap, max(7000, cap - step), max(7000, cap - step * 2)]
    return _unique_budget_sequence([value for value in budgets if value <= cap])



def _build_distinct_variant(
    common_kwargs: Dict[str, Any],
    *,
    budget_mode: str,
    priority: str,
    initial_budget: int,
    used_signatures: set[Tuple[Tuple[str, str], ...]],
    manual_budget_cap: int,
) -> Dict[str, object]:
    purpose = str(common_kwargs.get("purpose", "gaming") or "gaming")
    last_result: Optional[Dict[str, object]] = None

    for candidate_budget in _candidate_budgets_for_variant(
        initial_budget=initial_budget,
        budget_mode=budget_mode,
        priority=priority,
        purpose=purpose,
        manual_budget_cap=manual_budget_cap,
    ):
        result = _build_variant_result(
            common_kwargs,
            budget_mode=budget_mode,
            target_budget=candidate_budget,
            priority=priority,
        )
        if not result.get("parts"):
            continue
        last_result = result
        signature = _result_signature(result)
        if signature and signature not in used_signatures:
            return result

    fallback = last_result or _build_variant_result(
        common_kwargs,
        budget_mode=budget_mode,
        target_budget=initial_budget,
        priority=priority,
    )

    fallback_signature = _result_signature(fallback)
    if fallback_signature and fallback_signature not in used_signatures:
        return fallback

    return {}



def _make_alternative_card(
    *,
    key: str,
    title: str,
    description: str,
    result: Dict[str, object],
    requested_budget: int,
    priority: str,
    purpose: str,
    primary_total: int,
    is_primary: bool = False,
    primary_result: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    total = int(result.get("total", 0) or 0)
    notes = result.get("notes", [])
    if not isinstance(notes, list):
        notes = []

    part_explanations = result.get("part_explanations", {})
    if not isinstance(part_explanations, dict):
        part_explanations = {}

    changed_keys = [] if is_primary else _changed_part_keys(primary_result or {}, result)
    changed_explanations = {role: part_explanations.get(role, "") for role in changed_keys if role in part_explanations}
    raw_parts = result.get("parts", {})
    if not isinstance(raw_parts, dict):
        raw_parts = {}

    return {
        "key": key,
        "title": title,
        "description": description,
        "is_primary": is_primary,
        "total": total,
        "requested_budget": requested_budget,
        "tier": result.get("tier", "unknown"),
        "tier_title": TIER_TITLES.get(str(result.get("tier", "unknown")), str(result.get("tier", "unknown"))),
        "priority": priority,
        "priority_title": _priority_card_title(priority),
        "delta_text": _delta_text(total, primary_total, is_primary),
        "parts_excerpt": _parts_excerpt_from_result(result, purpose),
        "parts": raw_parts,
        "notes": notes,
        "card_notes": notes[:2],
        "part_explanations": part_explanations,
        "changed_part_keys": changed_keys,
        "changed_part_explanations": changed_explanations,
        "_result": result,
    }



def _find_minimum_viable_config(max_budget: int, common_kwargs: Dict[str, Any]) -> Tuple[Optional[int], Optional[Dict[str, object]]]:
    purpose = str(common_kwargs.get("purpose", ""))
    gpu_mode = str(common_kwargs.get("gpu_mode", "auto"))
    settings = _auto_budget_settings(purpose, gpu_mode=gpu_mode)

    start = max(7000, settings["start"])
    stop = min(max_budget, settings["stop"])
    coarse_step = settings["coarse_step"]
    fine_step = settings["fine_step"]

    if stop < start:
        return None, None

    first_budget: Optional[int] = None
    first_result: Optional[Dict[str, object]] = None

    for budget in range(start, stop + coarse_step, coarse_step):
        result = build_pc(budget=budget, **common_kwargs)
        if _is_result_acceptable_for_auto_budget(result, purpose):
            first_budget = budget
            first_result = result
            break

    if first_budget is None or first_result is None:
        return None, None

    refine_start = max(start, first_budget - coarse_step + fine_step)
    chosen_budget = first_budget
    chosen_result = first_result

    for budget in range(refine_start, min(first_budget, stop) + fine_step, fine_step):
        if budget > stop:
            break
        result = build_pc(budget=budget, **common_kwargs)
        if _is_result_acceptable_for_auto_budget(result, purpose):
            chosen_budget = budget
            chosen_result = result
            break

    return chosen_budget, chosen_result



def build_pc_alternatives(
    base_result: Dict[str, object],
    budget_mode: str = "manual",
    **payload: Any,
) -> List[Dict[str, object]]:
    """Формує 3 пріоритетні конфігурації: бюджетну, збалансовану і продуктивну."""
    if not base_result.get("parts"):
        return []

    purpose = str(payload.get("purpose", "gaming") or "gaming")
    selected_priority = str(payload.get("priority", "balanced") or "balanced")
    manual_budget = int(payload.get("budget", 0) or 0)

    common_kwargs = dict(payload)
    common_kwargs.pop("budget", None)

    if budget_mode == "auto":
        target_budgets = _auto_priority_targets(base_result, common_kwargs, purpose)
    else:
        target_budgets = _manual_priority_targets(manual_budget, purpose)

    cards: List[Dict[str, object]] = []
    ordered_priorities = _priority_display_order(selected_priority)
    used_signatures: set[Tuple[Tuple[str, str], ...]] = set()
    primary_total = int(base_result.get("total", 0) or 0)

    for index, priority in enumerate(ordered_priorities):
        is_primary = index == 0
        target_budget = int(target_budgets.get(priority, manual_budget or primary_total or 0))
        variant_result = _build_distinct_variant(
            common_kwargs,
            budget_mode=budget_mode,
            priority=priority,
            initial_budget=target_budget,
            used_signatures=used_signatures,
            manual_budget_cap=manual_budget,
        )

        if not variant_result.get("parts"):
            continue

        signature = _result_signature(variant_result)
        if signature and signature in used_signatures:
            continue
        if signature:
            used_signatures.add(signature)

        if is_primary:
            primary_total = int(variant_result.get("total", 0) or 0)
            description = "Основна рекомендація відповідно до обраного тобою пріоритету підбору."
            title = "Рекомендована конфігурація"
        else:
            variant_meta = PRIORITY_VARIANT_META.get(priority, PRIORITY_VARIANT_META["balanced"])
            title = str(variant_meta["title"])
            description = str(variant_meta["description"])

        cards.append(
            _make_alternative_card(
                key=f"priority-{priority}",
                title=title,
                description=description,
                result=variant_result,
                requested_budget=_requested_budget_for_result(variant_result, budget_mode, target_budget),
                priority=priority,
                purpose=purpose,
                primary_total=primary_total,
                is_primary=is_primary,
                primary_result=cards[0]["_result"] if cards and not is_primary and isinstance(cards[0].get("_result"), dict) else (variant_result if is_primary else None),
            )
        )

    return cards

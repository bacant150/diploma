from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import app

from .common import *  # noqa: F401,F403

# ===== Оцінка продуктивності =====



def _gpu_game_score(gpu: Part) -> int:
    meta_score = gpu.meta.get("game_score")
    if isinstance(meta_score, (int, float)):
        return int(meta_score)

    scores = {
        "NVIDIA GTX 1650 4GB": 45,
        "AMD RX 6500 XT 4GB": 40,
        "NVIDIA GTX 1660 SUPER 6GB": 70,
        "NVIDIA RTX 2060 6GB": 78,
        "AMD RX 6600 8GB": 86,
        "NVIDIA RTX 3050 8GB": 82,
        "AMD RX 6600 XT 8GB": 101,
        "AMD RX 6650 XT 8GB": 108,
        "AMD RX 7600 8GB": 112,
        "NVIDIA RTX 3060 12GB": 108,
        "NVIDIA RTX 4060 8GB": 118,
        "AMD RX 6700 XT 12GB": 132,
        "AMD RX 6750 XT 12GB": 142,
        "NVIDIA RTX 4060 Ti 8GB": 138,
        "NVIDIA RTX 4060 Ti 16GB": 146,
        "AMD RX 7700 XT 12GB": 170,
        "NVIDIA RTX 4070 12GB": 176,
        "AMD RX 7800 XT 16GB": 200,
        "NVIDIA RTX 4070 SUPER 12GB": 205,
        "AMD RX 7900 GRE 16GB": 228,
        "NVIDIA RTX 4070 Ti SUPER 16GB": 255,
        "AMD RX 7900 XT 20GB": 288,
        "AMD RX 7900 XTX 24GB": 342,
        "NVIDIA RTX 4080 SUPER 16GB": 370,
        "NVIDIA RTX 4090 24GB": 470,
    }
    return scores.get(gpu.name, 50)



def _cpu_game_score(cpu: Part) -> int:
    meta_score = cpu.meta.get("game_score")
    if isinstance(meta_score, (int, float)):
        return int(meta_score)

    scores = {
        "AMD Athlon 3000G": 24,
        "AMD Ryzen 3 3200G": 40,
        "AMD Ryzen 3 4100": 58,
        "AMD Ryzen 5 4600G": 72,
        "AMD Ryzen 5 5500": 84,
        "AMD Ryzen 5 5600G": 92,
        "AMD Ryzen 5 5600": 100,
        "AMD Ryzen 5 5600X": 106,
        "AMD Ryzen 7 5700G": 112,
        "AMD Ryzen 7 5700X": 118,
        "AMD Ryzen 7 5800X": 122,
        "AMD Ryzen 7 5800X3D": 155,
        "AMD Ryzen 5 7500F": 126,
        "AMD Ryzen 5 7600": 132,
        "AMD Ryzen 7 7700": 145,
        "AMD Ryzen 7 7700X": 152,
        "AMD Ryzen 7 7800X3D": 190,
        "AMD Ryzen 9 7900": 176,
        "AMD Ryzen 9 7900X": 184,
        "AMD Ryzen 9 7950X": 196,
        "AMD Ryzen 9 7950X3D": 235,
        "Intel i3-12100": 76,
        "Intel i3-12100F": 74,
        "Intel i5-12400": 102,
        "Intel i5-12400F": 100,
        "Intel i5-13400": 122,
        "Intel i5-13400F": 120,
        "Intel i5-13600KF": 158,
        "Intel i7-12700": 140,
        "Intel i7-12700F": 138,
        "Intel i7-13700F": 170,
        "Intel i7-14700KF": 194,
        "Intel i9-13900KF": 218,
        "Intel i9-14900KF": 232,
    }
    return scores.get(cpu.name, 60)


def _quality_multiplier(graphics_quality: str) -> float:
    mapping = {
        "low": 0.72,
        "medium": 0.88,
        "high": 1.00,
        "ultra": 1.18,
    }
    return mapping.get(graphics_quality, 1.00)


def _resolution_multiplier(resolution: str) -> float:
    mapping = {
        "1080p": 1.00,
        "1440p": 1.32,
        "4k": 1.82,
    }
    return mapping.get(resolution, 1.00)


def _fps_multiplier(target_fps: int) -> float:
    target_fps = max(30, min(500, target_fps))
    if target_fps <= 60:
        return 1.00
    if target_fps <= 75:
        return 1.08
    if target_fps <= 90:
        return 1.16
    if target_fps <= 120:
        return 1.30
    if target_fps <= 144:
        return 1.42
    if target_fps <= 165:
        return 1.55
    if target_fps <= 240:
        return 1.80
    if target_fps <= 300:
        return 1.92
    if target_fps <= 360:
        return 2.08
    return 2.28


def _calculate_gaming_requirement(
    games: List[str],
    resolution: str,
    graphics_quality: str,
    target_fps: int,
) -> Dict[str, object]:
    """Розраховує мінімальні умовні вимоги до CPU/GPU під вибрані ігри."""
    target_fps = max(30, min(500, target_fps))
    valid_games = [g for g in games if g in GAMES_DB]

    if not valid_games:
        return {
            "required_gpu_score": 0,
            "required_cpu_score": 0,
            "selected_games": [],
            "is_active": False,
        }

    gpu_mult = _resolution_multiplier(resolution) * _quality_multiplier(graphics_quality) * _fps_multiplier(target_fps)

    cpu_fps_mult = (
        1.00 if target_fps <= 60 else
        1.12 if target_fps <= 90 else
        1.28 if target_fps <= 144 else
        1.48 if target_fps <= 240 else
        1.58 if target_fps <= 300 else
        1.68 if target_fps <= 360 else
        1.80
    )

    cpu_mult = (
        (1.00 if resolution == "1080p" else 1.08 if resolution == "1440p" else 1.15)
        * (0.92 if graphics_quality == "low" else 0.98 if graphics_quality == "medium" else 1.00 if graphics_quality == "high" else 1.04)
        * cpu_fps_mult
    )

    gpu_reqs: List[float] = []
    cpu_reqs: List[float] = []

    for game_key in valid_games:
        game = GAMES_DB[game_key]
        gpu_reqs.append(float(game["gpu_base"]) * gpu_mult)
        cpu_reqs.append(float(game["cpu_base"]) * cpu_mult)

    required_gpu = max(gpu_reqs)
    required_cpu = max(cpu_reqs)

    extra_games_bonus = min(max(len(valid_games) - 1, 0) * 0.04, 0.16)
    required_gpu *= (1.0 + extra_games_bonus)
    required_cpu *= (1.0 + extra_games_bonus * 0.7)

    return {
        "required_gpu_score": round(required_gpu, 1),
        "required_cpu_score": round(required_cpu, 1),
        "selected_games": valid_games,
        "is_active": True,
    }


def _gaming_target_label(requirement: Dict[str, object], graphics_quality: str, target_fps: int, resolution: str) -> str:
    if not requirement.get("is_active"):
        return "Використано стандартний режим підбору ігрової конфігурації."

    return (
        f"Ціль: {resolution}, {graphics_quality.upper()}, {target_fps} FPS у вибраних іграх."
    )


def _gaming_performance_label(parts: Dict[str, Part], resolution: str) -> str:
    gpu = parts.get("GPU")
    cpu = parts.get("CPU")
    if not gpu or not cpu:
        return "Збалансована ігрова конфігурація."

    gpu_score = _gpu_game_score(gpu)
    cpu_score = _cpu_game_score(cpu)
    combined = gpu_score * 0.7 + cpu_score * 0.3

    if resolution == "1080p":
        if combined >= 240:
            return "Орієнтовний клас: 1080p Ultra / дуже високий FPS."
        if combined >= 160:
            return "Орієнтовний клас: 1080p High / Ultra."
        return "Орієнтовний клас: 1080p Medium / High."

    if resolution == "1440p":
        if combined >= 255:
            return "Орієнтовний клас: 1440p Ultra."
        if combined >= 175:
            return "Орієнтовний клас: 1440p High."
        return "Орієнтовний клас: 1440p Medium."

    if combined >= 330:
        return "Орієнтовний клас: 4K High / Ultra."
    if combined >= 235:
        return "Орієнтовний клас: 4K Medium / High."
    return "Орієнтовний клас: 4K Medium."


def _motherboard_fit_score(cpu: Part, mb: Part, budget: int) -> float:
    score = 0.0
    socket = cpu.meta.get("socket")
    cpu_score = _cpu_game_score(cpu)
    mb_name = mb.name

    if socket == "AM5":
        if "X670E" in mb_name:
            score += 14
        elif "X670" in mb_name:
            score += 12
        elif "B650" in mb_name:
            score += 10
        elif "A620" in mb_name:
            score += 5

    elif socket == "LGA1700":
        if cpu_score >= 190:
            if "Z790" in mb_name:
                score += 14
            elif "Z690" in mb_name:
                score += 12
            elif "B760" in mb_name:
                score += 8
            elif "H610" in mb_name:
                score -= 22
        else:
            if "Z790" in mb_name or "Z690" in mb_name:
                score += 10
            elif "B760" in mb_name or "B660" in mb_name:
                score += 8
            elif "H610" in mb_name:
                score += 2

    elif socket == "AM4":
        if cpu_score >= 145:
            if "X570" in mb_name:
                score += 12
            elif "B550" in mb_name:
                score += 10
            elif "B450" in mb_name:
                score += 4
            elif "A520" in mb_name or "A320" in mb_name:
                score -= 12
        else:
            if "B550" in mb_name:
                score += 8
            elif "B450" in mb_name:
                score += 6
            elif "A520" in mb_name:
                score += 2

    if budget >= 38000 and mb.meta.get("ram_type") == "DDR5":
        score += 4

    return score


def _requirement_fit_bonus(
    gpu_score: float,
    cpu_score: float,
    required_gpu_score: float,
    required_cpu_score: float,
) -> float:
    if required_gpu_score <= 0 or required_cpu_score <= 0:
        return 0.0

    gpu_ratio = gpu_score / max(required_gpu_score, 1)
    cpu_ratio = cpu_score / max(required_cpu_score, 1)

    score = 0.0

    if gpu_ratio >= 1.10:
        score += 34
    elif gpu_ratio >= 1.0:
        score += 24
    elif gpu_ratio >= 0.93:
        score += 8
    else:
        score -= (1.0 - gpu_ratio) * 90

    if cpu_ratio >= 1.10:
        score += 24
    elif cpu_ratio >= 1.0:
        score += 18
    elif cpu_ratio >= 0.93:
        score += 6
    else:
        score -= (1.0 - cpu_ratio) * 80

    return score


def _gaming_build_score(
    parts: Dict[str, Part],
    resolution: str,
    budget: int,
    wifi_required: bool,
    requirement: Dict[str, object],
) -> float:
    gpu = parts.get("GPU")
    cpu = parts.get("CPU")
    mb = parts.get("Motherboard")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    psu = parts.get("PSU")
    case = parts.get("Case")

    if not gpu or not cpu or not mb or not ram or not ssd or not psu or not case:
        return -1_000_000

    total = sum(p.price for p in parts.values())
    if total > budget:
        return -1_000_000

    gpu_score = _gpu_game_score(gpu)
    cpu_score = _cpu_game_score(cpu)

    ram_size = int(ram.meta.get("size_gb", 0))
    ssd_size = int(ssd.meta.get("size_gb", 0))
    vram = int(gpu.meta.get("vram", 0))
    socket = cpu.meta.get("socket")
    psu_watt = int(psu.meta.get("watt", 0))
    required_watt = _estimate_required_watt(cpu, gpu, "gaming")

    if resolution == "1080p":
        score = gpu_score * 0.55 + cpu_score * 0.30
        min_ratio = 0.72
    elif resolution == "1440p":
        score = gpu_score * 0.65 + cpu_score * 0.22
        min_ratio = 0.60
    else:
        score = gpu_score * 0.75 + cpu_score * 0.15
        min_ratio = 0.50

    ratio = cpu_score / max(gpu_score, 1)
    if ratio < min_ratio:
        score -= (min_ratio - ratio) * 120

    expensive_cpu_for_gpu = cpu.price / max(gpu.price, 1)
    if resolution == "1080p" and expensive_cpu_for_gpu > 1.05:
        score -= (expensive_cpu_for_gpu - 1.05) * 35
    elif resolution in ("1440p", "4k") and expensive_cpu_for_gpu > 0.95:
        score -= (expensive_cpu_for_gpu - 0.95) * 30

    if ram_size >= 64:
        score += 16
    elif ram_size >= 32:
        score += 10
    elif ram_size >= 16:
        score += 6
    else:
        score -= 50

    if budget >= 38000 and ram_size < 32:
        score -= 14

    if ssd_size >= 4000:
        score += 10
    elif ssd_size >= 2000:
        score += 7
    elif ssd_size >= 1000:
        score += 4
    elif ssd_size >= 500:
        score += 1
    else:
        score -= 20

    if resolution == "4k" and vram < 12:
        score -= 60
    elif resolution == "1440p" and vram < 8:
        score -= 40
    elif resolution == "1080p" and vram < 8:
        score -= 25

    if socket == "AM5":
        score += 10
    elif socket == "LGA1700":
        score += 6
    elif socket == "AM4":
        score += 4

    score += _motherboard_fit_score(cpu, mb, budget)

    if psu_watt >= required_watt + 150:
        score += 7
    elif psu_watt >= required_watt:
        score += 4
    else:
        score -= 40

    if "Airflow" in case.name or "Showcase" in case.name:
        score += 4

    if wifi_required and mb.meta.get("wifi") is True:
        score += 4
    elif wifi_required and mb.meta.get("wifi") is not True:
        score -= 3

    score += _requirement_fit_bonus(
        gpu_score=gpu_score,
        cpu_score=cpu_score,
        required_gpu_score=float(requirement.get("required_gpu_score", 0)),
        required_cpu_score=float(requirement.get("required_cpu_score", 0)),
    )

    budget_left = budget - total
    usage_ratio = total / max(budget, 1)
    if budget_left < 0:
        score -= 100
    elif usage_ratio >= 0.88:
        score += 10
    elif usage_ratio >= 0.75:
        score += 6
    elif usage_ratio <= 0.55:
        score -= 10

    return score


def _evaluate_requirement_match(parts: Dict[str, Part], requirement: Dict[str, object]) -> Dict[str, object]:
    gpu = parts.get("GPU")
    cpu = parts.get("CPU")
    if not gpu or not cpu or not requirement.get("is_active"):
        return {
            "match_status": "standard",
            "gpu_ratio": None,
            "cpu_ratio": None,
            "match_note": "Працює стандартний режим оцінки без сценарію по конкретних іграх.",
        }

    gpu_ratio = _gpu_game_score(gpu) / max(float(requirement.get("required_gpu_score", 1)), 1)
    cpu_ratio = _cpu_game_score(cpu) / max(float(requirement.get("required_cpu_score", 1)), 1)
    min_ratio = min(gpu_ratio, cpu_ratio)

    if min_ratio >= 1.05:
        status = "excellent"
        note = "Конфігурація впевнено покриває задані вимоги із запасом."
    elif min_ratio >= 0.97:
        status = "good"
        note = "Конфігурація відповідає заданим вимогам для вибраних ігор."
    elif min_ratio >= 0.90:
        status = "near"
        note = "Конфігурація близька до цілі, але в окремих сценах може знадобитися невелике зниження налаштувань."
    else:
        status = "weak"
        note = "Конфігурація може не дотягувати до заданої цілі у найважчих вибраних іграх."

    return {
        "match_status": status,
        "gpu_ratio": round(gpu_ratio, 2),
        "cpu_ratio": round(cpu_ratio, 2),
        "match_note": note,
    }


def _budget_summary_note(total: int, budget: int) -> str:
    left = budget - total
    if left <= 1500:
        return f"Бюджет використано майже повністю: {total} грн із {budget} грн."
    return f"Загальна вартість збірки: {total} грн, залишок бюджету: ~{left} грн."


# ===== Офісний сценарій =====


def _office_cpu_score(cpu: Part) -> float:
    return _cpu_game_score(cpu)



def _office_igpu_score(cpu: Part) -> float:
    if cpu.meta.get("igpu") is not True:
        return 0.0

    meta_score = cpu.meta.get("office_igpu_score")
    if isinstance(meta_score, (int, float)):
        return float(meta_score)

    scores = {
        "AMD Ryzen 5 8600G": 96,
        "AMD Ryzen 7 8700G": 112,
        "AMD Ryzen 5 7600": 44,
        "AMD Ryzen 7 7700": 48,
        "AMD Ryzen 7 7800X3D": 50,
        "AMD Ryzen 9 7900": 50,
        "AMD Ryzen 9 7950X": 52,
        "Intel i3-12100": 40,
        "Intel i5-12400": 46,
        "Intel i5-12600K": 52,
        "Intel i5-13400": 50,
        "Intel i5-14500": 54,
        "Intel i5-14600K": 58,
        "Intel i7-12700": 56,
        "Intel i7-13700": 60,
        "Intel i7-14700": 62,
        "Intel i9-14900K": 68,
    }
    return scores.get(cpu.name, 36.0)


def _office_gpu_score(gpu: Optional[Part]) -> float:
    if not gpu:
        return 0.0
    return round(_gpu_game_score(gpu) * 0.42 + gpu.meta.get("vram", 0) * 2.0, 1)


def _office_tabs_ram_bonus(tabs: str) -> int:
    return {
        "auto": 0,
        "up_to_10": 0,
        "10_30": 4,
        "30_60": 8,
        "60_plus": 16,
    }.get(tabs, 0)


def _office_tabs_cpu_bonus(tabs: str) -> float:
    return {
        "auto": 0.0,
        "up_to_10": 0.0,
        "10_30": 8.0,
        "30_60": 18.0,
        "60_plus": 34.0,
    }.get(tabs, 0.0)


def _office_monitor_bonus(monitors: str) -> Dict[str, float]:
    mapping = {
        "auto": {"cpu": 0.0, "ram": 0, "gpu": 0.0},
        "1": {"cpu": 0.0, "ram": 0, "gpu": 0.0},
        "2": {"cpu": 8.0, "ram": 4, "gpu": 6.0},
        "3_plus": {"cpu": 18.0, "ram": 8, "gpu": 18.0},
    }
    return mapping.get(monitors, mapping["auto"])


def _office_default_apps() -> List[str]:
    return ["word", "excel", "browser", "zoom"]


def _calculate_office_requirement(
    office_apps: List[str],
    office_tabs: str,
    office_monitors: str,
    gpu_mode: str,
) -> Dict[str, object]:
    """Оцінює вимоги офісного сценарію за вибраними застосунками та режимом роботи."""
    valid_apps = [a for a in office_apps if a in OFFICE_APPS_DB]
    if not valid_apps:
        valid_apps = _office_default_apps()

    cpu_required = 0.0
    ram_required = 8
    ssd_required = 256
    gpu_required = 0.0
    dedicated_needed = False

    for app_key in valid_apps:
        app = OFFICE_APPS_DB[app_key]
        cpu_required = max(cpu_required, float(app["cpu_base"]))
        ram_required = max(ram_required, int(app["ram_gb"]))
        ssd_required = max(ssd_required, int(app["ssd_gb"]))
        gpu_required = max(gpu_required, float(app["gpu_need"]))
        if float(app["gpu_need"]) >= 70:
            dedicated_needed = True

    extra_apps = max(0, len(valid_apps) - 1)
    cpu_required += extra_apps * 7.0
    ram_required += min(extra_apps * 2, 12)
    ssd_required += min(extra_apps * 64, 512)

    cpu_required += _office_tabs_cpu_bonus(office_tabs)
    ram_required += _office_tabs_ram_bonus(office_tabs)

    mon_bonus = _office_monitor_bonus(office_monitors)
    cpu_required += float(mon_bonus["cpu"])
    ram_required += int(mon_bonus["ram"])
    gpu_required += float(mon_bonus["gpu"])

    if office_monitors == "3_plus":
        dedicated_needed = dedicated_needed or gpu_required >= 55

    if gpu_mode == "dedicated":
        dedicated_needed = True
    elif gpu_mode == "integrated":
        dedicated_needed = False

    ram_required = max(4, min(256, ram_required))
    available_ram = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})
    target_ram = min(available_ram, key=lambda x: (abs(x - ram_required), x)) if available_ram else ram_required
    available_ssd = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})
    target_ssd = min(available_ssd, key=lambda x: (abs(x - ssd_required), x)) if available_ssd else ssd_required

    return {
        "selected_apps": valid_apps,
        "required_cpu_score": round(cpu_required, 1),
        "required_ram_gb": target_ram,
        "required_ssd_gb": target_ssd,
        "required_gpu_score": round(gpu_required, 1),
        "requires_dedicated_gpu": dedicated_needed,
        "tabs": office_tabs,
        "monitors": office_monitors,
    }


def _office_ram_targets(requirement: Dict[str, object], ram_size: str) -> List[int]:
    preferred = _parse_preference_size(ram_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})
    if preferred in available:
        others = [x for x in available if x != preferred]
        return [preferred] + sorted(others, key=lambda x: (abs(x - preferred), x))
    target = int(requirement.get("required_ram_gb", 16))
    return sorted(available, key=lambda x: (0 if x >= target else 1, abs(x - target), x))


def _office_ssd_targets(requirement: Dict[str, object], ssd_size: str) -> List[int]:
    preferred = _parse_preference_size(ssd_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})
    if preferred in available:
        others = [x for x in available if x != preferred]
        return [preferred] + sorted(others, key=lambda x: (abs(x - preferred), x))
    target = int(requirement.get("required_ssd_gb", 512))
    return sorted(available, key=lambda x: (0 if x >= target else 1, abs(x - target), x))


def _office_can_use_igpu(requirement: Dict[str, object], cpu: Part) -> bool:
    if cpu.meta.get("igpu") is not True:
        return False
    gpu_need = float(requirement.get("required_gpu_score", 0))
    monitors = requirement.get("monitors")
    igpu_score = _office_igpu_score(cpu)
    if monitors == "3_plus" and igpu_score < 60:
        return False
    return igpu_score >= gpu_need * 0.9


def _office_build_score(parts: Dict[str, Part], budget: int, requirement: Dict[str, object], wifi_required: bool) -> float:
    cpu = parts.get("CPU")
    mb = parts.get("Motherboard")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    psu = parts.get("PSU")
    case = parts.get("Case")
    gpu = parts.get("GPU")
    if not cpu or not mb or not ram or not ssd or not psu or not case:
        return -1_000_000
    total = sum(p.price for p in parts.values())
    if total > budget:
        return -1_000_000

    cpu_score = _office_cpu_score(cpu)
    req_cpu = float(requirement.get("required_cpu_score", 0))
    ram_gb = int(ram.meta.get("size_gb", 0))
    req_ram = int(requirement.get("required_ram_gb", 8))
    ssd_gb = int(ssd.meta.get("size_gb", 0))
    req_ssd = int(requirement.get("required_ssd_gb", 256))
    req_gpu = float(requirement.get("required_gpu_score", 0))
    need_dedicated = bool(requirement.get("requires_dedicated_gpu", False))

    graphics_score = _office_gpu_score(gpu) if gpu else _office_igpu_score(cpu)

    score = 0.0
    score += min(cpu_score / max(req_cpu, 1), 1.45) * 42
    score += min(ram_gb / max(req_ram, 1), 1.65) * 26
    score += min(ssd_gb / max(req_ssd, 1), 1.50) * 14
    score += min(graphics_score / max(req_gpu, 1), 1.6) * 16 if req_gpu > 0 else 8

    if need_dedicated and not gpu:
        score -= 65
    if not need_dedicated and gpu and budget < 30000:
        score -= 8

    if wifi_required and mb.meta.get("wifi") is True:
        score += 4
    elif wifi_required:
        score -= 4

    if int(requirement.get("required_ram_gb", 0)) >= 32 and ram_gb < 32:
        score -= 14
    if int(requirement.get("required_ssd_gb", 0)) >= 1000 and ssd_gb < 1000:
        score -= 12

    if budget >= 50000 and total < budget * 0.62:
        score -= 10
    elif budget >= 50000 and total >= budget * 0.78:
        score += 6

    left = budget - total
    if 0 <= left <= 2000:
        score += 6

    if cpu.meta.get("socket") == "AM5":
        score += 5
    elif cpu.meta.get("socket") == "LGA1700":
        score += 4

    return score


def _office_match_status(parts: Dict[str, Part], requirement: Dict[str, object]) -> str:
    cpu = parts.get("CPU")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    gpu = parts.get("GPU")
    if not cpu or not ram or not ssd:
        return "weak"
    cpu_ratio = _office_cpu_score(cpu) / max(float(requirement.get("required_cpu_score", 1)), 1)
    ram_ratio = int(ram.meta.get("size_gb", 0)) / max(int(requirement.get("required_ram_gb", 1)), 1)
    ssd_ratio = int(ssd.meta.get("size_gb", 0)) / max(int(requirement.get("required_ssd_gb", 1)), 1)
    graphics_score = _office_gpu_score(gpu) if gpu else _office_igpu_score(cpu)
    req_gpu = float(requirement.get("required_gpu_score", 0))
    gpu_ratio = graphics_score / max(req_gpu, 1) if req_gpu > 0 else 1.0
    min_ratio = min(cpu_ratio, ram_ratio, ssd_ratio, gpu_ratio)
    if min_ratio >= 1.08:
        return "excellent"
    if min_ratio >= 1.0:
        return "good"
    if min_ratio >= 0.9:
        return "near"
    return "weak"


# ===== Додаткові ігрові фільтри =====

def _priority_label(priority: str) -> str:
    return {
        "auto": "автоматичний підбір",
        "budget": "бюджетний режим",
        "balanced": "збалансований режим (ціна/якість)",
        "best": "режим максимальної продуктивності",
    }.get(priority, "автоматичний підбір")


def _priority_score_adjustment(total: int, budget: int, priority: str) -> float:
    usage = total / max(budget, 1)
    left = budget - total
    if priority == "budget":
        if usage < 0.55:
            return -6.0
        if 0.60 <= usage <= 0.82:
            return 16.0
        if 0.82 < usage <= 0.90:
            return 8.0
        if usage > 0.95:
            return -12.0
        return 2.0 + max(left, 0) / max(budget, 1) * 6.0
    if priority == "balanced":
        if 0.78 <= usage <= 0.93:
            return 12.0
        if 0.68 <= usage < 0.78 or 0.93 < usage <= 1.0:
            return 6.0
        if usage < 0.58:
            return -10.0
        return 0.0
    if priority == "best":
        if 0 <= left <= max(2500, int(budget * 0.06)):
            return 16.0
        if usage >= 0.90:
            return 12.0
        if usage >= 0.82:
            return 6.0
        return -usage * 2.0
    return 0.0


def _priority_note(priority: str) -> str:
    if priority == "budget":
        return "Пріоритет підбору: бюджетний варіант з акцентом на економію."
    if priority == "balanced":
        return "Пріоритет підбору: збалансовано (ціна/якість)."
    if priority == "best":
        return "Пріоритет підбору: максимальна продуктивність у межах бюджету."
    return "Пріоритет підбору: автоматично."


# ===== Сценарій для навчання =====


def _study_default_apps() -> List[str]:
    return ["docs", "browser", "zoom"]


def _study_tabs_ram_bonus(tabs: str) -> int:
    return {
        "auto": 0,
        "up_to_10": 0,
        "10_30": 4,
        "30_60": 8,
        "60_plus": 16,
    }.get(tabs, 0)


def _study_tabs_cpu_bonus(tabs: str) -> float:
    return {
        "auto": 0.0,
        "up_to_10": 0.0,
        "10_30": 6.0,
        "30_60": 14.0,
        "60_plus": 28.0,
    }.get(tabs, 0.0)


def _study_monitor_bonus(monitors: str) -> Dict[str, float]:
    mapping = {
        "auto": {"cpu": 0.0, "ram": 0, "gpu": 0.0},
        "1": {"cpu": 0.0, "ram": 0, "gpu": 0.0},
        "2": {"cpu": 6.0, "ram": 4, "gpu": 5.0},
        "3_plus": {"cpu": 14.0, "ram": 8, "gpu": 14.0},
    }
    return mapping.get(monitors, mapping["auto"])


def _calculate_study_requirement(
    study_apps: List[str],
    study_tabs: str,
    study_monitors: str,
    gpu_mode: str,
) -> Dict[str, object]:
    """Оцінює вимоги навчального сценарію за програмами, вкладками та моніторами."""
    valid_apps = [a for a in study_apps if a in STUDY_APPS_DB]
    if not valid_apps:
        valid_apps = _study_default_apps()

    cpu_required = 0.0
    ram_required = 8
    ssd_required = 256
    gpu_required = 0.0
    dedicated_needed = False

    for app_key in valid_apps:
        app = STUDY_APPS_DB.get(app_key) or OFFICE_APPS_DB.get(app_key)
        if app is None:
            continue
        cpu_required = max(cpu_required, float(app["cpu_base"]))
        ram_required = max(ram_required, int(app["ram_gb"]))
        ssd_required = max(ssd_required, int(app["ssd_gb"]))
        gpu_required = max(gpu_required, float(app["gpu_need"]))
        if float(app["gpu_need"]) >= 60:
            dedicated_needed = True

    extra_apps = max(0, len(valid_apps) - 1)
    cpu_required += extra_apps * 6.0
    ram_required += min(extra_apps * 2, 12)
    ssd_required += min(extra_apps * 64, 512)

    cpu_required += _study_tabs_cpu_bonus(study_tabs)
    ram_required += _study_tabs_ram_bonus(study_tabs)

    mon_bonus = _study_monitor_bonus(study_monitors)
    cpu_required += float(mon_bonus["cpu"])
    ram_required += int(mon_bonus["ram"])
    gpu_required += float(mon_bonus["gpu"])

    if study_monitors == "3_plus":
        dedicated_needed = dedicated_needed or gpu_required >= 50

    if gpu_mode == "dedicated":
        dedicated_needed = True
    elif gpu_mode == "integrated":
        dedicated_needed = False

    ram_required = max(4, min(256, ram_required))
    available_ram = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})
    target_ram = min(available_ram, key=lambda x: (abs(x - ram_required), x)) if available_ram else ram_required
    available_ssd = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})
    target_ssd = min(available_ssd, key=lambda x: (abs(x - ssd_required), x)) if available_ssd else ssd_required

    return {
        "selected_apps": valid_apps,
        "required_cpu_score": round(cpu_required, 1),
        "required_ram_gb": target_ram,
        "required_ssd_gb": target_ssd,
        "required_gpu_score": round(gpu_required, 1),
        "requires_dedicated_gpu": dedicated_needed,
        "tabs": study_tabs,
        "monitors": study_monitors,
    }


def _study_ram_targets(requirement: Dict[str, object], ram_size: str) -> List[int]:
    preferred = _parse_preference_size(ram_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})
    if preferred in available:
        others = [x for x in available if x != preferred]
        return [preferred] + sorted(others, key=lambda x: (abs(x - preferred), x))
    target = int(requirement.get("required_ram_gb", 16))
    return sorted(available, key=lambda x: (0 if x >= target else 1, abs(x - target), x))


def _study_ssd_targets(requirement: Dict[str, object], ssd_size: str) -> List[int]:
    preferred = _parse_preference_size(ssd_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})
    if preferred in available:
        others = [x for x in available if x != preferred]
        return [preferred] + sorted(others, key=lambda x: (abs(x - preferred), x))
    target = int(requirement.get("required_ssd_gb", 512))
    return sorted(available, key=lambda x: (0 if x >= target else 1, abs(x - target), x))


def _study_can_use_igpu(requirement: Dict[str, object], cpu: Part) -> bool:
    if cpu.meta.get("igpu") is not True:
        return False
    gpu_need = float(requirement.get("required_gpu_score", 0))
    monitors = requirement.get("monitors")
    igpu_score = _office_igpu_score(cpu)
    if monitors == "3_plus" and igpu_score < 58:
        return False
    return igpu_score >= gpu_need * 0.9


def _study_build_score(parts: Dict[str, Part], budget: int, requirement: Dict[str, object], wifi_required: bool) -> float:
    cpu = parts.get("CPU")
    mb = parts.get("Motherboard")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    psu = parts.get("PSU")
    case = parts.get("Case")
    gpu = parts.get("GPU")
    if not cpu or not mb or not ram or not ssd or not psu or not case:
        return -1_000_000
    total = sum(p.price for p in parts.values())
    if total > budget:
        return -1_000_000

    cpu_score = _office_cpu_score(cpu)
    req_cpu = float(requirement.get("required_cpu_score", 0))
    ram_gb = int(ram.meta.get("size_gb", 0))
    req_ram = int(requirement.get("required_ram_gb", 8))
    ssd_gb = int(ssd.meta.get("size_gb", 0))
    req_ssd = int(requirement.get("required_ssd_gb", 256))
    req_gpu = float(requirement.get("required_gpu_score", 0))
    need_dedicated = bool(requirement.get("requires_dedicated_gpu", False))
    graphics_score = _office_gpu_score(gpu) if gpu else _office_igpu_score(cpu)

    score = 0.0
    score += min(cpu_score / max(req_cpu, 1), 1.45) * 40
    score += min(ram_gb / max(req_ram, 1), 1.65) * 28
    score += min(ssd_gb / max(req_ssd, 1), 1.50) * 16
    score += min(graphics_score / max(req_gpu, 1), 1.6) * 14 if req_gpu > 0 else 8

    if need_dedicated and not gpu:
        score -= 70
    if not need_dedicated and gpu and budget < 32000:
        score -= 8

    if wifi_required and mb.meta.get("wifi") is True:
        score += 4
    elif wifi_required:
        score -= 4

    if req_ram >= 32 and ram_gb < 32:
        score -= 14
    if req_ssd >= 1000 and ssd_gb < 1000:
        score -= 12

    left = budget - total
    if 0 <= left <= 2000:
        score += 6

    if cpu.meta.get("socket") == "AM5":
        score += 5
    elif cpu.meta.get("socket") == "LGA1700":
        score += 4

    return score


def _study_match_status(parts: Dict[str, Part], requirement: Dict[str, object]) -> str:
    cpu = parts.get("CPU")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    gpu = parts.get("GPU")
    if not cpu or not ram or not ssd:
        return "weak"
    cpu_ratio = _office_cpu_score(cpu) / max(float(requirement.get("required_cpu_score", 1)), 1)
    ram_ratio = int(ram.meta.get("size_gb", 0)) / max(int(requirement.get("required_ram_gb", 1)), 1)
    ssd_ratio = int(ssd.meta.get("size_gb", 0)) / max(int(requirement.get("required_ssd_gb", 1)), 1)
    graphics_score = _office_gpu_score(gpu) if gpu else _office_igpu_score(cpu)
    req_gpu = float(requirement.get("required_gpu_score", 0))
    gpu_ratio = graphics_score / max(req_gpu, 1) if req_gpu > 0 else 1.0
    min_ratio = min(cpu_ratio, ram_ratio, ssd_ratio, gpu_ratio)
    if min_ratio >= 1.08:
        return "excellent"
    if min_ratio >= 1.0:
        return "good"
    if min_ratio >= 0.9:
        return "near"
    return "weak"

# ===== Сценарій creator / монтаж / 3D =====


def _creator_default_apps() -> List[str]:
    return ["premiere", "photoshop", "blender"]


def _creator_complexity_bonus(level: str) -> Dict[str, float]:
    """
    Повертає бонус до вимог для creator-сценарію.

    Підтримує і внутрішні значення логіки (`basic`, `advanced`, `pro`), і значення
    з HTML-форми (`light`, `medium`, `heavy`). Це прибирає баг, коли частина
    вибору користувача ігнорувалася через різні назви одного й того ж рівня.
    """
    aliases = {
        "light": "basic",
        "medium": "medium",
        "heavy": "advanced",
    }
    normalized = aliases.get(level, level)

    mapping = {
        "auto": {"cpu": 0.0, "ram": 0, "gpu": 0.0, "ssd": 0, "vram": 0},
        "basic": {"cpu": 0.0, "ram": 0, "gpu": 0.0, "ssd": 0, "vram": 0},
        "medium": {"cpu": 10.0, "ram": 8, "gpu": 10.0, "ssd": 500, "vram": 2},
        "advanced": {"cpu": 22.0, "ram": 16, "gpu": 22.0, "ssd": 1000, "vram": 4},
        "pro": {"cpu": 36.0, "ram": 32, "gpu": 34.0, "ssd": 2000, "vram": 8},
    }
    return mapping.get(normalized, mapping["auto"])


def _creator_monitor_bonus(monitors: str) -> Dict[str, float]:
    mapping = {
        "auto": {"cpu": 0.0, "ram": 0, "gpu": 0.0},
        "1": {"cpu": 0.0, "ram": 0, "gpu": 0.0},
        "2": {"cpu": 8.0, "ram": 8, "gpu": 8.0},
        "3_plus": {"cpu": 18.0, "ram": 16, "gpu": 18.0},
    }
    return mapping.get(monitors, mapping["auto"])


def _creator_resolution_bonus(resolution: str) -> Dict[str, float]:
    mapping = {
        "1080p": {"gpu": 0.0, "vram": 0},
        "1440p": {"gpu": 8.0, "vram": 2},
        "4k": {"gpu": 18.0, "vram": 4},
    }
    return mapping.get(resolution, mapping["1080p"])


def _creator_complexity_label(level: str) -> str:
    """Повертає підпис складності проєктів."""
    mapping = {
        "auto": "авто",
        "light": "легкі",
        "basic": "базові",
        "medium": "середні",
        "heavy": "важкі",
        "advanced": "складні",
        "pro": "професійні",
    }
    return mapping.get(level, level)


def _calculate_creator_requirement(
    creator_apps: List[str],
    project_complexity: str,
    creator_monitors: str,
    resolution: str,
    gpu_mode: str,
) -> Dict[str, object]:
    """Оцінює вимоги creator-сценарію за програмами, складністю та роздільною здатністю."""
    valid_apps = [a for a in creator_apps if a in CREATOR_APPS_DB]
    if not valid_apps:
        valid_apps = _creator_default_apps()

    cpu_required = 80.0
    ram_required = 16
    ssd_required = 512
    gpu_required = 35.0
    vram_required = 6
    dedicated_needed = True

    for app_key in valid_apps:
        app = CREATOR_APPS_DB.get(app_key)
        if app is None:
            continue
        cpu_required = max(cpu_required, float(app["cpu_base"]))
        ram_required = max(ram_required, int(app["ram_gb"]))
        ssd_required = max(ssd_required, int(app["ssd_gb"]))
        gpu_required = max(gpu_required, float(app["gpu_need"]))
        vram_required = max(vram_required, int(app.get("vram_gb", 6)))
        if float(app["gpu_need"]) >= 40 or int(app.get("vram_gb", 0)) >= 6:
            dedicated_needed = True

    extra_apps = max(0, len(valid_apps) - 1)
    cpu_required += extra_apps * 8.0
    ram_required += min(extra_apps * 4, 24)
    ssd_required += min(extra_apps * 128, 2000)

    complexity_bonus = _creator_complexity_bonus(project_complexity)
    cpu_required += float(complexity_bonus["cpu"])
    ram_required += int(complexity_bonus["ram"])
    gpu_required += float(complexity_bonus["gpu"])
    ssd_required += int(complexity_bonus["ssd"])
    vram_required += int(complexity_bonus["vram"])

    monitor_bonus = _creator_monitor_bonus(creator_monitors)
    cpu_required += float(monitor_bonus["cpu"])
    ram_required += int(monitor_bonus["ram"])
    gpu_required += float(monitor_bonus["gpu"])

    resolution_bonus = _creator_resolution_bonus(resolution)
    gpu_required += float(resolution_bonus["gpu"])
    vram_required += int(resolution_bonus["vram"])

    if gpu_mode == "integrated":
        dedicated_needed = False
    elif gpu_mode in {"auto", "dedicated"}:
        dedicated_needed = True

    ram_required = max(16, min(256, ram_required))
    available_ram = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})
    target_ram = min(available_ram, key=lambda x: (abs(x - ram_required), x)) if available_ram else ram_required
    available_ssd = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})
    target_ssd = min(available_ssd, key=lambda x: (abs(x - ssd_required), x)) if available_ssd else ssd_required

    return {
        "selected_apps": valid_apps,
        "required_cpu_score": round(cpu_required, 1),
        "required_ram_gb": target_ram,
        "required_ssd_gb": target_ssd,
        "required_gpu_score": round(gpu_required, 1),
        "required_vram_gb": vram_required,
        "requires_dedicated_gpu": dedicated_needed,
        "project_complexity": project_complexity,
        "monitors": creator_monitors,
    }


def _creator_ram_targets(requirement: Dict[str, object], ram_size: str) -> List[int]:
    preferred = _parse_preference_size(ram_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})
    if preferred in available:
        others = [x for x in available if x != preferred]
        return [preferred] + sorted(others, key=lambda x: (abs(x - preferred), x))
    target = int(requirement.get("required_ram_gb", 32))
    return sorted(available, key=lambda x: (0 if x >= target else 1, abs(x - target), x))


def _creator_ssd_targets(requirement: Dict[str, object], ssd_size: str) -> List[int]:
    preferred = _parse_preference_size(ssd_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})
    if preferred in available:
        others = [x for x in available if x != preferred]
        return [preferred] + sorted(others, key=lambda x: (abs(x - preferred), x))
    target = int(requirement.get("required_ssd_gb", 1000))
    return sorted(available, key=lambda x: (0 if x >= target else 1, abs(x - target), x))


def _creator_build_score(parts: Dict[str, Part], budget: int, requirement: Dict[str, object], wifi_required: bool, priority: str) -> float:
    cpu = parts.get("CPU")
    mb = parts.get("Motherboard")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    psu = parts.get("PSU")
    case = parts.get("Case")
    gpu = parts.get("GPU")
    if not cpu or not mb or not ram or not ssd or not psu or not case:
        return -1_000_000
    total = sum(p.price for p in parts.values())
    if total > budget:
        return -1_000_000

    cpu_score = _cpu_game_score(cpu)
    req_cpu = float(requirement.get("required_cpu_score", 1))
    ram_gb = int(ram.meta.get("size_gb", 0))
    req_ram = int(requirement.get("required_ram_gb", 16))
    ssd_gb = int(ssd.meta.get("size_gb", 0))
    req_ssd = int(requirement.get("required_ssd_gb", 512))
    req_gpu = float(requirement.get("required_gpu_score", 1))
    req_vram = int(requirement.get("required_vram_gb", 6))
    graphics_score = _office_gpu_score(gpu) if gpu else _office_igpu_score(cpu)
    vram = int(gpu.meta.get("vram", 0)) if gpu else 0

    score = 0.0
    score += min(cpu_score / max(req_cpu, 1), 1.45) * 34
    score += min(ram_gb / max(req_ram, 1), 1.55) * 24
    score += min(ssd_gb / max(req_ssd, 1), 1.55) * 16
    score += min(graphics_score / max(req_gpu, 1), 1.55) * 20
    score += min(vram / max(req_vram, 1), 1.60) * 16

    if bool(requirement.get("requires_dedicated_gpu", True)) and not gpu:
        score -= 90
    if req_ram >= 64 and ram_gb < 64:
        score -= 18
    if req_ssd >= 2000 and ssd_gb < 2000:
        score -= 14
    if req_vram >= 12 and vram < 12:
        score -= 20

    if wifi_required and mb.meta.get("wifi") is True:
        score += 4
    elif wifi_required:
        score -= 4

    if cpu.meta.get("socket") == "AM5":
        score += 5
    elif cpu.meta.get("socket") == "LGA1700":
        score += 4

    if psu.meta.get("watt", 0) >= _estimate_required_watt(cpu, gpu, "creator"):
        score += 5
    if "Airflow" in case.name or "Premium" in case.name:
        score += 4

    score += _priority_score_adjustment(total, budget, priority)
    return score


def _creator_match_status(parts: Dict[str, Part], requirement: Dict[str, object]) -> str:
    cpu = parts.get("CPU")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    gpu = parts.get("GPU")
    if not cpu or not ram or not ssd or not gpu:
        return "weak"
    cpu_ratio = _cpu_game_score(cpu) / max(float(requirement.get("required_cpu_score", 1)), 1)
    ram_ratio = int(ram.meta.get("size_gb", 0)) / max(int(requirement.get("required_ram_gb", 1)), 1)
    ssd_ratio = int(ssd.meta.get("size_gb", 0)) / max(int(requirement.get("required_ssd_gb", 1)), 1)
    gpu_ratio = _office_gpu_score(gpu) / max(float(requirement.get("required_gpu_score", 1)), 1)
    vram_ratio = int(gpu.meta.get("vram", 0)) / max(int(requirement.get("required_vram_gb", 1)), 1)
    min_ratio = min(cpu_ratio, ram_ratio, ssd_ratio, gpu_ratio, vram_ratio)
    if min_ratio >= 1.08:
        return "excellent"
    if min_ratio >= 1.0:
        return "good"
    if min_ratio >= 0.9:
        return "near"
    return "weak"

__all__ = [name for name in globals() if not name.startswith("__")]

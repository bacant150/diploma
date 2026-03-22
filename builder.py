from typing import Dict, List, Optional
from parts_db import PARTS, Part, GAMES_DB, OFFICE_APPS_DB, STUDY_APPS_DB, CREATOR_APPS_DB


VALID_MB_SOCKETS = {"AM4", "AM5", "LGA1700"}

def _cat(cat: str) -> List[Part]:
    return [p for p in PARTS if p.category == cat]


def _pick_cheapest(cands: List[Part], max_price: int) -> Optional[Part]:
    fits = [p for p in cands if p.price <= max_price]
    if not fits:
        return None
    return min(fits, key=lambda p: p.price)


def _pick_best(cands: List[Part], max_price: int) -> Optional[Part]:
    fits = [p for p in cands if p.price <= max_price]
    if not fits:
        return None
    return max(fits, key=lambda p: p.price)


def _pick_preferred(cands: List[Part], max_price: int, preferred_names: List[str]) -> Optional[Part]:
    fits = [p for p in cands if p.price <= max_price]
    if not fits:
        return None

    name_to_rank = {name: i for i, name in enumerate(preferred_names)}

    def sort_key(p: Part):
        return (name_to_rank.get(p.name, 10_000), -p.price)

    fits.sort(key=sort_key)
    return fits[0]


def _cpu_candidates(
    tiers: List[str],
    require_igpu: bool = False,
    preferred_sockets: Optional[List[str]] = None,
) -> List[Part]:
    cpus = [
        p for p in _cat("cpu")
        if p.meta.get("tier") in tiers and p.meta.get("socket") in VALID_MB_SOCKETS
    ]
    if require_igpu:
        cpus = [p for p in cpus if p.meta.get("igpu") is True]
    if preferred_sockets:
        socket_rank = {s: i for i, s in enumerate(preferred_sockets)}
        cpus.sort(key=lambda p: (socket_rank.get(p.meta.get("socket"), 999), p.price))
    return cpus


def _gpu_candidates(tiers: List[str], min_vram: int = 0) -> List[Part]:
    gpus = [
        p for p in _cat("gpu")
        if p.meta.get("tier") in tiers and p.meta.get("vram", 0) >= min_vram
    ]
    gpus.sort(key=lambda p: p.price)
    return gpus


def _pick_cpu_for_budget(
    budget_slice: int,
    tiers: List[str],
    require_igpu: bool = False,
    preferred_sockets: Optional[List[str]] = None,
) -> Optional[Part]:
    cpus = _cpu_candidates(tiers, require_igpu=require_igpu, preferred_sockets=preferred_sockets)
    return _pick_best(cpus, budget_slice)


def _pick_gpu_for_budget(
    budget_slice: int,
    tiers: List[str],
    min_vram: int = 0,
    preferred_names: Optional[List[str]] = None,
) -> Optional[Part]:
    gpus = _gpu_candidates(tiers, min_vram=min_vram)
    if preferred_names:
        return _pick_preferred(gpus, budget_slice, preferred_names)
    return _pick_best(gpus, budget_slice)


def _pick_motherboard(cpu: Part, wifi: bool, max_price: int, prefer_ddr4: bool = False) -> Optional[Part]:
    mbs = [p for p in _cat("mb") if p.meta.get("socket") == cpu.meta.get("socket")]

    if prefer_ddr4:
        ddr4 = [p for p in mbs if p.meta.get("ram_type") == "DDR4"]
        if ddr4:
            mbs = ddr4

    if wifi:
        wifi_mbs = [p for p in mbs if p.meta.get("wifi") is True]
        return _pick_best(wifi_mbs, max_price) or _pick_best(mbs, max_price)

    return _pick_best(mbs, max_price)


def _pick_ram(ram_type: str, targets: List[int], max_price: int) -> Optional[Part]:
    for size in targets:
        cand = _pick_best(
            [p for p in _cat("ram") if p.meta.get("ram_type") == ram_type and p.meta.get("size_gb") == size],
            max_price,
        )
        if cand:
            return cand
    return None


def _pick_ssd(targets: List[int], max_price: int) -> Optional[Part]:
    for size in targets:
        cand = _pick_best([p for p in _cat("ssd") if p.meta.get("size_gb") == size], max_price)
        if cand:
            return cand
    return None


def _parse_preference_size(value: str) -> Optional[int]:
    if value == "auto":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ram_targets_by_preference(ram_size: str, budget: int, integrated: bool = False) -> List[int]:
    preferred = _parse_preference_size(ram_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ram") if int(p.meta.get("size_gb", 0)) > 0})

    if preferred in available:
        others = [size for size in available if size != preferred]
        return [preferred] + sorted(others, key=lambda size: (abs(size - preferred), size))

    if integrated:
        return [32, 16, 64, 8, 128, 4, 256, 2] if budget >= 24000 else [16, 8, 32, 4, 64, 2, 128, 256]
    if budget >= 120000:
        return [64, 32, 128, 96, 16, 256, 8, 4, 2]
    if budget >= 38000:
        return [32, 16, 64, 128, 8, 256, 4, 2]
    return [16, 8, 32, 4, 64, 2, 128, 256]


def _ssd_targets_by_preference(ssd_size: str, budget: int, integrated: bool = False) -> List[int]:
    preferred = _parse_preference_size(ssd_size)
    available = sorted({int(p.meta.get("size_gb", 0)) for p in _cat("ssd") if int(p.meta.get("size_gb", 0)) > 0})

    if preferred in available:
        others = [size for size in available if size != preferred]
        return [preferred] + sorted(others, key=lambda size: (abs(size - preferred), size))

    if integrated:
        return [1000, 512, 500, 256, 2000, 128, 4000] if budget < 28000 else [2000, 1000, 512, 500, 4000, 256, 128]
    if budget >= 80000:
        return [4000, 2000, 1000, 512, 500, 256, 128]
    if budget >= 45000:
        return [2000, 1000, 512, 500, 4000, 256, 128]
    return [1000, 512, 500, 256, 2000, 128, 4000]


def _motherboard_candidates_for_platform(cpu: Part, wifi: bool, memory_platform: str) -> List[Part]:
    mbs = [p for p in _cat("mb") if p.meta.get("socket") == cpu.meta.get("socket")]

    if memory_platform == "ddr4":
        mbs = [p for p in mbs if p.meta.get("ram_type") == "DDR4"]
    elif memory_platform == "ddr5":
        mbs = [p for p in mbs if p.meta.get("ram_type") == "DDR5"]

    if wifi:
        wifi_mbs = [p for p in mbs if p.meta.get("wifi") is True]
        return wifi_mbs + [p for p in mbs if p not in wifi_mbs]
    return mbs


def _pick_motherboard_for_platform(cpu: Part, wifi: bool, max_price: int, memory_platform: str, prefer_ddr4: bool = False) -> Optional[Part]:
    if memory_platform == "ddr4":
        return _pick_best(_motherboard_candidates_for_platform(cpu, wifi, "ddr4"), max_price)
    if memory_platform == "ddr5":
        return _pick_best(_motherboard_candidates_for_platform(cpu, wifi, "ddr5"), max_price)
    return _pick_motherboard(cpu, wifi=wifi, max_price=max_price, prefer_ddr4=prefer_ddr4)


def _pick_psu(required_watt: int, max_price: int) -> Optional[Part]:
    psus = [p for p in _cat("psu") if p.meta.get("watt", 0) >= required_watt]
    return _pick_cheapest(psus, max_price) or _pick_best(_cat("psu"), max_price)



def _pick_case(max_price: int, premium: bool = False) -> Optional[Part]:
    cases = [p for p in _cat("case") if p.price <= max_price]
    if not cases:
        return None

    def premium_key(p: Part):
        return (
            0 if p.meta.get("showcase") else 1,
            0 if p.meta.get("premium") else 1,
            0 if p.meta.get("airflow") else 1,
            -p.price,
        )

    def standard_key(p: Part):
        return (
            0 if p.meta.get("airflow") else 1,
            0 if p.meta.get("premium") else 1,
            0 if p.meta.get("showcase") else 1,
            p.price,
        )

    fits = sorted(cases, key=premium_key if premium else standard_key)
    return fits[0]


def _estimate_required_watt(cpu: Optional[Part], gpu: Optional[Part], purpose: str) -> int:
    if purpose == "office":
        return 400
    if purpose == "study":
        if gpu and gpu.meta.get("vram", 0) >= 12:
            return 650
        return 500 if gpu else 450
    if purpose == "creator":
        if gpu and gpu.meta.get("vram", 0) >= 24:
            return 1000
        if gpu and gpu.meta.get("vram", 0) >= 20:
            return 850
        if gpu and gpu.meta.get("vram", 0) >= 16:
            return 750
        if gpu and gpu.meta.get("vram", 0) >= 12:
            return 650
        return 550
    if purpose == "gaming":
        if gpu and gpu.meta.get("vram", 0) >= 24:
            return 1000
        if gpu and gpu.meta.get("vram", 0) >= 20:
            return 850
        if gpu and gpu.meta.get("vram", 0) >= 16:
            return 750
        if gpu and gpu.meta.get("vram", 0) >= 12:
            return 650
        return 550
    return 500


def _result(parts: Dict[str, Part], notes: List[str], tier: str, budget: int, meta: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    total = sum(p.price for p in parts.values())
    parts_out = {k: {"name": v.name, "price": v.price} for k, v in parts.items()}
    result = {
        "parts": parts_out,
        "total": total,
        "notes": notes[:3],
        "tier": tier,
    }
    if meta:
        result.update(meta)
    return result


def _fail(message: str, tier: str = "unknown") -> Dict[str, object]:
    return {
        "parts": {},
        "total": 0,
        "notes": [message],
        "tier": tier,
    }


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
    return 2.00


def _calculate_gaming_requirement(
    games: List[str],
    resolution: str,
    graphics_quality: str,
    target_fps: int,
) -> Dict[str, object]:
    """Розраховує мінімальні умовні вимоги до CPU/GPU під вибрані ігри."""
    valid_games = [g for g in games if g in GAMES_DB]

    if not valid_games:
        return {
            "required_gpu_score": 0,
            "required_cpu_score": 0,
            "selected_games": [],
            "is_active": False,
        }

    gpu_mult = _resolution_multiplier(resolution) * _quality_multiplier(graphics_quality) * _fps_multiplier(target_fps)

    cpu_mult = (
        (1.00 if resolution == "1080p" else 1.08 if resolution == "1440p" else 1.15)
        * (0.92 if graphics_quality == "low" else 0.98 if graphics_quality == "medium" else 1.00 if graphics_quality == "high" else 1.04)
        * (1.00 if target_fps <= 60 else 1.12 if target_fps <= 90 else 1.28 if target_fps <= 144 else 1.48)
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


def _cpu_brand_matches(cpu: Part, cpu_brand: str) -> bool:
    if cpu_brand == "auto":
        return True
    name = cpu.name.lower()
    if cpu_brand == "amd":
        return name.startswith("amd")
    if cpu_brand == "intel":
        return name.startswith("intel")
    return True


def _gpu_brand_matches(gpu: Part, gpu_brand: str) -> bool:
    if gpu_brand == "auto":
        return True
    name = gpu.name.lower()
    if gpu_brand == "amd":
        return name.startswith("amd")
    if gpu_brand == "nvidia":
        return name.startswith("nvidia")
    return True



def _igpu_game_score(cpu: Part) -> int:
    meta_score = cpu.meta.get("igpu_game_score")
    if isinstance(meta_score, (int, float)):
        return int(meta_score)

    scores = {
        "AMD Athlon 3000G": 20,
        "AMD Ryzen 5 4600G": 48,
        "AMD Ryzen 5 5600G": 62,
        "AMD Ryzen 7 5700G": 72,
        "AMD Ryzen 5 7600": 46,
        "AMD Ryzen 5 8600G": 112,
        "AMD Ryzen 7 8700G": 138,
        "AMD Ryzen 7 7700": 52,
        "Intel G7400": 14,
        "Intel i3-12100": 24,
        "Intel i3-13100": 28,
        "Intel i5-12400": 32,
        "Intel i5-13400": 36,
        "Intel i5-13600K": 44,
        "Intel i7-13700": 48,
    }
    return scores.get(cpu.name, 18 if cpu.meta.get("igpu") else 0)


def _build_gaming_pc_integrated(
    budget: int,
    resolution: str,
    wifi: bool,
    games: List[str],
    graphics_quality: str,
    target_fps: int,
    cpu_brand: str,
    ram_size: str = "auto",
    ssd_size: str = "auto",
    memory_platform: str = "auto",
) -> Dict[str, object]:
    """Підбирає конфігурацію для офісного сценарію з урахуванням фільтрів користувача."""
    notes: List[str] = []
    tier = "budget" if budget <= 18000 else "mid"
    requirement = _calculate_gaming_requirement(games, resolution, graphics_quality, target_fps)

    cpu_candidates = [
        cpu for cpu in _cpu_candidates(["budget", "mid", "upper"], require_igpu=True, preferred_sockets=["AM5", "LGA1700", "AM4"])
        if _cpu_brand_matches(cpu, cpu_brand)
    ]

    best_config: Optional[Dict[str, Part]] = None
    best_score = -1_000_000.0

    for cpu in cpu_candidates:
        partial: Dict[str, Part] = {"CPU": cpu}
        spent = cpu.price

        mb = _pick_motherboard_for_platform(
            cpu,
            wifi=wifi,
            max_price=min(int(budget * 0.24), budget - spent),
            memory_platform=memory_platform,
            prefer_ddr4=(cpu.meta.get("socket") != "AM5"),
        )
        if not mb:
            mb = _pick_motherboard_for_platform(
                cpu,
                wifi=wifi,
                max_price=budget - spent,
                memory_platform=memory_platform,
                prefer_ddr4=False,
            )
        if not mb:
            continue
        partial["Motherboard"] = mb
        spent = sum(p.price for p in partial.values())

        ram_targets = _ram_targets_by_preference(ram_size, budget, integrated=True)
        ram = _pick_ram(mb.meta.get("ram_type"), ram_targets, min(int(budget * 0.20), budget - spent))
        if not ram:
            ram = _pick_ram(mb.meta.get("ram_type"), ram_targets, budget - spent)
        if not ram:
            continue
        partial["RAM"] = ram
        spent = sum(p.price for p in partial.values())

        ssd_targets = _ssd_targets_by_preference(ssd_size, budget, integrated=True)
        ssd = _pick_ssd(ssd_targets, min(int(budget * 0.16), budget - spent))
        if not ssd:
            ssd = _pick_ssd(ssd_targets, budget - spent)
        if not ssd:
            continue
        partial["SSD"] = ssd
        spent = sum(p.price for p in partial.values())

        psu = _pick_psu(_estimate_required_watt(cpu, None, "study"), min(int(budget * 0.12), budget - spent))
        if not psu:
            psu = _pick_psu(450, budget - spent)
        if not psu:
            continue
        partial["PSU"] = psu
        spent = sum(p.price for p in partial.values())

        case = _pick_case(budget - spent, premium=False)
        if not case:
            continue
        partial["Case"] = case

        total = sum(p.price for p in partial.values())
        if total > budget:
            continue

        igpu_score = _igpu_game_score(cpu)
        cpu_score = _cpu_game_score(cpu)
        ram_bonus = 6 if ram.meta.get("size_gb", 0) >= 32 else 0
        score = igpu_score * 1.5 + cpu_score * 0.35 + ram_bonus
        if resolution == "1440p":
            score -= 30
        elif resolution == "4k":
            score -= 80
        if graphics_quality == "ultra":
            score -= 35
        elif graphics_quality == "high":
            score -= 15
        if target_fps > 120:
            score -= 25
        elif target_fps > 60:
            score -= 10

        if requirement.get("is_active"):
            required_gpu = float(requirement.get("required_gpu_score", 0))
            gpu_ratio = igpu_score / max(required_gpu, 1)
            if gpu_ratio < 0.55:
                score -= 120
            elif gpu_ratio < 0.75:
                score -= 50
            else:
                score += 8

        if score > best_score:
            best_score = score
            best_config = partial.copy()

    if not best_config:
        return _fail("Не вдалося зібрати ігровий ПК без дискретної відеокарти в межах бюджету.", tier)

    total = sum(p.price for p in best_config.values())
    cpu = best_config["CPU"]
    match_info = {
        "match_status": "integrated",
        "gpu_ratio": round(_igpu_game_score(cpu) / max(float(requirement.get("required_gpu_score", 1)) or 1, 1), 2) if requirement.get("is_active") else None,
        "cpu_ratio": round(_cpu_game_score(cpu) / max(float(requirement.get("required_cpu_score", 1)) or 1, 1), 2) if requirement.get("is_active") else None,
        "match_note": "Збірка без дискретної відеокарти найкраще підходить для невибагливих ігор, esports-проєктів або дуже обмеженого бюджету.",
    }
    notes.append(_gaming_target_label(requirement, graphics_quality, target_fps, resolution))
    notes.append(match_info["match_note"])
    notes.append(_budget_summary_note(total, budget))
    return _result(best_config, notes, tier, budget, meta={"game_requirement": requirement, "match_info": match_info})


# ===== Пріоритет підбору =====


def _priority_label(priority: str) -> str:
    return {
        "auto": "автоматичний підбір",
        "balanced": "збалансований режим (ціна/якість)",
        "best": "режим максимально найкращої конфігурації",
    }.get(priority, "автоматичний підбір")


def _priority_score_adjustment(total: int, budget: int, priority: str) -> float:
    usage = total / max(budget, 1)
    left = budget - total
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
    if priority == "balanced":
        return "Пріоритет підбору: збалансовано (ціна/якість)."
    if priority == "best":
        return "Пріоритет підбору: максимально найкращий варіант у межах бюджету."
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
        app = STUDY_APPS_DB[app_key]
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


def build_office_pc(
    budget: int,
    wifi: bool,
    office_apps: Optional[List[str]] = None,
    office_tabs: str = "auto",
    office_monitors: str = "auto",
    gpu_mode: str = "auto",
    cpu_brand: str = "auto",
    ram_size: str = "auto",
    ssd_size: str = "auto",
    memory_platform: str = "auto",
    priority: str = "auto",
) -> Dict[str, object]:
    notes: List[str] = []
    tier = "budget" if budget <= 18000 else "mid" if budget <= 36000 else "upper"
    requirement = _calculate_office_requirement(office_apps or [], office_tabs, office_monitors, gpu_mode)
    cpu_candidates = [
        c for c in _cpu_candidates(["budget", "mid", "upper"], require_igpu=(gpu_mode != "dedicated"), preferred_sockets=["LGA1700", "AM5", "AM4"])
        if _cpu_brand_matches(c, cpu_brand)
    ]
    if not cpu_candidates:
        return _fail("Не вдалося підібрати процесор для офісного ПК за заданими параметрами.", tier)
    dedicated_allowed = gpu_mode != "integrated"
    dedicated_required = bool(requirement.get("requires_dedicated_gpu", False)) and dedicated_allowed
    gpu_pool = [g for g in _gpu_candidates(["budget", "mid"], min_vram=4) if (gpu_mode == "dedicated" or float(requirement.get("required_gpu_score", 0)) >= 35 or office_monitors == "3_plus")]
    best_config: Optional[Dict[str, Part]] = None
    best_score = -1_000_000.0
    gpu_options: List[Optional[Part]] = [None]
    if dedicated_allowed and (dedicated_required or budget >= 26000):
        gpu_options += gpu_pool
    for cpu in cpu_candidates:
        if gpu_mode == "integrated" and cpu.meta.get("igpu") is not True:
            continue
        for gpu in gpu_options:
            if gpu_mode == "dedicated" and gpu is None:
                continue
            if gpu is None and not _office_can_use_igpu(requirement, cpu):
                continue
            partial: Dict[str, Part] = {"CPU": cpu}
            if gpu:
                partial["GPU"] = gpu
            spent = sum(p.price for p in partial.values())
            if spent > int(budget * 0.72):
                continue
            mb_budget = min(int(budget * 0.20), budget - spent)
            if mb_budget <= 0:
                continue
            prefer_ddr4 = memory_platform != "ddr5" and budget < 32000
            mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=mb_budget, memory_platform=memory_platform, prefer_ddr4=prefer_ddr4)
            if not mb:
                mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=budget - spent, memory_platform=memory_platform, prefer_ddr4=False)
            if not mb:
                continue
            partial["Motherboard"] = mb
            spent = sum(p.price for p in partial.values())
            ram = _pick_ram(mb.meta.get("ram_type"), _office_ram_targets(requirement, ram_size), min(int(budget * 0.18), budget - spent)) or _pick_ram(mb.meta.get("ram_type"), _office_ram_targets(requirement, ram_size), budget - spent)
            if not ram:
                continue
            partial["RAM"] = ram
            spent = sum(p.price for p in partial.values())
            ssd = _pick_ssd(_office_ssd_targets(requirement, ssd_size), min(int(budget * 0.16), budget - spent)) or _pick_ssd(_office_ssd_targets(requirement, ssd_size), budget - spent)
            if not ssd:
                continue
            partial["SSD"] = ssd
            spent = sum(p.price for p in partial.values())
            psu_purpose = "study" if gpu else "office"
            psu = _pick_psu(_estimate_required_watt(cpu, gpu, psu_purpose), min(int(budget * 0.12), budget - spent)) or _pick_psu(_estimate_required_watt(cpu, gpu, psu_purpose), budget - spent)
            if not psu:
                continue
            partial["PSU"] = psu
            spent = sum(p.price for p in partial.values())
            case = _pick_case(budget - spent, premium=bool(gpu and gpu.price >= 10000))
            if not case:
                continue
            partial["Case"] = case
            total = sum(p.price for p in partial.values())
            score = _office_build_score(partial, budget, requirement, wifi_required=wifi)
            score += _priority_score_adjustment(total, budget, priority)
            if gpu_mode == "dedicated" and gpu:
                score += 4
            if gpu_mode == "integrated" and gpu is None:
                score += 4
            if cpu_brand != "auto":
                score += 2
            if score > best_score:
                best_score = score
                best_config = partial.copy()
    if not best_config:
        return _fail("Не вдалося зібрати офісний ПК за заданими параметрами.", tier)
    total = sum(p.price for p in best_config.values())
    selected_titles = [OFFICE_APPS_DB[a]["title"] for a in requirement["selected_apps"]]
    match_status = _office_match_status(best_config, requirement)
    if match_status == "excellent":
        first_note = "Конфігурація з запасом підходить для вибраних офісних сценаріїв і багатозадачності."
    elif match_status == "good":
        first_note = "Конфігурація добре підходить для вибраних офісних програм і щоденної роботи."
    elif match_status == "near":
        first_note = "Конфігурація загалом підходить, але для найважчих офісних сценаріїв запас буде помірним."
    else:
        first_note = "Конфігурація є найкращим варіантом у межах бюджету, але для частини важких офісних задач може бути на межі."
    tabs_label = {"auto": "авто", "up_to_10": "до 10", "10_30": "10-30", "30_60": "30-60", "60_plus": "60+"}.get(office_tabs, office_tabs)
    monitors_label = {"auto": "авто", "1": "1", "2": "2", "3_plus": "3+"}.get(office_monitors, office_monitors)
    graphics_note = "без дискретної відеокарти" if "GPU" not in best_config else "з дискретною відеокартою"
    notes.extend([
        first_note,
        f"Сценарій підбору: {', '.join(selected_titles)}; вкладки — {tabs_label}; монітори — {monitors_label}; збірка сформована {graphics_note}.",
        _priority_note(priority),
        _budget_summary_note(total, budget),
    ])
    return _result(best_config, notes, tier, budget, meta={"office_requirement": requirement})


def build_study_pc(
    budget: int,
    wifi: bool,
    study_apps: Optional[List[str]] = None,
    study_tabs: str = "auto",
    study_monitors: str = "auto",
    gpu_mode: str = "auto",
    cpu_brand: str = "auto",
    ram_size: str = "auto",
    ssd_size: str = "auto",
    memory_platform: str = "auto",
    priority: str = "auto",
) -> Dict[str, object]:
    """Підбирає ПК для навчання, програмування й повсякденних задач."""
    notes: List[str] = []
    tier = "budget" if budget <= 18000 else "mid" if budget <= 36000 else "upper"
    requirement = _calculate_study_requirement(study_apps or [], study_tabs, study_monitors, gpu_mode)
    cpu_candidates = [
        c for c in _cpu_candidates(["budget", "mid", "upper"], require_igpu=(gpu_mode != "dedicated"), preferred_sockets=["LGA1700", "AM5", "AM4"])
        if _cpu_brand_matches(c, cpu_brand)
    ]
    if not cpu_candidates:
        return _fail("Не вдалося підібрати процесор для ПК для навчання.", tier)
    dedicated_allowed = gpu_mode != "integrated"
    dedicated_required = bool(requirement.get("requires_dedicated_gpu", False)) and dedicated_allowed
    gpu_pool = [g for g in _gpu_candidates(["budget", "mid"], min_vram=4) if (gpu_mode == "dedicated" or float(requirement.get("required_gpu_score", 0)) >= 30 or study_monitors == "3_plus")]
    best_config: Optional[Dict[str, Part]] = None
    best_score = -1_000_000.0
    gpu_options: List[Optional[Part]] = [None]
    if dedicated_allowed and (dedicated_required or budget >= 26000):
        gpu_options += gpu_pool
    for cpu in cpu_candidates:
        if gpu_mode == "integrated" and cpu.meta.get("igpu") is not True:
            continue
        for gpu in gpu_options:
            if gpu_mode == "dedicated" and gpu is None:
                continue
            if gpu is None and not _study_can_use_igpu(requirement, cpu):
                continue
            partial: Dict[str, Part] = {"CPU": cpu}
            if gpu:
                partial["GPU"] = gpu
            spent = sum(p.price for p in partial.values())
            if spent > int(budget * 0.72):
                continue
            mb_budget = min(int(budget * 0.20), budget - spent)
            if mb_budget <= 0:
                continue
            prefer_ddr4 = memory_platform != "ddr5" and budget < 32000
            mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=mb_budget, memory_platform=memory_platform, prefer_ddr4=prefer_ddr4)
            if not mb:
                mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=budget - spent, memory_platform=memory_platform, prefer_ddr4=False)
            if not mb:
                continue
            partial["Motherboard"] = mb
            spent = sum(p.price for p in partial.values())
            ram = _pick_ram(mb.meta.get("ram_type"), _study_ram_targets(requirement, ram_size), min(int(budget * 0.18), budget - spent)) or _pick_ram(mb.meta.get("ram_type"), _study_ram_targets(requirement, ram_size), budget - spent)
            if not ram:
                continue
            partial["RAM"] = ram
            spent = sum(p.price for p in partial.values())
            ssd = _pick_ssd(_study_ssd_targets(requirement, ssd_size), min(int(budget * 0.16), budget - spent)) or _pick_ssd(_study_ssd_targets(requirement, ssd_size), budget - spent)
            if not ssd:
                continue
            partial["SSD"] = ssd
            spent = sum(p.price for p in partial.values())
            psu_purpose = "study" if gpu else "office"
            psu = _pick_psu(_estimate_required_watt(cpu, gpu, psu_purpose), min(int(budget * 0.12), budget - spent)) or _pick_psu(_estimate_required_watt(cpu, gpu, psu_purpose), budget - spent)
            if not psu:
                continue
            partial["PSU"] = psu
            spent = sum(p.price for p in partial.values())
            case = _pick_case(budget - spent, premium=bool(gpu and gpu.price >= 10000))
            if not case:
                continue
            partial["Case"] = case
            total = sum(p.price for p in partial.values())
            score = _study_build_score(partial, budget, requirement, wifi_required=wifi)
            score += _priority_score_adjustment(total, budget, priority)
            if gpu_mode == "dedicated" and gpu:
                score += 4
            if gpu_mode == "integrated" and gpu is None:
                score += 4
            if cpu_brand != "auto":
                score += 2
            if score > best_score:
                best_score = score
                best_config = partial.copy()
    if not best_config:
        return _fail("Не вдалося зібрати ПК для навчання за заданими параметрами.", tier)
    total = sum(p.price for p in best_config.values())
    selected_titles = [STUDY_APPS_DB[a]["title"] for a in requirement["selected_apps"]]
    match_status = _study_match_status(best_config, requirement)
    if match_status == "excellent":
        first_note = "Конфігурація з запасом підходить для вибраних навчальних сценаріїв."
    elif match_status == "good":
        first_note = "Конфігурація добре підходить для навчання, програмування та повсякденних задач."
    elif match_status == "near":
        first_note = "Конфігурація загалом підходить, але для найважчих навчальних сценаріїв запас буде помірним."
    else:
        first_note = "Конфігурація є найкращим варіантом у межах бюджету, але для частини важких задач може бути на межі."
    tabs_label = {"auto": "авто", "up_to_10": "до 10", "10_30": "10-30", "30_60": "30-60", "60_plus": "60+"}.get(study_tabs, study_tabs)
    monitors_label = {"auto": "авто", "1": "1", "2": "2", "3_plus": "3+"}.get(study_monitors, study_monitors)
    graphics_note = "без дискретної відеокарти" if "GPU" not in best_config else "з дискретною відеокартою"
    notes.extend([
        first_note,
        f"Сценарій підбору: {', '.join(selected_titles)}; вкладки — {tabs_label}; монітори — {monitors_label}; збірка сформована {graphics_note}.",
        _priority_note(priority),
        _budget_summary_note(total, budget),
    ])
    return _result(best_config, notes, tier, budget, meta={"study_requirement": requirement})


def build_gaming_pc(
    budget: int,
    resolution: str,
    wifi: bool,
    games: List[str],
    graphics_quality: str,
    target_fps: int,
    gpu_mode: str = "auto",
    cpu_brand: str = "auto",
    gpu_brand: str = "auto",
    ram_size: str = "auto",
    ssd_size: str = "auto",
    memory_platform: str = "auto",
    priority: str = "auto",
) -> Dict[str, object]:
    """Підбирає ігрову конфігурацію з урахуванням цілі FPS, роздільної здатності та брендів."""
    if budget < 12500:
        return _fail("Замалий бюджет для ігрового ПК.", "budget")
    if gpu_mode == "integrated" and gpu_brand != "auto":
        gpu_brand = "auto"
    if memory_platform == "ddr4" and resolution == "4k" and budget >= 90000:
        memory_platform = "auto"
    requirement = _calculate_gaming_requirement(games, resolution, graphics_quality, target_fps)
    def dedicated_build() -> Dict[str, object]:
        notes: List[str] = []
        tier = "budget" if budget <= 20000 else "mid" if budget <= 45000 else "upper"
        min_vram = 8 if resolution in ("1080p", "1440p") else 12
        if gpu_mode == "dedicated" and budget < 16000:
            return _fail("Для ігрового ПК з дискретною відеокартою потрібен трохи більший бюджет.", "budget")
        if resolution == "1080p":
            gpu_tiers = ["budget", "mid", "upper"]
            max_gpu_share = 0.55 if budget < 90000 else 0.62
            cpu_tiers = ["budget", "mid", "upper"]
        elif resolution == "1440p":
            gpu_tiers = ["mid", "upper"]
            max_gpu_share = 0.62
            cpu_tiers = ["mid", "upper"]
        else:
            gpu_tiers = ["upper"]
            max_gpu_share = 0.72
            cpu_tiers = ["upper"]
        gpu_candidates = [g for g in _gpu_candidates(gpu_tiers, min_vram=min_vram) if g.price <= int(budget * max_gpu_share) and _gpu_brand_matches(g, gpu_brand)]
        cpu_candidates = [c for c in _cpu_candidates(cpu_tiers, require_igpu=False, preferred_sockets=["AM5", "LGA1700", "AM4"]) if _cpu_brand_matches(c, cpu_brand)]
        if not gpu_candidates:
            return _fail("Не вдалося підібрати відеокарту за заданими фільтрами.", tier)
        if not cpu_candidates:
            return _fail("Не вдалося підібрати процесор за заданими фільтрами.", tier)
        best_exact_config: Optional[Dict[str, Part]] = None
        best_exact_score = -1_000_000.0
        best_fallback_config: Optional[Dict[str, Part]] = None
        best_fallback_score = -1_000_000.0
        for gpu in gpu_candidates:
            for cpu in cpu_candidates:
                gpu_score = _gpu_game_score(gpu)
                cpu_score = _cpu_game_score(cpu)
                if resolution == "1080p" and cpu_score < gpu_score * 0.55:
                    continue
                if resolution == "1440p" and cpu_score < gpu_score * 0.48:
                    continue
                if resolution == "4k" and cpu_score < gpu_score * 0.38:
                    continue
                partial: Dict[str, Part] = {"GPU": gpu, "CPU": cpu}
                spent = gpu.price + cpu.price
                if spent > int(budget * 0.84):
                    continue
                mb_budget = min(int(budget * 0.18), budget - spent)
                if mb_budget <= 0:
                    continue
                prefer_ddr4 = (cpu.meta.get("socket") != "AM5") and budget < 42000
                mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=mb_budget, memory_platform=memory_platform, prefer_ddr4=prefer_ddr4)
                if not mb and cpu.meta.get("socket") != "AM5":
                    mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=budget - spent, memory_platform=memory_platform, prefer_ddr4=False)
                if not mb:
                    continue
                partial["Motherboard"] = mb
                spent = sum(p.price for p in partial.values())
                ram_targets = _ram_targets_by_preference(ram_size, budget, integrated=False)
                ram = _pick_ram(mb.meta.get("ram_type"), ram_targets, min(int(budget * 0.16), budget - spent)) or _pick_ram(mb.meta.get("ram_type"), ram_targets, budget - spent)
                if not ram:
                    continue
                partial["RAM"] = ram
                spent = sum(p.price for p in partial.values())
                ssd_targets = _ssd_targets_by_preference(ssd_size, budget, integrated=False)
                ssd = _pick_ssd(ssd_targets, min(int(budget * 0.13), budget - spent)) or _pick_ssd(ssd_targets, budget - spent)
                if not ssd:
                    continue
                partial["SSD"] = ssd
                spent = sum(p.price for p in partial.values())
                psu = _pick_psu(_estimate_required_watt(cpu, gpu, "gaming"), min(int(budget * 0.11), budget - spent)) or _pick_psu(_estimate_required_watt(cpu, gpu, "gaming"), budget - spent)
                if not psu:
                    continue
                partial["PSU"] = psu
                spent = sum(p.price for p in partial.values())
                case = _pick_case(budget - spent, premium=(gpu.price >= 18000 or budget >= 60000))
                if not case:
                    continue
                partial["Case"] = case
                total = sum(p.price for p in partial.values())
                if total > budget:
                    continue
                score = _gaming_build_score(partial, resolution, budget, wifi_required=wifi, requirement=requirement)
                score += _priority_score_adjustment(total, budget, priority)
                if cpu_brand != "auto":
                    score += 3
                if gpu_brand != "auto":
                    score += 3
                match_info = _evaluate_requirement_match(partial, requirement)
                if score > best_fallback_score:
                    best_fallback_score = score
                    best_fallback_config = partial.copy()
                if match_info.get("match_status") in {"excellent", "good", "near"} and score > best_exact_score:
                    best_exact_score = score
                    best_exact_config = partial.copy()
        chosen_config = best_exact_config or best_fallback_config
        if not chosen_config:
            return _fail("Не вдалося зібрати ігровий ПК за заданими параметрами.", tier)
        total = sum(p.price for p in chosen_config.values())
        match_info = _evaluate_requirement_match(chosen_config, requirement)
        notes.append(_gaming_target_label(requirement, graphics_quality, target_fps, resolution))
        notes.append(match_info["match_note"] if requirement["is_active"] else _gaming_performance_label(chosen_config, resolution))
        notes.append(_priority_note(priority))
        notes.append(_budget_summary_note(total, budget))
        return _result(chosen_config, notes, tier, budget, meta={"game_requirement": requirement, "match_info": match_info})
    if gpu_mode == "dedicated":
        return dedicated_build()
    if gpu_mode == "integrated":
        integrated = _build_gaming_pc_integrated(budget, resolution, wifi, games, graphics_quality, target_fps, cpu_brand, ram_size, ssd_size, memory_platform)
        if integrated.get("parts"):
            integrated.setdefault("notes", [])
            integrated["notes"] = integrated.get("notes", [])[:2] + [_priority_note(priority), integrated.get("notes", [""])[-1]]
        return integrated
    dedicated = dedicated_build()
    integrated = _build_gaming_pc_integrated(budget, resolution, wifi, games, graphics_quality, target_fps, cpu_brand, ram_size, ssd_size, memory_platform)
    if dedicated.get("parts") and integrated.get("parts"):
        dedicated_gpu = dedicated["parts"].get("GPU")
        if requirement.get("is_active"):
            d_status = dedicated.get("match_info", {}).get("match_status")
            if d_status in {"excellent", "good", "near"}:
                return dedicated
        if dedicated_gpu:
            return dedicated
        return integrated
    return dedicated if dedicated.get("parts") else integrated


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
        app = CREATOR_APPS_DB[app_key]
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


def build_creator_pc(
    budget: int,
    resolution: str,
    wifi: bool,
    creator_apps: Optional[List[str]] = None,
    creator_project_complexity: str = "auto",
    creator_monitors: str = "auto",
    gpu_mode: str = "auto",
    cpu_brand: str = "auto",
    gpu_brand: str = "auto",
    ram_size: str = "auto",
    ssd_size: str = "auto",
    memory_platform: str = "auto",
    priority: str = "auto",
) -> Dict[str, object]:
    """Підбирає конфігурацію для монтажу, 3D і творчих професійних застосунків."""
    notes: List[str] = []
    tier = "mid" if budget <= 32000 else "upper"
    requirement = _calculate_creator_requirement(creator_apps or [], creator_project_complexity, creator_monitors, resolution, gpu_mode)

    cpu_candidates = [
        c for c in _cpu_candidates(["mid", "upper"], require_igpu=False, preferred_sockets=["LGA1700", "AM5", "AM4"])
        if _cpu_brand_matches(c, cpu_brand)
    ]
    if not cpu_candidates:
        return _fail("Не вдалося підібрати процесор для ПК монтажу / 3D.", tier)

    gpu_candidates = [
        g for g in _gpu_candidates(["mid", "upper"], min_vram=int(requirement.get("required_vram_gb", 6)))
        if _gpu_brand_matches(g, gpu_brand)
    ]
    if gpu_mode == "integrated":
        return _fail("Для ПК монтажу / 3D потрібна дискретна відеокарта.", tier)
    if not gpu_candidates:
        return _fail("Не вдалося підібрати відеокарту для ПК монтажу / 3D.", tier)

    best_config: Optional[Dict[str, Part]] = None
    best_score = -1_000_000.0

    for gpu in gpu_candidates:
        for cpu in cpu_candidates:
            partial: Dict[str, Part] = {"GPU": gpu, "CPU": cpu}
            spent = sum(p.price for p in partial.values())
            if spent > int(budget * 0.84):
                continue

            mb_budget = min(int(budget * 0.18), budget - spent)
            if mb_budget <= 0:
                continue
            prefer_ddr4 = memory_platform != "ddr5" and budget < 42000 and cpu.meta.get("socket") != "AM5"
            mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=mb_budget, memory_platform=memory_platform, prefer_ddr4=prefer_ddr4)
            if not mb:
                mb = _pick_motherboard_for_platform(cpu, wifi=wifi, max_price=budget - spent, memory_platform=memory_platform, prefer_ddr4=False)
            if not mb:
                continue
            partial["Motherboard"] = mb
            spent = sum(p.price for p in partial.values())

            ram = _pick_ram(mb.meta.get("ram_type"), _creator_ram_targets(requirement, ram_size), min(int(budget * 0.18), budget - spent)) or _pick_ram(mb.meta.get("ram_type"), _creator_ram_targets(requirement, ram_size), budget - spent)
            if not ram:
                continue
            partial["RAM"] = ram
            spent = sum(p.price for p in partial.values())

            ssd = _pick_ssd(_creator_ssd_targets(requirement, ssd_size), min(int(budget * 0.14), budget - spent)) or _pick_ssd(_creator_ssd_targets(requirement, ssd_size), budget - spent)
            if not ssd:
                continue
            partial["SSD"] = ssd
            spent = sum(p.price for p in partial.values())

            psu = _pick_psu(_estimate_required_watt(cpu, gpu, "creator"), min(int(budget * 0.11), budget - spent)) or _pick_psu(_estimate_required_watt(cpu, gpu, "creator"), budget - spent)
            if not psu:
                continue
            partial["PSU"] = psu
            spent = sum(p.price for p in partial.values())

            case = _pick_case(budget - spent, premium=True)
            if not case:
                continue
            partial["Case"] = case

            total = sum(p.price for p in partial.values())
            score = _creator_build_score(partial, budget, requirement, wifi_required=wifi, priority=priority)
            if cpu_brand != "auto":
                score += 2
            if gpu_brand != "auto":
                score += 2
            if score > best_score:
                best_score = score
                best_config = partial.copy()

    if not best_config:
        return _fail("Не вдалося зібрати ПК монтажу / 3D за заданими параметрами.", tier)

    total = sum(p.price for p in best_config.values())
    selected_titles = [CREATOR_APPS_DB[a]["title"] for a in requirement["selected_apps"]]
    match_status = _creator_match_status(best_config, requirement)
    if match_status == "excellent":
        first_note = "Конфігурація з запасом підходить для монтажу, 3D та важких творчих проєктів."
    elif match_status == "good":
        first_note = "Конфігурація добре підходить для монтажу, рендерингу та роботи з 3D."
    elif match_status == "near":
        first_note = "Конфігурація загалом підходить, але для найважчих проєктів запас буде помірним."
    else:
        first_note = "Конфігурація є найкращим варіантом у межах бюджету, але для частини важких 3D/монтажних задач може бути на межі."

    complexity_label = _creator_complexity_label(creator_project_complexity)
    monitors_label = {"auto": "авто", "1": "1", "2": "2", "3_plus": "3+"}.get(creator_monitors, creator_monitors)
    notes.extend([
        first_note,
        f"Сценарій підбору: {', '.join(selected_titles)}; складність проєктів — {complexity_label}; монітори — {monitors_label}; цільова роздільна здатність — {resolution}.",
        _priority_note(priority),
        _budget_summary_note(total, budget),
    ])
    return _result(best_config, notes, tier, budget, meta={"creator_requirement": requirement})


def _find_part_by_name(name: str) -> Optional[Part]:
    """Повертає першу комплектуючу з бази за точною назвою."""
    for part in PARTS:
        if part.name == name:
            return part
    return None


def _rebuild_parts_from_result(result: Dict[str, object]) -> Dict[str, Part]:
    """Відновлює словник комплектуючих у форматі {role: Part} з результату шаблону."""
    rebuilt: Dict[str, Part] = {}
    raw_parts = result.get("parts", {})
    if not isinstance(raw_parts, dict):
        return rebuilt

    for role, part_data in raw_parts.items():
        if not isinstance(part_data, dict):
            continue
        name = str(part_data.get("name", ""))
        part = _find_part_by_name(name)
        if part:
            rebuilt[str(role)] = part
    return rebuilt


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
        return _fail("Бюджет занадто малий для збирання ПК.", "budget")
    if purpose == "gaming":
        return build_gaming_pc(budget, resolution, wifi, games or [], graphics_quality, target_fps, gpu_mode, cpu_brand, gpu_brand, ram_size, ssd_size, memory_platform, priority)
    if purpose == "office":
        return build_office_pc(budget, wifi, office_apps or [], office_tabs, office_monitors, gpu_mode, cpu_brand, ram_size, ssd_size, memory_platform, priority)
    if purpose == "study":
        return build_study_pc(budget, wifi, study_apps or [], study_tabs, study_monitors, gpu_mode, cpu_brand, ram_size, ssd_size, memory_platform, priority)
    if purpose == "creator":
        return build_creator_pc(budget, resolution, wifi, creator_apps or [], creator_project_complexity, creator_monitors, gpu_mode, cpu_brand, gpu_brand, ram_size, ssd_size, memory_platform, priority)
    return _fail("Невідоме призначення ПК.", "unknown")

from __future__ import annotations

from typing import Dict, List, Optional

from .common import *  # noqa: F401,F403
from .scoring import *  # noqa: F401,F403

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
    """Підбирає ігрову конфігурацію на вбудованій графіці для дуже обмеженого бюджету."""
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
    selected_titles = []
    for a in requirement["selected_apps"]:
        app = STUDY_APPS_DB.get(a) or OFFICE_APPS_DB.get(a)
        if app:
            selected_titles.append(app.get("title", a))
        else:
            selected_titles.append(a)
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
                required_watt = _estimate_required_watt(cpu, gpu, "gaming")
                psu = _pick_psu(required_watt, min(int(budget * 0.11), budget - spent)) or _pick_psu(required_watt, budget - spent)
                if not _psu_is_safe(psu, required_watt):
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

            required_watt = _estimate_required_watt(cpu, gpu, "creator")
            psu = _pick_psu(required_watt, min(int(budget * 0.11), budget - spent)) or _pick_psu(required_watt, budget - spent)
            if not _psu_is_safe(psu, required_watt):
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
    selected_titles = []

    for a in requirement["selected_apps"]:
        app = CREATOR_APPS_DB.get(a) or OFFICE_APPS_DB.get(a)
        if app:
            selected_titles.append(app.get("title", a))
        else:
            selected_titles.append(a)
            
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

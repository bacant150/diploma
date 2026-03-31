from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from parts_db import PARTS, Part, GAMES_DB, OFFICE_APPS_DB

try:
    from parts_db import STUDY_APPS_DB  # type: ignore
except ImportError:
    STUDY_APPS_DB = {}

try:
    from parts_db import CREATOR_APPS_DB  # type: ignore
except ImportError:
    CREATOR_APPS_DB = {}


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

__all__ = [name for name in globals() if not name.startswith("__")]

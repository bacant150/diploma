from __future__ import annotations

import logging
from typing import Any

from parts_db import Part

logger = logging.getLogger("pcbuilder.builder.postprocess")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _append_unique(items: list[str], message: str) -> None:
    text = str(message or "").strip()
    if text and text not in items:
        items.append(text)


def _guess_motherboard_form_factor(motherboard: Part | None) -> str:
    if motherboard is None:
        return "unknown"
    raw = f"{motherboard.name} {motherboard.meta.get('form_factor', '')}".upper()
    if "E-ATX" in raw or "EATX" in raw:
        return "E-ATX"
    if "MATX" in raw or "M-ATX" in raw or "MICRO ATX" in raw:
        return "mATX"
    if "ATX" in raw:
        return "ATX"
    return "unknown"


def _case_supports_board(case_size: str, board_size: str) -> bool:
    case_norm = str(case_size or "").upper()
    board_norm = str(board_size or "").upper()
    if not case_norm or not board_norm or board_norm == "UNKNOWN":
        return True
    if case_norm == "E-ATX":
        return True
    if case_norm == "ATX":
        return board_norm in {"ATX", "MATX", "M-ATX", "MАТX"}
    if case_norm in {"MATX", "M-ATX", "MАТX"}:
        return board_norm in {"MATX", "M-ATX", "MАТX"}
    return True


def _estimate_cpu_power(cpu: Part | None) -> int:
    if cpu is None:
        return 0
    name = cpu.name.upper()
    if "RYZEN 9" in name or "I9" in name:
        return 170
    if "RYZEN 7" in name or "I7" in name:
        return 125
    if "RYZEN 5" in name or "I5" in name:
        return 95
    if "RYZEN 3" in name or "I3" in name:
        return 65
    return 65


def _estimate_gpu_power(gpu: Part | None) -> int:
    if gpu is None:
        return 0
    name = gpu.name.upper()
    heuristics: list[tuple[str, int]] = [
        ("4090", 450),
        ("5080", 360),
        ("4080", 320),
        ("5070 TI", 300),
        ("4070 TI", 285),
        ("7900 XTX", 355),
        ("7900 XT", 315),
        ("9070 XT", 315),
        ("9070", 260),
        ("7900 GRE", 260),
        ("7800 XT", 265),
        ("7700 XT", 245),
        ("5070", 250),
        ("4070 SUPER", 235),
        ("4070", 220),
        ("4060 TI", 180),
        ("5060 TI", 180),
        ("9060 XT", 180),
        ("4060", 140),
        ("5060", 145),
        ("3060 TI", 200),
        ("3060", 170),
        ("3050", 130),
        ("6750 XT", 250),
        ("6700 XT", 230),
        ("6650 XT", 180),
        ("6600 XT", 165),
        ("6600", 140),
        ("7600", 165),
        ("6500 XT", 110),
        ("ARC B580", 190),
        ("ARC B570", 165),
        ("ARC A580", 175),
        ("1660 SUPER", 125),
        ("2060", 160),
        ("1650", 75),
        ("580 8GB", 185),
        ("570 4GB", 150),
        ("1050 TI", 75),
    ]
    for needle, watt in heuristics:
        if needle in name:
            return watt
    return 160


def _estimate_required_watt(cpu: Part | None, gpu: Part | None, purpose: str) -> int:
    overhead = 120
    if purpose == "creator":
        overhead = 140
    elif purpose == "gaming":
        overhead = 130
    return _estimate_cpu_power(cpu) + _estimate_gpu_power(gpu) + overhead


def _compatibility_record(code: str, status: str, message: str) -> dict[str, str]:
    return {"code": code, "status": status, "message": message}


def evaluate_build_compatibility(
    parts: dict[str, Part],
    purpose: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    errors: list[str] = []
    warnings: list[str] = []

    cpu = parts.get("CPU")
    gpu = parts.get("GPU")
    motherboard = parts.get("Motherboard")
    ram = parts.get("RAM")
    ssd = parts.get("SSD")
    psu = parts.get("PSU")
    case = parts.get("Case")

    cpu_socket = str(cpu.meta.get("socket", "")).strip() if cpu else ""
    mb_socket = str(motherboard.meta.get("socket", "")).strip() if motherboard else ""
    if cpu and motherboard:
        if cpu_socket and mb_socket and cpu_socket == mb_socket:
            checks.append(
                _compatibility_record(
                    "cpu_socket",
                    "ok",
                    f"Процесор і материнська плата сумісні за сокетом {cpu_socket}.",
                )
            )
        else:
            message = (
                f"Несумісний сокет: процесор {cpu_socket or 'невідомий'}, "
                f"материнська плата {mb_socket or 'невідомий'}."
            )
            checks.append(_compatibility_record("cpu_socket", "error", message))
            _append_unique(errors, message)

    ram_type = str(ram.meta.get("ram_type", "")).strip() if ram else ""
    mb_ram_type = str(motherboard.meta.get("ram_type", "")).strip() if motherboard else ""
    if ram and motherboard:
        if ram_type and mb_ram_type and ram_type == mb_ram_type:
            checks.append(
                _compatibility_record(
                    "memory_type",
                    "ok",
                    f"ОЗП і материнська плата узгоджені за стандартом {ram_type}.",
                )
            )
        else:
            message = (
                f"Несумісний тип пам’яті: ОЗП {ram_type or 'невідомий'}, "
                f"материнська плата {mb_ram_type or 'невідомий'}."
            )
            checks.append(_compatibility_record("memory_type", "error", message))
            _append_unique(errors, message)

    board_size = _guess_motherboard_form_factor(motherboard)
    case_size = str(case.meta.get("size", "")).strip() if case else ""
    if motherboard and case:
        if _case_supports_board(case_size, board_size):
            checks.append(
                _compatibility_record(
                    "form_factor",
                    "ok",
                    f"Корпус {case_size or 'невідомого формату'} підтримує плату {board_size}.",
                )
            )
        else:
            message = (
                f"Корпус {case_size or 'невідомого формату'} не підходить для плати {board_size}."
            )
            checks.append(_compatibility_record("form_factor", "error", message))
            _append_unique(errors, message)

    required_watt = _estimate_required_watt(cpu, gpu, purpose)
    psu_watt = _safe_int(psu.meta.get("watt"), 0) if psu else 0
    if psu:
        reserve = psu_watt - required_watt
        if required_watt <= 0:
            checks.append(
                _compatibility_record(
                    "psu_headroom",
                    "warning",
                    f"Потужність БЖ {psu_watt} Вт визначено, але енергоспоживання конфігурації оцінено приблизно.",
                )
            )
        elif reserve >= 100:
            checks.append(
                _compatibility_record(
                    "psu_headroom",
                    "ok",
                    f"Блок живлення {psu_watt} Вт має хороший запас над орієнтовною потребою {required_watt} Вт.",
                )
            )
        elif reserve >= 0:
            message = (
                f"Блок живлення {psu_watt} Вт працює майже без запасу над орієнтовною потребою {required_watt} Вт."
            )
            checks.append(_compatibility_record("psu_headroom", "warning", message))
            _append_unique(warnings, message)
        else:
            message = (
                f"Недостатня потужність БЖ: {psu_watt} Вт при орієнтовній потребі {required_watt} Вт."
            )
            checks.append(_compatibility_record("psu_headroom", "error", message))
            _append_unique(errors, message)

    ram_size = _safe_int(ram.meta.get("size_gb"), 0) if ram else 0
    ssd_size = _safe_int(ssd.meta.get("size_gb"), 0) if ssd else 0
    minimums = {
        "office": {"ram_gb": 8, "ssd_gb": 256},
        "study": {"ram_gb": 8, "ssd_gb": 256},
        "gaming": {"ram_gb": 16, "ssd_gb": 512},
        "creator": {"ram_gb": 32, "ssd_gb": 1000},
    }.get(purpose, {"ram_gb": 8, "ssd_gb": 256})

    if ram:
        if ram_size >= minimums["ram_gb"]:
            checks.append(
                _compatibility_record(
                    "ram_capacity",
                    "ok",
                    f"Обсяг ОЗП {ram_size} ГБ відповідає сценарію {purpose}.",
                )
            )
        else:
            message = (
                f"Для сценарію {purpose} бажано щонайменше {minimums['ram_gb']} ГБ ОЗП, зараз {ram_size} ГБ."
            )
            checks.append(_compatibility_record("ram_capacity", "warning", message))
            _append_unique(warnings, message)

    if ssd:
        if ssd_size >= minimums["ssd_gb"]:
            checks.append(
                _compatibility_record(
                    "ssd_capacity",
                    "ok",
                    f"SSD {ssd_size} ГБ відповідає очікуваному мінімуму для сценарію {purpose}.",
                )
            )
        else:
            message = (
                f"Для сценарію {purpose} бажано щонайменше {minimums['ssd_gb']} ГБ SSD, зараз {ssd_size} ГБ."
            )
            checks.append(_compatibility_record("ssd_capacity", "warning", message))
            _append_unique(warnings, message)

    has_igpu = bool(cpu.meta.get("igpu")) if cpu else False
    if purpose == "gaming":
        if gpu:
            vram = _safe_int(gpu.meta.get("vram"), 0)
            if vram < 8:
                message = (
                    f"Для ігрового сценарію краще мати від 8 ГБ VRAM, зараз у відеокарти {vram} ГБ."
                )
                checks.append(_compatibility_record("gaming_gpu_vram", "warning", message))
                _append_unique(warnings, message)
            else:
                checks.append(
                    _compatibility_record(
                        "gaming_gpu_vram",
                        "ok",
                        f"Відеокарта має {vram} ГБ VRAM, чого достатньо для більшості ігрових сценаріїв цього рівня.",
                    )
                )
        elif has_igpu:
            message = (
                "Ігрова конфігурація побудована без дискретної відеокарти; підійде лише для легких ігор або стартового рівня."
            )
            checks.append(_compatibility_record("gaming_gpu_presence", "warning", message))
            _append_unique(warnings, message)
        else:
            message = "Ігрова конфігурація не має ні дискретної, ні вбудованої графіки."
            checks.append(_compatibility_record("gaming_gpu_presence", "error", message))
            _append_unique(errors, message)

    if purpose == "creator":
        if gpu is None:
            message = "Для монтажу / 3D бажана дискретна відеокарта для прискорення ефектів і рендерингу."
            checks.append(_compatibility_record("creator_gpu_presence", "warning", message))
            _append_unique(warnings, message)
        else:
            vram = _safe_int(gpu.meta.get("vram"), 0)
            if vram < 8:
                message = (
                    f"Для важчих творчих задач бажано від 8 ГБ VRAM, зараз у відеокарти {vram} ГБ."
                )
                checks.append(_compatibility_record("creator_gpu_vram", "warning", message))
                _append_unique(warnings, message)
            else:
                checks.append(
                    _compatibility_record(
                        "creator_gpu_vram",
                        "ok",
                        f"Відеокарта має {vram} ГБ VRAM, що доречно для монтажу, GPU-ефектів і 3D.",
                    )
                )

    status = "ok"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"

    return {
        "status": status,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "estimated_required_watt": required_watt,
        "psu_watt": psu_watt,
    }


def _fallback_explanation(role: str, part: Part, purpose: str) -> str:
    labels = {
        "CPU": "Процесор",
        "GPU": "Відеокарта",
        "Motherboard": "Материнська плата",
        "RAM": "Оперативна пам’ять",
        "SSD": "Накопичувач",
        "PSU": "Блок живлення",
        "Case": "Корпус",
    }
    return (
        f"{labels.get(role, role)} {part.name} підібрано для сценарію {purpose} "
        "з урахуванням сумісності та балансу конфігурації."
    )


def _merge_part_explanations(
    result: dict[str, Any],
    parts: dict[str, Part],
    compatibility: dict[str, Any],
    purpose: str,
) -> dict[str, str]:
    explanations = dict(result.get("part_explanations") or {})

    cpu = parts.get("CPU")
    motherboard = parts.get("Motherboard")
    ram = parts.get("RAM")
    gpu = parts.get("GPU")
    psu = parts.get("PSU")
    case = parts.get("Case")

    for role, part in parts.items():
        text = str(explanations.get(role) or "").strip()
        if not text:
            text = _fallback_explanation(role, part, purpose)

        if role == "CPU" and cpu and motherboard:
            socket = str(cpu.meta.get("socket", "")).strip()
            if socket and socket in motherboard.name:
                text += f" Платформа узгоджена з материнською платою за сокетом {socket}."
        elif role == "Motherboard" and motherboard and ram:
            board_size = _guess_motherboard_form_factor(motherboard)
            ram_type = str(motherboard.meta.get("ram_type", "")).strip()
            extras: list[str] = []
            if board_size != "unknown":
                extras.append(f"форм-фактор {board_size}")
            if ram_type:
                extras.append(f"підтримка {ram_type}")
            if extras:
                text += " Додатково враховано: " + ", ".join(extras) + "."
        elif role == "RAM" and ram and motherboard:
            ram_type = str(ram.meta.get("ram_type", "")).strip()
            if ram_type:
                text += f" Тип пам’яті сумісний із материнською платою: {ram_type}."
        elif role == "GPU" and gpu:
            vram = _safe_int(gpu.meta.get("vram"), 0)
            if vram > 0:
                text += f" Доступно {vram} ГБ VRAM для цього сценарію."
        elif role == "PSU" and psu:
            required = _safe_int(compatibility.get("estimated_required_watt"), 0)
            watt = _safe_int(psu.meta.get("watt"), 0)
            if required > 0 and watt > 0:
                reserve = watt - required
                if reserve >= 0:
                    text += f" Орієнтовний запас потужності становить близько {reserve} Вт."
                else:
                    text += " Потрібно звернути увагу на запас потужності блока живлення."
        elif role == "Case" and case and motherboard:
            board_size = _guess_motherboard_form_factor(motherboard)
            case_size = str(case.meta.get("size", "")).strip()
            if case_size and board_size != "unknown":
                text += f" Корпус розрахований на плату формату {board_size} у класі {case_size}."

        explanations[role] = text.strip()

    return explanations


def finalize_build_result(
    result: dict[str, Any],
    *,
    parts: dict[str, Part],
    purpose: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    compatibility = evaluate_build_compatibility(parts, purpose, context)
    result["compatibility"] = compatibility
    result["compatibility_checks"] = compatibility["checks"]
    result["part_explanations"] = _merge_part_explanations(result, parts, compatibility, purpose)

    notes = list(result.get("notes") or [])
    if compatibility["errors"]:
        _append_unique(notes, f"Виявлено проблеми сумісності: {compatibility['errors'][0]}")
    elif compatibility["warnings"]:
        _append_unique(notes, f"Є зауваження до конфігурації: {compatibility['warnings'][0]}")
    result["notes"] = notes

    logger.info(
        "Постобробка конфігурації завершена: purpose=%s status=%s warnings=%s errors=%s",
        purpose,
        compatibility["status"],
        len(compatibility["warnings"]),
        len(compatibility["errors"]),
    )
    return result

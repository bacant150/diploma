from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .common import *  # noqa: F401,F403

def _part_label(role: str) -> str:
    return {
        "CPU": "Процесор",
        "GPU": "Відеокарта",
        "Motherboard": "Материнська плата",
        "RAM": "Оперативна пам’ять",
        "SSD": "SSD",
        "PSU": "Блок живлення",
        "Case": "Корпус",
    }.get(role, role)


def _format_storage_capacity(size_gb: int) -> str:
    if size_gb >= 1000 and size_gb % 1000 == 0:
        return f"{size_gb // 1000} ТБ"
    return f"{size_gb} ГБ" if size_gb > 0 else "невказаного обсягу"


def _graphics_quality_label(value: str) -> str:
    return {
        "low": "низькі",
        "medium": "середні",
        "high": "високі",
        "ultra": "ультра",
    }.get(value, value or "високі")


def _describe_cpu(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    socket = str(part.meta.get("socket", "")).strip()
    has_igpu = part.meta.get("igpu") is True
    gpu = parts.get("GPU")

    if purpose == "gaming":
        resolution = str(context.get("resolution", "1080p"))
        quality = _graphics_quality_label(str(context.get("graphics_quality", "high")))
        fps = int(context.get("target_fps", 60) or 60)
        base = f"Процесор підібраний під ігровий сценарій {resolution}, {quality} налаштування та ціль {fps} FPS."
        if gpu:
            base += f" Добре поєднується з {gpu.name} і не створює помітного вузького місця для цієї відеокарти."
        elif has_igpu:
            base += " Використовується разом із вбудованою графікою, тому розрахований на легші ігри або стартову конфігурацію."
    elif purpose == "creator":
        base = "Процесор орієнтований на монтаж, рендеринг і багатопотокові задачі, тому дає хороший запас для важчих творчих проєктів."
    elif purpose == "office":
        base = "Процесор достатній для щоденної офісної роботи, багатозадачності, браузера та типових робочих програм."
    else:
        base = "Процесор підібраний для навчання, програмування, браузера та повсякденних задач із запасом по чуйності системи."

    extras: List[str] = []
    if socket:
        extras.append(f"Платформа: {socket}")
    if has_igpu:
        extras.append("є вбудована графіка")
    if extras:
        base += " " + "; ".join(extras) + "."
    return base


def _describe_gpu(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    vram = int(part.meta.get("vram", 0) or 0)
    vram_text = f"{vram} ГБ відеопам’яті" if vram > 0 else "достатній запас відеопам’яті"

    if purpose == "gaming":
        resolution = str(context.get("resolution", "1080p"))
        quality = _graphics_quality_label(str(context.get("graphics_quality", "high")))
        fps = int(context.get("target_fps", 60) or 60)
        return f"Відеокарта відповідає цілі {resolution}, {quality} налаштування та {fps} FPS. Має {vram_text}, що важливо для сучасних ігор і текстур."
    if purpose == "creator":
        return f"Відеокарта прискорює монтаж, GPU-ефекти, 3D та рендеринг. {vram_text.capitalize()} корисно для складніших сцен, таймлайнів і проєктів."
    if purpose == "office":
        return f"Дискретна відеокарта додає запас для кількох моніторів, апаратного прискорення інтерфейсу та легких графічних задач. Передбачено {vram_text}."
    return f"Відеокарта дає запас для навчальних задач, роботи з графікою та кількома моніторами. Передбачено {vram_text}."


def _describe_motherboard(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    socket = str(part.meta.get("socket", "")).strip()
    ram_type = str(part.meta.get("ram_type", "")).strip()
    wifi_on_board = part.meta.get("wifi") is True

    base = "Материнська плата підібрана під процесор і пам’ять, тому забезпечує сумісність усієї платформи."
    details: List[str] = []
    if socket:
        details.append(f"сокет {socket}")
    if ram_type:
        details.append(f"підтримка {ram_type}")
    if wifi_on_board:
        details.append("є вбудований Wi‑Fi")
    if details:
        base += " Ключові параметри: " + ", ".join(details) + "."
    return base


def _describe_ram(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    size_gb = int(part.meta.get("size_gb", 0) or 0)
    ram_type = str(part.meta.get("ram_type", "")).strip()
    size_text = f"{size_gb} ГБ" if size_gb > 0 else "обраний обсяг"

    if purpose == "gaming":
        base = f"Обсяг оперативної пам’яті {size_text} достатній для ігор, фонових задач і стабільної роботи системи."
    elif purpose == "creator":
        base = f"Обсяг {size_text} дає запас для монтажу, важчих проєктів, багатозадачності та кешування робочих даних."
    elif purpose == "office":
        base = f"Обсяг {size_text} підібраний для комфортної офісної роботи, браузера та одночасного запуску кількох програм."
    else:
        base = f"Обсяг {size_text} підходить для навчання, програмування, відеозв’язку та повсякденної багатозадачності."

    if ram_type:
        base += f" Використовується пам’ять стандарту {ram_type}."
    return base


def _describe_ssd(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    size_gb = int(part.meta.get("size_gb", 0) or 0)
    size_text = _format_storage_capacity(size_gb)
    if purpose == "gaming":
        return f"SSD на {size_text} забезпечує швидке завантаження системи, ігор і зменшує час завантаження рівнів та великих проєктів."
    if purpose == "creator":
        return f"Накопичувач на {size_text} підібраний для системи, програм і робочих файлів, щоб проєкти відкривалися та зберігалися швидше."
    if purpose == "office":
        return f"SSD на {size_text} прискорює запуск Windows, офісних програм і забезпечує швидку повсякденну роботу без затримок."
    return f"SSD на {size_text} дає швидкий запуск системи, навчальних програм і достатній простір для файлів та проєктів."


def _describe_psu(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    watt = int(part.meta.get("watt", 0) or 0)
    required_watt = _estimate_required_watt(parts.get("CPU"), parts.get("GPU"), purpose)
    if watt > 0 and required_watt > 0:
        reserve = watt - required_watt
        if reserve >= 0:
            return f"Блок живлення на {watt} Вт покриває енергоспоживання системи із запасом приблизно {reserve} Вт, що корисно для стабільності та пікових навантажень."
        return f"Блок живлення на {watt} Вт підібраний як найближчий доступний варіант під цю конфігурацію."
    return "Блок живлення підібраний за потужністю під цю конфігурацію, щоб система працювала стабільно під навантаженням."


def _describe_case(part: Part, purpose: str, context: Dict[str, Any], parts: Dict[str, Part]) -> str:
    airflow = part.meta.get("airflow") is True
    showcase = part.meta.get("showcase") is True
    premium = part.meta.get("premium") is True

    base = "Корпус підібраний під габарити та клас конфігурації, щоб компоненти були сумісні між собою."
    details: List[str] = []
    if airflow:
        details.append("акцент на продув і охолодження")
    if showcase:
        details.append("вітринний дизайн")
    if premium:
        details.append("вищий клас виконання")
    if details:
        base += " Особливості: " + ", ".join(details) + "."
    return base


def _build_part_explanations(parts: Dict[str, Part], purpose: str, context: Dict[str, Any]) -> Dict[str, str]:
    descriptions: Dict[str, str] = {}
    for role, part in parts.items():
        if role == "CPU":
            descriptions[role] = _describe_cpu(part, purpose, context, parts)
        elif role == "GPU":
            descriptions[role] = _describe_gpu(part, purpose, context, parts)
        elif role == "Motherboard":
            descriptions[role] = _describe_motherboard(part, purpose, context, parts)
        elif role == "RAM":
            descriptions[role] = _describe_ram(part, purpose, context, parts)
        elif role == "SSD":
            descriptions[role] = _describe_ssd(part, purpose, context, parts)
        elif role == "PSU":
            descriptions[role] = _describe_psu(part, purpose, context, parts)
        elif role == "Case":
            descriptions[role] = _describe_case(part, purpose, context, parts)
    return descriptions


def _enrich_result_with_component_explanations(
    result: Dict[str, object],
    parts: Dict[str, Part],
    purpose: str,
    context: Dict[str, Any],
) -> Dict[str, object]:
    result["part_explanations"] = _build_part_explanations(parts, purpose, context)
    return result

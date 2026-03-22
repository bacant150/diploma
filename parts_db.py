
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Part:
    category: str
    name: str
    price: int  # грн (орієнтовна середня ринкова ціна)
    meta: Dict[str, object]


# tiers: budget | mid | upper
# ram_type: DDR4 | DDR5
# sockets: AM4 | AM5 | LGA1700
# У цій версії використані реальні моделі (SKU) з орієнтацією на середню

PARTS: List[Part] = [
    # ---------------- CPU ----------------
    Part("cpu", "AMD Ryzen 5 5500 BOX", 4699, {"tier": "mid", "socket": "AM4", "igpu": False, "game_score": 84}),
    Part("cpu", "AMD Ryzen 5 5600 BOX", 5999, {"tier": "mid", "socket": "AM4", "igpu": False, "game_score": 100}),
    Part("cpu", "AMD Ryzen 5 5600G BOX", 7899, {"tier": "mid", "socket": "AM4", "igpu": True, "game_score": 92, "igpu_game_score": 62, "office_igpu_score": 42}),
    Part("cpu", "AMD Ryzen 7 5700G BOX", 10999, {"tier": "upper", "socket": "AM4", "igpu": True, "game_score": 112, "igpu_game_score": 72, "office_igpu_score": 52}),
    Part("cpu", "AMD Ryzen 7 5700X BOX", 8999, {"tier": "upper", "socket": "AM4", "igpu": False, "game_score": 118}),
    Part("cpu", "AMD Ryzen 5 7500F Tray", 6999, {"tier": "upper", "socket": "AM5", "igpu": False, "game_score": 126}),
    Part("cpu", "AMD Ryzen 5 7600 BOX", 8799, {"tier": "upper", "socket": "AM5", "igpu": True, "game_score": 132, "igpu_game_score": 46, "office_igpu_score": 44}),
    Part("cpu", "AMD Ryzen 5 8600G BOX", 9699, {"tier": "upper", "socket": "AM5", "igpu": True, "game_score": 138, "igpu_game_score": 112, "office_igpu_score": 96}),
    Part("cpu", "AMD Ryzen 7 7700 Tray", 10999, {"tier": "upper", "socket": "AM5", "igpu": True, "game_score": 145, "igpu_game_score": 52, "office_igpu_score": 48}),
    Part("cpu", "AMD Ryzen 7 7800X3D BOX", 18999, {"tier": "upper", "socket": "AM5", "igpu": True, "game_score": 190, "igpu_game_score": 50, "office_igpu_score": 50}),
    Part("cpu", "AMD Ryzen 9 7900 BOX", 16999, {"tier": "upper", "socket": "AM5", "igpu": True, "game_score": 176, "igpu_game_score": 50, "office_igpu_score": 50}),
    Part("cpu", "AMD Ryzen 9 7950X BOX", 37499, {"tier": "upper", "socket": "AM5", "igpu": True, "game_score": 196, "igpu_game_score": 52, "office_igpu_score": 52}),
    Part("cpu", "Intel Pentium Gold G7400 BOX", 2799, {"tier": "budget", "socket": "LGA1700", "igpu": True, "game_score": 20, "igpu_game_score": 14, "office_igpu_score": 20}),
    Part("cpu", "Intel Core i3-12100 BOX", 6999, {"tier": "budget", "socket": "LGA1700", "igpu": True, "game_score": 76, "igpu_game_score": 24, "office_igpu_score": 40}),
    Part("cpu", "Intel Core i5-12400F BOX", 6999, {"tier": "mid", "socket": "LGA1700", "igpu": False, "game_score": 100}),
    Part("cpu", "Intel Core i5-12400 BOX", 7999, {"tier": "mid", "socket": "LGA1700", "igpu": True, "game_score": 102, "igpu_game_score": 32, "office_igpu_score": 46}),
    Part("cpu", "Intel Core i5-13400F BOX", 8499, {"tier": "upper", "socket": "LGA1700", "igpu": False, "game_score": 120}),
    Part("cpu", "Intel Core i5-13400 BOX", 9499, {"tier": "upper", "socket": "LGA1700", "igpu": True, "game_score": 122, "igpu_game_score": 36, "office_igpu_score": 50}),
    Part("cpu", "Intel Core i5-14600KF BOX", 12599, {"tier": "upper", "socket": "LGA1700", "igpu": False, "game_score": 158}),

    # ---------------- GPU ----------------
    Part("gpu", "AMD Radeon RX 6600 Sapphire Pulse 8GB", 11899, {"tier": "budget", "vram": 8, "game_score": 86}),
    Part("gpu", "NVIDIA GeForce RTX 3060 ASUS Dual 12GB", 18499, {"tier": "mid", "vram": 12, "game_score": 108}),
    Part("gpu", "NVIDIA GeForce RTX 4060 ASUS Dual OC 8GB", 14999, {"tier": "mid", "vram": 8, "game_score": 118}),
    Part("gpu", "AMD Radeon RX 6750 XT MSI Gaming X Trio 12GB", 23999, {"tier": "upper", "vram": 12, "game_score": 142}),
    Part("gpu", "NVIDIA GeForce RTX 4060 Ti Gigabyte Gaming OC 16GB", 24999, {"tier": "upper", "vram": 16, "game_score": 146}),
    Part("gpu", "AMD Radeon RX 7700 XT XFX QICK 319 Black 12GB", 22899, {"tier": "upper", "vram": 12, "game_score": 170}),
    Part("gpu", "NVIDIA GeForce RTX 4070 SUPER ASUS Dual EVO 12GB", 33999, {"tier": "upper", "vram": 12, "game_score": 205}),
    Part("gpu", "AMD Radeon RX 7800 XT XFX QICK 319 Core 16GB", 31999, {"tier": "upper", "vram": 16, "game_score": 200}),
    Part("gpu", "NVIDIA GeForce RTX 4070 Ti SUPER PNY XLR8 VERTO 16GB", 68600, {"tier": "upper", "vram": 16, "game_score": 255}),
    Part("gpu", "NVIDIA GeForce RTX 4080 SUPER 16GB", 54999, {"tier": "upper", "vram": 16, "game_score": 370}),
    Part("gpu", "AMD Radeon RX 7900 XTX XFX MERC 310 24GB", 58999, {"tier": "upper", "vram": 24, "game_score": 342}),
    Part("gpu", "NVIDIA GeForce RTX 4090 Gigabyte Gaming OC 24GB", 109999, {"tier": "upper", "vram": 24, "game_score": 470}),

    # ---------------- Motherboards ----------------
    Part("mb", "MSI B550M PRO-VDH (AM4, DDR4, mATX)", 5499, {"socket": "AM4", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "MSI B550M PRO-VDH WIFI (AM4, DDR4, mATX)", 6499, {"socket": "AM4", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "ASUS TUF GAMING X570-PLUS WIFI (AM4, DDR4, ATX)", 12499, {"socket": "AM4", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "Gigabyte A620M S2H (AM5, DDR5, mATX)", 6599, {"socket": "AM5", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "ASUS TUF GAMING A620M-PLUS WIFI (AM5, DDR5, mATX)", 6399, {"socket": "AM5", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "ASRock B650M-HDV/M.2 (AM5, DDR5, mATX)", 5599, {"socket": "AM5", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "MSI PRO B650-S WIFI (AM5, DDR5, ATX)", 9599, {"socket": "AM5", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "MSI MAG X670E TOMAHAWK WIFI (AM5, DDR5, ATX)", 17999, {"socket": "AM5", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "ASUS PRIME H610M-K D4 (LGA1700, DDR4, mATX)", 3199, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "ASUS PRIME H610M-A WIFI D4 (LGA1700, DDR4, mATX)", 4999, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "MSI PRO B760M-P DDR4 (LGA1700, DDR4, mATX)", 5599, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "MSI PRO B760M-A WIFI DDR4 (LGA1700, DDR4, mATX)", 9999, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "MSI PRO B760-P DDR4 II (LGA1700, DDR4, ATX)", 9999, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "MSI B760 GAMING PLUS WIFI (LGA1700, DDR5, ATX)", 8599, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": True}),

    # ---------------- RAM ----------------
    Part("ram", "Kingston Fury Beast 8GB (1x8) DDR4-3200", 2999, {"ram_type": "DDR4", "size_gb": 8, "speed": 3200}),
    Part("ram", "Kingston Fury Beast 16GB (2x8) DDR4-3200", 5999, {"ram_type": "DDR4", "size_gb": 16, "speed": 3200}),
    Part("ram", "Kingston Fury Beast 32GB (2x16) DDR4-3200", 7499, {"ram_type": "DDR4", "size_gb": 32, "speed": 3200}),
    Part("ram", "Kingston Fury Beast 64GB (2x32) DDR4-3200", 25999, {"ram_type": "DDR4", "size_gb": 64, "speed": 3200}),
    Part("ram", "Kingston Fury Beast 16GB (2x8) DDR5-5600", 7599, {"ram_type": "DDR5", "size_gb": 16, "speed": 5600}),
    Part("ram", "Kingston Fury Beast 32GB (2x16) DDR5-6000", 20999, {"ram_type": "DDR5", "size_gb": 32, "speed": 6000}),
    Part("ram", "Kingston Fury Beast 64GB (2x32) DDR5-6000", 38999, {"ram_type": "DDR5", "size_gb": 64, "speed": 6000}),
    Part("ram", "Corsair Vengeance 96GB (2x48) DDR5-6000", 49999, {"ram_type": "DDR5", "size_gb": 96, "speed": 6000}),

    # ---------------- SSD ----------------
    Part("ssd", "Patriot P220 256GB SATA SSD", 2169, {"size_gb": 256}),
    Part("ssd", "Kingston NV3 500GB NVMe SSD", 4899, {"size_gb": 500}),
    Part("ssd", "Kingston NV3 1TB NVMe SSD", 6999, {"size_gb": 1000}),
    Part("ssd", "Kingston NV3 2TB NVMe SSD", 12999, {"size_gb": 2000}),
    Part("ssd", "Kingston KC3000 4TB NVMe SSD", 35999, {"size_gb": 4000}),

    # ---------------- PSU ----------------
    Part("psu", "MSI MAG A550BN 550W 80+ Bronze", 2899, {"watt": 550}),
    Part("psu", "MSI MAG A650BN 650W 80+ Bronze", 3499, {"watt": 650}),
    Part("psu", "DeepCool PL750D 750W 80+ Bronze", 3599, {"watt": 750}),
    Part("psu", "be quiet! Pure Power 12 M 850W 80+ Gold", 6999, {"watt": 850}),
    Part("psu", "MSI MAG A1000GL 1000W 80+ Gold", 9999, {"watt": 1000}),

    # ---------------- Cases ----------------
    Part("case", "DeepCool MATREXX 40 3FS Black", 2199, {"size": "mATX", "airflow": True, "premium": False, "showcase": False}),
    Part("case", "Zalman S2 TG Black", 2299, {"size": "ATX", "airflow": False, "premium": False, "showcase": True}),
    Part("case", "DeepCool CC560 V2 Black", 3299, {"size": "ATX", "airflow": True, "premium": False, "showcase": False}),
    Part("case", "Montech AIR 903 MAX Black", 3675, {"size": "ATX", "airflow": True, "premium": True, "showcase": False}),
]

# Умовна база вимог ігор.
# gpu_base / cpu_base = умовна потреба в score для 1080p High 60 FPS.
GAMES_DB: Dict[str, Dict[str, object]] = {
    "cs2": {"title": "Counter-Strike 2", "gpu_base": 78, "cpu_base": 118, "genre": "esports"},
    "valorant": {"title": "Valorant", "gpu_base": 58, "cpu_base": 108, "genre": "esports"},
    "fortnite": {"title": "Fortnite", "gpu_base": 95, "cpu_base": 92, "genre": "battle_royale"},
    "gta5": {"title": "GTA V", "gpu_base": 82, "cpu_base": 84, "genre": "open_world"},
    "warzone": {"title": "Call of Duty: Warzone", "gpu_base": 135, "cpu_base": 112, "genre": "shooter"},
    "apex": {"title": "Apex Legends", "gpu_base": 112, "cpu_base": 96, "genre": "battle_royale"},
    "pubg": {"title": "PUBG: Battlegrounds", "gpu_base": 110, "cpu_base": 102, "genre": "battle_royale"},
    "cyberpunk2077": {"title": "Cyberpunk 2077", "gpu_base": 168, "cpu_base": 102, "genre": "rpg"},
    "rdr2": {"title": "Red Dead Redemption 2", "gpu_base": 155, "cpu_base": 98, "genre": "open_world"},
    "hogwarts": {"title": "Hogwarts Legacy", "gpu_base": 158, "cpu_base": 96, "genre": "rpg"},
    "alanwake2": {"title": "Alan Wake 2", "gpu_base": 190, "cpu_base": 100, "genre": "story"},
    "witcher3": {"title": "The Witcher 3", "gpu_base": 120, "cpu_base": 86, "genre": "rpg"},
    "forza5": {"title": "Forza Horizon 5", "gpu_base": 132, "cpu_base": 90, "genre": "racing"},
    "rainbowsix": {"title": "Rainbow Six Siege", "gpu_base": 82, "cpu_base": 105, "genre": "esports"},
    "dota2": {"title": "Dota 2", "gpu_base": 50, "cpu_base": 86, "genre": "moba"},
    "lol": {"title": "League of Legends", "gpu_base": 45, "cpu_base": 78, "genre": "moba"},
    "battlefield2042": {"title": "Battlefield 2042", "gpu_base": 145, "cpu_base": 108, "genre": "shooter"},
    "starfield": {"title": "Starfield", "gpu_base": 165, "cpu_base": 102, "genre": "rpg"},
    "re4": {"title": "Resident Evil 4", "gpu_base": 128, "cpu_base": 84, "genre": "horror"},
    "wukong": {"title": "Black Myth: Wukong", "gpu_base": 182, "cpu_base": 108, "genre": "action"},
}


# Умовна база офісних програм і сценаріїв.
# cpu_base = умовна потреба в CPU score.
# ram_gb = комфортний обсяг RAM для сценарію.
# ssd_gb = бажаний обсяг SSD.
# gpu_need = потреба в графіці: 0-100.
OFFICE_APPS_DB: Dict[str, Dict[str, object]] = {
    "word": {"title": "Word / Google Docs", "cpu_base": 24, "ram_gb": 4, "ssd_gb": 128, "gpu_need": 0, "multi_monitor": 1},
    "excel": {"title": "Excel / Google Sheets", "cpu_base": 42, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 5, "multi_monitor": 1},
    "browser": {"title": "Браузер / веб-робота", "cpu_base": 30, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 0, "multi_monitor": 1},
    "zoom": {"title": "Zoom / Microsoft Teams", "cpu_base": 48, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 8, "multi_monitor": 1},
    "outlook": {"title": "Outlook / пошта", "cpu_base": 28, "ram_gb": 4, "ssd_gb": 128, "gpu_need": 0, "multi_monitor": 1},
    "accounting": {"title": "1C / BAS / бухгалтерія", "cpu_base": 52, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 0, "multi_monitor": 1},
    "photoshop": {"title": "Adobe Photoshop", "cpu_base": 88, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 62, "multi_monitor": 1},
    "figma": {"title": "Figma", "cpu_base": 56, "ram_gb": 16, "ssd_gb": 256, "gpu_need": 35, "multi_monitor": 1},
    "vscode": {"title": "VS Code / програмування", "cpu_base": 74, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 5, "multi_monitor": 2},
    "powerbi": {"title": "Power BI / аналітика", "cpu_base": 78, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 18, "multi_monitor": 2},
    "autocad_light": {"title": "AutoCAD light / креслення", "cpu_base": 96, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 72, "multi_monitor": 2},
}


# Умовна база навчальних програм і сценаріїв.
# cpu_base = умовна потреба в CPU score.
# ram_gb = комфортний обсяг RAM для сценарію.
# ssd_gb = бажаний обсяг SSD.
# gpu_need = потреба в графіці: 0-100.
STUDY_APPS_DB: Dict[str, Dict[str, object]] = {
    "docs": {"title": "Word / Google Docs", "cpu_base": 20, "ram_gb": 4, "ssd_gb": 128, "gpu_need": 0, "multi_monitor": 1},
    "browser": {"title": "Браузер / онлайн-навчання", "cpu_base": 28, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 0, "multi_monitor": 1},
    "zoom": {"title": "Zoom / Google Meet", "cpu_base": 42, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 5, "multi_monitor": 1},
    "powerpoint": {"title": "PowerPoint / презентації", "cpu_base": 24, "ram_gb": 8, "ssd_gb": 256, "gpu_need": 0, "multi_monitor": 1},
    "vscode": {"title": "VS Code / програмування", "cpu_base": 62, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 5, "multi_monitor": 2},
    "python": {"title": "Python / навчальні проєкти", "cpu_base": 56, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 4, "multi_monitor": 1},
    "android_studio": {"title": "Android Studio", "cpu_base": 88, "ram_gb": 16, "ssd_gb": 1000, "gpu_need": 18, "multi_monitor": 2},
    "figma": {"title": "Figma", "cpu_base": 52, "ram_gb": 16, "ssd_gb": 256, "gpu_need": 28, "multi_monitor": 1},
    "photoshop_light": {"title": "Photoshop light", "cpu_base": 72, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 42, "multi_monitor": 1},
    "autocad_student": {"title": "AutoCAD student", "cpu_base": 92, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 70, "multi_monitor": 2},
}


# Умовна база програм для монтажу / 3D.
# cpu_base = умовна потреба в CPU score.
# ram_gb = комфортний обсяг RAM для сценарію.
# ssd_gb = бажаний обсяг SSD.
# gpu_need = потреба в графіці: 0-100.
# vram_gb = бажаний обсяг відеопам’яті.
CREATOR_APPS_DB: Dict[str, Dict[str, object]] = {
    "premiere": {"title": "Adobe Premiere Pro", "cpu_base": 86, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 62, "vram_gb": 8, "multi_monitor": 2},
    "davinci": {"title": "DaVinci Resolve", "cpu_base": 88, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 76, "vram_gb": 12, "multi_monitor": 2},
    "aftereffects": {"title": "Adobe After Effects", "cpu_base": 92, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 58, "vram_gb": 8, "multi_monitor": 2},
    "blender": {"title": "Blender / 3D рендер", "cpu_base": 94, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 84, "vram_gb": 12, "multi_monitor": 2},
    "maya": {"title": "Autodesk Maya", "cpu_base": 96, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 82, "vram_gb": 12, "multi_monitor": 2},
    "substance": {"title": "Substance Painter", "cpu_base": 78, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 88, "vram_gb": 12, "multi_monitor": 1},
    "photoshop": {"title": "Adobe Photoshop", "cpu_base": 74, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 36, "vram_gb": 6, "multi_monitor": 1},
    "illustrator": {"title": "Adobe Illustrator", "cpu_base": 68, "ram_gb": 16, "ssd_gb": 512, "gpu_need": 28, "vram_gb": 4, "multi_monitor": 1},
    "cad3d": {"title": "CAD / 3D моделювання", "cpu_base": 90, "ram_gb": 32, "ssd_gb": 1000, "gpu_need": 72, "vram_gb": 8, "multi_monitor": 2},
    "unreal": {"title": "Unreal Engine", "cpu_base": 98, "ram_gb": 32, "ssd_gb": 2000, "gpu_need": 90, "vram_gb": 12, "multi_monitor": 2},
}

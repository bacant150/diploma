from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Part:
    category: str
    name: str
    price: int  # грн (орієнтовно)
    meta: Dict[str, object]


# tiers: budget | mid | upper
# ram_type: DDR4 | DDR5
# sockets: AM4 | AM5 | LGA1700

PARTS: List[Part] = [
    # ---------------- CPU ----------------
    Part("cpu", "AMD Athlon 3000G", 1500, {"tier": "budget", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 3 3100", 2200, {"tier": "budget", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 3 4100", 2400, {"tier": "budget", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 1600AF", 2300, {"tier": "budget", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 2600", 2600, {"tier": "budget", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 3600", 3000, {"tier": "budget", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 4500", 3200, {"tier": "budget", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 4600G", 3900, {"tier": "mid", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 5 4600G", 4200, {"tier": "mid", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 5 5600G", 5200, {"tier": "mid", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 7 5700G", 7600, {"tier": "upper", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 5 5500", 3700, {"tier": "mid", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 5600G", 4800, {"tier": "mid", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 5 5600", 4200, {"tier": "mid", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 5600X", 4700, {"tier": "mid", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 7 5700G", 6900, {"tier": "upper", "socket": "AM4", "igpu": True}),
    Part("cpu", "AMD Ryzen 7 5700X", 6500, {"tier": "upper", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 7 5800X", 7600, {"tier": "upper", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 7 5800X3D", 10500, {"tier": "upper", "socket": "AM4", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 7500F", 7600, {"tier": "upper", "socket": "AM5", "igpu": False}),
    Part("cpu", "AMD Ryzen 5 7600", 8900, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 5 8600G", 10800, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 7 8700G", 14500, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 7 7700", 11800, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 7 7700X", 13200, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 7 7800X3D", 16500, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 9 7900", 17800, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 9 7900X", 20500, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 9 7950X", 26500, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "AMD Ryzen 9 7950X3D", 31500, {"tier": "upper", "socket": "AM5", "igpu": True}),
    Part("cpu", "Intel G7400", 2000, {"tier": "budget", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i3-12100", 3600, {"tier": "budget", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i3-12100F", 3300, {"tier": "budget", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i3-13100", 4200, {"tier": "mid", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i3-13100F", 3900, {"tier": "mid", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i5-12400", 5600, {"tier": "mid", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i5-13400", 7900, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i5-13600K", 11800, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i7-13700", 13800, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i5-12400F", 5200, {"tier": "mid", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i5-13400", 7800, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i5-13400F", 7200, {"tier": "upper", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i5-13500", 9800, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i5-13600KF", 10500, {"tier": "upper", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i7-12700F", 8800, {"tier": "upper", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i7-13700F", 12800, {"tier": "upper", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i7-13700K", 14900, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i7-14700F", 16200, {"tier": "upper", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i7-14700K", 18400, {"tier": "upper", "socket": "LGA1700", "igpu": True}),
    Part("cpu", "Intel i9-14900KF", 26500, {"tier": "upper", "socket": "LGA1700", "igpu": False}),
    Part("cpu", "Intel i9-14900K", 28900, {"tier": "upper", "socket": "LGA1700", "igpu": True}),

    # ---------------- GPU ----------------
    Part("gpu", "NVIDIA GTX 1050 Ti 4GB", 3200, {"tier": "budget", "vram": 4}),
    Part("gpu", "AMD RX 570 4GB", 3600, {"tier": "budget", "vram": 4}),
    Part("gpu", "AMD RX 580 8GB", 4900, {"tier": "budget", "vram": 8}),
    Part("gpu", "NVIDIA GTX 1650 4GB", 5200, {"tier": "budget", "vram": 4}),
    Part("gpu", "NVIDIA GTX 1660 SUPER 6GB", 7600, {"tier": "budget", "vram": 6}),
    Part("gpu", "NVIDIA RTX 2060 6GB", 8200, {"tier": "budget", "vram": 6}),
    Part("gpu", "NVIDIA RTX 3050 8GB", 8800, {"tier": "budget", "vram": 8}),
    Part("gpu", "AMD RX 6500 XT 4GB", 5200, {"tier": "budget", "vram": 4}),
    Part("gpu", "AMD RX 6600 8GB", 8500, {"tier": "budget", "vram": 8}),
    Part("gpu", "Intel Arc A580 8GB", 9100, {"tier": "mid", "vram": 8}),
    Part("gpu", "AMD RX 6600 XT 8GB", 9800, {"tier": "mid", "vram": 8}),
    Part("gpu", "AMD RX 6650 XT 8GB", 10500, {"tier": "mid", "vram": 8}),
    Part("gpu", "AMD RX 7600 8GB", 11000, {"tier": "mid", "vram": 8}),
    Part("gpu", "NVIDIA RTX 3060 12GB", 11800, {"tier": "mid", "vram": 12}),
    Part("gpu", "NVIDIA RTX 4060 8GB", 12500, {"tier": "mid", "vram": 8}),
    Part("gpu", "NVIDIA RTX 3060 Ti 8GB", 13200, {"tier": "mid", "vram": 8}),
    Part("gpu", "AMD RX 6700 XT 12GB", 13500, {"tier": "upper", "vram": 12}),
    Part("gpu", "AMD RX 6750 XT 12GB", 15000, {"tier": "upper", "vram": 12}),
    Part("gpu", "NVIDIA RTX 4060 Ti 8GB", 16500, {"tier": "upper", "vram": 8}),
    Part("gpu", "NVIDIA RTX 4060 Ti 16GB", 20500, {"tier": "upper", "vram": 16}),
    Part("gpu", "AMD RX 7700 XT 12GB", 19500, {"tier": "upper", "vram": 12}),
    Part("gpu", "NVIDIA RTX 4070 12GB", 22000, {"tier": "upper", "vram": 12}),
    Part("gpu", "AMD RX 7800 XT 16GB", 24000, {"tier": "upper", "vram": 16}),
    Part("gpu", "NVIDIA RTX 4070 SUPER 12GB", 26000, {"tier": "upper", "vram": 12}),
    Part("gpu", "AMD RX 7900 GRE 16GB", 28500, {"tier": "upper", "vram": 16}),
    Part("gpu", "NVIDIA RTX 4070 Ti SUPER 16GB", 36000, {"tier": "upper", "vram": 16}),
        Part("gpu", "NVIDIA RTX 4080 SUPER 16GB", 52000, {"tier": "upper", "vram": 16}),
    Part("gpu", "NVIDIA RTX 4090 24GB", 98000, {"tier": "upper", "vram": 24}),
    Part("gpu", "AMD RX 7900 XT 20GB", 36000, {"tier": "upper", "vram": 20}),
    Part("gpu", "AMD RX 7900 XTX 24GB", 45000, {"tier": "upper", "vram": 24}),
    Part("gpu", "NVIDIA RTX 4080 SUPER 16GB", 52000, {"tier": "upper", "vram": 16}),
    Part("gpu", "AMD RX 7900 XTX 24GB", 54000, {"tier": "upper", "vram": 24}),
    Part("gpu", "NVIDIA RTX 4090 24GB", 90000, {"tier": "upper", "vram": 24}),

    # ---------------- Motherboards ----------------
    Part("mb", "A520M (AM4, DDR4, mATX)", 2600, {"socket": "AM4", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "A520M Wi-Fi (AM4, DDR4, mATX)", 3200, {"socket": "AM4", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "B450M (AM4, DDR4, mATX)", 3000, {"socket": "AM4", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "B450M Wi-Fi (AM4, DDR4, mATX)", 3600, {"socket": "AM4", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "B550 (AM4, DDR4, ATX)", 4200, {"socket": "AM4", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "B550 Wi-Fi (AM4, DDR4, ATX)", 5000, {"socket": "AM4", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "X570 (AM4, DDR4, ATX)", 6500, {"socket": "AM4", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "X570 Wi-Fi (AM4, DDR4, ATX)", 7600, {"socket": "AM4", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "A620M (AM5, DDR5, mATX)", 5200, {"socket": "AM5", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "A620M Wi-Fi (AM5, DDR5, mATX)", 6100, {"socket": "AM5", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "B650 (AM5, DDR5, ATX)", 8200, {"socket": "AM5", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "B650 Wi-Fi (AM5, DDR5, ATX)", 9200, {"socket": "AM5", "ram_type": "DDR5", "wifi": True}),
            Part("mb", "X670E (AM5, DDR5, ATX)", 13500, {"socket": "AM5", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "X670E Wi-Fi (AM5, DDR5, ATX)", 15500, {"socket": "AM5", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "H610M (LGA1700, DDR4, mATX)", 3000, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "H610M Wi-Fi (LGA1700, DDR4, mATX)", 3800, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "B660 (LGA1700, DDR4, ATX)", 4800, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "B660 Wi-Fi (LGA1700, DDR4, ATX)", 5600, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "B760 (LGA1700, DDR4, ATX)", 5600, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": False}),
    Part("mb", "B760 Wi-Fi (LGA1700, DDR4, ATX)", 6500, {"socket": "LGA1700", "ram_type": "DDR4", "wifi": True}),
    Part("mb", "B760 (LGA1700, DDR5, ATX)", 7200, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "B760 Wi-Fi (LGA1700, DDR5, ATX)", 8200, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "Z690 (LGA1700, DDR5, ATX)", 9800, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "Z690 Wi-Fi (LGA1700, DDR5, ATX)", 11200, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": True}),
    Part("mb", "Z790 (LGA1700, DDR5, ATX)", 13800, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": False}),
    Part("mb", "Z790 Wi-Fi (LGA1700, DDR5, ATX)", 15800, {"socket": "LGA1700", "ram_type": "DDR5", "wifi": True}),

    # ---------------- RAM ----------------
    Part("ram", "2GB DDR4 (1x2) 2400", 350, {"ram_type": "DDR4", "size_gb": 2, "speed": 2400}),
    Part("ram", "4GB DDR4 (1x4) 2666", 650, {"ram_type": "DDR4", "size_gb": 4, "speed": 2666}),
    Part("ram", "8GB DDR4 (1x8) 3200", 1100, {"ram_type": "DDR4", "size_gb": 8, "speed": 3200}),
    Part("ram", "16GB DDR4 (2x8) 3200", 1800, {"ram_type": "DDR4", "size_gb": 16, "speed": 3200}),
    Part("ram", "16GB DDR4 (2x8) 3600", 2100, {"ram_type": "DDR4", "size_gb": 16, "speed": 3600}),
    Part("ram", "32GB DDR4 (2x16) 3200", 3200, {"ram_type": "DDR4", "size_gb": 32, "speed": 3200}),
    Part("ram", "32GB DDR4 (2x16) 3600", 3600, {"ram_type": "DDR4", "size_gb": 32, "speed": 3600}),
    Part("ram", "64GB DDR4 (2x32) 3200", 6800, {"ram_type": "DDR4", "size_gb": 64, "speed": 3200}),
    Part("ram", "128GB DDR4 (4x32) 3200", 13600, {"ram_type": "DDR4", "size_gb": 128, "speed": 3200}),
    Part("ram", "256GB DDR4 (8x32) 3200", 27200, {"ram_type": "DDR4", "size_gb": 256, "speed": 3200}),

    Part("ram", "8GB DDR5 (1x8) 5200", 1700, {"ram_type": "DDR5", "size_gb": 8, "speed": 5200}),
    Part("ram", "16GB DDR5 (2x8) 5600", 2600, {"ram_type": "DDR5", "size_gb": 16, "speed": 5600}),
    Part("ram", "32GB DDR5 (2x16) 5600", 4300, {"ram_type": "DDR5", "size_gb": 32, "speed": 5600}),
    Part("ram", "32GB DDR5 (2x16) 6000", 4800, {"ram_type": "DDR5", "size_gb": 32, "speed": 6000}),
    Part("ram", "64GB DDR5 (2x32) 5600", 8800, {"ram_type": "DDR5", "size_gb": 64, "speed": 5600}),
    Part("ram", "64GB DDR5 (2x32) 6000", 9800, {"ram_type": "DDR5", "size_gb": 64, "speed": 6000}),
    Part("ram", "96GB DDR5 (2x48) 6000", 15600, {"ram_type": "DDR5", "size_gb": 96, "speed": 6000}),
    Part("ram", "128GB DDR5 (4x32) 6000", 21400, {"ram_type": "DDR5", "size_gb": 128, "speed": 6000}),
    Part("ram", "192GB DDR5 (4x48) 6000", 31400, {"ram_type": "DDR5", "size_gb": 192, "speed": 6000}),
    Part("ram", "256GB DDR5 (8x32) 5600", 42600, {"ram_type": "DDR5", "size_gb": 256, "speed": 5600}),

    # ---------------- SSD ----------------
    Part("ssd", "128GB SATA SSD", 650, {"size_gb": 128}),
    Part("ssd", "256GB SATA SSD", 900, {"size_gb": 256}),
    Part("ssd", "512GB SATA SSD", 1250, {"size_gb": 512}),
    Part("ssd", "500GB NVMe SSD", 1400, {"size_gb": 500}),
    Part("ssd", "512GB NVMe SSD", 1550, {"size_gb": 512}),
    Part("ssd", "1TB NVMe SSD", 2200, {"size_gb": 1000}),
    Part("ssd", "2TB NVMe SSD", 3900, {"size_gb": 2000}),
    Part("ssd", "4TB NVMe SSD", 8200, {"size_gb": 4000}),

    # ---------------- PSU ----------------
    Part("psu", "400W 80+ Bronze", 1300, {"watt": 400}),
    Part("psu", "450W 80+ Bronze", 1500, {"watt": 450}),
    Part("psu", "500W 80+ Bronze", 1700, {"watt": 500}),
    Part("psu", "550W 80+ Bronze", 1950, {"watt": 550}),
    Part("psu", "650W 80+ Bronze", 2400, {"watt": 650}),
    Part("psu", "650W 80+ Gold", 3200, {"watt": 650}),
    Part("psu", "750W 80+ Gold", 3600, {"watt": 750}),
    Part("psu", "850W 80+ Gold", 4600, {"watt": 850}),
    Part("psu", "1000W 80+ Gold", 6200, {"watt": 1000}),
    Part("psu", "1200W 80+ Gold", 8900, {"watt": 1200}),
    Part("psu", "1000W 80+ Gold", 6200, {"watt": 1000}),
    Part("psu", "1200W 80+ Platinum", 9800, {"watt": 1200}),

    # ---------------- Cases ----------------
    Part("case", "Entry mATX Case", 700, {"size": "mATX"}),
    Part("case", "Basic mATX Case", 900, {"size": "mATX"}),
    Part("case", "Basic ATX Case", 1200, {"size": "ATX"}),
    Part("case", "Airflow ATX Case", 1800, {"size": "ATX"}),
    Part("case", "Premium Airflow ATX Case", 3200, {"size": "ATX"}),
    Part("case", "Tempered Glass ATX Case", 4200, {"size": "ATX"}),
    Part("case", "Flagship Full Tower Case", 7600, {"size": "E-ATX"}),
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

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
    Part('cpu', 'AMD Athlon 3000G', 1699, {'tier': 'budget', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 3 3100', 2599, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 3 4100', 2799, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 1600AF', 2299, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 2600', 2799, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 3600', 3399, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 4500', 3199, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 4600G', 3999, {'tier': 'mid', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 5 5500', 4699, {'tier': 'mid', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 5600G', 7899, {'tier': 'mid', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 5 5600', 5999, {'tier': 'mid', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 5600X', 6599, {'tier': 'mid', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 7 5700G', 10999, {'tier': 'upper', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 7 5700X', 8999, {'tier': 'upper', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 7 5800X', 10999, {'tier': 'upper', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 7 5800X3D', 12999, {'tier': 'upper', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 7500F', 6999, {'tier': 'upper', 'socket': 'AM5', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 7600', 8799, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 5 8600G', 9699, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 7 8700G', 13999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 7 7700', 10999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 7 7700X', 12999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 7 7800X3D', 18999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 9 7900', 16999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 9 7900X', 18999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 9 7950X', 37499, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 9 7950X3D', 44999, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
    Part('cpu', 'Intel G7400', 2799, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i3-12100', 6999, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i3-12100F', 4299, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i3-13100', 5299, {'tier': 'mid', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i3-13100F', 4799, {'tier': 'mid', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i5-12400', 7999, {'tier': 'mid', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-12400F', 6999, {'tier': 'mid', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i5-13400', 9499, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13400F', 8499, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i5-13500', 11999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13600K', 13999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13600KF', 12599, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-12700F', 11999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-13700', 18499, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i7-13700F', 16999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-13700K', 19999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i7-14700F', 19999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-14700K', 22999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i9-14900KF', 34999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i9-14900K', 37999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),

    # ---------------- GPU ----------------
    Part('gpu', 'NVIDIA GTX 1050 Ti 4GB', 4999, {'tier': 'budget', 'vram': 4}),
    Part('gpu', 'AMD RX 570 4GB', 4499, {'tier': 'budget', 'vram': 4}),
    Part('gpu', 'AMD RX 580 8GB', 6999, {'tier': 'budget', 'vram': 8}),
    Part('gpu', 'NVIDIA GTX 1650 4GB', 7499, {'tier': 'budget', 'vram': 4}),
    Part('gpu', 'NVIDIA GTX 1660 SUPER 6GB', 9999, {'tier': 'budget', 'vram': 6}),
    Part('gpu', 'NVIDIA RTX 2060 6GB', 10999, {'tier': 'budget', 'vram': 6}),
    Part('gpu', 'NVIDIA RTX 3050 8GB', 10999, {'tier': 'budget', 'vram': 8}),
    Part('gpu', 'AMD RX 6500 XT 4GB', 7999, {'tier': 'budget', 'vram': 4}),
    Part('gpu', 'AMD RX 6600 8GB', 11899, {'tier': 'budget', 'vram': 8}),
    Part('gpu', 'Intel Arc A580 8GB', 9499, {'tier': 'mid', 'vram': 8}),
    Part('gpu', 'AMD RX 6600 XT 8GB', 12999, {'tier': 'mid', 'vram': 8}),
    Part('gpu', 'AMD RX 6650 XT 8GB', 14499, {'tier': 'mid', 'vram': 8}),
    Part('gpu', 'AMD RX 7600 8GB', 13999, {'tier': 'mid', 'vram': 8}),
    Part('gpu', 'NVIDIA RTX 3060 12GB', 18499, {'tier': 'mid', 'vram': 12}),
    Part('gpu', 'NVIDIA RTX 4060 8GB', 14999, {'tier': 'mid', 'vram': 8}),
    Part('gpu', 'NVIDIA RTX 3060 Ti 8GB', 16999, {'tier': 'mid', 'vram': 8}),
    Part('gpu', 'AMD RX 6700 XT 12GB', 18999, {'tier': 'upper', 'vram': 12}),
    Part('gpu', 'AMD RX 6750 XT 12GB', 23999, {'tier': 'upper', 'vram': 12}),
    Part('gpu', 'NVIDIA RTX 4060 Ti 8GB', 19999, {'tier': 'upper', 'vram': 8}),
    Part('gpu', 'NVIDIA RTX 4060 Ti 16GB', 24999, {'tier': 'upper', 'vram': 16}),
    Part('gpu', 'AMD RX 7700 XT 12GB', 22899, {'tier': 'upper', 'vram': 12}),
    Part('gpu', 'NVIDIA RTX 4070 12GB', 26999, {'tier': 'upper', 'vram': 12}),
    Part('gpu', 'AMD RX 7800 XT 16GB', 31999, {'tier': 'upper', 'vram': 16}),
    Part('gpu', 'NVIDIA RTX 4070 SUPER 12GB', 33999, {'tier': 'upper', 'vram': 12}),
    Part('gpu', 'AMD RX 7900 GRE 16GB', 37999, {'tier': 'upper', 'vram': 16}),
    Part('gpu', 'NVIDIA RTX 4070 Ti SUPER 16GB', 49999, {'tier': 'upper', 'vram': 16}),
    Part('gpu', 'AMD RX 7900 XT 20GB', 46999, {'tier': 'upper', 'vram': 20}),
    Part('gpu', 'AMD RX 7900 XTX 24GB', 58999, {'tier': 'upper', 'vram': 24}),
    Part('gpu', 'NVIDIA RTX 4080 SUPER 16GB', 54999, {'tier': 'upper', 'vram': 16}),
    Part('gpu', 'NVIDIA RTX 4090 24GB', 109999, {'tier': 'upper', 'vram': 24}),

    # ---------------- Motherboards ----------------
    Part('mb', 'A520M (AM4, DDR4, mATX)', 2999, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'A520M Wi-Fi (AM4, DDR4, mATX)', 3999, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'B450M (AM4, DDR4, mATX)', 3599, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'B450M Wi-Fi (AM4, DDR4, mATX)', 4499, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'B550 (AM4, DDR4, ATX)', 5499, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'B550 Wi-Fi (AM4, DDR4, ATX)', 6499, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'X570 (AM4, DDR4, ATX)', 9999, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'X570 Wi-Fi (AM4, DDR4, ATX)', 12499, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'A620M (AM5, DDR5, mATX)', 6599, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'A620M Wi-Fi (AM5, DDR5, mATX)', 7999, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'B650 (AM5, DDR5, ATX)', 7799, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'B650 Wi-Fi (AM5, DDR5, ATX)', 9599, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'X670E (AM5, DDR5, ATX)', 16999, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'X670E Wi-Fi (AM5, DDR5, ATX)', 18999, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'H610M (LGA1700, DDR4, mATX)', 3199, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'H610M Wi-Fi (LGA1700, DDR4, mATX)', 4999, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'B660 (LGA1700, DDR4, ATX)', 4999, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'B660 Wi-Fi (LGA1700, DDR4, ATX)', 6499, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'B760 (LGA1700, DDR4, ATX)', 5599, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'B760 Wi-Fi (LGA1700, DDR4, ATX)', 6999, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'B760 (LGA1700, DDR5, ATX)', 7299, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'B760 Wi-Fi (LGA1700, DDR5, ATX)', 8599, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'Z690 (LGA1700, DDR5, ATX)', 10999, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'Z690 Wi-Fi (LGA1700, DDR5, ATX)', 12999, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'Z790 (LGA1700, DDR5, ATX)', 14999, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'Z790 Wi-Fi (LGA1700, DDR5, ATX)', 16999, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': True}),

    # ---------------- RAM ----------------
    Part('ram', 'Kingston Fury Beast 8GB (1x8) DDR4-3200', 1499, {'ram_type': 'DDR4', 'size_gb': 8, 'speed': 3200}),
    Part('ram', 'Kingston Fury Beast 16GB (2x8) DDR4-3200', 2799, {'ram_type': 'DDR4', 'size_gb': 16, 'speed': 3200}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR4-3200', 4799, {'ram_type': 'DDR4', 'size_gb': 32, 'speed': 3200}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR4-3200', 8999, {'ram_type': 'DDR4', 'size_gb': 64, 'speed': 3200}),
    Part('ram', 'Corsair Vengeance LPX 128GB (4x32) DDR4-3200', 18999, {'ram_type': 'DDR4', 'size_gb': 128, 'speed': 3200}),
    Part('ram', 'Corsair Vengeance LPX 256GB (8x32) DDR4-3200', 37999, {'ram_type': 'DDR4', 'size_gb': 256, 'speed': 3200}),
    Part('ram', 'Kingston ValueRAM 8GB (1x8) DDR5-5200', 1499, {'ram_type': 'DDR5', 'size_gb': 8, 'speed': 5200}),
    Part('ram', 'Kingston Fury Beast 16GB (2x8) DDR5-5600', 3599, {'ram_type': 'DDR5', 'size_gb': 16, 'speed': 5600}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR5-5600', 5499, {'ram_type': 'DDR5', 'size_gb': 32, 'speed': 5600}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR5-6000', 5999, {'ram_type': 'DDR5', 'size_gb': 32, 'speed': 6000}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR5-5600', 9999, {'ram_type': 'DDR5', 'size_gb': 64, 'speed': 5600}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR5-6000', 10999, {'ram_type': 'DDR5', 'size_gb': 64, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 96GB (2x48) DDR5-6000', 16999, {'ram_type': 'DDR5', 'size_gb': 96, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 128GB (4x32) DDR5-6000', 22999, {'ram_type': 'DDR5', 'size_gb': 128, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 192GB (4x48) DDR5-6000', 35999, {'ram_type': 'DDR5', 'size_gb': 192, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 256GB (8x32) DDR5-5600', 47999, {'ram_type': 'DDR5', 'size_gb': 256, 'speed': 5600}),

    # ---------------- SSD ----------------
    Part('ssd', 'Apacer AS350 128GB SATA SSD', 799, {'size_gb': 128}),
    Part('ssd', 'Patriot P220 256GB SATA SSD', 1199, {'size_gb': 256}),
    Part('ssd', 'Patriot P220 512GB SATA SSD', 1799, {'size_gb': 512}),
    Part('ssd', 'Kingston NV3 500GB NVMe SSD', 2999, {'size_gb': 500}),
    Part('ssd', 'Kingston NV3 512GB NVMe SSD', 3199, {'size_gb': 512}),
    Part('ssd', 'Kingston NV3 1TB NVMe SSD', 5999, {'size_gb': 1000}),
    Part('ssd', 'Kingston NV3 2TB NVMe SSD', 12999, {'size_gb': 2000}),
    Part('ssd', 'Kingston KC3000 4TB NVMe SSD', 24999, {'size_gb': 4000}),

    # ---------------- PSU ----------------
    Part('psu', 'Chieftec Value APB-400B8 400W 80+ Bronze', 1499, {'watt': 400}),
    Part('psu', 'Chieftec Value APB-450B8 450W 80+ Bronze', 1699, {'watt': 450}),
    Part('psu', 'Chieftec Value APB-500B8 500W 80+ Bronze', 1899, {'watt': 500}),
    Part('psu', 'MSI MAG A550BN 550W 80+ Bronze', 2499, {'watt': 550}),
    Part('psu', 'MSI MAG A650BN 650W 80+ Bronze', 2999, {'watt': 650}),
    Part('psu', 'be quiet! System Power 10 650W 80+ Gold', 3899, {'watt': 650}),
    Part('psu', 'DeepCool PL750D 750W 80+ Bronze', 3599, {'watt': 750}),
    Part('psu', 'be quiet! Pure Power 12 M 850W 80+ Gold', 5799, {'watt': 850}),
    Part('psu', 'MSI MAG A1000GL 1000W 80+ Gold', 7999, {'watt': 1000}),
    Part('psu', 'DeepCool PX1200G 1200W 80+ Gold', 11999, {'watt': 1200}),
    Part('psu', 'MSI MAG A1000GL 1000W 80+ Gold', 7999, {'watt': 1000}),
    Part('psu', 'be quiet! Straight Power 12 1200W 80+ Platinum', 14999, {'watt': 1200}),

    # ---------------- Cases ----------------
    Part('case', 'DeepCool MATREXX 40 3FS Airflow Black', 2299, {'size': 'mATX', 'airflow': True, 'premium': False, 'showcase': False}),
    Part('case', 'Zalman S2 TG Showcase Black', 2399, {'size': 'ATX', 'airflow': False, 'premium': False, 'showcase': True}),
    Part('case', 'DeepCool CC560 V2 Airflow Black', 3199, {'size': 'ATX', 'airflow': True, 'premium': False, 'showcase': False}),
    Part('case', 'Montech AIR 903 MAX Airflow Black', 3799, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': False}),
    Part('case', 'NZXT H6 Flow Showcase Black', 6399, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': True}),
    Part('case', 'Corsair 7000D Airflow Full Tower Black', 13999, {'size': 'E-ATX', 'airflow': True, 'premium': True, 'showcase': False}),

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

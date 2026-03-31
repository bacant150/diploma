from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, List


@dataclass(frozen=True)
class Part:
    category: str
    name: str
    price: int  # грн (орієнтовно)
    meta: Dict[str, object]


def _load_price_feed() -> Dict[str, Dict[str, object]]:
    price_feed_path = Path(__file__).resolve().parent / "data" / "price_feed.json"
    if not price_feed_path.exists():
        return {}

    try:
        with price_feed_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
            return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


# tiers: budget | mid | upper
# ram_type: DDR4 | DDR5
# sockets: AM4 | AM5 | LGA1700
_STATIC_PARTS: List[Part] = [
    # ---------------- CPU ----------------
    Part('cpu', 'AMD Ryzen 5 5500', 3799, {'tier': 'budget', 'socket': 'AM4', 'igpu': False, 'game_score': 84}),
    Part('cpu', 'AMD Ryzen 5 5600GT', 6837, {'tier': 'mid', 'socket': 'AM4', 'igpu': True, 'game_score': 96, 'office_igpu_score': 72}),
    Part('cpu', 'AMD Ryzen 5 5600', 5699, {'tier': 'mid', 'socket': 'AM4', 'igpu': False, 'game_score': 100}),
    Part('cpu', 'AMD Ryzen 5 5600X', 6499, {'tier': 'mid', 'socket': 'AM4', 'igpu': False, 'game_score': 108}),
    Part('cpu', 'AMD Ryzen 7 5700G', 8216, {'tier': 'upper', 'socket': 'AM4', 'igpu': True, 'game_score': 112, 'office_igpu_score': 88}),
    Part('cpu', 'AMD Ryzen 7 5700X', 7399, {'tier': 'upper', 'socket': 'AM4', 'igpu': False, 'game_score': 118}),
    Part('cpu', 'AMD Ryzen 7 5700X3D', 9599, {'tier': 'upper', 'socket': 'AM4', 'igpu': False, 'game_score': 150}),
    Part('cpu', 'AMD Ryzen 5 7500F', 7499, {'tier': 'upper', 'socket': 'AM5', 'igpu': False, 'game_score': 128}),
    Part('cpu', 'AMD Ryzen 5 8400F', 7179, {'tier': 'upper', 'socket': 'AM5', 'igpu': False, 'game_score': 120}),
    Part('cpu', 'AMD Ryzen 5 8500G', 7299, {'tier': 'upper', 'socket': 'AM5', 'igpu': True, 'game_score': 122, 'office_igpu_score': 96}),
    Part('cpu', 'AMD Ryzen 5 8600G', 9499, {'tier': 'upper', 'socket': 'AM5', 'igpu': True, 'game_score': 132, 'office_igpu_score': 104}),
    Part('cpu', 'AMD Ryzen 5 9600X', 10599, {'tier': 'upper', 'socket': 'AM5', 'igpu': True, 'game_score': 150, 'office_igpu_score': 54}),
    Part('cpu', 'AMD Ryzen 7 9700X', 13337, {'tier': 'upper', 'socket': 'AM5', 'igpu': True, 'game_score': 182, 'office_igpu_score': 60}),
    Part('cpu', 'AMD Ryzen 7 9800X3D', 21935, {'tier': 'upper', 'socket': 'AM5', 'igpu': True, 'game_score': 245, 'office_igpu_score': 62}),
    Part('cpu', 'AMD Ryzen 9 9900X', 19499, {'tier': 'upper', 'socket': 'AM5', 'igpu': True, 'game_score': 225, 'office_igpu_score': 72}),
    Part('cpu', 'Intel i3-13100', 6499, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': True, 'game_score': 78, 'office_igpu_score': 42}),
    Part('cpu', 'Intel i3-13100F', 4940, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': False, 'game_score': 76}),
    Part('cpu', 'Intel i3-14100', 6999, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': True, 'game_score': 82, 'office_igpu_score': 46}),
    Part('cpu', 'Intel i3-14100F', 5399, {'tier': 'budget', 'socket': 'LGA1700', 'igpu': False, 'game_score': 80}),
    Part('cpu', 'Intel i5-12400F', 6999, {'tier': 'mid', 'socket': 'LGA1700', 'igpu': False, 'game_score': 100}),
    Part('cpu', 'Intel i5-13400F', 8699, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False, 'game_score': 116}),
    Part('cpu', 'Intel i5-14400', 12565, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True, 'game_score': 128, 'office_igpu_score': 54}),
    Part('cpu', 'Intel i5-14400F', 9250, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False, 'game_score': 126}),
    Part('cpu', 'Intel i5-14600KF', 12999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False, 'game_score': 155}),
    Part('cpu', 'Intel i7-14700', 15539, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True, 'game_score': 188, 'office_igpu_score': 64}),
    Part('cpu', 'Intel i7-14700F', 14499, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False, 'game_score': 186}),
    Part('cpu', 'AMD Athlon 3000G', 1699, {'tier': 'budget', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 3 3100', 2599, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 3 4100', 2799, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 1600AF', 2299, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 2600', 2799, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 3600', 3399, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 4500', 3199, {'tier': 'budget', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 4600G', 5500, {'tier': 'mid', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 5 5600G', 7899, {'tier': 'mid', 'socket': 'AM4', 'igpu': True}),
    Part('cpu', 'AMD Ryzen 7 5800X', 10999, {'tier': 'upper', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 7 5800X3D', 14999, {'tier': 'upper', 'socket': 'AM4', 'igpu': False}),
    Part('cpu', 'AMD Ryzen 5 7600', 8799, {'tier': 'upper', 'socket': 'AM5', 'igpu': True}),
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
    Part('cpu', 'Intel i5-12400', 7999, {'tier': 'mid', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13400', 9499, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13500', 11999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13600K', 13999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i5-13600KF', 12599, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-12700F', 11999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-13700', 18499, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i7-13700F', 16999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i7-13700K', 19999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i7-14700K', 22999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),
    Part('cpu', 'Intel i9-14900KF', 34999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': False}),
    Part('cpu', 'Intel i9-14900K', 37999, {'tier': 'upper', 'socket': 'LGA1700', 'igpu': True}),

    # ---------------- GPU ----------------
    Part('gpu', 'Intel Arc B570 10GB', 13019, {'tier': 'budget', 'vram': 10, 'game_score': 95}),
    Part('gpu', 'Intel Arc B580 12GB', 15499, {'tier': 'mid', 'vram': 12, 'game_score': 120}),
    Part('gpu', 'NVIDIA RTX 5060 8GB', 20647, {'tier': 'mid', 'vram': 8, 'game_score': 145}),
    Part('gpu', 'NVIDIA RTX 5060 Ti 8GB', 22019, {'tier': 'upper', 'vram': 8, 'game_score': 172}),
    Part('gpu', 'NVIDIA RTX 5060 Ti 16GB', 28019, {'tier': 'upper', 'vram': 16, 'game_score': 190}),
    Part('gpu', 'AMD RX 9060 XT 16GB', 26252, {'tier': 'upper', 'vram': 16, 'game_score': 185}),
    Part('gpu', 'NVIDIA RTX 5070 12GB', 34099, {'tier': 'upper', 'vram': 12, 'game_score': 225}),
    Part('gpu', 'AMD RX 9070 16GB', 33029, {'tier': 'upper', 'vram': 16, 'game_score': 235}),
    Part('gpu', 'AMD RX 9070 XT 16GB', 38609, {'tier': 'upper', 'vram': 16, 'game_score': 270}),
    Part('gpu', 'NVIDIA RTX 5070 Ti 16GB', 59019, {'tier': 'upper', 'vram': 16, 'game_score': 300}),
    Part('gpu', 'NVIDIA RTX 5080 16GB', 67999, {'tier': 'upper', 'vram': 16, 'game_score': 390}),
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
    Part('mb', 'Gigabyte B550M AORUS ELITE (AM4, DDR4, mATX)', 4499, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'ASUS PRIME B550M-K (AM4, DDR4, mATX)', 4699, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'ASRock B550M Pro4 (AM4, DDR4, mATX)', 4755, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'ASUS TUF GAMING B550-PLUS (AM4, DDR4, ATX)', 5697, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'ASUS TUF GAMING B550M-PLUS Wi-Fi II (AM4, DDR4, mATX)', 6299, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'MSI B550-A PRO (AM4, DDR4, ATX)', 5499, {'socket': 'AM4', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'Gigabyte A620M H (AM5, DDR5, mATX)', 3762, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'Gigabyte A620M DS3H (AM5, DDR5, mATX)', 5916, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'ASUS TUF GAMING A620-PRO WIFI (AM5, DDR5, ATX)', 6999, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'MSI PRO B650M-B (AM5, DDR5, mATX)', 5200, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'MSI PRO B650M-P (AM5, DDR5, mATX)', 5780, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'Gigabyte B650M S2H (AM5, DDR5, mATX)', 5899, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'MSI PRO B650-S Wi-Fi (AM5, DDR5, ATX)', 6999, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'ASUS PRIME B650M-A WIFI II (AM5, DDR5, mATX)', 7299, {'socket': 'AM5', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'ASUS PRIME B760M-K D4 (LGA1700, DDR4, mATX)', 5143, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': False}),
    Part('mb', 'MSI PRO B760-P WIFI DDR4 (LGA1700, DDR4, ATX)', 7200, {'socket': 'LGA1700', 'ram_type': 'DDR4', 'wifi': True}),
    Part('mb', 'MSI PRO B760M-P (LGA1700, DDR5, mATX)', 4979, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'MSI PRO B760-P II (LGA1700, DDR5, ATX)', 6161, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': False}),
    Part('mb', 'MSI B760M GAMING PLUS WIFI (LGA1700, DDR5, mATX)', 6699, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': True}),
    Part('mb', 'ASUS TUF GAMING B760-PLUS WIFI (LGA1700, DDR5, ATX)', 8299, {'socket': 'LGA1700', 'ram_type': 'DDR5', 'wifi': True}),
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
    Part('ram', 'Kingston Fury Beast 16GB (2x8) DDR4-3200', 3199, {'ram_type': 'DDR4', 'size_gb': 16, 'speed': 3200}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR4-3200', 5625, {'ram_type': 'DDR4', 'size_gb': 32, 'speed': 3200}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR4-3200', 10999, {'ram_type': 'DDR4', 'size_gb': 64, 'speed': 3200}),
    Part('ram', 'Kingston Fury Beast 16GB (2x8) DDR5-6000', 4999, {'ram_type': 'DDR5', 'size_gb': 16, 'speed': 6000}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR5-6000', 6599, {'ram_type': 'DDR5', 'size_gb': 32, 'speed': 6000}),
    Part('ram', 'Kingston Fury Beast 48GB (2x24) DDR5-6000', 8999, {'ram_type': 'DDR5', 'size_gb': 48, 'speed': 6000}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR5-6000', 11999, {'ram_type': 'DDR5', 'size_gb': 64, 'speed': 6000}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR5-6400', 7299, {'ram_type': 'DDR5', 'size_gb': 32, 'speed': 6400}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR5-6400', 13499, {'ram_type': 'DDR5', 'size_gb': 64, 'speed': 6400}),
    Part('ram', 'Corsair Vengeance LPX 128GB (4x32) DDR4-3200', 18999, {'ram_type': 'DDR4', 'size_gb': 128, 'speed': 3200}),
    Part('ram', 'Corsair Vengeance LPX 256GB (8x32) DDR4-3200', 52999, {'ram_type': 'DDR4', 'size_gb': 256, 'speed': 3200}),
    Part('ram', 'Kingston ValueRAM 8GB (1x8) DDR5-5200', 1499, {'ram_type': 'DDR5', 'size_gb': 8, 'speed': 5200}),
    Part('ram', 'Kingston Fury Beast 16GB (2x8) DDR5-5600', 3599, {'ram_type': 'DDR5', 'size_gb': 16, 'speed': 5600}),
    Part('ram', 'Kingston Fury Beast 32GB (2x16) DDR5-5600', 5499, {'ram_type': 'DDR5', 'size_gb': 32, 'speed': 5600}),
    Part('ram', 'Kingston Fury Beast 64GB (2x32) DDR5-5600', 9999, {'ram_type': 'DDR5', 'size_gb': 64, 'speed': 5600}),
    Part('ram', 'Corsair Vengeance 96GB (2x48) DDR5-6000', 70000, {'ram_type': 'DDR5', 'size_gb': 96, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 128GB (4x32) DDR5-6000', 100000, {'ram_type': 'DDR5', 'size_gb': 128, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 192GB (4x48) DDR5-6000', 140000, {'ram_type': 'DDR5', 'size_gb': 192, 'speed': 6000}),
    Part('ram', 'Corsair Vengeance 256GB (8x32) DDR5-5600', 200000, {'ram_type': 'DDR5', 'size_gb': 256, 'speed': 5600}),

    # ---------------- SSD ----------------
    Part('ssd', 'Patriot P220 256GB SATA SSD', 1399, {'size_gb': 256}),
    Part('ssd', 'Patriot P220 512GB SATA SSD', 3209, {'size_gb': 512}),
    Part('ssd', 'Patriot P220 1TB SATA SSD', 5499, {'size_gb': 1000}),
    Part('ssd', 'Kingston NV3 500GB NVMe SSD', 2799, {'size_gb': 500}),
    Part('ssd', 'Kingston NV3 1TB NVMe SSD', 3899, {'size_gb': 1000}),
    Part('ssd', 'Kingston NV3 2TB NVMe SSD', 6999, {'size_gb': 2000}),
    Part('ssd', 'WD Blue SN580 1TB NVMe SSD', 6999, {'size_gb': 1000}),
    Part('ssd', 'WD Blue SN580 2TB NVMe SSD', 10999, {'size_gb': 2000}),
    Part('ssd', 'Crucial P3 Plus 1TB NVMe SSD', 3599, {'size_gb': 1000}),
    Part('ssd', 'Crucial P3 Plus 2TB NVMe SSD', 6999, {'size_gb': 2000}),
    Part('ssd', 'Apacer AS350 128GB SATA SSD', 799, {'size_gb': 128}),
    Part('ssd', 'Kingston NV3 512GB NVMe SSD', 3199, {'size_gb': 512}),
    Part('ssd', 'Kingston KC3000 4TB NVMe SSD', 24999, {'size_gb': 4000}),

    # ---------------- PSU ----------------
    Part('psu', 'MSI MAG A550BN 550W 80+ Bronze', 2499, {'watt': 550}),
    Part('psu', 'MSI MAG A650BN 650W 80+ Bronze', 4055, {'watt': 650}),
    Part('psu', 'MSI MAG A750BN PCIE5 750W 80+ Bronze', 4699, {'watt': 750}),
    Part('psu', 'DeepCool PL650D 650W 80+ Bronze', 3299, {'watt': 650}),
    Part('psu', 'DeepCool PL750D 750W 80+ Bronze', 3599, {'watt': 750}),
    Part('psu', 'MSI MAG A850GL PCIE5 850W 80+ Gold', 5479, {'watt': 850}),
    Part('psu', 'be quiet! Pure Power 12 M 850W 80+ Gold', 5799, {'watt': 850}),
    Part('psu', 'Corsair RM850e 850W 80+ Gold', 6999, {'watt': 850}),
    Part('psu', 'MSI MAG A1000GL PCIE5 1000W 80+ Gold', 7299, {'watt': 1000}),
    Part('psu', 'Chieftec Value APB-400B8 400W 80+ Bronze', 1499, {'watt': 400}),
    Part('psu', 'Chieftec Value APB-450B8 450W 80+ Bronze', 1699, {'watt': 450}),
    Part('psu', 'Chieftec Value APB-500B8 500W 80+ Bronze', 1899, {'watt': 500}),
    Part('psu', 'be quiet! System Power 10 650W 80+ Gold', 3899, {'watt': 650}),
    Part('psu', 'MSI MAG A1000GL 1000W 80+ Gold', 7999, {'watt': 1000}),
    Part('psu', 'DeepCool PX1200G 1200W 80+ Gold', 11999, {'watt': 1200}),
    Part('psu', 'be quiet! Straight Power 12 1200W 80+ Platinum', 14999, {'watt': 1200}),

    # ---------------- Cases ----------------
    Part('case', 'DeepCool MATREXX 40 3FS Airflow Black', 2399, {'size': 'mATX', 'airflow': True, 'premium': False, 'showcase': False}),
    Part('case', 'DeepCool CC360 ARGB Black', 2499, {'size': 'mATX', 'airflow': True, 'premium': False, 'showcase': True}),
    Part('case', 'DeepCool CC560 LIMITED V2 Black', 1699, {'size': 'ATX', 'airflow': True, 'premium': False, 'showcase': False}),
    Part('case', 'DeepCool CC560 V2 Airflow Black', 2979, {'size': 'ATX', 'airflow': True, 'premium': False, 'showcase': False}),
    Part('case', 'Montech AIR 903 MAX Black', 3999, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': False}),
    Part('case', 'Montech AIR 903 MAX White', 3999, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': False}),
    Part('case', 'NZXT H6 Flow Black', 4199, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': True}),
    Part('case', 'NZXT H6 Flow RGB Black', 5590, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': True}),
    Part('case', 'NZXT H6 Flow RGB White', 5499, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': True}),
    Part('case', 'Zalman S2 TG Showcase Black', 2399, {'size': 'ATX', 'airflow': False, 'premium': False, 'showcase': True}),
    Part('case', 'Montech AIR 903 MAX Airflow Black', 3799, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': False}),
    Part('case', 'NZXT H6 Flow Showcase Black', 6399, {'size': 'ATX', 'airflow': True, 'premium': True, 'showcase': True}),
    Part('case', 'Corsair 7000D Airflow Full Tower Black', 13999, {'size': 'E-ATX', 'airflow': True, 'premium': True, 'showcase': False}),


]


def _build_runtime_parts() -> List[Part]:
    price_feed = _load_price_feed()
    runtime_parts: List[Part] = []

    for part in _STATIC_PARTS:
        entry = price_feed.get(part.name, {})
        live_price = entry.get("price")

        if isinstance(live_price, (int, float)) and live_price > 0:
            runtime_parts.append(Part(part.category, part.name, int(live_price), part.meta))
        else:
            runtime_parts.append(part)

    return runtime_parts


PARTS = _build_runtime_parts()


# Умовна база вимог ігор.
# gpu_base / cpu_base = умовна потреба в score для 1080p High 60 FPS.
GAMES_DB = {
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


OFFICE_APPS_DB = {
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
}

STUDY_APPS_DB = {
    # Тимчасово порожньо
}

CREATOR_APPS_DB = {
    # Тимчасово порожньо
}
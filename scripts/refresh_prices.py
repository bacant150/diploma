import argparse
import html as html_lib
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LINKS_PATH = DATA_DIR / "price_links.json"
FEED_PATH = DATA_DIR / "price_feed.json"
ROZETKA_HOME = "https://rozetka.com.ua/ua/"
HARD_ROZETKA_HOME = "https://hard.rozetka.com.ua/ua/"

sys.path.insert(0, str(BASE_DIR))

try:
    import parts_db  # type: ignore
except Exception as exc:  # pragma: no cover
    print(f"[FATAL] Не вдалося імпортувати parts_db.py: {exc}")
    raise


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": ROZETKA_HOME,
}

AVAILABILITY_PATTERNS = [
    r"Є\s+в\s+наявності",
    r"Закінчується",
    r"Немає\s+в\s+наявності",
    r"Готовий\s+до\s+відправлення",
    r"Під\s+замовлення",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    for warmup_url in (ROZETKA_HOME, HARD_ROZETKA_HOME):
        try:
            session.get(warmup_url, timeout=20, allow_redirects=True)
        except requests.RequestException:
            pass
    return session


def get_local_price_map() -> dict[str, int]:
    static_parts = getattr(parts_db, "_STATIC_PARTS", None)
    if static_parts is None:
        static_parts = getattr(parts_db, "PARTS", [])
    return {part.name: int(part.price) for part in static_parts}


def clean_text(raw_html: str) -> str:
    cleaned = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw_html)
    cleaned = re.sub(r"(?is)<style.*?>.*?</style>", " ", cleaned)
    cleaned = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    cleaned = html_lib.unescape(cleaned)
    cleaned = cleaned.replace(" ", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_title(raw_html: str) -> str | None:
    patterns = [
        r"<h1[^>]*>(.*?)</h1>",
        r"<title>(.*?)</title>",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_html, re.IGNORECASE | re.DOTALL)
        if match:
            title = re.sub(r"<[^>]+>", " ", match.group(1))
            title = html_lib.unescape(title)
            title = re.sub(r"\s+", " ", title).strip()
            if title:
                return title
    return None


def extract_product_code(text: str) -> str | None:
    match = re.search(r"Код:\s*(\d{6,})", text)
    return match.group(1) if match else None


def parse_price_to_int(raw_value: str) -> int:
    digits = re.sub(r"[^\d]", "", raw_value)
    if not digits:
        raise ValueError("Не вдалося перетворити ціну")
    return int(digits)


def extract_primary_price(text: str) -> int:
    patterns = [
        r"Код:\s*\d{6,}(?:(?!Купити).){0,900}?([\d\s]{3,20})\s*₴",
        r"Код:\s*\d{6,}(?:(?!Оплатити\s+частинами).){0,900}?([\d\s]{3,20})\s*₴",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return parse_price_to_int(match.group(1))

    top_text = text[:4000]
    candidates = re.findall(r"([\d\s]{3,20})\s*₴", top_text)
    for candidate in candidates:
        try:
            value = parse_price_to_int(candidate)
        except ValueError:
            continue
        if 100 <= value <= 1_000_000:
            return value

    raise ValueError("Не вдалося знайти ціну на сторінці Rozetka")


def extract_availability(text: str) -> str | None:
    for pattern in AVAILABILITY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def fetch_rozetka_data(session: requests.Session, url: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            response = session.get(
                url,
                timeout=30,
                allow_redirects=True,
                headers={"Referer": HARD_ROZETKA_HOME},
            )
            response.raise_for_status()
            raw_html = response.text
            text = clean_text(raw_html)
            price = extract_primary_price(text)
            return {
                "price": price,
                "title": extract_title(raw_html),
                "product_code": extract_product_code(text),
                "availability": extract_availability(text),
                "url": url,
            }
        except Exception as exc:
            last_error = exc
            for warmup_url in (ROZETKA_HOME, HARD_ROZETKA_HOME):
                try:
                    session.get(warmup_url, timeout=20, allow_redirects=True)
                except requests.RequestException:
                    pass
            time.sleep(1.0 + attempt * 0.6)

    assert last_error is not None
    raise last_error


def build_feed_item_from_rozetka(url: str, rozetka_data: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "price": int(rozetka_data["price"]),
        "source_used": "rozetka",
        "rozetka_price": int(rozetka_data["price"]),
        "rozetka_url": url,
        "product_code": rozetka_data.get("product_code"),
        "availability": rozetka_data.get("availability"),
        "title": rozetka_data.get("title"),
        "checked_at": now,
    }


def build_feed_item_from_local(local_price: int) -> dict[str, Any]:
    return {
        "price": int(local_price),
        "source_used": "local",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Оновлення цін з Rozetka з fallback на локальні ціни")
    parser.add_argument("--limit", type=int, default=0, help="Обробити лише перші N записів для тесту")
    parser.add_argument("--delay", type=float, default=1.1, help="Пауза між запитами в секундах")
    args = parser.parse_args()

    links = load_json(LINKS_PATH)
    feed = load_json(FEED_PATH)
    local_prices = get_local_price_map()
    session = build_session()

    updated = 0
    errors = 0
    processed = 0

    for part_name, item in links.items():
        if args.limit and processed >= args.limit:
            break
        processed += 1

        rozetka_url = (item or {}).get("rozetka_url", "")
        local_price = local_prices.get(part_name)

        if rozetka_url:
            try:
                rozetka_data = fetch_rozetka_data(session, rozetka_url)
                feed[part_name] = build_feed_item_from_rozetka(rozetka_url, rozetka_data)
                updated += 1
                print(f"[ROZETKA] {part_name}: {feed[part_name]['price']} грн")
            except Exception as exc:
                errors += 1
                print(f"[ROZETKA ERR] {part_name}: {exc}")
                if local_price is not None:
                    feed[part_name] = build_feed_item_from_local(local_price)
                    print(f"[LOCAL] {part_name}: {local_price} грн")
        else:
            if local_price is not None:
                feed[part_name] = build_feed_item_from_local(local_price)
                print(f"[LOCAL] {part_name}: {local_price} грн")

        sleep_for = max(0.0, args.delay + random.uniform(0.0, 0.4))
        time.sleep(sleep_for)

    save_json(FEED_PATH, feed)
    print()
    print(f"Done. Updated: {updated}, errors: {errors}, total written: {len(feed)}")


if __name__ == "__main__":
    main()

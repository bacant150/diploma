import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LINKS_PATH = DATA_DIR / "price_links.json"
FEED_PATH = DATA_DIR / "price_feed.json"
DEBUG_DIR = DATA_DIR / "price_debug"

sys.path.insert(0, str(BASE_DIR))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    import parts_db  # type: ignore
except Exception as exc:
    print(f"[FATAL] Не вдалося імпортувати parts_db.py: {exc}")
    raise


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)

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


def get_local_price_map() -> dict[str, int]:
    static_parts = getattr(parts_db, "_STATIC_PARTS", None)
    if static_parts is None:
        static_parts = getattr(parts_db, "PARTS", [])
    return {part.name: int(part.price) for part in static_parts}


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u2009", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def parse_price_to_int(raw_value: str) -> int:
    digits = re.sub(r"[^\d]", "", raw_value)
    if not digits:
        raise ValueError("Не вдалося перетворити ціну")
    return int(digits)


def extract_product_code(text: str) -> str | None:
    match = re.search(r"Код:\s*(\d{6,})", text)
    return match.group(1) if match else None


def extract_availability(text: str) -> str | None:
    for pattern in AVAILABILITY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def sanitize_filename(value: str) -> str:
    value = re.sub(r'[\\/:*?"<>|]+', "_", value)
    value = re.sub(r"\s+", "_", value.strip())
    return value[:120] or "item"


def save_debug_files(part_name: str, body_text: str, html: str) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = sanitize_filename(part_name)
    (DEBUG_DIR / f"{stamp}_{base}.txt").write_text(body_text, encoding="utf-8")
    (DEBUG_DIR / f"{stamp}_{base}.html").write_text(html, encoding="utf-8")


def extract_title(page: Any, body_text: str) -> str | None:
    try:
        h1 = page.locator("h1").first.inner_text(timeout=2500).strip()
        if h1:
            return h1
    except Exception:
        pass

    try:
        title = page.title().strip()
        if title:
            return title
    except Exception:
        pass

    lines = [line.strip() for line in body_text.splitlines() if line.strip()]
    for line in lines[:15]:
        if (
            len(line) >= 10
            and "₴" not in line
            and "Код:" not in line
            and "ROZETKA" not in line.upper()
        ):
            return line
    return None


def extract_price_from_visible_dom(page: Any) -> int | None:
    candidates = page.evaluate(
        """
        () => {
          const out = [];
          const seen = new Set();

          for (const el of document.querySelectorAll('body *')) {
            const style = window.getComputedStyle(el);
            if (!style || style.visibility === 'hidden' || style.display === 'none') continue;

            const rect = el.getBoundingClientRect();
            if (rect.width < 2 || rect.height < 2) continue;
            if (rect.top > window.innerHeight * 1.8) continue;

            const txt = (el.innerText || '').replace(/\\s+/g, ' ').trim();
            if (!txt) continue;
            if (txt.length > 40) continue;
            if (!/^\\d[\\d\\s]{1,18}₴$/.test(txt)) continue;

            const key = `${txt}|${Math.round(rect.top)}|${Math.round(rect.left)}`;
            if (seen.has(key)) continue;
            seen.add(key);

            out.push({
              text: txt,
              top: rect.top,
              left: rect.left,
              width: rect.width,
              height: rect.height
            });
          }

          out.sort((a, b) => {
            if (Math.abs(a.top - b.top) > 6) return a.top - b.top;
            return a.left - b.left;
          });

          return out;
        }
        """
    )

    if not isinstance(candidates, list):
        return None

    values: list[int] = []
    for item in candidates:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        try:
            value = parse_price_to_int(text)
        except ValueError:
            continue
        if 100 <= value <= 1_000_000:
            values.append(value)

    if not values:
        return None

    # Зазвичай перші 1-2 значення зверху — це основна ціна / стара+нова ціна
    top_values = values[:3]
    return min(top_values)


def _segment_after_code(text: str) -> str:
    text = normalize_text(text)

    start_match = re.search(r"Код:\s*\d{6,}", text)
    start = start_match.start() if start_match else 0
    segment = text[start : start + 5000]

    end_markers = [
        "Цей товар у інших продавців",
        "Усі товари бренду",
        "Оплата.",
        "Гарантія.",
        "Лідерська продуктивність",
        "Ігровий процесор для ПК",
        "Простий апгрейд",
    ]

    end_positions = [segment.find(marker) for marker in end_markers if segment.find(marker) > 0]
    if end_positions:
        segment = segment[: min(end_positions)]

    return segment


def extract_price_from_text(text: str) -> int:
    segment = _segment_after_code(text)

    matches = list(re.finditer(r"([\d][\d\s]{1,18})\s*₴", segment))
    values: list[int] = []

    for match in matches:
        raw = match.group(1)
        try:
            value = parse_price_to_int(raw)
        except ValueError:
            continue

        if not (100 <= value <= 1_000_000):
            continue

        context_start = max(0, match.start() - 25)
        context = segment[context_start : match.start()].lower()

        # Відсікаємо "від 1088 ₴ x 4" та схожі блоки розстрочки
        if "від " in context:
            continue

        values.append(value)

    if values:
        return min(values[:3])

    raise ValueError("Не вдалося знайти ціну на сторінці Rozetka")


class RozetkaBrowserClient:
    def __init__(self, headless: bool = True, timeout_ms: int = 60000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "RozetkaBrowserClient":
        if sync_playwright is None:
            raise RuntimeError(
                "Не знайдено Playwright. Встанови його командою: "
                "pip install playwright && python -m playwright install chromium"
            )

        self._pw = sync_playwright().start()
        chromium = self._pw.chromium

        errors: list[str] = []
        variants = [
            {
                "channel": "chrome",
                "headless": self.headless,
                "args": ["--disable-blink-features=AutomationControlled"],
            },
            {
                "headless": self.headless,
                "args": ["--disable-blink-features=AutomationControlled"],
            },
        ]

        for kwargs in variants:
            try:
                self._browser = chromium.launch(**kwargs)
                break
            except Exception as exc:
                errors.append(str(exc))

        if self._browser is None:
            raise RuntimeError("Не вдалося запустити Playwright: " + " | ".join(errors))

        self._context = self._browser.new_context(
            user_agent=UA,
            locale="uk-UA",
            viewport={"width": 1440, "height": 2200},
            ignore_https_errors=True,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._context is not None:
                self._context.close()
        finally:
            try:
                if self._browser is not None:
                    self._browser.close()
            finally:
                if self._pw is not None:
                    self._pw.stop()

    def _dismiss_overlays(self, page: Any) -> None:
        selectors = [
            "button:has-text('Прийняти')",
            "button:has-text('Зрозуміло')",
            "button:has-text('Accept')",
            "button:has-text('ОК')",
        ]
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=1200):
                    locator.click(timeout=1200)
                    page.wait_for_timeout(250)
            except Exception:
                pass

    def _fetch_once(self, part_name: str, url: str) -> dict[str, Any]:
        if self._context is None:
            raise RuntimeError("Browser context не ініціалізований")

        page = self._context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            self._dismiss_overlays(page)
            page.wait_for_timeout(1500)

            body_text = page.locator("body").inner_text(timeout=5000)
            body_text = normalize_text(body_text)
            html = page.content()

            price = extract_price_from_visible_dom(page)
            if price is None:
                price = extract_price_from_text(body_text)

            return {
                "price": price,
                "title": extract_title(page, body_text),
                "product_code": extract_product_code(body_text),
                "availability": extract_availability(body_text),
                "url": url,
            }

        except Exception:
            try:
                body_text = normalize_text(page.locator("body").inner_text(timeout=2000))
            except Exception:
                body_text = ""

            try:
                html = page.content()
            except Exception:
                html = ""

            save_debug_files(part_name, body_text, html)
            raise

        finally:
            try:
                page.close()
            except Exception:
                pass

    def fetch(self, part_name: str, url: str) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(1, 4):
            try:
                return self._fetch_once(part_name, url)
            except Exception as exc:
                last_error = exc
                time.sleep(0.8 + attempt * 0.7)

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
    parser = argparse.ArgumentParser(
        description="Оновлення цін з Rozetka через Playwright"
    )
    parser.add_argument("--limit", type=int, default=0, help="Обробити лише перші N записів для тесту")
    parser.add_argument("--delay", type=float, default=1.5, help="Пауза між товарами в секундах")
    parser.add_argument("--headed", action="store_true", help="Запустити браузер з вікном")
    parser.add_argument("--timeout", type=int, default=60, help="Таймаут завантаження сторінки в секундах")
    args = parser.parse_args()

    links = load_json(LINKS_PATH)
    feed = load_json(FEED_PATH)
    local_prices = get_local_price_map()

    updated = 0
    errors = 0
    processed = 0

    with RozetkaBrowserClient(headless=not args.headed, timeout_ms=args.timeout * 1000) as client:
        print("[INFO] HTTP backend: playwright/chromium")

        for part_name, item in links.items():
            if args.limit and processed >= args.limit:
                break

            processed += 1
            rozetka_url = (item or {}).get("rozetka_url", "")
            local_price = local_prices.get(part_name)

            if rozetka_url:
                try:
                    rozetka_data = client.fetch(part_name, rozetka_url)
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

            time.sleep(max(0.0, args.delay + random.uniform(0.2, 0.8)))

    save_json(FEED_PATH, feed)

    print()
    print(f"Done. Updated: {updated}, errors: {errors}, total written: {len(feed)}")


if __name__ == "__main__":
    main()
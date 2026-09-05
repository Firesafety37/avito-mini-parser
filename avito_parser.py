from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

ARTICLES = {
    "223112R020": "Прокладка головки блока цилиндра",
    "233002F700": "Балансирный вал в сборе",
}
FIELDNAMES = [
    "article",
    "query",
    "title",
    "price",
    "location",
    "condition",
    "url",
    "price_rank",
    "checked_at",
    "status",
    "error",
]
MOSCOW_REGION = ("москва", "московская область", "химки", "балашиха", "подольск")
AVITO = "https://www.avito.ru"


def price_to_int(text: str) -> int | None:
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else None


def is_target_region(location: str) -> bool:
    s = (location or "").lower()
    return any(x in s for x in MOSCOW_REGION)


def is_new_item(text: str) -> bool:
    s = (text or "").lower().replace("ё", "е")
    if "б/у" in s or "бу" in s or "с пробегом" in s:
        return False
    return "нов" in s


def status_row(article: str, query: str, status: str, error: str = "", checked_at: str = "") -> dict:
    return {
        "article": article,
        "query": query,
        "title": "",
        "price": "",
        "location": "",
        "condition": "",
        "url": "",
        "price_rank": "",
        "checked_at": checked_at,
        "status": status,
        "error": error,
    }


def build_search_url(query: str) -> str:
    # Avito params are intentionally simple: Москва, condition=new, sort by cheap first.
    return f"{AVITO}/moskva_i_mo?q={quote_plus(query)}&s=1&f=ASgBAgICAUTyCrCKAQ"


def _text(node, selector: str) -> str:
    found = node.select_one(selector)
    return found.get_text(" ", strip=True) if found else ""


def parse_html(html: str, article: str, query: str, checked_at: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select('[data-marker="item"]') or soup.select("article")
    rows = []
    for card in cards:
        link = card.select_one('a[itemprop="url"], a[href*="/items/"], a[href]')
        title = _text(card, '[itemprop="name"], h3') or (link.get_text(" ", strip=True) if link else "")
        price_node = card.select_one('[itemprop="price"]')
        price = price_to_int(price_node.get("content", "") if price_node else _text(card, '[data-marker="item-price"]'))
        location = _text(card, '[data-marker="item-address"], [itemprop="address"]')
        full_text = card.get_text(" ", strip=True)
        url = urljoin(AVITO, link.get("href", "")) if link else ""
        if price is None or not is_target_region(location) or not is_new_item(full_text):
            continue
        rows.append({
            "article": article,
            "query": query,
            "title": title,
            "price": price,
            "location": location,
            "condition": "новое",
            "url": url,
            "price_rank": "",
            "checked_at": checked_at,
            "status": "найдено",
            "error": "",
        })
    return rows


def select_top(rows: list[dict], limit: int = 5) -> list[dict]:
    seen = set()
    unique = []
    for row in sorted(rows, key=lambda r: r["price"]):
        if row["url"] in seen:
            continue
        seen.add(row["url"])
        unique.append(row)
    for rank, row in enumerate(unique[:limit], 1):
        row["price_rank"] = rank
    return unique[:limit]


def write_csv(rows: list[dict], output: Path) -> None:
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def collect(samples: Path, live: bool, checked_at: str) -> list[dict]:
    out = []
    for article, name in ARTICLES.items():
        query = f"{article} {name}"
        try:
            sample = samples / f"{article}.html"
            if sample.exists():
                html = sample.read_text(encoding="utf-8")
            elif live:
                r = requests.get(build_search_url(query), timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
                html = r.text
            else:
                out.append(status_row(article, query, "ошибка", "sample html not found", checked_at))
                continue
            rows = select_top(parse_html(html, article, query, checked_at))
            out.extend(rows or [status_row(article, query, "не найдено", checked_at=checked_at)])
        except Exception as e:
            out.append(status_row(article, query, "ошибка", str(e), checked_at))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mini Avito parser for test task")
    parser.add_argument("--samples", type=Path, default=Path("samples"))
    parser.add_argument("--output", type=Path, default=Path("result.csv"))
    parser.add_argument("--live", action="store_true", help="try Avito HTTP without bypassing protections")
    parser.add_argument("--checked-at", default="")
    args = parser.parse_args(argv)
    checked_at = args.checked_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    write_csv(collect(args.samples, args.live, checked_at), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

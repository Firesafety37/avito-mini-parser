import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import avito_parser as p


def test_price_to_int_keeps_only_numeric_prices():
    assert p.price_to_int("2 100 ₽") == 2100
    assert p.price_to_int("Цена не указана") is None


def test_sample_html_is_filtered_deduped_sorted_and_ranked():
    checked_at = "2026-01-01T00:00:00+00:00"
    html = (ROOT / "samples" / "223112R020.html").read_text(encoding="utf-8")

    rows = p.select_top(p.parse_html(html, "223112R020", "223112R020", checked_at))

    assert [r["price"] for r in rows] == [1900, 2100, 2500, 2800, 3000]
    assert [r["price_rank"] for r in rows] == [1, 2, 3, 4, 5]
    assert {r["condition"] for r in rows} == {"новое"}
    assert all(p.is_target_region(r["location"]) for r in rows)


def test_duplicate_urls_do_not_repeat_within_article():
    html = (ROOT / "samples" / "233002F700.html").read_text(encoding="utf-8")

    rows = p.select_top(p.parse_html(html, "233002F700", "233002F700", "now"))

    assert [r["price"] for r in rows] == [8600, 9500]
    assert len({r["url"] for r in rows}) == len(rows)


def test_status_rows_cover_empty_and_errors():
    row = p.status_row("X", "X", "не найдено")
    err = p.status_row("X", "X", "ошибка", "timeout")

    assert row["status"] == "не найдено"
    assert err["status"] == "ошибка"
    assert err["error"] == "timeout"
    assert set(row) == set(p.FIELDNAMES)


def test_main_writes_csv_with_required_columns(tmp_path):
    out = tmp_path / "result.csv"

    code = p.main(["--samples", str(ROOT / "samples"), "--output", str(out), "--checked-at", "now"])

    assert code == 0
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert rows
    assert list(rows[0].keys()) == p.FIELDNAMES
    assert all(r["price"] == "" or r["price"].isdigit() for r in rows)
    assert [int(r["price"]) for r in rows if r["article"] == "223112R020"] == [1900, 2100, 2500, 2800, 3000]

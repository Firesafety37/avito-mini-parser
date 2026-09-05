# Avito Mini Parser

Мини-парсер объявлений Avito по артикулам из тестового задания.

По умолчанию проект работает как `live-first`: сначала делает реальные запросы к Avito, сохраняет/парсит HTML, а если Avito ограничивает доступ — честно отражает ошибку или использует `samples/` как воспроизводимый fallback. CAPTCHA, cookies, авторизация, прокси и обход блокировок не используются.

## Установка

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Быстрый запуск

```bash
python avito_parser.py --output result.csv
```

## Режимы

Live-first, основной режим:

```bash
python avito_parser.py --mode live-first --output result.csv --raw-dir raw_html
```

Только live, без fallback:

```bash
python avito_parser.py --mode live --output result-live.csv --raw-dir raw_html
```

Только сохранённые HTML:

```bash
python avito_parser.py --mode samples --samples samples --output result.csv
```

## Масштабирование списка артикулов

Без изменения кода можно передать CSV:

```bash
python avito_parser.py --articles articles.csv --output result.csv
```

Формат `articles.csv`:

```csv
article,name
223112R020,Прокладка головки блока цилиндра
233002F700,Балансирный вал в сборе
```

Для большого списка можно увеличить паузу между live-запросами:

```bash
python avito_parser.py --articles articles.csv --delay 3 --output result.csv
```

## Проверка

```bash
pytest -q
```

## Что собирается

`result.csv` содержит одну строку на объявление или строку статуса `не найдено` / `ошибка`.

Поля:

- `article`
- `query`
- `title`
- `price`
- `location`
- `condition`
- `url`
- `price_rank`
- `checked_at`
- `status`
- `error`

Цена сохраняется числом. Объявления без числовой цены не попадают в top-5.

## Регион, состояние и сортировка

- Регион задаётся в `build_search_url()` как `/moskva_i_mo/zapchasti_i_aksessuary`.
- Состояние задаётся URL-фильтром `f=...` и дополнительно проверяется в `is_new_item()`.
- Сортировка по цене задаётся `s=1` и дополнительно гарантируется в `select_top()`.

## Если Avito блокирует live

Скрипт не скрывает проблему: в `--mode live` появится строка `ошибка`, например `Avito access restricted` или `HTTP 429`. Это ожидаемо для датацентров/VPS и не обходится по условиям задания.

Для проверки логики без обхода защиты используйте:

```bash
python avito_parser.py --mode samples --output result.csv
```

## Дорожная карта

[ROADMAP.md](ROADMAP.md)

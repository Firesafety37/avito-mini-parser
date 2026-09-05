# Avito Mini Parser

Мини-парсер объявлений Avito по артикулам из тестового задания.

По умолчанию проект сначала делает live-запросы к Avito. Если Avito ограничивает доступ, включается fallback на сохранённые HTML-файлы из `samples/`. Live-режим не обходит CAPTCHA, авторизацию, cookies и другие средства защиты.

## Установка

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python avito_parser.py --output result.csv
```

По умолчанию используется `--mode live-first`: сначала live-запросы к Avito, если Avito ограничил доступ — fallback на `samples/`.

Только live, без fallback:

```bash
python avito_parser.py --mode live --output result-live.csv
```

Только сохранённые HTML:

```bash
python avito_parser.py --mode samples --samples samples --output result.csv
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

- Регион задаётся в `build_search_url()` как поиск по Москве и Московской области.
- Состояние задаётся в URL-фильтре и дополнительно проверяется в `is_new_item()`.
- Сортировка по цене задаётся параметрами URL и дополнительно гарантируется в `select_top()`.

## Ограничение

Проект не обходит CAPTCHA, авторизацию, блокировки, cookies и другие средства защиты Avito. Если live-страница недоступна, скрипт пишет строку со статусом `ошибка`. Основной проверяемый режим — парсинг HTML из `samples/`.

## План

Дорожная карта выполнения: [ROADMAP.md](ROADMAP.md).

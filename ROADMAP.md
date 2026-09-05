# Avito Mini Parser Roadmap

> **For Hermes:** Ponytail full: минимум файлов, stdlib где можно, без обхода блокировок Avito. TDD/self-check для парсинга обязателен.

**Goal:** Сделать публичный GitHub-репозиторий с Python 3.10+ мини-парсером Avito, результатом `result.csv`/`result.xlsx`, README и кратким отчётом по времени/сложностям/ИИ.

**Architecture:** Один CLI-скрипт ищет артикулы через Avito или, если сайт недоступен/блокирует, парсит сохранённые HTML-файлы. Основная логика разделена ровно настолько, чтобы тестировать: URL builder, HTML parser, фильтрация/дедуп/топ-5, CSV export. Без cookies, токенов, CAPTCHA bypass.

**Tech Stack:** Python 3.10+, `requests`, `beautifulsoup4`, `pytest`; CSV через stdlib. `pandas/openpyxl` не нужны: задание разрешает `result.csv`.

---

## Принятые решения

- Репозиторий: `avito-mini-parser` у `Firesafety37`, публичный.
- Выходной файл: `result.csv`, не XLSX — меньше зависимостей, полностью подходит под ТЗ.
- По умолчанию использовать тестовые HTML из `samples/`, чтобы результат воспроизводился без нарушения защиты Avito.
- Реальный HTTP-режим оставить опциональным флагом `--live`; при ошибках писать строку `ошибка`, без попыток обхода.
- Регион/состояние/сортировка задаются через формирование Avito URL: Москва+МО, `condition=new`, сортировка по цене; дополнительно фильтровать HTML после парсинга.

## Структура файлов

```text
avito-mini-parser/
├── avito_parser.py
├── requirements.txt
├── README.md
├── REPORT.md
├── result.csv              # генерируется и коммитится как пример результата
├── samples/
│   ├── 223112R020.html
│   └── 233002F700.html
└── tests/
    └── test_avito_parser.py
```

---

## План по шагам

### Task 1: Создать локальный проект и git

**Objective:** Подготовить пустую рабочую папку без лишнего scaffolding.

**Files:**
- Create dir: `/root/avito-mini-parser`
- Create: `.gitignore`

**Actions:**
1. Создать директорию `/root/avito-mini-parser`.
2. `git init -b main`.
3. `.gitignore`: только `__pycache__/`, `.pytest_cache/`, `.venv/`.
4. Commit: `chore: initialize project`.

**Verify:**
- `git status --short` пустой после коммита.

---

### Task 2: Написать первый failing self/test для CSV schema и статусов

**Objective:** Зафиксировать контракт результата до реализации.

**Files:**
- Create: `tests/test_avito_parser.py`
- Create: `requirements.txt`

**Test cases:**
- CSV columns включают все поля ТЗ:
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
- Для пустой выдачи создаётся одна строка `status == "не найдено"`.

**Run RED:**
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest tests/test_avito_parser.py -q
```
Expected: FAIL, потому что `avito_parser.py` ещё нет.

**Commit after GREEN:**
`test: define result schema and empty result behavior`

---

### Task 3: Реализовать минимальные dataclass/helpers

**Objective:** Сделать минимальную модель строки результата и обработку пустых результатов.

**Files:**
- Create: `avito_parser.py`
- Modify: `tests/test_avito_parser.py`

**Implementation outline:**
- `ARTICLES = {"223112R020": "Прокладка головки блока цилиндра", ...}`
- `FIELDNAMES = [...]`
- `make_status_row(article, query, status, error="") -> dict`
- `write_csv(rows, path)` через stdlib `csv.DictWriter`.

**Run GREEN:**
```bash
pytest tests/test_avito_parser.py -q
```
Expected: PASS.

**Commit:**
`feat: add result row schema and csv writer`

---

### Task 4: Добавить тестовые HTML samples

**Objective:** Иметь воспроизводимые данные без зависимости от Avito и без обхода блокировок.

**Files:**
- Create: `samples/223112R020.html`
- Create: `samples/233002F700.html`
- Modify: `tests/test_avito_parser.py`

**Sample coverage:**
- Для `223112R020`: 7 карточек, из них:
  - 5 валидных новых Москва/МО с числовой ценой;
  - 1 б/у — должна отфильтроваться;
  - 1 другой регион — должна отфильтроваться;
  - 1 без числовой цены — не участвует в top-5.
- Для `233002F700`: 2 валидные карточки + дубль URL.

**Tests:**
- Парсер возвращает только новые Москва/МО.
- Цена `int`, не строка.
- Дубли URL в рамках артикула убираются.
- Top-5 сортируется по цене.

**Run RED:**
`pytest tests/test_avito_parser.py -q`
Expected: FAIL — HTML parser ещё не реализован.

**Commit after GREEN:**
`test: add sample html parser cases`

---

### Task 5: Реализовать HTML parser и фильтрацию

**Objective:** Извлекать объявления из сохранённых HTML и применять требования ТЗ.

**Files:**
- Modify: `avito_parser.py`

**Implementation outline:**
- `parse_html(html, article, query, checked_at) -> list[dict]`
- Использовать BeautifulSoup.
- Поддержать селекторы samples + мягкие fallback по `data-marker`, ссылкам `/items/`, тексту цены.
- `price_to_int(text) -> int | None`.
- `is_new(condition_text/title/card_text)` — строго новое; не пропускать `б/у`.
- `is_target_region(location)` — Москва, Московская область, Химки, Балашиха, Подольск и т.п. достаточно для samples; не пытаться сделать геокодер.
- `select_top(rows)` — dedup по URL, убрать price None, sort asc, rank 1..5.

**Run GREEN:**
```bash
pytest tests/test_avito_parser.py -q
```
Expected: PASS.

**Commit:**
`feat: parse saved avito html and select cheapest ads`

---

### Task 6: Добавить CLI

**Objective:** Запуск одной командой, генерация `result.csv`.

**Files:**
- Modify: `avito_parser.py`

**CLI:**
```bash
python avito_parser.py --samples samples --output result.csv
python avito_parser.py --live --output result.csv
```

**Behavior:**
- По умолчанию samples mode.
- Для каждого артикула:
  - если sample file есть — парсить его;
  - если нет и `--live` — пробовать HTTP GET;
  - если ошибка HTTP/timeout — строка `ошибка`;
  - если валидных объявлений нет — строка `не найдено`.
- `checked_at` один ISO timestamp на запуск.

**Test:**
- Минимальный тест `main([...])` создаёт CSV во временной папке и проверяет количество/сортировку строк.

**Run:**
```bash
pytest tests/test_avito_parser.py -q
python avito_parser.py --samples samples --output result.csv
```
Expected: tests PASS, создан `result.csv`.

**Commit:**
`feat: add cli and csv generation`

---

### Task 7: README и отчёт

**Objective:** Закрыть формальные требования задания.

**Files:**
- Create: `README.md`
- Create: `REPORT.md`

**README must include:**
- Что делает скрипт.
- Установка:
  ```bash
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
  ```
- Запуск:
  ```bash
  python avito_parser.py --samples samples --output result.csv
  ```
- Опционально live:
  ```bash
  python avito_parser.py --live --output result.csv
  ```
- Где задаются регион, состояние и сортировка:
  - в `build_search_url()` query params/path;
  - дополнительно проверяются фильтрами после парсинга.
- Ограничение: CAPTCHA/блокировки не обходятся.

**REPORT must include:**
- Фактически затраченное время: примерно 1.5–2 часа.
- Сложности: нестабильная HTML-структура Avito, возможные блокировки, нет обхода CAPTCHA по ТЗ.
- Использование ИИ: помощь в структуре кода, тест-кейсах, README; финальная проверка руками/тестами.

**Commit:**
`docs: add usage guide and implementation report`

---

### Task 8: Финальная проверка

**Objective:** Перед публикацией реально проверить артефакты.

**Commands:**
```bash
. .venv/bin/activate
pytest -q
python avito_parser.py --samples samples --output result.csv
python - <<'PY'
import csv
with open('result.csv', newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
assert rows, 'empty result.csv'
assert all(r['price'] == '' or r['price'].isdigit() for r in rows)
print(len(rows), rows[0].keys())
PY
git status --short
```

**Expected:**
- tests pass;
- `result.csv` не пустой;
- цены числовые;
- только ожидаемые изменения.

**Commit if result.csv changed:**
`chore: add generated sample result`

---

### Task 9: Создать GitHub repo и push

**Objective:** Передать результат ссылкой.

**Actions:**
1. Проверить наличие `gh`; если нет — использовать GitHub API token из `/root/.hermes/.env`/git credentials.
2. Создать публичный репозиторий `Firesafety37/avito-mini-parser`.
3. Добавить remote origin.
4. Push `main`.

**Commands preferred:**
```bash
gh repo create avito-mini-parser --public --source . --push --description "Mini parser for Avito test task"
```

**Fallback:** GitHub REST API + `git push`.

**Verify:**
- Открыть/проверить `https://github.com/Firesafety37/avito-mini-parser`.
- Убедиться, что есть `avito_parser.py`, `result.csv`, `README.md`, `REPORT.md`.

---

## Риски и как закрываем

| Риск | Решение |
|---|---|
| Avito блокирует HTTP | Основной режим через сохранённые HTML; live без обхода, ошибки пишутся в CSV |
| Меняется HTML Avito | Parser tolerant: `data-marker` + fallback; samples доказывают контракт |
| Лишние зависимости | Только `requests`, `beautifulsoup4`, `pytest`; CSV stdlib |
| Проверяющий ожидает XLSX | ТЗ разрешает CSV; README явно указывает `result.csv` |
| Регион/состояние неточно в live HTML | Фильтруем после парсинга, спорные карточки не включаем |

---

## Definition of Done

- [ ] Репозиторий GitHub создан и доступен.
- [ ] Есть исходный код `avito_parser.py`.
- [ ] Есть `result.csv` с одной строкой на объявление/статус.
- [ ] Есть `README.md` с запуском и зависимостями.
- [ ] Есть `REPORT.md` с временем, сложностями, ИИ.
- [ ] `pytest -q` проходит.
- [ ] `python avito_parser.py --samples samples --output result.csv` реально создаёт результат.
- [ ] В коде нет логинов/cookies/tokens.

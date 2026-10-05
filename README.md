# docs2md — рабочие документы в Markdown

**Один CLI для превращения рабочих документов в Markdown.** Без LibreOffice, без pandoc, без
«тяжёлых» офисных пакетов: только Python и несколько библиотек.

> **Abstract (EN).** `docs2md` converts work documents — PDF, DOCX, PPTX, XLSX, HTML, EPUB, Jupyter
> notebooks and plain-text formats — into Markdown for LLM pipelines and text analysis. It is a thin,
> dependency-light CLI: no LibreOffice/pandoc, just Python. Two details it gets right where generic
> converters stumble: **tables from PDF** (via PyMuPDF) and **text inside grouped shapes in PPTX**
> (a naive extractor loses almost everything). Unsupported formats fail loudly instead of
> "almost working". MIT licensed.

## Что умеет

| Формат | Что извлекается |
|---|---|
| **PDF** | текст по страницам, **таблицы** в Markdown (PyMuPDF), сведения о текстовом слое |
| **DOCX** | текст с чистой разметкой (экранирование снимается) |
| **PPTX** | текст слайдов, таблицы, **заметки слайдов** (с рекурсией в группы фигур) |
| **XLSX / XLSM** | листы и значения, выгрузка в Markdown-таблицы |
| **HTML / HTM** | текст и таблицы |
| **EPUB** | книга целиком, глава за главой |
| **IPYNB** | markdown-ячейки, код, выводы, ошибки, пометки картинок |
| **TXT / MD / CSV / JSON / YAML** | как есть |

## Чего не умеет — честно

* **сканы** (PDF без текстового слоя) — нужен OCR, здесь его нет; `--info` покажет, есть ли слой;
* **`.doc`, `.odt`, `.rtf`, `.tex`, `.rst`** — нужен pandoc (не подключён);
* **`.xls`** (старый бинарный), **`.dwg`**, **`.msg`**, **аудио и видео**.

На такие файлы инструмент отвечает **явным отказом**, а не «почти сработало».

## Установка

```bash
git clone https://github.com/toposferapro/docs2md.git
cd docs2md
pip install -r requirements.txt
```

Зависимости: `PyMuPDF`, `python-pptx`, `mammoth`, `markdownify`, `EbookLib`, `openpyxl`.
Python 3.10+.

`scripts/html_to_pdf.sh` — необязательный бонус в обратную сторону (HTML → PDF через Chromium);
для него нужен `chrome-headless-shell` или `chromium`.

## Использование

```bash
# один документ в stdout
python3 docs2md.py договор.docx > договор.md

# в файл, с диапазоном страниц для PDF
python3 docs2md.py смета.pdf --pages 1-5 --out смета.md

# презентация целиком
python3 docs2md.py "ЛУЧИ презентация.pptx" --out лучи.md

# пачка файлов в каталог
python3 docs2md.py *.docx *.pdf --out ./markdown/

# что поддержано / прогнать автотесты
python3 docs2md.py --list-formats
python3 docs2md.py --self-test
```

Для PDF отдельно:

```bash
python3 scripts/pdf_to_md.py отчёт.pdf --info          # есть ли текстовый слой
python3 scripts/pdf_to_md.py отчёт.pdf --no-tables     # только текст
```

## Две детали, ради которых это написано

1. **Таблицы из PDF.** Универсальные конвертеры обычно вываливают текст подряд и таблицы теряют:
   на нашем тестовом отчёте популярный конвертер дал **0 таблиц**, а этот извлекает их структурой
   через `page.find_tables()`.
2. **Текст в PPTX лежит внутри групп фигур.** Без рекурсии в группы на презентации из 20 слайдов
   остаётся ~900 знаков вместо ~16 000. Здесь группы разбираются.

Плюс аккуратная чистка Markdown: экранирование вида `07\.09\.2026` и `__жирный__` снимается, но
**код, таблицы и идентификаторы (`__pycache__`, `__init__`) не трогаются**.

## Структура

```
docs2md.py              единая точка входа (разбор по расширению)
scripts/doc_to_md.py    DOCX / HTML / EPUB / IPYNB / XLSX / текстовые
scripts/pdf_to_md.py    PDF: текст и таблицы
scripts/pptx_to_md.py   PPTX: слайды, таблицы, заметки
scripts/html_to_pdf.sh  необязательно: HTML → PDF (Chromium)
tests/test_docs2md.py   автотесты: чистка + конвертация всех форматов
SKILL.md                описание для установки как навык агента
```

## Тесты

```bash
python3 tests/test_docs2md.py
```

27 проверок: 10 на чистку Markdown, 13 на конвертацию форматов, 4 точечных (таблица и текст в PPTX,
жирный текст в DOCX, честный отказ на `.doc`). Тесты собирают тестовые файлы сами — образцов в
репозитории не нужно.

## Происхождение

Собрано для внутренних задач [Топосферы](https://toposfera.pro) — разбора брифов, ТЗ, смет,
презентаций и рыночных исследований в Markdown для дальнейшего анализа. Открыто под MIT: если
пригодится — пользуйтесь.

## Лицензия

MIT — см. [LICENSE](LICENSE).

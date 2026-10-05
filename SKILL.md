---
name: docs2md
description: >
  Разбор рабочих документов в Markdown: PDF (текст и таблицы), DOCX, PPTX (слайды, таблицы,
  заметки), XLSX/XLSM, HTML, EPUB, IPYNB и текстовые форматы (TXT/MD/CSV/JSON/YAML).
  Использовать, когда документ надо превратить в Markdown для дальнейшего анализа — брифинг, ТЗ,
  смета, договор, презентация, рыночное исследование. Сканы не поддержаны (нужен OCR).
---

# docs2md — документы в Markdown

Навык-обёртка над CLI `docs2md.py`. Все инструменты работают от обычного `python3`, без LibreOffice
и pandoc. Каталог навыка держим как `SKILL_DIR` — путь к папке, где лежит этот файл.

## Быстрые команды

```bash
# один документ в Markdown
python3 "${SKILL_DIR}/docs2md.py" "договор.docx" > договор.md

# PDF: сначала сведения (важно для сканов), потом текст с таблицами
python3 "${SKILL_DIR}/scripts/pdf_to_md.py" "смета.pdf" --info
python3 "${SKILL_DIR}/docs2md.py" "смета.pdf" --pages 1-5 > смета.md

# презентация (текст, таблицы, заметки слайдов)
python3 "${SKILL_DIR}/docs2md.py" "презентация.pptx" > презентация.md

# пачка файлов в каталог
python3 "${SKILL_DIR}/docs2md.py" *.docx *.pdf --out ./markdown/

# что поддержано и автотесты
python3 "${SKILL_DIR}/docs2md.py" --list-formats
python3 "${SKILL_DIR}/docs2md.py" --self-test
```

## Правила работы

1. **Сначала `--info`, потом текст.** У PDF бывает только картинка (скан) — тогда текст вернётся
   пустым, и нужен OCR, а не повторные попытки извлечения.
2. **Большие файлы — диапазонами.** `--pages 1-5` вместо выгрузки 500 страниц в контекст.
3. **Ничего не перезаписываем на месте.** Все команды пишут в новый файл или в stdout.
4. **Честный отказ лучше «почти сработало».** `.doc/.odt/.rtf/.tex/.rst` требуют pandoc, сканы — OCR;
   эти случаи называются прямо.
5. **Если правите чистку Markdown** (`clean_markdown` в `scripts/doc_to_md.py`) — сначала прогоните
   `tests/test_docs2md.py`: он держит 27 проверок, включая код, таблицы и идентификаторы `__pycache__`.

## Зависимости

`PyMuPDF`, `python-pptx`, `mammoth`, `markdownify`, `EbookLib`, `openpyxl` — ставятся
`pip install -r requirements.txt`. Chromium нужен только для необязательного `scripts/html_to_pdf.sh`.

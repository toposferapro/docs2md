#!/usr/bin/env python3
"""PDF → Markdown: текст по страницам и таблицы (через PyMuPDF).

Почему свой, а не общий конвертер: PyMuPDF умеет находить **таблицы** и отдавать их структурой,
а текстовые «универсальные» конвертеры обычно просто вываливают текст подряд и таблицы теряют
(проверено: на нашем рыночном исследовании один популярный конвертер дал 0 таблиц, этот — извлёк).

Про сканы: если в PDF нет текстового слоя (страница — картинка), текст вернётся пустым. Это не
поломка: нужен OCR, а его здесь нет — см. `--info`, он показывает, есть ли текстовый слой.

Использование:
    python3 pdf_to_md.py файл.pdf > файл.md
    python3 pdf_to_md.py файл.pdf --pages 1-5 --no-tables
    python3 pdf_to_md.py файл.pdf --info
"""
from __future__ import annotations

import argparse
import sys


def parse_pages(spec: str | None, total: int) -> list[int] | None:
    """'1-5,8' → [1,2,3,4,5,8]. Пусто → None (значит все страницы)."""
    if not spec:
        return None
    pages: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(chunk))
    return [p for p in pages if 1 <= p <= total]


def _table_md(rows: list[list[str | None]]) -> str:
    clean = [[(c or "").replace("\n", " ").strip() for c in row] for row in rows]
    if not clean:
        return ""
    width = max(len(r) for r in clean)
    out: list[str] = []
    for i, row in enumerate(clean):
        cells = row + [""] * (width - len(row))
        out.append("| " + " | ".join(cells) + " |")
        if i == 0:
            out.append("|" + "---|" * width)
    return "\n".join(out)


def to_markdown(path: str, pages: str | None = None, with_tables: bool = True) -> str:
    """PDF → Markdown: по странице заголовок, текст и таблицы."""
    import fitz  # PyMuPDF

    out: list[str] = [f"# {path.split('/')[-1]}", ""]
    with fitz.open(path) as doc:
        total = doc.page_count
        wanted = parse_pages(pages, total) or list(range(1, total + 1))
        out.append(f"_страниц: {total}; в разбор попало: {len(wanted)}_")
        out.append("")
        for p in wanted:
            page = doc[p - 1]
            text = page.get_text().strip()
            out.append(f"## Страница {p}")
            if text:
                out.append(text)
            else:
                out.append("_(текстового слоя нет — вероятно скан, нужен OCR)_")
            if with_tables:
                try:
                    found = page.find_tables()
                except Exception:      # старые версии PyMuPDF без find_tables
                    found = None
                for i, table in enumerate((found.tables if found else []), 1):
                    md = _table_md(table.extract())
                    if md:
                        out.append(f"\n**Таблица {i}**\n")
                        out.append(md)
            out.append("")
    return "\n".join(out).strip() + "\n"


def cmd_info(path: str) -> int:
    import fitz

    with fitz.open(path) as doc:
        print(f"Файл:      {path}")
        print(f"Страниц:   {doc.page_count}")
        print(f"Метаданные: {doc.metadata.get('title') or '—'}")
        print("Текстовый слой (символов по страницам):")
        empty = 0
        for i in range(doc.page_count):
            n = len(doc[i].get_text().strip())
            if n == 0:
                empty += 1
            print(f"  стр. {i + 1:>4}: {n}")
        if empty:
            print(f"⚠️ страниц без текста: {empty} — вероятно сканы, нужен OCR")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="PDF → Markdown (текст и таблицы)")
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="диапазон, например 1-5,8 (по умолчанию все)")
    ap.add_argument("--no-tables", action="store_true", help="не извлекать таблицы")
    ap.add_argument("--info", action="store_true", help="только сведения о файле и текстовом слое")
    ap.add_argument("--out", help="записать в файл вместо stdout")
    args = ap.parse_args()

    if args.info:
        return cmd_info(args.pdf)

    text = to_markdown(args.pdf, pages=args.pages, with_tables=not args.no_tables)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Записано: {args.out} ({len(text)} символов)", file=sys.stderr)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

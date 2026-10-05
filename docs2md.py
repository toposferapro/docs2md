#!/usr/bin/env python3
"""docs2md — рабочие документы в Markdown одной командой.

Поддерживаются: PDF (текст и таблицы), DOCX, PPTX, XLSX/XLSM, HTML, EPUB, IPYNB,
а также текстовые TXT/MD/CSV/JSON/YAML.

Чего нет и почему: сканы (нет OCR), старые .doc/.odt/.rtf/.tex/.rst (нужен pandoc),
.xls, .dwg, .msg, аудио и видео. Эти форматы честно называются неподдержанными —
лучше явный отказ, чем «почти сработало».

Примеры:
    docs2md.py договор.docx                     > договор.md
    docs2md.py презентация.pptx --out дек.md
    docs2md.py смета.pdf --pages 1-5
    docs2md.py папка/*.docx --out ./markdown/   # несколько файлов в каталог
    docs2md.py --list-formats
    docs2md.py --self-test
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))

import doc_to_md      # noqa: E402
import pdf_to_md      # noqa: E402
import pptx_to_md     # noqa: E402

VERSION = "1.0.0"

PDF_EXT = {".pdf"}
PPTX_EXT = {".pptx", ".pptm", ".ppsx"}
SUPPORTED = sorted(set(doc_to_md.DISPATCH) | doc_to_md.PLAIN | PDF_EXT | PPTX_EXT)
UNSUPPORTED = sorted(set(doc_to_md.LEGACY) | {".xls", ".dwg", ".msg", ".mp3", ".wav", ".mp4"})


def convert(path: str, pages: str | None = None, tables: bool = True) -> str:
    """Определить формат по расширению и вернуть Markdown."""
    ext = os.path.splitext(path)[1].lower()
    if ext in PDF_EXT:
        return pdf_to_md.to_markdown(path, pages=pages, with_tables=tables)
    if ext in PPTX_EXT:
        return pptx_to_md.to_markdown(path)
    if ext in doc_to_md.DISPATCH or ext in doc_to_md.PLAIN:
        return doc_to_md.convert(path)
    if ext in doc_to_md.LEGACY:
        raise SystemExit(f"{ext}: не поддержано — нужен pandoc (пока не подключали)")
    raise SystemExit(f"{ext}: формат не поддержан. Список: docs2md.py --list-formats")


def cmd_list_formats() -> int:
    print("Поддержаны:")
    for ext in SUPPORTED:
        print("   ", ext)
    print("\nОбрабатываются как текст (без разбора структуры):")
    print("    .txt .md .csv .json .yaml .yml")
    print("\nНе поддержаны:")
    print("   ", " ".join(UNSUPPORTED))
    print("    (сканы — нет OCR; .doc/.odt/.rtf/.tex/.rst — нужен pandoc)")
    return 0


def cmd_self_test() -> int:
    """Прогнать автотесты пакета, если он установлен из репозитория."""
    test_file = os.path.join(HERE, "tests", "test_docs2md.py")
    if not os.path.isfile(test_file):
        print("тестов рядом нет — запустите tests/test_docs2md.py из репозитория", file=sys.stderr)
        return 2
    import subprocess
    return subprocess.call([sys.executable, test_file])


def main() -> int:
    ap = argparse.ArgumentParser(description="Рабочие документы → Markdown",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("files", nargs="*", help="документы для конвертации")
    ap.add_argument("--out", help="файл (для одного документа) или каталог (для нескольких)")
    ap.add_argument("--pages", help="PDF: какие страницы, например 1-5,8 (по умолчанию все)")
    ap.add_argument("--no-tables", action="store_true", help="PDF: не извлекать таблицы")
    ap.add_argument("--list-formats", action="store_true", help="показать поддержанные форматы")
    ap.add_argument("--self-test", action="store_true", help="прогнать автотесты")
    ap.add_argument("--version", action="version", version=f"docs2md {VERSION}")
    args = ap.parse_args()

    if args.list_formats:
        return cmd_list_formats()
    if args.self_test:
        return cmd_self_test()
    if not args.files:
        ap.print_help()
        return 2

    for path in args.files:
        if not os.path.isfile(path):
            print(f"Нет файла: {path}", file=sys.stderr)
            return 1

    # один файл: stdout или --out как файл
    if len(args.files) == 1 and not (args.out and os.path.isdir(args.out)):
        text = convert(args.files[0], pages=args.pages, tables=not args.no_tables)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"Записано: {args.out} ({len(text)} символов)", file=sys.stderr)
        else:
            print(text, end="")
        return 0

    # несколько файлов: пишем в каталог
    if not args.out:
        print("Для нескольких файлов нужен --out КАТАЛОГ", file=sys.stderr)
        return 2
    os.makedirs(args.out, exist_ok=True)
    done = 0
    for path in args.files:
        try:
            text = convert(path, pages=args.pages, tables=not args.no_tables)
        except SystemExit as exc:
            print(f"  ✗ {os.path.basename(path)}: {exc}", file=sys.stderr)
            continue
        name = os.path.splitext(os.path.basename(path))[0] + ".md"
        target = os.path.join(args.out, name)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"  ✓ {target} ({len(text)} символов)")
        done += 1
    print(f"Готово: {done} из {len(args.files)}")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())

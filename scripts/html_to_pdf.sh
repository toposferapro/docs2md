#!/usr/bin/env bash
# HTML → PDF через Chromium (headless shell): точная вёрстка, кириллица, без офисных пакетов.
#
# Использование:
#   html_to_pdf.sh in.html out.pdf [--landscape] [--margin 12mm] [--paper A4] [--keep-fonts]
#
# Почему headless shell, а не полный chrome: в нашем контейнере полный бинарь падает
# на старте crashpad (`FATAL:...spawn_subproc`), а headless shell рендерит штатно.
# Playwright запускает полный chrome со своими флагами — он рабочий (проверено), но для
# печати из CLI достаточно shell'а и он не требует node.
#
# Если во входном HTML есть свой `@page`, он сохраняется — свои правила не навязываем,
# если только не передан --landscape/--margin/--paper (тогда они добавляются поверх).
set -uo pipefail

IN=${1:-}
OUT=${2:-}
if [ -z "$IN" ] || [ -z "$OUT" ]; then
  echo "Использование: $0 in.html out.pdf [--landscape] [--margin 12mm] [--paper A4]" >&2
  exit 2
fi
shift 2

LANDSCAPE=0
MARGIN="12mm"
PAPER="A4"
FORCE_PAGE_RULE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --landscape) LANDSCAPE=1; FORCE_PAGE_RULE=1 ;;
    --margin)    MARGIN="${2:-12mm}"; FORCE_PAGE_RULE=1; shift ;;
    --paper)     PAPER="${2:-A4}"; FORCE_PAGE_RULE=1; shift ;;
    --keep-fonts) shift ;;
    *) echo "неизвестный флаг: $1" >&2; exit 2 ;;
  esac
  shift
done

[ -f "$IN" ] || { echo "Нет файла: $IN" >&2; exit 1; }
IN_ABS=$(readlink -f "$IN") || exit 1

# 1. Ищем бинарь: сначала headless shell, затем полный chromium, затем системный
BIN=""
for pat in "$HOME"/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell \
           "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux64/chrome \
           /usr/bin/chromium /usr/bin/chromium-browser /usr/bin/google-chrome; do
  # shellcheck disable=SC2086
  cand=$(ls -d $pat 2>/dev/null | sort -V | tail -1)
  if [ -n "${cand:-}" ] && [ -x "$cand" ]; then BIN="$cand"; break; fi
done
[ -n "$BIN" ] || { echo "Chromium не найден. Поставить: см. SKILL.md (Google storage + распаковка в ~/.cache/ms-playwright)" >&2; exit 3; }

# 2. Готовим HTML: если нужны свои @page-правила — делаем копию рядом с исходником
#    (чтобы не поломать относительные картинки/стили), иначе печатаем как есть.
WORK=""
TARGET="$IN_ABS"
cleanup() { [ -n "$WORK" ] && rm -rf "$WORK"; }
trap cleanup EXIT

if [ "$FORCE_PAGE_RULE" = "1" ]; then
  DIR=$(dirname "$IN_ABS")
  if [ -w "$DIR" ]; then
    WORK=$(mktemp -p "$DIR" .html2pdf-XXXXXX.html)
  else
    WORK=$(mktemp -t html2pdf-XXXXXX.html)
    echo "! каталог $DIR недоступен для записи: копия во временном каталоге," >&2
    echo "  относительные картинки и стили из HTML могут не подхватиться" >&2
  fi
  ORIENT="portrait"
  [ "$LANDSCAPE" = "1" ] && ORIENT="landscape"
  {
    printf '<style>@page { size: %s %s; margin: %s; }</style>\n' "$PAPER" "$ORIENT" "$MARGIN"
    cat "$IN_ABS"
  } > "$WORK"
  TARGET="$WORK"
fi

# 3. Печатаем
PROFILE=$(mktemp -d)
OUT_ABS=$(readlink -f "$(dirname "$OUT")")/$(basename "$OUT")
"$BIN" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
      --hide-scrollbars --no-pdf-header-footer --disable-breakpad --disable-crash-reporter \
      --virtual-time-budget=10000 --user-data-dir="$PROFILE" \
      --print-to-pdf="$OUT_ABS" "file://$TARGET" >/tmp/html2pdf.log 2>&1
CODE=$?
rm -rf "$PROFILE"

if [ -s "$OUT_ABS" ]; then
  printf 'Готово: %s (%s)\n' "$OUT_ABS" "$(du -h "$OUT_ABS" | cut -f1)"
  exit 0
fi

echo "Не получилось собрать PDF (код $CODE). Хвост лога Chromium:" >&2
tail -n 5 /tmp/html2pdf.log >&2
exit 4

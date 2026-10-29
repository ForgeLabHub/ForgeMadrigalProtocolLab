#!/usr/bin/env bash
# Проверка окружения. Ничего не устанавливает и не меняет.
set -uo pipefail
PORT_DUMMY="${PORT_DUMMY:-}"
failures=0; warnings=0
ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
bad()  { printf '  \033[31mfail\033[0m  %s\n' "$1"; failures=$((failures+1)); }
warn() { printf '  \033[33mwarn\033[0m  %s\n' "$1"; warnings=$((warnings+1)); }

printf '\nИнтерпретатор\n'
if command -v python3 >/dev/null 2>&1; then
  pv="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  case "$pv" in
    3.12|3.13) ok "python $pv (поддерживается проектом)";;
    *) bad "python $pv: требуется >=3.12 (см. requires-python)";;
  esac
else
  bad "python3 не найден"
fi

printf '\nЗависимости\n'
python3 - <<'PY' 2>/dev/null || warn "зависимости не установлены: make install-dev"
import importlib.util
core = {"dpkt": "чтение захватов", "yaml": "правила"}
missing = [f"{m} ({why})" for m, why in core.items() if not importlib.util.find_spec(m)]
if missing:
    print("  \033[31mfail\033[0m  нет: " + ", ".join(missing))
    raise SystemExit(1)
print("  \033[32mok\033[0m    dpkt, PyYAML установлены")
if importlib.util.find_spec("PySide6"):
    print("  \033[32mok\033[0m    PySide6 установлен — доступны интерфейсные тесты")
else:
    print("  \033[33mwarn\033[0m  PySide6 не установлен — интерфейсные тесты недоступны (make install)")
PY
command -v ruff >/dev/null 2>&1 && ok "ruff" || warn "ruff не найден (make install-dev)"

printf '\nГрафическое окружение\n'
case "${QT_QPA_PLATFORM:-}" in
  offscreen) ok "QT_QPA_PLATFORM=offscreen (тесты без дисплея)";;
  "") if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then ok "дисплей доступен (${DISPLAY:-$WAYLAND_DISPLAY})"; else warn "дисплея нет: для интерфейса задайте QT_QPA_PLATFORM=offscreen"; fi;;
  *) ok "QT_QPA_PLATFORM=$QT_QPA_PLATFORM";;
esac
if [ -e /usr/lib/x86_64-linux-gnu/libEGL.so.1 ] || [ -e /usr/lib64/libEGL.so.1 ]; then
  ok "libEGL доступна"
else
  warn "libEGL не найдена — PySide6 не импортируется (нужен пакет libegl1, libgl1, libxkbcommon0)"
fi

printf '\nИнструменты git\n'
command -v git >/dev/null 2>&1 && ok "git" || bad "git не найден"
[ -f LICENSE ] && ok "LICENSE на месте (MIT)" || warn "нет файла лицензии"

printf '\n'
if [ "$failures" -gt 0 ]; then printf '\033[31m%d проверок провалено\033[0m, предупреждений: %d\n' "$failures" "$warnings"; exit 1; fi
printf '\033[32mГотово к работе\033[0m, предупреждений: %d\n' "$warnings"

#!/usr/bin/env bash
# Проверка документации: обязательные файлы, живые ссылки, полнота спецификаций модулей.
set -uo pipefail
failures=0
ok()  { printf '  \033[32mok\033[0m    %s\n' "$1"; }
bad() { printf '  \033[31mfail\033[0m  %s\n' "$1"; failures=$((failures+1)); }

printf '\nОбязательные документы\n'
required=(
  README.md BUILD.md ARCHITECTURE.md LICENSE
  docs/index.md
  docs/PROJECT_MAP.md docs/CONTRACT.md docs/PORTABILITY.md
  docs/verification/matrix.md
  docs/modules/module-template.md
)
for f in "${required[@]}"; do [ -s "$f" ] && ok "$f" || bad "$f отсутствует или пуст"; done

printf '\nСпецификации модулей\n'
shopt -s nullglob
headings=("Назначение" "Сценарии" "Контракт" "Данные" "Права" "Зависимости" "Конфигурация" "Сборка" "Тесты" "Наблюдаемость" "Ограничения")
count=0; module_ok=1
for m in docs/modules/*.md; do
  case "$m" in *module-template.md) continue ;; esac
  count=$((count+1))
  for h in "${headings[@]}"; do
    if ! grep -qi "$h" "$m"; then bad "$m: нет раздела «$h»"; module_ok=0; fi
  done
done
[ "$count" -gt 0 ] && [ "$module_ok" -eq 1 ] && ok "спецификаций: $count, все с 11 разделами"

printf '\nСсылки\n'
broken=0
while IFS= read -r line; do
  file="${line%%:*}"; target="$(printf '%s' "$line" | sed -n 's/.*](\([^)#]*\).*/\1/p')"
  [ -z "$target" ] && continue
  case "$target" in http*|mailto:*|\#*|/*) continue ;; esac
  base="$(dirname "$file")"
  if [ ! -e "$base/$target" ] && [ ! -e "$target" ]; then bad "$file -> $target (битая ссылка)"; broken=$((broken+1)); fi
done < <(grep -rnoE '\[[^]]*\]\([^)]+\)' --include='*.md' . 2>/dev/null | grep -v '^./presentation/')
[ "$broken" -eq 0 ] && ok "битых относительных ссылок нет"

printf '\nСсылки на чужой аккаунт\n'
if grep -rq "Pavel1778/madrigal-protocol-lab" --include='*.md' --include='*.py' . 2>/dev/null; then
  bad "документация ссылается на прежний адрес репозитория"
else
  ok "ссылки ведут на ForgeLabHub/ForgeMadrigalProtocolLab"
fi

printf '\n'
if [ "$failures" -gt 0 ]; then printf '\033[31m%d проблем в документации\033[0m\n' "$failures"; exit 1; fi
printf '\033[32mДокументация согласована\033[0m\n'

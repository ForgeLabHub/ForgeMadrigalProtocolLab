# Разработка

Рабочие процедуры, которые нужны при изменении кода. Правила веток, коммитов и
ревью — в [CONTRIBUTING](../CONTRIBUTING.md); здесь — то, что приходится делать
руками и что легко забыть.

## Интерфейсные строки и переводы

Исходные строки интерфейса — английские, в вызовах `tr()`. Русский перевод лежит
в `src/ui/locale/madrigal_ru.ts` (источник правды, хранится в git) и собирается в
`src/ui/locale/madrigal_ru.qm` (тоже хранится, чтобы окно работало без
инструментов Qt).

После добавления или изменения любой строки `tr()`:

```
scripts/update_translations.sh
```

Скрипт вызывает `pyside6-lupdate` (обновляет `.ts` на месте, сохраняя уже
переведённые строки) и `pyside6-lrelease` (пересобирает `.qm`).

### Обязательный шаг после обновления каталога

`lupdate` возвращает в каталог записи `type="vanished"` для строк, которые были в
`.ts`, но исчезли из исходников (например, при переформулировке подписи). Такие
записи ломают `tests/ui/test_i18n.py::test_catalogue_has_no_unfinished_translations`,
потому что тест считает незавершёнными всё с типом `unfinished`, `vanished` или
`obsolete`.

После `scripts/update_translations.sh` удалите блоки `<message>`, у которых
`<translation>` помечена `type="vanished"` или `type="unfinished"`, и пересоберите
`.qm`:

```
.venv/bin/pyside6-lrelease src/ui/locale/madrigal_ru.ts -qm src/ui/locale/madrigal_ru.qm
```

Проверка:

```
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_i18n.py -q
```

Файл `.ts` должен содержать только завершённые переводы: `grep -c 'type="unfinished"' src/ui/locale/madrigal_ru.ts` возвращает `0`, как и для
`type="vanished"`.

### Ловушка `self.tr(переменная)`

`lupdate` не извлекает строку, если в `tr()` передана переменная. Строка попадает
в каталог только тогда, когда тот же литерал встречается в вызове
`self.tr("...")`. Всегда используйте литерал.

## Тесты

Полный прогон:

```
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q
```

Изолированные подмножества для быстрой проверки:

```
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ --ignore=tests/ui -q          # без интерфейса
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ --ignore=tests/ui --ignore=tests/web -q
```

### Изоляция состояния интерфейса

Тесты `tests/ui` работают с настоящим `QApplication`, поэтому состояние Qt
переживает границы тестов. `tests/ui/conftest.py` убирает эту зависимость от
порядка:

- `QSettings` перенаправляется во временный каталог, и хранилище очищается перед
  каждым тестом;
- локаль процесса принудительно английская, чтобы `system` разрешалось в `en`;
- установленный `QTranslator` снимается после каждого теста: окно, закрытое с
  выбранным русским языком, может быть собрано сборщиком мусора вместе со своим
  менеджером, и Qt продолжит переводить по каталогу, на который уже никто не
  ссылается.

Новый тест, который переключает язык, не обязан возвращать прежний выбор вручную:
фикстура в `conftest.py` делает это для всего каталога `tests/ui`.

## Линт

```
.venv/bin/ruff check .
```

`ruff format --check` и `mypy` пока не воротятся CI; их состояние зафиксировано в
[docs/AUDIT.md](AUDIT.md). На изменяемых файлах их стоит запускать локально.

## Сборка артефактов

- `scripts/build_linux_binary.sh` — одиночный исполняемый файл (PyInstaller).
- `scripts/build_deb.sh` — пакет `.deb`.
- `scripts/build_submission.py` — архив сдачи из чистого дерева.

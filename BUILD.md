# Сборка: от чистой машины до установленного приложения

Проект заявлен для **Linux x86-64**, Python **>=3.12**. Подробности по форматам
поставки — [docs/INSTALL.md](docs/INSTALL.md) и [docs/BINARY.md](docs/BINARY.md).

## Закреплённые версии

| Инструмент | Версия | Источник истины |
| --- | --- | --- |
| Python | 3.12 и 3.13 (матрица CI) | `pyproject.toml` (`requires-python`), `ci.yml` |
| PySide6 | 6.8.1 | `pyproject.toml` |
| dpkt | 1.9.8 | `pyproject.toml` |
| PyYAML | 6.0.2 | `pyproject.toml` |
| dev-инструменты | pytest 9.0.3, ruff 0.16.10, mypy 2.4.0, pytest-cov 7.1.0, pip-audit 2.10.1 | `[project.optional-dependencies].dev` |
| web-стек | fastapi, uvicorn, jinja2, python-multipart | `[project.optional-dependencies].web` |

Требования `web` и `dev` заданы диапазонами: для воспроизводимости релизного
окружения фиксируйте их через `pip freeze` при сборке артефакта — это осознанный
компромисс (см. [docs/audit/portability-audit-2026-10-29.md](docs/audit/portability-audit-2026-10-29.md)).

## Уровень A — исходный код

```bash
make doctor          # python, dpkt/PyYAML, PySide6, libEGL, QT_QPA_PLATFORM, ruff, LICENSE
make install-dev     # pip install -e ".[dev,web]"
make lint            # ruff
make test-core       # 446 тестов без Qt: protocol, capture, hypothesis (~15 с)
make test-web        # веб-интерфейс
make docs-check
```

Уровень A работает без графической подсистемы: ядро не зависит от Qt.

## Уровень B — артефакты

```bash
make wheel            # dist/*.whl + sdist
make package          # установка wheel в чистый venv и запуск madrigal-lab --help
```

## Уровень C — интерфейс

```bash
make test-ui          # QT_QPA_PLATFORM=offscreen, нужен PySide6 и libEGL
```

На сервере без дисплея интерфейс запускается с `QT_QPA_PLATFORM=offscreen`.

## Уровень D — полный набор тестов

```bash
make test             # все каталоги tests/ (как в CI)
```

## Уровень E — установка на чистую машину

```bash
python -m venv /tmp/venv && . /tmp/venv/bin/activate
pip install dist/*.whl
QT_QPA_PLATFORM=offscreen madrigal-lab --help
```

Форматы поставки (бинарь, `.deb`-подобная раскладка, desktop-файл, установщик) описаны
в [docs/INSTALL.md](docs/INSTALL.md) и `packaging/`.

## Типовые ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| `ImportError: libEGL.so.1` | нет системных библиотек Qt | установить `libegl1 libgl1 libxkbcommon0` |
| `qt.qpa.plugin: could not load the Qt platform plugin "xcb"` | нет дисплея | `QT_QPA_PLATFORM=offscreen` |
| Тесты UI падают на runner | нет PySide6 или locale | матрица CI ставит Qt-библиотеки; локально `make install` |
| `ModuleNotFoundError: src` | запуск без установки пакета | `make install-dev` или `PYTHONPATH=src` |
| `pytest` не находит тесты | не активирован venv | активировать `$(VENV)` |

## Доказательство

`ci.yml` (тесты, интерфейс, качество кода, аудит зависимостей) и
`portability.yml` (упаковка, проверка установки, документация). Матрица утверждений —
[docs/verification/matrix.md](docs/verification/matrix.md).

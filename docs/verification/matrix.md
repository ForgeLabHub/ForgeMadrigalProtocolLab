# Матрица проверок

Проект большой, поэтому «CI зелёный» мало что говорит без расшифровки: ниже —
какие утверждения чем доказаны.

| Утверждение | Проверка | Команда | CI |
| --- | --- | --- | --- |
| Разбор PCAP/PCAPNG не теряет и не выдумывает байты | `tests/capture/*` | `make test-core` | `ci.yml` → `test` |
| Сборка потока устойчива к пропускам, перекрытиям, повторам | `tests/capture/test_reassembly*`, `test_fragmentation`, `test_boundaries` | `make test-core` | `ci.yml` → `test` |
| Каждый байт связан с породившим пакетом (провенанс) | `tests/capture/test_provenance.py` | `make test-core` | `ci.yml` → `test` |
| Правила интерпретации детерминированы и не зависят от данных | `tests/protocol/test_engine.py`, `test_rule.py`, `test_framing.py` | `make test-core` | `ci.yml` → `test` |
| Гипотезы и контрпримеры различимы (наблюдение ≠ вывод) | `tests/hypothesis/*` | `make test-core` | `ci.yml` → `test` |
| Работа на реальном корпусе | `tests/integration/*`, `tests/hypothesis/test_real_corpus.py` | `make test-integration` | `ci.yml` → `test` |
| Отчёт и экспорт воспроизводимы | `tests/report/*`, `tests/integration/test_reference_report.py` | `make test-integration` | `ci.yml` → `test` |
| Проект-контейнер переносим | `tests/project/*` | `make test-integration` | `ci.yml` → `test` |
| Интерфейс не теряет состояние и корректен геометрически | `tests/ui/*` (offscreen) | `make test-ui` | `ci.yml` → `ui-tests` |
| Веб-интерфейс работает | `tests/web/*` | `make test-web` | `ci.yml` → `test` |
| Стиль и статика | `ruff check .` | `make lint` | `ci.yml` → `code-quality` |
| Нет известных уязвимостей в зависимостях | `pip-audit` | — | `ci.yml` → `audit` |
| Собранный wheel устанавливается и запускается | `make package` | `make package` | `portability.yml` → `package` |
| Документация полна и ссылки живые | `make docs-check` | `make docs-check` | `portability.yml` → `docs` |
| Окружение пригодно до запуска | `make doctor` | `make doctor` | локально |

## Что доказывается локально, а что только в CI

| Уровень | Где проверяется |
| --- | --- |
| Ядро без Qt (`make test-core`, 446 тестов) | локально за ~15 с и в CI |
| Веб-интерфейс (`make test-web`) | локально и в CI |
| Интерфейс (`make test-ui`) | только там, где есть PySide6 и системные библиотеки Qt |
| Пакет (`make package`) | локально в venv и в CI |

Локальные тесты ядра выполняются без PySide6, dpkt и PyYAML обязательны.

## Что сознательно не проверяется

- Совпадение английского и русского наборов документации.
- Совместимость с Windows/macOS: проект заявлен для Linux x86-64.
- Производительность на захватах, значительно превышающих корпус.
- Качество гипотез: проверяется непротиворечивость и наличие контрпримеров, а не
  «истинность» протокола.

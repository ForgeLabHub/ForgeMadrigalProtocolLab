# Индекс документации

Точка входа. Документов много (42 в `docs/` и параллельный русский набор в
`docs/ru/`); здесь карта: что читать, когда и что из этого проверяется машиной.

## Если вы здесь впервые

1. [../README.md](../README.md) — что делает инструмент и три инварианта.
2. [PROJECT_MAP.md](PROJECT_MAP.md) — целостная картина за 15 минут.
3. [../BUILD.md](../BUILD.md) — сборка, тесты, артефакты.
4. [verification/matrix.md](verification/matrix.md) — чем доказано, что это работает.

## Карта по вопросам

| Вопрос | Документ |
| --- | --- |
| Что это и как этим пользоваться | [../README.md](../README.md), [USAGE.md](USAGE.md), [demo.md](demo.md), [demo_cli.md](demo_cli.md) |
| Устройство системы | [../ARCHITECTURE.md](../ARCHITECTURE.md), [PROJECT_MAP.md](PROJECT_MAP.md) |
| Почему приняты решения | [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) |
| Контракты форматов и правил | [CONTRACT.md](CONTRACT.md), [PROTOCOL_API.md](PROTOCOL_API.md), [CAPTURE_API.md](CAPTURE_API.md), [schemas/](schemas/) |
| Правила интерпретации v1/v2 | [RULE_V1_V2.md](RULE_V1_V2.md) |
| Корпус и его анализ | [CORPUS_ANALYSIS.md](CORPUS_ANALYSIS.md), [REAL_CORPUS_ANALYSIS.md](REAL_CORPUS_ANALYSIS.md), [DATASET_INVESTIGATION.md](DATASET_INVESTIGATION.md), [REFERENCE_INVESTIGATION.md](REFERENCE_INVESTIGATION.md) |
| Метрики и бенчмарки | [METRICS.md](METRICS.md), [BENCHMARK.md](BENCHMARK.md) |
| Веб-интерфейс | [WEB.md](WEB.md) |
| Интерфейс и его проверки | [UI_TESTING.md](UI_TESTING.md), [GUI_VERIFICATION.md](GUI_VERIFICATION.md), [UX_COHERENCE_PLAN.md](UX_COHERENCE_PLAN.md) |
| Установка и артефакты | [INSTALL.md](INSTALL.md), [BINARY.md](BINARY.md) |
| Переносимость | [PORTABILITY.md](PORTABILITY.md) |
| Настройки | [SETTINGS.md](SETTINGS.md) |
| Стиль и разработка | [STYLE.md](STYLE.md), [DEVELOPMENT.md](DEVELOPMENT.md), [GIT_HYGIENE.md](GIT_HYGIENE.md) |
| Границы проекта | [BEYOND_SCOPE.md](BEYOND_SCOPE.md) |
| Аудит и соответствие | [AUDIT.md](AUDIT.md), [STACK_COMPLIANCE.md](STACK_COMPLIANCE.md), [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) |
| Защита и демонстрация | [DEFENSE_CHECKLIST.md](DEFENSE_CHECKLIST.md), [DEFENSE_FAQ.md](DEFENSE_FAQ.md), [DEMO_CHEATSHEET.md](DEMO_CHEATSHEET.md), [FAQ_FOR_JUDGES.md](FAQ_FOR_JUDGES.md), [PRESENTATION_VERIFICATION.md](PRESENTATION_VERIFICATION.md), [SUBMISSION.md](SUBMISSION.md) |
| Планы и прогресс | [ROADMAP.md](ROADMAP.md), [../PROGRESS.md](../PROGRESS.md), [../CHANGELOG.md](../CHANGELOG.md) |
| Спецификации модулей | [modules/](modules/) |
| Сборка и проверки | [../BUILD.md](../BUILD.md), [verification/matrix.md](verification/matrix.md) |

## Два языка

`docs/*.md` — английский набор, `docs/ru/*.md` — русский. Правило: изменение
контракта или поведения обновляет **оба** набора. Расхождение языков не проверяется
автоматически — это известное ограничение (см.
[verification/matrix.md](verification/matrix.md)).

## Правила

1. Документ, утверждающий поведение, должен иметь строку в
   [verification/matrix.md](verification/matrix.md).
2. Новый модуль описывается по [modules/module-template.md](modules/module-template.md);
   наличие 11 разделов проверяет `make docs-check`.
3. Ссылки только на актуальный адрес репозитория
   (`ForgeLabHub/ForgeMadrigalProtocolLab`); проверяется `make docs-check`.

## Управление проектом

- `forge.sh` / `forge.bat` — запуск, остановка, логи, тесты, база и контейнеры одной командой; см. раздел в README.

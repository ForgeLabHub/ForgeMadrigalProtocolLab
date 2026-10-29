# Madrigal Protocol Lab — единая точка входа.
#
# Особенность проекта: интерфейс требует Qt, поэтому тесты разделены на ядро
# (без Qt, быстро) и интерфейс (offscreen, требует PySide6 и системные библиотеки).
# Это разделение и есть переносимость: ядро проверяется на любой машине и в CI
# без графических зависимостей.

SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV   ?= .venv
DIST   ?= dist

.PHONY: help doctor venv install install-dev test test-core test-ui test-web lint \
        build wheel package docs-check verify clean

help: ## Список целей
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

doctor: ## Проверить инструменты, Qt и окружение (ничего не меняет)
	@./scripts/doctor.sh

venv: ## Создать виртуальное окружение
	$(PYTHON) -m venv $(VENV)
	@echo "активируйте: source $(VENV)/bin/activate"

install: ## Установить пакет (десктоп)
	$(PYTHON) -m pip install -e .

install-dev: ## Установить пакет с dev- и web-зависимостями
	$(PYTHON) -m pip install -e ".[dev,web]"

## --- Проверки -------------------------------------------------------------

test-core: ## Ядро без Qt: protocol, capture, hypothesis (быстро)
	PYTHONPATH=src $(PYTHON) -m pytest tests/protocol tests/capture tests/hypothesis -q

test-web: ## Веб-интерфейс (без Qt)
	PYTHONPATH=src $(PYTHON) -m pytest tests/web -q

test-ui: ## Интерфейс, offscreen (нужен PySide6)
	QT_QPA_PLATFORM=offscreen PYTHONPATH=src $(PYTHON) -m pytest tests/ui -q

test-integration: ## Интеграционные проверки корпуса и отчётов
	PYTHONPATH=src $(PYTHON) -m pytest tests/integration tests/report tests/project -q

test: ## Все тесты (как в CI)
	QT_QPA_PLATFORM=offscreen PYTHONPATH=src $(PYTHON) -m pytest tests -q

lint: ## ruff
	$(PYTHON) -m ruff check .

## --- Артефакты ------------------------------------------------------------

wheel: ## Собрать wheel и sdist
	$(PYTHON) -m pip install -q build
	$(PYTHON) -m build --outdir $(DIST)
	@ls -la $(DIST)

build: wheel ## То же, что wheel

package: wheel ## Проверить, что собранный wheel устанавливается и запускается
	$(PYTHON) -m venv /tmp/madrigal-package-check
	/tmp/madrigal-package-check/bin/pip install -q "$(DIST)"/*.whl
	QT_QPA_PLATFORM=offscreen /tmp/madrigal-package-check/bin/madrigal-lab --help

docs-check: ## Проверить документацию, ссылки и спецификации модулей
	@./scripts/docs-check.sh

verify: lint test-core test-web docs-check ## Локальная матрица без Qt
	@echo "verify: ok (интерфейсные и интеграционные тесты — в CI)"

clean: ## Удалить артефакты
	rm -rf $(DIST) build *.egg-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

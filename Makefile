.DEFAULT_GOAL := help

# Команда uv (можно переопределить: make UV=uvx ...)
UV ?= uv
# Список доступных лабораторных (имена модулей без расширения), отсортированный
LABS := $(sort $(patsubst labs/%.py,%,$(wildcard labs/lab*.py)))
# Имя лабораторной, переданное после `run` (например, `make run lab01`)
RUN_ARGS := $(filter-out run,$(MAKECMDGOALS))
# Go-модули (каталоги с go.mod внутри src/golang)
GO_MODULES := $(sort $(dir $(wildcard src/golang/*/go.mod)))

# $(call go_foreach,<команда>) — выполнить команду в каждом Go-модуле, упав на первой ошибке
define go_foreach
@for m in $(GO_MODULES); do echo "==> $$m"; (cd $$m && $(1)) || exit 1; done
endef

.PHONY: help sync test cov run clean docs docs-build \
        go go-build go-vet go-test go-fmt check

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

sync: ## Установить зависимости
	$(UV) sync

test: ## Запустить тесты (pytest)
	$(UV) run pytest -v

cov: ## Тесты с отчётом покрытия (как в CI)
	$(UV) run pytest --cov --cov-report=term-missing

run: ## Запустить лабораторную (make run lab01) или показать список (make run)
ifeq ($(RUN_ARGS),)
	@echo "Доступные лабораторные работы:"
	@for lab in $(LABS); do echo "  $$lab"; done
	@echo ""
	@echo "Запуск: make run lab01"
else ifeq ($(filter $(RUN_ARGS),$(LABS)),)
	@echo "Лабораторная '$(RUN_ARGS)' не найдена. Доступные:"
	@for lab in $(LABS); do echo "  $$lab"; done
	@exit 1
else
	$(UV) run python -m labs.$(RUN_ARGS)
endif

# Перехватываем имена лабораторных, переданные как цели, чтобы make не ругался.
lab%:
	@:

docs: ## Запустить локальный сервер документации (http://127.0.0.1:8000)
	$(UV) run --group docs mkdocs serve

docs-build: ## Собрать статический сайт документации в site/
	$(UV) run --group docs mkdocs build --strict

go: go-build go-vet go-test ## Собрать, проверить и протестировать все Go-модули

go-build: ## Собрать все Go-модули (src/golang/*)
	$(call go_foreach,go build ./...)

go-vet: ## Прогнать go vet по всем Go-модулям
	$(call go_foreach,go vet ./...)

go-test: ## Прогнать go test по всем Go-модулям
	$(call go_foreach,go test ./...)

go-fmt: ## Отформатировать Go-код (gofmt -w) во всех модулях
	$(call go_foreach,gofmt -w .)

check: cov go docs-build ## Полная проверка перед пушем: покрытие + Go + strict-сборка docs

clean: ## Удалить кэш и временные файлы
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf site
	rm -f .coverage coverage.xml junit.xml

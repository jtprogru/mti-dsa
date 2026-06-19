.DEFAULT_GOAL := help

# Команда uv (можно переопределить: make UV=uvx ...)
UV ?= uv
# Список доступных лабораторных (имена модулей без расширения), отсортированный
LABS := $(sort $(patsubst src/python/labs/%.py,%,$(wildcard src/python/labs/lab*.py)))
# Имя лабораторной, переданное после `py-run` (например, `make py-run lab01`)
RUN_ARGS := $(filter-out py-run,$(MAKECMDGOALS))
# Go-модули (каталоги с go.mod внутри src/golang)
GO_MODULES := $(sort $(dir $(wildcard src/golang/*/go.mod)))

# $(call go_foreach,<команда>) — выполнить команду в каждом Go-модуле, упав на первой ошибке
define go_foreach
@for m in $(GO_MODULES); do echo "==> $$m"; (cd $$m && $(1)) || exit 1; done
endef

.PHONY: help sync test py-test py-run cov py-cov go-cov clean docs docs-build \
        go go-build go-vet go-test go-fmt check

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

sync: ## Установить зависимости
	$(UV) sync

test: py-test go-test ## Прогнать все тесты (Python + Go)

py-test: ## Прогнать Python-тесты (pytest)
	$(UV) run pytest -v

cov: py-cov go-cov ## Покрытие всех тестов (Python + Go)

py-cov: ## Python-покрытие (pytest --cov, как в CI)
	$(UV) run pytest --cov --cov-report=term-missing

go-cov: ## Go-покрытие: итоговый процент statements по каждому модулю
	@for m in $(GO_MODULES); do \
		printf '==> %-22s ' "$$m"; \
		( cd $$m && go test -coverprofile=cover.out ./... >/dev/null 2>&1 \
			&& go tool cover -func=cover.out | awk 'END {print $$NF}'; \
			st=$$?; rm -f cover.out; exit $$st ) \
		|| { echo "FAIL (см. make go-test)"; exit 1; }; \
	done

py-run: ## Запустить Python-лабораторную (make py-run lab01) или показать список (make py-run)
ifeq ($(RUN_ARGS),)
	@echo "Доступные Python-лабораторные работы:"
	@for lab in $(LABS); do echo "  $$lab"; done
	@echo ""
	@echo "Запуск: make py-run lab01"
else ifeq ($(filter $(RUN_ARGS),$(LABS)),)
	@echo "Лабораторная '$(RUN_ARGS)' не найдена. Доступные:"
	@for lab in $(LABS); do echo "  $$lab"; done
	@exit 1
else
	PYTHONPATH=src/python $(UV) run python -m labs.$(RUN_ARGS)
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

check: py-cov go docs-build ## Полная проверка перед пушем: Python-покрытие + Go + strict-сборка docs

clean: ## Удалить кэш и временные файлы
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf site
	rm -f .coverage coverage.xml junit.xml
	find src/golang -name cover.out -delete

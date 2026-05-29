.DEFAULT_GOAL := help

LAB ?= 01

.PHONY: help sync test run clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

sync: ## Установить зависимости
	uv sync

test: ## Запустить тесты
	uv run pytest -v

run: ## Запустить лабораторную (make run LAB=01)
	uv run python -m labs.lab$(LAB)

clean: ## Удалить кэш и временные файлы
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +

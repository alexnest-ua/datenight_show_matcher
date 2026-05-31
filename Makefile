# DateNight Show Matcher — developer convenience targets.
# Backend runs in a local venv; frontend uses bun.

VENV := backend/.venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip
BIN  := $(VENV)/bin
BUN  := $(HOME)/.bun/bin/bun
HANDLE ?= @art_girl

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[1m%-16s\033[0m %s\n", $$1, $$2}'

install: install-backend install-frontend ## Install backend (venv) + frontend (bun)

install-backend: ## Create venv and install the backend (editable, with dev extras)
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -e "backend[dev]"

install-frontend: ## Install frontend dependencies
	cd frontend && $(BUN) install

cli: ## Run the CLI: make cli HANDLE=@tech_babe
	$(BIN)/get-show $(HANDLE)

serve: ## Run the FastAPI + SSE backend on :8000
	$(BIN)/datenight serve

mcp: ## Run the MCP server on stdio (for inspection)
	$(BIN)/datenight mcp-server

seed: ## (Re)build the SQLite catalog
	$(BIN)/datenight seed-db --force

fixtures: ## Record offline demo fixtures into frontend/src/demo/
	$(BIN)/datenight demo-fixtures

info: ## Show resolved config / mode
	$(BIN)/datenight info

test: ## Run the backend test-suite
	$(BIN)/pytest -q backend/tests

lint: ## Ruff lint the backend
	$(BIN)/ruff check backend/app

web-dev: ## Run the Vite dev server (proxies /api to :8000)
	cd frontend && $(BUN) run dev

web-build: ## Build the static frontend into frontend/dist
	cd frontend && $(BUN) run build

up: ## docker compose up (web on :8080, backend on :8000)
	docker compose up --build

down: ## docker compose down
	docker compose down

demo: up ## Alias for `up` — the full local demo

.PHONY: help install install-backend install-frontend cli serve mcp seed fixtures \
        info test lint web-dev web-build up down demo

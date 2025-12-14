PYTHON ?= python3
VENV ?= .venv
UVICORN ?= $(VENV)/bin/uvicorn
PIP ?= $(VENV)/bin/pip
ALEMBIC ?= $(VENV)/bin/alembic
DEV_REQ ?= backend/requirements-dev.txt

.PHONY: venv install-backend install-dev run-api dev-up dev-down dev-up-all lint format test migrate-up migrate-down

venv:
	$(PYTHON) -m venv $(VENV)

install-backend: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

install-dev: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r $(DEV_REQ)

run-api: install-backend
	AIDOC_ENVIRONMENT=development $(UVICORN) app.main:app --reload --app-dir backend

dev-up:
	docker compose up -d postgres qdrant minio

dev-down:
	docker compose down

dev-up-all:
	docker compose up -d

lint: install-dev
	$(VENV)/bin/ruff check backend

format: install-dev
	$(VENV)/bin/ruff format backend
	$(VENV)/bin/black backend

test: install-dev
	AIDOC_ENVIRONMENT=test $(VENV)/bin/pytest

migrate-up: install-dev
	cd backend && AIDOC_DATABASE_URL=$${AIDOC_DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/ai_docs} $(ALEMBIC) upgrade head

migrate-down: install-dev
	cd backend && AIDOC_DATABASE_URL=$${AIDOC_DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/ai_docs} $(ALEMBIC) downgrade -1

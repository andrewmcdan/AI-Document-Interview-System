PYTHON ?= python3
VENV ?= .venv
UVICORN ?= $(VENV)/bin/uvicorn
PIP ?= $(VENV)/bin/pip

.PHONY: venv install-backend run-api dev-up dev-down

venv:
	$(PYTHON) -m venv $(VENV)

install-backend: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

run-api: install-backend
	AIDOC_ENVIRONMENT=development $(UVICORN) app.main:app --reload --app-dir backend

dev-up:
	docker-compose up -d postgres qdrant minio

dev-down:
	docker-compose down

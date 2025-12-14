# AI Document Interview System

Scaffold for the MVP described in the project overview PDF. The system ingests user documents, embeds chunked text, and answers natural language questions with grounded citations.

## Repository Layout
- `backend/`: FastAPI application with ingestion and retrieval placeholders.
  - `app/core/`: configuration via Pydantic settings.
  - `app/api/routes/`: document, query, and health endpoints.
  - `app/services/`: OpenAI wrapper plus ingestion/retrieval services.
  - `app/storage/`: S3 object store + Qdrant vector store helpers.
  - `app/db/`: SQLAlchemy async session factory and models for documents and chunks.
  - `requirements.txt` and `.env.example` for local setup.
- `docs/ARCHITECTURE.md`: distilled notes from the PDF.
- `frontend/`: placeholder; fill in with Next.js/Vite client when ready.
- `docker-compose.yml`: Postgres, Qdrant, MinIO, and the API service.
- `Makefile`: quick tasks for creating a venv, installing backend deps, running the API, and bringing up infra.

## Quickstart
```bash
# start databases and storage
make dev-up
# (or dev-up-all to include the API container)

# install backend deps into .venv and run the API (default port 8000)
make run-api

# for development tooling (lint/format/tests/migrations)
make install-dev
```

Configure environment variables via `backend/.env.example`. Update `AIDOC_DATABASE_URL`, `AIDOC_OPENAI_API_KEY`, and storage endpoints as needed.
Storage options:
- Default S3/MinIO (`AIDOC_STORAGE_BACKEND=s3` with `AIDOC_S3_*` settings).
- Local filesystem: set `AIDOC_STORAGE_BACKEND=local` and `AIDOC_LOCAL_STORAGE_PATH` (uploads will be stored under that directory).

Database setup:
- In development, tables auto-create on startup (see `backend/app/db/models.py`).
- Alembic is configured in `backend/alembic`; run `make migrate-up` (or `migrate-down`) with `AIDOC_DATABASE_URL` set.

Ingestion notes:
- Supported formats: PDF, DOCX, TXT. PDF extraction falls back to OCR (requires `tesseract` binary + Pillow).
- Text is normalized (strip repeated headers/footers, dedupe lines) before chunking.
- Chunking is token-aware via `tiktoken` with configurable size/overlap; page and token offsets and snippets are stored in chunk metadata.
- OCR note: install `tesseract-ocr` locally; the API Docker image installs Tesseract/Poppler, so OCR works inside `docker-compose`.
- Ingestion jobs: uploads create `ingestion_jobs` records (status pending/running/completed/failed); poll `GET /ingestion_jobs` or `/ingestion_jobs/{id}/status`.

Health endpoints:
- `/health` basic heartbeat
- `/ready` checks DB, Qdrant, object storage, and OpenAI connectivity

Query options:
- `document_ids` (optional) to restrict retrieval to specific documents.
- `min_score` (optional) to drop low-confidence vector hits.
- `user_id` (optional) to scope retrieval to a user (expects owner_id on documents/chunks).

Conversation support:
- `/query` and `/conversations/{id}/query` log messages to conversations/messages tables; new conversations are created automatically when no ID is supplied.
- Conversation APIs: `GET /conversations?user_id=...`, `GET /conversations/{id}`, `GET /conversations/{id}/messages`.
- Query logs: `GET /query_logs?user_id=...` (logs are appended automatically on queries).

Auth note: requests require `X-User-Id` header for scoping documents, conversations, query logs, and retrievals. Replace with real auth/JWT in production.
Auth (current behavior):
- Preferred: `Authorization: Bearer <JWT>` signed with `AIDOC_AUTH_SECRET` (HS256; `aud` optional). Uses `sub` as user ID.
- Dev fallback: if `AIDOC_AUTH_SECRET` is unset, you can send `X-User-Id` for scoping. Remove this in production.

## Dev scripts
- `make lint` – ruff check
- `make format` – ruff format + black
- `make test` – pytest (sets `AIDOC_ENVIRONMENT=test`)
- `make migrate-up` / `make migrate-down` – Alembic migrations using `AIDOC_DATABASE_URL`
- Upload limits: accepts PDF/DOCX/TXT; rejects files over 25MB and unsupported MIME types.

## Next Steps
- Implement text extraction (PDF/DOCX + OCR fallback) and chunking in `app/services/ingestion.py`.
- Define database models/migrations for users, documents, chunks, conversations, and query logs.
- Flesh out retrieval prompt building and citation formatting in `app/services/retrieval.py`.
- Connect API routes to persistence (Postgres) and background workers for long-running ingestion.
- Stand up the frontend client to handle uploads, chat flows, and citation display.

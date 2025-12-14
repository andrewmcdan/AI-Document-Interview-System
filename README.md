# AI Document Interview System

This is an end-to-end “document interview” stack: you upload handbooks/policies, we extract/normalize/chunk and embed them, then you can query or run deep analysis with grounded citations. It includes:
- FastAPI backend with background ingestion jobs, retrieval, conversations, streaming chat, and deep analysis across documents.
- Next.js frontend for uploads (with AI metadata), chat with conversation history, and an analysis page to find common themes across docs.
- Qdrant for vector search, Postgres for metadata, and S3/MinIO or local storage for files.

## Repository Layout
- `backend/`: FastAPI app (ingestion, retrieval, conversations, analysis, auth).
  - `app/api/routes/`: documents, ingestion_jobs, query (+ streaming), conversations, query_logs, analysis, auth, admin reset, health.
  - `app/services/`: ingestion pipeline, retrieval, analysis, OpenAI wrapper.
  - `app/storage/`: S3/local object store + Qdrant vector store helpers.
  - `app/db/`: async SQLAlchemy session + models (documents, chunks, ingestion_jobs, conversations/messages, query_logs, analysis_jobs).
  - `requirements*.txt`, `.env.example` for local setup.
- `frontend/`: Next.js app with upload (batch + AI metadata), chat (streaming, conversations, doc filters), analysis page, documents list, login, admin reset.
- `docs/ARCHITECTURE.md`: notes from the PDF.
- `docker-compose.yml`: Postgres, Qdrant, MinIO, and API service.
- `Makefile`: quick tasks for venv, backend deps, API, and local infra.

## Quickstart
```bash
# start databases and storage
make dev-up
# (or dev-up-all to include the API container)

# install backend deps into .venv and run the API (default port 8000)
make run-api

# for development tooling (lint/format/tests/migrations)
make install-dev

# frontend
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_BASE_URL (default http://localhost:8000)
npm run dev

# or run everything in docker (api + frontend + deps)
docker compose up --build
```

Configure environment variables via `backend/.env.example`. Update `AIDOC_DATABASE_URL`, `AIDOC_OPENAI_API_KEY`, storage backend, and auth secret as needed.
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

### API surface (high level)
- Upload: `POST /documents` (background ingestion job), `GET /ingestion_jobs`, `GET /ingestion_jobs/{id}/status`, soft-delete `/documents/{id}`.
- Query: `POST /query` and `/query/stream`; conversation-scoped: `POST /conversations/{id}/query` and `/conversations/{id}/query/stream`.
- Conversations: `GET /conversations`, `GET /conversations/{id}`, `GET /conversations/{id}/messages`, `PATCH /conversations/{id}/title`.
- Analysis: `POST /analysis` to start deep analysis (background job), `GET /analysis`, `GET /analysis/{id}`.
- Health: `/health`, `/ready` (checks DB, Qdrant, object storage, OpenAI).
- Admin: `/admin/reset` (dev-only purge of DB/vector/object storage).
- Auth: `/auth/login` (demo JWT signer).

### Auth
- Preferred: `Authorization: Bearer <JWT>` signed with `AIDOC_AUTH_SECRET` (HS256; `sub` used as user ID; `aud` optional).
- Dev fallback: if no secret is set, use `X-User-Id`. Remove in production.

### Frontend pages
- `/login`: get a demo JWT.
- `/upload`: batch upload, AI metadata suggestion, auto job polling.
- `/documents`: list docs.
- `/chat`: conversations, streaming answers, doc filters, inline title editing.
- `/analysis`: start/poll deep analysis jobs and view themes/answer.
- `/admin`: dev reset.

## Dev scripts
- `make lint` – ruff check
- `make format` – ruff format + black
- `make test` – pytest (sets `AIDOC_ENVIRONMENT=test`)
- `make migrate-up` / `make migrate-down` – Alembic migrations using `AIDOC_DATABASE_URL`
- Upload limits: accepts PDF/DOCX/TXT; rejects files over 25MB and unsupported MIME types.

---
This entire project was authored with OpenAI’s Codex via VS Code, with guidance and troubleshooting by Andrew McDaniel.

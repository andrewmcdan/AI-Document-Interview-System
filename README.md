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
- `docker-compose.yml`: Postgres, Qdrant, and MinIO for local dev.
- `Makefile`: quick tasks for creating a venv, installing backend deps, running the API, and bringing up infra.

## Quickstart
```bash
# start databases and storage
make dev-up

# install backend deps into .venv and run the API (default port 8000)
make run-api
```

Configure environment variables via `backend/.env.example`. Update `AIDOC_DATABASE_URL`, `AIDOC_OPENAI_API_KEY`, and storage endpoints as needed.

Create the Postgres tables before running locally (models live in `backend/app/db/models.py`); add Alembic migrations or call `Base.metadata.create_all` during bootstrap in early development.

## Next Steps
- Implement text extraction (PDF/DOCX + OCR fallback) and chunking in `app/services/ingestion.py`.
- Define database models/migrations for users, documents, chunks, conversations, and query logs.
- Flesh out retrieval prompt building and citation formatting in `app/services/retrieval.py`.
- Connect API routes to persistence (Postgres) and background workers for long-running ingestion.
- Stand up the frontend client to handle uploads, chat flows, and citation display.

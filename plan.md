# AI Document Interview System – Plan

## MVP

### Backend & Data Layer
- Finalize ORM models (users, query logs, upload jobs, retry states) and add Alembic migrations for them.
- [x] Add DB bootstrap hook to create collections/tables in dev (auto-create at startup); seed minimal demo data (pending).
- [x] Alembic set up with migrations for documents/chunks, conversations/messages, query logs, and ingestion jobs.
- Hard-delete path implemented for documents (DB/Qdrant/S3). Implement soft-delete retention/cleanup if needed.

### Ingestion Pipeline
- [x] Add format detection and handlers (PDF, DOCX, TXT).
- [x] Add fallback OCR for scanned PDFs via Tesseract/Poppler (requires Tesseract binary installed).
- [x] Add Tesseract dependency to local/dev containers for reliable OCR.
- [x] Implement text normalization with repeated header/footer stripping and line de-dupe.
- [x] Replace word-split chunking with token-aware splitter (tiktoken); tune size/overlap; store page/offset metadata.
- [x] Move ingestion to a FastAPI background task and return job status; still consider external worker/queue for large jobs and retries.
- Handle large files/streams, virus scanning stub, and upload size limits.
- Add re-chunk/re-embed workflow for model upgrades or parameter changes.
- Add ingestion job tracking (status table, retries) and API to poll progress.
- [x] Provide local filesystem storage option alongside S3/MinIO.
- [x] Add AI-assisted document metadata suggestion endpoint (title/description from file text).

### Retrieval & QA
- [x] Build basic retrieval path: embed query, search Qdrant, and assemble grounded prompt with citations.
- [x] Add document filters and min-score thresholding for retrieval requests.
- [x] Add user filters for retrieval requests (uses user_id on QueryRequest).
- [x] Dedupe overlapping chunks to reduce prompt noise; per-user/org score thresholds still TBD.
- [x] Design initial grounded prompt template with citation tags and “I don’t know” fallback; refine style later.
- Support conversation context (carry prior turns) and session persistence.
- Add streaming responses (Server-Sent Events) and error handling for OpenAI timeouts/rate limits.

### API Surface & Auth
- [x] Wire CRUD for documents/conversations/query logs; paginate lists.
- [x] Add JWT-based auth (HS256) with dev fallback; enforce per-user scoping across documents, conversations, query logs, and retrieval.
- [x] Validate uploads (MIME/type/size), and add request/response models with proper error codes.
- [x] Add health/ready endpoints that check DB, Qdrant, S3, and OpenAI connectivity.
- [x] Add request ID middleware and CORS configuration for frontend integration.
- [x] Add conversation listing/fetch endpoints; add query log retrieval (conversation portion done; query logs pending).

### Observability & Ops
- Instrument logging/metrics (structlog + OpenTelemetry); capture latencies, token usage, and retrieval stats.
- Persist query logs with request/response, retrieved chunks, scores, and costs; add admin view/export.
- Add rate limiting and request IDs; enable CORS config.
- [x] Expand `docker-compose` with API service.
- [x] Add Make targets for lint/format/test/migrations; optional Tesseract dependency still pending.
- [x] Query logs persisted and list endpoint added.
- [x] Add structured logging for requests/ingestion; metrics still pending.
- Add structured logging and request IDs in logs; add basic metrics (latency, error counts).

### Testing & Quality
- Add unit tests for ingestion (extraction, chunking), retrieval prompt building, and OpenAI wrappers (with fakes).
- Add integration tests against local Postgres/Qdrant/MinIO (using docker compose) and contract tests for APIs.
- Lint/format tooling (ruff/black/mypy) and CI workflow.

### Frontend
- Choose stack (Next.js or Vite+React) and scaffold: auth gate, document uploader, document list, chat view with citations, history sidebar.
- [x] Scaffold basic frontend (Next.js) with upload, job status polling, chat, and document selection.
- [x] Add demo login to obtain JWT via `/auth/login`; shared auth state.
- [x] Implement upload status with auto-polling until ingestion completes/fails (added batch upload + per-job refresh).
- [x] Add AI-assisted title/description suggestion on upload.
- [x] Add conversation history view, streaming answers, and ability to continue a thread.
- Enhance chat UI with source snippets, citation chips, and doc filters; add typing/streaming indicator (streaming done; citations/filters partially).
- Add document list filters/pagination and easy copy of IDs for chat filters.
- [x] Improve layout/theming for readability and responsiveness; ensure request IDs/dev headers handled.
- [x] Add admin reset screen for dev purge workflow.
- Add toast/error banners and inline progress on uploads.
- [x] Add AI-suggested conversation titles and inline title editing.

## Future Plans
- External worker/queue (Celery/RQ/Arq) for ingestion with retries and large files; virus scanning stub.
- Re-chunk/re-embed workflow for model upgrades; versioned embeddings.
- Conversation context persistence and streaming responses (SSE/WebSockets).
- Soft-delete retention policies and background cleanup for documents/chunks/storage.
- Rate limiting and abuse protection.
- Metrics and tracing via OpenTelemetry; token/cost tracking.
- Secrets management (vault/SSM), audit logging, and PII handling guidance.
- S3 bucket policies, signed URL expirations, encryption at rest.
- Dependency scanning/vulnerability management.
- Frontend enhancements: richer upload progress, error toasts, source previews, mobile polish, streaming display, request signing headers.

## Deep Analysis (Proposed)
- New Analysis jobs: background workflow to answer open-ended aggregations (e.g., “common rules across all handbooks”).
- API: POST `/analysis` to start (task type, doc filters, budgets), GET `/analysis/{id}` for status/result. Persist themes with citations.
- Pipeline: retrieve larger chunk sets per doc; map step extracts per-doc key bullets with citations; reduce step dedupes/merges themes and returns consolidated list with supporting doc IDs/chunk IDs.
- Controls: chunk/token budget caps, max themes, strict-citation prompts, optional coverage reporting (which docs mention or omit a theme).
- Frontend: “Analysis” page to select docs, start an analysis job, poll status, and render themes with citations and supporting docs. Reuse ingestion-job style polling.

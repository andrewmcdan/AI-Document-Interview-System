# Frontend Placeholder

Minimal Next.js frontend scaffolded for integration testing.

## Setup
```bash
cd frontend
npm install
# or: pnpm install / yarn install
cp .env.example .env.local  # adjust NEXT_PUBLIC_API_BASE_URL as needed
npm run dev
```

## Pages
- `/upload`: upload a document (with JWT or dev user header), view returned ingestion job id, and refresh job status.
- `/chat`: send questions (optionally filtered to document IDs), view answers and citations.

## Auth
- Preferred: `Authorization: Bearer <JWT>` (HS256, `sub` used as user ID).
- Dev fallback: `X-User-Id` when JWT is not set and backend allows it.

No dependencies are installed yet; scaffold once the desired frontend stack is chosen.

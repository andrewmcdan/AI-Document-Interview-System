# Frontend (Next.js)

MVP client for uploads, chat, and deep analysis.

## Setup
```bash
cd frontend
npm install
# or: pnpm install / yarn install
cp .env.example .env.local  # adjust NEXT_PUBLIC_API_BASE_URL as needed
npm run dev
```

## Pages
- `/login`: get a demo JWT from the backend (`/auth/login`).
- `/upload`: batch upload with AI-suggested title/description, background ingestion jobs with auto-polling.
- `/documents`: list your documents/IDs.
- `/chat`: conversations with streaming answers, doc filters, inline title editing (AI-suggested), and sources.
- `/analysis`: start/poll deep analysis jobs across selected docs; view answers/themes.
- `/admin`: dev-only purge reset.

## Auth
- Preferred: `Authorization: Bearer <JWT>` (HS256, `sub` used as user ID).
- Dev fallback: `X-User-Id` when JWT is not set and backend allows it.

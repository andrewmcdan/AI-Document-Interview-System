from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import documents, health, query
from app.api.routes import conversations, query_logs, ingestion_jobs, auth, admin
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.session import init_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Initialize database tables on startup in development.
    if settings.environment.lower() in {"development", "local"}:
        await init_models(settings.database_url)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging()
    log = get_logger()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # Simple request ID middleware
    class RequestIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            request.state.request_id = request_id
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

    class LoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            log.info("request.start", method=request.method, path=request.url.path)
            response = await call_next(request)
            log.info(
                "request.end",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                request_id=request.headers.get("X-Request-ID"),
            )
            return response

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(query.router)
    app.include_router(conversations.router)
    app.include_router(query_logs.router)
    app.include_router(ingestion_jobs.router)
    app.include_router(auth.router)
    app.include_router(admin.router)

    return app


app = create_app()

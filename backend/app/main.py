from fastapi import FastAPI

from app.api.routes import documents, health, query
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(query.router)

    return app


app = create_app()

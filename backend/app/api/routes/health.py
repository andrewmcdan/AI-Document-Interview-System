from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api import deps
from app.storage.object_store import ObjectStore
from app.storage.vector_store import VectorStore
from app.services.openai_client import OpenAIClient

router = APIRouter(tags=["health"])


class ComponentStatus(BaseModel):
    status: str
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, ComponentStatus]


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    session_factory: async_sessionmaker[AsyncSession] = Depends(deps.get_sessionmaker),
    vector_store: VectorStore = Depends(deps.get_vector_store),
    object_store: ObjectStore = Depends(deps.get_object_store),
    openai_client: OpenAIClient = Depends(deps.get_openai_client),
) -> ReadinessResponse:
    checks = {
        "database": await _check_database(session_factory),
        "qdrant": _check_qdrant(vector_store),
        "object_storage": _check_object_storage(object_store),
        "openai": _check_openai(openai_client),
    }
    status = "ok" if all(result["status"] == "ok" for result in checks.values()) else "degraded"
    return ReadinessResponse(status=status, checks=checks)


async def _check_database(session_factory: async_sessionmaker[AsyncSession]) -> dict[str, str]:
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - best effort health check
        return {"status": "error", "detail": str(exc)}


def _check_qdrant(vector_store: VectorStore) -> dict[str, str]:
    try:
        vector_store.client.get_collections()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - best effort health check
        return {"status": "error", "detail": str(exc)}


def _check_object_storage(object_store: ObjectStore) -> dict[str, str]:
    try:
        object_store.client.list_buckets()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - best effort health check
        return {"status": "error", "detail": str(exc)}


def _check_openai(openai_client: OpenAIClient) -> dict[str, str]:
    if not getattr(openai_client.client, "api_key", None):
        return {"status": "skipped", "detail": "API key not configured"}
    try:
        openai_client.client.models.list()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - best effort health check
        return {"status": "error", "detail": str(exc)}

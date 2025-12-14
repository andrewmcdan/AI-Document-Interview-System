from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api import deps
from app.api.security import get_current_user
from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter(prefix="/admin", tags=["admin"])
log = get_logger()


@router.post("/reset")
async def reset_data(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
    vector_store=Depends(deps.get_vector_store),
    object_store=Depends(deps.get_object_store),
    settings=Depends(get_settings),
) -> dict[str, str]:
    """Dangerous reset endpoint for local/dev: clears DB rows, vector store, and object storage."""
    if settings.environment.lower() not in {"development", "local", "test"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reset not permitted outside development/test environments.",
        )

    # Clear relational data
    await db.execute(
        text(
            "TRUNCATE TABLE query_logs, messages, conversations, document_chunks, ingestion_jobs, documents "
            "RESTART IDENTITY CASCADE"
        )
    )
    await db.commit()

    # Clear vector store and object storage (best effort)
    try:
        vector_store.reset()
    except Exception as exc:  # pragma: no cover - best effort
        log.exception("admin.reset.vector_store_failed", error=str(exc))
    try:
        object_store.purge_all()
    except Exception as exc:  # pragma: no cover - best effort
        log.exception("admin.reset.object_store_failed", error=str(exc))

    log.info("admin.reset.completed", user=current_user)
    return {"status": "reset complete"}

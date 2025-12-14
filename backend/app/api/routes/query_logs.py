from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db import models_querylog
from app.schemas.query_log import QueryLog

router = APIRouter(prefix="/query_logs", tags=["query_logs"])


@router.get("", response_model=list[QueryLog])
async def list_query_logs(
    user_id: str | None = None,
    current_user: str = Depends(deps.get_current_user),
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[QueryLog]:
    target_user = user_id or current_user
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    stmt = (
        select(models_querylog.QueryLog)
        .where(models_querylog.QueryLog.user_id == target_user)
        .order_by(models_querylog.QueryLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return [QueryLog.model_validate(log) for log in logs]

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.security import get_current_user
from app.db import models
from app.schemas.ingestion import IngestionJob

router = APIRouter(prefix="/ingestion_jobs", tags=["ingestion_jobs"])


@router.get("", response_model=list[IngestionJob])
async def list_ingestion_jobs(
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[IngestionJob]:
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    stmt = (
        select(models.IngestionJob)
        .where(models.IngestionJob.owner_id == current_user)
        .order_by(models.IngestionJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [IngestionJob.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=IngestionJob)
async def get_ingestion_job(
    job_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> IngestionJob:
    job = await db.get(models.IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    if job.owner_id and job.owner_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized for this job")
    return IngestionJob.model_validate(job)


@router.get("/{job_id}/status")
async def get_ingestion_status(
    job_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> dict[str, str | None]:
    job = await db.get(models.IngestionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    if job.owner_id and job.owner_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized for this job")
    return {
        "status": job.status,
        "error": job.error,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }

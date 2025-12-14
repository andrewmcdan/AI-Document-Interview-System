from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.security import get_current_user
from app.db import models
from app.schemas.analysis import AnalysisJob as AnalysisJobSchema, AnalysisRequest
from app.services.analysis import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisJobSchema)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
    session_factory=Depends(deps.get_sessionmaker),
    analysis_service: AnalysisService = Depends(deps.get_analysis_service),
) -> AnalysisJobSchema:
    job_id = str(uuid.uuid4())
    job = models.AnalysisJob(
        id=job_id,
        owner_id=current_user,
        task_type=request.task_type,
        question=request.question,
        document_ids=request.document_ids,
        status="pending",
    )
    db.add(job)
    await db.flush()
    await db.commit()

    background_tasks.add_task(
        _run_analysis_job,
        session_factory=session_factory,
        job_id=job_id,
        owner_id=current_user,
        request=request,
    )

    return AnalysisJobSchema.model_validate(job)


async def _run_analysis_job(session_factory, job_id: str, owner_id: str, request: AnalysisRequest):
    async with session_factory() as session:
        service = AnalysisService(deps.get_openai_client())
        try:
            await service.run_analysis(
                db=session,
                owner_id=owner_id,
                document_ids=request.document_ids or [],
                question=request.question,
                task_type=request.task_type,
                max_chunks_per_doc=request.max_chunks_per_doc,
                job_id=job_id,
            )
        except Exception as exc:  # pragma: no cover - best effort
            await session.execute(
                models.AnalysisJob.__table__.update()
                .where(models.AnalysisJob.id == job_id)
                .values(status="failed", error=str(exc), finished_at=datetime.utcnow())
            )
            await session.commit()


@router.get("", response_model=list[AnalysisJobSchema])
async def list_analysis_jobs(
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[AnalysisJobSchema]:
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    stmt = (
        select(models.AnalysisJob)
        .where(models.AnalysisJob.owner_id == current_user)
        .order_by(models.AnalysisJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [AnalysisJobSchema.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=AnalysisJobSchema)
async def get_analysis_job(
    job_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> AnalysisJobSchema:
    job = await db.get(models.AnalysisJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if job.owner_id and job.owner_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized for this job")
    return AnalysisJobSchema.model_validate(job)

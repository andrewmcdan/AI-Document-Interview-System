from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.security import get_current_user
from app.db import models
from app.schemas.ingestion import IngestionJob
from app.schemas.document import Document
from app.services.ingestion import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.get("", response_model=list[Document])
async def list_documents(
    owner_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[Document]:
    owner_filter = owner_id or current_user
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)

    stmt = select(models.Document).where(models.Document.deleted_at.is_(None))
    if owner_filter:
        stmt = stmt.where(models.Document.owner_id == owner_filter)
    stmt = stmt.limit(limit).offset(offset).order_by(models.Document.created_at.desc())

    result = await db.execute(stmt)
    documents = result.scalars().all()
    return [Document.model_validate(doc) for doc in documents]


@router.post("", response_model=IngestionJob)
async def upload_document(
    title: str = Form(...),
    description: str | None = Form(None),
    owner_id: str | None = Form(None),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = Depends(),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
    session_factory=Depends(deps.get_sessionmaker),
    pipeline: IngestionPipeline = Depends(deps.get_ingestion_pipeline),
) -> IngestionJob:
    owner = owner_id or current_user
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.")
    document_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    tmp_path = Path(f"/tmp/{document_id}_{file.filename}")
    with tmp_path.open("wb") as buffer:
        buffer.write(file_content)

    job = models.IngestionJob(
        id=job_id,
        document_id=document_id,
        owner_id=owner,
        status="pending",
    )
    db.add(job)
    await db.flush()

    background_tasks.add_task(
        run_ingestion_job,
        pipeline=pipeline,
        session_factory=session_factory,
        tmp_path=tmp_path,
        document_id=document_id,
        title=title or file.filename,
        description=description,
        owner_id=owner,
        job_id=job_id,
    )

    await db.commit()

    return IngestionJob(
        id=job_id,
        document_id=document_id,
        owner_id=owner,
        status="pending",
        created_at=job.created_at or datetime.utcnow(),
    )


async def run_ingestion_job(
    pipeline: IngestionPipeline,
    session_factory,
    tmp_path: Path,
    document_id: str,
    title: str,
    description: str | None,
    owner_id: str | None,
    job_id: str,
):
    async with session_factory() as session:
        try:
            await pipeline.ingest(
                tmp_path,
                document_id=document_id,
                db=session,
                title=title,
                description=description,
                owner_id=owner_id,
                job_id=job_id,
            )
        finally:
            tmp_path.unlink(missing_ok=True)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
    vector_store=Depends(deps.get_vector_store),
    object_store=Depends(deps.get_object_store),
) -> dict[str, str]:
    document = await db.get(models.Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.owner_id and document.owner_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    document.deleted_at = datetime.utcnow()
    await db.commit()

    # Immediate cleanup of vector store and object store; replace with background job if needed.
    vector_store.delete_by_document(document_id)
    prefix = f"{document_id}/"
    object_store.delete_prefix(prefix)

    return {"status": f"document {document_id} soft-deleted and cleanup completed"}

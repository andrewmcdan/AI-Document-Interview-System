from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated, Literal
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.security import get_current_user
from app.db import models
from app.schemas.ingestion import IngestionJob
from app.schemas.document import Document
from app.services.ingestion import IngestionPipeline
from app.services.openai_client import OpenAIClient

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class SuggestedMeta(BaseModel):
    title: str
    description: str


@router.post("/describe", response_model=SuggestedMeta)
async def describe_document(
    file: UploadFile = File(...),
    pipeline: IngestionPipeline = Depends(deps.get_ingestion_pipeline),
    openai_client: OpenAIClient = Depends(deps.get_openai_client),
) -> SuggestedMeta:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB.")

    tmp_path = Path(f"/tmp/describe_{uuid.uuid4()}_{file.filename}")
    with tmp_path.open("wb") as buffer:
        buffer.write(content)

    try:
        segments = pipeline.extract_text(tmp_path)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to extract text: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    joined = " ".join(text for _, text in segments)
    sample = joined[:4000]
    prompt = (
        "You are helping create metadata for a document. "
        "Given the following document text, propose:\n"
        "1) A concise title (max 8 words).\n"
        "2) A 1-2 sentence description summarizing the document.\n\n"
        f"Document text:\n{sample}\n\n"
        "Respond in JSON with keys: title, description."
    )
    try:
        raw = openai_client.chat(prompt, temperature=0.3)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate metadata: {exc}") from exc

    # Simple extraction if model returned JSON; else fallback to plain text split
    import json

    title = ""
    description = ""
    try:
        parsed = json.loads(raw)
        title = parsed.get("title") or ""
        description = parsed.get("description") or ""
    except Exception:
        pass
    if not title:
        title = file.filename.rsplit(".", 1)[0]
    if not description:
        description = raw.strip()[:500]

    return SuggestedMeta(title=title.strip(), description=description.strip())


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
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str | None = Form(None),
    owner_id: str | None = Form(None),
    file: UploadFile = File(...),
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
    storage_key = f"{document_id}/{file.filename}"
    with tmp_path.open("wb") as buffer:
        buffer.write(file_content)

    document = models.Document(
        id=document_id,
        title=title or file.filename,
        description=description,
        owner_id=owner,
        storage_key=storage_key,
    )
    db.add(document)

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
        storage_key=storage_key,
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
    storage_key: str,
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
                storage_key=storage_key,
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

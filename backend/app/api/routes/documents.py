from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db import models
from app.schemas.document import Document
from app.services.ingestion import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[Document])
async def list_documents(
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[Document]:
    result = await db.execute(select(models.Document))
    documents = result.scalars().all()
    return [Document.model_validate(doc) for doc in documents]


@router.post("", response_model=Document)
async def upload_document(
    title: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db_session),
    pipeline: IngestionPipeline = Depends(deps.get_ingestion_pipeline),
) -> Document:
    document_id = str(uuid.uuid4())
    tmp_path = Path(f"/tmp/{document_id}_{file.filename}")
    with tmp_path.open("wb") as buffer:
        buffer.write(await file.read())

    try:
        document = await pipeline.ingest(
            tmp_path,
            document_id=document_id,
            db=db,
            title=title or file.filename,
            description=description,
            owner_id=None,
        )
    finally:
        tmp_path.unlink(missing_ok=True)
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(deps.get_db_session),
) -> dict[str, str]:
    _ = db
    # TODO: delete from DB, vector store, and object storage
    return {"status": f"document {document_id} deletion scheduled"}

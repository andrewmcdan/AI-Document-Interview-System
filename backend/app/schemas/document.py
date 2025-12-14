from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    title: str
    description: str | None = None


class DocumentCreate(DocumentBase):
    file_path: Path | None = None


class Document(DocumentBase):
    id: str
    owner_id: str | None = None
    storage_key: str | None = None
    created_at: datetime | None = None
    deleted_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    text: str
    meta: dict[str, Any] = Field(default_factory=dict)

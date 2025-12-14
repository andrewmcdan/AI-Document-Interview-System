from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IngestionJob(BaseModel):
    id: str
    document_id: str
    owner_id: str | None = None
    status: str
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

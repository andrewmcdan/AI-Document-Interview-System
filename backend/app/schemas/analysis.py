from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalysisRequest(BaseModel):
    task_type: str = "summary"
    question: str | None = None
    document_ids: list[str] | None = None
    max_chunks_per_doc: int = 30


class AnalysisJob(BaseModel):
    id: str
    owner_id: str | None = None
    task_type: str
    question: str | None = None
    document_ids: list[str] | None = None
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

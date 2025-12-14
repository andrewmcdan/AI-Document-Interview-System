from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    top_k: int = 5
    document_ids: list[str] | None = None
    min_score: float | None = None
    user_id: str | None = None


class AnswerSource(BaseModel):
    document_id: str
    chunk_id: str
    document_title: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = {}


class QueryResponse(BaseModel):
    answer: str
    sources: list[AnswerSource]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

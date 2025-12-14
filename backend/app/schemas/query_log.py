from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class QueryLog(BaseModel):
    id: str
    user_id: str | None = None
    conversation_id: str | None = None
    question: str
    answer: str
    sources: list[dict[str, Any]] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

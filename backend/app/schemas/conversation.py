from __future__ import annotations

from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, Field

from app.schemas.query import QueryResponse


class Message(BaseModel):
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    id: str
    user_id: str
    messages: Sequence[Message] = ()
    last_answer: QueryResponse | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

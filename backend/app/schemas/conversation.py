from __future__ import annotations

from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.query import QueryResponse


class Message(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(from_attributes=True)


class Conversation(BaseModel):
    id: str
    user_id: str
    title: str | None = None
    messages: Sequence[Message] = ()
    last_answer: QueryResponse | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

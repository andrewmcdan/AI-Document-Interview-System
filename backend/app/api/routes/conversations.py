from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.security import get_current_user
from app.db import models_conversation
from app.schemas.conversation import Conversation, Message

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[Conversation])
async def list_conversations(
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[Conversation]:
    target_user = user_id or current_user
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    stmt = (
        select(models_conversation.Conversation)
        .where(models_conversation.Conversation.user_id == target_user)
        .order_by(models_conversation.Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    convos = result.scalars().all()
    return [Conversation.model_validate(c) for c in convos]


@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> Conversation:
    convo = await db.get(models_conversation.Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized for this conversation")
    await db.refresh(convo)
    return Conversation.model_validate(convo)


@router.get("/{conversation_id}/messages", response_model=list[Message])
async def list_messages(
    conversation_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
) -> list[Message]:
    convo = await db.get(models_conversation.Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized for this conversation")
    await db.refresh(convo)
    return [Message.model_validate(m) for m in convo.messages]

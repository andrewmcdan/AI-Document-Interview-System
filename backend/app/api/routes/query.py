from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.security import get_current_user
from app.db import models_conversation, models_querylog
from app.schemas.query import QueryRequest, QueryResponse
from app.schemas.query_log import QueryLog
from app.services.retrieval import RetrievalService

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
    retrieval: RetrievalService = Depends(deps.get_retrieval_service),
) -> QueryResponse:
    request.user_id = current_user
    return await _answer_and_log(request=request, db=db, retrieval=retrieval)


@router.post("/conversations/{conversation_id}/query", response_model=QueryResponse)
async def query_conversation(
    conversation_id: str,
    request: QueryRequest,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(deps.get_db_session),
    retrieval: RetrievalService = Depends(deps.get_retrieval_service),
) -> QueryResponse:
    convo = await db.get(models_conversation.Conversation, conversation_id)
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized for this conversation")

    request.user_id = current_user
    response = await _answer_and_log(request=request, db=db, retrieval=retrieval, conversation_id=conversation_id)
    return response


async def _answer_and_log(
    *,
    request: QueryRequest,
    db: AsyncSession,
    retrieval: RetrievalService,
    conversation_id: str | None = None,
) -> QueryResponse:
    answer = retrieval.answer(request)
    await _log_message(db, request, answer, conversation_id=conversation_id)
    return answer


async def _log_message(
    db: AsyncSession,
    request: QueryRequest,
    response: QueryResponse,
    conversation_id: str | None,
):
    """Persist conversation and messages for audit/history."""
    user_id = request.user_id or "anonymous"

    if conversation_id:
        convo = await db.get(models_conversation.Conversation, conversation_id)
    else:
        convo = models_conversation.Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=(request.question[:80] + "...") if len(request.question) > 80 else request.question,
        )
        db.add(convo)
        await db.flush()
        conversation_id = convo.id

    user_msg = models_conversation.Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=request.question,
    )
    assistant_msg = models_conversation.Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=response.answer,
    )
    db.add_all([user_msg, assistant_msg])
    db.add(
        models_querylog.QueryLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            question=request.question,
            answer=response.answer,
            sources=[s.model_dump() for s in response.sources],
        )
    )
    await db.commit()

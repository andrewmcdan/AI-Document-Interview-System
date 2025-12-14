from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api import deps
from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval import RetrievalService

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    retrieval: RetrievalService = Depends(deps.get_retrieval_service),
) -> QueryResponse:
    return retrieval.answer(request)


@router.post("/conversations/{conversation_id}/query", response_model=QueryResponse)
async def query_conversation(
    conversation_id: str,
    request: QueryRequest,
    retrieval: RetrievalService = Depends(deps.get_retrieval_service),
) -> QueryResponse:
    _ = conversation_id
    return retrieval.answer(request)

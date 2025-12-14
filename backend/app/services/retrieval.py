from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.schemas.query import AnswerSource, QueryRequest, QueryResponse
from app.services.openai_client import OpenAIClient
from app.storage.vector_store import VectorStore


@dataclass
class RetrievalService:
    vector_store: VectorStore
    openai_client: OpenAIClient

    def answer(self, query: QueryRequest) -> QueryResponse:
        if not getattr(self.openai_client.client, "api_key", None):
            return QueryResponse(
                answer="Retrieval pipeline not yet configured. Set AIDOC_OPENAI_API_KEY and implement chunk retrieval.",
                sources=[],
            )

        # TODO: embed the question, fetch top-K chunks, and build grounded prompt.
        prompt = f"Question: {query.question}\n\nSources: [pending indexing]"
        content = self.openai_client.chat(prompt)
        return QueryResponse(answer=content, sources=[])

    def format_sources(self, hits: Iterable[AnswerSource]) -> list[AnswerSource]:
        return list(hits)

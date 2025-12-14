from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from qdrant_client.models import FieldCondition, Filter, MatchValue

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

        query_vector = self.openai_client.embed(query.question)
        qdrant_filter = self._build_filter(query)
        hits = self.vector_store.query(query_vector, limit=query.top_k, query_filter=qdrant_filter)
        filtered_hits = self._filter_hits(hits, query.min_score)
        deduped_hits = self._dedupe_hits(filtered_hits)
        sources = self._build_sources(deduped_hits)
        prompt = self._build_prompt(query.question, sources)
        content = self.openai_client.chat(prompt)
        return QueryResponse(answer=content, sources=sources)

    def format_sources(self, hits: Iterable[AnswerSource]) -> list[AnswerSource]:
        return list(hits)

    def _filter_hits(self, hits, min_score: float | None):
        if min_score is None:
            return hits
        return [hit for hit in hits if (hit.score or 0.0) >= min_score]

    def _dedupe_hits(self, hits, overlap_ratio: float = 0.5):
        """Drop overlapping chunks from the same document/page to reduce redundancy."""
        if not hits:
            return hits

        ranges_by_doc_page: dict[tuple[str, int | None], list[tuple[int, int]]] = {}
        deduped = []
        seen_chunk_ids = set()

        for hit in hits:
            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id")
            if chunk_id and chunk_id in seen_chunk_ids:
                continue

            meta = payload.get("meta", {}) or {}
            page = meta.get("page")
            start = meta.get("start_token")
            end = meta.get("end_token")
            key = (payload.get("document_id", ""), page)

            if start is not None and end is not None:
                existing_ranges = ranges_by_doc_page.setdefault(key, [])
                if any(self._overlaps((start, end), r, overlap_ratio) for r in existing_ranges):
                    continue
                existing_ranges.append((start, end))

            deduped.append(hit)
            if chunk_id:
                seen_chunk_ids.add(chunk_id)

        return deduped

    @staticmethod
    def _overlaps(a: tuple[int, int], b: tuple[int, int], threshold: float) -> bool:
        a_start, a_end = a
        b_start, b_end = b
        if a_end <= b_start or b_end <= a_start:
            return False
        overlap = min(a_end, b_end) - max(a_start, b_start)
        len_a = max(1, a_end - a_start)
        len_b = max(1, b_end - b_start)
        return overlap / min(len_a, len_b) >= threshold

    def _build_filter(self, query: QueryRequest) -> Filter | None:
        conditions = []
        if query.document_ids:
            doc_conditions = [
                FieldCondition(key="document_id", match=MatchValue(value=doc_id)) for doc_id in query.document_ids
            ]
            conditions.append(Filter(should=doc_conditions, minimum_should_match=1))

        if query.user_id:
            conditions.append(
                FieldCondition(
                    key="owner_id",
                    match=MatchValue(value=query.user_id),
                )
            )

        if not conditions:
            return None
        return Filter(must=conditions)

    def _build_sources(self, hits) -> list[AnswerSource]:
        sources: list[AnswerSource] = []
        for hit in hits:
            payload = hit.payload or {}
            meta = payload.get("meta", {}) or {}
            text = payload.get("text")
            if text:
                meta = {**meta, "text": text}
            sources.append(
                AnswerSource(
                    document_id=payload.get("document_id", ""),
                    chunk_id=payload.get("chunk_id", ""),
                    document_title=payload.get("document_title"),
                    score=hit.score,
                    metadata=meta,
                )
            )
        return sources

    def _build_prompt(self, question: str, sources: list[AnswerSource]) -> str:
        if not sources:
            return (
                "You are an assistant that only answers based on provided sources.\n"
                "No sources were retrieved for this question. Respond with \"I do not know based on the provided documents.\""
                f"\n\nQuestion: {question}"
            )

        source_blocks: list[str] = []
        for idx, source in enumerate(sources, start=1):
            title = source.document_title or source.document_id
            meta = source.metadata or {}
            page = meta.get("page")
            location = f" (page {page})" if page else ""
            body = self._truncate(meta.get("text") or meta.get("text_snippet") or "")
            source_blocks.append(
                f"[{idx}] {title}{location} :: {body}"
            )

        prompt = (
            "You are a grounded assistant. Use ONLY the sources below to answer. "
            "Cite sources using [number] markers. If the sources are insufficient, say you do not know.\n\n"
            f"Question: {question}\n\nSources:\n" + "\n\n".join(source_blocks)
        )
        return prompt

    @staticmethod
    def _truncate(text: str, limit: int = 1200) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

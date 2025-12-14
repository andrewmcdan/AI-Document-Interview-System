from __future__ import annotations

from datetime import datetime
import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db import models
from app.services.openai_client import OpenAIClient

log = get_logger()


class AnalysisService:
    def __init__(self, openai_client: OpenAIClient):
        self.openai = openai_client

    async def run_analysis(
        self,
        *,
        db: AsyncSession,
        owner_id: str | None,
        document_ids: list[str] | None,
        question: str | None,
        task_type: str,
        max_chunks_per_doc: int = 30,
        job_id: str,
    ) -> dict:
        await self._mark_status(db, job_id, "running")

        docs = await self._fetch_docs(db, owner_id, document_ids)
        doc_summaries = []
        for doc in docs:
            chunks = await self._fetch_chunks(db, doc.id, max_chunks_per_doc)
            text = "\n\n".join(c.text for c in chunks)
            summary = await self._summarize_doc(doc.title, text)
            doc_summaries.append({"document_id": doc.id, "title": doc.title, "summary": summary})

        merged = await self._merge_summaries(doc_summaries, question=question, task_type=task_type)
        result = {"doc_summaries": doc_summaries, "themes": merged.get("themes"), "answer": merged.get("answer")}
        await self._mark_status(db, job_id, "completed", result=result)
        return result

    async def _fetch_docs(self, db: AsyncSession, owner_id: str | None, doc_ids: list[str] | None):
        stmt = select(models.Document).where(models.Document.deleted_at.is_(None))
        if owner_id:
            stmt = stmt.where(models.Document.owner_id == owner_id)
        if doc_ids:
            stmt = stmt.where(models.Document.id.in_(doc_ids))
        stmt = stmt.order_by(models.Document.created_at.desc()).limit(20)
        res = await db.execute(stmt)
        return res.scalars().all()

    async def _fetch_chunks(self, db: AsyncSession, document_id: str, limit: int):
        stmt = (
            select(models.DocumentChunk)
            .where(models.DocumentChunk.document_id == document_id)
            .order_by(models.DocumentChunk.created_at.asc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    async def _summarize_doc(self, title: str, text: str) -> str:
        prompt = (
            "You are summarizing a document. Provide 3-6 concise bullets capturing key rules/policies.\n"
            f"Title: {title}\n\n"
            f"Content:\n{text[:6000]}\n\n"
            "Bullets:"
        )
        return self.openai.chat(prompt, temperature=0.2)

    async def _merge_summaries(self, doc_summaries: Iterable[dict], question: str | None, task_type: str) -> dict:
        payload_lines = []
        for idx, doc in enumerate(doc_summaries, start=1):
            payload_lines.append(f"[{idx}] {doc['title']}: {doc['summary']}")

        prompt = (
            "You are merging summaries from multiple documents. Identify common themes/rules across them.\n"
            "Return a short answer plus 4-8 themes. Keep concise and cite doc indexes in brackets when relevant.\n"
        )
        if question:
            prompt += f"Focus on answering: {question}\n"
        prompt += "\n".join(payload_lines)
        answer = self.openai.chat(prompt, temperature=0.2)
        return {"answer": answer, "themes": payload_lines}

    async def _mark_status(self, db: AsyncSession, job_id: str, status: str, result: dict | None = None):
        await db.execute(
            models.AnalysisJob.__table__.update()
            .where(models.AnalysisJob.id == job_id)
            .values(
                status=status,
                started_at=datetime.utcnow() if status == "running" else models.AnalysisJob.started_at,
                finished_at=datetime.utcnow() if status in {"completed", "failed"} else None,
                result=result,
            )
        )
        await db.commit()

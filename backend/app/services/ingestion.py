from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import uuid
from typing import Iterable

import fitz
import pdfplumber
from docx import Document as DocxDocument
from qdrant_client.models import PointStruct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db import models
from app.schemas.document import Document as DocumentSchema
from app.schemas.document import DocumentChunk
from app.services.openai_client import OpenAIClient
from app.storage.object_store import ObjectStore
from app.storage.vector_store import VectorStore


@dataclass
class IngestionPipeline:
    settings: Settings
    object_store: ObjectStore
    vector_store: VectorStore
    openai_client: OpenAIClient

    async def ingest(
        self,
        file_path: Path,
        document_id: str,
        db: AsyncSession,
        *,
        title: str,
        description: str | None = None,
        owner_id: str | None = None,
    ) -> DocumentSchema:
        """Ingest a document file into storage, DB metadata, and the vector store."""
        object_key = f"{document_id}/{file_path.name}"
        self.object_store.upload_file(file_path, object_key=object_key)

        text = self.extract_text(file_path)
        chunks = self.chunk_text(text, document_id=document_id)
        embeddings = self.embed_chunks(chunks)

        try:
            document = await self._persist_document(
                db=db,
                document_id=document_id,
                title=title,
                description=description,
                owner_id=owner_id,
                storage_key=object_key,
            )
            await self.persist_chunks(
                db=db,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
            )
            await db.commit()
            await db.refresh(document)
        except Exception:
            await db.rollback()
            raise

        return DocumentSchema(
            id=document.id,
            title=document.title,
            description=document.description,
            owner_id=document.owner_id,
            storage_key=document.storage_key,
            created_at=document.created_at,
        )

    def extract_text(self, file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            text = self._extract_pdf(file_path)
        elif suffix == ".docx":
            text = self._extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type for ingestion: {file_path.suffix}")

        cleaned = self._normalize_text(text)
        if not cleaned:
            raise ValueError("No text extracted from document; check if the file is scanned or empty.")
        return cleaned

    def chunk_text(self, text: str, document_id: str) -> list[DocumentChunk]:
        words = text.split()
        chunk_size = max(1, self.settings.chunk_size_tokens)
        overlap = max(0, min(self.settings.chunk_overlap_tokens, chunk_size - 1))

        chunks: list[DocumentChunk] = []
        start = 0
        index = 0

        while start < len(words):
            end = min(len(words), start + chunk_size)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words).strip()

            chunk_id = str(uuid.uuid4())
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    text=chunk_text,
                    metadata={"chunk_index": index, "start_word": start, "end_word": end},
                )
            )

            index += 1
            if end >= len(words):
                break
            start = max(0, end - overlap)

        return chunks

    def embed_chunks(self, chunks: Iterable[DocumentChunk]) -> list[list[float]]:
        if not getattr(self.openai_client.client, "api_key", None):
            raise ValueError("OpenAI API key is missing; set AIDOC_OPENAI_API_KEY to enable embeddings.")
        return [self.openai_client.embed(chunk.text) for chunk in chunks]

    async def persist_chunks(
        self,
        *,
        db: AsyncSession,
        document_id: str,
        chunks: Iterable[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        if not embeddings:
            raise ValueError("No embeddings produced for document; aborting persistence.")

        self.vector_store.ensure_collection(vector_size=len(embeddings[0]))

        points: list[PointStruct] = []
        chunk_rows: list[models.DocumentChunk] = []

        for chunk, embedding in zip(chunks, embeddings):
            points.append(
                PointStruct(
                    id=chunk.id,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "chunk_id": chunk.id,
                        "text": chunk.text,
                        "metadata": chunk.metadata,
                    },
                )
            )
            chunk_rows.append(
                models.DocumentChunk(
                    id=chunk.id,
                    document_id=document_id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                )
            )

        self.vector_store.upsert_chunks(points)
        db.add_all(chunk_rows)

    async def _persist_document(
        self,
        *,
        db: AsyncSession,
        document_id: str,
        title: str,
        description: str | None,
        owner_id: str | None,
        storage_key: str,
    ) -> models.Document:
        document = models.Document(
            id=document_id,
            title=title,
            description=description,
            owner_id=owner_id,
            storage_key=storage_key,
        )
        db.add(document)
        await db.flush()
        return document

    def _extract_pdf(self, file_path: Path) -> str:
        text_parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text_parts.append(page_text)
        combined = "\n".join(text_parts).strip()
        if combined:
            return combined

        # Fallback to PyMuPDF text extraction if pdfplumber finds nothing.
        with fitz.open(file_path) as doc:
            return "\n".join([page.get_text("text") for page in doc]).strip()

    def _extract_docx(self, file_path: Path) -> str:
        document = DocxDocument(file_path)
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        return "\n".join(paragraphs).strip()

    def _normalize_text(self, text: str) -> str:
        normalized = re.sub(r"\r\n?", "\n", text)
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

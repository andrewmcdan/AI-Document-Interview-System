from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.core.config import Settings


@dataclass
class VectorStore:
    client: QdrantClient
    collection_name: str = "document_chunks"

    @classmethod
    def from_settings(cls, settings: Settings) -> "VectorStore":
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        return cls(client=client)

    def ensure_collection(self, vector_size: int) -> None:
        """Create the collection if it does not exist."""
        if vector_size <= 0:
            raise ValueError("Vector size must be positive.")

        try:
            self.client.get_collection(self.collection_name)
        except UnexpectedResponse:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert_chunks(self, points: Iterable[PointStruct]) -> None:
        self.client.upsert(collection_name=self.collection_name, points=list(points))

    def query(self, vector: list[float], limit: int = 5, query_filter: Any | None = None):
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

    def delete_by_document(self, document_id: str) -> None:
        flt = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )
        self.client.delete(collection_name=self.collection_name, wait=True, filter=flt)

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.db.session import get_session, get_session_factory
from app.services.ingestion import IngestionPipeline
from app.services.openai_client import OpenAIClient
from app.services.retrieval import RetrievalService
from app.storage.object_store import ObjectStore
from app.storage.vector_store import VectorStore


def get_sessionmaker(settings: Settings = Depends(get_settings)) -> async_sessionmaker[AsyncSession]:
    return get_session_factory(settings.database_url)


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_sessionmaker),
) -> AsyncIterator[AsyncSession]:
    async for session in get_session(session_factory):
        yield session


def get_object_store(settings: Settings = Depends(get_settings)) -> ObjectStore:
    return ObjectStore.from_settings(settings)


def get_vector_store(settings: Settings = Depends(get_settings)) -> VectorStore:
    return VectorStore.from_settings(settings)


def get_openai_client(settings: Settings = Depends(get_settings)) -> OpenAIClient:
    return OpenAIClient.from_settings(settings)


def get_ingestion_pipeline(
    settings: Settings = Depends(get_settings),
    object_store: ObjectStore = Depends(get_object_store),
    vector_store: VectorStore = Depends(get_vector_store),
    openai_client: OpenAIClient = Depends(get_openai_client),
) -> IngestionPipeline:
    return IngestionPipeline(
        settings=settings,
        object_store=object_store,
        vector_store=vector_store,
        openai_client=openai_client,
    )


def get_retrieval_service(
    vector_store: VectorStore = Depends(get_vector_store),
    openai_client: OpenAIClient = Depends(get_openai_client),
) -> RetrievalService:
    return RetrievalService(vector_store=vector_store, openai_client=openai_client)

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "AI Document Interview System API"
    environment: str = "development"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_docs",
        description="SQLAlchemy-compatible database URL.",
    )

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "ai-documents"

    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    completion_model: str = "gpt-4o-mini"

    chunk_size_tokens: int = 600
    chunk_overlap_tokens: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AIDOC_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

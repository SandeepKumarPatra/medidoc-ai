"""Configuration settings for MediDoc AI.

Loads environment variables via pydantic-settings with validation and sensible defaults.
"""

from functools import lru_cache
from typing import List, Optional, Union
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration schema."""

    # Application
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: Union[List[str], str] = ["http://localhost:5173"]

    # Database (PostgreSQL 16 with pgvector)
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/medidoc"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "medidoc"
    postgres_port: int = 5432

    # Embeddings
    # Dev default: BAAI/bge-small-en-v1.5 (384 dim); production option: BAAI/bge-m3 (1024 dim)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # Chunking (in approximate token units)
    parent_chunk_size: int = 1500
    child_chunk_size: int = Field(
        default=100,
        validation_alias=AliasChoices("CHILD_CHUNK_TOKENS", "child_chunk_tokens", "child_chunk_size", "CHILD_CHUNK_SIZE"),
        description="Target child chunk size in tokens (default 100)",
    )
    child_chunk_overlap: int = Field(
        default=20,
        validation_alias=AliasChoices("CHILD_CHUNK_OVERLAP", "child_chunk_overlap"),
        description="Target child chunk overlap in tokens (default 20)",
    )

    # Reranker & LLM
    # Supported reranker models:
    # - "BAAI/bge-reranker-base" (default cross-encoder)
    # - "cross-encoder/ms-marco-MiniLM-L-6-v2" (fast, lightweight CPU option)
    # - "BAAI/bge-reranker-v2-m3" (multilingual cross-encoder)
    reranker_model: str = "BAAI/bge-reranker-base"
    rerank_candidates: int = 10
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    llm_model: str = "gemini-2.5-flash"
    openai_api_key: str = ""
    llm_timeout: float = 30.0
    llm_thinking_budget: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("LLM_THINKING_BUDGET", "llm_thinking_budget"),
        description="Thinking / reasoning budget in tokens (0 to disable, -1 automatic, or positive token count)",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Allow comma-delimited strings or lists for CORS origins."""
        if isinstance(value, str):
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()

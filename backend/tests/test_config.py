"""Tests for configuration settings and defaults."""

import os
from backend.app.config import Settings, get_settings


def test_settings_defaults():
    """Verify default configuration attributes."""
    settings = Settings(_env_file=None)
    assert settings.embedding_dim == 384
    assert settings.embedding_model == "BAAI/bge-small-en-v1.5"
    assert settings.parent_chunk_size == 1500
    assert settings.child_chunk_size == 300
    assert settings.child_chunk_overlap == 50
    assert settings.rerank_candidates == 10
    assert settings.reranker_model == "BAAI/bge-reranker-base"
    assert settings.llm_timeout == 30.0
    assert "http://localhost:5173" in settings.cors_origins


def test_cors_origins_parsing():
    """Verify comma-separated and JSON string parsing for CORS origins."""
    s = Settings(cors_origins="http://example.com, http://localhost:3000")
    assert s.cors_origins == ["http://example.com", "http://localhost:3000"]

    s2 = Settings(cors_origins='["http://example.com", "http://localhost:3000"]')
    assert s2.cors_origins == ["http://example.com", "http://localhost:3000"]

"""Embeddings wrapper utilizing LangChain and configured Hugging Face sentence models.

Wraps model embedding calls with batching, input validation, and singleton caching
to ensure consistent vector dimensionality and efficient GPU/CPU inference.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentEmbedder:
    """LangChain-compatible embeddings wrapper for document ingestion and retrieval."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        logger.info("Initializing HuggingFaceEmbeddings with model: %s", self.model_name)
        self._embedder = HuggingFaceEmbeddings(
            model_name=self.model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute normalized vector embeddings for a list of document texts.

        Args:
            texts: List of chunk texts to embed.

        Returns:
            List of float embedding vectors of dimension settings.embedding_dim.
        """
        if not texts:
            return []
        return self._embedder.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """Compute normalized vector embedding for a single search query.

        Args:
            query: Query string.

        Returns:
            Float vector embedding.
        """
        return self._embedder.embed_query(query)


@lru_cache()
def get_embedder() -> DocumentEmbedder:
    """Return cached singleton instance of DocumentEmbedder."""
    return DocumentEmbedder()

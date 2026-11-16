"""Retrieval module for MediDoc AI.

Exposes the unified retrieve() function supporting:
- naive: Dense child vector search
- parent_child: Dense child vector search with parent expansion
- hybrid: Vector + PostgreSQL full-text search with RRF
- hybrid_rerank: Vector + full-text search with RRF and cross-encoder reranking
"""

from backend.app.retrieval.schemas import RetrievalChunk, RetrievalResponse
from backend.app.retrieval.service import retrieve

__all__ = ["retrieve", "RetrievalChunk", "RetrievalResponse"]

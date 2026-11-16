"""Dense vector retrieval using pgvector cosine similarity on child chunks."""

from __future__ import annotations

import logging
import time
from typing import List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.models import Child, Document
from backend.app.ingestion.embedder import get_embedder

logger = logging.getLogger(__name__)
settings = get_settings()

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def dense_search(
    question: str,
    top_k: int,
    db: Session,
) -> Tuple[List[Tuple[Child, float, str]], float, float]:
    """Execute dense semantic search using pgvector cosine distance over child chunks.

    Args:
        question: Natural language question.
        top_k: Number of nearest neighbors to retrieve.
        db: Active SQLAlchemy session.

    Returns:
        Tuple of:
          - List of (Child, similarity_score, document_filename)
          - Embedding latency in milliseconds
          - Search execution latency in milliseconds
    """
    embedder = get_embedder()

    # Prepend BGE query instruction if the configured model is from the BGE family
    if "bge" in settings.embedding_model.lower():
        formatted_query = f"{BGE_QUERY_PREFIX}{question}"
    else:
        formatted_query = question

    # 1. Compute query vector
    t0 = time.perf_counter()
    query_vector = embedder.embed_query(formatted_query)
    embed_ms = (time.perf_counter() - t0) * 1000.0

    # 2. Execute pgvector cosine distance search
    t1 = time.perf_counter()
    cosine_distance = Child.embedding.cosine_distance(query_vector)
    # Cosine similarity is 1.0 - cosine_distance
    cosine_similarity = (1.0 - cosine_distance).label("similarity")

    stmt = (
        select(Child, cosine_similarity, Document.filename)
        .join(Document, Child.document_id == Document.id)
        .order_by(cosine_distance.asc())
        .limit(top_k)
    )

    rows = db.execute(stmt).all()
    search_ms = (time.perf_counter() - t1) * 1000.0

    results: List[Tuple[Child, float, str]] = []
    for child, similarity, filename in rows:
        results.append((child, float(similarity) if similarity is not None else 0.0, str(filename)))

    logger.debug(
        "Dense search retrieved %d chunks in %.2f ms (embed: %.2f ms)",
        len(results),
        search_ms,
        embed_ms,
    )
    return results, embed_ms, search_ms

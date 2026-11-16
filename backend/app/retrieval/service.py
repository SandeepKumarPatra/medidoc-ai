"""Unified retrieval service exposing retrieve(question, mode, top_k).

Supports all four Phase 2 retrieval modes:
- naive: Dense pgvector cosine similarity over child chunks, returns child text
- parent_child: Dense similarity over child chunks, expands to deduplicated parent sections
- hybrid: pgvector similarity (top 50) + Postgres full-text rank (top 50) merged by RRF (k=60), then parent expansion
- hybrid_rerank: hybrid candidates, cross-encoder reranking, then parent expansion
"""

from __future__ import annotations

import logging
import time
from typing import Literal, Optional
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.session import SessionLocal
from backend.app.retrieval.dense import dense_search
from backend.app.retrieval.expansion import expand_to_parents
from backend.app.retrieval.fusion import reciprocal_rank_fusion
from backend.app.retrieval.rerank import rerank_candidates
from backend.app.retrieval.schemas import RetrievalChunk, RetrievalResponse
from backend.app.retrieval.sparse import sparse_search

logger = logging.getLogger(__name__)
settings = get_settings()

RetrievalMode = Literal["naive", "parent_child", "hybrid", "hybrid_rerank"]


def retrieve(
    question: str,
    mode: str = "hybrid_rerank",
    top_k: int = 5,
    db: Optional[Session] = None,
) -> RetrievalResponse:
    """Execute multi-strategy document retrieval.

    Args:
        question: Query string.
        mode: Retrieval strategy ('naive', 'parent_child', 'hybrid', 'hybrid_rerank').
        top_k: Number of results to return.
        db: Optional active SQLAlchemy database session. If None, manages its own session.

    Returns:
        RetrievalResponse with scored chunks and per-stage latency breakdown.
    """
    valid_modes = {"naive", "parent_child", "hybrid", "hybrid_rerank"}
    if mode not in valid_modes:
        raise ValueError(f"Unknown retrieval mode '{mode}'. Valid modes: {valid_modes}")

    session_created = False
    if db is None:
        db = SessionLocal()
        session_created = True

    try:
        t_start = time.perf_counter()
        timings: dict[str, float] = {}

        if mode == "naive":
            # 1. Naive: Dense vector search over child chunks, return child text directly
            dense_results, embed_ms, search_ms = dense_search(question, top_k=top_k, db=db)
            timings["embed_ms"] = round(embed_ms, 2)
            timings["dense_search_ms"] = round(search_ms, 2)

            chunks: list[RetrievalChunk] = []
            for child, score, filename in dense_results:
                chunks.append(
                    RetrievalChunk(
                        id=str(child.id),
                        document_id=str(child.document_id),
                        document_filename=filename,
                        text=child.text,
                        score=score,
                        page_start=child.page_start,
                        page_end=child.page_end,
                        chunk_type="child",
                        mode=mode,
                    )
                )

        elif mode == "parent_child":
            # 2. Parent-Child: Dense vector search, expand to parent sections and deduplicate
            # Query candidate pool of children (e.g. top 50 or top_k * 4) to ensure sufficient parents
            candidate_k = max(top_k * 4, 50)
            dense_results, embed_ms, search_ms = dense_search(question, top_k=candidate_k, db=db)
            timings["embed_ms"] = round(embed_ms, 2)
            timings["dense_search_ms"] = round(search_ms, 2)

            chunks, expansion_ms = expand_to_parents(
                candidates=dense_results,
                top_k=top_k,
                db=db,
                mode=mode,
            )
            timings["expansion_ms"] = round(expansion_ms, 2)

        elif mode == "hybrid":
            # 3. Hybrid: Dense (top 50) + Sparse full-text (top 50), RRF (k=60), expand to parents
            dense_results, embed_ms, dense_search_ms = dense_search(question, top_k=50, db=db)
            sparse_results, sparse_search_ms = sparse_search(question, top_k=50, db=db)
            timings["embed_ms"] = round(embed_ms, 2)
            timings["dense_search_ms"] = round(dense_search_ms, 2)
            timings["sparse_search_ms"] = round(sparse_search_ms, 2)

            fused_candidates, fusion_ms = reciprocal_rank_fusion(
                dense_results=dense_results,
                sparse_results=sparse_results,
                k=60,
            )
            timings["fusion_ms"] = round(fusion_ms, 2)

            chunks, expansion_ms = expand_to_parents(
                candidates=fused_candidates,
                top_k=top_k,
                db=db,
                mode=mode,
            )
            timings["expansion_ms"] = round(expansion_ms, 2)

        elif mode == "hybrid_rerank":
            # 4. Hybrid Rerank: Dense (top 50) + Sparse (top 50), RRF (k=60), CrossEncoder rerank, expand to parents
            dense_results, embed_ms, dense_search_ms = dense_search(question, top_k=50, db=db)
            sparse_results, sparse_search_ms = sparse_search(question, top_k=50, db=db)
            timings["embed_ms"] = round(embed_ms, 2)
            timings["dense_search_ms"] = round(dense_search_ms, 2)
            timings["sparse_search_ms"] = round(sparse_search_ms, 2)

            fused_candidates, fusion_ms = reciprocal_rank_fusion(
                dense_results=dense_results,
                sparse_results=sparse_results,
                k=60,
            )
            timings["fusion_ms"] = round(fusion_ms, 2)

            # Rerank top RERANK_CANDIDATES (config, default 20) fused candidates using cross-encoder
            rerank_limit = settings.rerank_candidates
            rerank_pool = fused_candidates[:rerank_limit]
            reranked_candidates, rerank_ms, rerank_text_chars = rerank_candidates(
                question=question,
                candidates=rerank_pool,
            )
            timings["rerank_ms"] = round(rerank_ms, 2)
            timings["rerank_text_chars"] = rerank_text_chars

            chunks, expansion_ms = expand_to_parents(
                candidates=reranked_candidates,
                top_k=top_k,
                db=db,
                mode=mode,
            )
            timings["expansion_ms"] = round(expansion_ms, 2)

        total_ms = (time.perf_counter() - t_start) * 1000.0
        timings["total_ms"] = round(total_ms, 2)

        return RetrievalResponse(
            question=question,
            mode=mode,
            results=chunks,
            timings=timings,
        )

    finally:
        if session_created and db is not None:
            db.close()

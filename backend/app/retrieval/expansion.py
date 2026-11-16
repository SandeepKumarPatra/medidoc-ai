"""Parent section expansion and deduplication for hierarchical RAG."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Set, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Parent
from backend.app.retrieval.fusion import FusedCandidate
from backend.app.retrieval.schemas import RetrievalChunk

logger = logging.getLogger(__name__)


def expand_to_parents(
    candidates: List[Any],  # FusedCandidate or Tuple[Child, float, str]
    top_k: int,
    db: Session,
    mode: str,
) -> Tuple[List[RetrievalChunk], float]:
    """Expand candidate child chunks to their parent sections and deduplicate.

    Preserves the ranking order of the highest-scoring child for each distinct parent.

    Args:
        candidates: Ordered child candidates (from dense search, RRF fusion, or reranker).
        top_k: Maximum number of distinct parent sections to return.
        db: Active SQLAlchemy database session.
        mode: Retrieval strategy mode name.

    Returns:
        Tuple of:
          - Ranked list of deduplicated parent RetrievalChunk items (at most top_k).
          - Expansion latency in milliseconds.
    """
    t0 = time.perf_counter()

    if not candidates:
        return [], 0.0

    # Normalize candidates into list of (child, score, filename)
    normalized: List[Tuple[Any, float, str]] = []
    for item in candidates:
        if isinstance(item, FusedCandidate):
            normalized.append((item.child, item.score, item.document_filename))
        elif isinstance(item, tuple) and len(item) == 3:
            normalized.append(item)
        else:
            raise ValueError(f"Unsupported candidate format: {type(item)}")

    # 1. Group results by parent_id, keeping the best-scoring child per parent
    parent_best: Dict[uuid.UUID, Tuple[Any, float, str]] = {}
    for child, score, filename in normalized:
        p_id = child.parent_id
        if p_id not in parent_best or score > parent_best[p_id][1]:
            parent_best[p_id] = (child, score, filename)

    # 2. Sort distinct parents by their best child score descending
    sorted_distinct_parents = sorted(
        parent_best.items(),
        key=lambda item: item[1][1],
        reverse=True,
    )

    # 3. Take top_k distinct parents
    selected_parents = sorted_distinct_parents[:top_k]

    # Pre-fetch parent records from database in batch
    candidate_parent_ids = [p_id for p_id, _ in selected_parents]
    parents_query = db.execute(
        select(Parent).where(Parent.id.in_(candidate_parent_ids))
    ).scalars().all()
    parent_map: Dict[uuid.UUID, Parent] = {p.id: p for p in parents_query}

    parent_chunks: List[RetrievalChunk] = []
    seen_parent_ids: Set[uuid.UUID] = set()

    for p_id, (best_child, best_score, filename) in selected_parents:
        if p_id in seen_parent_ids:
            continue

        parent = parent_map.get(p_id)
        if not parent:
            parent = db.get(Parent, p_id)
            if not parent:
                continue
            parent_map[p_id] = parent

        seen_parent_ids.add(p_id)
        parent_chunks.append(
            RetrievalChunk(
                id=str(parent.id),
                document_id=str(parent.document_id),
                document_filename=filename,
                text=parent.text,
                score=best_score,
                page_start=parent.page_start,
                page_end=parent.page_end,
                section_title=parent.section_title,
                chunk_type="parent",
                mode=mode,
                metadata={
                    "matched_child_id": str(best_child.id),
                    "section_type": parent.section_type,
                    "parent_id": str(parent.id),
                },
            )
        )

    expansion_ms = (time.perf_counter() - t0) * 1000.0

    logger.debug(
        "Expanded %d candidates to %d unique parent sections in %.2f ms",
        len(candidates),
        len(parent_chunks),
        expansion_ms,
    )
    return parent_chunks, expansion_ms

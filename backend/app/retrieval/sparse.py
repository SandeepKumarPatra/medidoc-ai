"""Sparse keyword retrieval using PostgreSQL full-text search (tsvector + plainto_tsquery)."""

from __future__ import annotations

import logging
import time
from typing import List, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.models import Child, Document

logger = logging.getLogger(__name__)


def sparse_search(
    question: str,
    top_k: int,
    db: Session,
) -> Tuple[List[Tuple[Child, float, str]], float]:
    """Execute full-text keyword search using PostgreSQL plainto_tsquery and ts_rank_cd.

    Args:
        question: Natural language question.
        top_k: Number of ranked matches to retrieve.
        db: Active SQLAlchemy session.

    Returns:
        Tuple of:
          - List of (Child, rank_score, document_filename)
          - Search execution latency in milliseconds
    """
    t0 = time.perf_counter()
    ts_query = func.plainto_tsquery("english", question)
    rank_expr = func.ts_rank_cd(Child.tsv, ts_query).label("rank")

    stmt = (
        select(Child, rank_expr, Document.filename)
        .join(Document, Child.document_id == Document.id)
        .where(Child.tsv.op("@@")(ts_query))
        .order_by(rank_expr.desc())
        .limit(top_k)
    )

    rows = db.execute(stmt).all()
    search_ms = (time.perf_counter() - t0) * 1000.0

    results: List[Tuple[Child, float, str]] = []
    for child, rank, filename in rows:
        results.append((child, float(rank) if rank is not None else 0.0, str(filename)))

    logger.debug(
        "Sparse full-text search retrieved %d chunks in %.2f ms",
        len(results),
        search_ms,
    )
    return results, search_ms

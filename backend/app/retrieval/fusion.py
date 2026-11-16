"""Reciprocal Rank Fusion (RRF) combining dense semantic and sparse keyword rankings."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import uuid

from backend.app.db.models import Child

logger = logging.getLogger(__name__)


@dataclass
class FusedCandidate:
    """A child chunk candidate evaluated by Reciprocal Rank Fusion."""

    child: Child
    score: float
    document_filename: str
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None


def reciprocal_rank_fusion(
    dense_results: List[Tuple[Child, float, str]],
    sparse_results: List[Tuple[Child, float, str]],
    k: int = 60,
) -> Tuple[List[FusedCandidate], float]:
    """Fuse ranked lists from dense vector search and sparse full-text search.

    Computes RRF score for each item:
        RRF_score(d) = sum(1 / (k + rank_i(d))) for i in [dense, sparse]

    Args:
        dense_results: Ranked list of (Child, dense_similarity, document_filename).
        sparse_results: Ranked list of (Child, sparse_rank, document_filename).
        k: Smoothing constant (default 60 as per SPEC.md).

    Returns:
        Tuple of:
          - Ranked list of FusedCandidate sorted by RRF score descending.
          - Fusion computation latency in milliseconds.
    """
    t0 = time.perf_counter()

    scores: Dict[uuid.UUID, float] = {}
    candidates: Dict[uuid.UUID, FusedCandidate] = {}

    # 1. Process dense ranked results (1-indexed rank)
    for rank_idx, (child, dense_score, filename) in enumerate(dense_results, start=1):
        rrf_contribution = 1.0 / (k + rank_idx)
        scores[child.id] = scores.get(child.id, 0.0) + rrf_contribution

        if child.id not in candidates:
            candidates[child.id] = FusedCandidate(
                child=child,
                score=0.0,
                document_filename=filename,
                dense_rank=rank_idx,
                dense_score=dense_score,
            )
        else:
            candidates[child.id].dense_rank = rank_idx
            candidates[child.id].dense_score = dense_score

    # 2. Process sparse ranked results (1-indexed rank)
    for rank_idx, (child, sparse_score, filename) in enumerate(sparse_results, start=1):
        rrf_contribution = 1.0 / (k + rank_idx)
        scores[child.id] = scores.get(child.id, 0.0) + rrf_contribution

        if child.id not in candidates:
            candidates[child.id] = FusedCandidate(
                child=child,
                score=0.0,
                document_filename=filename,
                sparse_rank=rank_idx,
                sparse_score=sparse_score,
            )
        else:
            candidates[child.id].sparse_rank = rank_idx
            candidates[child.id].sparse_score = sparse_score

    # 3. Assign accumulated RRF scores and sort descending
    fused_list: List[FusedCandidate] = []
    for child_id, candidate in candidates.items():
        candidate.score = scores[child_id]
        fused_list.append(candidate)

    fused_list.sort(key=lambda x: x.score, reverse=True)
    fusion_ms = (time.perf_counter() - t0) * 1000.0

    logger.debug(
        "RRF fused %d dense and %d sparse candidates into %d unique items in %.2f ms",
        len(dense_results),
        len(sparse_results),
        len(fused_list),
        fusion_ms,
    )
    return fused_list, fusion_ms

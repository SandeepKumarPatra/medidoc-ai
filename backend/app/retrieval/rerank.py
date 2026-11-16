"""Cross-encoder reranking utilizing sentence-transformers and configured model."""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import List, Tuple

import torch
from sentence_transformers import CrossEncoder

from backend.app.config import get_settings
from backend.app.retrieval.fusion import FusedCandidate

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache()
def get_cross_encoder(model_name: str | None = None) -> CrossEncoder:
    """Return cached singleton instance of CrossEncoder."""
    target_model = model_name or settings.reranker_model
    logger.info("Initializing CrossEncoder with model: %s", target_model)
    try:
        return CrossEncoder(target_model, local_files_only=True)
    except Exception:
        return CrossEncoder(target_model)


def rerank_candidates(
    question: str,
    candidates: List[FusedCandidate],
    cross_encoder: CrossEncoder | None = None,
    batch_size: int = 16,
) -> Tuple[List[FusedCandidate], float, int]:
    """Score and reorder candidate child chunks using a deep CrossEncoder.

    Truncates passages to the cross-encoder max length, operates under torch.no_grad,
    and batches execution for optimal CPU throughput.

    Args:
        question: Query question string.
        candidates: Candidate child items from hybrid RRF fusion.
        cross_encoder: Optional initialized CrossEncoder model instance.
        batch_size: Inference batch size (default 16).

    Returns:
        Tuple of:
          - Reordered list of FusedCandidate sorted by cross-encoder score descending.
          - Reranking latency in milliseconds.
          - Total text size in characters sent to the reranker.
    """
    if not candidates:
        return [], 0.0, 0

    t0 = time.perf_counter()
    encoder = cross_encoder or get_cross_encoder()
    max_len = getattr(encoder, "max_seq_length", None) or getattr(encoder, "max_length", 512) or 512

    # Use child text (not parent text), truncated to cross-encoder max length
    pairs: List[List[str]] = []
    total_text_chars = 0
    for cand in candidates:
        child_text = cand.child.text.strip()
        # Conservative character truncation (~4 chars per token) matching model max length
        truncated_text = child_text[: max_len * 4]
        pairs.append([question, truncated_text])
        total_text_chars += len(truncated_text)

    with torch.no_grad():
        scores = encoder.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False,
        )

    reranked: List[FusedCandidate] = []
    for cand, score in zip(candidates, scores):
        reranked.append(
            FusedCandidate(
                child=cand.child,
                score=float(score),
                document_filename=cand.document_filename,
                dense_rank=cand.dense_rank,
                sparse_rank=cand.sparse_rank,
                dense_score=cand.dense_score,
                sparse_score=cand.sparse_score,
            )
        )

    reranked.sort(key=lambda x: x.score, reverse=True)
    rerank_ms = (time.perf_counter() - t0) * 1000.0

    logger.info(
        "CrossEncoder reranked %d candidates (input text: %d chars) in %.2f ms (batch_size=%d)",
        len(reranked),
        total_text_chars,
        rerank_ms,
        batch_size,
    )
    return reranked, rerank_ms, total_text_chars

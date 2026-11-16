"""Pydantic schemas and dataclasses for retrieval results and stage timings."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RetrievalChunk(BaseModel):
    """An individual retrieved passage or section."""

    id: str = Field(..., description="Chunk or parent section UUID")
    document_id: str = Field(..., description="Parent document UUID")
    document_filename: str = Field(..., description="Original filename of the source document")
    text: str = Field(..., description="Retrieved text content")
    score: float = Field(..., description="Retrieval score (similarity, RRF, or cross-encoder rank)")
    page_start: int = Field(..., description="First page number of the passage")
    page_end: int = Field(..., description="Last page number of the passage")
    section_title: Optional[str] = Field(None, description="Section heading if available")
    chunk_type: str = Field("child", description="'child' for naive mode, 'parent' for section-expanded modes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance metadata")


class RetrievalResponse(BaseModel):
    """Container for retrieval candidates, query metadata, and latency metrics."""

    question: str = Field(..., description="Original query/question")
    mode: str = Field(..., description="Retrieval strategy: naive, parent_child, hybrid, or hybrid_rerank")
    results: List[RetrievalChunk] = Field(default_factory=list, description="Ranked retrieved passages")
    timings: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-stage latency breakdown in milliseconds",
    )

"""SQLAlchemy 2.x declarative models for MediDoc AI.

Defines schemas for documents, hierarchical parent/child RAG chunks with pgvector embeddings
and PostgreSQL full-text search (tsvector + GIN), structured extractions, validation issues,
PII-safe audit logging, and evaluation ablation tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


class Document(Base):
    """Uploaded and indexed clinical or policy document."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)  # sop / discharge / lab
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    parents: Mapped[List[Parent]] = relationship(
        "Parent", back_populates="document", cascade="all, delete-orphan"
    )
    children: Mapped[List[Child]] = relationship(
        "Child", back_populates="document", cascade="all, delete-orphan"
    )
    extractions: Mapped[List[Extraction]] = relationship(
        "Extraction", back_populates="document", cascade="all, delete-orphan"
    )


class Parent(Base):
    """Coarse-grained parent document section (up to ~1500 tokens)."""

    __tablename__ = "parents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    section_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="parents")
    children: Mapped[List[Child]] = relationship(
        "Child", back_populates="parent", cascade="all, delete-orphan"
    )


class Child(Base):
    """Fine-grained child chunk (~300 tokens) with dense vector embedding and tsvector."""

    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(settings.embedding_dim), nullable=True)
    tsv = mapped_column(TSVECTOR, nullable=True)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="children")
    parent: Mapped[Parent] = relationship("Parent", back_populates="children")

    __table_args__ = (
        Index(
            "ix_children_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_children_tsv", "tsv", postgresql_using="gin"),
    )


class Extraction(Base):
    """Structured clinical extraction extracted by LLM from a discharge summary or lab report."""

    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    json_result: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="extractions")
    validation_issues: Mapped[List[ValidationIssue]] = relationship(
        "ValidationIssue", back_populates="extraction", cascade="all, delete-orphan"
    )


class ValidationIssue(Base):
    """Validation finding flagged on an extraction output."""

    __tablename__ = "validation_issues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    rule: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # error / warning
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    extraction: Mapped[Extraction] = relationship(
        "Extraction", back_populates="validation_issues"
    )


class AuditLog(Base):
    """Audit log entry capturing request metadata without any raw text or PII."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    pii_items_masked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")


class EvalRun(Base):
    """Evaluation batch benchmark run."""

    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    results: Mapped[List[EvalResult]] = relationship(
        "EvalResult", back_populates="eval_run", cascade="all, delete-orphan"
    )


class EvalResult(Base):
    """Individual question result within an evaluation run."""

    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("eval_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_doc: Mapped[str] = mapped_column(String(255), nullable=False)
    retrieved_ids: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reciprocal_rank: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    eval_run: Mapped[EvalRun] = relationship("EvalRun", back_populates="results")

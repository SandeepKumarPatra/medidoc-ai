"""Ingestion service coordinating PDF parsing, chunking, embedding, and database persistence.

Executes Phase 1 ingestion pipeline:
1. Parse PDF using Docling (with pypdf fallback)
2. Build coarse parents (<= ~1500 tokens)
3. Split parents into sentence-aligned children (~300 tokens, small overlap)
4. Embed child chunks via LangChain HuggingFaceEmbeddings wrapper
5. Persist document, parents, and children with pgvector embeddings and PostgreSQL tsvector (to_tsvector)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.models import Child, Document, Parent
from backend.app.ingestion.chunker import build_parents, split_children
from backend.app.ingestion.embedder import get_embedder
from backend.app.ingestion.parser import parse_pdf

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Summary of completed document ingestion."""

    document_id: uuid.UUID
    filename: str
    doc_type: str
    status: str
    page_count: int
    parent_chunks: int
    child_chunks: int


def ingest_document(
    db: Session,
    source: Union[Path, str, bytes],
    filename: str,
    doc_type: str,
) -> IngestionResult:
    """Ingest a PDF file into the database with hierarchical chunking and embeddings.

    Args:
        db: Active SQLAlchemy database session.
        source: PDF filesystem path or in-memory bytes.
        filename: Document filename.
        doc_type: Category of document ('sop', 'discharge', 'lab').

    Returns:
        IngestionResult with persisted entity counts and document ID.
    """
    logger.info("Starting ingestion for %s (type: %s)", filename, doc_type)

    # 1. Parse PDF
    parsed_doc = parse_pdf(source=source, filename=filename)

    # 2. Build parent chunks (<= ~1500 tokens)
    parents = build_parents(parsed_doc)

    # 3. Split parents into child chunks (~300 tokens, sentence-aligned)
    children = split_children(parents)

    # 4. Embed children via LangChain embeddings wrapper
    embedder = get_embedder()
    child_texts = [child.text for child in children]
    embeddings = embedder.embed_documents(child_texts) if child_texts else []

    # 5. Persist Document record
    doc_record = Document(
        id=uuid.uuid4(),
        filename=filename,
        doc_type=doc_type,
        status="completed",
        page_count=parsed_doc.page_count,
    )
    db.add(doc_record)
    db.flush()  # Assign doc_record.id

    # 6. Persist Parent chunks
    parent_models: list[Parent] = []
    for parent in parents:
        clean_text = parent.text.replace("\x00", "")
        p_model = Parent(
            id=uuid.uuid4(),
            document_id=doc_record.id,
            section_title=parent.section_title,
            text=clean_text,
            page_start=parent.page_start,
            page_end=parent.page_end,
            section_type=parent.section_type,
        )
        parent_models.append(p_model)
        db.add(p_model)

    db.flush()

    # 7. Persist Child chunks with Vector embedding and to_tsvector
    for idx, child in enumerate(children):
        parent_model = parent_models[child.parent_index]
        clean_child_text = child.text.replace("\x00", "")
        child_embedding = embeddings[idx] if idx < len(embeddings) else None

        c_model = Child(
            id=uuid.uuid4(),
            parent_id=parent_model.id,
            document_id=doc_record.id,
            text=clean_child_text,
            embedding=child_embedding,
            tsv=func.to_tsvector("english", clean_child_text),
            page_start=child.page_start,
            page_end=child.page_end,
        )
        db.add(c_model)

    # 8. Commit entire transaction
    db.commit()
    db.refresh(doc_record)

    logger.info(
        "Successfully ingested %s: document_id=%s, %d parents, %d children",
        filename,
        doc_record.id,
        len(parents),
        len(children),
    )

    return IngestionResult(
        document_id=doc_record.id,
        filename=doc_record.filename,
        doc_type=doc_record.doc_type,
        status=doc_record.status,
        page_count=doc_record.page_count,
        parent_chunks=len(parents),
        child_chunks=len(children),
    )

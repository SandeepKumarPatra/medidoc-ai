"""Ingestion service coordinating PDF parsing, chunking, embedding, and database persistence.

Executes Phase 1 ingestion pipeline:
1. Parse PDF using Docling (with pypdf fallback)
2. Build coarse parents (<= ~1500 tokens)
3. Split parents into sentence-aligned children (~300 tokens, small overlap)
4. Embed child chunks via LangChain HuggingFaceEmbeddings wrapper
5. Persist document, parents, and children with pgvector embeddings and PostgreSQL tsvector (to_tsvector)
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from sqlalchemy import delete, func, select
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
    is_duplicate: bool = False


def ingest_document(
    db: Session,
    source: Union[Path, str, bytes],
    filename: str,
    doc_type: str,
) -> IngestionResult:
    """Ingest a PDF file into the database with hierarchical chunking and embeddings.

    Avoids duplicates by hashing the file bytes and returning existing records.

    Args:
        db: Active SQLAlchemy database session.
        source: PDF filesystem path or in-memory bytes.
        filename: Document filename.
        doc_type: Category of document ('sop', 'discharge', 'lab').

    Returns:
        IngestionResult with persisted entity counts and document ID.
    """
    logger.info("Starting ingestion for %s (type: %s)", filename, doc_type)

    # 0. Compute file SHA-256 hash
    if isinstance(source, bytes):
        content_bytes = source
    else:
        with open(source, "rb") as f:
            content_bytes = f.read()

    file_hash = hashlib.sha256(content_bytes).hexdigest()

    # Query all existing documents with this filename
    existing_docs = db.execute(
        select(Document).where(Document.filename == filename)
    ).scalars().all()

    # If an exact byte-hash match exists for this filename, return it without re-indexing
    matching_doc = next((d for d in existing_docs if d.file_hash == file_hash), None)
    if matching_doc:
        # Clean up any stale duplicate document records for the same filename
        stale_docs = [d for d in existing_docs if d.id != matching_doc.id]
        if stale_docs:
            logger.info("Cleaning up %d stale duplicate records for %s", len(stale_docs), filename)
            for stale in stale_docs:
                db.execute(delete(Child).where(Child.document_id == stale.id))
                db.execute(delete(Parent).where(Parent.document_id == stale.id))
                db.delete(stale)
            db.commit()

        logger.info(
            "Document %s already indexed with hash %s (id=%s). Returning existing record.",
            filename,
            file_hash,
            matching_doc.id,
        )
        p_count = db.execute(
            select(func.count(Parent.id)).where(Parent.document_id == matching_doc.id)
        ).scalar() or 0
        c_count = db.execute(
            select(func.count(Child.id)).where(Child.document_id == matching_doc.id)
        ).scalar() or 0

        return IngestionResult(
            document_id=matching_doc.id,
            filename=matching_doc.filename,
            doc_type=matching_doc.doc_type,
            status=matching_doc.status,
            page_count=matching_doc.page_count,
            parent_chunks=int(p_count),
            child_chunks=int(c_count),
            is_duplicate=True,
        )

    # When the same filename is re-uploaded with different content, replace the old document
    # by deleting old children and parents first
    if existing_docs:
        logger.info(
            "Re-uploading %s with different content. Replacing %d existing document record(s).",
            filename,
            len(existing_docs),
        )
        for old_doc in existing_docs:
            db.execute(delete(Child).where(Child.document_id == old_doc.id))
            db.execute(delete(Parent).where(Parent.document_id == old_doc.id))
            db.delete(old_doc)
        db.flush()

    # 1. Parse PDF
    parsed_doc = parse_pdf(source=content_bytes, filename=filename)

    # 2. Build parent chunks (<= ~1500 tokens)
    raw_parents = build_parents(parsed_doc)

    # 2b. Defensive de-duplication: skip parents whose normalized text hash already exists in this document
    parents = []
    seen_parent_hashes: set[str] = set()
    for parent in raw_parents:
        norm_text = " ".join(parent.text.lower().split())
        norm_hash = hashlib.md5(norm_text.encode("utf-8")).hexdigest()
        if norm_hash in seen_parent_hashes:
            logger.warning(
                "Defensive de-duplication: skipping duplicate parent '%s' in %s (hash=%s)",
                parent.section_title,
                filename,
                norm_hash,
            )
            continue
        seen_parent_hashes.add(norm_hash)
        parents.append(parent)

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
        file_hash=file_hash,
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


def ingest_all_sops(sop_dir: Path | None = None) -> list[IngestionResult]:
    """Ingest all synthetic SOP documents from data/generated/ into the database."""
    from backend.app.db.session import SessionLocal

    target_dir = sop_dir or (Path(__file__).resolve().parents[3] / "data" / "generated")
    pdf_paths = sorted(target_dir.glob("sop_*.pdf"))
    if not pdf_paths:
        logger.warning("No SOP PDFs found in %s to ingest.", target_dir)
        return []

    logger.info("Ingesting %d SOP documents from %s...", len(pdf_paths), target_dir)
    results: list[IngestionResult] = []
    db = SessionLocal()
    try:
        for p in pdf_paths:
            print(f"Indexing {p.name}...")
            res = ingest_document(db=db, source=p, filename=p.name, doc_type="sop")
            results.append(res)
            print(f"  -> {p.name}: {res.parent_chunks} parents, {res.child_chunks} children (id={res.document_id})")
        return results
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Ingest PDFs into MediDoc AI database.")
    parser.add_argument(
        "--sops",
        action="store_true",
        default=True,
        help="Ingest all SOP PDFs from data/generated/ (default: True)",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Optional directory path containing SOP PDFs",
    )
    args = parser.parse_args()
    ingest_all_sops(sop_dir=args.dir)

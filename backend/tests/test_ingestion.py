"""Integration tests for MediDoc AI ingestion pipeline and API endpoints against PostgreSQL."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.db.models import Child, Document, Parent
from backend.app.db.session import SessionLocal, engine
from backend.app.ingestion.service import ingest_document
from backend.app.main import app

settings = get_settings()


@pytest.fixture
def db_session(db: Session):
    """Yield an isolated session bound to test database."""
    return db


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_health_endpoint(client):
    """Assert GET /health reports API is operational and DB is connected."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_ingest_synthetic_sop_into_postgres(db_session):
    """Ingest a synthetic SOP PDF directly and verify database records, embeddings, and tsv."""
    pdf_path = Path("data/generated/sop_infection_control.pdf")
    assert pdf_path.exists(), f"Synthetic SOP PDF not found at {pdf_path}"

    result = ingest_document(
        db=db_session,
        source=pdf_path,
        filename=pdf_path.name,
        doc_type="sop",
    )

    # 1. Assert Ingestion Result Summary
    assert result.status == "completed"
    assert 6 <= result.page_count <= 10
    assert result.parent_chunks > 0
    assert result.child_chunks >= result.parent_chunks

    # 2. Assert Document Record in PostgreSQL
    doc = db_session.get(Document, result.document_id)
    assert doc is not None
    assert doc.filename == "sop_infection_control.pdf"
    assert doc.doc_type == "sop"
    assert doc.status == "completed"
    assert doc.page_count == result.page_count

    # 3. Assert Parent Records
    parents = db_session.execute(
        select(Parent).where(Parent.document_id == doc.id)
    ).scalars().all()
    assert len(parents) == result.parent_chunks
    for parent in parents:
        assert parent.text.strip()
        assert parent.page_start >= 1
        assert parent.page_end >= parent.page_start

    # 4. Assert Child Records with Embeddings, TSV, and Page Numbers
    children = db_session.execute(
        select(Child).where(Child.document_id == doc.id)
    ).scalars().all()
    assert len(children) == result.child_chunks

    for child in children:
        # Embeddings check
        assert child.embedding is not None, "Child embedding must not be null"
        assert len(child.embedding) == settings.embedding_dim, (
            f"Embedding dim must match config ({settings.embedding_dim})"
        )

        # Full-text TSV check
        assert child.tsv is not None, "Child tsvector must not be null"

        # Page numbers check
        assert child.page_start >= 1
        assert child.page_end >= child.page_start

    # 5. Assert PostgreSQL tsvector full-text search match
    fts_query = select(Child).where(
        Child.document_id == doc.id,
        Child.tsv.op("@@")(func.to_tsquery("english", "infection")),
    )
    fts_matches = db_session.execute(fts_query).scalars().all()
    assert len(fts_matches) > 0, "PostgreSQL FTS query for 'infection' should match child chunks"


def test_api_ingest_and_get_documents(client):
    """Test POST /ingest and GET /documents through FastAPI HTTP interface."""
    pdf_path = Path("data/generated/sop_discharge_process.pdf")
    assert pdf_path.exists(), f"Synthetic SOP PDF not found at {pdf_path}"

    with open(pdf_path, "rb") as f:
        response = client.post(
            "/ingest",
            files={"file": (pdf_path.name, f, "application/pdf")},
            data={"doc_type": "sop"},
        )

    assert response.status_code == 201, f"POST /ingest failed: {response.text}"
    ingest_data = response.json()
    assert ingest_data["status"] == "completed"
    assert ingest_data["filename"] == "sop_discharge_process.pdf"
    assert ingest_data["parent_chunks"] > 0
    assert ingest_data["child_chunks"] > 0

    # Test GET /documents
    docs_response = client.get("/documents")
    assert docs_response.status_code == 200
    doc_list = docs_response.json()
    assert isinstance(doc_list, list)
    assert len(doc_list) >= 1

    # Verify chunk counts are present and non-zero on the uploaded document
    matched_doc = next((d for d in doc_list if d["filename"] == "sop_discharge_process.pdf"), None)
    assert matched_doc is not None
    assert matched_doc["doc_type"] == "sop"
    assert matched_doc["parent_count"] > 0
    assert matched_doc["child_count"] > 0
    assert matched_doc["page_count"] >= 1


def test_ingest_rejects_non_pdf_and_invalid_signatures(client):
    """Assert POST /ingest rejects non-pdf file extensions and invalid header signatures."""
    # 1. Non-pdf extension
    res_txt = client.post(
        "/ingest",
        files={"file": ("notes.txt", b"plain text content", "text/plain")},
        data={"doc_type": "sop"},
    )
    assert res_txt.status_code == 400
    assert "Invalid file format" in res_txt.json()["detail"]

    # 2. .pdf extension but invalid binary signature (magic bytes)
    res_fake = client.post(
        "/ingest",
        files={"file": ("fake.pdf", b"This is not a pdf file header", "application/pdf")},
        data={"doc_type": "sop"},
    )
    assert res_fake.status_code == 400
    assert "PDF signature" in res_fake.json()["detail"]


def test_ingest_rejects_files_over_20mb(client):
    """Assert POST /ingest rejects uploads larger than 20 MB."""
    oversized_bytes = b"%PDF-1.4" + (b"0" * (20 * 1024 * 1024 + 10))
    response = client.post(
        "/ingest",
        files={"file": ("oversized.pdf", oversized_bytes, "application/pdf")},
        data={"doc_type": "sop"},
    )
    assert response.status_code == 400
    assert "20 MB" in response.json()["detail"]


def test_ingest_duplicate_detection_by_hash(client):
    """Assert uploading the exact same PDF returns the existing document record without re-indexing."""
    pdf_path = Path("data/generated/sop_discharge_process.pdf")
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    # First upload (or re-upload of existing)
    res1 = client.post(
        "/ingest",
        files={"file": (pdf_path.name, file_bytes, "application/pdf")},
        data={"doc_type": "sop"},
    )
    assert res1.status_code == 201
    data1 = res1.json()

    # Second upload with identical bytes
    res2 = client.post(
        "/ingest",
        files={"file": (pdf_path.name, file_bytes, "application/pdf")},
        data={"doc_type": "sop"},
    )
    assert res2.status_code == 201
    data2 = res2.json()

    # Document ID and counts must match
    assert data2["document_id"] == data1["document_id"]
    assert data2["parent_chunks"] == data1["parent_chunks"]
    assert data2["child_chunks"] == data1["child_chunks"]
    assert "duplicate detected by file hash" in data2["message"]


def test_ingest_replaces_old_document_on_different_content(db_session):
    """Assert re-uploading the same filename with different content deletes old parents/children and replaces the document."""
    pdf_path1 = Path("data/generated/sop_infection_control.pdf")
    pdf_path2 = Path("data/generated/sop_discharge_process.pdf")
    assert pdf_path1.exists() and pdf_path2.exists()

    filename = "test_replacement_lifecycle.pdf"

    # Ingest version 1
    res1 = ingest_document(db=db_session, source=pdf_path1, filename=filename, doc_type="sop")
    assert res1.status == "completed"
    doc1_id = res1.document_id

    parents1 = db_session.execute(select(Parent).where(Parent.document_id == doc1_id)).scalars().all()
    children1 = db_session.execute(select(Child).where(Child.document_id == doc1_id)).scalars().all()
    assert len(parents1) > 0 and len(children1) > 0

    # Ingest version 2 with different content under the exact same filename
    res2 = ingest_document(db=db_session, source=pdf_path2, filename=filename, doc_type="sop")
    assert res2.status == "completed"
    doc2_id = res2.document_id
    assert doc2_id != doc1_id

    # Verify old doc1 and its parents/children are deleted
    assert db_session.get(Document, doc1_id) is None
    old_p = db_session.execute(select(Parent).where(Parent.document_id == doc1_id)).scalars().all()
    old_c = db_session.execute(select(Child).where(Child.document_id == doc1_id)).scalars().all()
    assert len(old_p) == 0
    assert len(old_c) == 0

    # Verify only ONE document with this filename exists
    all_matching = db_session.execute(select(Document).where(Document.filename == filename)).scalars().all()
    assert len(all_matching) == 1
    assert all_matching[0].id == doc2_id


def test_ingest_defensive_parent_deduplication(db_session):
    """Assert defensive de-duplication skips parents whose normalized text hash already exists in the same document."""
    from unittest.mock import patch
    from backend.app.ingestion.chunker import ParentChunk

    pdf_path = Path("data/generated/sop_infection_control.pdf")
    duplicate_parents = [
        ParentChunk(
            section_title="1.0 Unique Section",
            text="This is unique clinical section content.",
            page_start=1,
            page_end=1,
        ),
        ParentChunk(
            section_title="1.0 Unique Section Duplicate",
            text="  This is  unique clinical   section content.  ",  # duplicate normalized text
            page_start=1,
            page_end=1,
        ),
        ParentChunk(
            section_title="2.0 Another Section",
            text="This is different clinical section content.",
            page_start=2,
            page_end=2,
        ),
    ]

    with patch("backend.app.ingestion.service.build_parents", return_value=duplicate_parents):
        result = ingest_document(
            db=db_session,
            source=pdf_path,
            filename="test_dedup_defense.pdf",
            doc_type="sop",
        )
        assert result.parent_chunks == 2
        # verify in DB
        db_parents = db_session.execute(
            select(Parent).where(Parent.document_id == result.document_id)
        ).scalars().all()
        assert len(db_parents) == 2
        titles = [p.section_title for p in db_parents]
        assert "1.0 Unique Section" in titles
        assert "2.0 Another Section" in titles
        assert "1.0 Unique Section Duplicate" not in titles


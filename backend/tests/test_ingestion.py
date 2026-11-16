"""Integration tests for MediDoc AI ingestion pipeline and API endpoints against PostgreSQL."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.app.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.db.models import Child, Document, Parent
from backend.app.db.session import SessionLocal, engine
from backend.app.ingestion.service import ingest_document
from backend.app.main import app

settings = get_settings()


@pytest.fixture(scope="module")
def db_session():
    """Ensure database schema is initialized and yield an isolated session."""
    init_db(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


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

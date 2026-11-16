"""FastAPI application entrypoint for MediDoc AI.

Configures CORS, database lifecycles, and core REST endpoints:
- GET /health: Health probe checking database connectivity and app status
- POST /ingest: Multi-part PDF upload and indexing (doc_type parameter)
- GET /documents: List indexed documents with parent/child chunk counts
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import List, Literal

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.db.models import Child, Document, Parent
from backend.app.db.session import get_db
from backend.app.ingestion.service import ingest_document

logger = logging.getLogger(__name__)
settings = get_settings()


# --- Pydantic Schemas ---

class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="API operational status")
    database: str = Field(..., description="PostgreSQL and pgvector connectivity status")
    app_env: str = Field(..., description="Environment tier")
    version: str = Field("1.0.0", description="Service semantic version")


class IngestResponse(BaseModel):
    """PDF ingestion response schema."""

    document_id: str = Field(..., description="UUID of the indexed document")
    filename: str = Field(..., description="Original filename of the ingested document")
    doc_type: str = Field(..., description="Document category (sop, discharge, or lab)")
    status: str = Field(..., description="Ingestion processing status")
    page_count: int = Field(..., description="Total pages in the PDF document")
    parent_chunks: int = Field(..., description="Number of parent sections created")
    child_chunks: int = Field(..., description="Number of child chunks embedded and indexed")
    message: str = Field("Document successfully ingested and indexed", description="Human-readable outcome")

    model_config = ConfigDict(from_attributes=True)


class DocumentItem(BaseModel):
    """Summary of an indexed document with chunk statistics."""

    id: str = Field(..., description="Document UUID")
    filename: str = Field(..., description="Filename")
    doc_type: str = Field(..., description="Category: sop, discharge, or lab")
    status: str = Field(..., description="Processing status")
    page_count: int = Field(..., description="Number of pages")
    parent_count: int = Field(..., description="Count of parent sections")
    child_count: int = Field(..., description="Count of child vector chunks")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# --- Application Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Perform application startup and shutdown tasks."""
    logger.info("Starting MediDoc AI API server...")
    try:
        init_db()
        logger.info("Database tables and pgvector extension ready.")
    except Exception as exc:
        logger.warning("Could not auto-initialize DB on startup (%s); will retry on request.", exc)
    yield
    logger.info("Shutting down MediDoc AI API server...")


# --- FastAPI Application ---

app = FastAPI(
    title="MediDoc AI API",
    description="Clinical document assistant for healthcare-IT: ingestion, RAG, and extraction.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check probe",
    tags=["System"],
)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Check API operational health and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1;"))
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "disconnected"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=HealthResponse(
                status="unhealthy",
                database=db_status,
                app_env=settings.app_env,
            ).model_dump(),
        )

    return HealthResponse(
        status="ok",
        database=db_status,
        app_env=settings.app_env,
    )


@app.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a PDF document",
    tags=["Ingestion"],
)
async def ingest_pdf(
    file: UploadFile = File(..., description="PDF document binary upload"),
    doc_type: Literal["sop", "discharge", "lab"] = Form(
        ..., description="Document type: sop (policy), discharge (summary), or lab (report)"
    ),
    db: Session = Depends(get_db),
) -> IngestResponse:
    """Upload, parse, chunk, embed, and index a PDF document into pgvector and full-text search."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Uploaded file must have a .pdf extension.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty.",
        )

    try:
        result = ingest_document(
            db=db,
            source=content,
            filename=file.filename,
            doc_type=doc_type.lower(),
        )
        return IngestResponse(
            document_id=str(result.document_id),
            filename=result.filename,
            doc_type=result.doc_type,
            status=result.status,
            page_count=result.page_count,
            parent_chunks=result.parent_chunks,
            child_chunks=result.child_chunks,
        )
    except Exception as exc:
        logger.error("Failed to ingest document %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index PDF document: {exc}",
        )


@app.get(
    "/documents",
    response_model=List[DocumentItem],
    summary="List all indexed documents with chunk statistics",
    tags=["Documents"],
)
def list_documents(db: Session = Depends(get_db)) -> List[DocumentItem]:
    """Retrieve all indexed documents alongside parent and child chunk counts."""
    parent_counts = (
        db.query(Parent.document_id, func.count(Parent.id).label("parent_count"))
        .group_by(Parent.document_id)
        .subquery()
    )
    child_counts = (
        db.query(Child.document_id, func.count(Child.id).label("child_count"))
        .group_by(Child.document_id)
        .subquery()
    )

    rows = (
        db.query(
            Document,
            func.coalesce(parent_counts.c.parent_count, 0).label("parent_count"),
            func.coalesce(child_counts.c.child_count, 0).label("child_count"),
        )
        .outerjoin(parent_counts, Document.id == parent_counts.c.document_id)
        .outerjoin(child_counts, Document.id == child_counts.c.document_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    results: List[DocumentItem] = []
    for doc, p_count, c_count in rows:
        results.append(
            DocumentItem(
                id=str(doc.id),
                filename=doc.filename,
                doc_type=doc.doc_type,
                status=doc.status,
                page_count=doc.page_count,
                parent_count=int(p_count),
                child_count=int(c_count),
                created_at=doc.created_at.isoformat() if doc.created_at else "",
            )
        )

    return results

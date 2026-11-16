"""FastAPI application entrypoint for MediDoc AI.

Configures CORS, database lifecycles, and core REST endpoints:
- GET /health: Health probe checking database connectivity and app status
- POST /ingest: Multi-part PDF upload and indexing (doc_type parameter)
- GET /documents: List indexed documents with parent/child chunk counts
"""

from __future__ import annotations

import hashlib
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, List, Literal, Optional

import torch
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.db.models import AuditLog, Child, Document, Extraction, Parent, ValidationIssue
from backend.app.db.session import get_db
from backend.app.extraction.extractor import extract_clinical_document
from backend.app.extraction.schema import ClinicalExtraction
from backend.app.extraction.validator import ValidationIssueSchema, validate_extraction
from backend.app.ingestion.embedder import get_embedder
from backend.app.ingestion.service import ingest_document
from backend.app.privacy.audit import record_audit_log
from backend.app.retrieval.qa import answer_question
from backend.app.retrieval.rerank import get_cross_encoder
from backend.app.retrieval.service import retrieve

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


class AskRequest(BaseModel):
    """Question answering query request schema."""

    question: str = Field(..., min_length=1, description="Question regarding hospital policies or SOPs")
    mode: Literal["naive", "parent_child", "hybrid", "hybrid_rerank"] = Field(
        default="hybrid_rerank",
        description="Retrieval strategy: naive, parent_child, hybrid, or hybrid_rerank",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")
    debug: bool = Field(
        default=False,
        description="When true, returns the full synthesized prompt text sent to the LLM",
    )


class SourceItem(BaseModel):
    """Provenance citation for an individual retrieved passage."""

    document: str = Field(..., description="Document filename")
    pages: str = Field(..., description="Page label (e.g. 'p. 2' or 'pp. 2-3')")
    citation: str = Field(..., description="Citation string: [document, pages]")
    section_title: str | None = Field(None, description="Section heading")
    score: float = Field(..., description="Relevance score from retrieval")
    parent_id: str | None = Field(None, description="Parent section UUID for parent-expanded modes")


class AskResponse(BaseModel):
    """Question answering response schema."""

    answer: str = Field(..., description="Synthesized clinical policy answer")
    sources: List[SourceItem] = Field(..., description="Cited source documents and pages")
    retrieved_ids: List[str] = Field(..., description="Retrieved chunk or section IDs")
    timings: dict[str, Any] = Field(..., description="Per-stage latency breakdown and model metadata")
    prompt: Optional[str] = Field(
        default=None,
        description="Full prompt text sent to the LLM (only present when debug=true)",
    )
    prompt_version: str = Field(..., description="Version tag of the prompt template")


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


class ExtractResponse(BaseModel):
    """Clinical document extraction response schema."""

    extraction: ClinicalExtraction = Field(..., description="Structured clinical data extracted from document")
    validation_issues: List[ValidationIssueSchema] = Field(..., description="Validation issues identified by rules")
    pii_items_masked: int = Field(..., description="Total count of PII/PHI items redacted prior to LLM call")
    prompt_version: str = Field(..., description="Version of extraction prompt template")
    llm_model: str = Field(..., description="LLM model identifier used for extraction")
    latency_ms: float = Field(..., description="Extraction latency in milliseconds")

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

    # Warm up embedding model and reranker once at API startup
    try:
        logger.info("Warming up embedding model and cross-encoder reranker...")
        embedder = get_embedder()
        embedder.embed_query("warmup query")
        reranker = get_cross_encoder()
        with torch.no_grad():
            reranker.predict([["warmup query", "warmup passage"]], batch_size=1, show_progress_bar=False)
        logger.info("Embedding and reranker models warmed up successfully.")
    except Exception as exc:
        logger.warning("Could not warm up models on startup: %s", exc)

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
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

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

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 20 MB (received {len(content)} bytes).",
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Uploaded file content does not have a valid PDF signature.",
        )

    t0 = time.perf_counter()
    try:
        result = ingest_document(
            db=db,
            source=content,
            filename=file.filename,
            doc_type=doc_type.lower(),
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0
        record_audit_log(
            db=db,
            endpoint="/ingest",
            document_id=result.document_id,
            pii_items_masked=0,
            latency_ms=latency_ms,
            status="success",
        )
        message = (
            "Document already ingested (duplicate detected by file hash)"
            if getattr(result, "is_duplicate", False)
            else "Document successfully ingested and indexed"
        )
        return IngestResponse(
            document_id=str(result.document_id),
            filename=result.filename,
            doc_type=result.doc_type,
            status=result.status,
            page_count=result.page_count,
            parent_chunks=result.parent_chunks,
            child_chunks=result.child_chunks,
            message=message,
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            record_audit_log(
                db=db,
                endpoint="/ingest",
                document_id=None,
                pii_items_masked=0,
                latency_ms=latency_ms,
                status="error",
            )
        except Exception:
            pass
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


@app.post(
    "/ask",
    response_model=AskResponse,
    response_model_exclude_none=True,
    summary="Answer a clinical or policy question using RAG with source citations",
    tags=["Retrieval & QA"],
)
def ask_question_endpoint(
    request: AskRequest,
    db: Session = Depends(get_db),
) -> AskResponse:
    """Retrieve grounded context passages across SOPs and generate a cited clinical policy answer.

    - Supports retrieval modes: naive, parent_child, hybrid, hybrid_rerank
    - Enforces answers derived solely from retrieved context
    - Cites sources as [document, pages]
    - Returns answer, sources, retrieved IDs, stage timings, prompt (only when debug=true), and prompt_version
    """
    t0 = time.perf_counter()
    try:
        retrieval_res = retrieve(
            question=request.question,
            mode=request.mode,
            top_k=request.top_k,
            db=db,
        )
        answer_res = answer_question(retrieval_response=retrieval_res)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        record_audit_log(
            db=db,
            endpoint="/ask",
            document_id=None,
            pii_items_masked=0,
            latency_ms=latency_ms,
            status="success",
        )

        logger.info(
            "Completed /ask request (mode=%s): model=%s, generation_ms=%s ms, timings=%s",
            request.mode,
            answer_res.timings.get("llm_model"),
            answer_res.timings.get("generation_ms"),
            answer_res.timings,
        )

        return AskResponse(
            answer=answer_res.answer,
            sources=[
                SourceItem(
                    document=src.document,
                    pages=src.pages,
                    citation=src.citation,
                    section_title=src.section_title,
                    score=src.score,
                    parent_id=src.parent_id,
                )
                for src in answer_res.sources
            ],
            retrieved_ids=answer_res.retrieved_ids,
            timings=answer_res.timings,
            prompt=answer_res.prompt if request.debug else None,
            prompt_version=answer_res.prompt_version,
        )
    except TimeoutError as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            record_audit_log(
                db=db,
                endpoint="/ask",
                document_id=None,
                pii_items_masked=0,
                latency_ms=latency_ms,
                status="error",
            )
        except Exception:
            pass
        logger.error("LLM timeout processing question '%s': %s", request.question, exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"LLM request timed out: {exc}",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            record_audit_log(
                db=db,
                endpoint="/ask",
                document_id=None,
                pii_items_masked=0,
                latency_ms=latency_ms,
                status="error",
            )
        except Exception:
            pass
        logger.error("Error processing question '%s': %s", request.question, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {exc}",
        )


@app.post(
    "/extract",
    response_model=ExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured clinical JSON and validation issues from a PDF report",
    tags=["Extraction & Validation"],
)
async def extract_pdf_endpoint(
    file: UploadFile = File(..., description="PDF clinical document (discharge summary or lab report)"),
    db: Session = Depends(get_db),
) -> ExtractResponse:
    """Upload a clinical PDF, mask PII, extract structured JSON via LLM, and run validation rules.

    - Validates PDF extension and signature
    - Rejects files over 20 MB
    - Masks names, phone numbers, emails, MRNs before LLM invocation
    - Never returns or logs masked text or raw clinical text
    - Persists extraction and validation issues in database
    - Records metadata-only audit log row
    """
    MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
    t0 = time.perf_counter()

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

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 20 MB (received {len(content)} bytes).",
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Uploaded file content does not have a valid PDF signature.",
        )

    file_hash = hashlib.sha256(content).hexdigest()
    doc_type = "lab" if "lab" in file.filename.lower() else "discharge"

    # Find or initialize document record for foreign-key attachment
    doc = db.query(Document).filter(Document.file_hash == file_hash).first()
    if not doc:
        doc = Document(
            filename=file.filename,
            doc_type=doc_type,
            status="extracted",
            page_count=1,
            file_hash=file_hash,
        )
        db.add(doc)
        db.flush()

    try:
        extraction_res = extract_clinical_document(
            source=content,
            filename=file.filename,
        )
    except TimeoutError as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            record_audit_log(
                db=db,
                endpoint="/extract",
                document_id=doc.id,
                pii_items_masked=0,
                latency_ms=latency_ms,
                status="error",
            )
        except Exception:
            pass
        logger.error("LLM timeout during extraction for %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"LLM extraction request timed out: {exc}",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            record_audit_log(
                db=db,
                endpoint="/extract",
                document_id=doc.id,
                pii_items_masked=0,
                latency_ms=latency_ms,
                status="error",
            )
        except Exception:
            pass
        logger.error("Extraction failed for %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract structured data from PDF: {exc}",
        )

    # Update document page count
    doc.page_count = extraction_res.page_count

    # Persist extraction row
    extraction_row = Extraction(
        document_id=doc.id,
        json_result=extraction_res.raw_dict,
        model=extraction_res.llm_model,
        prompt_version=extraction_res.prompt_version,
    )
    db.add(extraction_row)
    db.flush()

    # Persist validation issue rows
    for issue in extraction_res.validation_issues:
        v_issue = ValidationIssue(
            extraction_id=extraction_row.id,
            field=issue.field,
            rule=issue.rule,
            severity=issue.severity,
            message=issue.message,
        )
        db.add(v_issue)

    total_latency_ms = (time.perf_counter() - t0) * 1000.0

    # Write audit log row
    record_audit_log(
        db=db,
        endpoint="/extract",
        document_id=doc.id,
        pii_items_masked=extraction_res.pii_items_masked,
        latency_ms=total_latency_ms,
        status="success",
    )

    db.commit()

    return ExtractResponse(
        extraction=extraction_res.extraction,
        validation_issues=extraction_res.validation_issues,
        pii_items_masked=extraction_res.pii_items_masked,
        prompt_version=extraction_res.prompt_version,
        llm_model=extraction_res.llm_model,
        latency_ms=round(total_latency_ms, 2),
    )


@app.post(
    "/validate",
    response_model=List[ValidationIssueSchema],
    status_code=status.HTTP_200_OK,
    summary="Validate extracted clinical data against hospital rules",
    tags=["Extraction & Validation"],
)
def validate_clinical_data_endpoint(
    extraction: ClinicalExtraction,
    db: Session = Depends(get_db),
) -> List[ValidationIssueSchema]:
    """Validate extracted clinical JSON against SPEC.md rules.

    Checks:
    - discharge_date must not be before admission_date
    - every medication has a dose and a unit
    - diagnosis list is not empty
    - age between 0 and 120

    Returns list of validation issues found. Never stores or logs clinical text.
    """
    t0 = time.perf_counter()
    try:
        issues = validate_extraction(extraction)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        record_audit_log(
            db=db,
            endpoint="/validate",
            document_id=None,
            pii_items_masked=0,
            latency_ms=latency_ms,
            status="success",
        )
        return issues
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        try:
            record_audit_log(
                db=db,
                endpoint="/validate",
                document_id=None,
                pii_items_masked=0,
                latency_ms=latency_ms,
                status="error",
            )
        except Exception:
            pass
        logger.error("Validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate clinical data: {exc}",
        )


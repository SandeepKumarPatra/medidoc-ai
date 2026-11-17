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
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, List, Literal, Optional

import torch
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db.init_db import init_db
from backend.app.db.models import AuditLog, Child, Document, EvalResult, EvalRun, Extraction, Parent, ValidationIssue
from backend.app.db.session import SessionLocal, get_db
from backend.app.eval.metrics import compare_hybrid_vs_dense, compute_category_breakdown
from backend.app.eval.runner import (
    RERANKER_BGE,
    RERANKER_MINILM,
    load_sop_questions,
    run_answers_evaluation,
    run_extraction_evaluation,
    run_retrieval_mode_evaluation,
    run_unanswerable_evaluation,
)
from backend.app.eval.schemas import (
    EvalResultsResponse,
    EvalRunRequest,
    EvalRunResponse,
    ModeEvalSummary,
    QuestionEvalItem,
)
from backend.app.extraction.extractor import extract_clinical_document
from backend.app.extraction.schema import ClinicalExtraction
from backend.app.extraction.validator import ValidationIssueSchema, validate_extraction
from backend.app.ingestion.embedder import get_embedder
from backend.app.ingestion.parser import get_document_converter
from backend.app.ingestion.service import ingest_document
from backend.app.privacy.audit import record_audit_log
from backend.app.retrieval.qa import CitedSource, answer_question
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
    page_start: int = Field(..., description="First page number of the source range")
    page_end: int = Field(..., description="Last page number of the source range")
    citation: str = Field(..., description="Citation string: [document, pages]")
    section_title: str | None = Field(None, description="Section heading")
    score: float = Field(..., description="Relevance score from retrieval")
    parent_id: str | None = Field(None, description="Parent section UUID for parent-expanded modes")


class AskResponse(BaseModel):
    """Question answering response schema."""

    answer: str = Field(..., description="Synthesized clinical policy answer")
    sources: List[SourceItem] = Field(..., description="Cited source documents and pages")
    citations: List[CitedSource] = Field(
        default_factory=list,
        description="Sources actually cited in the synthesized answer",
    )
    dropped_citations: List[str] = Field(
        default_factory=list,
        description="Invalid or non-existent citation tags dropped from the answer",
    )
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
    parse_ms: float = Field(0.0, description="PDF parsing stage latency in milliseconds")
    mask_ms: float = Field(0.0, description="PII masking stage latency in milliseconds")
    llm_ms: float = Field(0.0, description="LLM structured generation stage latency in milliseconds")
    total_ms: float = Field(..., description="Total request latency in milliseconds")
    latency_ms: float = Field(..., description="Extraction latency in milliseconds (legacy alias for total_ms)")

    model_config = ConfigDict(from_attributes=True)


class StatsOverviewResponse(BaseModel):
    """Aggregated statistics across documents, extractions, validation, and audit logs."""

    documents_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Document counts grouped by doc_type (sop, discharge, lab)",
    )
    total_documents: int = Field(0, description="Total count of indexed documents")
    parents_total: int = Field(0, description="Total count of parent sections")
    children_total: int = Field(0, description="Total count of child chunks")
    extractions_total: int = Field(0, description="Total number of extraction attempts stored")
    extractions_with_issues: int = Field(0, description="Count of extractions with at least one validation issue")
    issue_rate: float = Field(0.0, description="Fraction of extractions with validation issues (0.0 to 1.0)")
    issue_counts_by_rule: dict[str, int] = Field(
        default_factory=dict,
        description="Validation issue counts grouped by rule name",
    )
    asks_total: int = Field(0, description="Total number of Q&A requests logged in audit_log")
    avg_latency_ms_by_endpoint: dict[str, float] = Field(
        default_factory=dict,
        description="Average latency in ms grouped by endpoint",
    )
    total_pii_masked: int = Field(0, description="Total count of PII items masked across all requests")

    model_config = ConfigDict(from_attributes=True)


class AuditLogRow(BaseModel):
    """Metadata-only audit log record representation."""

    id: str = Field(..., description="Audit entry UUID")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    endpoint: str = Field(..., description="API endpoint called")
    document_id: Optional[str] = Field(None, description="Document UUID if associated")
    pii_items_masked: int = Field(..., description="Number of PII items masked")
    latency_ms: float = Field(..., description="Request latency in ms")
    status: str = Field(..., description="Status (success, error)")

    model_config = ConfigDict(from_attributes=True)


class DailyCallCount(BaseModel):
    """Daily invocation count breakdown for charting."""

    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    endpoint: str = Field(..., description="API endpoint")
    count: int = Field(..., description="Call count for that endpoint on that date")

    model_config = ConfigDict(from_attributes=True)


class AuditStatsResponse(BaseModel):
    """Audit log inspection and historical frequency statistics."""

    recent_logs: List[AuditLogRow] = Field(
        default_factory=list,
        description="Recent audit log rows (metadata only, newest first)",
    )
    totals_by_endpoint: dict[str, int] = Field(
        default_factory=dict,
        description="Total historical call counts per endpoint",
    )
    calls_by_day: List[DailyCallCount] = Field(
        default_factory=list,
        description="Daily call counts for the last 14 days by endpoint for charts",
    )
    total_count: int = Field(0, description="Total matching audit log rows in the database")

    model_config = ConfigDict(from_attributes=True)


class ExtractionListItem(BaseModel):
    """Summary of a stored extraction run without raw document text."""

    id: str = Field(..., description="Extraction UUID")
    document_id: str = Field(..., description="Associated document UUID")
    filename: str = Field(..., description="Source document filename")
    doc_type: str = Field(..., description="Document type (discharge, lab, etc.)")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    issue_count: int = Field(..., description="Count of validation issues flagged")
    model: str = Field(..., description="LLM model identifier")
    prompt_version: str = Field(..., description="Extraction prompt version")

    model_config = ConfigDict(from_attributes=True)


class ExtractionDetailResponse(BaseModel):
    """Detailed view of an individual clinical extraction with structured JSON and rule issues."""

    id: str = Field(..., description="Extraction UUID")
    document_id: str = Field(..., description="Associated document UUID")
    filename: str = Field(..., description="Source document filename")
    doc_type: str = Field(..., description="Document type (discharge, lab, etc.)")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    model: str = Field(..., description="LLM model identifier")
    prompt_version: str = Field(..., description="Extraction prompt version")
    json_result: dict[str, Any] = Field(..., description="Extracted structured clinical JSON")
    validation_issues: List[ValidationIssueSchema] = Field(
        default_factory=list,
        description="Validation issues flagged against this extraction",
    )

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

    # Warm up embedding model, reranker, and Docling converter once at API startup
    try:
        logger.info("Warming up embedding model, cross-encoder reranker, and Docling parser...")
        embedder = get_embedder()
        embedder.embed_query("warmup query")
        reranker = get_cross_encoder()
        with torch.no_grad():
            reranker.predict([["warmup query", "warmup passage"]], batch_size=1, show_progress_bar=False)
        get_document_converter()
        logger.info("Embedding, reranker, and Docling converter warmed up successfully.")
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
                    page_start=src.page_start,
                    page_end=src.page_end,
                    citation=src.citation,
                    section_title=src.section_title,
                    score=src.score,
                    parent_id=src.parent_id,
                )
                for src in answer_res.sources
            ],
            citations=answer_res.citations,
            dropped_citations=answer_res.timings.get("dropped_citations", []),
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
        parse_ms=round(extraction_res.parse_ms, 2),
        mask_ms=round(extraction_res.mask_ms, 2),
        llm_ms=round(extraction_res.llm_ms, 2),
        total_ms=round(total_latency_ms, 2),
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


# --- Phase 4 Endpoints: Statistics and Extractions ---

@app.get(
    "/stats/overview",
    response_model=StatsOverviewResponse,
    summary="Get aggregated statistics across documents, extractions, and queries",
    tags=["Statistics"],
)
def get_stats_overview(db: Session = Depends(get_db)) -> StatsOverviewResponse:
    """Aggregated statistics computed directly from the database:
    - documents by doc_type (sop, discharge, lab)
    - total parents and children chunks
    - extractions_total and extractions_with_issues
    - issue_rate (ratio of extractions with issues)
    - issue counts per rule name
    - asks_total (total Q&A requests in audit_log)
    - average latency_ms per endpoint
    - total PII items masked
    """
    try:
        doc_type_rows = (
            db.query(Document.doc_type, func.count(Document.id))
            .group_by(Document.doc_type)
            .all()
        )
        documents_by_type = {
            str(row[0]): int(row[1]) for row in doc_type_rows if row[0] is not None
        }
        total_documents = sum(documents_by_type.values())

        parents_total = db.query(func.count(Parent.id)).scalar() or 0
        children_total = db.query(func.count(Child.id)).scalar() or 0

        extractions_total = db.query(func.count(Extraction.id)).scalar() or 0
        extractions_with_issues = (
            db.query(func.count(func.distinct(ValidationIssue.extraction_id)))
            .filter(ValidationIssue.extraction_id.isnot(None))
            .scalar()
            or 0
        )
        issue_rate = (
            round(extractions_with_issues / extractions_total, 4)
            if extractions_total > 0
            else 0.0
        )

        rule_rows = (
            db.query(ValidationIssue.rule, func.count(ValidationIssue.id))
            .group_by(ValidationIssue.rule)
            .all()
        )
        issue_counts_by_rule = {
            str(row[0]): int(row[1]) for row in rule_rows if row[0] is not None
        }

        asks_total = (
            db.query(func.count(AuditLog.id))
            .filter(AuditLog.endpoint == "/ask")
            .scalar()
            or 0
        )

        latency_rows = (
            db.query(AuditLog.endpoint, func.avg(AuditLog.latency_ms))
            .group_by(AuditLog.endpoint)
            .all()
        )
        avg_latency_ms_by_endpoint = {
            str(row[0]): round(float(row[1]), 2)
            for row in latency_rows
            if row[0] is not None and row[1] is not None
        }

        total_pii_masked = (
            db.query(func.coalesce(func.sum(AuditLog.pii_items_masked), 0)).scalar()
            or 0
        )

        return StatsOverviewResponse(
            documents_by_type=documents_by_type,
            total_documents=total_documents,
            parents_total=int(parents_total),
            children_total=int(children_total),
            extractions_total=int(extractions_total),
            extractions_with_issues=int(extractions_with_issues),
            issue_rate=float(issue_rate),
            issue_counts_by_rule=issue_counts_by_rule,
            asks_total=int(asks_total),
            avg_latency_ms_by_endpoint=avg_latency_ms_by_endpoint,
            total_pii_masked=int(total_pii_masked),
        )
    except Exception as exc:
        logger.error("Failed to compute stats overview: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load statistics overview: {exc}",
        )


@app.get(
    "/stats/audit",
    response_model=AuditStatsResponse,
    summary="Retrieve audit log entries and historical usage trends",
    tags=["Statistics"],
)
def get_stats_audit(
    limit: int = Query(
        default=50, ge=1, le=500, description="Max recent log entries to return"
    ),
    endpoint: Optional[str] = Query(
        default=None, description="Optional endpoint filter (e.g. /ask)"
    ),
    db: Session = Depends(get_db),
) -> AuditStatsResponse:
    """Retrieve recent audit_log rows (metadata only, newest first), plus totals per endpoint,
    and calls_by_day for the last 14 days (date, endpoint, count) for dashboard charts.
    """
    try:
        log_query = db.query(AuditLog)
        if endpoint and endpoint.strip():
            log_query = log_query.filter(AuditLog.endpoint == endpoint.strip())

        total_matching = log_query.count()
        recent_rows = (
            log_query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        )

        recent_logs = [
            AuditLogRow(
                id=str(row.id),
                timestamp=row.timestamp.isoformat() if row.timestamp else "",
                endpoint=row.endpoint,
                document_id=str(row.document_id) if row.document_id else None,
                pii_items_masked=row.pii_items_masked,
                latency_ms=round(row.latency_ms, 2),
                status=row.status,
            )
            for row in recent_rows
        ]

        totals_query = db.query(
            AuditLog.endpoint, func.count(AuditLog.id)
        ).group_by(AuditLog.endpoint)
        totals_by_endpoint = {
            str(row[0]): int(row[1]) for row in totals_query.all() if row[0] is not None
        }

        # Calls by day for the last 14 days
        fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
        day_expr = func.to_char(AuditLog.timestamp, "YYYY-MM-DD").label("day")
        day_query = (
            db.query(day_expr, AuditLog.endpoint, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.timestamp >= fourteen_days_ago)
            .group_by(day_expr, AuditLog.endpoint)
            .order_by(day_expr.asc(), AuditLog.endpoint.asc())
        )
        if endpoint and endpoint.strip():
            day_query = day_query.filter(AuditLog.endpoint == endpoint.strip())

        calls_by_day = [
            DailyCallCount(
                date=str(row[0]),
                endpoint=str(row[1]),
                count=int(row[2]),
            )
            for row in day_query.all()
            if row[0] is not None
        ]

        return AuditStatsResponse(
            recent_logs=recent_logs,
            totals_by_endpoint=totals_by_endpoint,
            calls_by_day=calls_by_day,
            total_count=total_matching,
        )
    except Exception as exc:
        logger.error("Failed to query audit statistics: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query audit statistics: {exc}",
        )


@app.get(
    "/extractions",
    response_model=List[ExtractionListItem],
    summary="List recent extractions with validation issue counts",
    tags=["Extraction & Validation"],
)
def list_extractions(
    limit: int = Query(
        default=20, ge=1, le=100, description="Max extractions to return"
    ),
    db: Session = Depends(get_db),
) -> List[ExtractionListItem]:
    """Retrieve recent extractions with id, source document filename, created_at,
    issue_count, llm model, and prompt_version. Never returns raw document text.
    """
    try:
        issue_counts = (
            db.query(
                ValidationIssue.extraction_id,
                func.count(ValidationIssue.id).label("issue_count"),
            )
            .group_by(ValidationIssue.extraction_id)
            .subquery()
        )

        rows = (
            db.query(
                Extraction,
                Document.filename,
                Document.doc_type,
                func.coalesce(issue_counts.c.issue_count, 0).label("issue_count"),
            )
            .join(Document, Extraction.document_id == Document.id)
            .outerjoin(issue_counts, Extraction.id == issue_counts.c.extraction_id)
            .order_by(Extraction.created_at.desc())
            .limit(limit)
            .all()
        )

        results: List[ExtractionListItem] = []
        for ext, fname, dtype, icount in rows:
            results.append(
                ExtractionListItem(
                    id=str(ext.id),
                    document_id=str(ext.document_id),
                    filename=fname,
                    doc_type=dtype,
                    created_at=ext.created_at.isoformat() if ext.created_at else "",
                    issue_count=int(icount),
                    model=ext.model,
                    prompt_version=ext.prompt_version,
                )
            )
        return results
    except Exception as exc:
        logger.error("Failed to list extractions: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve extractions list: {exc}",
        )


@app.get(
    "/extractions/{id}",
    response_model=ExtractionDetailResponse,
    summary="Get structured JSON result and validation issues for an extraction",
    tags=["Extraction & Validation"],
)
def get_extraction_detail(
    id: str,
    db: Session = Depends(get_db),
) -> ExtractionDetailResponse:
    """Retrieve the stored JSON result and validation issues for a single extraction.
    Never returns raw document text.
    """
    try:
        extraction_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid extraction UUID format: '{id}'",
        )

    extraction = (
        db.query(Extraction).filter(Extraction.id == extraction_uuid).first()
    )
    if not extraction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction with ID '{id}' not found.",
        )

    doc = db.query(Document).filter(Document.id == extraction.document_id).first()
    filename = doc.filename if doc else "unknown.pdf"
    doc_type = doc.doc_type if doc else "unknown"

    issues = (
        db.query(ValidationIssue)
        .filter(ValidationIssue.extraction_id == extraction.id)
        .all()
    )
    validation_issues = [
        ValidationIssueSchema(
            field=issue.field,
            rule=issue.rule,
            severity=issue.severity,
            message=issue.message,
        )
        for issue in issues
    ]

    return ExtractionDetailResponse(
        id=str(extraction.id),
        document_id=str(extraction.document_id),
        filename=filename,
        doc_type=doc_type,
        created_at=extraction.created_at.isoformat() if extraction.created_at else "",
        model=extraction.model,
        prompt_version=extraction.prompt_version,
        json_result=extraction.json_result,
        validation_issues=validation_issues,
    )


# ==============================================================================
# Phase 7: Evaluation Harness Endpoints
# ==============================================================================

def _background_eval_task(
    run_configs: List[Tuple[str, Optional[str], Optional[str], uuid.UUID]],
    with_answers: bool,
    with_extraction: bool,
) -> None:
    """Background worker for executing evaluation benchmark runs."""
    with SessionLocal() as db:
        try:
            questions = load_sop_questions()
            for mode, reranker, note, r_uuid in run_configs:
                run_retrieval_mode_evaluation(
                    db=db,
                    questions=questions,
                    mode=mode,
                    top_k=5,
                    reranker_model=reranker,
                    save_to_db=True,
                    notes=note,
                    run_id=r_uuid,
                )
            if with_answers:
                run_answers_evaluation(
                    db=db,
                    questions=questions,
                    sample_size=15,
                    mode="hybrid",
                )
                run_answers_evaluation(
                    db=db,
                    questions=questions,
                    sample_size=15,
                    mode="hybrid_rerank",
                )
                run_unanswerable_evaluation(
                    db=db,
                    mode="hybrid",
                )
            if with_extraction:
                run_extraction_evaluation()
        except Exception as exc:
            logger.error("Background evaluation task failed: %s", exc, exc_info=True)


@app.post(
    "/eval/run",
    response_model=EvalRunResponse,
    summary="Trigger asynchronous evaluation run across retrieval modes",
    tags=["Evaluation"],
)
def run_evaluation(
    request: Optional[EvalRunRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> EvalRunResponse:
    """Launch evaluation benchmark across configured retrieval modes in the background."""
    req = request or EvalRunRequest()
    requested_modes = req.modes

    configs: List[Tuple[str, Optional[str], Optional[str], uuid.UUID]] = []
    if "all" in requested_modes:
        configs = [
            ("naive", None, "Naive child vector search", uuid.uuid4()),
            ("parent_child", None, "Dense child search with parent expansion", uuid.uuid4()),
            ("hybrid", None, "Dense + sparse full-text with RRF (k=60)", uuid.uuid4()),
            ("hybrid_rerank", RERANKER_BGE, "Hybrid with BAAI/bge-reranker-base", uuid.uuid4()),
            ("hybrid_rerank", RERANKER_MINILM, "Hybrid with cross-encoder/ms-marco-MiniLM-L-6-v2", uuid.uuid4()),
        ]
    else:
        for m in requested_modes:
            if m == "naive":
                configs.append(("naive", None, req.notes or "Naive child vector search", uuid.uuid4()))
            elif m == "parent_child":
                configs.append(("parent_child", None, req.notes or "Dense child search with parent expansion", uuid.uuid4()))
            elif m == "hybrid":
                configs.append(("hybrid", None, req.notes or "Dense + sparse full-text with RRF (k=60)", uuid.uuid4()))
            elif m in ("hybrid_rerank", "hybrid_rerank_bge"):
                configs.append(("hybrid_rerank", RERANKER_BGE, req.notes or "Hybrid with BAAI/bge-reranker-base", uuid.uuid4()))
            elif m in ("hybrid_rerank_minilm", "hybrid_rerank_msmarco"):
                configs.append(("hybrid_rerank", RERANKER_MINILM, req.notes or "Hybrid with cross-encoder/ms-marco-MiniLM-L-6-v2", uuid.uuid4()))

    if not configs:
        configs = [("hybrid_rerank", RERANKER_BGE, "Hybrid with BAAI/bge-reranker-base", uuid.uuid4())]

    run_ids_map: Dict[str, str] = {}
    for m, r, _, r_uuid in configs:
        label = "hybrid_rerank_minilm" if r == RERANKER_MINILM else ("hybrid_rerank" if r == RERANKER_BGE else m)
        run_ids_map[label] = str(r_uuid)

    primary_run_id = str(configs[0][3])
    background_tasks.add_task(_background_eval_task, configs, req.with_answers, req.with_extraction)

    return EvalRunResponse(
        run_id=primary_run_id,
        run_ids=run_ids_map,
        status="started",
        message=f"Evaluation launched for {len(configs)} mode(s) in background.",
    )


@app.get(
    "/eval/results",
    response_model=EvalResultsResponse,
    summary="Get latest evaluation results and ablation metrics per mode",
    tags=["Evaluation"],
)
def get_eval_results(
    db: Session = Depends(get_db),
) -> EvalResultsResponse:
    """Retrieve the latest evaluation benchmark run and ablation metrics per retrieval mode."""
    try:
        questions = load_sop_questions()
        q_map = {q["id"]: q for q in questions}

        modes_query = db.query(EvalRun.mode).distinct().all()
        distinct_modes = [r[0] for r in modes_query if r[0]]

        mode_summaries: List[ModeEvalSummary] = []
        eval_items_by_mode: Dict[str, List[QuestionEvalItem]] = {}
        for m in distinct_modes:
            latest_run = (
                db.query(EvalRun)
                .filter(EvalRun.mode == m)
                .order_by(EvalRun.created_at.desc())
                .first()
            )
            if not latest_run:
                continue

            results = db.query(EvalResult).filter(EvalResult.run_id == latest_run.id).all()
            if not results:
                continue

            eval_items: List[QuestionEvalItem] = []
            for r in results:
                q_data = q_map.get(r.question_id, {})
                rank_val = round(1.0 / r.reciprocal_rank) if r.reciprocal_rank > 0 else None
                cat = q_data.get("category", "single")
                both_hit = r.hit if cat == "compound" else None
                eval_items.append(
                    QuestionEvalItem(
                        question_id=r.question_id,
                        question=q_data.get("question"),
                        category=cat,
                        paraphrased=bool(q_data.get("paraphrased", False)),
                        expected_doc=r.expected_doc,
                        expected_section=q_data.get("expected_section"),
                        expected_sections=q_data.get("expected_sections"),
                        hit=r.hit,
                        rank=rank_val,
                        reciprocal_rank=r.reciprocal_rank,
                        latency_ms=r.latency_ms,
                        both_hit_at_5=both_hit,
                    )
                )

            eval_items_by_mode[m] = eval_items
            breakdown = compute_category_breakdown(eval_items)
            summary = ModeEvalSummary(
                run_id=str(latest_run.id),
                mode=latest_run.mode,
                created_at=latest_run.created_at.isoformat() if latest_run.created_at else "",
                notes=latest_run.notes,
                overall=breakdown.all,
                single=breakdown.single,
                paraphrased=breakdown.paraphrased,
                keyword=breakdown.keyword,
                compound=breakdown.compound,
            )
            mode_summaries.append(summary)

        mode_order = {
            "naive": 1,
            "parent_child": 2,
            "hybrid": 3,
            "hybrid_rerank": 4,
            "hybrid_rerank_bge": 4,
            "hybrid_rerank_minilm": 5,
        }
        mode_summaries.sort(key=lambda s: (mode_order.get(s.mode, 99), s.created_at))

        hybrid_vs_dense = None
        if "parent_child" in eval_items_by_mode and "hybrid" in eval_items_by_mode:
            hybrid_vs_dense = compare_hybrid_vs_dense(
                eval_items_by_mode["parent_child"],
                eval_items_by_mode["hybrid"],
            )

        return EvalResultsResponse(runs=mode_summaries, hybrid_vs_dense=hybrid_vs_dense)
    except Exception as exc:
        logger.error("Failed to query eval results: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query evaluation results: {exc}",
        )


@app.get(
    "/eval/runs/{run_id}/questions",
    response_model=List[QuestionEvalItem],
    summary="Get per-question retrieval performance details for an evaluation run",
    tags=["Evaluation"],
)
def get_eval_run_questions(
    run_id: str,
    db: Session = Depends(get_db),
) -> List[QuestionEvalItem]:
    """Retrieve per-question retrieval hit, rank, and retrieved section titles for a given run_id."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invalid eval run UUID format: '{run_id}'",
        )

    eval_run = db.query(EvalRun).filter(EvalRun.id == run_uuid).first()
    if not eval_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run with ID '{run_id}' not found.",
        )

    results = db.query(EvalResult).filter(EvalResult.run_id == run_uuid).all()
    questions = load_sop_questions()
    q_map = {q["id"]: q for q in questions}

    all_chunk_ids: Set[str] = set()
    for r in results:
        if r.retrieved_ids and isinstance(r.retrieved_ids, list):
            for cid in r.retrieved_ids:
                all_chunk_ids.add(str(cid))

    chunk_uuid_list = []
    for cid_str in all_chunk_ids:
        try:
            chunk_uuid_list.append(uuid.UUID(cid_str))
        except ValueError:
            continue

    parent_map: Dict[str, Tuple[str, str]] = {}
    if chunk_uuid_list:
        parents_query = (
            db.query(Parent, Document.filename)
            .join(Document, Parent.document_id == Document.id)
            .filter(Parent.id.in_(chunk_uuid_list))
            .all()
        )
        for p, fname in parents_query:
            parent_map[str(p.id)] = (p.section_title or "", fname)

        children_query = (
            db.query(Child, Parent.section_title, Document.filename)
            .join(Parent, Child.parent_id == Parent.id)
            .join(Document, Child.document_id == Document.id)
            .filter(Child.id.in_(chunk_uuid_list))
            .all()
        )
        for c, p_sec, fname in children_query:
            parent_map[str(c.id)] = (p_sec or "", fname)

    items: List[QuestionEvalItem] = []
    for r in results:
        q_data = q_map.get(r.question_id, {})
        rank_val = round(1.0 / r.reciprocal_rank) if r.reciprocal_rank > 0 else None

        sec_titles = []
        doc_names = []
        if r.retrieved_ids and isinstance(r.retrieved_ids, list):
            for cid in r.retrieved_ids:
                sec_title, doc_name = parent_map.get(str(cid), ("", ""))
                sec_titles.append(sec_title)
                doc_names.append(doc_name)

        cat = q_data.get("category", "single")
        both_hit = r.hit if cat == "compound" else None
        items.append(
            QuestionEvalItem(
                question_id=r.question_id,
                question=q_data.get("question"),
                category=cat,
                paraphrased=bool(q_data.get("paraphrased", False)),
                expected_doc=r.expected_doc,
                expected_section=q_data.get("expected_section"),
                expected_sections=q_data.get("expected_sections"),
                hit=r.hit,
                rank=rank_val,
                reciprocal_rank=r.reciprocal_rank,
                latency_ms=r.latency_ms,
                both_hit_at_5=both_hit,
                retrieved_section_titles=sec_titles,
                retrieved_docs=doc_names,
            )
        )

    return items



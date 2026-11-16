# Architecture & Design Decisions

This document tracks key architectural decisions, rationale, and documented trade-offs for MediDoc AI.

---

## Decision 001: Phase 0 Foundation, Database, and Synthetic Generation

- **What was built:**
  - Initial directory layout separating `backend`, `frontend`, `data`, and `docs`.
  - Docker Compose configuration with PostgreSQL 16 using `pgvector/pgvector:pg16`, named volume `medidoc_postgres_data`, and a `pg_isready` healthcheck.
  - Pinned `backend/requirements.txt` locking core dependencies across FastAPI, SQLAlchemy, psycopg 3 binary, pgvector, and LangChain packages.
  - Synthetic document generator `data/generate_synthetic.py` outputting 5 multi-page SOP PDFs and 8 clinical reports (discharge summaries + lab reports) paired with ground-truth JSON files.
  - Pytest verification suite in `backend/tests/test_generate_synthetic.py`.

- **Why this design:**
  - **ReportLab for PDF Generation:** Enables programmatic, reproducible generation of multi-page hospital documents featuring tabular data, clear heading hierarchies, and standard headers/footers that parse cleanly under both Docling and pypdf layout extractors.
  - **Companion Ground-Truth JSON:** Structuring each clinical report's ground-truth file to match the exact Pydantic schema required by Phase 3 (`patient`, `diagnosis`, `medications`, `admission_date`, `discharge_date`, `summary`) enables direct field-by-field scoring and automated validation benchmarking.
  - **Deliberate Error Injections:** Embedding realistic edge cases (discharge date prior to admission, omitted medication dosage unit, empty diagnosis list, and out-of-range patient age) provides immediate test fixtures for the Phase 3 validation engine.
  - **Healthcheck-Driven Container Lifecycle:** Using `pg_isready` with interval retries prevents race conditions during local startup and CI test runners when the backend service depends on pgvector.

- **Documented Known Limitations & Trade-Offs:**
  - **PII Masking Boundary:** Labelled-field and regex patterns effectively redact identifiers (MRN, phone numbers, email addresses, explicit patient name blocks). However, unlabelled proper names embedded within free-form clinical narrative prose can occasionally be missed by regex; Phase 3 will document this limitation and provide fallback redaction heuristics.

---

## Decision 002: Phase 1 Database Schema, Hierarchical Chunking, and Ingestion Pipeline

- **What was built:**
  - SQLAlchemy 2.x declarative models for documents, coarse parents, fine children, extractions, validation issues, audit log (metadata only), and evaluation tables.
  - Docling layout parser with automated pypdf fallback preserving section headings, markdown tables, and page numbers.
  - Hierarchical chunker creating parent sections (<= ~1500 tokens) and sentence-aligned child chunks (~300 tokens, 50-token overlap).
  - Dense embedding generator with LangChain HuggingFaceEmbeddings (`BAAI/bge-small-en-v1.5`, 384 dim) and PostgreSQL full-text `to_tsvector('english', text)` population.
  - FastAPI endpoints for `GET /health` (with live DB probe), `POST /ingest` (multi-part PDF upload), and `GET /documents` (with chunk counts and CORS for `http://localhost:5173`).

- **Why this chunking and storage design:**
  - **Hierarchical Parent-Child Architecture:** Fine child chunks (~300 tokens) maximize dense semantic retrieval precision and keyword match accuracy, while linking to coarse parent sections (<= 1500 tokens) ensures LLM synthesis in Phase 2 receives coherent clinical section context without fragmentation.
  - **Dual-Indexing in PostgreSQL:** Pairing pgvector HNSW cosine indexing with a GIN index over `to_tsvector('english', text)` provides native hybrid search without external vector DB dependencies, directly enabling reciprocal rank fusion.
  - **Strict Page Provenance Tracking:** Maintaining explicit `page_start` and `page_end` integers across all chunk levels guarantees verifiable citation generation (`[document, pages]`) required for clinical compliance.

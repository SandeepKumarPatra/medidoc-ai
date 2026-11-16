# MediDoc AI

MediDoc AI is an evidence-based clinical document and hospital policy assistant designed for healthcare-IT environments (EMR/HMIS). It provides deterministic, verifiable policy question answering across hospital Standard Operating Procedures (SOPs) using hierarchical Retrieval-Augmented Generation (RAG) across four retrieval modes, automated structured JSON extraction from clinical discharge summaries and lab reports, deterministic business rule validation, pre-LLM PII redaction, and metadata-only operational audit logging with aggregated analytics dashboards.

> **Important Notice:** All documents, clinical reports, patient identifiers, and hospital policies used in this repository are strictly **synthetic** (generated programmatically using ReportLab). No real protected health information (PHI) or real patient records are ever used, stored, or processed.

---

## Project Status

| Phase | Milestone | Status | Description |
|---|---|---|---|
| **Phase 0** | Foundation & Synthetic Generator | **Done** | Docker Compose with PostgreSQL + pgvector, requirements, multi-page synthetic SOP and clinical PDF generator. |
| **Phase 1** | Ingestion & Storage | **Done** | SQLAlchemy schema, Docling parser with pypdf fallback, hierarchical chunking, dense vector + full-text indexing. |
| **Phase 1b** | SOP Corpus Expansion | **Done** | Expanded corpus to 12 multi-page hospital SOPs and 48 curated benchmark evaluation questions. |
| **Phase 2** | Retrieval & Grounded Q&A | **Done** | Unified `retrieve()` across 4 modes (naive, parent-child, hybrid, hybrid-rerank), grounded `/ask` endpoint. |
| **Phase 2b/c/d** | Optimization & Citations | **Done** | Distinct parent deduplication, reranker speedup, deterministic citations (`[S#]`), full page ranges, `LLM_THINKING_BUDGET`. |
| **Phase 3** | Clinical Extraction & Privacy | **Done** | Structured extraction (`extract-v1.1`), 4 business validation rules, pre-LLM PII redaction, metadata-only audit logging. |
| **Phase 4** | Observability & Admin Stats | **Done** | REST endpoints (`/stats/overview`, `/stats/audit`, `/extractions`), Docling converter singleton cache, CLI demo seeder. |
| **Phase 4c** | Test Isolation & Honesty | **Done** | Ephemeral test database (`medidoc_test`), 100-token child chunks (2.01x ratio), extraction honesty clauses. |
| **Phase 5** | Frontend Workspace Screens | **Planned** | React + Vite workspace screens for Document Extraction, Policy Q&A, and Knowledge Base management. |
| **Phase 6** | Frontend Dashboards | **Planned** | Overview, Evaluation, and Audit & Privacy dashboards rendered with Recharts. |
| **Phase 7** | Evaluation Harness | **Planned** | Automated evaluation runner across all four retrieval modes comparing hit@5, MRR, and extraction accuracy. |
| **Phase 8** | Full Packaging & Demo | **In progress** | Complete Docker Compose orchestration, comprehensive documentation, and demo walkthrough. |

---

## What It Does

- **Document Ingestion (`POST /ingest`):** Uploads multi-page PDFs, parses document headings and markdown tables via Docling (falling back to pypdf), builds coarse parent sections ($\le$ 1500 tokens), splits into sentence-aligned child chunks (~100 tokens, 20-token overlap), generates 384-dimensional embeddings (`BAAI/bge-small-en-v1.5`), and populates PostgreSQL full-text search vectors (`tsvector`).
- **Four Retrieval Modes:**
  1. *Naive:* Dense vector cosine similarity search over child chunks, returning child passages directly.
  2. *Parent-Child:* Dense vector search over child chunks expanded to coarse parent sections, deduplicated to the best-scoring child per parent.
  3. *Hybrid:* Reciprocal Rank Fusion (RRF $k=60$) combining top-50 dense pgvector candidates with top-50 PostgreSQL full-text tsvector candidates, expanded to deduplicated parent sections.
  4. *Hybrid Rerank:* Top hybrid candidates re-scored using a cross-attention transformer (`BAAI/bge-reranker-base`), deduplicated, and expanded to distinct parent sections.
- **Grounded Q&A with Deterministic Citations (`POST /ask`):** Synthesizes grounded answers using prompt template `rag-clinical-v1.1`. The LLM cites sources exclusively using numeric labels (`[S1]`, `[S1, S4]`). Post-processing deterministically replaces labels with verified metadata citations (`[document, pages]`), drops and flags non-existent references (e.g. `[S9]`), and returns both a `citations` list for actually cited sources and a `sources` list for all retrieved passages with full page ranges.
- **Structured Extraction & Rule Validation (`POST /extract`, `POST /validate`):** Redacts PII and extracts structured clinical schemas (`patient`, `diagnosis`, `medications`, `admission_date`, `discharge_date`, `summary`) from discharge summaries and lab reports with single-turn error recovery. Validates 4 business rules:
  1. `discharge_date_before_admission`: Discharge date must not precede admission date.
  2. `medication_missing_unit`: Every medication must specify dose and unit.
  3. `diagnosis_empty`: Diagnosis list must not be empty.
  4. `age_between_0_and_120`: Patient age must be between 0 and 120.
- **Pre-LLM PII Redaction:** Sanitizes demographic headers and clinical identifiers, replacing names (`[NAME]`), phone numbers (`[PHONE]`), emails (`[EMAIL]`), and MRN/IDs (`[MRN]`) before text reaches external LLMs.
- **Metadata-Only Audit Logging:** Records every invocation of `/ask`, `/ingest`, `/extract`, and `/validate` in `audit_log` with timestamp, endpoint, document ID, PII masked count, latency, and status. Raw document text and clinical values are never stored.
- **Analytics & Observability (`/stats/*`):** Aggregates document counts by type, parent/child counts, extraction issue rate, rule violation frequency, query totals, and 14-day daily volume breakdowns.

---

## Architecture & Tech Stack

```text
  [PDF Documents] (SOPs, Discharge Summaries, Lab Reports)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                      Ingestion Pipeline                     │
  │  Docling / pypdf ──► Parent Sections (<=1500 tokens)        │
  │                   ──► Child Chunks (100 tok, 20 overlap)    │
  │                   ──► BAAI/bge-small-en-v1.5 Embeddings     │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 PostgreSQL 16 Storage Layer                 │
  │  pgvector HNSW Cosine Index  │  GIN tsvector Index          │
  │  Documents, Parents, Children, Extractions, Audit Log       │
  └──────────────────────┬──────────────────────────────┬───────┘
                         │                              │
         ┌───────────────┘                              └───────────────┐
         ▼                                                              ▼
┌─────────────────────────────────┐            ┌──────────────────────────────────┐
│      Policy Q&A Pipeline        │            │  Extraction & Privacy Pipeline   │
│  Dense + Sparse Search          │            │  Pre-LLM PII Masker (Regex/Tags) │
│  RRF Fusion (k=60)              │            │  LLM Structured Output           │
│  Cross-Encoder Rerank           │            │  Business Rule Validator         │
│  Parent Section Expansion       │            │  Metadata-Only Audit Logging     │
│  Deterministic Citations ([S#]) │            │  FastAPI Endpoints               │
└────────────────┬────────────────┘            └────────────────┬─────────────────┘
                 │                                              │
                 └───────────────────────┬──────────────────────┘
                                         ▼
                         FastAPI REST API (/docs)
```

- **Backend:** Python 3.12, FastAPI, Pydantic v2
- **Database & Search:** PostgreSQL 16 with `pgvector/pgvector:pg16`, PostgreSQL Full-Text Search (GIN `to_tsvector`)
- **RAG & Embeddings:** LangChain, `langchain-huggingface`, `BAAI/bge-small-en-v1.5` (384-dim), `BAAI/bge-reranker-base` CrossEncoder
- **LLM Integration:** Google Gemini (`gemini-2.5-flash` / `gemini-3.1-flash-lite` via `langchain-google-genai`), OpenAI adapter stub
- **Document Processing:** Docling (with singleton lifespan caching), `pypdf`, ReportLab
- **Testing & Isolation:** Pytest with ephemeral test database (`medidoc_test`)
- **Operations:** Docker, Docker Compose

---

## Quickstart

### 1. Prerequisites
- Python 3.12+
- Docker and Docker Compose
- Google Gemini API key (set in `.env`)

### 2. Environment Setup
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your-actual-gemini-api-key
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_THINKING_BUDGET=0
```

Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

### 3. Start PostgreSQL with pgvector
Start the PostgreSQL container:
```bash
docker compose up -d postgres
```

### 4. Reset & Initialize Development Database
Initialize the `medidoc` database, enable `pgvector`, and create all tables:
```bash
python scripts/reset_dev_db.py
```

### 5. Generate Synthetic Hospital Documents
Generate 12 hospital SOPs (7 pages each) and 8 clinical reports (discharge summaries and lab reports with companion ground-truth JSON files):
```bash
python data/generate_synthetic.py
```
Output files are written to `data/generated/`.

### 6. Start the API Server
Start FastAPI with Uvicorn:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 7. Seed Demo Data
In a separate terminal, run the idempotent seeder to ingest all SOPs, extract clinical reports, and run sample policy queries:
```bash
python scripts/seed_demo_data.py --api-url http://localhost:8000
```
This populates the database and displays the validation comparison table matching all 4 injected error rules.

### 8. Explore Documentation & Endpoints
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Overview Stats:** [http://localhost:8000/stats/overview](http://localhost:8000/stats/overview)
- **Recent Audit Logs:** [http://localhost:8000/stats/audit?limit=20](http://localhost:8000/stats/audit?limit=20)
- **Stored Extractions:** [http://localhost:8000/extractions?limit=10](http://localhost:8000/extractions?limit=10)

### 9. Run the Test Suite
Run the full pytest suite (uses the isolated `medidoc_test` database; never writes to development data):
```bash
pytest backend/tests
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service operational health check, environment tier, and PostgreSQL/pgvector connectivity probe. |
| `POST` | `/ingest` | Upload, parse (Docling/pypdf), chunk, embed, and index a PDF policy or clinical document. |
| `GET` | `/documents` | List indexed documents with page counts, parent section counts, child chunk counts, and status. |
| `POST` | `/ask` | Answer policy questions using multi-mode RAG with deterministic citations and latency breakdown. |
| `POST` | `/extract` | Redact PII from an uploaded report, extract structured JSON via LLM, validate rules, and log audit metadata. |
| `POST` | `/validate` | Validate an arbitrary structured clinical JSON payload against business rules without calling an LLM. |
| `GET` | `/stats/overview` | Aggregated metrics: documents by type, parent/child totals, issue rate, rule breakdown, and query totals. |
| `GET` | `/stats/audit` | Query historical metadata-only audit logs with endpoint filtering and 14-day daily volume trends. |
| `GET` | `/extractions` | List recent structured extractions with source document metadata, prompt versions, and issue counts. |
| `GET` | `/extractions/{id}` | Retrieve detailed structured extraction JSON and associated validation issues by extraction UUID. |

---

## Privacy & Responsible AI

- **PII Masking:** Pre-inference regex and labelled-field patterns replace patient names (`[NAME]`), phone numbers (`[PHONE]`), emails (`[EMAIL]`), and medical record numbers (`[MRN]`) before text is transmitted to an LLM. Ages, dates, medication doses, and units are preserved to maintain clinical validity.
- **Metadata-Only Audit Logging:** The `audit_log` table strictly records operational telemetry (`id`, `timestamp`, `endpoint`, `document_id`, `pii_items_masked`, `latency_ms`, `status`). Raw document text, user questions, prompt contents, and extracted medical values are **never logged**.
- **Known Privacy Limitations:** Regex and pattern-based masking reliably captures demographic headers and standard ID patterns. However, unlabelled proper names embedded in free-form narrative text cannot be completely guaranteed without risking false-positive redaction of specialized medical nomenclature.

---

## Retrieval Design

- **Hierarchical Chunking:** Coarse parent sections ($\le$ 1500 tokens) aligned to document headings preserve full clinical context for generation. Child chunks (~100 tokens, 20-token overlap, sentence-aligned) provide high-precision semantic matching (~2.01 children per parent section).
- **Hybrid Search & RRF:** Combines dense cosine similarity (top 50) and PostgreSQL full-text search rank (top 50) via Reciprocal Rank Fusion ($k=60$):
  $$\text{RRF Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + r_m(d)}$$
  Overcomes vocabulary mismatch between clinical terminology and standard English without external vector databases.
- **Cross-Encoder Reranking:** Re-scores top hybrid candidates with `BAAI/bge-reranker-base`. Inference runs under `torch.no_grad()` on top `RERANK_CANDIDATES` (default 10) to keep CPU latency under 2 seconds.
- **Deterministic Citations (`rag-clinical-v1.1`):** The LLM cites sources exclusively using numeric labels (`[S1]`, `[S1, S4]`). Post-generation processing replaces these with verified metadata citations formatted `[document, pages]` (e.g. `[sop_infection_control.pdf, pp. 2-3]`). Non-existent source numbers (e.g. `[S9]`) are pruned from the answer and flagged. The response exposes both `citations` (sources actually cited) and `sources` (all retrieved candidates with full page ranges).
- **Latency Controls:** Configurable `LLM_THINKING_BUDGET=0` disables extraneous reasoning token generation in Gemini models, accelerating generation latency from ~6.4s to ~1.7s (3.75x speedup).

---

## Known Limitations

- **Compound Questions:** Complex inquiries containing multiple unrelated sub-questions across disparate hospital departments may retrieve fragmented passages; single-intent policy queries are recommended.
- **CPU Reranking & Parsing Latency:** Heavy CrossEncoder transformer reranking and deep Docling layout extraction require model warm-up and take several seconds per document on CPU.
- **Synthetic Data Only:** The system is developed and evaluated strictly on synthetic hospital SOPs and clinical reports; it has not been validated against uncurated third-party electronic medical record dumps.
- **Not for Clinical Decision-Making:** MediDoc AI is an architectural prototype and portfolio demonstration. It is not certified as a medical device and must never be used for real patient diagnosis, triage, or clinical care.

---

## Evaluation & Demonstrations

### TODO: Evaluation Results Table
<!-- TODO: Populate ablation benchmark metrics (hit@5, MRR, latency) across naive, parent_child, hybrid, and hybrid_rerank once Phase 7 evaluation harness runs. -->
*Benchmark ablation results comparing all 4 retrieval modes across the 48-question SOP dataset will be published here upon completion of Phase 7.*

### TODO: Screenshots
<!-- TODO: Add UI screenshots of Overview Dashboard, Document Extraction workspace, and Policy Q&A screen once Phase 5 and 6 frontend implementation is complete. -->
*Screenshots of the React + Vite dashboards and clinical workspaces will be displayed here.*

### TODO: Demo Video Link
<!-- TODO: Add link to recorded video demonstration of MediDoc AI. -->
*A recorded walkthrough video demonstrating document ingestion, hybrid reranking, and clinical extraction will be linked here.*

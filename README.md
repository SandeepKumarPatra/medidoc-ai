# MediDoc AI

Clinical document assistant for healthcare-IT contexts (EMR/HMIS). MediDoc AI reads synthetic hospital documents, extracts validated structured JSON from discharge summaries and lab reports, and answers questions about hospital standard operating procedures (SOPs) using multi-mode RAG with citations.

> **Hard Privacy Rules:**
> - Synthetic data ONLY. Never real patient data.
> - Never log or store raw document text or PII.
> - The audit log records operational metadata only (counts of masked items, latency, status).

---

## Architecture & Tech Stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2
- **Database & Search:** PostgreSQL 16 with `pgvector` extension, PostgreSQL Full-Text Search (tsvector + GIN)
- **RAG & Extraction:** LangChain, SentenceTransformers / BAAI embeddings & reranker, Gemini / OpenAI LLM
- **Ingestion & Parsing:** Docling (with `pypdf` fallback), ReportLab for synthetic generation
- **Frontend:** React, Vite, Tailwind CSS, Recharts
- **Operations:** Docker, Docker Compose

---

## Repository Structure

```
medidoc-ai/
  backend/
    app/
      main.py            # FastAPI app & routing
      config.py          # Settings from environment
      db/                # SQLAlchemy models & session
      ingestion/         # Document parsing & chunking
      retrieval/         # Naive, parent-child, hybrid, rerank
      llm/               # LLM adapter (Gemini / OpenAI)
      extraction/        # Schema extraction & validation
      privacy/           # PII masking & audit logging
      eval/              # Evaluation questions & runner
    tests/               # Pytest test suite
    requirements.txt     # Pinned Python dependencies
  frontend/              # React + Vite application
  data/
    generate_synthetic.py # Synthetic medical PDF generator
    generated/           # Generated synthetic PDFs and JSONs (.gitignored)
    eval/questions.json  # RAG evaluation benchmark
  docs/                  # Documentation
  docker-compose.yml     # PostgreSQL + pgvector service & placeholders
  .env.example           # Environment template
  SPEC.md                # System specification & roadmap
  DECISIONS.md           # Architecture decision records
  README.md              # Project guide
```

---

## Quickstart (Phase 0)

### 1. Prerequisites
- Python 3.12+
- Docker and Docker Compose

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your Gemini API key:
```bash
cp .env.example .env
```

### 3. Start Database Container
Start the PostgreSQL 16 container with the `pgvector` extension:
```bash
docker-compose up -d postgres
```
Verify container health:
```bash
docker-compose ps
```

### 4. Generate Synthetic Medical Documents
Generate 5 multi-page SOP policy PDFs and 8 clinical reports (discharge summaries and lab reports) with companion ground-truth JSON files:
```bash
python data/generate_synthetic.py
```
Outputs are written to `data/generated/`.

### 5. Run Verification Tests
Execute the test suite to verify generator output, multi-page structure, and schema compliance:
```bash
python -m pytest backend/tests/test_generate_synthetic.py -v
```

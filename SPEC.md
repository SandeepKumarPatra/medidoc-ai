# MediDoc AI - Specification

Clinical document assistant for a healthcare-IT context (EMR/HMIS).
Reads SYNTHETIC hospital documents, extracts validated structured JSON from
discharge summaries and lab reports, and answers questions about hospital
policies (SOPs) using RAG with citations. Includes a React web app with
dashboards.

**Hard rules:** synthetic data only. Never real patient data. Never log raw
document text or PII.

---

## 1. Tech stack (fixed, do not substitute without asking)

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| API | FastAPI, Pydantic v2 |
| ORM / DB | SQLAlchemy 2.x, PostgreSQL 16 with pgvector extension |
| RAG framework | LangChain (versions PINNED in requirements.txt) |
| Embeddings | Configurable. Dev default: BAAI/bge-small-en-v1.5 (384 dim). Better: BAAI/bge-m3 (1024 dim). Vector dimension must come from config |
| Keyword search | PostgreSQL full-text search (tsvector + GIN index) |
| Reranker | Configurable cross-encoder. Dev default: BAAI/bge-reranker-base. Better: BAAI/bge-reranker-v2-m3 |
| LLM | Gemini through LangChain; an OpenAI implementation switchable by config |
| PDF parsing | Docling; pypdf as fallback if Docling fails or is not installed |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Ops | Docker, docker compose (postgres with pgvector, backend, frontend) |

Follow the INSTALLED version's documentation for LangChain, not memory.
Do not upgrade packages without asking.

## 2. Repository layout

```
medidoc-ai/
  backend/
    app/
      main.py            FastAPI app, routers
      config.py          settings from env, retrieval mode toggles
      db/                SQLAlchemy models, session, init/migrations
      ingestion/         parse, chunk, embed, store
      retrieval/         naive, parent_child, hybrid, rerank
      llm/               LangChain LLM adapter (Gemini, OpenAI)
      extraction/        Pydantic schema, extractor, validator
      privacy/           PII masking, audit log
      eval/              question set, runner, metrics
    tests/
    requirements.txt
    Dockerfile
  frontend/              React + Vite + Tailwind + Recharts
  data/
    generate_synthetic.py
    generated/           (git-ignored)
    eval/questions.json  labelled evaluation questions
  docker-compose.yml
  .env.example   SPEC.md   DECISIONS.md   README.md   .agent/rules/
```

## 3. Database tables

| Table | Key columns |
|---|---|
| documents | id, filename, doc_type (sop / discharge / lab), status, page_count, created_at |
| parents | id, document_id, section_title, text, page_start, page_end, section_type |
| children | id, parent_id, document_id, text, embedding (vector), tsv (tsvector, GIN index), page_start, page_end |
| extractions | id, document_id, json_result (JSONB), model, prompt_version, created_at |
| validation_issues | id, extraction_id, field, rule, severity, message |
| audit_log | id, timestamp, endpoint, document_id, pii_items_masked, latency_ms, status. NEVER raw text |
| eval_runs | id, mode, created_at, notes |
| eval_results | id, run_id, question_id, expected_doc, retrieved_ids, hit, reciprocal_rank, latency_ms |

Use pgvector with an HNSW or IVFFlat index on children.embedding.

## 4. Ingestion (Phase 1)

1. Receive PDF. Parse with Docling (sections, headings, tables, page numbers); fall back to pypdf.
2. Build parent sections (max about 1500 tokens; split larger ones).
3. Split parents into child chunks of about 300 tokens, sentence-aligned, small overlap, using LangChain text splitters.
4. Embed children with the configured embedding model.
5. Insert parents and children. Fill tsv with to_tsvector('english', text).
6. Record the document and its status.

## 5. Retrieval modes (Phase 2)

All four modes live behind one function `retrieve(question, mode, top_k)`:

| Mode | Behaviour |
|---|---|
| naive | Dense similarity over children, return child text |
| parent_child | Dense similarity over children, return the parent sections (deduplicated) |
| hybrid | pgvector similarity (top 50) + Postgres full-text rank (top 50), merged by Reciprocal Rank Fusion (k=60), then parent expansion |
| hybrid_rerank | hybrid candidates, cross-encoder rerank, then parent expansion |

Answer generation:
- Use ONLY the retrieved context.
- Cite sources as [document, pages].
- If the context does not contain the answer, reply that it was not found.
- Return answer, sources, retrieved ids, latency per stage.

## 6. Extraction, validation, privacy (Phase 3)

Extraction schema (Pydantic):

```json
{
  "patient": {"name": "string", "age": 0, "sex": "M|F|O"},
  "diagnosis": ["string"],
  "medications": [{"name": "string", "dose": 0, "unit": "string", "frequency": "string"}],
  "admission_date": "YYYY-MM-DD",
  "discharge_date": "YYYY-MM-DD",
  "summary": "short clinician-style summary"
}
```

Use LangChain structured output. If validation fails, retry ONCE with the
error message in the prompt. Store the prompt_version.

Validation rules (return a list of issues with field, rule, severity, message):
- discharge_date must not be before admission_date
- every medication has a dose and a unit
- diagnosis list is not empty
- age between 0 and 120

PII masking (before EVERY LLM call): regex and labelled-field rules for names,
phone numbers, emails, ID numbers (e.g. MRN, Aadhaar-like, PAN-like patterns).
Replace with tokens like [NAME], [PHONE]. Known limit: unlabelled names can be
missed; document this in DECISIONS.md.

Audit log: record endpoint, document id, count of masked items, latency, status.
No document text, ever.

## 7. API

| Endpoint | Purpose |
|---|---|
| GET /health | service and database status |
| POST /ingest | upload and index a PDF (doc_type parameter) |
| GET /documents | list documents with chunk counts and status |
| POST /ask | {question, mode, top_k} returns answer, sources, retrieved ids, timings |
| POST /extract | upload a report, returns validated JSON and warnings |
| POST /validate | extracted JSON in, rule issues out |
| GET /stats/overview | totals, issue rate, average latency |
| GET /stats/audit | recent audit rows |
| POST /eval/run | run the evaluation set across all four modes |
| GET /eval/results | ablation data |

All request and response bodies are Pydantic models. Enable CORS for the frontend.

## 8. Frontend screens (Phases 5 and 6)

| # | Screen | Type | Content |
|---|---|---|---|
| 1 | Overview | Dashboard | documents indexed, extractions run, validation-issue rate, queries answered, average latency |
| 2 | Evaluation | Dashboard | ablation table and charts: naive vs parent_child vs hybrid vs hybrid_rerank (hit@5, MRR, latency) |
| 3 | Audit and Privacy | Dashboard | request log, PII items masked, status; never shows raw text |
| 4 | Document Extraction | Workspace | upload report, show JSON result, list validation issues |
| 5 | Policy Q&A | Workspace | chat with citations and a source viewer; mode selector |
| 6 | Knowledge Base | Workspace | document list, chunk counts, upload and ingest status |

Clean, simple, consistent layout with a sidebar. Loading and error states on every call.

## 9. Synthetic data (Phase 0)

`data/generate_synthetic.py` produces PDFs in `data/generated/`:
- 5 SOP / policy documents: infection control, discharge process, billing,
  medication safety, patient consent (multi-page, with headings and one table each)
- at least 5 discharge summaries / lab reports. Each has a ground-truth JSON
  file beside it (the exact values used) so extraction accuracy can be measured.
- Some reports must contain deliberate errors (missing dose unit, discharge date
  before admission) so the validator has something to catch.
- All names, phone numbers and IDs are fake.

## 10. Evaluation (Phase 7)

- `data/eval/questions.json`: 20 to 30 questions about the SOPs. Each has the
  expected document and page.
- Metrics: hit@5, MRR, latency per mode. Results saved to eval tables and shown
  on dashboard 2 and in the README.
- Extraction accuracy: compare extracted JSON with ground-truth JSON, per field.

## 11. Phases

| Phase | Build | Done when |
|---|---|---|
| 0 | repo, structure, docker-compose with Postgres + pgvector, synthetic data generator | 10+ synthetic PDFs exist, database container starts |
| 1 | DB schema and ingestion | /ingest indexes a PDF |
| 2 | retrieval modes and /ask | /ask returns a cited answer in all four modes |
| 3 | /extract, /validate, PII masking, audit log | valid JSON, correct issues, test proves no raw PII reaches the LLM call |
| 4 | stats and eval endpoints | endpoints return real data |
| 5 | React shell and screens 4, 5, 6 | upload, extract, ask all work in the browser |
| 6 | dashboards 1, 2, 3 | charts render from live data |
| 7 | evaluation harness | ablation table filled from a real run |
| 8 | full Docker, README, demo | docker compose up works from a clean clone |

Cut order if time runs short: Audit page, then Knowledge Base page, then any
cloud deploy. Never cut /ask, /extract, the evaluation table, the README.

## 12. Non-goals

No real patient data, no authentication system, no medical advice, no production
hardening. This is a portfolio prototype.

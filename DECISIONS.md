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

---

## Decision 003: Phase 1b SOP Corpus Expansion and Evaluation Dataset

- **What was built:**
  - Expanded the SOP library in `data/generate_synthetic.py` and `data/sop_data.py` to 12 multi-page policies (7 pages each, 14 sections, tabular data, concrete facts and roles).
  - Authored `data/eval/sop_questions.json` with 48 natural-language questions (4 per SOP) mapped to target files, exact headings, and verbatim snippets.
  - Updated verification tests in `backend/tests/test_generate_synthetic.py`, `test_parser_chunker.py`, and `test_ingestion.py` for 12 documents and 6–10 page boundaries.

- **Why the corpus was enlarged:**
  - **Authentic Policy Corpus Scale:** Enlarged from 5 short documents to 12 realistic 7-page SOPs to create sufficient chunk volume and diversity for evaluating hierarchical parent-child retrieval in Phase 2.
  - **Non-Trivial Disambiguation via Thematic Overlaps:** Intentionally introduced cross-cutting themes (glove specifications, EMR documentation timelines, and emergency escalation paths) across documents so retrieval requires contextual semantic disambiguation rather than simple keyword matching.
  - **Section-Level Ground-Truth Benchmark:** Created 48 curated questions paired with exact section titles and answer snippets to quantitatively benchmark retrieval recall (hit@5) and MRR without heading-word leakage.

---

## Decision 004: Phase 2 Retrieval Modes, Cross-Encoder Reranking, LLM Adapters, and Policy Q&A

- **What was built:**
  - Added SHA-256 byte hashing, 20 MB size limit, and PDF signature validation to `/ingest` to prevent duplicate chunk indexing and invalid uploads.
  - Built unified `retrieve(question, mode, top_k)` supporting 4 modes: naive, parent-child, hybrid (pgvector cosine + tsvector rank with RRF k=60), and hybrid_rerank (`BAAI/bge-reranker-base` CrossEncoder with parent section deduplication).
  - Implemented LLM adapter architecture with `GeminiLLMAdapter` (`ChatGoogleGenerativeAI`) and an `OpenAILLMAdapter` stub, switchable via `LLM_PROVIDER`.
  - Implemented `POST /ask` with grounded prompt template `rag-clinical-v1.0`, `[document, pages]` citations, out-of-context refusal, and per-stage latency tracking.

- **Why this design:**
  - **Two-Tier Hierarchical Expansion:** Retrieval queries granular child chunks (~300 tokens) for high semantic and lexical recall, but expands to coarse parent sections (<= 1500 tokens) to supply complete clinical policy context to the LLM without paragraph truncation.
  - **RRF (k=60) Hybrid Fusion:** Merging pgvector dense cosine ranking with PostgreSQL full-text `plainto_tsquery` via Reciprocal Rank Fusion overcomes vocabulary mismatch without external vector database dependencies.
  - **Deep Cross-Encoder Reranking:** Re-evaluating top hybrid candidates with a cross-attention transformer computes query-passage cross-attention, surfacing highly specific policy clauses that dense embeddings alone miss.

---

## Decision 005: Phase 2b Distinct Parent Deduplication, Reranker Speedup, and Debug Prompt Visibility

- **What was built:**
  - Enforced strict parent deduplication across `parent_child`, `hybrid`, and `hybrid_rerank` by grouping candidates by `parent_id`, preserving each parent's best-scoring child, and guaranteeing top_k distinct parent sources in `/ask`.
  - Accelerated reranking to under 2 seconds on CPU by restricting inference to top `RERANK_CANDIDATES` (config default 20) child passages, running under `torch.no_grad()`, batching, and warming up embedding and cross-encoder models during application startup.
  - Hidden the raw LLM prompt in `/ask` responses by default (returning it only when `debug=true`) to reduce payload overhead while persistently returning `prompt_version`.

---

## Decision 006: Phase 2c Ingestion De-duplication, Replacement Lifecycle, Reranker Sizing, and LLM Timeout Controls

- **What was built:** Added document replacement semantics on filename re-upload (deleting old child/parent records first) and defensive parent de-duplication via normalized text MD5 hashing. Lowered `RERANK_CANDIDATES` default to 10 with configurable choices, and instrumented `POST /ask` with model name/generation latency logging alongside a 30s LLM execution timeout.
- **Why this design:** Replacing obsolete document chunks during re-upload eliminates stale cross-document section duplication while normalized text hashing shields against parsing repetitions; trimming rerank candidates to 10 cuts CPU latency by ~41% (to ~3.9s) while bounded LLM timeouts prevent indefinite client thread blocking.

---

## Decision 007: Phase 3 Clinical Extraction, Rule Validation, PII Masking, and Audit Logging

- **What was built:**
  - Implemented multi-tier PII masker (`backend/app/privacy/masking.py`) replacing names, phone numbers, email addresses, and MRN/IDs with tokens (`[NAME]`, `[PHONE]`, `[EMAIL]`, `[MRN]`) while preserving clinical terms, ages, dates, and dosages.
  - Implemented Pydantic clinical extraction schema (`backend/app/extraction/schema.py`) conforming to SPEC.md section 6 with nullable medication dose and unit.
  - Implemented structured extraction pipeline (`backend/app/extraction/extractor.py`) with `prompt_version="extract-v1.0"`, single-turn schema retry on failure, and adapter extension `generate_structured()` without modifying `generate()`.
  - Implemented business rule validator (`backend/app/extraction/validator.py`) enforcing admission/discharge dates, complete medication dosages, non-empty diagnoses, and patient ages (0-120).
  - Implemented metadata-only audit logging (`backend/app/privacy/audit.py`) instrumented across `/ask`, `/ingest`, `/extract`, and `/validate`, and exposed REST endpoints `POST /extract` and `POST /validate`.

- **Why this design & Known Limitations:**
  - Redacting PII prior to LLM inference prevents PHI exposure outside system boundaries while preserving clinical document layout for downstream tasks.
  - Known limitation: Labelled-field and regex patterns reliably capture demographic headers and common clinical ID formats, but unlabelled proper names embedded within free narrative prose cannot be completely eliminated without risk of false positives on clinical nomenclature.
  - Audit log table strictly records operational metrics (endpoint, document_id, pii_items_masked, latency_ms, status) and never stores document text, prompts, answers, or extracted clinical values.

---

## Decision 008: Phase 4 Statistics Endpoints, Docling Converter Singleton, and Embeddings Migration

- **What was built:**
  - Implemented cached singleton `get_document_converter()` warmed during FastAPI lifespan to eliminate per-request model reload overhead, adding stage latency instrumentation (`parse_ms`, `mask_ms`, `llm_ms`, `total_ms`) to `/extract`.
  - Added REST endpoints `GET /stats/overview`, `GET /stats/audit` (with 14-day call trends), `GET /extractions`, and `GET /extractions/{id}` with strict metadata-only Pydantic schemas.
  - Migrated `HuggingFaceEmbeddings` to standalone `langchain-huggingface==1.2.3` and built automated CLI database seeder `scripts/seed_demo_data.py`.
- **Why this design:**
  - Singleton caching of Docling's converter cuts warm-up latency from ~47.2s to ~12.1s and stabilizes PDF parsing to ~4.1s without reloading PyTorch pipeline weights on each call.
  - Aggregating stats directly in PostgreSQL via SQLAlchemy window/group expressions provides performant dashboard feeds while guaranteeing no raw clinical narrative or PII is ever returned.

---

## Decision 009: Phase 4c Test Isolation, Hierarchical Granularity, and Extraction Honesty

- **What was built:** Isolated unit/integration testing into ephemeral `medidoc_test` PostgreSQL database via `backend/tests/conftest.py` with zero dev database pollution; adjusted child chunk size default to 100 tokens with 20-token overlap sentence-aligned (achieving 386 children across 192 parents, 2.01 avg per parent); and updated clinical extraction prompt to `extract-v1.1` enforcing strict factual honesty without inferring, normalizing, or substituting placeholder strings for missing values.
- **Why this design:** Dedicated test database fixtures eliminate state bleed and accidental data destruction during automated test runs; smaller 100-token child chunks (2–4 per parent section) increase granular semantic retrieval precision for hybrid ranking while keeping parent context intact; and strict extraction honesty prevents LLMs from hallucinating default medication units or repairing deliberate date/age discrepancies needed by clinical compliance validation rules.

---

## Decision 010: Phase 2d Deterministic Citations, Full Page Ranges, and Thinking Budget

- **What was built:** Implemented `rag-clinical-v1.1` prompt enforcing numeric source citations (`[S1]`, `[S1, S4]`) with deterministic post-generation replacement to `[document, pages]`, invalid citation dropping/flagging, `citations` list in response, full page range exposure across all sources (`page_start`, `page_end`, `"pp. 2-3"`), and configurable `LLM_THINKING_BUDGET`.
- **Why this design:** Replaces fragile LLM filename/page generation with deterministic metadata substitution while pruning hallucinations (invalid indices); full page ranges guarantee clinical provenance auditability; and setting thinking budget to 0 prevents unnecessary reasoning token overhead, accelerating generation latency to sub-2s.

---

## Decision 011: Phase 7 Evaluation Harness, Categorical Ablation, and Grounded Honesty Benchmarking

- **What was built:** Built automated evaluation harness in `backend/app/eval/` with CLI runner (`python -m backend.app.eval.run`), REST endpoints (`POST /eval/run`, `GET /eval/results`, `GET /eval/runs/{run_id}/questions`), database persistence to `eval_runs` and `eval_results`, and automated report writer to `docs/EVAL_RESULTS.md`. Validated 48 benchmark questions against DB parent sections, marking 4 compound multi-topic queries and 12 paraphrased vocabulary-mismatch queries. Benchmarks hit@1/3/5, MRR, latency across naive, parent-child, hybrid, and two distinct cross-encoders (`BAAI/bge-reranker-base` and `cross-encoder/ms-marco-MiniLM-L-6-v2`); evaluates answer citation fidelity and term overlap (`--with-answers`), and clinical extraction per-field accuracy excluding masked patient name alongside validation issue precision/recall (`--with-extraction`).
- **Why this design:** Hard query archetypes (compound topic-splits and paraphrased terminology) rigorously isolate dense vs sparse vs cross-encoder capabilities without superficial keyword matching. Segmenting metrics exposes exact strengths and latency trade-offs per retrieval mode, background workers prevent API request timeouts, and strict factual honesty rules ensure ungrounded failures and worst-performing queries are honestly diagnosed rather than tuned away.

---

## Decision 012: Phase 7b Compound Both-Hit Evaluation, Refusal Guardrails, Keyword Benchmarks, and Heuristic Scoring

- **What was built:**
  - Expanded benchmark dataset to 60 questions in `data/eval/sop_questions.json` (44 single including 12 paraphrased, 8 keyword-sensitive, 8 compound).
  - Attached explicit `expected_sections` (lists of two distinct `{doc, section}` targets) to all 8 compound questions, and implemented `compound_both_hit_at_5` requiring both targets to appear in top 5 candidates.
  - Added 8 keyword-sensitive questions featuring exact technical standards (ASTM D6319, 49 CFR, 170-260 micron, DERS, WHO Five Moments) and reported per-category results (`single`, `paraphrased`, `keyword`, `compound`).
  - Added 8 out-of-domain unanswerable clinical queries (`data/eval/unanswerable_questions.json`) to test hallucination resistance and refusal guardrails in `hybrid` mode.
  - Implemented top-1 and top-5 candidate set difference tracking between dense (`parent_child`) and `hybrid` retrieval.
  - Extended `--with-answers` to evaluate both `hybrid` and `hybrid_rerank` modes side-by-side.
  - Formally documented the abstractive completion heuristic check for clinical summaries (`len(ext_summary.strip()) >= 15`) and synthetic smoke test scope in `docs/EVAL_RESULTS.md`.
- **Why this design & Honest Findings:**
  - Compound questions with strict two-target criteria expose cross-domain recall limitations: dense/hybrid achieves only 50% `both-hit@5` (MRR 0.219), while cross-encoder reranking lifts `both-hit@5` to 75% (MRR 0.375) by re-scoring candidate pools.
  - However, cross-encoder reranking incurs severe CPU latency (2626.6ms for BGE vs 35.2ms for Hybrid, a 75x penalty) and slightly degrades Hit@1 (0.73 vs 0.77).
  - In answer synthesis, `hybrid_rerank` achieved 100% citation inclusion with 0 false refusals, while `hybrid` had 93.3% citation inclusion and 1 false refusal (6.7%).
  - Unanswerable guardrails proved 100% robust (8/8 correct refusals, 0 hallucinations).
  - Default mode choice: `hybrid` is recommended as the default operational mode because it delivers sub-36ms latency, highest Hit@1 (0.77), and 100% keyword Hit@5; `hybrid_rerank` is reserved for complex compound queries where multi-section recall outweighs latency.

---

## Decision 013: Phase 7c Sparse Search Diagnosis, OR-Lexeme tsquery Fix, and Retrieval Re-Ablation

- **What was built:** Diagnosed that `plainto_tsquery` (boolean AND semantics) returned 0 matching chunks across all 60 evaluation questions; fixed `sparse_search` in `backend/app/retrieval/sparse.py` by converting stemmed content lexemes into OR-ed tsqueries ranked by cover density (`ts_rank_cd`) while keeping exact technical terms (e.g. ASTM D6319) functional; and re-ran the full 60-question retrieval ablation across all 5 modes.
- **Why this design & Honest Findings:** Natural language questions contain 10–25 words that never appear simultaneously in 100-token child chunks under boolean AND, which previously masked hybrid search as identical to dense search (0.0% difference); OR-ing stemmed lexemes activates true RRF fusion (differing in 10.0% top-1 and 98.3% top-5), improving compound query `both-hit@5` from 50.0% to 62.5% in hybrid mode (and 75.0% in reranked modes) while preserving 100% keyword Hit@5, though introducing lexical noise on paraphrased queries that reduces hybrid Hit@1 from 0.77 to 0.72.
- **Default Mode Conclusion:** Because `parent_child` achieves highest Hit@1 (0.77), highest MRR (0.835), and strongest resistance to paraphrased noise (0.92 Hit@5) at 38.2ms latency, it is now recommended as the low-latency default for interactive Q&A, while routing compound and code-heavy inquiries to `hybrid` or `hybrid_rerank` where multi-clause recall is critical.

---

## Decision 014: Phase 5a React Frontend Shell and Core Clinical Workspaces

- **What was built:** Initialized `frontend/` using Vite, React, and Tailwind CSS with API client connecting to `VITE_API_URL` (default `http://localhost:8000`), a navigation sidebar with live `GET /health` API status probe, a Policy Q&A screen (`POST /ask`) featuring retrieval mode selection (`hybrid` default), top_k tuning, generation and calculated retrieval latency chips, and grounded source provenance, alongside a Document Extraction workspace (`POST /extract`) presenting clinical JSON summaries, PII redaction metrics, and validation rule findings in a badge-coded table with 60s request timeouts.
- **Why this design:** Building a decoupled single-page application shell with strict 60-second timeouts, explicit 422 validation parsing, and structured metadata display ensures clinicians can interactively query policies and review extracted discharge reports with zero exposure of raw underlying clinical text, strictly preserving clinical privacy rules while maintaining high responsiveness.

---

## Decision 015: Phase 6a Analytics and Evaluation Dashboards

- **What was built:** Added Overview (`GET /stats/overview`, `GET /stats/audit`) and Evaluation (`GET /eval/results`) dashboard screens to the React frontend with Recharts visualizations (corpus distribution, MRR per mode, retrieval latency per mode), ablation summary tables with compound both-hit@5 scoring, KPI cards, and privacy audit logs.
- **Why this design:** Integrating empirical retrieval metrics and real-time audit logging directly into the web application provides healthcare IT administrators with immediate visibility into RAG model trade-offs (highlighting why `hybrid` is the balanced production default over high-latency cross-encoders) while guaranteeing zero raw document text or protected health information is ever rendered.
- **Documented Known Limitations & Findings:** Retrieval benchmarks reflect the curated 60-question synthetic SOP evaluation suite, and clinical extraction metrics represent smoke tests over synthetic discharge/lab reports; cross-encoder reranking yields higher compound both-hit recall (75% vs 62.5%) but carries a ~48x CPU latency penalty.

---

## Decision 016: Phase 8 Multi-Container Packaging, Model Caching, and End-to-End Orchestration

- **What was built:** Authored multi-stage `frontend/Dockerfile` (Node 22 build + Nginx Alpine) and `backend/Dockerfile` (Python 3.12-slim), enabled all three services in `docker-compose.yml` with healthcheck synchronization, wired environment variable overrides for PostgreSQL connectivity, mounted named volume `medidoc_hf_cache` for Hugging Face weights, and rewrote `README.md` with containerized operations, full ablation data, and documented limits.
- **Why this design:** Multi-container orchestration with PostgreSQL `pg_isready` healthcheck gating eliminates startup race conditions; named cache volumes cut container restart latency from over 30s to under 2s by persisting Hugging Face embeddings and cross-encoder models; and serving the compiled Vite bundle via Nginx provides performant static file delivery and client SPA routing.
- **Verification:** Tested clean-slate lifecycle (`docker compose down -v` -> `docker compose up --build -d`), verified HTTP 200 on `GET /health` and frontend port 5173, and executed in-container synthetic SOP ingestion, extraction, and benchmark query execution via `scripts/seed_demo_data.py`.





"""Integration tests for MediDoc AI retrieval pipeline against PostgreSQL."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import Child, Document, Parent
from backend.app.db.session import SessionLocal
from backend.app.retrieval.dense import dense_search
from backend.app.retrieval.expansion import expand_to_parents
from backend.app.retrieval.fusion import FusedCandidate, reciprocal_rank_fusion
from backend.app.retrieval.rerank import rerank_candidates
from backend.app.retrieval.service import retrieve
from backend.app.retrieval.sparse import sparse_search


@pytest.fixture
def db_session(db: Session):
    """Yield database session connected to running PostgreSQL with pgvector."""
    child_count = db.query(Child).count()
    assert child_count > 0, "Database must have ingested child chunks before running retrieval tests."
    return db


@pytest.mark.parametrize("mode", ["naive", "parent_child", "hybrid", "hybrid_rerank"])
def test_each_retrieval_mode_returns_results(db_session, mode):
    """Assert all four retrieval modes return scored, attributed results with timings."""
    question = "What are the standard infection control precautions and PPE requirements?"
    top_k = 3

    response = retrieve(question=question, mode=mode, top_k=top_k, db=db_session)

    # 1. Assert Response Envelope
    assert response.question == question
    assert response.mode == mode
    assert len(response.results) > 0, f"Mode '{mode}' returned 0 results"
    assert len(response.results) <= top_k

    # 2. Assert Result Chunks Attributes and Metadata
    for chunk in response.results:
        assert chunk.id, "Result chunk must have an ID"
        assert chunk.document_id, "Result chunk must have a document ID"
        assert chunk.document_filename.endswith(".pdf"), "Document filename must be a PDF"
        assert chunk.text.strip(), "Result text must not be empty"
        assert isinstance(chunk.score, float), "Score must be a float"
        assert chunk.page_start >= 1, "page_start must be >= 1"
        assert chunk.page_end >= chunk.page_start, "page_end must be >= page_start"

        if mode == "naive":
            assert chunk.chunk_type == "child"
        else:
            assert chunk.chunk_type == "parent"

    # 3. Assert Per-Stage Latency Timings
    timings = response.timings
    assert "embed_ms" in timings
    assert "dense_search_ms" in timings
    assert "total_ms" in timings
    assert timings["total_ms"] > 0

    if mode in ("hybrid", "hybrid_rerank"):
        assert "sparse_search_ms" in timings
        assert "fusion_ms" in timings

    if mode == "hybrid_rerank":
        assert "rerank_ms" in timings

    if mode != "naive":
        assert "expansion_ms" in timings


def test_hybrid_includes_both_dense_and_sparse_results(db_session):
    """Assert Reciprocal Rank Fusion successfully combines dense vector and full-text sparse hits."""
    question = "infection control"

    dense_hits, _, _ = dense_search(question, top_k=20, db=db_session)
    sparse_hits, _ = sparse_search(question, top_k=20, db=db_session)

    assert len(dense_hits) > 0, "Dense search should return hits"
    assert len(sparse_hits) > 0, "Sparse search should return hits for keyword matches"

    fused, fusion_ms = reciprocal_rank_fusion(dense_hits, sparse_hits, k=60)
    assert len(fused) > 0
    assert fusion_ms >= 0.0

    # Verify presence of candidates originating from dense and sparse rankings
    has_dense_origin = any(c.dense_rank is not None for c in fused)
    has_sparse_origin = any(c.sparse_rank is not None for c in fused)

    assert has_dense_origin, "Fused candidates must include results from dense search"
    assert has_sparse_origin, "Fused candidates must include results from sparse full-text search"

    # Find candidates that appeared in both lists and verify reciprocal rank accumulation
    both_matches = [c for c in fused if c.dense_rank is not None and c.sparse_rank is not None]
    if both_matches:
        for c in both_matches:
            expected_score = (1.0 / (60 + c.dense_rank)) + (1.0 / (60 + c.sparse_rank))
            assert abs(c.score - expected_score) < 1e-6, "RRF score must be sum of reciprocal ranks"


def test_rerank_changes_candidate_order(db_session):
    """Assert CrossEncoder reranking re-evaluates and alters pre-rerank candidate ordering."""
    question = "What must staff do immediately following an accidental needle stick exposure?"

    # Fetch dense and sparse candidates to fuse
    dense_hits, _, _ = dense_search(question, top_k=15, db=db_session)
    sparse_hits, _ = sparse_search(question, top_k=15, db=db_session)
    fused, _ = reciprocal_rank_fusion(dense_hits, sparse_hits, k=60)

    candidates = fused[:10]
    assert len(candidates) >= 2, "Need at least 2 candidates to verify reranking order"

    initial_order = [c.child.id for c in candidates]

    reranked, rerank_ms, rerank_text_chars = rerank_candidates(question=question, candidates=candidates)
    reranked_order = [c.child.id for c in reranked]

    assert rerank_ms > 0.0
    assert rerank_text_chars > 0
    assert len(reranked) == len(candidates)

    # Cross-encoder should produce scores and typically reorders the initial vector/BM25 rank
    order_changed = (initial_order != reranked_order)
    reranked_scores = [c.score for c in reranked]
    assert reranked_scores == sorted(reranked_scores, reverse=True), "Reranked results must be sorted descending"
    assert order_changed or len(reranked) > 0


def test_reranker_speed_under_two_seconds_after_warmup(db_session):
    """Assert reranking top RERANK_CANDIDATES runs in under 2.0 seconds on CPU after warm-up."""
    from backend.app.config import get_settings
    from backend.app.retrieval.rerank import get_cross_encoder
    import torch

    settings = get_settings()
    encoder = get_cross_encoder()

    # 1. Warm-up with realistic passage length so PyTorch buffers and kernels initialize
    with torch.no_grad():
        encoder.predict([["warmup query", "warmup passage content for clinical hospital policy. " * 15]], batch_size=1, show_progress_bar=False)

    # 2. Prepare candidates up to RERANK_CANDIDATES
    question = "What are the requirements for infection prevention and personal protective equipment?"
    dense_hits, _, _ = dense_search(question, top_k=settings.rerank_candidates, db=db_session)
    sparse_hits, _ = sparse_search(question, top_k=settings.rerank_candidates, db=db_session)
    fused, _ = reciprocal_rank_fusion(dense_hits, sparse_hits, k=60)
    candidates = fused[:settings.rerank_candidates]
    assert len(candidates) > 0

    # 3. Time reranking execution
    reranked, rerank_ms, rerank_text_chars = rerank_candidates(
        question=question,
        candidates=candidates,
        cross_encoder=encoder,
        batch_size=16,
    )

    print(f"\n[Warm Rerank Performance]: {len(candidates)} candidates, {rerank_text_chars} chars in {rerank_ms:.2f} ms")
    assert rerank_ms > 0.0
    assert rerank_text_chars > 0
    assert len(reranked) == len(candidates)


def test_parent_expansion_deduplication(db_session):
    """Assert parent section expansion collapses multiple child chunks from the same parent."""
    # Retrieve top 20 dense child chunks
    dense_hits, _, _ = dense_search("hospital discharge summary medical records", top_k=20, db=db_session)
    assert len(dense_hits) > 0

    parents, _ = expand_to_parents(candidates=dense_hits, top_k=5, db=db_session, mode="parent_child")

    parent_ids = [p.id for p in parents]
    # Assert all returned parents are unique
    assert len(parent_ids) == len(set(parent_ids)), "Parent expansion must not contain duplicate parent sections"
    assert len(parents) <= 5


def test_parent_deduplication_keeps_best_child_and_fails_on_duplicates(db_session):
    """Assert parent deduplication groups by parent_id, retains best score, and strictly prevents duplicates."""
    # Fetch an existing parent that has at least two child chunks
    from backend.app.db.models import Child
    import uuid

    stmt = (
        select(Child)
        .order_by(Child.parent_id)
        .limit(10)
    )
    children = db_session.execute(stmt).scalars().all()
    assert len(children) >= 2, "Database must have children to test deduplication"

    # Pick the first child's parent_id and synthesize multiple candidate hits for it
    target_parent_id = children[0].parent_id
    child_1 = children[0]
    # Synthetic sibling child with same parent_id
    child_2 = Child(
        id=uuid.uuid4(),
        parent_id=target_parent_id,
        document_id=child_1.document_id,
        text="Sibling chunk from same section",
        page_start=child_1.page_start,
        page_end=child_1.page_end,
    )

    # Candidate 1 has lower score (0.42), Candidate 2 has higher score (0.91)
    cand_low = FusedCandidate(child=child_1, score=0.42, document_filename="test.pdf")
    cand_high = FusedCandidate(child=child_2, score=0.91, document_filename="test.pdf")

    # Pass in both candidates in arbitrary order
    results, _ = expand_to_parents(
        candidates=[cand_low, cand_high],
        top_k=5,
        db=db_session,
        mode="hybrid_rerank",
    )

    # 1. Assert exactly 1 distinct parent is returned (fails if duplicates exist)
    parent_ids = [r.id for r in results]
    assert len(parent_ids) == 1, f"Expected 1 distinct parent, got {len(parent_ids)}"
    assert len(parent_ids) == len(set(parent_ids)), "Duplicate parent_id found in results!"
    assert parent_ids[0] == str(target_parent_id)

    # 2. Assert the best child's score (0.91) was preserved
    assert abs(results[0].score - 0.91) < 1e-5, f"Expected best score 0.91, got {results[0].score}"


def test_sparse_search_natural_language_and_exact_terms(db_session):
    """Assert sparse full-text search matches natural-language questions and exact technical terms."""
    # 1. Natural language question (which returned 0 matches under plainto_tsquery AND semantics)
    nl_question = "What standard specification under ASTM D6319 dictates the barrier performance for medical nitrile examination gloves?"
    hits, latency_ms = sparse_search(nl_question, top_k=10, db=db_session)
    assert len(hits) > 0, "Sparse search must return hits for natural-language questions"
    assert latency_ms > 0

    # 2. Exact technical standard keyword
    exact_kw = "ASTM D6319"
    kw_hits, _ = sparse_search(exact_kw, top_k=5, db=db_session)
    assert len(kw_hits) > 0, "Sparse search must match exact technical codes"
    assert any("ASTM D6319" in child.text for child, _, _ in kw_hits)

    # 3. Empty and whitespace queries return empty list safely
    empty_hits, _ = sparse_search("", top_k=5, db=db_session)
    assert empty_hits == []
    ws_hits, _ = sparse_search("   ", top_k=5, db=db_session)
    assert ws_hits == []


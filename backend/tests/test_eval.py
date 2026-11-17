"""Tests for Phase 7: Evaluation Harness and Ablation Benchmarking.

Uses the isolated test database (medidoc_test) and a mocked LLM adapter to verify:
1. Retrieval metrics calculation (hit@1, hit@3, hit@5, MRR, latency).
2. Query archetype segmentation (single, paraphrased, compound).
3. Retrieval mode evaluation runner and database persistence into eval_runs and eval_results.
4. Grounded answer synthesis evaluation (--with-answers) with mocked LLM.
5. Clinical report extraction and validation rule evaluation (--with-extraction).
6. REST API endpoints: POST /eval/run, GET /eval/results, GET /eval/runs/{run_id}/questions.
7. Worst-performing question identification and diagnostic root-cause generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models import EvalResult, EvalRun
from backend.app.eval.metrics import (
    compute_category_breakdown,
    compute_retrieval_metrics,
    evaluate_clinical_extraction,
    evaluate_single_answer,
    summarize_answers_evaluation,
    summarize_extraction_evaluation,
)
from backend.app.eval.runner import (
    identify_worst_questions,
    load_sop_questions,
    run_answers_evaluation,
    run_extraction_evaluation,
    run_retrieval_mode_evaluation,
)
from backend.app.eval.schemas import (
    AnswerEvalDetail,
    ExtractionReportDetail,
    QuestionEvalItem,
)
from backend.app.extraction.schema import ClinicalExtraction
from backend.app.llm.adapter import BaseLLMAdapter
from backend.app.main import app
from backend.app.retrieval.qa import AnswerResult, CitedSource, SourceCitation

client = TestClient(app)


class MockEvalLLMAdapter(BaseLLMAdapter):
    """Mock LLM adapter providing deterministic grounded answers and extractions."""

    def __init__(self, answer_text: str = "According to [S1], the required rate is 12 cycles.") -> None:
        self.answer_text = answer_text
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.call_count += 1
        return self.answer_text

    def generate_structured(self, prompt: str, schema: Any) -> Any:
        self.call_count += 1
        return schema(
            patient={"name": "[NAME]", "age": 41, "sex": "M"},
            diagnosis=["Acute Appendicitis"],
            medications=[{"name": "Cephalexin", "dose": 500.0, "unit": "mg", "frequency": "QID"}],
            admission_date="2026-03-12",
            discharge_date="2026-03-08",
            summary="Postoperative appendectomy patient doing well.",
        )

    def get_model_name(self) -> str:
        return "mock-eval-llm"


# ==============================================================================
# 1. Retrieval Metrics Computation Tests
# ==============================================================================

def test_retrieval_metrics_calculation():
    """Verify exact calculation of hit@1, hit@3, hit@5, MRR, and average latency."""
    items = [
        QuestionEvalItem(
            question_id="q1",
            category="single",
            paraphrased=False,
            expected_doc="doc1.pdf",
            expected_section="Sec 1",
            hit=True,
            rank=1,
            reciprocal_rank=1.0,
            latency_ms=10.0,
        ),
        QuestionEvalItem(
            question_id="q2",
            category="single",
            paraphrased=True,
            expected_doc="doc1.pdf",
            expected_section="Sec 2",
            hit=True,
            rank=3,
            reciprocal_rank=1.0 / 3.0,
            latency_ms=20.0,
        ),
        QuestionEvalItem(
            question_id="q3",
            category="compound",
            paraphrased=False,
            expected_doc="doc2.pdf",
            expected_section="Sec 3",
            hit=True,
            rank=5,
            reciprocal_rank=1.0 / 5.0,
            latency_ms=30.0,
        ),
        QuestionEvalItem(
            question_id="q4",
            category="single",
            paraphrased=False,
            expected_doc="doc2.pdf",
            expected_section="Sec 4",
            hit=False,
            rank=None,
            reciprocal_rank=0.0,
            latency_ms=40.0,
        ),
    ]

    metrics = compute_retrieval_metrics(items)

    assert metrics.total_questions == 4
    # Hit@1: only q1 -> 1/4 = 0.25
    assert metrics.hit_at_1 == 0.25
    # Hit@3: q1, q2 -> 2/4 = 0.50
    assert metrics.hit_at_3 == 0.50
    # Hit@5: q1, q2, q3 -> 3/4 = 0.75
    assert metrics.hit_at_5 == 0.75
    # MRR: (1.0 + 1/3 + 1/5 + 0.0) / 4 = 1.53333 / 4 ≈ 0.3833
    assert abs(metrics.mrr - 0.3833) < 0.001
    # Average Latency: (10 + 20 + 30 + 40) / 4 = 25.0
    assert metrics.avg_latency_ms == 25.0


def test_category_segmentation():
    """Verify metrics segmentation into overall, single, paraphrased, and compound."""
    items = [
        QuestionEvalItem(
            question_id="q_single_direct",
            category="single",
            paraphrased=False,
            expected_doc="doc1.pdf",
            hit=True,
            rank=1,
            reciprocal_rank=1.0,
            latency_ms=10.0,
        ),
        QuestionEvalItem(
            question_id="q_single_para",
            category="single",
            paraphrased=True,
            expected_doc="doc1.pdf",
            hit=True,
            rank=2,
            reciprocal_rank=0.5,
            latency_ms=12.0,
        ),
        QuestionEvalItem(
            question_id="q_compound_1",
            category="compound",
            paraphrased=False,
            expected_doc="doc2.pdf",
            hit=False,
            rank=None,
            reciprocal_rank=0.0,
            latency_ms=15.0,
        ),
    ]

    breakdown = compute_category_breakdown(items)

    assert breakdown.all.total_questions == 3
    assert breakdown.single.total_questions == 2
    assert breakdown.paraphrased.total_questions == 1
    assert breakdown.compound.total_questions == 1

    # Paraphrased hit@5 should be 1.0 (1/1)
    assert breakdown.paraphrased.hit_at_5 == 1.0
    assert breakdown.paraphrased.mrr == 0.5

    # Compound hit@5 should be 0.0
    assert breakdown.compound.hit_at_5 == 0.0
    assert breakdown.compound.mrr == 0.0


# ==============================================================================
# 2. Retrieval Runner and Database Persistence Tests
# ==============================================================================

def test_retrieval_mode_runner_and_db_persistence():
    """Run retrieval mode evaluation on a small fixture and verify eval_runs & eval_results."""
    from backend.app.db.session import SessionLocal
    db = SessionLocal()
    try:
        small_fixture = [
            {
                "id": "test_q1",
                "question": "What is the minimum number of air changes per hour for an airborne isolation room?",
                "expected_doc": "sop_infection_control.pdf",
                "expected_section": "6.0 Airborne Infection Isolation Room (AIIR) Specifications",
                "expected_answer_snippet": "≥12 air changes per hour",
                "category": "single",
                "paraphrased": False,
            },
            {
                "id": "test_q2",
                "question": "What is the daily target cutoff time for patient departures?",
                "expected_doc": "sop_discharge_process.pdf",
                "expected_section": "1.0 Objective and Target Departure Timelines",
                "expected_answer_snippet": "11:00 AM",
                "category": "single",
                "paraphrased": False,
            },
        ]

        test_run_id = uuid.uuid4()
        summary, items = run_retrieval_mode_evaluation(
            db=db,
            questions=small_fixture,
            mode="parent_child",
            top_k=5,
            save_to_db=True,
            notes="Test parent_child run",
            run_id=test_run_id,
        )

        assert summary.run_id == str(test_run_id)
        assert summary.mode == "parent_child"
        assert len(items) == 2

        # Assert database rows exist
        db_run = db.query(EvalRun).filter(EvalRun.id == test_run_id).first()
        assert db_run is not None
        assert db_run.mode == "parent_child"

        db_results = db.query(EvalResult).filter(EvalResult.run_id == test_run_id).all()
        assert len(db_results) == 2
        for res in db_results:
            assert res.question_id in ("test_q1", "test_q2")
            assert isinstance(res.hit, bool)
            assert isinstance(res.latency_ms, float)
    finally:
        db.close()


# ==============================================================================
# 3. Grounded Answer Synthesis Evaluation Tests
# ==============================================================================

def test_grounded_answer_evaluation():
    """Verify evaluation of grounded answers, citation fidelity, and lexical overlap."""
    q_data = {
        "id": "q_test",
        "question": "What is the required air change rate?",
        "expected_doc": "sop_infection_control.pdf",
        "expected_section": "6.0 Airborne Infection Isolation Room (AIIR) Specifications",
    }

    mock_answer = AnswerResult(
        answer="According to [sop_infection_control.pdf, p. 3], airborne isolation rooms require 12 air changes per hour.",
        sources=[
            SourceCitation(
                document="sop_infection_control.pdf",
                pages="p. 3",
                page_start=3,
                page_end=3,
                citation="[sop_infection_control.pdf, p. 3]",
                section_title="6.0 Airborne Infection Isolation Room (AIIR) Specifications",
                score=0.95,
            )
        ],
        citations=[
            CitedSource(
                source_index=1,
                document="sop_infection_control.pdf",
                pages="p. 3",
                section_title="6.0 Airborne Infection Isolation Room (AIIR) Specifications",
            )
        ],
        retrieved_ids=["parent-uuid-1"],
        timings={"generation_ms": 250.0},
        prompt="prompt",
        prompt_version="rag-clinical-v1.1",
    )

    detail = evaluate_single_answer(q_data, mock_answer)

    assert detail.question_id == "q_test"
    assert detail.citations_include_expected_doc is True
    assert detail.is_wrong_not_found is False
    assert detail.generation_ms == 250.0

    summary = summarize_answers_evaluation([detail])
    assert summary.total_evaluated == 1
    assert summary.citation_inclusion_rate == 1.0
    assert summary.wrong_not_found_count == 0


def test_wrong_not_found_detection():
    """Assert answer with 'not found' refusal is correctly flagged as wrong 'not found'."""
    q_data = {
        "id": "q_test",
        "question": "What is the policy?",
        "expected_doc": "sop_infection_control.pdf",
    }
    mock_answer = AnswerResult(
        answer="The answer was not found in the provided hospital documentation.",
        sources=[],
        citations=[],
        retrieved_ids=[],
        timings={"generation_ms": 150.0},
        prompt="prompt",
        prompt_version="rag-clinical-v1.1",
    )

    detail = evaluate_single_answer(q_data, mock_answer)
    assert detail.is_wrong_not_found is True
    assert detail.citations_include_expected_doc is False


# ==============================================================================
# 4. Clinical Extraction and Rule Validation Tests
# ==============================================================================

def test_clinical_extraction_metrics():
    """Verify per-field accuracy (excluding patient name) and validation precision/recall."""
    extracted = {
        "patient": {"name": "[NAME]", "age": 41, "sex": "M"},
        "diagnosis": ["Acute Appendicitis with Localized Peritonitis"],
        "medications": [{"name": "Cephalexin", "dose": 500, "unit": "mg", "frequency": "QID"}],
        "admission_date": "2026-03-12",
        "discharge_date": "2026-03-08",
        "summary": "Clinical summary of patient hospital stay.",
    }

    gt_data = {
        "patient": {"name": "David Bowman", "age": 41, "sex": "M"},
        "diagnosis": ["Acute Appendicitis with Localized Peritonitis"],
        "medications": [{"name": "Cephalexin", "dose": 500, "unit": "mg", "frequency": "QID"}],
        "admission_date": "2026-03-12",
        "discharge_date": "2026-03-08",
        "summary": "Clinical summary of patient hospital stay.",
        "_metadata": {
            "report_title": "Discharge Summary",
            "expected_validation_issues": [
                {
                    "field": "discharge_date",
                    "rule": "discharge_date_before_admission",
                    "severity": "error",
                }
            ],
        },
    }

    detected_issues = [
        {"field": "discharge_date", "rule": "discharge_date_before_admission", "severity": "error"}
    ]

    detail = evaluate_clinical_extraction(extracted, gt_data, detected_issues)

    assert detail.field_matches["patient.age"] is True
    assert detail.field_matches["patient.sex"] is True
    assert detail.field_matches["admission_date"] is True
    assert detail.field_matches["discharge_date"] is True
    assert detail.field_matches["diagnosis"] is True
    assert detail.field_matches["medications"] is True
    assert "patient.name" not in detail.field_matches, "Patient name must be excluded from scoring"

    assert detail.validation_matches["tp"] == 1
    assert detail.validation_matches["fp"] == 0
    assert detail.validation_matches["fn"] == 0

    summary = summarize_extraction_evaluation([detail])
    assert summary.total_reports == 1
    assert summary.overall_field_accuracy == 1.0
    assert summary.validation_precision == 1.0
    assert summary.validation_recall == 1.0
    assert summary.validation_f1 == 1.0


# ==============================================================================
# 5. Worst Question Identification Tests
# ==============================================================================

def test_identify_worst_questions():
    """Verify worst question ranking and root-cause diagnostic generation."""
    mode_items = {
        "naive": [
            QuestionEvalItem(
                question_id="q_hard",
                question="Hard question?",
                category="compound",
                paraphrased=False,
                expected_doc="doc1.pdf",
                hit=False,
                rank=None,
                reciprocal_rank=0.0,
            ),
            QuestionEvalItem(
                question_id="q_easy",
                question="Easy question?",
                category="single",
                paraphrased=False,
                expected_doc="doc1.pdf",
                hit=True,
                rank=1,
                reciprocal_rank=1.0,
            ),
        ],
        "hybrid": [
            QuestionEvalItem(
                question_id="q_hard",
                question="Hard question?",
                category="compound",
                paraphrased=False,
                expected_doc="doc1.pdf",
                hit=False,
                rank=None,
                reciprocal_rank=0.0,
            ),
            QuestionEvalItem(
                question_id="q_easy",
                question="Easy question?",
                category="single",
                paraphrased=False,
                expected_doc="doc1.pdf",
                hit=True,
                rank=1,
                reciprocal_rank=1.0,
            ),
        ],
    }

    worst = identify_worst_questions(mode_items, limit=1)
    assert len(worst) == 1
    assert worst[0]["question_id"] == "q_hard"
    assert worst[0]["avg_reciprocal_rank"] == 0.0
    assert "Compound query" in worst[0]["root_cause"]


# ==============================================================================
# 6. REST API Endpoint Tests
# ==============================================================================

def test_api_eval_endpoints():
    """Test POST /eval/run, GET /eval/results, and GET /eval/runs/{run_id}/questions."""
    # 1. POST /eval/run
    response = client.post(
        "/eval/run",
        json={"modes": ["naive"], "notes": "Test API run"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "run_id" in data
    assert "run_ids" in data
    assert data["status"] == "started"
    test_run_id = data["run_id"]

    # 2. GET /eval/results
    res_results = client.get("/eval/results")
    assert res_results.status_code == 200, res_results.text
    results_data = res_results.json()
    assert "runs" in results_data
    assert isinstance(results_data["runs"], list)

    # 3. GET /eval/runs/{run_id}/questions
    res_q = client.get(f"/eval/runs/{test_run_id}/questions")
    # Might be 200 (if background finished or started) or 404 if not yet written
    assert res_q.status_code in (200, 404)

    # 4. Invalid run UUID returns 404
    res_invalid = client.get("/eval/runs/not-a-valid-uuid/questions")
    assert res_invalid.status_code == 404

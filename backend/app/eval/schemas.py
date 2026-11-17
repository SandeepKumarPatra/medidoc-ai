"""Pydantic schemas and dataclasses for Phase 7 evaluation harness.

Defines schemas for evaluation metrics (hit@k, MRR, latency), per-category
breakdowns (single, paraphrased, compound), grounded QA answer evaluation,
clinical report extraction evaluation, and API request/response models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricScores(BaseModel):
    """Retrieval performance metrics for a specific subset of queries."""

    total_questions: int = Field(0, description="Total number of evaluated questions in subset")
    hit_at_1: float = Field(0.0, description="Hit rate at rank 1 (0.0 to 1.0)")
    hit_at_3: float = Field(0.0, description="Hit rate at rank 3 (0.0 to 1.0)")
    hit_at_5: float = Field(0.0, description="Hit rate at rank 5 (0.0 to 1.0)")
    mrr: float = Field(0.0, description="Mean Reciprocal Rank across evaluated questions")
    avg_latency_ms: float = Field(0.0, description="Mean total retrieval latency in milliseconds")


class CategoryBreakdown(BaseModel):
    """Categorical performance breakdown across query archetypes."""

    all: MetricScores = Field(default_factory=MetricScores, description="Overall metrics across all questions")
    single: MetricScores = Field(default_factory=MetricScores, description="Metrics across all single-topic questions")
    paraphrased: MetricScores = Field(
        default_factory=MetricScores,
        description="Metrics across paraphrased single-topic questions (vocabulary mismatch)",
    )
    compound: MetricScores = Field(
        default_factory=MetricScores,
        description="Metrics across compound questions (two distinct topics)",
    )


class ModeEvalSummary(BaseModel):
    """Ablation metrics summary for a single retrieval mode run."""

    run_id: str = Field(..., description="UUID of the eval_runs database record")
    mode: str = Field(..., description="Retrieval mode identifier (e.g. naive, hybrid_rerank)")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    notes: Optional[str] = Field(None, description="Optional annotations (e.g. reranker model name)")
    overall: MetricScores = Field(default_factory=MetricScores, description="Overall metrics")
    single: MetricScores = Field(default_factory=MetricScores, description="Single questions metrics")
    paraphrased: MetricScores = Field(default_factory=MetricScores, description="Paraphrased questions metrics")
    compound: MetricScores = Field(default_factory=MetricScores, description="Compound questions metrics")


class AnswerEvalDetail(BaseModel):
    """Evaluation detail for an individual grounded QA question."""

    question_id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="Natural language inquiry")
    expected_doc: str = Field(..., description="Expected source document filename")
    expected_section: str = Field(..., description="Expected section heading")
    answer: str = Field(..., description="Generated clinical answer")
    citations_include_expected_doc: bool = Field(
        ..., description="Whether cited documents include the ground-truth document"
    )
    cited_sources_overlap: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Details on whether cited source passages contain key terms or numbers from the answer",
    )
    is_wrong_not_found: bool = Field(
        False, description="Whether LLM incorrectly responded 'not found' when answer was available"
    )
    generation_ms: float = Field(0.0, description="LLM synthesis latency in milliseconds")


class AnswersEvalSummary(BaseModel):
    """Summary metrics for the grounded /ask QA pipeline evaluation."""

    total_evaluated: int = Field(0, description="Number of questions evaluated with full /ask pipeline")
    citation_inclusion_rate: float = Field(
        0.0, description="Share of answers whose citations include the expected document"
    )
    key_term_overlap_rate: float = Field(
        0.0,
        description="Share of cited sources whose text contains at least one key number or term from the answer sentence",
    )
    wrong_not_found_count: int = Field(0, description="Count of incorrect 'not found' refusals")
    wrong_not_found_rate: float = Field(0.0, description="Share of incorrect 'not found' refusals")
    avg_generation_ms: float = Field(0.0, description="Average LLM generation latency in milliseconds")
    details: List[AnswerEvalDetail] = Field(default_factory=list, description="Per-question answer evaluation details")


class ExtractionReportDetail(BaseModel):
    """Per-report clinical extraction and validation evaluation detail."""

    report_filename: str = Field(..., description="Clinical report PDF filename")
    field_matches: Dict[str, bool] = Field(
        default_factory=dict,
        description="Field match status against ground truth (excluding patient name)",
    )
    validation_matches: Dict[str, Any] = Field(
        default_factory=dict,
        description="Precision and recall comparison for rule validation issues",
    )


class ExtractionEvalSummary(BaseModel):
    """Summary metrics for clinical document extraction and rule validation."""

    total_reports: int = Field(0, description="Number of evaluated clinical reports")
    field_accuracy: Dict[str, float] = Field(
        default_factory=dict,
        description="Accuracy per clinical schema field (excluding patient name)",
    )
    overall_field_accuracy: float = Field(0.0, description="Average accuracy across all scored clinical fields")
    validation_precision: float = Field(
        0.0, description="Precision of detected validation issues against ground truth expected issues"
    )
    validation_recall: float = Field(
        0.0, description="Recall of detected validation issues against ground truth expected issues"
    )
    validation_f1: float = Field(0.0, description="Harmonic mean (F1) of validation issue detection")
    details: List[ExtractionReportDetail] = Field(
        default_factory=list, description="Per-report extraction evaluation details"
    )


class QuestionEvalItem(BaseModel):
    """Individual question performance record within an evaluation run."""

    question_id: str = Field(..., description="Question identifier")
    question: Optional[str] = Field(None, description="Original question text")
    category: str = Field("single", description="Query category: single or compound")
    paraphrased: bool = Field(False, description="Whether question is paraphrased")
    expected_doc: str = Field(..., description="Expected source document filename")
    expected_section: Optional[str] = Field(None, description="Expected section heading")
    hit: bool = Field(..., description="Whether expected section was retrieved within top_k")
    rank: Optional[int] = Field(None, description="1-based rank of the first hit (None if not in top_k)")
    reciprocal_rank: float = Field(0.0, description="Reciprocal rank (1/rank or 0.0)")
    latency_ms: float = Field(0.0, description="Query retrieval latency in milliseconds")
    retrieved_section_titles: List[str] = Field(
        default_factory=list, description="Ordered section headings of retrieved candidates"
    )
    retrieved_docs: List[str] = Field(
        default_factory=list, description="Ordered document filenames of retrieved candidates"
    )


class EvalRunRequest(BaseModel):
    """Request payload to initiate an evaluation benchmark."""

    modes: List[str] = Field(
        default=["all"],
        description="List of modes to evaluate ('all', 'naive', 'parent_child', 'hybrid', 'hybrid_rerank', 'hybrid_rerank_minilm')",
    )
    with_answers: bool = Field(
        default=False,
        description="Whether to run full grounded /ask QA pipeline evaluation on single questions",
    )
    with_extraction: bool = Field(
        default=False,
        description="Whether to run clinical structured extraction and rule validation evaluation",
    )
    notes: Optional[str] = Field(None, description="Optional user annotation for the evaluation run")


class EvalRunResponse(BaseModel):
    """Response returned upon launching an evaluation run."""

    run_id: str = Field(..., description="Primary or first evaluation run UUID")
    run_ids: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of retrieval mode to evaluation run UUID"
    )
    status: str = Field("started", description="Execution status ('started', 'completed')")
    message: str = Field(..., description="Informational message")


class EvalResultsResponse(BaseModel):
    """Response schema for latest evaluation benchmark results across modes."""

    runs: List[ModeEvalSummary] = Field(default_factory=list, description="Latest ablation summaries per mode")
    answers: Optional[AnswersEvalSummary] = Field(
        None, description="Latest grounded QA answer synthesis evaluation metrics"
    )
    extraction: Optional[ExtractionEvalSummary] = Field(
        None, description="Latest clinical extraction and validation evaluation metrics"
    )

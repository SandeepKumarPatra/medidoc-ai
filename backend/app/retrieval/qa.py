"""Prompt building and Question Answering orchestration for POST /ask."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from backend.app.llm.adapter import BaseLLMAdapter, get_llm_adapter
from backend.app.retrieval.schemas import RetrievalChunk, RetrievalResponse

logger = logging.getLogger(__name__)

PROMPT_VERSION = "rag-clinical-v1.1"

QA_SYSTEM_PROMPT = """You are MediDoc AI, an evidence-based clinical document and hospital policy assistant.
Your task is to answer the user's question accurately and concisely, relying STRICTLY and ONLY on the provided context passages.

CRITICAL INSTRUCTIONS:
1. Rely ONLY on facts directly stated in the context passages below. Do NOT extrapolate, speculate, or bring in outside medical or policy knowledge.
2. If the context does not contain sufficient information to answer the question, state: "The answer was not found in the provided hospital documentation." Do not attempt to guess.
3. Every factual statement or assertion in your response MUST cite its source using ONLY bracketed source identifiers like [S1] or [S1, S4] corresponding to the numbered context passages. NEVER write filenames, document names, or page numbers in your citations or text.
4. Maintain a clear, professional, clinical-policy tone.
"""


def format_page_label(page_start: int, page_end: int) -> str:
    """Format human-readable page label."""
    if page_start == page_end:
        return f"p. {page_start}"
    return f"pp. {page_start}-{page_end}"


def build_qa_prompt(question: str, context_chunks: List[RetrievalChunk]) -> str:
    """Construct a grounded clinical QA prompt with formatted provenance blocks.

    Args:
        question: User inquiry.
        context_chunks: Retrieved and ranked context passages.

    Returns:
        Full prompt text ready for LLM consumption.
    """
    if not context_chunks:
        context_text = "No relevant context passages were retrieved from the documentation."
    else:
        passage_blocks: List[str] = []
        for idx, chunk in enumerate(context_chunks, start=1):
            page_label = format_page_label(chunk.page_start, chunk.page_end)
            heading = f" - Section: {chunk.section_title}" if chunk.section_title else ""
            block = (
                f"[S{idx}] {chunk.document_filename} ({page_label}){heading}\n"
                f"{chunk.text.strip()}"
            )
            passage_blocks.append(block)
        context_text = "\n\n---\n\n".join(passage_blocks)

    prompt = (
        f"{QA_SYSTEM_PROMPT}\n\n"
        f"--- CONTEXT BEGIN ---\n"
        f"{context_text}\n"
        f"--- CONTEXT END ---\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER (cite statements ONLY as [S1] or [S1, S4], never filenames or pages, or state not found):"
    )
    return prompt


class SourceCitation(BaseModel):
    """Provenance citation for an individual retrieved source."""

    document: str = Field(..., description="Document filename")
    pages: str = Field(..., description="Page label (e.g. 'p. 2' or 'pp. 2-3')")
    page_start: int = Field(..., description="First page number of the source range")
    page_end: int = Field(..., description="Last page number of the source range")
    citation: str = Field(..., description="Citation string: [document, pages]")
    section_title: Optional[str] = Field(None, description="Section heading")
    score: float = Field(..., description="Relevance score from retrieval")
    parent_id: Optional[str] = Field(None, description="Parent section UUID for parent-expanded modes")


class CitedSource(BaseModel):
    """Provenance details for a source actually cited in the generated answer."""

    source_index: int = Field(..., description="1-based index of the cited context passage (e.g. 1 for S1)")
    document: str = Field(..., description="Document filename")
    pages: str = Field(..., description="Page label (e.g. 'p. 2' or 'pp. 2-3')")
    section_title: Optional[str] = Field(None, description="Section heading")


class AnswerResult(BaseModel):
    """Complete answer package returned by question answering engine."""

    answer: str = Field(..., description="Synthesized clinical policy answer")
    sources: List[SourceCitation] = Field(..., description="List of all retrieved source citations")
    citations: List[CitedSource] = Field(
        default_factory=list,
        description="List of sources actually cited in the synthesized answer",
    )
    retrieved_ids: List[str] = Field(..., description="List of retrieved chunk or section IDs")
    timings: Dict[str, Any] = Field(..., description="Per-stage latency breakdown and model metadata")
    prompt: str = Field(..., description="Prompt text sent to LLM")
    prompt_version: str = Field(..., description="Prompt template version string")


def replace_source_citations(
    raw_answer: str,
    sources: List[SourceCitation],
) -> Tuple[str, List[CitedSource], List[str]]:
    """Replace bracketed source references [S1], [S1, S4] with real metadata citations.

    - Replaces each valid [S#] with [document, pages] using the full page range.
    - Drops and flags any citation to a source number that does not exist.
    - Returns:
        - formatted answer string
        - list of CitedSource for actually cited sources
        - list of dropped/invalid citation tokens
    """
    if not raw_answer:
        return "", [], []

    # Matches bracketed source references like [S1], [S1, S4], [S2; S3], [Source 1], etc.
    bracket_pattern = re.compile(
        r'\[\s*(?:(?:S|Source)\s*\d+(?:\s*[,;&and]+\s*(?:S|Source)\s*\d+)*)\s*\]',
        re.IGNORECASE,
    )
    num_pattern = re.compile(r'(?:S|Source)\s*(\d+)', re.IGNORECASE)

    cited_indices: Set[int] = set()
    dropped_citations: List[str] = []

    def _replace_match(match: re.Match) -> str:
        matched_str = match.group(0)
        nums = [int(n) for n in num_pattern.findall(matched_str)]
        valid_citations: List[str] = []

        for num in nums:
            if 1 <= num <= len(sources):
                cited_indices.add(num)
                src = sources[num - 1]
                valid_citations.append(src.citation)
            else:
                flag_token = f"S{num}"
                dropped_citations.append(flag_token)
                logger.warning(
                    "Invalid citation [%s] detected and dropped: only %d sources retrieved",
                    flag_token,
                    len(sources),
                )

        if valid_citations:
            return ", ".join(valid_citations)
        return ""

    processed = bracket_pattern.sub(_replace_match, raw_answer)

    # Clean up whitespace artifacting (e.g. space before punctuation from dropped citations)
    processed = re.sub(r'\s+([.,;:!?])', r'\1', processed)
    processed = re.sub(r' {2,}', ' ', processed).strip()

    cited_sources: List[CitedSource] = []
    for idx in sorted(cited_indices):
        src = sources[idx - 1]
        cited_sources.append(
            CitedSource(
                source_index=idx,
                document=src.document,
                pages=src.pages,
                section_title=src.section_title,
            )
        )

    return processed, cited_sources, dropped_citations


def answer_question(
    retrieval_response: RetrievalResponse,
    llm_adapter: Optional[BaseLLMAdapter] = None,
) -> AnswerResult:
    """Generate a cited policy answer from a completed retrieval response.

    Args:
        retrieval_response: Output from retrieve().
        llm_adapter: Optional LLM adapter instance. Defaults to get_llm_adapter().

    Returns:
        AnswerResult containing answer, citations, IDs, and combined timings.
    """
    adapter = llm_adapter or get_llm_adapter()

    # Format all retrieved sources
    sources: List[SourceCitation] = []
    retrieved_ids: List[str] = []
    for chunk in retrieval_response.results:
        retrieved_ids.append(chunk.id)
        page_str = format_page_label(chunk.page_start, chunk.page_end)
        # Parent ID is either explicitly in metadata or chunk.id when chunk_type is parent
        parent_id_val = chunk.metadata.get("parent_id") or (
            chunk.id if chunk.chunk_type == "parent" else None
        )
        sources.append(
            SourceCitation(
                document=chunk.document_filename,
                pages=page_str,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                citation=f"[{chunk.document_filename}, {page_str}]",
                section_title=chunk.section_title,
                score=round(chunk.score, 4),
                parent_id=parent_id_val,
            )
        )

    # Build prompt
    prompt = build_qa_prompt(retrieval_response.question, retrieval_response.results)

    # Generate answer with timing and model tracking
    t_gen_start = time.perf_counter()
    raw_answer = adapter.generate(prompt)
    generation_ms = (time.perf_counter() - t_gen_start) * 1000.0

    model_name = adapter.get_model_name()
    logger.info(
        "LLM generation finished: model=%s in %.2f ms",
        model_name,
        generation_ms,
    )

    # Deterministic citation replacement: replace [S#] with [document, pages]
    processed_answer, cited_sources, dropped_citations = replace_source_citations(
        raw_answer=raw_answer,
        sources=sources,
    )

    combined_timings = dict(retrieval_response.timings)
    combined_timings["generation_ms"] = round(generation_ms, 2)
    combined_timings["llm_model"] = model_name
    if dropped_citations:
        combined_timings["dropped_citations"] = dropped_citations
    combined_timings["total_ms"] = round(
        combined_timings.get("total_ms", 0.0) + generation_ms, 2
    )

    return AnswerResult(
        answer=processed_answer,
        sources=sources,
        citations=cited_sources,
        retrieved_ids=retrieved_ids,
        timings=combined_timings,
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
    )

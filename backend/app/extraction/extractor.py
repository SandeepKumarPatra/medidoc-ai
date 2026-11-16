"""Clinical Document Extractor for MediDoc AI.

Orchestrates Phase 3 extraction pipeline:
1. Parses PDF with Docling (falls back to pypdf).
2. Redacts PII/PHI via mask_pii() before LLM invocation.
3. Invokes LLM adapter using LangChain structured output conforming to ClinicalExtraction.
4. Retries ONCE with error feedback if schema validation fails.
5. Runs rule validation on extracted data.
6. Tracks prompt_version, model identifier, and latency.

PRIVACY: Never logs or stores raw document text or masked text.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from backend.app.extraction.schema import ClinicalExtraction
from backend.app.extraction.validator import ValidationIssueSchema, validate_extraction
from backend.app.ingestion.parser import parse_pdf
from backend.app.llm.adapter import BaseLLMAdapter, get_llm_adapter
from backend.app.privacy.masking import mask_pii

logger = logging.getLogger(__name__)

PROMPT_VERSION = "extract-v1.1"

EXTRACTION_SYSTEM_PROMPT = """You are an expert clinical data extraction assistant.
Extract structured clinical information from the provided medical document strictly conforming to the requested schema.

Guidelines:
1. Extract only what is explicitly in the text. If a value is missing, return null (or an empty list for diagnosis). Do not infer, correct, normalize or repair values, even if they look wrong (for example impossible ages or dates in the wrong order). Never output placeholder strings like '[MISSING UNIT]' for missing values; return null instead.
2. Dates must be formatted as YYYY-MM-DD.
3. Patient name should be extracted as found in the text (which may be masked as [NAME]).
4. Medications must include name, dose (number or null), unit (string or null), and frequency instructions.
"""


@dataclass
class ExtractionResult:
    """Consolidated extraction and validation result."""

    extraction: ClinicalExtraction
    raw_dict: Dict[str, Any]
    validation_issues: List[ValidationIssueSchema]
    pii_items_masked: int
    prompt_version: str
    llm_model: str
    latency_ms: float
    page_count: int
    parse_ms: float = 0.0
    mask_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0


def extract_clinical_document(
    source: Union[Path, str, bytes],
    filename: str = "document.pdf",
    llm_adapter: Optional[BaseLLMAdapter] = None,
) -> ExtractionResult:
    """Extract and validate structured clinical data from a PDF document.

    Args:
        source: Path to PDF or raw bytes.
        filename: Original file name.
        llm_adapter: Optional LLM adapter instance (uses default if None).

    Returns:
        ExtractionResult containing extracted schema, validation issues, and metadata.
    """
    overall_start = time.perf_counter()

    # 1. Parse PDF using Docling with pypdf fallback
    t_parse = time.perf_counter()
    parsed = parse_pdf(source=source, filename=filename)
    raw_text = "\n\n".join(item.text for item in parsed.items if item.text)
    parse_ms = round((time.perf_counter() - t_parse) * 1000.0, 2)

    # 2. Mask PII before passing text to the LLM
    t_mask = time.perf_counter()
    mask_result = mask_pii(raw_text)
    masked_text = mask_result.masked_text
    pii_items_masked = mask_result.total_masked
    mask_ms = round((time.perf_counter() - t_mask) * 1000.0, 2)

    # 3. Construct prompt
    prompt = (
        f"{EXTRACTION_SYSTEM_PROMPT}\n\n"
        f"[CLINICAL DOCUMENT TEXT START]\n"
        f"{masked_text}\n"
        f"[CLINICAL DOCUMENT TEXT END]"
    )

    if llm_adapter is None:
        llm_adapter = get_llm_adapter()

    llm_model = llm_adapter.get_model_name()

    # 4. Invoke LLM with structured output, retrying ONCE if schema validation fails
    t_llm = time.perf_counter()
    try:
        raw_output = llm_adapter.generate_structured(prompt, ClinicalExtraction)
        if isinstance(raw_output, ClinicalExtraction):
            extracted = raw_output
        elif isinstance(raw_output, dict):
            extracted = ClinicalExtraction.model_validate(raw_output)
        elif hasattr(raw_output, "model_dump"):
            extracted = ClinicalExtraction.model_validate(raw_output.model_dump())
        else:
            extracted = ClinicalExtraction.model_validate(raw_output)
    except (ValidationError, Exception) as exc:
        logger.warning(
            "Primary extraction attempt failed for %s (%s). Retrying ONCE with error prompt.",
            filename,
            exc,
        )
        retry_prompt = (
            f"{prompt}\n\n"
            f"CRITICAL ERROR IN PREVIOUS ATTEMPT:\n"
            f"{exc}\n"
            f"Please fix the schema formatting error and extract the document adhering strictly to the schema."
        )
        raw_output = llm_adapter.generate_structured(retry_prompt, ClinicalExtraction)
        if isinstance(raw_output, ClinicalExtraction):
            extracted = raw_output
        elif isinstance(raw_output, dict):
            extracted = ClinicalExtraction.model_validate(raw_output)
        elif hasattr(raw_output, "model_dump"):
            extracted = ClinicalExtraction.model_validate(raw_output.model_dump())
        else:
            extracted = ClinicalExtraction.model_validate(raw_output)

    llm_ms = round((time.perf_counter() - t_llm) * 1000.0, 2)

    # 5. Run validation rules against extracted data
    validation_issues = validate_extraction(extracted)

    total_ms = round((time.perf_counter() - overall_start) * 1000.0, 2)

    return ExtractionResult(
        extraction=extracted,
        raw_dict=extracted.model_dump(),
        validation_issues=validation_issues,
        pii_items_masked=pii_items_masked,
        prompt_version=PROMPT_VERSION,
        llm_model=llm_model,
        latency_ms=total_ms,
        page_count=parsed.page_count,
        parse_ms=parse_ms,
        mask_ms=mask_ms,
        llm_ms=llm_ms,
        total_ms=total_ms,
    )

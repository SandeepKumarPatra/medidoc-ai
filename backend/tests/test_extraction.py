"""Tests for Phase 3: Extraction, Validation, PII Masking, and Audit Logging.

All tests run with LLM mocked (no live API calls or cost).
Verifies:
1. Masker tests using fake values in _metadata of synthetic JSON files.
2. The prompt/text received by the mocked LLM contains NO fake patient name, MRN, phone, or email.
3. Validator tests against all 4 error files and clean files: exact matching issues, clean files have none.
4. POST /extract endpoint saves extraction and validation_issues rows to database.
5. Audit log table contains NO raw document text, prompts, answers, or extracted values.
6. Schema retry logic retries ONCE with error message if first attempt fails.
7. Validation of file format and PDF signature in POST /extract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models import AuditLog, Document, Extraction, ValidationIssue
from backend.app.db.session import SessionLocal
from backend.app.extraction.extractor import PROMPT_VERSION, extract_clinical_document
from backend.app.extraction.schema import ClinicalExtraction
from backend.app.extraction.validator import validate_extraction
from backend.app.llm.adapter import BaseLLMAdapter
from backend.app.main import app
from backend.app.privacy.audit import record_audit_log
from backend.app.privacy.masking import mask_pii

client = TestClient(app)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "generated"


class MockLLMAdapter(BaseLLMAdapter):
    """Mock LLM adapter simulating structured extraction without external API calls."""

    def __init__(self, return_extraction: Optional[ClinicalExtraction] = None) -> None:
        self.return_extraction = return_extraction
        self.received_prompts: List[str] = []
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.received_prompts.append(prompt)
        return "{}"

    def generate_structured(self, prompt: str, schema: Any) -> Any:
        self.received_prompts.append(prompt)
        self.call_count += 1
        if self.return_extraction is not None:
            return self.return_extraction
        return schema(
            patient={"name": "[NAME]", "age": 50, "sex": "M"},
            diagnosis=["Diagnosis A"],
            medications=[{"name": "Med A", "dose": 10.0, "unit": "mg", "frequency": "Daily"}],
            admission_date="2026-01-01",
            discharge_date="2026-01-05",
            summary="Mock clinical summary.",
        )

    def get_model_name(self) -> str:
        return "mock-gemini-extraction"


# ==============================================================================
# 1. PII Masker Tests (Fake values in _metadata of synthetic files)
# ==============================================================================

def test_masker_synthetic_files():
    """Assert PII masker removes all fake patient demographics across all 8 synthetic files."""
    json_files = sorted(DATA_DIR.glob("*.json"))
    assert len(json_files) >= 8, f"Expected at least 8 synthetic JSON files, found {len(json_files)}"

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        meta = gt_data.get("_metadata", {})
        demographics = meta.get("synthetic_demographics", {})
        patient_name = gt_data.get("patient", {}).get("name")
        mrn = demographics.get("mrn")
        phone = demographics.get("phone")
        email = demographics.get("email")

        # Read text from companion PDF
        pdf_file = json_file.with_suffix(".pdf")
        assert pdf_file.exists(), f"Companion PDF not found: {pdf_file}"

        from backend.app.ingestion.parser import parse_pdf_pypdf
        parsed_doc = parse_pdf_pypdf(pdf_file, filename=pdf_file.name)
        raw_text = "\n\n".join(item.text for item in parsed_doc.items if item.text)

        # Raw text should contain the unmasked synthetic values
        normalized_raw = " ".join(raw_text.split())
        assert patient_name in normalized_raw, f"Patient name '{patient_name}' should be in raw PDF text"
        assert mrn in raw_text, f"MRN '{mrn}' should be in raw PDF text"
        assert phone in raw_text, f"Phone '{phone}' should be in raw PDF text"
        assert email in raw_text, f"Email '{email}' should be in raw PDF text"

        # Apply PII masking
        result = mask_pii(raw_text)
        masked_text = result.masked_text
        counts = result.pii_counts

        # Assert NO fake PII values leaked into masked text
        assert patient_name not in masked_text, f"LEAK: Patient name '{patient_name}' leaked in {json_file.name}"
        for part in patient_name.split():
            if len(part) >= 3:
                assert part not in masked_text, f"LEAK: Patient name component '{part}' leaked in {json_file.name}"
        assert mrn not in masked_text, f"LEAK: MRN '{mrn}' leaked in {json_file.name}"
        assert phone not in masked_text, f"LEAK: Phone '{phone}' leaked in {json_file.name}"
        assert email not in masked_text, f"LEAK: Email '{email}' leaked in {json_file.name}"

        # Assert counts per PII type
        assert counts.get("NAME", 0) >= 1, f"Expected at least 1 NAME masked in {json_file.name}"
        assert counts.get("PHONE", 0) >= 1, f"Expected at least 1 PHONE masked in {json_file.name}"
        assert counts.get("EMAIL", 0) >= 1, f"Expected at least 1 EMAIL masked in {json_file.name}"
        assert counts.get("MRN", 0) >= 1, f"Expected at least 1 MRN masked in {json_file.name}"
        assert result.total_masked >= 4


def test_masker_preserves_clinical_values():
    """Assert ages, dates, diagnoses, medication names and doses are NOT masked."""
    clinical_text = """
    Patient Name: Arthur Pendelton
    MRN: MRN-2026-89102
    Age / Sex: 67 yrs / M
    Admission Date: 2026-01-10
    Discharge Date: 2026-01-15
    Contact: 555-014-9821
    Patient Email: arthur.p.synth@example-hospital.org
    PRIMARY & SECONDARY DIAGNOSES
      Acute Non-ST Elevation Myocardial Infarction (NSTEMI)
      Essential Primary Hypertension
    DISCHARGE MEDICATIONS & REGIMEN
      Aspirin 81 mg Daily orally
      Metoprolol Succinate 50 mg Daily orally
    """
    result = mask_pii(clinical_text)
    masked = result.masked_text

    # Preserved clinical fields
    assert "67 yrs" in masked
    assert "2026-01-10" in masked
    assert "2026-01-15" in masked
    assert "Acute Non-ST Elevation Myocardial Infarction (NSTEMI)" in masked
    assert "Essential Primary Hypertension" in masked
    assert "Aspirin" in masked
    assert "81" in masked
    assert "mg" in masked
    assert "Metoprolol Succinate" in masked
    assert "50" in masked

    # Redacted PII fields
    assert "Arthur Pendelton" not in masked
    assert "MRN-2026-89102" not in masked
    assert "555-014-9821" not in masked
    assert "arthur.p.synth@example-hospital.org" not in masked


# ==============================================================================
# 2. Mocked LLM Prompt PII Leakage Test
# ==============================================================================

def test_mocked_llm_receives_no_pii():
    """Assert the prompt text received by the LLM contains no fake name, MRN, phone or email."""
    json_path = DATA_DIR / "discharge_summary_01_cardiac.json"
    pdf_path = DATA_DIR / "discharge_summary_01_cardiac.pdf"
    with open(json_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    meta = gt_data["_metadata"]["synthetic_demographics"]
    patient_name = gt_data["patient"]["name"]
    mrn = meta["mrn"]
    phone = meta["phone"]
    email = meta["email"]

    expected_extraction = ClinicalExtraction.model_validate(gt_data)
    mock_adapter = MockLLMAdapter(return_extraction=expected_extraction)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res = extract_clinical_document(
        source=pdf_bytes,
        filename=pdf_path.name,
        llm_adapter=mock_adapter,
    )

    assert len(mock_adapter.received_prompts) == 1
    llm_received_text = mock_adapter.received_prompts[0]

    # Verify zero PII leakage into prompt
    assert patient_name not in llm_received_text, f"Prompt leaked patient name: {patient_name}"
    assert mrn not in llm_received_text, f"Prompt leaked MRN: {mrn}"
    assert phone not in llm_received_text, f"Prompt leaked phone: {phone}"
    assert email not in llm_received_text, f"Prompt leaked email: {email}"

    # Verify tokens exist in prompt
    assert "[NAME]" in llm_received_text
    assert "[MRN]" in llm_received_text
    assert "[PHONE]" in llm_received_text
    assert "[EMAIL]" in llm_received_text

    # Verify prompt version
    assert res.prompt_version == PROMPT_VERSION


# ==============================================================================
# 3. Validator Tests (All 4 error files and clean files)
# ==============================================================================

def test_validator_clean_and_error_files():
    """Assert all 4 error files produce exact expected issues, and clean files produce none."""
    json_files = sorted(DATA_DIR.glob("*.json"))
    assert len(json_files) >= 8

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("_metadata", {})
        has_errors = meta.get("has_deliberate_errors", False)
        expected_issues = meta.get("expected_validation_issues", [])

        issues = validate_extraction(data)
        actual_issues = [issue.model_dump() for issue in issues]

        if not has_errors:
            assert len(actual_issues) == 0, f"Clean file {json_file.name} produced unexpected issues: {actual_issues}"
        else:
            assert actual_issues == expected_issues, (
                f"Mismatch in {json_file.name}:\nActual:   {actual_issues}\nExpected: {expected_issues}"
            )


def test_validator_specific_rules():
    """Explicit unit checks for all 4 validation rules."""
    # 1. discharge_date before admission_date
    invalid_dates = {
        "patient": {"name": "Test", "age": 45, "sex": "M"},
        "diagnosis": ["Hypertension"],
        "medications": [{"name": "Lisinopril", "dose": 10.0, "unit": "mg", "frequency": "Daily"}],
        "admission_date": "2026-03-10",
        "discharge_date": "2026-03-05",
        "summary": "Summary",
    }
    issues = validate_extraction(invalid_dates)
    assert any(i.rule == "discharge_date_before_admission" and i.field == "discharge_date" for i in issues)

    # 2. Medication missing unit
    missing_unit = {
        "patient": {"name": "Test", "age": 45, "sex": "M"},
        "diagnosis": ["Hypertension"],
        "medications": [{"name": "Gabapentin", "dose": 300.0, "unit": None, "frequency": "Daily"}],
        "admission_date": "2026-03-01",
        "discharge_date": "2026-03-05",
        "summary": "Summary",
    }
    issues = validate_extraction(missing_unit)
    assert any(i.rule == "medication_missing_unit" and i.field == "medications[0].unit" for i in issues)

    # 3. Medication missing dose
    missing_dose = {
        "patient": {"name": "Test", "age": 45, "sex": "M"},
        "diagnosis": ["Hypertension"],
        "medications": [{"name": "Aspirin", "dose": None, "unit": "mg", "frequency": "Daily"}],
        "admission_date": "2026-03-01",
        "discharge_date": "2026-03-05",
        "summary": "Summary",
    }
    issues = validate_extraction(missing_dose)
    assert any(i.rule == "medication_missing_dose" and i.field == "medications[0].dose" for i in issues)

    # 4. Empty diagnosis list
    empty_diag = {
        "patient": {"name": "Test", "age": 45, "sex": "M"},
        "diagnosis": [],
        "medications": [{"name": "Aspirin", "dose": 81.0, "unit": "mg", "frequency": "Daily"}],
        "admission_date": "2026-03-01",
        "discharge_date": "2026-03-05",
        "summary": "Summary",
    }
    issues = validate_extraction(empty_diag)
    assert any(i.rule == "diagnosis_empty" and i.field == "diagnosis" for i in issues)

    # 5. Age out of range (age: 142)
    out_of_range_age = {
        "patient": {"name": "Test", "age": 142, "sex": "F"},
        "diagnosis": ["Anemia"],
        "medications": [{"name": "Iron", "dose": 324.0, "unit": "mg", "frequency": "Daily"}],
        "admission_date": "2026-03-01",
        "discharge_date": "2026-03-05",
        "summary": "Summary",
    }
    issues = validate_extraction(out_of_range_age)
    assert any(i.rule == "age_between_0_and_120" and i.field == "patient.age" for i in issues)


# ==============================================================================
# 4. Extraction Endpoint and Database Persistence Test
# ==============================================================================

@patch("backend.app.extraction.extractor.get_llm_adapter")
def test_extract_endpoint_and_database_persistence(mock_get_adapter, db: Session):
    """Assert POST /extract returns validated extraction and persists rows to extractions & validation_issues."""
    json_path = DATA_DIR / "discharge_summary_01_cardiac.json"
    pdf_path = DATA_DIR / "discharge_summary_01_cardiac.pdf"
    with open(json_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    expected_extraction = ClinicalExtraction.model_validate(gt_data)
    mock_adapter = MockLLMAdapter(return_extraction=expected_extraction)
    mock_get_adapter.return_value = mock_adapter

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/extract",
        files={"file": (pdf_path.name, file_bytes, "application/pdf")},
    )
    assert response.status_code == 200, f"Extraction failed: {response.text}"
    body = response.json()

    # Assert response fields
    assert "extraction" in body
    assert body["prompt_version"] == PROMPT_VERSION
    assert body["llm_model"] == "mock-gemini-extraction"
    assert body["pii_items_masked"] >= 4
    assert body["latency_ms"] > 0
    assert body["validation_issues"] == []

    # Check patient name in extracted body
    assert body["extraction"]["patient"]["name"] == "Arthur Pendelton"

    # Verify rows in database
    doc = db.query(Document).filter(Document.filename == pdf_path.name).first()
    assert doc is not None, f"Document record for {pdf_path.name} not found"

    extraction_row = db.query(Extraction).filter(Extraction.document_id == doc.id).order_by(Extraction.created_at.desc()).first()
    assert extraction_row is not None, "Extraction row was not saved in extractions table"
    assert extraction_row.prompt_version == PROMPT_VERSION
    assert extraction_row.model == "mock-gemini-extraction"
    assert extraction_row.json_result["patient"]["name"] == "Arthur Pendelton"
    assert len(extraction_row.json_result["medications"]) == 4

    # Validate issues table count for this clean extraction
    issues_rows = db.query(ValidationIssue).filter(ValidationIssue.extraction_id == extraction_row.id).all()
    assert len(issues_rows) == 0


@patch("backend.app.extraction.extractor.get_llm_adapter")
def test_extract_endpoint_persists_validation_issues(mock_get_adapter, db: Session):
    """Assert POST /extract persists deliberate validation issues to validation_issues table."""
    json_path = DATA_DIR / "discharge_summary_04_error_dates.json"
    pdf_path = DATA_DIR / "discharge_summary_04_error_dates.pdf"
    with open(json_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    expected_extraction = ClinicalExtraction.model_validate(gt_data)
    mock_adapter = MockLLMAdapter(return_extraction=expected_extraction)
    mock_get_adapter.return_value = mock_adapter

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/extract",
        files={"file": (pdf_path.name, file_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()

    assert len(body["validation_issues"]) == 1
    assert body["validation_issues"][0]["rule"] == "discharge_date_before_admission"

    doc = db.query(Document).filter(Document.filename == pdf_path.name).first()
    assert doc is not None

    extraction_row = db.query(Extraction).filter(Extraction.document_id == doc.id).order_by(Extraction.created_at.desc()).first()
    assert extraction_row is not None

    issues_rows = db.query(ValidationIssue).filter(ValidationIssue.extraction_id == extraction_row.id).all()
    assert len(issues_rows) == 1
    assert issues_rows[0].rule == "discharge_date_before_admission"
    assert issues_rows[0].field == "discharge_date"


def test_validate_endpoint():
    """Assert POST /validate returns validation issues for supplied extracted JSON."""
    clean_payload = {
        "patient": {"name": "Jane Doe", "age": 42, "sex": "F"},
        "diagnosis": ["Hypertension"],
        "medications": [{"name": "Amlodipine", "dose": 5.0, "unit": "mg", "frequency": "Daily"}],
        "admission_date": "2026-02-01",
        "discharge_date": "2026-02-05",
        "summary": "Routine admission and discharge.",
    }
    res_clean = client.post("/validate", json=clean_payload)
    assert res_clean.status_code == 200
    assert res_clean.json() == []

    error_payload = {
        "patient": {"name": "John Doe", "age": 150, "sex": "M"},
        "diagnosis": [],
        "medications": [{"name": "Metformin", "dose": None, "unit": None, "frequency": "Daily"}],
        "admission_date": "2026-03-10",
        "discharge_date": "2026-03-01",
        "summary": "Multiple deliberate errors.",
    }
    res_error = client.post("/validate", json=error_payload)
    assert res_error.status_code == 200
    issues = res_error.json()
    rule_names = {i["rule"] for i in issues}
    assert "age_between_0_and_120" in rule_names
    assert "discharge_date_before_admission" in rule_names
    assert "diagnosis_empty" in rule_names
    assert "medication_missing_dose" in rule_names
    assert "medication_missing_unit" in rule_names


# ==============================================================================
# 5. Audit Log Privacy Invariant Test
# ==============================================================================

def test_audit_log_never_contains_document_text(db: Session):
    """Assert no row in the audit_log table contains document text, prompts, or patient data."""
    # Record sample audit entries
    record_audit_log(db, endpoint="/ask", latency_ms=120.5, pii_items_masked=0, status="success")
    record_audit_log(db, endpoint="/extract", latency_ms=450.2, pii_items_masked=5, status="success")
    record_audit_log(db, endpoint="/validate", latency_ms=15.1, pii_items_masked=0, status="success")
    record_audit_log(db, endpoint="/ingest", latency_ms=890.0, pii_items_masked=0, status="success")

    rows = db.query(AuditLog).all()
    assert len(rows) >= 4, "Expected at least 4 audit rows"

    # Allowed column names on the AuditLog model
    allowed_columns = {
        "id",
        "timestamp",
        "endpoint",
        "document_id",
        "pii_items_masked",
        "latency_ms",
        "status",
    }

    actual_columns = {col.name for col in AuditLog.__table__.columns}
    assert actual_columns == allowed_columns, (
        f"AuditLog table contains unauthorized columns! Found: {actual_columns - allowed_columns}"
    )

    # Inspect all records to ensure strictly metadata values
    for row in rows:
        assert row.endpoint in {"/ask", "/ingest", "/extract", "/validate"}
        assert isinstance(row.pii_items_masked, int)
        assert isinstance(row.latency_ms, float)
        assert row.status in {"success", "error"}

        # Confirm no text fields exist on the instance
        for col in actual_columns:
            val = getattr(row, col)
            if isinstance(val, str) and col not in {"id", "endpoint", "status"}:
                pytest.fail(f"Unexpected string value in audit column {col}: {val}")


# ==============================================================================
# 6. Schema Retry Test (Retries ONCE with error message on failure)
# ==============================================================================

def test_extractor_retries_once_on_schema_failure():
    """Assert extractor retries once with the error message in prompt when first attempt fails."""
    pdf_path = DATA_DIR / "discharge_summary_01_cardiac.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    expected_extraction = ClinicalExtraction(
        patient={"name": "Arthur Pendelton", "age": 67, "sex": "M"},
        diagnosis=["NSTEMI"],
        medications=[{"name": "Aspirin", "dose": 81.0, "unit": "mg", "frequency": "Daily"}],
        admission_date="2026-01-10",
        discharge_date="2026-01-15",
        summary="Cardiac recovery summary.",
    )

    class FailingThenSucceedingMockAdapter(BaseLLMAdapter):
        def __init__(self):
            self.attempts = 0
            self.prompts: List[str] = []

        def generate(self, prompt: str) -> str:
            return "{}"

        def generate_structured(self, prompt: str, schema: Any) -> Any:
            self.prompts.append(prompt)
            self.attempts += 1
            if self.attempts == 1:
                raise ValueError("Simulated schema formatting failure on attempt 1")
            return expected_extraction

        def get_model_name(self) -> str:
            return "mock-retry-adapter"

    adapter = FailingThenSucceedingMockAdapter()
    result = extract_clinical_document(
        source=pdf_bytes,
        filename=pdf_path.name,
        llm_adapter=adapter,
    )

    assert adapter.attempts == 2, f"Expected exactly 2 attempts (1 initial + 1 retry), got {adapter.attempts}"
    assert len(adapter.prompts) == 2
    # Verify retry prompt includes error context
    assert "Simulated schema formatting failure on attempt 1" in adapter.prompts[1]
    assert result.extraction.patient.name == "Arthur Pendelton"


# ==============================================================================
# 7. Endpoint File Validation
# ==============================================================================

def test_extract_endpoint_invalid_file_handling():
    """Assert POST /extract rejects non-PDF and empty files."""
    # 1. Non-pdf extension
    res = client.post("/extract", files={"file": ("test.txt", b"plain text", "text/plain")})
    assert res.status_code == 400
    assert "Invalid file format" in res.json()["detail"]

    # 2. Empty file
    res = client.post("/extract", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"]

    # 3. Invalid PDF signature
    res = client.post("/extract", files={"file": ("fake.pdf", b"not-a-real-pdf-content", "application/pdf")})
    assert res.status_code == 400
    assert "valid PDF signature" in res.json()["detail"]

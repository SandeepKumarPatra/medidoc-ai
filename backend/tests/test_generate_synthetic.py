"""Tests for the synthetic medical document generator (Phase 0)."""

import json
from pathlib import Path
import pypdf
import pytest

from data.generate_synthetic import (
    generate_all_synthetic_data,
    get_synthetic_reports_dataset,
)


def test_synthetic_reports_dataset_structure():
    """Verify that the reports dataset definition contains required fields and deliberate errors."""
    reports = get_synthetic_reports_dataset()
    assert len(reports) >= 5, "Must define at least 5 clinical reports"

    error_reports = [r for r in reports if len(r.get("deliberate_errors", [])) > 0]
    assert len(error_reports) >= 2, "Must include multiple reports with deliberate errors"

    # Verify coverage of all 4 validation rules in deliberate errors
    error_rules = {
        err["rule"]
        for r in error_reports
        for err in r.get("deliberate_errors", [])
    }
    assert "discharge_date_before_admission" in error_rules
    assert "medication_missing_unit" in error_rules
    assert "diagnosis_empty" in error_rules
    assert "age_between_0_and_120" in error_rules


def test_generate_all_synthetic_data(tmp_path: Path):
    """Test generating all synthetic documents into a test directory."""
    eval_dir = tmp_path / "eval"
    summary = generate_all_synthetic_data(output_dir=tmp_path / "generated", eval_dir=eval_dir)

    # 1. Check SOP count and verify 6 to 10 pages requirement
    assert len(summary["sops"]) == 12, "Expected 12 SOP PDFs"
    for sop_path_str in summary["sops"]:
        sop_file = Path(sop_path_str)
        assert sop_file.exists()
        assert sop_file.stat().st_size > 1000

        # Verify 6 to 10 pages requirement using pypdf
        reader = pypdf.PdfReader(str(sop_file))
        assert 6 <= len(reader.pages) <= 10, (
            f"SOP {sop_file.name} must have between 6 and 10 pages (found {len(reader.pages)})"
        )

    # 2. Check Clinical Reports and Ground-Truth JSON pairs
    assert len(summary["reports"]) >= 5, "Expected at least 5 clinical reports"
    assert len(summary["ground_truth_json"]) == len(summary["reports"])

    for rep_path_str in summary["reports"]:
        pdf_file = Path(rep_path_str)
        json_file = pdf_file.with_suffix(".json")
        assert pdf_file.exists()
        assert json_file.exists(), f"Ground-truth JSON missing for {pdf_file.name}"

        # Verify PDF is valid and readable
        reader = pypdf.PdfReader(str(pdf_file))
        assert len(reader.pages) >= 1

        # Verify ground truth JSON structure matching SPEC.md schema
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "patient" in data
        assert "name" in data["patient"]
        assert "age" in data["patient"]
        assert "sex" in data["patient"]
        assert "diagnosis" in data
        assert isinstance(data["diagnosis"], list)
        assert "medications" in data
        assert isinstance(data["medications"], list)
        assert "admission_date" in data
        assert "discharge_date" in data
        assert "summary" in data

    # 3. Total PDFs >= 20 (12 SOPs + 8 Clinical Reports)
    total_pdfs = len(summary["sops"]) + len(summary["reports"])
    assert total_pdfs >= 20, f"Expected 20+ PDFs, got {total_pdfs}"

    # 4. Check generated question file
    assert summary["sop_questions"] is not None
    assert Path(summary["sop_questions"]).exists()


def test_sop_questions_file_structure():
    """Verify data/eval/sop_questions.json structure, required fields, and coverage across all 12 SOPs."""
    questions_path = Path("data/eval/sop_questions.json")
    assert questions_path.exists(), f"Evaluation question file not found at {questions_path}"

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    assert isinstance(questions, list), "sop_questions.json must contain a JSON array"
    assert 36 <= len(questions) <= 50, f"Expected 36-50 questions (3-4 per SOP), got {len(questions)}"

    expected_sop_filenames = {
        "sop_infection_control.pdf",
        "sop_discharge_process.pdf",
        "sop_billing_financial.pdf",
        "sop_medication_safety.pdf",
        "sop_patient_consent.pdf",
        "sop_hand_hygiene.pdf",
        "sop_fall_prevention.pdf",
        "sop_blood_transfusion.pdf",
        "sop_emergency_code_response.pdf",
        "sop_patient_identification.pdf",
        "sop_biomedical_waste.pdf",
        "sop_pharmacy_storage.pdf",
    }

    doc_question_counts: dict[str, int] = {}
    required_keys = {"id", "question", "expected_doc", "expected_section", "expected_answer_snippet"}

    for idx, q in enumerate(questions):
        assert isinstance(q, dict), f"Question at index {idx} must be a dictionary"
        missing_keys = required_keys - set(q.keys())
        assert not missing_keys, f"Question {q.get('id', idx)} missing fields: {missing_keys}"

        # Verify field types and content
        assert isinstance(q["id"], str) and q["id"].strip(), f"Invalid id in item {idx}"
        assert isinstance(q["question"], str) and len(q["question"].strip()) > 10, f"Question too short in {q['id']}"
        assert q["question"].strip().endswith("?"), f"Question should end with '?' in {q['id']}"
        assert isinstance(q["expected_doc"], str) and q["expected_doc"] in expected_sop_filenames, (
            f"Unexpected expected_doc '{q['expected_doc']}' in {q['id']}"
        )
        assert isinstance(q["expected_section"], str) and q["expected_section"].strip(), (
            f"Invalid expected_section in {q['id']}"
        )
        assert isinstance(q["expected_answer_snippet"], str) and q["expected_answer_snippet"].strip(), (
            f"Invalid expected_answer_snippet in {q['id']}"
        )

        doc = q["expected_doc"]
        doc_question_counts[doc] = doc_question_counts.get(doc, 0) + 1

    # Verify every SOP has 3 to 4 questions
    assert len(doc_question_counts) == 12, "All 12 SOPs must be represented in evaluation questions"
    for doc_name, count in doc_question_counts.items():
        assert 3 <= count <= 4, f"Document {doc_name} must have 3-4 questions, found {count}"


def test_deliberate_errors_ground_truth(tmp_path: Path):
    """Verify that the generated JSON files for deliberate error documents accurately flag the faults."""
    generate_all_synthetic_data(tmp_path)

    # Check date error
    date_err_json = tmp_path / "discharge_summary_04_error_dates.json"
    with open(date_err_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["discharge_date"] < data["admission_date"]
    assert data["_metadata"]["has_deliberate_errors"] is True

    # Check medication unit error
    med_err_json = tmp_path / "discharge_summary_05_error_med_unit.json"
    with open(med_err_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    units = [m["unit"] for m in data["medications"]]
    assert "" in units
    assert data["_metadata"]["has_deliberate_errors"] is True

    # Check empty diagnosis error
    diag_err_json = tmp_path / "discharge_summary_06_error_empty_diagnosis.json"
    with open(diag_err_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["diagnosis"]) == 0
    assert data["_metadata"]["has_deliberate_errors"] is True

    # Check age out of range error
    age_err_json = tmp_path / "lab_report_02_error_age.json"
    with open(age_err_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["patient"]["age"] > 120
    assert data["_metadata"]["has_deliberate_errors"] is True

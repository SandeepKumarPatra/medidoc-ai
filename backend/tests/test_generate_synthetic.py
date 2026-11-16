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
    summary = generate_all_synthetic_data(tmp_path)

    # 1. Check SOP count and verify multi-page requirement
    assert len(summary["sops"]) == 5, "Expected 5 SOP PDFs"
    for sop_path_str in summary["sops"]:
        sop_file = Path(sop_path_str)
        assert sop_file.exists()
        assert sop_file.stat().st_size > 1000

        # Verify multi-page requirement using pypdf
        reader = pypdf.PdfReader(str(sop_file))
        assert len(reader.pages) >= 2, f"SOP {sop_file.name} must be multi-page (found {len(reader.pages)})"

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

    # 3. Total PDFs >= 10 (SPEC.md Phase 0 completion condition)
    total_pdfs = len(summary["sops"]) + len(summary["reports"])
    assert total_pdfs >= 10, f"Expected 10+ PDFs, got {total_pdfs}"


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

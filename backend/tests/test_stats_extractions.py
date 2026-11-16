"""Tests for Phase 4 Statistics and Extractions endpoints.

Verifies:
1. GET /stats/overview accurately calculates aggregations matching database contents:
   - documents by doc_type
   - total parents and children
   - extractions_total and extractions_with_issues
   - issue_rate and issue counts per rule name
   - asks_total from audit_log
   - average latency_ms per endpoint
   - total PII items masked
2. GET /stats/audit supports limit and endpoint filtering, and computes daily call trends.
3. GET /extractions and GET /extractions/{id} return structured data and issue counts.
4. Privacy invariant: No stats or extractions endpoint returns raw document text or PII.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.models import AuditLog, Child, Document, Extraction, Parent, ValidationIssue
from backend.app.db.session import SessionLocal
from backend.app.main import app

client = TestClient(app)


def test_stats_overview_numbers_match_database(db: Session):
    """Assert GET /stats/overview computed metrics match ground-truth database rows."""
    # 1. Query database ground truth
    doc_type_rows = (
        db.query(Document.doc_type, func.count(Document.id))
        .group_by(Document.doc_type)
        .all()
    )
    expected_docs_by_type = {row[0]: int(row[1]) for row in doc_type_rows if row[0] is not None}
    expected_total_docs = sum(expected_docs_by_type.values())

    expected_parents = db.query(func.count(Parent.id)).scalar() or 0
    expected_children = db.query(func.count(Child.id)).scalar() or 0
    expected_extractions = db.query(func.count(Extraction.id)).scalar() or 0

    expected_with_issues = (
        db.query(func.count(func.distinct(ValidationIssue.extraction_id)))
        .filter(ValidationIssue.extraction_id.isnot(None))
        .scalar()
        or 0
    )
    expected_issue_rate = (
        round(expected_with_issues / expected_extractions, 4)
        if expected_extractions > 0
        else 0.0
    )

    rule_rows = (
        db.query(ValidationIssue.rule, func.count(ValidationIssue.id))
        .group_by(ValidationIssue.rule)
        .all()
    )
    expected_rules = {row[0]: int(row[1]) for row in rule_rows if row[0] is not None}

    expected_asks = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.endpoint == "/ask")
        .scalar()
        or 0
    )

    expected_total_pii = (
        db.query(func.coalesce(func.sum(AuditLog.pii_items_masked), 0)).scalar()
        or 0
    )

    latency_rows = (
        db.query(AuditLog.endpoint, func.avg(AuditLog.latency_ms))
        .group_by(AuditLog.endpoint)
        .all()
    )
    expected_avg_latencies = {
        row[0]: round(float(row[1]), 2)
        for row in latency_rows
        if row[0] is not None and row[1] is not None
    }

    # 2. Invoke endpoint
    response = client.get("/stats/overview")
    assert response.status_code == 200, f"GET /stats/overview failed: {response.text}"
    data = response.json()

    # 3. Assert exact matches
    assert data["documents_by_type"] == expected_docs_by_type
    assert data["total_documents"] == expected_total_docs
    assert data["parents_total"] == expected_parents
    assert data["children_total"] == expected_children
    assert data["extractions_total"] == expected_extractions
    assert data["extractions_with_issues"] == expected_with_issues
    assert data["issue_rate"] == expected_issue_rate
    assert data["issue_counts_by_rule"] == expected_rules
    assert data["asks_total"] == expected_asks
    assert data["total_pii_masked"] == expected_total_pii
    assert data["avg_latency_ms_by_endpoint"] == expected_avg_latencies


def test_stats_audit_endpoint():
    """Assert GET /stats/audit returns recent records, totals, and daily breakdown."""
    # 1. Unfiltered query with limit
    res = client.get("/stats/audit?limit=10")
    assert res.status_code == 200
    data = res.json()

    assert "recent_logs" in data
    assert "totals_by_endpoint" in data
    assert "calls_by_day" in data
    assert "total_count" in data

    assert len(data["recent_logs"]) <= 10
    if len(data["recent_logs"]) >= 2:
        # Verify newest first sorting
        t0 = data["recent_logs"][0]["timestamp"]
        t1 = data["recent_logs"][1]["timestamp"]
        assert t0 >= t1

    # Verify each recent log contains strictly metadata
    for log in data["recent_logs"]:
        assert "id" in log
        assert "timestamp" in log
        assert "endpoint" in log
        assert "pii_items_masked" in log
        assert "latency_ms" in log
        assert "status" in log
        # Invariant: No text/prompt/patient columns
        assert "text" not in log
        assert "prompt" not in log
        assert "patient" not in log

    # 2. Endpoint-filtered query
    res_filtered = client.get("/stats/audit?limit=20&endpoint=/ask")
    assert res_filtered.status_code == 200
    filtered_data = res_filtered.json()
    for log in filtered_data["recent_logs"]:
        assert log["endpoint"] == "/ask"
    for day in filtered_data["calls_by_day"]:
        assert day["endpoint"] == "/ask"


def test_extractions_list_and_detail_endpoints(db: Session):
    """Assert GET /extractions lists items and GET /extractions/{id} retrieves structured JSON."""
    # Ensure at least one extraction exists in test database
    if db.query(Extraction).count() == 0:
        doc = Document(
            filename="discharge_summary_sample.pdf",
            doc_type="discharge",
            status="extracted",
            page_count=1,
        )
        db.add(doc)
        db.flush()
        ext = Extraction(
            document_id=doc.id,
            json_result={
                "patient": {"name": "Test Patient", "age": 55, "sex": "M"},
                "diagnosis": ["Hypertension"],
                "medications": [{"name": "Lisinopril", "dose": 10.0, "unit": "mg", "frequency": "Daily"}],
                "admission_date": "2026-01-01",
                "discharge_date": "2026-01-05",
                "summary": "Sample summary.",
            },
            model="mock-model",
            prompt_version="extract-v1.1",
        )
        db.add(ext)
        db.flush()
        issue = ValidationIssue(
            extraction_id=ext.id,
            field="patient.name",
            rule="sample_rule",
            severity="warning",
            message="Sample warning",
        )
        db.add(issue)
        db.commit()

    # 1. List extractions
    res = client.get("/extractions?limit=5")
    assert res.status_code == 200
    extractions = res.json()
    assert isinstance(extractions, list)
    assert len(extractions) > 0

    item = extractions[0]
    assert "id" in item
    assert "document_id" in item
    assert "filename" in item
    assert "doc_type" in item
    assert "created_at" in item
    assert "issue_count" in item
    assert "model" in item
    assert "prompt_version" in item
    # Invariant: No document text in list
    assert "text" not in item
    assert "json_result" not in item

    # 2. Fetch specific detail
    ext_id = item["id"]
    detail_res = client.get(f"/extractions/{ext_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert detail["id"] == ext_id
    assert detail["filename"] == item["filename"]
    assert "json_result" in detail
    assert isinstance(detail["json_result"], dict)
    assert "patient" in detail["json_result"]
    assert "diagnosis" in detail["json_result"]
    assert "medications" in detail["json_result"]
    assert "validation_issues" in detail
    assert isinstance(detail["validation_issues"], list)
    assert len(detail["validation_issues"]) == item["issue_count"]

    # 3. Non-existent UUID returns 404
    non_existent = str(uuid.uuid4())
    res_404 = client.get(f"/extractions/{non_existent}")
    assert res_404.status_code == 404

    # 4. Invalid UUID format returns 404
    res_invalid = client.get("/extractions/not-a-valid-uuid")
    assert res_invalid.status_code == 404


def test_no_endpoint_returns_raw_document_text():
    """Verify strictly enforced privacy invariant across all stats and extractions endpoints."""
    # Ensure known raw PDF text snippets never appear in metadata responses
    banned_clinical_phrases = [
        "Chief Complaint",
        "Physical Examination",
        "Hospital Course",
        "Assessment and Plan",
        "Discharged in stable condition",
        "Normal sinus rhythm",
    ]

    # 1. GET /stats/overview
    overview_text = client.get("/stats/overview").text
    for phrase in banned_clinical_phrases:
        assert phrase not in overview_text, f"Raw text leaked in /stats/overview: {phrase}"

    # 2. GET /stats/audit
    audit_text = client.get("/stats/audit?limit=100").text
    for phrase in banned_clinical_phrases:
        assert phrase not in audit_text, f"Raw text leaked in /stats/audit: {phrase}"

    # 3. GET /extractions
    extractions_text = client.get("/extractions?limit=50").text
    for phrase in banned_clinical_phrases:
        assert phrase not in extractions_text, f"Raw text leaked in /extractions: {phrase}"

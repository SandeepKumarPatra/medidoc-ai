#!/usr/bin/env python3
"""MediDoc AI - Demo Data Seeding Script.

Seeds the running API with realistic demonstration data:
1. Ingests all generated hospital SOP policies (doc_type='sop').
2. Extracts structured clinical JSON from all generated discharge summaries and lab reports.
3. Submits 10 policy queries across all 4 retrieval modes (naive, parent_child, hybrid, hybrid_rerank).
4. Prints an aggregated operational summary and stops cleanly on any API error.

Usage:
    python scripts/seed_demo_data.py [--api-url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed a running MediDoc AI instance with SOPs, extractions, and queries."
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="Base URL of the running MediDoc AI FastAPI backend (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to generated synthetic PDF directory (default: repo data/generated)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-request HTTP timeout in seconds (default: 120s)",
    )
    return parser.parse_args()


def check_api_health(client: httpx.Client, base_url: str) -> None:
    """Verify backend API and database connectivity before starting seed pipeline."""
    health_url = f"{base_url.rstrip('/')}/health"
    print(f"\n[1/4] Checking API health at {health_url}...")
    try:
        response = client.get(health_url)
        if response.status_code != 200:
            print(f"[ERROR] API returned unhealthy status {response.status_code}: {response.text}")
            sys.exit(1)
        data = response.json()
        print(f"      API Status: {data.get('status')} | Database: {data.get('database')} | Env: {data.get('app_env')}")
    except httpx.ConnectError:
        print(f"\n[ERROR] Could not connect to MediDoc AI backend at {base_url}.")
        print("        Ensure the server is running with:")
        print("          uvicorn backend.app.main:app --reload")
        print("        or:")
        print("          docker compose up -d\n")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Unexpected error connecting to API: {exc}")
        sys.exit(1)


def ingest_sops(client: httpx.Client, base_url: str, data_dir: Path) -> Dict[str, Any]:
    """Ingest all policy SOP documents into pgvector and full-text search (idempotent)."""
    sop_files = sorted(data_dir.glob("sop_*.pdf"))
    if not sop_files:
        print(f"[WARNING] No sop_*.pdf files found in {data_dir}. Run data/generate_synthetic.py first.")
        return {"count": 0, "parent_chunks": 0, "child_chunks": 0}

    print(f"\n[2/4] Ingesting {len(sop_files)} SOP documents (doc_type=sop)...")
    ingest_url = f"{base_url.rstrip('/')}/ingest"
    docs_url = f"{base_url.rstrip('/')}/documents"

    # Query already indexed documents for idempotency
    existing_docs_res = client.get(docs_url)
    existing_map: Dict[str, Dict[str, Any]] = {}
    if existing_docs_res.status_code == 200:
        for doc in existing_docs_res.json():
            if doc.get("status") in ("completed", "indexed") and doc.get("filename"):
                existing_map[doc["filename"]] = doc

    total_parents = 0
    total_children = 0
    success_count = 0

    for idx, pdf_path in enumerate(sop_files, 1):
        if pdf_path.name in existing_map:
            doc_data = existing_map[pdf_path.name]
            p_chunks = doc_data.get("parent_count", 0)
            c_chunks = doc_data.get("child_count", 0)
            total_parents += p_chunks
            total_children += c_chunks
            success_count += 1
            print(f"      [{idx:02d}/{len(sop_files):02d}] {pdf_path.name:<32} -> [ALREADY INDEXED] {p_chunks:2d} parents, {c_chunks:2d} children")
            continue

        t0 = time.perf_counter()
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                data = {"doc_type": "sop"}
                res = client.post(ingest_url, files=files, data=data)

            if res.status_code not in (200, 201):
                print(f"[ERROR] Failed to ingest {pdf_path.name} (HTTP {res.status_code}): {res.text}")
                sys.exit(1)

            result = res.json()
            p_chunks = result.get("parent_chunks", 0)
            c_chunks = result.get("child_chunks", 0)
            total_parents += p_chunks
            total_children += c_chunks
            success_count += 1
            dt = (time.perf_counter() - t0) * 1000.0

            print(f"      [{idx:02d}/{len(sop_files):02d}] {pdf_path.name:<32} -> {p_chunks:2d} parents, {c_chunks:2d} children ({dt:.0f} ms)")
        except Exception as exc:
            print(f"[ERROR] Exception during ingestion of {pdf_path.name}: {exc}")
            sys.exit(1)

    return {
        "count": success_count,
        "parent_chunks": total_parents,
        "child_chunks": total_children,
    }


def extract_clinical_reports(client: httpx.Client, base_url: str, data_dir: Path) -> Dict[str, Any]:
    """Upload and extract structured clinical data from all discharge summaries and lab reports (idempotent)."""
    report_files = sorted(
        list(data_dir.glob("discharge_summary_*.pdf")) + list(data_dir.glob("lab_report_*.pdf"))
    )

    if not report_files:
        print(f"[WARNING] No clinical report PDFs found in {data_dir}.")
        return {"count": 0, "issues": 0, "pii_masked": 0, "comparisons": []}

    print(f"\n[3/4] Extracting structured data from {len(report_files)} clinical reports...")
    extract_url = f"{base_url.rstrip('/')}/extract"
    extractions_url = f"{base_url.rstrip('/')}/extractions?limit=100"

    # Query already stored extractions for idempotency
    existing_ext_res = client.get(extractions_url)
    existing_ext_map: Dict[str, Dict[str, Any]] = {}
    if existing_ext_res.status_code == 200:
        for ext in existing_ext_res.json():
            if ext.get("filename"):
                existing_ext_map[ext["filename"]] = ext

    success_count = 0
    total_issues = 0
    total_pii_masked = 0
    comparisons: List[Dict[str, Any]] = []

    for idx, pdf_path in enumerate(report_files, 1):
        issues: List[Dict[str, Any]] = []
        pii_count = 0
        is_cached = False

        if pdf_path.name in existing_ext_map:
            ext_meta = existing_ext_map[pdf_path.name]
            ext_id = ext_meta["id"]
            detail_res = client.get(f"{base_url.rstrip('/')}/extractions/{ext_id}")
            if detail_res.status_code == 200:
                detail_data = detail_res.json()
                issues = detail_data.get("validation_issues", [])
                is_cached = True
                print(f"      [{idx:02d}/{len(report_files):02d}] {pdf_path.name:<40} -> [ALREADY EXTRACTED] {len(issues)} issues")

        if not is_cached:
            t0 = time.perf_counter()
            try:
                with open(pdf_path, "rb") as f:
                    files = {"file": (pdf_path.name, f, "application/pdf")}
                    res = client.post(extract_url, files=files)

                if res.status_code != 200:
                    print(f"[ERROR] Failed to extract {pdf_path.name} (HTTP {res.status_code}): {res.text}")
                    sys.exit(1)

                result = res.json()
                issues = result.get("validation_issues", [])
                pii_count = result.get("pii_items_masked", 0)
                dt = (time.perf_counter() - t0) * 1000.0

                issue_str = f"{len(issues)} issues" if issues else "clean"
                print(f"      [{idx:02d}/{len(report_files):02d}] {pdf_path.name:<40} -> {issue_str}, {pii_count} PII masked ({dt:.0f} ms)")
            except Exception as exc:
                print(f"[ERROR] Exception during extraction of {pdf_path.name}: {exc}")
                sys.exit(1)

        total_issues += len(issues)
        total_pii_masked += pii_count
        success_count += 1

        # Compare triggered validation rules against ground-truth JSON
        json_path = data_dir / f"{pdf_path.stem}.json"
        expected_rules: List[str] = []
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    gt_data = json.load(f)
                exp_issues = gt_data.get("_metadata", {}).get("expected_validation_issues", [])
                expected_rules = sorted([i.get("rule") for i in exp_issues if "rule" in i])
            except Exception as exc:
                print(f"[WARNING] Could not read ground truth for {json_path.name}: {exc}")

        triggered_rules = sorted([
            i.get("rule") for i in issues if isinstance(i, dict) and "rule" in i
        ])
        match = (expected_rules == triggered_rules)

        comparisons.append({
            "filename": pdf_path.name,
            "triggered_rules": triggered_rules,
            "expected_rules": expected_rules,
            "match": match,
        })

    # Print Per-Report Validation Comparison Table
    print("\n" + "=" * 100)
    print(" CLINICAL EXTRACTION VALIDATION COMPARISON TABLE")
    print("=" * 100)
    print(f" {'Report Filename':<40} | {'Triggered Rules':<26} | {'Expected Rules':<26} | Status")
    print("-" * 100)
    for comp in comparisons:
        trig_str = ", ".join(comp["triggered_rules"]) if comp["triggered_rules"] else "none (clean)"
        exp_str = ", ".join(comp["expected_rules"]) if comp["expected_rules"] else "none (clean)"
        status_str = "MATCH (PASS)" if comp["match"] else "MISMATCH (FAIL)"
        print(f" {comp['filename']:<40} | {trig_str:<26} | {exp_str:<26} | {status_str}")
    print("=" * 100)

    return {
        "count": success_count,
        "issues": total_issues,
        "pii_masked": total_pii_masked,
        "comparisons": comparisons,
    }


def ask_sample_questions(client: httpx.Client, base_url: str, repo_root: Path) -> List[Dict[str, Any]]:
    """Ask 10 sample policy questions cycling through all 4 retrieval modes."""
    questions_file = repo_root / "data" / "eval" / "sop_questions.json"
    sample_questions: List[str] = []

    if questions_file.exists():
        try:
            with open(questions_file, "r", encoding="utf-8") as f:
                q_data = json.load(f)
                sample_questions = [item["question"] for item in q_data[:10]]
        except Exception as exc:
            print(f"[WARNING] Could not load questions from {questions_file}: {exc}")

    # Fallback curated questions if questions file is missing or short
    if len(sample_questions) < 10:
        sample_questions = [
            "What is the minimum air exchange rate for an airborne isolation room?",
            "What is the daily cutoff time for inpatient discharge departures?",
            "What disinfectant contact time is required for bleach during terminal cleaning?",
            "What are the mandatory clinical checks required before administering blood transfusions?",
            "What color container is designated for cytotoxic waste disposal?",
            "How frequently must patient fall risk reassessments be conducted?",
            "What is the required hand hygiene scrub duration using chlorhexidine?",
            "What temperature range must be maintained for refrigerated pharmacy storage?",
            "Within what timeframe must an EMR discharge summary be finalized by the attending physician?",
            "What emergency response code designates an adult cardiopulmonary arrest?",
        ]

    modes = ["naive", "parent_child", "hybrid", "hybrid_rerank"]
    print(f"\n[4/4] Submitting 10 sample policy queries across 4 retrieval modes...")
    ask_url = f"{base_url.rstrip('/')}/ask"
    results: List[Dict[str, Any]] = []

    for idx, question in enumerate(sample_questions[:10], 1):
        mode = modes[(idx - 1) % len(modes)]
        t0 = time.perf_counter()
        payload = {
            "question": question,
            "mode": mode,
            "top_k": 3,
        }

        max_retries = 2
        res = None
        for attempt in range(max_retries):
            try:
                res = client.post(ask_url, json=payload)
                if res.status_code == 200:
                    break
                if res.status_code == 504 and attempt < max_retries - 1:
                    print(f"      [RETRY] /ask timed out for '{question[:40]}...', retrying in 3s...")
                    time.sleep(3)
                    continue
                print(f"[ERROR] /ask query failed (HTTP {res.status_code}) for '{question}': {res.text}")
                sys.exit(1)
            except Exception as exc:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                print(f"[ERROR] Exception during /ask for '{question}': {exc}")
                sys.exit(1)

        data = res.json()
        dt = (time.perf_counter() - t0) * 1000.0
        sources_count = len(data.get("sources", []))
        answer_preview = (data.get("answer") or "").replace("\n", " ")[:60]
        print(f"      [{idx:02d}/10] Mode: {mode:<14} | {sources_count} sources | {dt:.0f} ms")
        print(f"             Q: {question}")
        print(f"             A: {answer_preview}...")

        results.append({
            "question": question,
            "mode": mode,
            "sources_count": sources_count,
            "latency_ms": dt,
        })

    return results


def main() -> None:
    """Execute complete demo data seeding lifecycle."""
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent

    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = repo_root / "data" / "generated"

    if not data_dir.exists():
        print(f"[ERROR] Data directory not found: {data_dir}")
        print("        Generate synthetic documents first using: python data/generate_synthetic.py")
        sys.exit(1)

    print("=" * 70)
    print(" MediDoc AI - Demo Data Seeder")
    print(f" Target API: {args.api_url}")
    print(f" Data Dir:   {data_dir}")
    print("=" * 70)

    start_time = time.perf_counter()

    with httpx.Client(base_url=args.api_url, timeout=args.timeout) as client:
        # 1. Check API Health
        check_api_health(client, args.api_url)

        # 2. Ingest SOPs
        sop_summary = ingest_sops(client, args.api_url, data_dir)

        # 3. Extract Clinical Reports
        extract_summary = extract_clinical_reports(client, args.api_url, data_dir)

        # 4. Ask Sample Questions across all 4 modes
        qa_results = ask_sample_questions(client, args.api_url, repo_root)

    total_time = time.perf_counter() - start_time

    # Print Final Summary Table
    print("\n" + "=" * 70)
    print(" SEEDING COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f" - Total Ingested SOPs:      {sop_summary['count']}")
    print(f" - Indexed Parent Sections:  {sop_summary['parent_chunks']}")
    print(f" - Indexed Child Chunks:     {sop_summary['child_chunks']}")
    print(f" - Clinical Reports Extracted:{extract_summary['count']}")
    print(f" - Validation Issues Logged: {extract_summary['issues']}")
    print(f" - PII Tokens Masked:        {extract_summary['pii_masked']}")
    print(f" - Sample Questions Asked:   {len(qa_results)}")
    print(f" - Total Elapsed Time:       {total_time:.2f} seconds")
    print("-" * 70)
    print(" Verification Endpoints:")
    print(f"   Overview Stats: {args.api_url}/stats/overview")
    print(f"   Audit Log:      {args.api_url}/stats/audit?limit=20")
    print(f"   Extractions:    {args.api_url}/extractions?limit=10")
    print(f"   Swagger Docs:   {args.api_url}/docs")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

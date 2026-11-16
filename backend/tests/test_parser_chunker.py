"""Tests for PDF parser and hierarchical chunker modules."""

from pathlib import Path
from backend.app.ingestion.parser import parse_pdf_pypdf, parse_pdf
from backend.app.ingestion.chunker import build_parents, split_children


def test_pypdf_parsing():
    """Verify pypdf fallback parses synthetic SOP PDF."""
    pdf_path = Path("data/generated/sop_infection_control.pdf")
    assert pdf_path.exists(), "Sample SOP PDF should exist"

    doc = parse_pdf_pypdf(pdf_path, filename=pdf_path.name)
    assert doc.page_count == 2
    assert len(doc.items) >= 2
    assert all(item.page_no in (1, 2) for item in doc.items)


def test_chunker_parent_and_child_generation():
    """Verify parents (<= 1500 tokens) and children (~300 tokens) with valid page ranges."""
    pdf_path = Path("data/generated/sop_infection_control.pdf")
    doc = parse_pdf_pypdf(pdf_path, filename=pdf_path.name)

    parents = build_parents(doc, max_tokens=1500)
    assert len(parents) >= 1
    for p in parents:
        assert p.page_start >= 1
        assert p.page_end >= p.page_start
        assert len(p.text.strip()) > 0

    children = split_children(parents, chunk_size=300, chunk_overlap=50)
    assert len(children) >= len(parents)
    for c in children:
        assert c.page_start >= 1
        assert c.page_end >= c.page_start
        assert len(c.text.strip()) > 0
        assert c.parent_index < len(parents)

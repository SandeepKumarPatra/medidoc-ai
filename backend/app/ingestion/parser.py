"""PDF document parser supporting Docling with a robust pypdf fallback.

Extracts structured sections, headings, tables (as Markdown), and text content while
preserving page provenance metadata for every block.
"""

from __future__ import annotations

import io
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

from pypdf import PdfReader

logger = logging.getLogger(__name__)


@dataclass
class ParsedItem:
    """An individual structural element extracted from a document."""

    text: str
    item_type: str  # 'heading', 'paragraph', 'table', 'section'
    page_no: int
    level: int = 1
    title: Optional[str] = None


@dataclass
class ParsedDocument:
    """Structured representation of a parsed document."""

    filename: str
    page_count: int
    items: List[ParsedItem] = field(default_factory=list)


def parse_pdf_docling(
    source: Union[Path, str, bytes],
    filename: str = "document.pdf",
) -> ParsedDocument:
    """Parse a PDF document using Docling for high-fidelity layout and table extraction.

    Args:
        source: Path to PDF or raw bytes.
        filename: Original file name.

    Returns:
        ParsedDocument containing structural items with page numbers.
    """
    from docling.document_converter import DocumentConverter

    temp_path: Optional[str] = None
    if isinstance(source, bytes):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(source)
            temp_path = tmp.name
        pdf_path = Path(temp_path)
    else:
        pdf_path = Path(source)

    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = result.document

        items: List[ParsedItem] = []
        max_page = 1

        for item, level in doc.iterate_items():
            # Extract page provenance if available
            page_no = 1
            if hasattr(item, "prov") and item.prov:
                page_no = getattr(item.prov[0], "page_no", 1)
            if page_no > max_page:
                max_page = page_no

            item_cls = type(item).__name__
            text = ""

            if item_cls == "SectionHeaderItem":
                text = getattr(item, "text", "").strip()
                if text:
                    items.append(
                        ParsedItem(
                            text=text,
                            item_type="heading",
                            page_no=page_no,
                            level=level,
                            title=text,
                        )
                    )
            elif item_cls == "TableItem":
                try:
                    text = item.export_to_markdown(doc=doc).strip()
                except Exception:
                    text = getattr(item, "text", "").strip()
                if text:
                    items.append(
                        ParsedItem(
                            text=text,
                            item_type="table",
                            page_no=page_no,
                            level=level,
                        )
                    )
            else:
                text = getattr(item, "text", "").strip()
                if text:
                    items.append(
                        ParsedItem(
                            text=text,
                            item_type="paragraph",
                            page_no=page_no,
                            level=level,
                        )
                    )

        # Ensure page count considers doc.pages if available
        if hasattr(doc, "pages") and doc.pages:
            max_page = max(max_page, len(doc.pages))

        return ParsedDocument(
            filename=filename,
            page_count=max_page,
            items=items,
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def parse_pdf_pypdf(
    source: Union[Path, str, bytes],
    filename: str = "document.pdf",
) -> ParsedDocument:
    """Fallback parser extracting text page-by-page using pypdf.

    Args:
        source: Path to PDF or raw bytes.
        filename: Original file name.

    Returns:
        ParsedDocument containing structural items with page numbers.
    """
    if isinstance(source, bytes):
        stream = io.BytesIO(source)
    else:
        stream = open(source, "rb")

    try:
        reader = PdfReader(stream)
        items: List[ParsedItem] = []
        page_count = len(reader.pages)

        # Regex heuristic for section headings (e.g., '1.0 Purpose', 'SECTION 2', all caps short lines)
        heading_pattern = re.compile(
            r"^(?:\d+(?:\.\d+)*\s+[A-Za-z]|SECTION\s+\d+|[A-Z\s]{4,40}$)", re.MULTILINE
        )

        for page_idx, page in enumerate(reader.pages):
            page_no = page_idx + 1
            raw_text = page.extract_text() or ""
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

            for para in paragraphs:
                lines = para.split("\n")
                first_line = lines[0].strip()
                if len(lines) == 1 and heading_pattern.match(first_line):
                    items.append(
                        ParsedItem(
                            text=first_line,
                            item_type="heading",
                            page_no=page_no,
                            level=1,
                            title=first_line,
                        )
                    )
                else:
                    items.append(
                        ParsedItem(
                            text=para,
                            item_type="paragraph",
                            page_no=page_no,
                            level=1,
                        )
                    )

        return ParsedDocument(
            filename=filename,
            page_count=max(page_count, 1),
            items=items,
        )
    finally:
        if not isinstance(source, bytes) and hasattr(stream, "close"):
            stream.close()


def parse_pdf(
    source: Union[Path, str, bytes],
    filename: str = "document.pdf",
) -> ParsedDocument:
    """Parse a PDF with Docling, gracefully falling back to pypdf on error.

    Args:
        source: Path to PDF or raw bytes.
        filename: Original file name.

    Returns:
        ParsedDocument with extracted items and page metadata.
    """
    logger.info("Parsing PDF %s", filename)
    try:
        parsed = parse_pdf_docling(source, filename=filename)
        if parsed.items:
            logger.info("Successfully parsed %s via Docling (%d items, %d pages)", filename, len(parsed.items), parsed.page_count)
            return parsed
        logger.warning("Docling returned 0 items for %s, falling back to pypdf", filename)
    except Exception as exc:
        logger.warning("Docling parsing failed for %s (%s). Falling back to pypdf.", filename, exc)

    parsed = parse_pdf_pypdf(source, filename=filename)
    logger.info("Parsed %s via pypdf fallback (%d items, %d pages)", filename, len(parsed.items), parsed.page_count)
    return parsed

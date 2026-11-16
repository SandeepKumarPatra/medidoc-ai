"""Hierarchical document chunking module for MediDoc AI.

Constructs coarse-grained parent sections (<= ~1500 tokens) aligned to document headings
and splits each parent into sentence-aligned child chunks (~300 tokens, small overlap)
while preserving page provenance metadata (page_start, page_end) on all chunks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.app.config import get_settings
from backend.app.ingestion.parser import ParsedDocument, ParsedItem

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ParentChunk:
    """Coarse-grained parent section representing an entire policy or clinical section."""

    section_title: Optional[str]
    text: str
    page_start: int
    page_end: int
    section_type: Optional[str] = "section"


@dataclass
class ChildChunk:
    """Fine-grained retrieval chunk derived from a parent section."""

    text: str
    page_start: int
    page_end: int
    parent_index: int


def get_token_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    """Instantiate a sentence-aligned RecursiveCharacterTextSplitter using tiktoken cl100k_base."""
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""],
    )


def build_parents(
    parsed_doc: ParsedDocument,
    max_tokens: int | None = None,
) -> List[ParentChunk]:
    """Group parsed structural elements into parent chunks bounded by max_tokens.

    Respects natural document headings when present; if an individual section exceeds
    max_tokens, it is cleanly partitioned into sub-parents with continued titles.

    Args:
        parsed_doc: The parsed PDF document.
        max_tokens: Maximum tokens per parent chunk (defaults to config setting).

    Returns:
        List of ParentChunk objects with page ranges.
    """
    token_limit = max_tokens or settings.parent_chunk_size
    splitter = get_token_splitter(chunk_size=token_limit, chunk_overlap=100)

    parents: List[ParentChunk] = []

    # Intermediate section accumulator
    current_title: Optional[str] = None
    current_items: List[ParsedItem] = []

    def flush_section():
        nonlocal current_title, current_items
        if not current_items:
            return

        combined_text = "\n\n".join(item.text for item in current_items if item.text.strip())
        if not combined_text.strip():
            current_items = []
            return

        min_page = min(item.page_no for item in current_items)
        max_page = max(item.page_no for item in current_items)
        section_type = "table" if (len(current_items) == 1 and current_items[0].item_type == "table") else "section"

        # Check token length
        sub_chunks = splitter.split_text(combined_text)
        if len(sub_chunks) <= 1:
            parents.append(
                ParentChunk(
                    section_title=current_title,
                    text=combined_text,
                    page_start=min_page,
                    page_end=max_page,
                    section_type=section_type,
                )
            )
        else:
            for idx, part in enumerate(sub_chunks):
                title_suffix = f" (Part {idx + 1})" if current_title else None
                sub_title = f"{current_title}{title_suffix}" if current_title else None
                parents.append(
                    ParentChunk(
                        section_title=sub_title,
                        text=part,
                        page_start=min_page,
                        page_end=max_page,
                        section_type=section_type,
                    )
                )

        current_items = []

    for item in parsed_doc.items:
        if item.item_type == "heading":
            # New heading triggers flushing the current accumulated section
            flush_section()
            current_title = item.text.strip()
            current_items.append(item)
        else:
            current_items.append(item)

    # Flush any remaining items
    flush_section()

    # Fallback if document had no items or headings produced no parents
    if not parents and parsed_doc.items:
        fallback_text = "\n\n".join(item.text for item in parsed_doc.items if item.text.strip())
        if fallback_text.strip():
            sub_chunks = splitter.split_text(fallback_text)
            for part in sub_chunks:
                parents.append(
                    ParentChunk(
                        section_title=None,
                        text=part,
                        page_start=1,
                        page_end=parsed_doc.page_count,
                        section_type="section",
                    )
                )

    logger.info("Built %d parent chunks from %s", len(parents), parsed_doc.filename)
    return parents


def split_children(
    parents: List[ParentChunk],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[ChildChunk]:
    """Split parent chunks into fine-grained child chunks for dense and sparse indexing.

    Chunks are sentence-aligned with a small overlap to ensure grammatical continuity.
    Page numbers are assigned based on the parent's page boundaries.

    Args:
        parents: List of ParentChunk objects.
        chunk_size: Target child chunk size in tokens (defaults to config).
        chunk_overlap: Target overlap in tokens (defaults to config).

    Returns:
        List of ChildChunk objects with parent references and page numbers.
    """
    size = chunk_size or settings.child_chunk_size
    overlap = chunk_overlap or settings.child_chunk_overlap
    splitter = get_token_splitter(chunk_size=size, chunk_overlap=overlap)

    children: List[ChildChunk] = []

    for parent_idx, parent in enumerate(parents):
        splits = splitter.split_text(parent.text)
        if not splits:
            splits = [parent.text]

        total_splits = len(splits)
        for split_idx, split_text in enumerate(splits):
            if not split_text.strip():
                continue

            # Compute page span for child chunk
            if parent.page_start == parent.page_end:
                p_start = parent.page_start
                p_end = parent.page_start
            else:
                # Interpolate across the parent's page range based on split progress
                progress_start = split_idx / total_splits
                progress_end = (split_idx + 1) / total_splits
                page_span = parent.page_end - parent.page_start
                p_start = parent.page_start + int(progress_start * (page_span + 1))
                p_end = parent.page_start + int(progress_end * (page_span + 1))
                p_start = min(max(p_start, parent.page_start), parent.page_end)
                p_end = min(max(p_end, p_start), parent.page_end)

            children.append(
                ChildChunk(
                    text=split_text,
                    page_start=p_start,
                    page_end=p_end,
                    parent_index=parent_idx,
                )
            )

    logger.info("Split %d parents into %d child chunks", len(parents), len(children))
    return children

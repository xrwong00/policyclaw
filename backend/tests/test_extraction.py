"""Unit test — PDF chunk extraction."""

from __future__ import annotations

import io

import pytest
from pypdf import PdfWriter


def _build_tiny_pdf() -> bytes:
    """Minimal PDF with two blank pages — exercises page-iteration path only.

    We don't assert on text content because pypdf needs a writer that embeds
    text streams; for the extractor we mainly verify it consumes bytes and
    yields a structured chunk list without crashing.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.mark.unit
def test_parse_pdf_chunks_returns_list_for_valid_pdf() -> None:
    from app.services.pdf_parser import parse_pdf_chunks

    chunks = parse_pdf_chunks(_build_tiny_pdf(), "sample.pdf")

    assert isinstance(chunks, list)
    for chunk in chunks:
        assert hasattr(chunk, "text")
        assert hasattr(chunk, "page")
        assert hasattr(chunk, "section")
        assert hasattr(chunk, "source")
        assert chunk.source == "sample.pdf"
        assert chunk.page >= 1


@pytest.mark.unit
def test_parse_pdf_chunks_handles_non_pdf_bytes_gracefully() -> None:
    """Non-PDF bytes should either raise or yield no chunks — the pipeline must
    never produce spurious structured output that a downstream GLM call could
    over-interpret."""
    from app.services.pdf_parser import parse_pdf_chunks

    try:
        chunks = parse_pdf_chunks(b"not a pdf", "junk.pdf")
    except Exception:
        return  # Raising is acceptable.
    assert chunks == []

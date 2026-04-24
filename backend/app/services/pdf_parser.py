from __future__ import annotations

from dataclasses import dataclass

import fitz  # pymupdf


@dataclass(slots=True)
class PolicyChunk:
    text: str
    page: int
    section: str
    source: str


@dataclass(slots=True)
class ClauseWithBBox:
    clause_id: str
    text: str
    page: int
    bbox: tuple[float, float, float, float]
    source: str


_MIN_CHUNK_CHARS = 40
_MIN_CLAUSE_CHARS = 20
_CLAUSE_TEXT_CAP = 1200


def _detect_section(block_text: str, page: int) -> str:
    lines = [line.strip() for line in block_text.splitlines() if line.strip()]
    if not lines:
        return f"Page {page}"

    heading = lines[0][:80]
    return heading if heading else f"Page {page}"


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 160) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def _iter_page_blocks(page: "fitz.Page") -> list[tuple[tuple[float, float, float, float], str, int]]:
    """Return list of (bbox, text, block_no) for TEXT blocks only, in reading order."""
    raw = page.get_text("blocks") or []
    blocks: list[tuple[tuple[float, float, float, float], str, int]] = []
    for item in raw:
        # PyMuPDF returns: (x0, y0, x1, y1, text, block_no, block_type)
        if len(item) < 7:
            continue
        x0, y0, x1, y1, text, block_no, block_type = item[:7]
        if block_type != 0:
            continue
        if not isinstance(text, str):
            continue
        blocks.append(((float(x0), float(y0), float(x1), float(y1)), text, int(block_no)))
    return blocks


def parse_pdf_chunks(pdf_bytes: bytes, source_name: str) -> list[PolicyChunk]:
    """Parse PDF and split text into metadata-rich chunks for retrieval.

    Backed by PyMuPDF. Public signature preserved for profile_extraction_service
    and analyze_service callers.
    """
    chunks: list[PolicyChunk] = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return chunks

    try:
        for page_index, page in enumerate(doc, start=1):
            page_text = (page.get_text("text") or "").strip()
            if not page_text:
                continue

            blocks = [block.strip() for block in page_text.split("\n\n") if block.strip()]
            if not blocks:
                blocks = [page_text]

            for block in blocks:
                section = _detect_section(block, page_index)
                for piece in _chunk_text(block):
                    cleaned = " ".join(piece.split())
                    if len(cleaned) < _MIN_CHUNK_CHARS:
                        continue
                    chunks.append(
                        PolicyChunk(
                            text=cleaned,
                            page=page_index,
                            section=section,
                            source=source_name,
                        )
                    )
    finally:
        doc.close()

    return chunks


def extract_clauses_with_bboxes(
    pdf_bytes: bytes, source_name: str
) -> list[ClauseWithBBox]:
    """Block-level extraction using PyMuPDF, one ClauseWithBBox per text block.

    Blocks approximate paragraphs — the right granularity for clause-level risk
    annotation. Returns an empty list on encrypted/image-only PDFs so the caller
    can degrade gracefully.
    """
    clauses: list[ClauseWithBBox] = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return clauses

    try:
        for page_index, page in enumerate(doc, start=1):
            for bbox, raw_text, block_no in _iter_page_blocks(page):
                cleaned = " ".join(raw_text.split())
                if len(cleaned) < _MIN_CLAUSE_CHARS:
                    continue
                if len(cleaned) > _CLAUSE_TEXT_CAP:
                    cleaned = cleaned[:_CLAUSE_TEXT_CAP]
                clauses.append(
                    ClauseWithBBox(
                        clause_id=f"p{page_index}-c{block_no}",
                        text=cleaned,
                        page=page_index,
                        bbox=bbox,
                        source=source_name,
                    )
                )
    finally:
        doc.close()

    return clauses

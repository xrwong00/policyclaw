from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


@dataclass(slots=True)
class PolicyChunk:
    text: str
    page: int
    section: str
    source: str


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


def parse_pdf_chunks(pdf_bytes: bytes, source_name: str) -> list[PolicyChunk]:
    """Parse PDF and split text into metadata-rich chunks for retrieval."""
    reader = PdfReader(BytesIO(pdf_bytes))
    chunks: list[PolicyChunk] = []

    for page_index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if not page_text:
            continue

        blocks = [block.strip() for block in page_text.split("\n\n") if block.strip()]
        if not blocks:
            blocks = [page_text]

        for block in blocks:
            section = _detect_section(block, page_index)
            for piece in _chunk_text(block):
                cleaned = " ".join(piece.split())
                if len(cleaned) < 40:
                    continue
                chunks.append(
                    PolicyChunk(
                        text=cleaned,
                        page=page_index,
                        section=section,
                        source=source_name,
                    )
                )

    return chunks

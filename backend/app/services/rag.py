from __future__ import annotations

import re
from collections import Counter

from app.services.pdf_parser import PolicyChunk


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)]


def _score_chunk(query_tokens: Counter[str], chunk: PolicyChunk) -> float:
    chunk_tokens = Counter(_tokenize(chunk.text))
    if not chunk_tokens:
        return 0.0

    overlap = 0.0
    for token, count in query_tokens.items():
        overlap += min(count, chunk_tokens.get(token, 0))

    density_bonus = min(len(chunk.text), 1200) / 1200.0
    return overlap + (0.15 * density_bonus)


def retrieve_relevant_chunks(
    chunks: list[PolicyChunk],
    query: str,
    k: int = 10,
) -> list[PolicyChunk]:
    """Simple lexical retrieval. Designed to be swapped with embeddings later."""
    if not chunks:
        return []

    query_tokens = Counter(_tokenize(query))
    if not query_tokens:
        return chunks[:k]

    scored = [(chunk, _score_chunk(query_tokens, chunk)) for chunk in chunks]
    scored.sort(key=lambda item: item[1], reverse=True)

    return [chunk for chunk, _ in scored[:k]]


def build_context(chunks: list[PolicyChunk]) -> str:
    lines: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[{idx}] source={chunk.source}; page={chunk.page}; section={chunk.section}\n{chunk.text}"
        )
    return "\n\n".join(lines)

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    id: str
    document_id: str
    filename: str
    page: int
    text: str


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_page_text(
    text: str,
    document_id: str,
    filename: str,
    page: int,
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[TextChunk]:
    """Split one page into overlapping character chunks at word boundaries."""
    cleaned = normalize_text(text)
    if not cleaned:
        return []

    chunks: list[TextChunk] = []
    start = 0
    chunk_number = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        if end < len(cleaned):
            boundary = cleaned.rfind(" ", start, end)
            if boundary > start + chunk_size // 2:
                end = boundary
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(
                TextChunk(
                    id=f"{document_id}-p{page}-c{chunk_number}",
                    document_id=document_id,
                    filename=filename,
                    page=page,
                    text=piece,
                )
            )
            chunk_number += 1
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


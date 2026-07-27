import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from .loaders.base import RawDocument

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _split_into_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]
    return paragraphs or [text.strip()]


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Trocea texto por párrafos, agrupándolos hasta `chunk_size` caracteres con
    solapamiento (`chunk_overlap`) para no perder contexto entre chunks."""
    paragraphs = _split_into_paragraphs(text)
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            overlap_tail = current[-chunk_overlap:] if chunk_overlap else ""
            current = f"{overlap_tail}\n\n{paragraph}".strip()
        else:
            # Un solo párrafo ya excede chunk_size: se corta en bloques duros.
            for start in range(0, len(paragraph), chunk_size - chunk_overlap):
                chunks.append(paragraph[start : start + chunk_size])
            current = ""

    if current:
        chunks.append(current)

    return chunks


def build_chunks(document: RawDocument, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    pieces = chunk_text(document.content, chunk_size, chunk_overlap)
    chunks: list[Chunk] = []

    for index, piece in enumerate(pieces):
        source = document.metadata.get("source", "unknown")
        raw_id = f"{source}::{document.metadata.get('page', document.metadata.get('sheet', ''))}::{index}::{piece[:50]}"
        chunk_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]
        metadata = {**document.metadata, "chunk_index": index}
        chunks.append(Chunk(id=chunk_id, text=piece, metadata=metadata))

    return chunks

"""Intelligent text chunking with configurable size and overlap."""
import logging
from dataclasses import dataclass
from typing import List

from src.document_loader import Document

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    source: str
    chunk_index: int
    metadata: dict


def split_documents(
    documents: List[Document],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[Chunk]:
    """Split documents into overlapping text chunks."""
    all_chunks: List[Chunk] = []

    for doc in documents:
        chunks = _split_text(doc.content, chunk_size, chunk_overlap)
        logger.info("  %s → %d chunk(s)", doc.source, len(chunks))

        for idx, text in enumerate(chunks):
            all_chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    chunk_index=idx,
                    metadata={**doc.metadata, "file_type": doc.file_type},
                )
            )

    logger.info("Total chunks produced: %d", len(all_chunks))
    return all_chunks


def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split *text* by word boundaries, respecting chunk_size and overlap."""
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words).strip()

        if chunk_text:
            chunks.append(chunk_text)

        if end >= len(words):
            break

        # Move forward by (chunk_size - overlap) to create overlapping windows
        step = max(1, chunk_size - overlap)
        start += step

    return chunks

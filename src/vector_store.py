"""ChromaDB vector store — persist, load, and query document embeddings."""
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings

from src.text_splitter import Chunk

logger = logging.getLogger(__name__)


def _chunk_id(chunk: Chunk) -> str:
    key = f"{chunk.source}::{chunk.chunk_index}::{chunk.text[:64]}"
    return hashlib.md5(key.encode()).hexdigest()


class VectorStore:
    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        embedding_model: str,
    ):
        self._embedding_model = embedding_model
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Vector store ready — collection '%s' has %d document(s)",
            collection_name,
            self._collection.count(),
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: List[Chunk]) -> int:
        """Upsert chunks into the collection. Returns count of new items."""
        if not chunks:
            return 0

        from src.embeddings import embed_texts

        ids = [_chunk_id(c) for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [
            {"source": c.source, "chunk_index": c.chunk_index, **c.metadata}
            for c in chunks
        ]

        embeddings = embed_texts(texts, self._embedding_model)

        self._collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Indexed %d chunk(s)", len(chunks))
        return len(chunks)

    def needs_reindex(self, chunks: List[Chunk]) -> bool:
        """Return True if the store doesn't exactly mirror the current chunks.

        Detects both additions (new documents) and removals (deleted documents).
        """
        if self._collection.count() == 0:
            return True
        ids = set(_chunk_id(c) for c in chunks)
        # Count mismatch catches both added and removed documents
        if self._collection.count() != len(ids):
            return True
        # Same count but different content (document swap): check every ID exists
        existing = self._collection.get(ids=list(ids), include=[])
        return len(existing["ids"]) < len(ids)

    def delete_stale_chunks(self, current_chunks: List[Chunk]) -> int:
        """Remove from the store any chunks not present in *current_chunks*.

        Called after add_chunks so that vectors from deleted documents are purged.
        Returns the number of deleted entries.
        """
        current_ids = {_chunk_id(c) for c in current_chunks}
        all_ids = set(self._collection.get(include=[])["ids"])
        stale_ids = list(all_ids - current_ids)
        if stale_ids:
            self._collection.delete(ids=stale_ids)
            logger.info("Purged %d stale chunk(s) from vector store", len(stale_ids))
        return len(stale_ids)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        min_score: float = 0.3,
    ) -> List[Dict]:
        """
        Return top-k chunks ranked by cosine similarity.
        Each result dict has: text, source, chunk_index, score.
        """
        if self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # ChromaDB cosine distance → similarity score (0-1)
            score = 1.0 - dist
            if score >= min_score:
                hits.append(
                    {
                        "text": doc,
                        "source": meta.get("source", "unknown"),
                        "chunk_index": meta.get("chunk_index", 0),
                        "score": round(score, 4),
                    }
                )

        return hits

    def count(self) -> int:
        return self._collection.count()

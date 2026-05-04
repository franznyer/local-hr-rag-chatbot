"""Core RAG pipeline — orchestrates retrieval, prompt construction, and generation."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import src.config as cfg
from src.document_loader import load_documents
from src.embeddings import embed_query
from src.prompts import HR_SYSTEM_PROMPT, build_rag_prompt
from src.providers.base import BaseProvider, Message, ProviderResponse
from src.text_splitter import split_documents
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    answer: str
    sources: List[dict]
    confidence: float
    provider: str
    model: str
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


def _build_provider(provider_name: str) -> BaseProvider:
    """Instantiate the right provider from config."""
    if provider_name == "openai":
        from src.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(cfg.MODEL_NAME, cfg.OPENAI_API_KEY)

    if provider_name == "claude":
        from src.providers.claude_provider import ClaudeProvider
        return ClaudeProvider(cfg.MODEL_NAME, cfg.ANTHROPIC_API_KEY)

    if provider_name == "mistral":
        from src.providers.mistral_provider import MistralProvider
        return MistralProvider(cfg.MODEL_NAME, cfg.MISTRAL_API_KEY)

    if provider_name == "ollama":
        from src.providers.ollama_provider import OllamaProvider
        return OllamaProvider(cfg.MODEL_NAME, cfg.OLLAMA_BASE_URL)

    if provider_name == "lmstudio":
        from src.providers.lmstudio_provider import LMStudioProvider
        return LMStudioProvider(cfg.MODEL_NAME, cfg.LMSTUDIO_BASE_URL)

    raise ValueError(f"Unknown AI provider: '{provider_name}'. "
                     "Valid options: openai, claude, mistral, ollama, lmstudio")


class RAGPipeline:
    """Full retrieval-augmented generation pipeline for HR documents."""

    def __init__(self, provider_name: Optional[str] = None):
        self._provider_name = (provider_name or cfg.AI_PROVIDER).lower()
        self._provider: Optional[BaseProvider] = None
        self._vector_store: Optional[VectorStore] = None

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Load documents, build/reload vector store, and warm up the provider."""
        logger.info("=== Initialising RAG pipeline ===")
        self._init_vector_store()
        self._init_provider()

    def _init_vector_store(self) -> None:
        self._vector_store = VectorStore(
            persist_dir=cfg.VECTORSTORE_DIR,
            collection_name=cfg.CHROMA_COLLECTION_NAME,
            embedding_model=cfg.EMBEDDING_MODEL,
        )

        docs = load_documents(cfg.DOCUMENTS_DIR)
        if not docs:
            logger.warning("No documents found in %s", cfg.DOCUMENTS_DIR)
            return

        chunks = split_documents(docs, cfg.CHUNK_SIZE, cfg.CHUNK_OVERLAP)

        if self._vector_store.needs_reindex(chunks):
            logger.info("Indexing documents into vector store …")
            self._vector_store.add_chunks(chunks)
        else:
            logger.info("Vector store up-to-date, skipping re-index.")

    def _init_provider(self) -> None:
        logger.info("Loading AI provider: %s / %s", self._provider_name, cfg.MODEL_NAME)
        self._provider = _build_provider(self._provider_name)

        if not self._provider.health_check():
            logger.warning(
                "Provider '%s' health check failed — make sure the service is running.",
                self._provider_name,
            )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, question: str, chat_history: Optional[List[Message]] = None) -> RAGResponse:
        """Run the full RAG pipeline for a user question."""
        if not question.strip():
            return RAGResponse(
                answer="Veuillez poser une question.",
                sources=[],
                confidence=0.0,
                provider=self._provider_name,
                model=cfg.MODEL_NAME,
            )

        # 1. Retrieve relevant chunks
        query_vector = embed_query(question, cfg.EMBEDDING_MODEL)
        hits = self._vector_store.similarity_search(
            query_vector, top_k=cfg.TOP_K_RESULTS, min_score=cfg.MIN_RELEVANCE_SCORE
        )

        logger.info("Retrieved %d chunk(s) for query: %s", len(hits), question[:80])

        # 2. Build messages
        user_content = build_rag_prompt(question, hits)
        messages: List[Message] = [Message(role="system", content=HR_SYSTEM_PROMPT)]

        if chat_history:
            messages.extend(chat_history[-6:])  # keep last 3 turns

        messages.append(Message(role="user", content=user_content))

        # 3. Call the AI provider
        response: ProviderResponse = self._provider.complete(messages)

        if not response.success:
            return RAGResponse(
                answer="",
                sources=hits,
                confidence=0.0,
                provider=self._provider_name,
                model=cfg.MODEL_NAME,
                error=response.error,
            )

        # 4. Compute a simple confidence score
        confidence = _compute_confidence(hits)

        return RAGResponse(
            answer=response.content,
            sources=hits,
            confidence=confidence,
            provider=response.provider,
            model=response.model,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def reindex(self) -> int:
        """Force re-index of all documents. Returns total chunks indexed."""
        docs = load_documents(cfg.DOCUMENTS_DIR)
        chunks = split_documents(docs, cfg.CHUNK_SIZE, cfg.CHUNK_OVERLAP)
        return self._vector_store.add_chunks(chunks)

    def provider_status(self) -> dict:
        return {
            "provider": self._provider_name,
            "model": cfg.MODEL_NAME,
            "healthy": self._provider.health_check() if self._provider else False,
            "indexed_chunks": self._vector_store.count() if self._vector_store else 0,
        }


def _compute_confidence(hits: List[dict]) -> float:
    """Average top-3 similarity scores as a rough confidence indicator."""
    if not hits:
        return 0.0
    scores = [h["score"] for h in hits[:3]]
    return round(sum(scores) / len(scores), 2)

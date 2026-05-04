"""Centralized configuration management."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

# Directories
DOCUMENTS_DIR = BASE_DIR / "documents"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

# Ensure directories exist
DOCUMENTS_DIR.mkdir(exist_ok=True)
VECTORSTORE_DIR.mkdir(exist_ok=True)

# Embedding model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Text splitting
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))

# ChromaDB
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "hr_documents")

# AI Provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

# Provider API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

# Ollama / LM Studio endpoints
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")

# RAG retrieval
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "4"))
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.3"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

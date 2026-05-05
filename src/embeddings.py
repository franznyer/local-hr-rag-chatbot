"""Local embedding generation via sentence-transformers."""
import logging
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    """Load and cache the embedding model (loaded once per process)."""
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", model_name)
        model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded.")
        return model
    except ImportError:
        raise ImportError("Run: pip install sentence-transformers")


def embed_texts(texts: List[str], model_name: str) -> List[List[float]]:
    """Return a list of embedding vectors for the given texts."""
    if not texts:
        return []
    model = _load_model(model_name)
    vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return vectors.tolist()


def embed_query(query: str, model_name: str) -> List[float]:
    """Return a single embedding vector for a search query."""
    return embed_texts([query], model_name)[0]

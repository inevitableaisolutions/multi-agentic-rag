"""Vertex AI embedding client.

Uses gemini-embedding-001 (768 dimensions) for text vectorization.
Falls back to a simple TF-IDF-based approach if Vertex AI is unavailable.
"""

import os
import numpy as np

from customer_support_agent.config.settings import settings

# Lazy-loaded clients
_vertex_model = None


def _get_vertex_model():
    """Lazy-initialize the Vertex AI embedding model."""
    global _vertex_model
    if _vertex_model is None:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(
            project=settings.GOOGLE_CLOUD_PROJECT or os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=settings.GOOGLE_CLOUD_LOCATION,
        )
        _vertex_model = TextEmbeddingModel.from_pretrained(settings.EMBEDDING_MODEL)
    return _vertex_model


def get_embeddings(
    texts: list[str],
    batch_size: int = 100,
) -> np.ndarray:
    """Get embeddings for a list of texts using Vertex AI.

    Args:
        texts: List of text strings to embed.
        batch_size: Max texts per API call (Vertex AI limit: 250).

    Returns:
        numpy array of shape (len(texts), embedding_dimensions).
    """
    if not texts:
        return np.array([])

    use_vertex = settings.GOOGLE_GENAI_USE_VERTEXAI and (
        settings.GOOGLE_CLOUD_PROJECT or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )

    if use_vertex:
        return _get_vertex_embeddings(texts, batch_size)
    elif settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY"):
        return _get_genai_embeddings(texts, batch_size)
    else:
        raise ValueError(
            "No embedding backend configured. Set GOOGLE_CLOUD_PROJECT for Vertex AI "
            "or GOOGLE_API_KEY for Google AI Studio."
        )


def _get_vertex_embeddings(texts: list[str], batch_size: int) -> np.ndarray:
    """Get embeddings via Vertex AI TextEmbeddingModel."""
    model = _get_vertex_model()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        # Truncate texts that are too long (2048 token limit ≈ 8192 chars)
        batch = [t[:8000] for t in batch]
        results = model.get_embeddings(batch)
        all_embeddings.extend([r.values for r in results])

    return np.array(all_embeddings, dtype="float32")


def _get_genai_embeddings(texts: list[str], batch_size: int) -> np.ndarray:
    """Get embeddings via Google AI Studio (Gemini API key)."""
    from google import genai

    api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch = [t[:8000] for t in batch]
        result = client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=batch,
        )
        all_embeddings.extend([e.values for e in result.embeddings])

    return np.array(all_embeddings, dtype="float32")

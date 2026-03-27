"""FAISS index builder for dense vector search.

Builds a FAISS index from chunked documents using Vertex AI embeddings.
Supports building from scratch and loading from disk.
"""

import json
from pathlib import Path

import faiss
import numpy as np

from customer_support_agent.rag.chunker import load_and_chunk_documents
from customer_support_agent.rag.embeddings import get_embeddings
from customer_support_agent.config.settings import settings


# Module-level cache
_index = None
_documents = None


def build_index(
    knowledge_base_dir: str = settings.KNOWLEDGE_BASE_DIR,
) -> tuple[faiss.Index, list[dict]]:
    """Build a FAISS index from knowledge base documents.

    Returns:
        Tuple of (FAISS index, list of document metadata dicts).
    """
    # Load and chunk documents
    documents = load_and_chunk_documents(knowledge_base_dir)
    if not documents:
        raise ValueError(f"No documents found in {knowledge_base_dir}")

    # Get embeddings for all chunks
    texts = [doc["content"] for doc in documents]
    embeddings = get_embeddings(texts)

    # Normalize for cosine similarity (inner product on normalized = cosine)
    faiss.normalize_L2(embeddings)

    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine on normalized vectors
    index.add(embeddings)

    return index, documents


def get_index(
    knowledge_base_dir: str = settings.KNOWLEDGE_BASE_DIR,
) -> tuple[faiss.Index, list[dict]]:
    """Get or build the FAISS index (cached in memory).

    Returns:
        Tuple of (FAISS index, list of document metadata dicts).
    """
    global _index, _documents

    if _index is None or _documents is None:
        _index, _documents = build_index(knowledge_base_dir)

    return _index, _documents


def save_index(index: faiss.Index, documents: list[dict], output_dir: str = "data") -> None:
    """Save FAISS index and document metadata to disk."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(out / "faiss.index"))

    with open(out / "documents.json", "w") as f:
        json.dump(documents, f, indent=2)


def load_index(input_dir: str = "data") -> tuple[faiss.Index, list[dict]]:
    """Load FAISS index and document metadata from disk."""
    inp = Path(input_dir)

    index = faiss.read_index(str(inp / "faiss.index"))

    with open(inp / "documents.json") as f:
        documents = json.load(f)

    return index, documents

"""FAISS-based semantic cache for similar query deduplication.

Caches query-response pairs. On new query, checks if a semantically similar
query was already answered. Cache hit skips all agents = instant response.

Expected cost savings: 40-60% on repeated/similar queries.
"""

import time
from collections import OrderedDict

import faiss
import numpy as np

from customer_support_agent.rag.embeddings import get_embeddings
from customer_support_agent.config.settings import settings


class SemanticCache:
    """FAISS-based semantic cache with LRU eviction."""

    def __init__(
        self,
        similarity_threshold: float = settings.CACHE_SIMILARITY_THRESHOLD,
        max_size: int = 1000,
        ttl_seconds: int = 3600,  # 1 hour default TTL
    ):
        self.similarity_threshold = similarity_threshold
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # FAISS index for cached query embeddings
        self.dimension = settings.EMBEDDING_DIMENSIONS
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine on normalized)

        # Ordered dict for LRU eviction: key=int index, value=cache entry
        self.entries: OrderedDict[int, dict] = OrderedDict()
        self._next_id = 0

        # Stats
        self.hits = 0
        self.misses = 0

    def lookup(self, query: str) -> dict | None:
        """Check if a similar query exists in the cache.

        Args:
            query: The incoming query string.

        Returns:
            Cached response dict if found (similarity > threshold), None otherwise.
        """
        if self.index.ntotal == 0:
            self.misses += 1
            return None

        # Embed the query
        query_embedding = get_embeddings([query])
        faiss.normalize_L2(query_embedding)

        # Search cache
        scores, indices = self.index.search(query_embedding, 1)
        best_score = float(scores[0][0])
        best_idx = int(indices[0][0])

        if best_score >= self.similarity_threshold and best_idx in self.entries:
            entry = self.entries[best_idx]

            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                # Expired — don't return, but don't evict here (lazy eviction)
                self.misses += 1
                return None

            # Cache hit!
            self.hits += 1
            # Move to end for LRU
            self.entries.move_to_end(best_idx)
            return {
                "cached_response": entry["response"],
                "original_query": entry["query"],
                "similarity_score": best_score,
                "cache_hit": True,
            }

        self.misses += 1
        return None

    def store(self, query: str, response: str, metadata: dict | None = None) -> None:
        """Store a query-response pair in the cache.

        Args:
            query: The query string.
            response: The generated response.
            metadata: Optional metadata to store alongside.
        """
        # Evict if at capacity
        if len(self.entries) >= self.max_size:
            # Remove oldest (first) entry
            oldest_key = next(iter(self.entries))
            del self.entries[oldest_key]
            # Note: FAISS doesn't support deletion from IndexFlatIP.
            # For production, use IndexIDMap. For demo scale, rebuild is fine.

        # Embed and add to index
        query_embedding = get_embeddings([query])
        faiss.normalize_L2(query_embedding)
        self.index.add(query_embedding)

        # Store entry
        self.entries[self._next_id] = {
            "query": query,
            "response": response,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self._next_id += 1

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        total = self.hits + self.misses
        return {
            "size": len(self.entries),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0.0,
            "total_queries": total,
        }

    def clear(self) -> None:
        """Clear the entire cache."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.entries.clear()
        self._next_id = 0
        self.hits = 0
        self.misses = 0

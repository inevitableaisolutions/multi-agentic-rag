"""Centralized configuration for the Customer Support Intelligence system."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration loaded from environment variables / .env file."""

    # --- GCP ---
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GOOGLE_GENAI_USE_VERTEXAI: bool = True

    # --- Google AI Studio (alternative auth) ---
    GOOGLE_API_KEY: str = ""

    # --- Models ---
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 3072

    # --- RAG ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128
    RAG_TOP_K: int = 5
    KNOWLEDGE_BASE_DIR: str = "customer_support_agent/knowledge_base"

    # --- Cache ---
    CACHE_SIMILARITY_THRESHOLD: float = 0.95

    # --- BigQuery ---
    BQ_DATASET: str = "support_analytics"
    BQ_TABLE: str = "interactions"

    # --- Fallbacks ---
    USE_LOCAL_ANALYTICS: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Singleton instance
settings = Settings()

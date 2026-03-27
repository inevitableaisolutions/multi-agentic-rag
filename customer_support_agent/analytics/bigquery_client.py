"""Analytics client with BigQuery + SQLite fallback.

Uses BigQuery in production, SQLite for local development.
The interface is identical — callers don't need to know which backend is active.
"""

import json
import os
import sqlite3
from pathlib import Path

from customer_support_agent.config.settings import settings


class SQLiteBackend:
    """SQLite backend for local development analytics."""

    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                timestamp TEXT,
                session_id TEXT,
                original_query TEXT,
                rewritten_queries TEXT,
                intent TEXT,
                sentiment TEXT,
                urgency TEXT,
                retrieved_doc_ids TEXT,
                num_docs_retrieved INTEGER,
                faithfulness_score REAL,
                answer_relevance_score REAL,
                context_relevance_score REAL,
                overall_score REAL,
                hallucination_detected INTEGER,
                compliance_passed INTEGER,
                decision TEXT,
                cache_hit INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def insert_row(self, row: dict):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO interactions VALUES (
                :timestamp, :session_id, :original_query, :rewritten_queries,
                :intent, :sentiment, :urgency, :retrieved_doc_ids, :num_docs_retrieved,
                :faithfulness_score, :answer_relevance_score, :context_relevance_score,
                :overall_score, :hallucination_detected, :compliance_passed,
                :decision, :cache_hit
            )""",
            row,
        )
        conn.commit()
        conn.close()

    def get_all_rows(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM interactions ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]


class BigQueryBackend:
    """BigQuery backend for production analytics."""

    def __init__(self):
        from google.cloud import bigquery
        self.client = bigquery.Client(
            project=settings.GOOGLE_CLOUD_PROJECT or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        self.table_id = (
            f"{settings.GOOGLE_CLOUD_PROJECT}.{settings.BQ_DATASET}.{settings.BQ_TABLE}"
        )

    def insert_row(self, row: dict):
        errors = self.client.insert_rows_json(self.table_id, [row])
        if errors:
            raise RuntimeError(f"BigQuery insert failed: {errors}")

    def get_all_rows(self) -> list[dict]:
        query = f"SELECT * FROM `{self.table_id}` ORDER BY timestamp DESC LIMIT 100"
        results = self.client.query(query).result()
        return [dict(row) for row in results]


class AnalyticsClient:
    """Unified analytics client that auto-selects backend."""

    def __init__(self):
        if settings.USE_LOCAL_ANALYTICS:
            self._backend = SQLiteBackend()
        else:
            try:
                self._backend = BigQueryBackend()
            except Exception:
                # Fall back to SQLite if BigQuery setup fails
                self._backend = SQLiteBackend()

    def insert_row(self, row: dict):
        self._backend.insert_row(row)

    def get_all_rows(self) -> list[dict]:
        return self._backend.get_all_rows()


# Singleton
_client = None


def get_analytics_client() -> AnalyticsClient:
    global _client
    if _client is None:
        _client = AnalyticsClient()
    return _client

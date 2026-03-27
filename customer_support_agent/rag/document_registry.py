"""Document registry — tracks ingested documents with hash-based deduplication.

Enterprise pattern: metadata DB that tracks document IDs, content hashes,
versions, and status. Prevents duplicates, handles updates, tracks history.

Uses SQLite for local dev. Production: swap to Firestore or Cloud SQL.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class DocumentRegistry:
    """Tracks all ingested documents with hash-based deduplication."""

    def __init__(self, db_path: str = "document_registry.db"):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id          TEXT PRIMARY KEY,
                filename        TEXT NOT NULL,
                source_path     TEXT NOT NULL,
                category        TEXT NOT NULL,
                file_hash       TEXT NOT NULL,
                content_hash    TEXT NOT NULL,
                version         INTEGER DEFAULT 1,
                status          TEXT DEFAULT 'active',
                chunk_count     INTEGER DEFAULT 0,
                file_format     TEXT,
                file_size_bytes INTEGER,
                ingested_at     TEXT NOT NULL,
                updated_at      TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON documents(file_hash)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_hash ON documents(content_hash)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON documents(status)
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """SHA-256 hash of raw file bytes."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """SHA-256 hash of normalized text content.
        Catches same content in different formats (PDF vs DOCX).
        """
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def check_document(self, file_path: str, content_text: str = "") -> dict:
        """Check if a document is new, an update, or a duplicate.

        Args:
            file_path: Path to the file.
            content_text: Extracted text content (optional, for content-level dedup).

        Returns:
            dict with:
                - action: "skip_duplicate" | "skip_content_duplicate" | "update" | "new"
                - existing_doc: dict of existing document record (if any)
                - reason: human-readable explanation
        """
        file_hash = self.compute_file_hash(file_path)
        filename = Path(file_path).name

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Check 1: Exact file hash match (same file bytes)
        row = conn.execute(
            "SELECT * FROM documents WHERE file_hash = ? AND status = 'active'",
            (file_hash,),
        ).fetchone()
        if row:
            conn.close()
            return {
                "action": "skip_duplicate",
                "existing_doc": dict(row),
                "reason": f"Exact duplicate of '{row['filename']}' (same file hash)",
            }

        # Check 2: Content hash match (same text, different format)
        if content_text:
            content_hash = self.compute_content_hash(content_text)
            row = conn.execute(
                "SELECT * FROM documents WHERE content_hash = ? AND status = 'active'",
                (content_hash,),
            ).fetchone()
            if row:
                conn.close()
                return {
                    "action": "skip_content_duplicate",
                    "existing_doc": dict(row),
                    "reason": f"Same content as '{row['filename']}' (different format/file)",
                }

        # Check 3: Same filename in same category (this is an update)
        row = conn.execute(
            "SELECT * FROM documents WHERE filename = ? AND status = 'active'",
            (filename,),
        ).fetchone()
        if row:
            conn.close()
            return {
                "action": "update",
                "existing_doc": dict(row),
                "reason": f"Updated version of '{row['filename']}' (v{row['version']} → v{row['version'] + 1})",
            }

        conn.close()
        return {
            "action": "new",
            "existing_doc": None,
            "reason": "New document",
        }

    def register_document(
        self,
        file_path: str,
        content_text: str,
        category: str,
        chunk_count: int = 0,
        file_format: str = "",
    ) -> dict:
        """Register a new or updated document in the registry.

        Handles the full ingestion flow:
        - New docs: create record
        - Updates: supersede old version, create new record with incremented version
        - Duplicates: should be caught by check_document() before calling this

        Returns:
            dict with doc_id, version, action taken
        """
        file_hash = self.compute_file_hash(file_path)
        content_hash = self.compute_content_hash(content_text)
        filename = Path(file_path).name
        file_size = Path(file_path).stat().st_size
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)

        # Check if this is an update to an existing document
        existing = conn.execute(
            "SELECT * FROM documents WHERE filename = ? AND status = 'active'",
            (filename,),
        ).fetchone()

        if existing:
            # Supersede old version
            old_doc_id = existing[0]  # doc_id
            old_version = existing[6]  # version

            conn.execute(
                "UPDATE documents SET status = 'superseded', updated_at = ? WHERE doc_id = ?",
                (now, old_doc_id),
            )

            new_version = old_version + 1
            doc_id = f"{filename}::v{new_version}"
            action = "updated"
        else:
            new_version = 1
            doc_id = f"{filename}::v1"
            action = "created"

        conn.execute(
            """INSERT INTO documents
            (doc_id, filename, source_path, category, file_hash, content_hash,
             version, status, chunk_count, file_format, file_size_bytes, ingested_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)""",
            (
                doc_id, filename, file_path, category, file_hash, content_hash,
                new_version, chunk_count, file_format, file_size, now, now,
            ),
        )
        conn.commit()
        conn.close()

        return {
            "doc_id": doc_id,
            "version": new_version,
            "action": action,
            "filename": filename,
        }

    def get_active_documents(self) -> list[dict]:
        """Get all active (current version) documents."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM documents WHERE status = 'active' ORDER BY category, filename"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_document_history(self, filename: str) -> list[dict]:
        """Get all versions of a document (active + superseded)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM documents WHERE filename = ? ORDER BY version DESC",
            (filename,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_document(self, filename: str) -> bool:
        """Soft-delete a document (mark as deleted, don't remove from DB)."""
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "UPDATE documents SET status = 'deleted', updated_at = ? WHERE filename = ? AND status = 'active'",
            (now, filename),
        )
        conn.commit()
        affected = result.rowcount
        conn.close()
        return affected > 0

    def get_stats(self) -> dict:
        """Get registry statistics."""
        conn = sqlite3.connect(self.db_path)
        stats = {
            "active": conn.execute("SELECT COUNT(*) FROM documents WHERE status = 'active'").fetchone()[0],
            "superseded": conn.execute("SELECT COUNT(*) FROM documents WHERE status = 'superseded'").fetchone()[0],
            "deleted": conn.execute("SELECT COUNT(*) FROM documents WHERE status = 'deleted'").fetchone()[0],
            "total_versions": conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
        }
        conn.close()
        return stats

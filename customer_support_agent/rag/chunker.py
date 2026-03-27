"""Fixed-length text chunker with overlap.

Splits markdown documents into chunks of configurable token size with overlap
to prevent losing context at chunk boundaries.
"""

from pathlib import Path

from customer_support_agent.config.settings import settings


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks by estimated token count.

    Args:
        text: The text to chunk.
        chunk_size: Target chunk size in tokens (default: 512).
        chunk_overlap: Overlap between chunks in tokens (default: 128).

    Returns:
        List of text chunks.
    """
    # Convert token targets to character estimates
    char_chunk_size = chunk_size * 4
    char_overlap = chunk_overlap * 4

    if len(text) <= char_chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + char_chunk_size

        # Try to break at a paragraph or sentence boundary
        if end < len(text):
            # Look for paragraph break within last 20% of chunk
            search_start = end - (char_chunk_size // 5)
            para_break = text.rfind("\n\n", search_start, end)
            if para_break > start:
                end = para_break + 2
            else:
                # Fall back to sentence boundary
                sent_break = text.rfind(". ", search_start, end)
                if sent_break > start:
                    end = sent_break + 2

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward by (chunk_size - overlap)
        start = start + char_chunk_size - char_overlap

    return chunks


def load_and_chunk_documents(knowledge_base_dir: str = settings.KNOWLEDGE_BASE_DIR) -> list[dict]:
    """Load ALL supported files from the knowledge base and chunk them.

    Supports: PDF, Word (.docx), Excel (.xlsx), CSV, Images, Markdown, TXT.
    PDFs with tables and images are extracted (tables → markdown, images → Gemini Vision).

    Returns:
        List of dicts with keys: content, source, title, category
    """
    from customer_support_agent.rag.document_loader import load_directory, LOADERS

    kb_path = Path(knowledge_base_dir)
    all_chunks = []

    # Load all supported document formats
    documents = load_directory(str(kb_path))

    for doc in documents:
        content = doc.get("text", "")
        if not content.strip():
            continue

        # Extract title from first # heading (for markdown-like content)
        title = doc.get("title", "Unknown")
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        source = doc.get("source", "unknown")
        category = doc.get("category", "general")

        # Chunk the document
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "content": chunk,
                "source": source,
                "title": title,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "format": doc.get("metadata", {}).get("format", "unknown"),
            })

    return all_chunks

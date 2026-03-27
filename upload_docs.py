"""Upload documents to the knowledge base.

Drop files into the knowledge base and rebuild the index.
Supports: PDF, Word (.docx), Excel (.xlsx), CSV, Images, Markdown, TXT.

Usage:
    # Upload a single file to a category
    python upload_docs.py billing invoice.pdf
    python upload_docs.py technical setup_guide.docx
    python upload_docs.py account user_data.xlsx

    # Upload multiple files
    python upload_docs.py billing *.pdf

    # List supported formats
    python upload_docs.py --formats

    # Show current knowledge base stats
    python upload_docs.py --stats
"""

import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from customer_support_agent.rag.document_loader import LOADERS
from customer_support_agent.rag.chunker import load_and_chunk_documents

console = Console()

KB_DIR = Path("customer_support_agent/knowledge_base")
VALID_CATEGORIES = ["billing", "technical", "account", "general"]


def show_formats():
    """Show supported file formats."""
    table = Table(title="Supported File Formats", box=box.ROUNDED)
    table.add_column("Extension", style="cyan")
    table.add_column("Format", style="green")
    table.add_column("Features", style="yellow")

    format_info = {
        ".pdf": ("PDF Document", "Text, tables, images (Gemini Vision)"),
        ".docx": ("Word Document", "Text, headings, tables, embedded images"),
        ".xlsx": ("Excel Spreadsheet", "All sheets → markdown tables"),
        ".xls": ("Excel (Legacy)", "All sheets → markdown tables"),
        ".csv": ("CSV Data", "Tabular data → markdown table"),
        ".png": ("PNG Image", "Gemini Vision description"),
        ".jpg": ("JPEG Image", "Gemini Vision description"),
        ".jpeg": ("JPEG Image", "Gemini Vision description"),
        ".md": ("Markdown", "Direct text ingestion"),
        ".txt": ("Plain Text", "Direct text ingestion"),
    }

    for ext, (name, features) in sorted(format_info.items()):
        table.add_row(ext, name, features)

    console.print(table)


def show_stats():
    """Show current knowledge base statistics."""
    chunks = load_and_chunk_documents()

    table = Table(title="Knowledge Base Statistics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    categories = {}
    formats = {}
    for chunk in chunks:
        cat = chunk["category"]
        fmt = chunk.get("format", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
        formats[fmt] = formats.get(fmt, 0) + 1

    table.add_row("Total Chunks", str(len(chunks)))
    table.add_row("Unique Sources", str(len(set(c["source"] for c in chunks))))

    for cat, count in sorted(categories.items()):
        table.add_row(f"  Category: {cat}/", str(count))

    for fmt, count in sorted(formats.items()):
        table.add_row(f"  Format: {fmt}", str(count))

    table.add_row(
        "Avg Chunk Size",
        f"{sum(len(c['content']) for c in chunks) // max(len(chunks), 1)} chars",
    )

    console.print(table)

    # Show files
    console.print("\n[bold]Files in knowledge base:[/bold]")
    for cat_dir in sorted(KB_DIR.iterdir()):
        if cat_dir.is_dir():
            files = sorted(cat_dir.iterdir())
            if files:
                console.print(f"  [cyan]{cat_dir.name}/[/cyan]")
                for f in files:
                    console.print(f"    {f.name} ({f.stat().st_size // 1024}KB)")


def upload_file(category: str, file_path: str):
    """Upload a file with enterprise-grade deduplication.

    Uses document registry with SHA-256 hash-based dedup:
    - Same file bytes → skip (exact duplicate)
    - Same text content, different format → skip (content duplicate)
    - Same filename, different content → update (supersede old version)
    - New file → ingest
    """
    from customer_support_agent.rag.document_registry import DocumentRegistry
    from customer_support_agent.rag.document_loader import load_document

    src = Path(file_path)
    if not src.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return False

    if src.suffix.lower() not in LOADERS:
        console.print(f"[red]Unsupported format: {src.suffix}[/red]")
        show_formats()
        return False

    if category not in VALID_CATEGORIES:
        console.print(f"[red]Invalid category: {category}[/red]")
        console.print(f"[dim]Valid categories: {', '.join(VALID_CATEGORIES)}[/dim]")
        return False

    # Extract text content for content-level dedup
    try:
        doc = load_document(str(src))
        content_text = doc.get("text", "")
    except Exception as e:
        console.print(f"[red]Failed to parse {src.name}: {e}[/red]")
        return False

    # Check registry for duplicates
    registry = DocumentRegistry()
    check = registry.check_document(str(src), content_text)

    if check["action"] == "skip_duplicate":
        console.print(f"[yellow]⚠ Skipped (exact duplicate):[/yellow] {check['reason']}")
        return False

    if check["action"] == "skip_content_duplicate":
        console.print(f"[yellow]⚠ Skipped (same content):[/yellow] {check['reason']}")
        return False

    if check["action"] == "update":
        console.print(f"[cyan]↻ Updating:[/cyan] {check['reason']}")

    # Copy file to knowledge base (skip if already in place)
    dest_dir = KB_DIR / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if src.resolve() != dest.resolve():
        shutil.copy2(str(src), str(dest))

    # Register in document registry
    result = registry.register_document(
        file_path=str(dest),
        content_text=content_text,
        category=category,
        file_format=src.suffix.lstrip("."),
    )

    if result["action"] == "updated":
        console.print(
            f"[green]✓ Updated:[/green] {src.name} → {category}/ "
            f"(v{result['version']})"
        )
    else:
        console.print(
            f"[green]✓ Uploaded:[/green] {src.name} → {category}/ "
            f"(v{result['version']})"
        )
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[bold]Usage:[/bold]")
        console.print("  python upload_docs.py [category] [file1] [file2] ...")
        console.print("  python upload_docs.py --formats")
        console.print("  python upload_docs.py --stats")
        console.print(f"\n[dim]Categories: {', '.join(VALID_CATEGORIES)}[/dim]")
        sys.exit(0)

    if sys.argv[1] == "--formats":
        show_formats()
    elif sys.argv[1] == "--stats":
        show_stats()
    else:
        category = sys.argv[1]
        files = sys.argv[2:]

        if not files:
            console.print("[red]No files specified.[/red]")
            sys.exit(1)

        uploaded = 0
        for f in files:
            if upload_file(category, f):
                uploaded += 1

        if uploaded > 0:
            console.print(f"\n[bold green]{uploaded} file(s) uploaded.[/bold green]")
            console.print("[dim]Run 'adk web customer_support_agent' to test with new data.[/dim]")
            console.print("[dim]The index rebuilds automatically on next query.[/dim]")

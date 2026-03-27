"""Batch evaluation script.

Runs all test queries through the guardrails and RAG pipeline,
collecting metrics for each. Generates a summary report.

Usage: python -m customer_support_agent.eval.batch_eval
"""

import json
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from customer_support_agent.guardrails import run_guardrails

console = Console()


def load_test_dataset() -> list[dict]:
    """Load test queries from the eval dataset."""
    dataset_path = Path(__file__).parent / "test_dataset.json"
    with open(dataset_path) as f:
        return json.load(f)


def run_guardrails_eval(dataset: list[dict]) -> dict:
    """Evaluate guardrails on the test dataset (no LLM needed)."""
    results = []
    for item in dataset:
        start = time.time()
        result = run_guardrails(item["query"])
        elapsed = (time.time() - start) * 1000

        results.append({
            "query": item["query"][:60] + "...",
            "expected_intent": item["expected_intent"],
            "is_safe": result["is_safe"],
            "pii_detected": result["pii_detected"],
            "latency_ms": round(elapsed, 2),
        })

    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["is_safe"]),
        "blocked": sum(1 for r in results if not r["is_safe"]),
        "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / len(results), 2),
        "details": results,
    }


def print_report(guardrails_report: dict):
    """Print a formatted evaluation report."""
    console.print("\n[bold cyan]Batch Evaluation Report[/bold cyan]\n")

    # Guardrails results
    table = Table(title="Guardrails Evaluation", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Queries", str(guardrails_report["total"]))
    table.add_row("Passed", str(guardrails_report["passed"]))
    table.add_row("Blocked", str(guardrails_report["blocked"]))
    table.add_row("Avg Latency", f"{guardrails_report['avg_latency_ms']}ms")

    console.print(table)

    # Detail table
    detail_table = Table(title="Query Details", box=box.SIMPLE)
    detail_table.add_column("Query", style="dim", max_width=50)
    detail_table.add_column("Intent", style="cyan")
    detail_table.add_column("Status", style="green")
    detail_table.add_column("PII", style="yellow")

    for r in guardrails_report["details"]:
        status = "✓ Pass" if r["is_safe"] else "✗ Block"
        pii = ", ".join(r["pii_detected"]) if r["pii_detected"] else "-"
        detail_table.add_row(r["query"], r["expected_intent"], status, pii)

    console.print(detail_table)
    console.print()


if __name__ == "__main__":
    dataset = load_test_dataset()
    console.print(f"[dim]Loaded {len(dataset)} test queries[/dim]")

    guardrails_report = run_guardrails_eval(dataset)
    print_report(guardrails_report)

    console.print("[dim]Note: Full pipeline evaluation (with LLM agents) requires GOOGLE_API_KEY or GCP auth.[/dim]")
    console.print("[dim]Run: adk web customer_support_agent — then test queries manually.[/dim]\n")

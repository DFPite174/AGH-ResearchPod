"""
AGH Research Pod Command Line Interface (CLI).
Empowers quant researchers to discover, deconstruct, and replicate quantitative breakthroughs.
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Safe console for Windows GBK compatibility
console = Console(highlight=False, legacy_windows=False)


@click.group()
def main():
    """AGH Research Pod: Tri-Engine Autonomous Opportunity Discovery & Replication Pod."""
    pass


@main.command()
def info():
    """Display system status, integrated engines, and active pipelines."""
    console.print(Panel.fit(
        "[bold cyan]AGH Research Pod (Project Archimedes-AGH)[/bold cyan]\n"
        "[green]Tri-Engine Triad: Academic + GitHub + HuggingFace[/green]\n"
        "Status: [bold green]Online & Operational[/bold green] | Environment: China A-Share & SSE/SZSE Native",
        title="[System Information]",
        border_style="cyan"
    ))
    
    table = Table(title="Integrated Engines & Benchmark Assets", border_style="dim")
    table.add_column("Engine / Asset", style="bold yellow")
    table.add_column("Status", style="green")
    table.add_column("Key Responsibility")
    
    table.add_row("Academic Ingestion", "Active", "arXiv (q-fin), SSRN, CNKI Finance (Economic Quarterly, Journal of Financial Research)")
    table.add_row("GitHub Radar", "Active", "Trending quant repositories, Awesome lists, C++/Python baseline code")
    table.add_row("HuggingFace Radar", "Active", "Time-series foundations, FinNLP weights, open agent spaces")
    table.add_row("Deconstruction Engine", "Active", "Formula LaTeX extraction, implicit friction audit, license screening")
    table.add_row("Replication Sandbox", "Active", "Isolated Docker/gVisor environment with LLM self-healing")
    table.add_row("Benchmark 001", "Verified", "Zheng Zhenlong et al. (2025) Convertible Bond Pricing L/S Strategy")
    table.add_row("Benchmark 002", "Verified", "Zheng Zhenlong & Lin Hai (2004a) CB Pricing & Underpricing Discovery")
    
    console.print(table)


@main.command(name="run-benchmark-001")
def benchmark_001():
    """Execute end-to-end replication of Zheng Zhenlong et al. (2025) Convertible Bond Paper."""
    from benchmarks.benchmark_001_cb_pricing.run_replication import run_benchmark_001
    run_benchmark_001()


@main.command(name="run-benchmark-002")
def benchmark_002():
    """Execute end-to-end replication of Zheng Zhenlong & Lin Hai (2004a) Convertible Bond Paper."""
    from benchmarks.benchmark_002_zheng_lin_2004.run_replication import run_benchmark_002_replication
    run_benchmark_002_replication()


@main.command(name="run-benchmark-003")
def benchmark_003():
    """Execute Plan B NautilusTrader 1.231.0 institutional convertible bond execution & dual ledger audit."""
    from benchmarks.benchmark_003_nautilus_execution.run_replication import run_benchmark
    run_benchmark()


@main.command()
def scan():
    """Trigger tri-engine scan to discover and align latest quantitative research."""
    from agh.ingestion.collector import TriEngineCollector
    from agh.alignment.linker import GraphAlignmentEngine
    
    console.print("[cyan]Triggering A/G/H multi-source polling...[/cyan]")
    collector = TriEngineCollector()
    items = collector.scan_sources()
    
    linker = GraphAlignmentEngine()
    console.print(f"[green]Discovered {len(items)} high-priority insight items.[/green]\n")
    
    for item in items:
        node = linker.align_item(item)
        console.print(Panel(
            f"[bold]Title:[/bold] {node.paper_title}\n"
            f"[bold]Author:[/bold] {node.paper_author} ({node.journal})\n"
            f"[bold]Evidence Chain:[/bold] Academic: [green]Yes[/green] | GitHub: [green]{node.github_repo_url}[/green] | HF: {node.hf_model_id or 'None'}\n"
            f"[bold]Relevance Score:[/bold] [bold yellow]{node.relevance_score}/10.0[/bold yellow]\n"
            f"[bold]Domain Tags:[/bold] {', '.join(node.domain_tags)}",
            title=f"[Opportunity Candidate: {item.source_type.upper()}]",
            border_style="green"
        ))


if __name__ == "__main__":
    main()

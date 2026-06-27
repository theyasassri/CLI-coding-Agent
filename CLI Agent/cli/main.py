# cli/main.py
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table

# Import our backend components built in previous steps
from config.schema import AuditorSettings
from scanner.python_scanner import PythonScanner
from rag.store import VectorStoreManager
from rag.indexer import KnowledgeIndexer

# Initialize Rich console for beautiful terminal formatting
console = Console()

@click.group()
@click.version_option(version="0.1.0", message="Code Auditor Agent CLI - Version %(version)s")
def cli():
    """Autonomous AI Software Quality & Security Auditor CLI Agent.
    
    This agent continuously audits codebases for vulnerabilities, provides conceptual
    context matching using an embedded RAG vector hub, and automates fixes.
    """
    pass

@cli.command(name="init")
def init():
    """Initializes the local hidden workspace system paths and configs."""
    console.print("[bold blue]Initializing Code Auditor workspace settings...[/bold blue]")
    
    # Instantiate the store manager to trigger directory structures creation safely
    store_manager = VectorStoreManager()
    
    console.print(f"[bold green]✓[/bold green] Persistent local vector store created at: [yellow]{store_manager.db_dir}[/yellow]")
    console.print("[bold green]✓[/bold green] Workspace initialized successfully. Run [magenta]auditor index[/magenta] to load rules.")

@cli.command(name="scan")
@click.argument("target_path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
def scan(target_path: str):
    """Executes a local AST code scanning traversal over a targeted workspace directory."""
    console.print(f"[bold blue]Launching security AST analysis scanner on directory: {target_path}[/bold blue]\n")
    
    scanner = PythonScanner()
    findings = scanner.scan(target_path)
    
    if not findings:
        console.print("[bold green]✨ Success! No vulnerabilities or anti-patterns detected in this repository.[/bold green]")
        return

    # Build a clean output summary report table using Rich UI layouts
    table = Table(title=f"Scan Report Summary ({len(findings)} Issues Detected)", title_style="bold magenta")
    table.add_column("File", style="cyan")
    table.add_column("Line:Col", style="inverse")
    table.add_column("Severity", style="bold red")
    table.add_column("CWE ID", style="yellow")
    table.add_column("Description", style="white")

    for f in findings:
        # Style severities cleanly
        sev_color = "red" if f.severity in ["CRITICAL", "HIGH"] else "yellow"
        table.add_row(
            f.file,
            f"{f.line}:{f.col}",
            f"[{sev_color}]{f.severity}[/{sev_color}]",
            f.cwe_id,
            f.description
        )

    console.print(table)

if __name__ == "__main__":
    cli()
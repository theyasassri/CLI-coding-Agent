# cli/main.py
import sys
from pathlib import Path
import click
from rich.console import Console


# Import our backend components built in previous steps
from config import AuditorSettings
from rag import VectorStoreManager, KnowledgeIndexer
from cli.commands.audit import execute_audit_pipeline

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
@click.option("--dry-run", is_flag=True, help="Preview identified code anomalies without running AI correction cycles.")
def scan(target_path: str, dry_run:bool):
    """Executes a local AST code scanning traversal over a targeted workspace directory."""
    execute_audit_pipeline(target_path=target_path, dry_run=dry_run)
    
if __name__ == "__main__":
    cli()
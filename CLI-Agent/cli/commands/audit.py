from pathlib import Path
import os
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import our cross-module layers
from scanner import PythonScanner
from rag import VectorStoreManager
from agent import CodeRepairOrchestrator

console = Console()

def execute_audit_pipeline(target_path: str, dry_run: bool):
    """
    Main background operation that connects the AST scanner findings 
    RAG database context matching, and the live AI healing engine loop.
    """
    path_obj = Path(target_path).resolve()
    
    # 1. Initialize our visual progress bars using Rich
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Task Step A: Abstract Syntax Tree Extraction
        scan_task = progress.add_task(description="[cyan]Parsing code into Abstract Syntax Trees...[/cyan]", total=None)
        scanner = PythonScanner()
        findings = scanner.scan(str(path_obj))
        progress.update(scan_task, completed=True, description="[green]✓ AST Code Scanning Completed.[/green]")
        
        if not findings:
            console.print("\n[bold green] Success! Your codebase matches all safety thresholds.[/bold green]")
            return

        console.print(f"\n[bold yellow] Identified {len(findings)} security anti-patterns. Querying memory buffers...[/bold yellow]\n")

        # Task Step B: Vector Store Querying (RAG Context Enrichment)
        rag_task = progress.add_task(description="[magenta]Fetching matching structural guidelines from ChromaDB...[/magenta]", total=None)
        
        try:
            store_manager = VectorStoreManager()
            collection = store_manager.get_or_create_knowledge_collection()
            
            # Loop over findings to enrich them with background documentation context
            for finding in findings:
                # Query our vector store using the CWE description text as the query vector
                results = collection.query(
                    query_texts=[finding.description],
                    n_results=1
                )
                
                # If a contextual vector documentation block matches, attach it directly to the finding
                if results and results['documents'] and results['documents'][0]:
                    matched_doc = results['documents'][0][0]
                    finding.fix_hint += f"\n\n[Reference Standard]:\n{matched_doc}"
                    
        except Exception as e:
            # If the vector database isn't initialized yet, fail gracefully and fall back to native fixes
            progress.update(rag_task, description="[yellow]! Vector store uninitialized. Skipping RAG integration.[/yellow]")
            
        progress.update(rag_task, completed=True, description="[green]✓ Retrieval-Augmented Context synthesis finished.[/green]")

    # 2. Render final summary blocks or pass directly downstream to the LLM layer
    for idx, f in enumerate(findings, 1):
        console.print(f"\n[bold red]Vulnerability #{idx}: {f.cwe_id} ({f.severity})[/bold red]")
        console.print(f"[bold white]Location:[/bold white] {f.file}:{f.line}")
        console.print(f"[bold white]Issue:[/bold white] {f.description}")
        console.print(f"[bold green]Suggested Patching Strategy:[/bold green]\n{f.fix_hint}")
        console.print("-" * 60)

    if dry_run:
        console.print("\n[bold yellow] --dry-run active: AI agent structural autofix cycles skipped.[/bold yellow]")
    else:
        if not os.getenv("GEMINI_API_KEY"):
            console.print("\n[bold red]Execution Halted: 'GEMINI_API_KEY' environment variable not found.[/bold red]")
            console.print("[dim]Please set the key via: $env:GEMINI_API_KEY='your_key' (PowerShell) or use --dry-run[/dim]\n")
            return
        console.print("\n[bold blue] Next Step: Passing payloads into the LLM Self-Healing Iteration Loop...[/bold blue]")
        # This will trigger our agent/orchestrator.py code down the road!
        orchestrator = CodeRepairOrchestrator(repo_path=str(path_obj))
        orchestrator.execute_self_healing_loop(findings=findings)
 

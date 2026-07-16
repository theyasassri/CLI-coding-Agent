# git/pr_manager.py
import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()

class GitHubPRManager:
    def __init__(self, repo_path: str):
        self.repo_path = str(Path(repo_path).resolve())

    def _run_git_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Helper to safely execute shell subsystems inside the local repo context."""
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )

    def create_remediation_branch(self, branch_name: str) -> None:
        """Creates and switches to an isolated safety sandbox branch for modifications."""
        try:
            console.print(f"[dim]Creating unique working branch: {branch_name}...[/dim]")
            # Checkout -b switches cleanly to a brand new target branch reference
            self._run_git_command(["checkout", "-b", branch_name])
        except subprocess.CalledProcessError:
            # Fallback if the branch reference already exists locally
            self._run_git_command(["checkout", branch_name])

    def commit_and_push_changes(self, branch_name: str, message: str) -> bool:
        """Stages modified files, builds a verification commit, and pushes upstream."""
        try:
            # Stage all AI-remediated source changes
            self._run_git_command(["add", "."])
            
            # Check if there are actual diffs to commit to prevent empty tree failures
            status = self._run_git_command(["status", "--porcelain"])
            if not status.stdout.strip():
                console.print("[yellow]No distinct code alterations found. Skipping commit layer.[/yellow]")
                return False

            self._run_git_command(["commit", "-m", message])
            console.print(f"[green]Remediation commit created successfully.[/green]")
            
            # Push changes directly up to the origin workspace
            self._run_git_command(["push", "--set-upstream", "origin", branch_name])
            return True
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Git Operation Failure:[/bold red] {e.stderr}")
            return False

    def generate_github_pr(self, title: str, body: str, head_branch: str, base_branch: str = "main") -> Optional[str]:
        """
        Uses the official GitHub CLI ('gh') installed on the machine 
        to programmatically initialize a Pull Request.
        """
        try:
            console.print("  Pull Request execution triggered. Dispatching GitHub API call...")
            
            # Construct the execution layout leveraging the external 'gh' subsystem tool
            cmd = [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--head", head_branch,
                "--base", base_branch
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            pr_url = result.stdout.strip()
            console.print(f"[bold green]Pull Request successfully deployed![/bold green]")
            return pr_url
            
        except FileNotFoundError:
            console.print("[yellow]Notice: 'gh' CLI missing on runtime machine. Code preserved locally on branch.[/yellow]")
            return None
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]GitHub API Generation Error:[/bold red] {e.stderr}")
            return None
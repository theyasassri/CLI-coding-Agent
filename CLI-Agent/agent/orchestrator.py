# agent/orchestrator.py
import os
from pathlib import Path
from typing import List, Dict, Any, cast
from anthropic import Anthropic
from anthropic.types import MessageParam, ToolParam, TextBlock
from rich.console import Console

# Import our tool executors and tool metadata schemas
from agent.tools import read_file_content, write_file_content, AVAILABLE_TOOLS_MANIFEST
from scanner.base import Finding

console = Console()

class CodeRepairOrchestrator:
    def __init__(self, repo_path: str):
        self.repo_path = str(Path(repo_path).resolve())
        # Retrieve the API key securely from environment variables
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("CRITICAL error: 'ANTHROPIC_API_KEY' environment variable is missing.")
            
        self.client = Anthropic(api_key=self.api_key)
        # We target Claude 3.5 Sonnet for precise code parsing capabilities
        self.model = "claude-3-5-sonnet-20241022"

    def execute_self_healing_loop(self, findings: List[Finding], max_iterations: int = 3) -> bool:
        """
        Iterates over code vulnerabilities, hands them to Claude, 
        and executes real-time patches until the code is secure.
        """
        console.print(f"\n[bold purple] Activating AI Core. Iteration limit: {max_iterations}[/bold purple]")
        
        for idx, finding in enumerate(findings, 1):
            console.print(f"\n[bold cyan]Processing Defect #{idx}: {finding.cwe_id} ({finding.file})[/bold cyan]")
            
            # 1. Build a robust system instruction context prompt
            system_prompt = (
                "You are an elite, autonomous AI security remediation engineer.\n"
                "Your objective is to fix vulnerabilities detected via static AST analysis.\n"
                "Always use the 'read_file_content' tool to fully read code files before patching them.\n"
                "Once you have analyzed the issue, apply clean corrections using 'write_file_patch'.\n"
                "Ensure your code edits adhere strictly to clean architectural conventions."
            )
            
            # 2. Set up initial conversation history with explicit Anthropic type tracking
            messages: List[MessageParam] = [
                {
                    "role": "user",
                    "content": (
                        f"Vulnerability Detected:\n"
                        f"- File: {finding.file}\n"
                        f"- Line: {finding.line}, Column: {finding.col}\n"
                        f"- Severity: {finding.severity}\n"
                        f"- Issue: {finding.description}\n"
                        f"- Guidance context: {finding.fix_hint}\n\n"
                        f"Please inspect this file and completely patch the vulnerability."
                    )
                }
            ]
            
            iteration = 0
            while iteration < max_iterations:
                iteration += 1
                console.print(f"  └─ [dim]Agent Query Phase (Cycle {iteration}/{max_iterations})...[/dim]")
                
                # Request response payload from Anthropic API endpoint with clean casting
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    tools=cast(List[ToolParam], AVAILABLE_TOOLS_MANIFEST),
                    messages=messages
                )
                
                # Check if the LLM desires to invoke a tool execution block
                if response.stop_reason == "tool_use":
                    # Append Claude's raw thinking/tool response to keep history balanced
                    messages.append({"role": "assistant", "content": cast(Any, response.content)})
                    
                    tool_outputs: List[Dict[str, Any]] = []
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_args = cast(Dict[str, Any], block.input)
                            tool_call_id = block.id
                            
                            console.print(f"[yellow]Claude requests tool execution:[/yellow] [magenta]{tool_name}()[/magenta]")
                            
                            # Extract parameters safely as typed strings to pass to tool methods
                            relative_path = str(tool_args.get("relative_path", ""))
                            
                            # Execute the appropriate native python tool function locally
                            if tool_name == "read_file_content":
                                result = read_file_content(relative_path, self.repo_path)
                            elif tool_name == "write_file_content":
                                updated_content = str(tool_args.get("updated_content", ""))
                                result = write_file_content(relative_path, self.repo_path, updated_content)
                            else:
                                result = f"Error: Unknown tool function name '{tool_name}'."
                                
                            # Package the output format to pass back to the API container
                            tool_outputs.append({
                                "type": "tool_result",
                                "tool_use_id": tool_call_id,
                                "content": result
                            })
                    
                    # Update our message history arrays with the tool outputs
                    messages.append({"role": "user", "content": cast(Any, tool_outputs)})
                else:
                    # Safely locate the plain TextBlock inside the content array to extract the final summary text
                    final_text = ""
                    for block in response.content:
                        if isinstance(block, TextBlock):
                            final_text = block.text
                            break
                    
                    console.print(f"[bold green]✓ Agent concluded repairs:[/bold green] {final_text}")
                    break
                    
        return True
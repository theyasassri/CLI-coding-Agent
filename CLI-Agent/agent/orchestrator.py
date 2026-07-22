# agent/orchestrator.py
import os
from pathlib import Path
from typing import List, Dict, Any
from google import genai
from google.genai import types
from rich.console import Console
import difflib

# Import our tool executors and tool metadata schemas
from agent.tools import read_file_content, write_file_content, validate_patch_integrity
from scanner.base import Finding

console = Console()

class CodeRepairOrchestrator:
    def __init__(self, repo_path: str):
        self.repo_path = str(Path(repo_path).resolve())
        # Retrieve the free Gemini key securely from environment variables
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("CRITICAL error: 'GEMINI_API_KEY' environment variable is missing.")
            
        # Initialize the modern official Google GenAI client framework
        self.client = genai.Client(api_key=self.api_key)
        # We target gemini-2.5-flash for incredibly high speed and strong code repair skills
        self.model = "gemini-2.5-flash"

    def execute_self_healing_loop(self, findings: List[Finding], max_iterations: int = 3) -> bool:
        """
        Iterates over code vulnerabilities, hands them to Gemini, 
        and executes real-time patches using native tool declarations.
        """
        console.print(f"\n[bold purple] Activating Gemini AI Core (Self-Validation Enabled). Max Cycles: {max_iterations}[/bold purple]")
        
        # Mapping key names to python functions for execution
        tool_functions = {
            "read_file_content": read_file_content,
            "write_file_content": write_file_content
        }
        
        for idx, finding in enumerate(findings, 1):
            console.print(f"\n[bold cyan]Processing Defect #{idx}: {finding.cwe_id} ({finding.file})[/bold cyan]")
            
            system_prompt = (
                "You are an elite, autonomous AI security remediation engineer.\n"
                "Your objective is to fix vulnerabilities detected via static AST analysis.\n"
                "Always use the 'read_file_content' tool to fully read code files before patching them.\n"
                "Once you have analyzed the issue, apply clean corrections using 'write_file_patch'.\n"
                "Ensure your code edits adhere strictly to clean architectural conventions."
            )
            
            # Formulate the developer configuration schema object
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                tools=[read_file_content, write_file_content]
            )
            
            # Gemini handles multi-turn conversations cleanly using explicit chat sessions
            chat = self.client.chats.create(model=self.model, config=config)

            target_file_path = str(Path(finding.file).as_posix())
            if not target_file_path.startswith("sandbox/") and Path(self.repo_path, "sandbox", target_file_path).exists():
                target_file_path = f"sandbox/{target_file_path}"

            user_message = (
                f"Vulnerability Detected:\n"
                f"- Relative Path: {target_file_path}\n"
                f"- Line: {finding.line}, Column: {finding.col}\n"
                f"- Severity: {finding.severity}\n"
                f"- Issue: {finding.description}\n"
                f"- Guidance context: {finding.fix_hint}\n\n"
                f"Please inspect the file at '{target_file_path}' using 'read_file_content' and completely patch the vulnerability using 'write_file_content',"
                f"and ensure the resulting code compiles cleanly."
            )
            
            iteration = 0
            current_input: Any = user_message
            
            while iteration < max_iterations:
                iteration += 1
                console.print(f"  └─ [dim]Gemini Query Phase (Cycle {iteration}/{max_iterations})...[/dim]")
                
                # Transmit history turn packet downstream to the chat buffer endpoint
                response = chat.send_message(current_input)
                
                # Check if Gemini wants to call any local system tools
                if response.function_calls:
                    tool_responses = []
                    
                    for call in response.function_calls:
                        tool_name = call.name or "unknown_tool"
                        # Explicitly ensure call.args is treated as a dictionary, preventing None errors
                        tool_args = call.args if call.args is not None else {}
                        
                        console.print(f"[yellow]Gemini requests tool execution:[/yellow] [magenta]{tool_name}()[/magenta]")
                        
                        # Initialize result to prevent unbound variable issues
                        result = ""
                        if tool_name in tool_functions:
                            # Safely extract paths and parameters with default fallbacks
                            relative_path = str(tool_args.get("relative_path", ""))
                            
                            # Execute local file system adjustments dynamically
                            if tool_name == "read_file_content":
                                result = read_file_content(relative_path, self.repo_path)
                            elif tool_name == "write_file_content":
                                updated_content = str(tool_args.get("updated_content", ""))
                                old_content = read_file_content(relative_path, self.repo_path)
                                write_res = write_file_content(relative_path, self.repo_path, updated_content)

                                console.print("\n[bold yellow]---Propose Code Patch Diff ---[/bold yellow]")
                                diff = difflib.unified_diff(
                                    old_content.splitlines(),
                                    updated_content.splitlines(),
                                    fromfile="a/" + relative_path,
                                    tofile="b/" + relative_path,
                                    lineterm=""
                                )

                                for line in diff:
                                    if line.startswith('+') and not line.startswith('+++'):
                                        console.print(f"[green]{line}[/green]")
                                    elif line.startswith('-') and not line.startswith('---'):
                                        console.print(f"[red]{line}[/red]")
                                    elif line.startswith('@'):
                                        console.print(f"[cyan]{line}[/cyan]")
                                    else:
                                        console.print(f"[dim]{line}[/dim]")

                                console.print("[bold yellow]====================[/bold yellow]\n")

                                console.print(f"[dim]Executing automated syntax and validation check...[/dim]")
                                val_check = validate_patch_integrity(relative_path, self.repo_path)

                                if val_check["success"]:
                                    console.print(f"[green]{val_check['feedback']}[/green]")
                                    result = f"{write_res}\n\nValidation Passed: {val_check['feedback']}"
                                else:
                                    console.print(f"[red]{val_check['feedback']}[/red]")
                                    result = f"{write_res}\n\nCRITICAL VALIDATION ERROR : \n{val_check['feedback']}\nPlease fix this error and write a valid patch."
                        else:
                            result = f"Error: Function {tool_name} is unhandled."
                        
                        # Pack tool response back in Gemini's format
                        tool_responses.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": result}
                            )
                        )
                    
                    # Set the next loop input to be the tool outputs
                    current_input = tool_responses
                else:
                    console.print(f"[bold green] Gemini concluded repairs:[/bold green] {response.text}")
                    break
                    
        return True
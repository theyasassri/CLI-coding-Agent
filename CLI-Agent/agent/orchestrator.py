# agent/orchestrator.py
import os
from pathlib import Path
from typing import List, Dict, Any
from google import genai
from google.genai import types
from rich.console import Console

# Import our tool executors and tool metadata schemas
from agent.tools import read_file_content, write_file_content
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
        console.print(f"\n[bold purple] Activating Gemini AI Core. Iteration limit: {max_iterations}[/bold purple]")
        
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
            
            user_message = (
                f"Vulnerability Detected:\n"
                f"- File: {finding.file}\n"
                f"- Line: {finding.line}, Column: {finding.col}\n"
                f"- Severity: {finding.severity}\n"
                f"- Issue: {finding.description}\n"
                f"- Guidance context: {finding.fix_hint}\n\n"
                f"Please inspect this file and completely patch the vulnerability."
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
                                result = write_file_content(relative_path, self.repo_path, updated_content)
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
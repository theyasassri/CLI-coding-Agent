from pathlib import Path
import json

def read_file_content(relative_path:str, root_repo_path:str) -> str:
    """
    Allows the AI agent to read the raw content of a file in the workspace."""

    try:
        full_path = Path(root_repo_path) / relative_path
        if not full_path.exists():
            return f"Error: File '{relative_path}' not found at path destination."
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file context: {str(e)}"
    
def write_file_content(relative_path: str, root_repo_path: str, updated_content: str) -> str:
    """
    Allows the AI agent to write fully corrected code updated back to the disk."""
    try: 
        full_path = Path(root_repo_path) / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(updated_content, encoding="utf-8")
        return f"Success: Clean patch securely written to {relative_path}."
    except Exception as e:
        return f"Error writing patch updates to file asset: {str(e)}"
    
AVAILABLE_TOOLS_MANIFEST = [
    {
        "name": "read_file_content",
        "description": "Reads the entire text payload layout of a targeted system file inside the working repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "he repository relative path to the target source asset (e.g., 'auth/login.py')."
                }
            },
            "required": ["relative_path"]
        }
    },
    {
        "name": "write_file_patch",
        "description": "Overwrites or updates code contents for a targeted file asset inside the working repository workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "relative_path": {
                    "type": "string",
                    "description": "The repository relative file path destination to save modified contents."
                },
                "updated_content": {
                    "type": "string",
                    "description": "The complete, revised code file content payload with security repairs implemented."
                }
            },
            "required": ["relative_path", "updated_content"]
        }
    }]
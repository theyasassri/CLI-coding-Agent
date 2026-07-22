from pathlib import Path
import json

def read_file_content(relative_path:str, root_repo_path:str) -> str:
    """
    Reads and returns the contents of a specified file relatve to the root repository."""
    base_path = Path(root_repo_path).resolve()
    target_path = (base_path / relative_path).resolve()

    if not target_path.exists():
        sandbox_path = (base_path / "sandbox" / relative_path).resolve()
        if sandbox_path.exists():
            target_path = sandbox_path
    if not target_path.exists():
        return f"Error: File '{relative_path}' not found at path destination."
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

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
from pathlib import Path
import json
import subprocess
import sys

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
    """Writes updated content to a specified target file inside the repository."""
    base_path = Path(root_repo_path).resolve()
    target_path = (base_path / relative_path).resolve()

    if not target_path.exists():
        sandbox_path = (base_path / "sandbox" / relative_path).resolve()
        if sandbox_path.exists():
            target_path = sandbox_path

    try: 
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        return f"File successfully updated at: {target_path.relative_to(base_path)}"
    except Exception as e:
        return f"Error writing patch to file {str(e)}"
    
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

def validate_patch_integrity(relative_path: str, root_repo_path: str) -> dict:
    """
    Validates that a patched file contains valid Python syntax and doesn't break until tests.
    Returns a dictionary with 'success' (bool) and 'feedback' (str).
    """
    base_path = Path(root_repo_path).resolve()
    target_path = (base_path / relative_path).resolve()

    if not target_path.exists():
        target_path = (base_path / "sandbox" / relative_path).resolve()

    if not target_path.exists():
        return {
            "success": False,
            "feedback": f"Validation Failed: Target file '{relative_path}' could not be resolved."
        }

    try:
        cmd = [sys.executable, "-m", "py_compile", str(target_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode !=0:
            return {
                "success": False,
                "feedback": f"SYNTAX ERROR DETECTED in {relative_path}:\n{res.stderr.strip()}"
            }

    except Exception as e:
        return {"success": False, " feedback": f" Compilation check error: {str(e)}"}


    tests_dir = base_path / "tests"
    if tests_dir.exists():
        try:
            test_cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir)]
            test_res = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
            if test_res.returncode !=0:
                return {
                    "success": False,
                    "feedback": f"UNIT TESTS FAILED after patch:\n{test_res.stderr.strip()}"
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "feedback": "Validation Error: Unit tests timed out"}
        except Exception as e:
            return {"success": False, "feedback": f"Test runner execution error: {str(e)}"}

    return {
        "success": True,
        "feedback": f"Validation Successful: '{relative_path}' passes syntax compilation and test suites." 
    }
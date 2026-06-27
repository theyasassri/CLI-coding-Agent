import ast
from pathlib import Path
from typing import List
from scanner.base import BaseScanner, Finding

class SecurityNodeVisitor(ast.NodeVisitor):
    """
    Walks the Abstract Syntax Tree of a Python file looking for specific dangerous node configurations (anti patterns).
    """
    def __init__(self, file_relative_path: str):
        self.findings: List[Finding] = []
        self.file_path = file_relative_path
    
    def visit_Call(self, node: ast.Call):
        """ Triggered whenever the parser encounters an actie function call. """
        
        #pattern 1 : Check for dangerous dynamic excecution via eval()
        if isinstance(node.func, ast.Name) and node.func.id == "eval":
            self.findings.append(
                Finding(
                    file=self.file_path,
                    line=node.lineno,
                    col=node.col_offset,
                    severity="CRITICAL",
                    cwe_id="CWE-95",
                    description="Direct call to eval() ddetected. This permits arbitrary remote code execution if input is untrusted.",
                    fix_hint="Replace eval() with literal_eval() from the built-in 'ast' module, or rewrite using safe dictionary lookups."
                )
            )

        #pattern 2 : check for command ijection vulnerabilities via subprocess.run(...,shell=TRUE)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                # Inspect keyword arguments for the presence of shell=True
                for kwarg in node.keywords:
                    if kwarg.arg == "shell" and isinstance(kwarg.value, ast.Constant) and kwarg.value.value is True:
                        self.findings.append(
                            Finding(
                                file=self.file_path,
                                line=node.lineno,
                                col=node.col_offset,
                                severity="HIGH",
                                cwe_id="CWE-78",
                                description="Subprocess executed with shell=True. This introduces a servere OS command injection vulnerability.",
                                fix_hint="Remove shell=True and pass the command arguements as a structured list: e.g., ['ls','-la'] instead of'ls -la'."
                            )
                        )

        # Propogate downwards to keep exploring deeper nested elements in this syntax tree.
        self.generic_visit(node)

class PythonScanner(BaseScanner):
    def scan(self, repo_path: str) -> List[Finding]:
        all_findings: List[Finding] = []
        root_dir = Path(repo_path)

        # Recursively search for target source files while skipping dependency noise
        for path in root_dir.rglob("*.py"):
            if any(part in path.parts for part in["node_modules", "tests", ".venv", ".git"]):
                continue
            try:
                code_content = path.read_text(encoding="utf-8")
                #compile raw text structure cleanly directly into an AST object hierarchy
                tree = ast.parse(code_content, filename=str(path))

                #Run our customized node parsing visitor rules
                relative_path = str(path.relative_to(root_dir))
                visitor = SecurityNodeVisitor(relative_path)
                visitor.visit(tree)

                all_findings.extend(visitor.findings)
            except Exception as e:
                #safely skip un-parasible corrupt source assests or syntax deviations
                print(f"Skipping file{path} due to parsing error: {e}")
                
        return all_findings
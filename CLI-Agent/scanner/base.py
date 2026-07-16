from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Finding:
    file: str
    line:int
    col:int
    severity: str #critical, high,medium,low
    cwe_id:str #eg:- CWE-78, CWE-89
    description: str
    fix_hint: str

    def to_dict(self) -> dict:
        """Helper method to serialize findings to JSON/dictionaries easily."""
        return asdict(self)
    
class BaseScanner(ABC):
    @abstractmethod
    def scan(self, repo_path: str) -> List[Finding]:
        
        """
        Traverses the repository path and returns a structured list of security or quality findings. Must be imlemented by every language language engine.
        """
        pass


#2026-06-26##
##1. The Abstract Base Scanner (scanner/base.py)
##We want our auditor to scale to Go, Rust, or Java down the road without breaking our main execution pipeline. To do this, we use the Strategy Design Pattern by defining an Abstract Base Class (ABC) that forces every language scanner to return data in the exact same format.
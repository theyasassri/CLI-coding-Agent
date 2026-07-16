# config/schema.py
from pydantic import BaseModel, Field
from typing import List

class ScannerConfig(BaseModel):
    languages: List[str] = Field(default_factory=lambda: ["python", "nodejs", "react"])
    exclude: List[str] = Field(default_factory=lambda: ["tests/", "node_modules/", ".venv/", "env/"])
    min_severity: str = "medium"

class QualityThresholds(BaseModel):
    min_coverage: int = Field(default=80, ge=0, le=100)
    max_complexity: int = Field(default=10, ge=1)
    max_defect_density: float = Field(default=0.1)

class AgentConfig(BaseModel):
    max_iterations: int = Field(default=20, ge=1)
    model: str = "claude-sonnet-4-6"
    auto_fix: bool = True

class GitHubConfig(BaseModel):
    auto_pr: bool = True
    base_branch: str = "main"

class AuditorSettings(BaseModel):
    version: str = "1"
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    quality: QualityThresholds = Field(default_factory=QualityThresholds)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)

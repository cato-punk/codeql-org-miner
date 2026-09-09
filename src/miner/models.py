from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AnalysisStatus(str, Enum):
    ANALYZED = "analyzed"
    FAILED_CLONE = "failed_clone"
    UNSUPPORTED_LANGUAGE = "unsupported"
    FAILED_DB_CREATE = "failed_db_create"
    FAILED_ANALYSIS = "failed_analysis"

class Finding(BaseModel):
    rule_id: str
    severity: str
    message: str
    file: str
    start_line: int

    def __lt__(self, other: "Finding") -> bool:
        return (self.file, self.start_line, self.rule_id) < (other.file, other.start_line, other.rule_id)

class RepositoryResult(BaseModel):
    name: str
    url: str
    status: AnalysisStatus
    error_reason: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    findings: List[Finding] = Field(default_factory=list)

class Summary(BaseModel):
    repositories: int
    analyzed: int
    failed: int
    unsupported: int
    findings: int

class OrganizationReport(BaseModel):
    organization: str
    summary: Summary
    repositories: List[RepositoryResult]

    def sort_results(self) -> None:
        """Ordena repositorios y hallazgos de forma alfabética y determinista."""
        self.repositories.sort(key=lambda r: r.name)
        for repo in self.repositories:
            repo.findings.sort()
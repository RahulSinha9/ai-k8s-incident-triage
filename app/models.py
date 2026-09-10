from typing import List

from pydantic import BaseModel, Field


class PodEvidence(BaseModel):
    namespace: str
    pod: str
    phase: str = "Unknown"
    restart_count: int = 0
    waiting_reasons: List[str] = Field(default_factory=list)
    terminated_reasons: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    logs: str = ""


class Diagnosis(BaseModel):
    namespace: str
    pod: str
    severity: str
    category: str
    summary: str
    evidence: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class TriageReport(BaseModel):
    namespace: str
    incidents: List[Diagnosis] = Field(default_factory=list)
    healthy_pods: int = 0
    analyzed_pods: int = 0

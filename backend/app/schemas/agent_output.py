from pydantic import BaseModel, Field, field_validator
from typing import Literal


class EvidenceItem(BaseModel):
    claim: str = Field(..., min_length=1)
    citation: str = Field(..., min_length=1)


class AgentOutput(BaseModel):
    agent_name: str = Field(..., min_length=1)
    pillar: str = Field(..., min_length=1)
    sub_score: float = Field(..., ge=0.0, le=100.0)
    confidence: Literal["Low", "Medium", "High"]
    evidence: list[EvidenceItem] = Field(..., min_length=1)
    data_completeness_pct: float = Field(..., ge=0.0, le=100.0)
    raw_findings: dict = Field(default_factory=dict)

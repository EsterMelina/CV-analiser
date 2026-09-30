from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RequirementBreakdownItem(BaseModel):
    requirement_id: int
    name: str
    category: str
    is_mandatory: bool
    weight: float
    met: bool
    match_score: float
    contribution: float
    evidence: str | None = None


class CandidateMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    overall_score: float
    recommendation_label: str
    breakdown: list[RequirementBreakdownItem]
    mandatory_missing: list[str]
    computed_at: datetime
    criteria_version: int = 1
    resume_id: int | None = None
    stale: bool = False


class RankingItem(BaseModel):
    analysis_id: int | None = None
    analysis_execution_id: str | None = None
    analysis_method: str | None = None
    analysis_error: str | None = None
    application_id: int
    candidate_id: int
    candidate_name: str
    candidate_email: str
    score: float | None
    recommendation_label: str | None
    mandatory_missing: list[str] = []
    status: str
    analysis_status: str = "pending"
    stale: bool = False

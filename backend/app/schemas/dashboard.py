from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_jobs: int
    active_jobs: int
    closed_jobs: int
    total_candidates: int
    total_applications: int
    analyzed_applications: int
    recommended_applications: int
    interview_selected_applications: int
    pending_evaluation_applications: int


class JobApplicationCount(BaseModel):
    job_id: int
    job_title: str
    job_code: str
    total_applications: int
    recommended: int

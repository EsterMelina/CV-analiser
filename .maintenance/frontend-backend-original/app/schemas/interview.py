from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.interview import InterviewResult, RecruiterRating


class InterviewCreate(BaseModel):
    scheduled_at: datetime
    interviewers: str | None = None
    location_or_link: str | None = None
    notes: str | None = None


class InterviewResultUpdate(BaseModel):
    result: InterviewResult
    result_notes: str | None = None


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    scheduled_at: datetime
    interviewers: str | None = None
    location_or_link: str | None = None
    notes: str | None = None
    result: InterviewResult
    result_notes: str | None = None
    created_at: datetime


class RecruiterFeedbackCreate(BaseModel):
    system_recommended: bool = False
    selected_for_interview: bool = False
    hired: bool = False
    rating: RecruiterRating | None = None
    comments: str | None = None


class RecruiterFeedbackRead(RecruiterFeedbackCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

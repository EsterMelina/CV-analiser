from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.application import ApplicationSource, ApplicationStatus


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None


class CandidateCreate(CandidateBase):
    pass


class CandidateRead(CandidateBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    content_type: str | None = None
    file_size_bytes: int | None = None
    uploaded_at: datetime


class ApplicationCreate(BaseModel):
    job_id: int
    candidate: CandidateCreate
    source: ApplicationSource = ApplicationSource.UPLOAD


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    recruiter_notes: str | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    candidate_id: int
    job_id: int
    source: ApplicationSource
    status: ApplicationStatus
    score: float | None = None
    recruiter_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationDetailRead(ApplicationRead):
    candidate: CandidateRead
    resumes: list[ResumeRead] = []

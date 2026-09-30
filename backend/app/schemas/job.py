from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus, JobType, JobModality
from app.schemas.job_requirement import JobRequirementRead


class JobBase(BaseModel):
    title: str
    code: str
    description: str
    department: str | None = None
    location: str | None = None
    job_type: JobType = JobType.FULL_TIME
    modality: JobModality = JobModality.ON_SITE
    min_experience_years: int = Field(default=0, ge=0)
    education_level: str | None = None


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = None
    description: str | None = None
    department: str | None = None
    location: str | None = None
    job_type: JobType | None = None
    modality: JobModality | None = None
    min_experience_years: int | None = Field(default=None, ge=0)
    education_level: str | None = None


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criteria_version: int = 1
    company_id: int
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    closed_at: datetime | None = None


class JobDetailRead(JobRead):
    requirements: list[JobRequirementRead] = []


class JobListItem(BaseModel):
    """Versão resumida para listagens (evita carregar requisitos completos)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    code: str
    status: JobStatus
    department: str | None = None
    location: str | None = None
    created_at: datetime

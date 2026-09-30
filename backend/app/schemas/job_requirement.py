from pydantic import BaseModel, ConfigDict, Field

from app.models.job_requirement import RequirementCategory, RequirementLevel


class JobRequirementBase(BaseModel):
    name: str
    description: str | None = None
    category: RequirementCategory = RequirementCategory.OTHER
    weight: float = Field(default=0.0, ge=0.0, le=1.0)
    expected_level: RequirementLevel = RequirementLevel.INTERMEDIATE
    is_mandatory: bool = False


class JobRequirementCreate(JobRequirementBase):
    pass


class JobRequirementUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: RequirementCategory | None = None
    weight: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_level: RequirementLevel | None = None
    is_mandatory: bool | None = None


class JobRequirementRead(JobRequirementBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int

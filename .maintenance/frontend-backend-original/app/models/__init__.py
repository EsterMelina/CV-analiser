"""
Importa todos os modelos ORM para que fiquem registados em Base.metadata
antes de qualquer chamada a Base.metadata.create_all() ou Alembic autogenerate.
"""
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus, JobType, JobModality
from app.models.job_requirement import JobRequirement, RequirementCategory, RequirementLevel
from app.models.candidate import Candidate
from app.models.application import Application, Resume, ApplicationSource, ApplicationStatus
from app.models.candidate_profile import (
    CandidateEducation, CandidateExperience, CandidateSkill,
    CandidateCertification, CandidateLanguage, CandidateProject, CandidateMatch,
)
from app.models.interview import Interview, InterviewResult, RecruiterFeedback, RecruiterRating
from app.models.email_integration import (
    EmailAccount, EmailProviderType, EmailAccountStatus,
    EmailMessage, EmailAttachment, AttachmentClassification,
)
from app.models.processing_log import ProcessingLog, ProcessingSource, ProcessingStatus

__all__ = [
    "Company",
    "User", "UserRole",
    "Job", "JobStatus", "JobType", "JobModality",
    "JobRequirement", "RequirementCategory", "RequirementLevel",
    "Candidate",
    "Application", "Resume", "ApplicationSource", "ApplicationStatus",
    "CandidateEducation", "CandidateExperience", "CandidateSkill",
    "CandidateCertification", "CandidateLanguage", "CandidateProject", "CandidateMatch",
    "Interview", "InterviewResult", "RecruiterFeedback", "RecruiterRating",
    "EmailAccount", "EmailProviderType", "EmailAccountStatus",
    "EmailMessage", "EmailAttachment", "AttachmentClassification",
    "ProcessingLog", "ProcessingSource", "ProcessingStatus",
]

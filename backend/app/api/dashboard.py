from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.models.application import Application, ApplicationStatus
from app.models.candidate_profile import CandidateMatch
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardSummary, JobApplicationCount
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

PENDING_STATUSES = [
    ApplicationStatus.RECEIVED, ApplicationStatus.IN_ANALYSIS,
    ApplicationStatus.ANALYZED, ApplicationStatus.IN_EVALUATION,
]


def _jobs_query(db: Session, current_user: User):
    query = db.query(Job)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Job.company_id == current_user.company_id)
    return query


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job_ids = [j.id for j in _jobs_query(db, current_user).with_entities(Job.id).all()]

    total_jobs = len(job_ids)
    active_jobs = _jobs_query(db, current_user).filter(Job.status == JobStatus.PUBLISHED).count()
    closed_jobs = _jobs_query(db, current_user).filter(Job.status == JobStatus.CLOSED).count()

    if not job_ids:
        return DashboardSummary(
            total_jobs=0, active_jobs=0, closed_jobs=0, total_candidates=0,
            total_applications=0, analyzed_applications=0, recommended_applications=0,
            interview_selected_applications=0, pending_evaluation_applications=0,
        )

    applications_query = db.query(Application).filter(Application.job_id.in_(job_ids))
    total_applications = applications_query.count()
    total_candidates = applications_query.with_entities(Application.candidate_id).distinct().count()

    analyzed_applications = (
        db.query(CandidateMatch)
        .join(Application, CandidateMatch.application_id == Application.id)
        .filter(Application.job_id.in_(job_ids))
        .count()
    )
    recommended_applications = (
        db.query(CandidateMatch)
        .join(Application, CandidateMatch.application_id == Application.id)
        .filter(Application.job_id.in_(job_ids), CandidateMatch.recommendation_label == "Recomendado")
        .count()
    )
    interview_selected_applications = applications_query.filter(
        Application.status == ApplicationStatus.INTERVIEW_SELECTED
    ).count()
    pending_evaluation_applications = applications_query.filter(
        Application.status.in_(PENDING_STATUSES)
    ).count()

    return DashboardSummary(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        closed_jobs=closed_jobs,
        total_candidates=total_candidates,
        total_applications=total_applications,
        analyzed_applications=analyzed_applications,
        recommended_applications=recommended_applications,
        interview_selected_applications=interview_selected_applications,
        pending_evaluation_applications=pending_evaluation_applications,
    )


@router.get("/applications-by-job", response_model=list[JobApplicationCount])
def get_applications_by_job(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    jobs = _jobs_query(db, current_user).filter(Job.status != JobStatus.ARCHIVED).all()

    results = []
    for job in jobs:
        total = db.query(Application).filter(Application.job_id == job.id).count()
        recommended = (
            db.query(CandidateMatch)
            .join(Application, CandidateMatch.application_id == Application.id)
            .filter(Application.job_id == job.id, CandidateMatch.recommendation_label == "Recomendado")
            .count()
        )
        results.append(JobApplicationCount(
            job_id=job.id, job_title=job.title, job_code=job.code,
            total_applications=total, recommended=recommended,
        ))
    return sorted(results, key=lambda r: r.total_applications, reverse=True)

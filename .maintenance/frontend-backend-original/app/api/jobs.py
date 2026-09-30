from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.schemas.job import JobCreate, JobUpdate, JobRead, JobDetailRead, JobListItem
from app.api.deps import get_current_user, require_recruiter

router = APIRouter(prefix="/api/jobs", tags=["Vagas"])


def _company_scope(current_user: User) -> int | None:
    """Admin pode (por agora) ver tudo; recruiter fica restrito à sua empresa."""
    if current_user.role == UserRole.ADMIN:
        return None
    return current_user.company_id


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_recruiter)])
def create_job(payload: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Utilizador sem empresa associada")

    if db.query(Job).filter(Job.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma vaga com este código")

    job = Job(**payload.model_dump(), company_id=current_user.company_id, created_by_id=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobListItem])
def list_jobs(
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, description="Pesquisa por título ou código"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Job)

    company_id = _company_scope(current_user)
    if company_id:
        query = query.filter(Job.company_id == company_id)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    if search:
        like = f"%{search}%"
        query = query.filter((Job.title.ilike(like)) | (Job.code.ilike(like)))

    return query.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobDetailRead)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).options(joinedload(Job.requirements)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")

    company_id = _company_scope(current_user)
    if company_id and job.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta vaga")
    return job


@router.put("/{job_id}", response_model=JobRead, dependencies=[Depends(require_recruiter)])
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_recruiter)])
def archive_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    job.status = JobStatus.ARCHIVED
    db.commit()


@router.post("/{job_id}/publish", response_model=JobRead, dependencies=[Depends(require_recruiter)])
def publish_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    if not job.requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vaga precisa de pelo menos um requisito antes de ser publicada",
        )
    job.status = JobStatus.PUBLISHED
    job.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/close", response_model=JobRead, dependencies=[Depends(require_recruiter)])
def close_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    job.status = JobStatus.CLOSED
    job.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def _get_owned_job(job_id: int, db: Session, current_user: User) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    company_id = _company_scope(current_user)
    if company_id and job.company_id != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta vaga")
    return job

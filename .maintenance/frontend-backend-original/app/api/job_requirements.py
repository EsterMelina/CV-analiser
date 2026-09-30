from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job
from app.models.job_requirement import JobRequirement
from app.models.user import User, UserRole
from app.schemas.job_requirement import JobRequirementCreate, JobRequirementUpdate, JobRequirementRead
from app.api.deps import get_current_user, require_recruiter

router = APIRouter(tags=["Requisitos de Vaga"])


def _get_owned_job(job_id: int, db: Session, current_user: User) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    if current_user.role != UserRole.ADMIN and job.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta vaga")
    return job


@router.post(
    "/api/jobs/{job_id}/requirements",
    response_model=JobRequirementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_recruiter)],
)
def create_requirement(job_id: int, payload: JobRequirementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    requirement = JobRequirement(**payload.model_dump(), job_id=job.id)
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


@router.get("/api/jobs/{job_id}/requirements", response_model=list[JobRequirementRead])
def list_requirements(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    return job.requirements


@router.put("/api/requirements/{requirement_id}", response_model=JobRequirementRead, dependencies=[Depends(require_recruiter)])
def update_requirement(requirement_id: int, payload: JobRequirementUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    requirement = db.get(JobRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisito não encontrado")
    _get_owned_job(requirement.job_id, db, current_user)  # valida acesso

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(requirement, field, value)
    db.commit()
    db.refresh(requirement)
    return requirement


@router.delete("/api/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_recruiter)])
def delete_requirement(requirement_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    requirement = db.get(JobRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requisito não encontrado")
    _get_owned_job(requirement.job_id, db, current_user)  # valida acesso

    db.delete(requirement)
    db.commit()

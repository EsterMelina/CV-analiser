"""
Router de candidatos e candidaturas.

Nesta fase (Backend + BD), o upload de CV apenas valida, armazena o ficheiro
e regista os metadados. A extração de texto/NLP e o cálculo de score
(secções 14-19 do prompt mestre) ficam para a fase de IA/Matching.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.application import Application, Resume, ApplicationSource
from app.models.user import User, UserRole
from app.schemas.candidate import CandidateRead, ApplicationRead, ApplicationDetailRead, ApplicationStatusUpdate, ResumeRead
from app.api.deps import get_current_user, require_recruiter

router = APIRouter(tags=["Candidatos e Candidaturas"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _get_owned_job(job_id: int, db: Session, current_user: User) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    if current_user.role != UserRole.ADMIN and job.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta vaga")
    return job


def _find_or_create_candidate(db: Session, name: str, email: str, phone: str | None, location: str | None) -> Candidate:
    """Prevenção de duplicados (secção 13): usa o e-mail como chave principal."""
    candidate = db.query(Candidate).filter(Candidate.email == email).first()
    if candidate:
        # Atualiza dados básicos caso tenham mudado, sem apagar histórico
        candidate.name = name or candidate.name
        candidate.phone = phone or candidate.phone
        candidate.location = location or candidate.location
        return candidate

    candidate = Candidate(name=name, email=email, phone=phone, location=location)
    db.add(candidate)
    db.flush()  # garante candidate.id sem fazer commit ainda
    return candidate


@router.post(
    "/api/jobs/{job_id}/cvs",
    response_model=ApplicationDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_recruiter)],
)
async def upload_cv(
    job_id: int,
    candidate_name: str = Form(...),
    candidate_email: str = Form(...),
    candidate_phone: str | None = Form(default=None),
    candidate_location: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato não suportado. Utilize: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Ficheiro excede o limite de {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    candidate = _find_or_create_candidate(db, candidate_name, candidate_email, candidate_phone, candidate_location)

    application = Application(candidate_id=candidate.id, job_id=job.id, source=ApplicationSource.UPLOAD)
    db.add(application)
    db.flush()

    upload_dir = Path(settings.UPLOAD_DIR) / str(job.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(contents)

    resume = Resume(
        application_id=application.id,
        original_filename=file.filename or stored_name,
        stored_path=str(stored_path),
        content_type=file.content_type,
        file_size_bytes=len(contents),
    )
    db.add(resume)
    db.commit()
    db.refresh(application)
    return application


@router.get("/api/jobs/{job_id}/cvs", response_model=list[ApplicationDetailRead])
def list_job_cvs(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, current_user)
    applications = (
        db.query(Application)
        .options(joinedload(Application.candidate), joinedload(Application.resumes))
        .filter(Application.job_id == job.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return applications


# Alias explícito pedido na secção 28 do prompt mestre (mesma informação que /cvs)
@router.get("/api/jobs/{job_id}/candidates", response_model=list[ApplicationDetailRead])
def list_job_candidates(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_job_cvs(job_id, db, current_user)


@router.get("/api/candidates", response_model=list[CandidateRead])
def list_candidates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Nota: numa fase futura, restringir por candidaturas visíveis à empresa do recrutador.
    return db.query(Candidate).order_by(Candidate.name).all()


@router.get("/api/candidates/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")
    return candidate


@router.get("/api/candidates/{candidate_id}/applications", response_model=list[ApplicationRead])
def get_candidate_applications(candidate_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")
    return candidate.applications


@router.get("/api/cvs/{resume_id}", response_model=ResumeRead)
def get_cv(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV não encontrado")
    return resume


@router.patch(
    "/api/applications/{application_id}/status",
    response_model=ApplicationRead,
    dependencies=[Depends(require_recruiter)],
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidatura não encontrada")
    _get_owned_job(application.job_id, db, current_user)  # valida acesso à vaga

    application.status = payload.status
    if payload.recruiter_notes is not None:
        application.recruiter_notes = payload.recruiter_notes
    db.commit()
    db.refresh(application)
    return application

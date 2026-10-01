"""
Router de candidatos e candidaturas.

O upload valida e armazena o ficheiro e coloca a análise na fila do worker
quando o fornecedor de IA e os requisitos da vaga estão configurados.
"""
import uuid
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.models.application import Application, Resume, ApplicationSource
from app.models.user import User, UserRole
from app.schemas.candidate import CandidateRead, ApplicationRead, ApplicationDetailRead, ApplicationStatusUpdate, ResumeRead
from app.api.deps import get_current_user, require_recruiter
from app.schemas.candidate import CandidateCreate
from app.services.documents import validate_document, MIME
from app.services.automatic_analysis import enqueue_uploaded_resume
from app.services.analysis_overview import overview
from app.services.candidate_identity import extract_candidate_identity, UNKNOWN_NAME

router = APIRouter(tags=["Candidatos e Candidaturas"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _get_owned_job(job_id: int, db: Session, current_user: User) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    if current_user.role != UserRole.ADMIN and job.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta vaga")
    return job


def _find_or_create_candidate(db: Session, name: str, email: str, phone: str | None, location: str | None, company_id: int) -> Candidate:
    """Prevenção de duplicados (secção 13): usa o e-mail como chave principal."""
    email = email.strip().lower()
    candidate = db.query(Candidate).filter(Candidate.email == email, Candidate.company_id == company_id).first()
    if candidate:
        # Atualiza dados básicos caso tenham mudado, sem apagar histórico
        if name and name != UNKNOWN_NAME:
            candidate.name = name
        candidate.phone = phone or candidate.phone
        candidate.location = location or candidate.location
        return candidate

    candidate = Candidate(name=name, email=email, phone=phone, location=location, company_id=company_id)
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
    candidate_name: str | None = Form(default=None),
    candidate_email: str | None = Form(default=None),
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

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read(max_bytes + 1)
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Ficheiro excede o limite de {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    validate_document(contents, extension)
    try:
        extracted_name, extracted_email = extract_candidate_identity(contents, extension)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    email = extracted_email or (candidate_email or "").strip().lower()
    if not email:
        raise HTTPException(422, "Não foi possível identificar o e-mail no CV. Envie um PDF/DOCX com o e-mail de contacto em texto legível.")
    try:
        identity = CandidateCreate(name=extracted_name or (candidate_name or "").strip() or UNKNOWN_NAME,
                                   email=email,
                                   phone=candidate_phone, location=candidate_location)
    except ValidationError:
        raise HTTPException(422, "Nome ou e-mail inválido")
    digest = hashlib.sha256(contents).hexdigest()
    stored_path = None
    committed = False
    try:
        # Serialise uploads to the same job before candidate/application lookup.
        db.query(Job).filter(Job.id == job.id).with_for_update().one()
        candidate = _find_or_create_candidate(db, identity.name, str(identity.email), identity.phone, identity.location, job.company_id)
        application = db.query(Application).filter(Application.candidate_id == candidate.id,
            Application.job_id == job.id).order_by(Application.id.desc()).first()
        if application is None:
            application = Application(candidate_id=candidate.id, job_id=job.id, source=ApplicationSource.UPLOAD)
            db.add(application)
            db.flush()
        if any(resume.sha256 == digest for resume in application.resumes):
            db.commit()
            return ApplicationDetailRead.model_validate(application).model_copy(update=overview(db, application))
        version = max((resume.version for resume in application.resumes), default=0) + 1
        upload_dir = Path(settings.UPLOAD_DIR).resolve() / str(job.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = upload_dir / f"{uuid.uuid4().hex}{extension}"
        stored_path.write_bytes(contents)
        resume = Resume(application_id=application.id, original_filename=Path(file.filename or "cv").name[:255],
            stored_path=str(stored_path), content_type=MIME[extension], file_size_bytes=len(contents),
            sha256=digest, version=version)
        db.add(resume)
        db.flush()
        application.analysis_status = "pending"
        if enqueue_uploaded_resume(db, job, current_user, resume):
            application.analysis_status = "queued"
        db.commit()
        committed = True
        db.refresh(application)
        return ApplicationDetailRead.model_validate(application).model_copy(update=overview(db, application))
    except Exception:
        db.rollback()
        if stored_path is not None and not committed:
            stored_path.unlink(missing_ok=True)
        raise


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
    from app.services.analysis_overview import overview
    return [ApplicationDetailRead.model_validate(application).model_copy(update=overview(db, application))
            for application in applications]


# Alias explícito pedido na secção 28 do prompt mestre (mesma informação que /cvs)
@router.get("/api/jobs/{job_id}/candidates", response_model=list[ApplicationDetailRead])
def list_job_candidates(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_job_cvs(job_id, db, current_user)


@router.get("/api/candidates", response_model=list[CandidateRead])
def list_candidates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Candidate)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Candidate.company_id == current_user.company_id)
    return query.order_by(Candidate.name).all()


@router.get("/api/candidates/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidato não encontrado")
    if current_user.role != UserRole.ADMIN and candidate.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sem acesso a este candidato")
    return candidate


@router.get("/api/candidates/{candidate_id}/applications", response_model=list[ApplicationRead])
def get_candidate_applications(candidate_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    candidate = get_candidate(candidate_id, db, current_user)
    return candidate.applications


@router.get("/api/cvs/{resume_id}", response_model=ResumeRead)
def get_cv(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV não encontrado")
    _get_owned_job(resume.application.job_id, db, current_user)
    return resume


@router.get("/api/cvs/{resume_id}/download")
def download_cv(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = get_cv(resume_id, db, current_user)
    path = Path(resume.stored_path).resolve()
    if not path.is_relative_to(Path(settings.UPLOAD_DIR).resolve()) or not path.is_file():
        raise HTTPException(404, "Documento indisponível; contacte o administrador")
    return FileResponse(path, filename=resume.original_filename, media_type=resume.content_type,
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})


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

    from app.services.application_state import transition
    transition(application, payload.status)
    if payload.recruiter_notes is not None:
        application.recruiter_notes = payload.recruiter_notes
    db.commit()
    db.refresh(application)
    return application


@router.get("/api/applications/{application_id}", response_model=ApplicationDetailRead)
def application_detail(application_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.api.interviews import _get_owned_application
    from app.services.analysis_overview import overview
    application = _get_owned_application(application_id, db, current_user)
    return ApplicationDetailRead.model_validate(application).model_copy(update=overview(db, application))

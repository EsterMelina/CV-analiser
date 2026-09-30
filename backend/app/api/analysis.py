import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.application import Application, Resume
from app.models.candidate_profile import CandidateMatch
from app.models.job import Job
from app.models.user import User, UserRole
from app.schemas.analysis import CandidateMatchRead, RankingItem
from app.api.deps import get_current_user, require_recruiter
from app.services.analysis_service import analyze_resume, AnalysisError
from app.services.text_extraction import TextExtractionError

router = APIRouter(tags=["Análise e Ranking"])


def _match_to_schema(match: CandidateMatch) -> CandidateMatchRead:
    return CandidateMatchRead(
        id=match.id,
        application_id=match.application_id,
        overall_score=match.overall_score,
        recommendation_label=match.recommendation_label,
        breakdown=json.loads(match.breakdown_json),
        mandatory_missing=json.loads(match.mandatory_missing_json),
        computed_at=match.computed_at,
        criteria_version=match.criteria_version, resume_id=match.resume_id,
        stale=match.criteria_version != match.application.job.criteria_version,
    )


def _get_owned_job(job_id: int, db: Session, current_user: User) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    if current_user.role != UserRole.ADMIN and job.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta vaga")
    return job


@router.post(
    "/api/cvs/{resume_id}/analyze",
    response_model=CandidateMatchRead,
    dependencies=[Depends(require_recruiter)],
)
def analyze_cv(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.core.config import settings
    if not settings.LEGACY_ANALYSIS_ENABLED:
        raise HTTPException(410, "Motor antigo desactivado; utilize analysis-executions")
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV não encontrado")

    _get_owned_job(resume.application.job_id, db, current_user)

    try:
        match = analyze_resume(db, resume)
    except TextExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except AnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return _match_to_schema(match)


@router.get("/api/cvs/{resume_id}/analysis", response_model=CandidateMatchRead)
def get_cv_analysis(resume_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV não encontrado")
    _get_owned_job(resume.application.job_id, db, current_user)

    match = db.query(CandidateMatch).filter(CandidateMatch.application_id == resume.application_id).first()
    if not match or match.resume_id != resume.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este CV ainda não foi analisado. Chame POST /api/cvs/{id}/analyze primeiro.",
        )
    return _match_to_schema(match)


@router.get("/api/jobs/{job_id}/ranking", response_model=list[RankingItem])
def get_job_ranking(
    job_id: int,
    filter: str | None = Query(
        default=None,
        description="recomendado | avaliar | baixa_compatibilidade | requisito_obrigatorio_ausente",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_owned_job(job_id, db, current_user)

    applications = (
        db.query(Application)
        .options(joinedload(Application.candidate))
        .filter(Application.job_id == job.id)
        .all()
    )

    label_map = {
        "recomendado": "Recomendado",
        "avaliar": "Avaliar",
        "compatibilidade_parcial": "Compatibilidade parcial",
        "baixa_compatibilidade": "Baixa compatibilidade",
        "requisito_obrigatorio_ausente": "Requisito obrigatório ausente",
    }
    wanted_label = label_map.get(filter) if filter else None

    items: list[RankingItem] = []
    for app in applications:
        from app.services.analysis_overview import overview
        summary = overview(db, app)
        if wanted_label and summary["recommendation_label"] != wanted_label:
            continue
        items.append(RankingItem(
            application_id=app.id, candidate_id=app.candidate.id,
            candidate_name=app.candidate.name, candidate_email=app.candidate.email,
            status=app.status.value, **{key: value for key, value in summary.items()
                                      if key != "latest_resume_id"},
        ))

    items.sort(key=lambda i: (i.score is None, -(i.score or 0)))
    return items

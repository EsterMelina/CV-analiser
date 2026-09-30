import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.api.candidates import get_cv
from app.api.interviews import _get_owned_application
from app.models.user import User
from app.models.analysis_run import AnalysisRun, AnalysisEvidence
from app.models.application import Resume
from app.models.criteria_version import CriteriaVersion
from app.schemas.ai import StrictModel, Evidence, Profile
from app.services.criteria import preserve, snapshot
from app.services.executions import enqueue, public
from app.services.professional_analysis import serialize
from app.services.ai_service import validate_citation
from app.services.ai_provider import ProviderError, require_analysis_provider, configuration_error
from app.services.scoring import calculate_score, POLICY_VERSION

router = APIRouter(tags=["Análises profissionais e revisão"])


class ReviewRequest(StrictModel):
    reason: str = Field(min_length=10, max_length=2000)
    evidence: list[Evidence]
    profile: Profile | None = None


@router.get("/api/analysis-configuration")
def analysis_configuration(user: User = Depends(get_current_user)):
    error = configuration_error()
    return {"ready": error is None, "message": error}


@router.post("/api/cvs/{resume_id}/analysis-executions", status_code=202)
def start_analysis(resume_id: int, idempotency_key: str = Header(alias="Idempotency-Key"),
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = get_cv(resume_id, db, user)
    try:
        require_analysis_provider()
    except ProviderError as exc:
        raise HTTPException(503, str(exc)) from None
    job = resume.application.job
    if not job.requirements or sum(r.weight for r in job.requirements) <= 0:
        raise HTTPException(422, "Configure requisitos com soma dos pesos superior a zero")
    path = Path(resume.stored_path).resolve()
    if not path.is_relative_to(Path(settings.UPLOAD_DIR).resolve()) or not path.is_file():
        raise HTTPException(422, "Documento indisponível")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if resume.sha256 and digest != resume.sha256:
        raise HTTPException(409, "Documento alterado; requer recuperação ou nova versão")
    preserve(db, job, user.id)
    payload = {"resume_id": resume.id, "document_hash": digest, "criteria": snapshot(job), "criteria_version": job.criteria_version}
    return public(enqueue(db, job, user, idempotency_key, "analysis", payload))


@router.get("/api/applications/{application_id}/analysis-runs")
def history(application_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    application = _get_owned_application(application_id, db, user)
    latest = max(application.resumes, key=lambda r: r.version).id
    return [serialize(run, application.job, latest) for run in db.query(AnalysisRun).filter_by(
        application_id=application_id).order_by(AnalysisRun.id.desc()).all()]


@router.post("/api/analysis-runs/{run_id}/review", status_code=201)
def review(run_id: int, value: ReviewRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    original = db.get(AnalysisRun, run_id)
    if not original:
        raise HTTPException(404, "Análise não encontrada")
    application = _get_owned_application(original.application_id, db, user)
    if original.status in {"not_evaluable", "legacy-unverified"}:
        raise HTTPException(409, "Documento sem texto: envie uma versão legível antes de avaliar")
    latest = db.query(AnalysisRun).filter_by(application_id=application.id).order_by(AnalysisRun.id.desc()).with_for_update().first()
    if latest.id != original.id:
        raise HTTPException(409, "Existe análise mais recente; reabra antes de rever")
    sources = {s["location"]: s["text"] for s in json.loads(original.sources_json)}
    try:
        for evidence in value.evidence:
            for citation in evidence.citations:
                validate_citation(citation, sources)
        if value.profile:
            for fact in value.profile.skills + value.profile.education + value.profile.languages:
                validate_citation(fact.evidence, sources)
            for experience in value.profile.experiences:
                validate_citation(experience.evidence, sources)
        criteria = db.query(CriteriaVersion).filter_by(job_id=application.job_id, version=original.criteria_version).one()
        evidence_data = [e.model_dump() for e in value.evidence]
        scoring = calculate_score(json.loads(criteria.snapshot_json)["requirements"], evidence_data)
    except (ProviderError, ValueError) as exc:
        raise HTTPException(422, str(exc))
    reviewed = AnalysisRun(application_id=application.id, resume_id=original.resume_id,
        created_at=datetime.now(timezone.utc),
        document_hash=original.document_hash, criteria_version=original.criteria_version,
        parent_id=original.id, created_by_id=user.id, method="human-review", policy_version=POLICY_VERSION,
        status="reviewed", score=scoring["score"], reason=value.reason,
        sources_json=original.sources_json, profile_json=value.profile.model_dump_json() if value.profile else original.profile_json,
        result_json=json.dumps(scoring, ensure_ascii=False))
    db.add(reviewed)
    db.flush()
    for evidence in value.evidence:
        db.add(AnalysisEvidence(run_id=reviewed.id, requirement_id=evidence.requirement_id,
            state=evidence.state, content_json=evidence.model_dump_json()))
    latest_resume = max(application.resumes, key=lambda r: r.version).id
    if original.criteria_version == application.job.criteria_version and original.resume_id == latest_resume:
        application.analysis_status = "reviewed"
        application.score = reviewed.score
    db.commit()
    return serialize(reviewed, application.job, latest_resume)

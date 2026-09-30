from datetime import datetime, timezone
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.api.jobs import _get_owned_job
from app.models.user import User
from app.models.ai_execution import AIExecution
from app.models.questionnaire import Questionnaire, QuestionnaireVersion
from app.schemas.ai import StrictModel, QuestionnaireContent, GenerationConfig
from app.services import questionnaires as service
from app.services.criteria import preserve, snapshot
from app.services.executions import enqueue, public

router = APIRouter(tags=["Questionários e IA"])


class SaveRequest(StrictModel):
    expected_revision: int = Field(ge=1)
    content: QuestionnaireContent


class RevisionRequest(StrictModel):
    expected_revision: int = Field(ge=1)


class GenerateRequest(StrictModel):
    config: GenerationConfig
    version_id: int | None = None
    target_key: str | None = None


class ApplyRequest(RevisionRequest):
    execution_id: str


def owned_version(db, user, version_id):
    version = db.get(QuestionnaireVersion, version_id)
    if not version:
        raise HTTPException(404, "Versão não encontrada")
    questionnaire = db.get(Questionnaire, version.questionnaire_id)
    job = _get_owned_job(questionnaire.job_id, db, user)
    return version, job


def owned_execution(db, user, execution_id):
    execution = db.get(AIExecution, execution_id)
    if not execution:
        raise HTTPException(404, "Execução não encontrada")
    _get_owned_job(execution.job_id, db, user)
    return execution


@router.get("/api/jobs/{job_id}/questionnaires")
def list_versions(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, user)
    versions = db.query(QuestionnaireVersion).join(Questionnaire).filter(Questionnaire.job_id == job.id).order_by(QuestionnaireVersion.number.desc()).all()
    return [service.serialize(version, job) for version in versions]


@router.post("/api/jobs/{job_id}/questionnaires", status_code=201)
def create_manual(job_id: int, value: QuestionnaireContent, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, user)
    for q in value.questions:
        q.provenance = "manual"
    version = service.create_version(db, job, user.id, value)
    db.commit()
    return service.serialize(version, job)


@router.get("/api/questionnaire-versions/{version_id}")
def get_version(version_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version, job = owned_version(db, user, version_id)
    return service.serialize(version, job)


@router.put("/api/questionnaire-versions/{version_id}")
def save_version(version_id: int, value: SaveRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version, job = owned_version(db, user, version_id)
    service.validate_content(db, job, version.criteria_version, value.content)
    previous = {q.key: q for q in service.content(version).questions}
    for q in value.content.questions:
        old = previous.get(q.key)
        q.provenance = "manual" if old is None else old.provenance
        if old and old.model_dump(exclude={"provenance"}) != q.model_dump(exclude={"provenance"}):
            q.provenance = "edited"
    service.reserve_edit(db, version, value.expected_revision)
    service.replace_questions(db, version, value.content)
    db.commit()
    return service.serialize(version, job)


@router.post("/api/questionnaire-versions/{version_id}/fork", status_code=201)
def fork_version(version_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    source, job = owned_version(db, user, version_id)
    version = service.create_version(db, job, user.id, service.content(source), source=source)
    db.commit()
    return service.serialize(version, job)


@router.post("/api/questionnaire-versions/{version_id}/approve")
def approve(version_id: int, value: RevisionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version, job = owned_version(db, user, version_id)
    service.validate_content(db, job, version.criteria_version, service.content(version), approval=True)
    service.reserve_edit(db, version, value.expected_revision)
    version.status = "approved"
    version.approved_by_id = user.id
    version.approved_at = datetime.now(timezone.utc)
    db.commit()
    return service.serialize(version, job)


@router.post("/api/questionnaire-versions/{version_id}/archive")
def archive(version_id: int, value: RevisionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version, job = owned_version(db, user, version_id)
    changed = db.query(QuestionnaireVersion).filter_by(id=version.id, revision=value.expected_revision).filter(
        QuestionnaireVersion.status != "archived").update({"revision": value.expected_revision + 1,
        "status": "archived", "archived_at": datetime.now(timezone.utc)}, synchronize_session=False)
    if not changed:
        raise HTTPException(409, "Versão alterada ou já arquivada")
    db.commit()
    db.refresh(version)
    return service.serialize(version, job)


@router.post("/api/jobs/{job_id}/questionnaires/generate", status_code=202)
def generate(job_id: int, value: GenerateRequest, idempotency_key: str = Header(alias="Idempotency-Key"),
             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = _get_owned_job(job_id, db, user)
    preserve(db, job, user.id)
    payload = {"config": value.config.model_dump(), "criteria": snapshot(job), "criteria_version": job.criteria_version,
               "version_id": value.version_id, "target_key": value.target_key}
    if value.version_id:
        version, parent_job = owned_version(db, user, value.version_id)
        if parent_job.id != job.id or version.status != "draft" or version.criteria_version != job.criteria_version:
            raise HTTPException(409, "Regeneração exige rascunho com critérios actuais")
        payload["base_revision"] = version.revision
        if value.target_key:
            question = next((q for q in service.content(version).questions if q.key == value.target_key), None)
            if not question or value.config.count != 1 or value.config.requirement_ids != [question.requirement_id] or value.config.format != question.format:
                raise HTTPException(422, "Configuração incompatível com a pergunta alvo")
    elif value.target_key:
        raise HTTPException(422, "Pergunta alvo exige versão")
    if value.config.category and any(r.category.value != value.config.category for r in job.requirements
                                    if r.id in value.config.requirement_ids):
        raise HTTPException(422, "As competências seleccionadas não pertencem à área indicada")
    available = {r.id for r in job.requirements}
    if not set(value.config.requirement_ids) <= available:
        raise HTTPException(422, "Competência não pertence à vaga")
    return public(enqueue(db, job, user, idempotency_key, "questionnaire", payload))


@router.get("/api/executions/{execution_id}")
def get_execution(execution_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return public(owned_execution(db, user, execution_id))


@router.post("/api/executions/{execution_id}/retry")
def retry(execution_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    execution = owned_execution(db, user, execution_id)
    changed = db.query(AIExecution).filter_by(id=execution.id, status="failed").filter(AIExecution.attempts < 3).update(
        {"status": "queued", "error": None, "finished_at": None}, synchronize_session=False)
    if not changed:
        raise HTTPException(409, "Pedido activo, concluído ou limite de tentativas atingido")
    db.commit()
    db.refresh(execution)
    return public(execution)


@router.post("/api/questionnaire-versions/{version_id}/apply-generation")
def apply_generation(version_id: int, value: ApplyRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version, job = owned_version(db, user, version_id)
    execution = owned_execution(db, user, value.execution_id)
    payload = json.loads(execution.payload_json)
    if execution.status != "succeeded" or execution.kind != "questionnaire" or payload.get("version_id") != version.id:
        raise HTTPException(409, "Proposta não disponível para esta versão")
    if value.expected_revision != payload["base_revision"]:
        raise HTTPException(409, "O rascunho mudou desde o pedido; gere nova proposta")
    proposal = QuestionnaireContent.model_validate(json.loads(execution.result_json)["content"])
    if payload.get("target_key"):
        current = service.content(version)
        replacement = proposal.questions[0].model_copy(update={"key": payload["target_key"]})
        current.questions = [replacement if q.key == replacement.key else q for q in current.questions]
        proposal = current
    service.validate_content(db, job, version.criteria_version, proposal)
    service.reserve_edit(db, version, value.expected_revision)
    service.replace_questions(db, version, proposal)
    version.execution_id = execution.id
    db.commit()
    return service.serialize(version, job)


@router.get("/api/questionnaire-versions/{version_id}/print")
def print_version(version_id: int, mode: str = Query(pattern="^(questions|guide)$", default="questions"),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version, job = owned_version(db, user, version_id)
    questions = service.content(version).questions
    return {"job": job.title, "code": job.code, "version": version.number, "status": version.status,
        "mode": mode, "language": version.language,
        "questions": [q.model_dump() if mode == "guide" else
            {"prompt": q.prompt, "format": q.format, "options": q.options} for q in questions]}

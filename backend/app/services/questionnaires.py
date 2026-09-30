import json
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func
from app.models.job import Job
from app.models.questionnaire import Questionnaire, QuestionnaireVersion, Question
from app.models.criteria_version import CriteriaVersion
from app.schemas.ai import QuestionnaireContent
from app.services.criteria import preserve


def content(version):
    return QuestionnaireContent(language=version.language, questions=[json.loads(q.content_json) for q in version.questions])


def serialize(version, job):
    return {"id": version.id, "number": version.number, "revision": version.revision,
        "status": version.status, "criteria_version": version.criteria_version,
        "stale": version.criteria_version != job.criteria_version,
        "created_by_id": version.created_by_id, "created_at": version.created_at,
        "approved_by_id": version.approved_by_id, "approved_at": version.approved_at,
        "source_version_id": version.source_version_id, "execution_id": version.execution_id,
        "content": content(version).model_dump(mode="json")}


def validate_content(db, job, criteria_version, value, approval=False):
    try:
        QuestionnaireContent.model_validate(value.model_dump())
    except ValidationError:
        raise HTTPException(422, "Conteúdo inválido ou perguntas repetidas") from None
    snapshot = db.query(CriteriaVersion).filter_by(job_id=job.id, version=criteria_version).one()
    requirements = {r["id"]: r for r in json.loads(snapshot.snapshot_json)["requirements"]}
    for q in value.questions:
        if q.requirement_id not in requirements or q.category != requirements[q.requirement_id]["category"]:
            raise HTTPException(422, "Pergunta sem ligação aos critérios desta versão")
        if approval and (not q.rubric or not q.expected_answer):
            raise HTTPException(422, "Aprovação exige resposta esperada e rubrica em todas as perguntas")
    if approval and not value.questions:
        raise HTTPException(422, "Não é possível aprovar um questionário vazio")


def replace_questions(db, version, value):
    db.query(Question).filter_by(version_id=version.id).delete(synchronize_session=False)
    db.flush()
    for index, q in enumerate(value.questions):
        db.add(Question(version_id=version.id, position=index, content_json=q.model_dump_json()))
    version.language = value.language
    db.flush()
    db.expire(version, ["questions"])


def create_version(db, job, user_id, value, source=None, execution_id=None, criteria_version=None):
    db.query(Job).filter_by(id=job.id).with_for_update().one()
    preserve(db, job, user_id)
    questionnaire = db.query(Questionnaire).filter_by(job_id=job.id).first()
    if not questionnaire:
        questionnaire = Questionnaire(job_id=job.id)
        db.add(questionnaire)
        db.flush()
    criteria_version = criteria_version or (source.criteria_version if source else job.criteria_version)
    validate_content(db, job, criteria_version, value)
    number = (db.query(func.max(QuestionnaireVersion.number)).filter_by(questionnaire_id=questionnaire.id).scalar() or 0) + 1
    version = QuestionnaireVersion(questionnaire_id=questionnaire.id, number=number,
        criteria_version=criteria_version, created_by_id=user_id,
        source_version_id=source.id if source else None, execution_id=execution_id)
    db.add(version)
    db.flush()
    replace_questions(db, version, value)
    return version


def reserve_edit(db, version, expected):
    changed = db.query(QuestionnaireVersion).filter_by(id=version.id, status="draft", revision=expected).update(
        {"revision": expected + 1}, synchronize_session=False)
    if changed != 1:
        raise HTTPException(409, "Versão alterada ou imutável. Reabra antes de guardar; edições locais foram preservadas.")
    db.refresh(version)

import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
from sqlalchemy.orm import object_session
from app.models.criteria_version import CriteriaVersion
from app.models.application import Resume, Application
from app.models.analysis_run import AnalysisRun, AnalysisEvidence
from app.services.located_text import extract_located
from app.services.ai_service import run
from app.services.ai_provider import ProviderError, require_analysis_provider, get_provider
from app.services.scoring import calculate_score, POLICY_VERSION, known_experience_days


def prepare_result(db, payload, provider=None, progress=None):
    if provider is None:
        require_analysis_provider()
    resume = db.get(Resume, payload["resume_id"])
    if not resume:
        raise ProviderError("Documento indisponível")
    from app.core.config import settings
    path = Path(resume.stored_path).resolve()
    if not path.is_relative_to(Path(settings.UPLOAD_DIR).resolve()) or not path.is_file():
        raise ProviderError("Documento indisponível")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != payload["document_hash"]:
        raise ProviderError("Documento alterado desde o pedido; envie nova versão")
    located = extract_located(str(path))
    result = {"sources": located["sources"], "profile": {}, "evidence": [], "score": None,
              "status": "not_evaluable", "policy_version": POLICY_VERSION,
              "reason": "Documento sem texto; OCR indisponível. Envie PDF textual/DOCX ou peça revisão."}
    if located["quality"] != "text":
        return result, "parser-no-ocr"
    model_payload = {"sources": located["sources"], "criteria": payload["criteria"]}
    provider = provider or get_provider()
    if getattr(provider, "assessment_only", False):
        from app.services.compact_evaluation import supported_profile
        provider.progress = progress
        evaluation, provider_name = run("evaluate", model_payload, provider)
        profile = supported_profile(payload["criteria"]["requirements"], evaluation)
        result["profile_scope"] = "supported_requirements"
    else:
        profile, provider_name = run("profile", model_payload, provider)
        evaluation, _ = run("evaluate", model_payload, provider)
    evidence = evaluation.model_dump(mode="json")["evidence"]
    scoring = calculate_score(payload["criteria"]["requirements"], evidence)
    simulated = provider_name.startswith("mock")
    result.update(scoring)
    result.update(profile=profile.model_dump(mode="json"), evidence=evidence,
        known_experience_days=known_experience_days(profile.experiences), method=provider_name,
        status="review_required" if simulated else "completed",
        reason="Resultado simulado; não usar para decisões." if simulated else scoring["summary"])
    if simulated:
        result["score"] = None
        result["recommendation"] = None
        result["summary"] = result["reason"]
    return result, provider_name


def persist_result(db, execution, payload, result):
    resume = db.get(Resume, payload["resume_id"])
    analysis = AnalysisRun(application_id=resume.application_id, resume_id=resume.id,
        created_at=datetime.now(timezone.utc),
        document_hash=payload["document_hash"], criteria_version=payload["criteria_version"],
        execution_id=execution.id, created_by_id=execution.created_by_id,
        method=result.get("method", "parser-no-ocr"), policy_version=POLICY_VERSION,
        status=result["status"], score=result["score"],
        profile_json=json.dumps(result["profile"], ensure_ascii=False),
        sources_json=json.dumps(result["sources"], ensure_ascii=False),
        result_json=json.dumps(result, ensure_ascii=False), reason=result["reason"])
    db.add(analysis)
    db.flush()
    for evidence in result["evidence"]:
        db.add(AnalysisEvidence(run_id=analysis.id, requirement_id=evidence["requirement_id"],
            state=evidence["state"], content_json=json.dumps(evidence, ensure_ascii=False)))
    application = db.get(Application, resume.application_id)
    latest_document = max(application.resumes, key=lambda r: r.version)
    if latest_document.id == resume.id and application.job.criteria_version == payload["criteria_version"]:
        application.analysis_status = result["status"]
        application.score = result["score"]
    return {"analysis_id": analysis.id, "status": analysis.status}


def serialize(analysis, job, latest_resume_id):
    db = object_session(analysis)
    version = db.query(CriteriaVersion).filter_by(
        job_id=job.id, version=analysis.criteria_version).first() if db else None
    requirements = json.loads(version.snapshot_json)["requirements"] if version else []
    return {"id": analysis.id, "resume_id": analysis.resume_id, "document_hash": analysis.document_hash,
        "requirements": requirements,
        "criteria_version": analysis.criteria_version, "method": analysis.method, "policy_version": analysis.policy_version,
        "status": analysis.status, "score": analysis.score, "reason": analysis.reason,
        "created_by_id": analysis.created_by_id, "created_at": analysis.created_at, "parent_id": analysis.parent_id,
        "stale": analysis.criteria_version != job.criteria_version or analysis.resume_id != latest_resume_id,
        "profile": json.loads(analysis.profile_json), "sources": json.loads(analysis.sources_json),
        "evidence": [json.loads(e.content_json) for e in analysis.evidence], "result": json.loads(analysis.result_json)}

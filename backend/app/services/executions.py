from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from app.models.ai_execution import AIExecution
from app.models.job import Job
from app.models.company import Company
from app.models.user import User
from app.services.ai_service import run
from app.services.ai_provider import ProviderError, PROMPT_VERSION
from app.core.config import settings


def execution_timeout():
    return 2 * settings.AI_TIMEOUT_SECONDS + 30 if settings.AI_PROVIDER in {"ollama", "openai-compatible"} else 55


def enqueue(db, job, user, key, kind, payload, *, commit=True):
    if not key or len(key) > 100:
        raise HTTPException(422, "Idempotency-Key obrigatório, até 100 caracteres")
    encoded = json.dumps({"kind": kind, "payload": payload}, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    existing = db.query(AIExecution).filter_by(company_id=job.company_id, idempotency_key=key).first()
    if existing:
        if existing.payload_hash != digest:
            raise HTTPException(409, "Chave já utilizada para outro pedido")
        return existing
    execution = AIExecution(id=str(uuid4()), company_id=job.company_id, job_id=job.id,
        created_by_id=user.id, idempotency_key=key, kind=kind,
        prompt_version=PROMPT_VERSION,
        payload_hash=digest, payload_json=json.dumps(payload, ensure_ascii=False))
    db.add(execution)
    if not commit:
        # The caller commits the document and its queued analysis atomically.
        db.flush()
        return execution
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(AIExecution).filter_by(company_id=job.company_id, idempotency_key=key).first()
        if not existing or existing.payload_hash != digest:
            raise HTTPException(409, "Pedido concorrente incompatível")
        return existing
    return execution


def public(execution):
    return {"id": execution.id, "kind": execution.kind, "status": execution.status,
        "attempts": execution.attempts, "error": execution.error, "provider": execution.provider,
        "prompt_version": execution.prompt_version, "created_at": execution.created_at,
        "finished_at": execution.finished_at,
        "result": json.loads(execution.result_json) if execution.result_json else None}


def claim(db):
    now = datetime.now(timezone.utc)
    available = or_(AIExecution.status == "queued", and_(AIExecution.status == "running", AIExecution.lease_until < now))
    db.query(AIExecution).filter(available, AIExecution.attempts >= 3).update(
        {"status": "failed", "error": "Limite de tentativas atingido; pode criar novo pedido"}, synchronize_session=False)
    candidate = db.query(AIExecution).filter(available, AIExecution.attempts < 3).order_by(AIExecution.created_at).first()
    if candidate is None:
        db.commit()
        return None
    token = str(uuid4())
    claimed = db.query(AIExecution).filter(AIExecution.id == candidate.id, available, AIExecution.attempts < 3).update(
        {"status": "running", "lease_token": token,
         "attempts": AIExecution.attempts + 1, "error": None,
         "lease_until": now + timedelta(seconds=execution_timeout() + 10)}, synchronize_session=False)
    db.commit()
    if not claimed:
        return None
    db.refresh(candidate)
    return candidate.id, token


def process_one(db, provider=None):
    claimed = claim(db)
    if not claimed:
        return False
    execution_id, token = claimed
    execution = db.get(AIExecution, execution_id)
    payload = json.loads(execution.payload_json)
    try:
        company = db.get(Company, execution.company_id)
        user = db.get(User, execution.created_by_id)
        if not company or not company.is_active or not user or not user.is_active:
            raise ProviderError("Empresa ou utilizador inactivo")
        if user.role.value != "admin" and user.company_id != company.id:
            raise ProviderError("Utilizador já não pertence à empresa")
        if execution.kind == "questionnaire":
            output, provider_name = run("questionnaire", payload, provider)
            result = {"content": output.model_dump(mode="json"), "simulated": provider_name.startswith("mock")}
        elif execution.kind == "analysis":
            from app.services.professional_analysis import prepare_result
            def progress(value):
                changed = db.query(AIExecution).filter_by(id=execution_id, lease_token=token, status="running").update(
                    {"result_json": json.dumps({"progress": value})}, synchronize_session=False)
                db.commit()
                if not changed:
                    raise ProviderError("A execução já não está activa")
            progress({"stage": "preparing", "elapsed_seconds": 0})
            result, provider_name = prepare_result(db, payload, provider, progress)
        else:
            raise ProviderError("Operação desconhecida")
        # Commit only if this worker still owns the lease. All domain writes share this transaction.
        db.expire_all()
        execution = db.query(AIExecution).filter_by(id=execution_id, lease_token=token, status="running").filter(
            AIExecution.lease_until > datetime.now(timezone.utc)).with_for_update().first()
        if execution is None:
            db.rollback()
            return True
        if execution.kind == "questionnaire" and not payload.get("version_id"):
            from app.services.questionnaires import create_version
            version = create_version(db, db.get(Job, execution.job_id), execution.created_by_id, output,
                execution_id=execution.id, criteria_version=payload["criteria_version"])
            result["version_id"] = version.id
        elif execution.kind == "analysis":
            from app.services.professional_analysis import persist_result
            result = persist_result(db, execution, payload, result)
        execution.status = "succeeded"
        execution.result_json = json.dumps(result, ensure_ascii=False)
        execution.provider = provider_name
        execution.finished_at = datetime.now(timezone.utc)
        execution.lease_token = None
        db.commit()
    except Exception as exc:
        db.rollback()
        message = str(exc) if isinstance(exc, ProviderError) else "Falha de execução; conteúdo anterior preservado"
        logging.getLogger(__name__).error("Execução %s falhou: %s", execution_id, message)
        db.query(AIExecution).filter_by(id=execution_id, lease_token=token).update({
            "status": "failed", "error": message,
            "lease_token": None, "finished_at": datetime.now(timezone.utc)}, synchronize_session=False)
        db.commit()
    return True

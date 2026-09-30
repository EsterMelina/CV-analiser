"""One read model for candidate lists and ranking, including unfinished jobs."""
import json
from datetime import timezone
from app.models.ai_execution import AIExecution
from app.models.analysis_run import AnalysisRun
from app.models.candidate_profile import CandidateMatch


def _time(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def overview(db, application):
    latest = max(application.resumes, key=lambda r: (r.version, r.id), default=None)
    runs = db.query(AnalysisRun).filter_by(application_id=application.id).order_by(AnalysisRun.id.desc()).all()
    current = next((r for r in runs if latest and r.resume_id == latest.id and
                    r.criteria_version == application.job.criteria_version), None)
    run = current or next(iter(runs), None)
    match = None if run else db.query(CandidateMatch).filter_by(application_id=application.id).first()
    result = run or match
    stale = bool(result and (not latest or result.resume_id != latest.id or
                            result.criteria_version != application.job.criteria_version))
    state = run.status if run else "completed" if match else "pending"
    if stale:
        state = "stale"
    label = match.recommendation_label if match and not stale else None
    score = (run.score if run else match.overall_score if match else None) if not stale else None
    missing = []
    if current:
        data = json.loads(current.result_json)
        missing = data.get("mandatory_missing", []) if isinstance(data, dict) else []
        if current.status == "completed" and current.score is not None:
            label = data.get("recommendation")
    elif match and not stale:
        missing = json.loads(match.mandatory_missing_json)
    executions = db.query(AIExecution).filter_by(job_id=application.job_id, kind="analysis").all()
    relevant = [e for e in executions if latest and
                json.loads(e.payload_json).get("resume_id") == latest.id and
                json.loads(e.payload_json).get("criteria_version") == application.job.criteria_version]
    active = [e for e in relevant if e.status in {"queued", "running"}]
    execution = max(active, key=lambda e: (_time(e.created_at), e.id), default=None)
    error = None
    if execution:
        state = execution.status
    else:
        failed = max((e for e in relevant if e.status == "failed"),
                     key=lambda e: _time(e.finished_at or e.created_at), default=None)
        completed_at = _time(result.created_at if run else match.computed_at) if result else None
        if run:
            source = next((e for e in relevant if e.id == run.execution_id), None)
            if source and source.finished_at:
                completed_at = max(completed_at, _time(source.finished_at))
        if failed and (not completed_at or _time(failed.finished_at or failed.created_at) > completed_at):
            state, error = "error", failed.error
    return {"analysis_status": state, "analysis_id": run.id if run else None,
            "analysis_execution_id": execution.id if execution else None,
            "analysis_method": run.method if run else "legacy-keywords" if match else None,
            "analysis_error": error, "latest_resume_id": latest.id if latest else None,
            "stale": stale, "score": score, "recommendation_label": label,
            "mandatory_missing": missing}

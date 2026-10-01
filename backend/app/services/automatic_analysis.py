"""Queue analysis as part of the upload transaction, without calling the model."""
from app.services.ai_provider import configuration_error
from app.services.criteria import preserve, snapshot
from app.services.executions import enqueue


def enqueue_uploaded_resume(db, job, user, resume):
    # Keep uploads available when AI or job criteria are not ready. The manual
    # action remains available once the recruiter fixes the configuration.
    if configuration_error() or not job.requirements or sum(r.weight for r in job.requirements) <= 0:
        return None
    preserve(db, job, user.id)
    return enqueue(db, job, user, f"upload-analysis:{resume.id}", "analysis", {
        "resume_id": resume.id,
        "document_hash": resume.sha256,
        "criteria": snapshot(job),
        "criteria_version": job.criteria_version,
    }, commit=False)

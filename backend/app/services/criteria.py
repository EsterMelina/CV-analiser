import json
from app.models.criteria_version import CriteriaVersion
from app.schemas.job_requirement import JobRequirementRead


def snapshot(job):
    return {"title": job.title, "description": job.description,
        "min_experience_years": job.min_experience_years, "education_level": job.education_level,
        "requirements": [JobRequirementRead.model_validate(r).model_dump(mode="json") for r in sorted(job.requirements, key=lambda r: r.id)]}


def preserve(db, job, user_id=None):
    existing = db.query(CriteriaVersion).filter_by(job_id=job.id, version=job.criteria_version).first()
    if not existing:
        db.add(CriteriaVersion(job_id=job.id, version=job.criteria_version,
            snapshot_json=json.dumps(snapshot(job), ensure_ascii=False), created_by_id=user_id))
        db.flush()


def changed(db, job, user_id):
    db.flush()
    db.expire(job, ["requirements"])
    job.criteria_version += 1
    preserve(db, job, user_id)

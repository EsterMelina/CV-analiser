"""
Orquestra o pipeline unificado descrito na secção 32 do prompt mestre:

    ficheiro armazenado -> extração de texto -> NLP -> matching -> scoring
    -> persistência (CandidateSkill/Education/..., CandidateMatch,
       Application.score) -> log de processamento

Usado tanto pelo upload manual como pela futura sincronização de e-mail
(mesmo pipeline, fonte diferente — application.source).
"""
import json

from sqlalchemy.orm import Session

from app.models.application import Application, Resume, ApplicationStatus
from app.models.job_requirement import JobRequirement
from app.models.candidate_profile import CandidateSkill, CandidateEducation, CandidateLanguage, CandidateMatch
from app.models.processing_log import ProcessingLog, ProcessingSource, ProcessingStatus
from app.services.text_extraction import extract_text, TextExtractionError
from app.services.matching_engine import compute_match
from app.services.application_state import ANALYSIS_STATES


class AnalysisError(Exception):
    pass


def analyze_resume(db: Session, resume: Resume) -> CandidateMatch:
    application: Application = resume.application
    job = application.job
    candidate = application.candidate

    previous_status = application.status
    application.analysis_status = "running"
    db.commit()

    try:
        if not resume.raw_text:
            resume.raw_text = extract_text(resume.stored_path)

        requirements = db.query(JobRequirement).filter(JobRequirement.job_id == job.id).all()
        if not requirements:
            raise AnalysisError("A vaga não tem requisitos configurados — não é possível calcular o score.")
        if sum(r.weight for r in requirements) <= 0:
            raise AnalysisError("A soma dos pesos deve ser superior a zero")
        from app.services.criteria import preserve
        preserve(db, job)

        result = compute_match(requirements, resume.raw_text, min_experience_years=job.min_experience_years)

        # --- Persistir competências/formação/idiomas extraídos (secção 14) ---
        db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()
        db.query(CandidateEducation).filter(CandidateEducation.candidate_id == candidate.id).delete()
        db.query(CandidateLanguage).filter(CandidateLanguage.candidate_id == candidate.id).delete()

        from app.services.nlp_extraction import extract_skills, extract_education_lines, extract_languages
        for skill in extract_skills(resume.raw_text):
            db.add(CandidateSkill(
                candidate_id=candidate.id, name=skill.name, category=skill.category,
                evidence_snippet=skill.evidence_snippet, confidence=skill.confidence,
            ))
        for line in extract_education_lines(resume.raw_text):
            db.add(CandidateEducation(candidate_id=candidate.id, raw_text=line))
        for lang in extract_languages(resume.raw_text):
            db.add(CandidateLanguage(candidate_id=candidate.id, language=lang))

        # --- Persistir o resultado do matching (explicabilidade, secção 25) ---
        breakdown = [
            {
                "requirement_id": r.requirement_id,
                "name": r.name,
                "category": r.category,
                "is_mandatory": r.is_mandatory,
                "weight": r.weight,
                "met": r.met,
                "match_score": r.match_score,
                "contribution": r.contribution,
                "evidence": r.evidence,
            }
            for r in result.requirement_results
        ]

        existing_match = db.query(CandidateMatch).filter(CandidateMatch.application_id == application.id).first()
        if existing_match:
            db.delete(existing_match)
            db.flush()

        candidate_match = CandidateMatch(
            resume_id=resume.id, criteria_version=job.criteria_version,
            application_id=application.id,
            overall_score=result.overall_score,
            recommendation_label=result.recommendation_label,
            breakdown_json=json.dumps(breakdown, ensure_ascii=False),
            mandatory_missing_json=json.dumps(result.mandatory_missing, ensure_ascii=False),
        )
        db.add(candidate_match)

        application.score = result.overall_score
        application.analysis_status = "completed"
        if previous_status in ANALYSIS_STATES:
            application.status = (
                ApplicationStatus.RECOMMENDED if result.recommendation_label == "Recomendado"
                else ApplicationStatus.ANALYZED
            )

        db.add(ProcessingLog(
            source=ProcessingSource.UPLOAD if application.source.value == "upload" else ProcessingSource.EMAIL,
            candidate_email=candidate.email,
            document_name=resume.original_filename,
            application_id=application.id,
            status=ProcessingStatus.PROCESSED,
        ))

        db.commit()
        db.refresh(candidate_match)
        return candidate_match

    except Exception as exc:
        db.rollback()
        application.analysis_status = "error"
        db.add(ProcessingLog(
            source=ProcessingSource.UPLOAD if application.source.value == "upload" else ProcessingSource.EMAIL,
            candidate_email=candidate.email,
            document_name=resume.original_filename,
            application_id=application.id,
            status=ProcessingStatus.ERROR,
            error_message=str(exc) if isinstance(exc, (TextExtractionError, AnalysisError)) else "Falha interna na análise; tente novamente",
        ))
        db.commit()
        raise

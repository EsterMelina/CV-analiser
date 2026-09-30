from fastapi import HTTPException
from app.models.application import ApplicationStatus as S
from app.models.interview import InterviewResult

TERMINAL = {S.HIRED, S.REJECTED}
ANALYSIS_STATES = {S.RECEIVED, S.IN_ANALYSIS, S.ANALYZED, S.RECOMMENDED}


def transition(application, target):
    if application.status in TERMINAL and target not in {application.status, S.IN_EVALUATION}:
        raise HTTPException(409, "Reabra a candidatura em avaliação antes de mudar a decisão final")
    if target in {S.IN_ANALYSIS, S.ANALYZED, S.RECOMMENDED}:
        raise HTTPException(409, "Este estado é controlado pela análise")
    application.status = target
    if application.feedback:
        application.feedback.hired = target == S.HIRED


def feedback_facts(application):
    match = application.match_result
    return {
        "system_recommended": bool(match and match.recommendation_label == "Recomendado"),
        "selected_for_interview": application.status in {S.INTERVIEW_SELECTED, S.INTERVIEWED} or any(
            interview.result != InterviewResult.CANCELLED for interview in application.interviews),
        "hired": application.status == S.HIRED,
    }

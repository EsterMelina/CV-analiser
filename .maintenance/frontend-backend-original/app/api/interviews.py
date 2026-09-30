from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.application import Application
from app.models.interview import Interview, RecruiterFeedback
from app.models.user import User, UserRole
from app.schemas.interview import (
    InterviewCreate, InterviewResultUpdate, InterviewRead,
    RecruiterFeedbackCreate, RecruiterFeedbackRead,
)
from app.api.deps import get_current_user, require_recruiter

router = APIRouter(tags=["Entrevistas e Feedback"])


def _get_owned_application(application_id: int, db: Session, current_user: User) -> Application:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidatura não encontrada")
    if current_user.role != UserRole.ADMIN and application.job.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta candidatura")
    return application


@router.post(
    "/api/applications/{application_id}/interview",
    response_model=InterviewRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_recruiter)],
)
def schedule_interview(
    application_id: int, payload: InterviewCreate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(application_id, db, current_user)

    interview = Interview(application_id=application.id, scheduled_by_id=current_user.id, **payload.model_dump())
    db.add(interview)

    from app.models.application import ApplicationStatus
    application.status = ApplicationStatus.INTERVIEW_SELECTED

    db.commit()
    db.refresh(interview)
    return interview


@router.get("/api/applications/{application_id}/interviews", response_model=list[InterviewRead])
def list_interviews(application_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    application = _get_owned_application(application_id, db, current_user)
    return db.query(Interview).filter(Interview.application_id == application.id).order_by(Interview.scheduled_at).all()


@router.patch(
    "/api/interviews/{interview_id}/result",
    response_model=InterviewRead,
    dependencies=[Depends(require_recruiter)],
)
def update_interview_result(
    interview_id: int, payload: InterviewResultUpdate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrevista não encontrada")
    _get_owned_application(interview.application_id, db, current_user)

    interview.result = payload.result
    interview.result_notes = payload.result_notes

    if payload.result.value == "completed":
        from app.models.application import ApplicationStatus
        application = db.get(Application, interview.application_id)
        if application:
            application.status = ApplicationStatus.INTERVIEWED

    db.commit()
    db.refresh(interview)
    return interview


@router.put(
    "/api/applications/{application_id}/feedback",
    response_model=RecruiterFeedbackRead,
    dependencies=[Depends(require_recruiter)],
)
def upsert_feedback(
    application_id: int, payload: RecruiterFeedbackCreate,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(application_id, db, current_user)

    feedback = db.query(RecruiterFeedback).filter(RecruiterFeedback.application_id == application.id).first()
    if feedback:
        for field, value in payload.model_dump().items():
            setattr(feedback, field, value)
    else:
        feedback = RecruiterFeedback(application_id=application.id, submitted_by_id=current_user.id, **payload.model_dump())
        db.add(feedback)

    if payload.hired:
        from app.models.application import ApplicationStatus
        application.status = ApplicationStatus.HIRED
    elif not payload.selected_for_interview and payload.rating and payload.rating.value == "not_suitable":
        from app.models.application import ApplicationStatus
        application.status = ApplicationStatus.REJECTED

    db.commit()
    db.refresh(feedback)
    return feedback


@router.get("/api/applications/{application_id}/feedback", response_model=RecruiterFeedbackRead)
def get_feedback(application_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    application = _get_owned_application(application_id, db, current_user)
    feedback = db.query(RecruiterFeedback).filter(RecruiterFeedback.application_id == application.id).first()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ainda sem feedback registado")
    return feedback

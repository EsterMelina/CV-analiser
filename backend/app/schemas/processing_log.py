from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.processing_log import ProcessingSource, ProcessingStatus


class ProcessingLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: ProcessingSource
    candidate_email: str | None = None
    document_name: str | None = None
    application_id: int | None = None
    email_message_id: int | None = None
    status: ProcessingStatus
    error_message: str | None = None
    created_at: datetime

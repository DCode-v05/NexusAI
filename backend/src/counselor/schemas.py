from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AlertCard(BaseModel):
    id: int
    alert_id: int | None = None
    student_id: int
    student_name: str = "Unknown"
    risk_score: float
    anomaly_score: float
    sentiment_score: float
    tier: str = "low"
    trigger_message: str | None = None
    is_resolved: bool
    created_at: datetime
    notes: list["CaseNoteResponse"] = []

    model_config = ConfigDict(from_attributes=True)


class CaseNoteCreate(BaseModel):
    alert_id: int
    note_text: str = Field(..., min_length=1, max_length=5000)


class CaseNoteResponse(BaseModel):
    id: int
    alert_id: int
    note_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResolveAlertRequest(BaseModel):
    alert_id: int
    resolution_notes: str | None = None


class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from src.wellbeing.models import RiskTier


class SurveySubmit(BaseModel):
    q1_score: int = Field(..., ge=1, le=10)
    q2_score: int = Field(..., ge=1, le=10)
    q3_score: int = Field(..., ge=1, le=10)
    free_text: str | None = Field(None, max_length=2000)


class RiskResult(BaseModel):
    score: float
    tier: RiskTier
    anomaly_score: float
    sentiment_score: float
    survey_decline: float


class WellbeingAlertResponse(BaseModel):
    id: int
    student_id: int
    risk_score: float
    tier: RiskTier
    is_resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    student_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    risk_tier: RiskTier | str
    risk_score: float | None = None
    agent: str | None = None
    helpline: str | None = None

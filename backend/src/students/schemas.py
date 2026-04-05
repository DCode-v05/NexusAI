from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    program: str | None = None
    year: int | None = Field(None, ge=1, le=6)
    cgpa: float | None = Field(None, ge=0.0, le=10.0)


class StudentResponse(BaseModel):
    id: int
    user_id: int
    name: str
    program: str | None
    year: int | None
    cgpa: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BehaviorLogCreate(BaseModel):
    session_gap_days: float = Field(0.0, ge=0.0)
    survey_skip_streak: int = Field(0, ge=0)
    avg_session_length: float = Field(0.0, ge=0.0)
    assignment_delay_hrs: float = Field(0.0, ge=0.0)
    chat_initiation_freq: float = Field(0.0, ge=0.0)
    mood_score_trend: float = 0.0
    login_hour_variance: float = Field(0.0, ge=0.0)


class BehaviorLogResponse(BehaviorLogCreate):
    id: int
    student_id: int
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MoodSurveyCreate(BaseModel):
    q1_score: int = Field(..., ge=1, le=10)
    q2_score: int = Field(..., ge=1, le=10)
    q3_score: int = Field(..., ge=1, le=10)
    free_text: str | None = Field(None, max_length=2000)


class MoodSurveyResponse(BaseModel):
    id: int
    student_id: int
    q1_score: int
    q2_score: int
    q3_score: int
    composite_score: float
    free_text: str | None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentDashboardResponse(BaseModel):
    profile: StudentResponse
    latest_behavior: BehaviorLogResponse | None
    mood_history: list[MoodSurveyResponse]
    login_streak: int

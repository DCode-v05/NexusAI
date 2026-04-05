from datetime import datetime

from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.shared.utils import utcnow


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    program: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    behavior_logs = relationship("BehaviorLog", back_populates="student", order_by="BehaviorLog.logged_at.desc()")
    mood_surveys = relationship("MoodSurvey", back_populates="student", order_by="MoodSurvey.submitted_at.desc()")
    wellbeing_alerts = relationship("WellbeingAlert", back_populates="student")


class BehaviorLog(Base):
    """Passive behavioral signals — 7 features used by IsolationForest."""

    __tablename__ = "behavior_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    # The 7 behavioral features
    session_gap_days: Mapped[float] = mapped_column(Float, default=0.0)
    survey_skip_streak: Mapped[int] = mapped_column(Integer, default=0)
    avg_session_length: Mapped[float] = mapped_column(Float, default=0.0)  # minutes
    assignment_delay_hrs: Mapped[float] = mapped_column(Float, default=0.0)
    chat_initiation_freq: Mapped[float] = mapped_column(Float, default=0.0)  # per day
    mood_score_trend: Mapped[float] = mapped_column(Float, default=0.0)  # slope over last 7 days
    login_hour_variance: Mapped[float] = mapped_column(Float, default=0.0)

    logged_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)

    student = relationship("Student", back_populates="behavior_logs")


class MoodSurvey(Base):
    """Daily 3-question PHQ-inspired mood check-in."""

    __tablename__ = "mood_surveys"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    q1_score: Mapped[int] = mapped_column(Integer)   # How are you feeling? (1–10)
    q2_score: Mapped[int] = mapped_column(Integer)   # Energy level? (1–10)
    q3_score: Mapped[int] = mapped_column(Integer)   # Motivation for studies? (1–10)
    composite_score: Mapped[float] = mapped_column(Float)  # avg of 3 scores
    free_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)

    student = relationship("Student", back_populates="mood_surveys")

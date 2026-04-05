from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, Integer, ForeignKey, Boolean, Enum as SQLEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.shared.utils import utcnow


class RiskTier(str, PyEnum):
    low = "low"
    moderate = "moderate"
    high = "high"
    crisis = "crisis"


class WellbeingAlert(Base):
    __tablename__ = "wellbeing_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)

    risk_score: Mapped[float] = mapped_column(Float)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    survey_decline: Mapped[float] = mapped_column(Float, default=0.0)
    tier: Mapped[RiskTier] = mapped_column(SQLEnum(RiskTier))

    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    student = relationship("Student", back_populates="wellbeing_alerts")


class ChatMessage(Base):
    """Persisted chat turns — survives server restarts and seeds the in-memory context store."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))        # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    risk_tier: Mapped[str] = mapped_column(String(20), default="low")
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)

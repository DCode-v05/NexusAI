from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.shared.utils import utcnow


class SkillProfile(Base):
    __tablename__ = "skill_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True, index=True)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    target_role: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    raw_resume_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    student = relationship("Student")
    roadmaps = relationship("CareerRoadmap", back_populates="skill_profile")


class CareerRoadmap(Base):
    __tablename__ = "career_roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_profile_id: Mapped[int] = mapped_column(ForeignKey("skill_profiles.id"), index=True)
    target_role: Mapped[str] = mapped_column(String(200))
    roadmap_json: Mapped[dict] = mapped_column(JSON)  # 12-week structured plan
    generated_at: Mapped[datetime] = mapped_column(default=utcnow)

    skill_profile = relationship("SkillProfile", back_populates="roadmaps")

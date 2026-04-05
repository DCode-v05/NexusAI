from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.shared.utils import utcnow
from datetime import datetime


class UserRole(str, PyEnum):
    student = "student"
    counselor = "counselor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False)


class RevokedToken(Base):
    """Token blacklist — stores revoked JWT IDs (jti) until their expiry."""
    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)  # used for cleanup

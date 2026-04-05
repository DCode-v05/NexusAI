"""MCP Student DB Server — port 9001.

Tools: get_profile, update_behavior_log, get_history, set_flag
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select, desc, String, Float, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from datetime import datetime


class Settings(BaseSettings):
    # No default — must be explicitly set via environment variable or .env file.
    # Example: DATABASE_URL=postgresql+asyncpg://nexus:nexus@postgres:5432/nexusai
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(200))
    program: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class BehaviorLog(Base):
    __tablename__ = "behavior_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    session_gap_days: Mapped[float] = mapped_column(Float, default=0.0)
    survey_skip_streak: Mapped[int] = mapped_column(Integer, default=0)
    avg_session_length: Mapped[float] = mapped_column(Float, default=0.0)
    assignment_delay_hrs: Mapped[float] = mapped_column(Float, default=0.0)
    chat_initiation_freq: Mapped[float] = mapped_column(Float, default=0.0)
    mood_score_trend: Mapped[float] = mapped_column(Float, default=0.0)
    login_hour_variance: Mapped[float] = mapped_column(Float, default=0.0)
    logged_at: Mapped[datetime] = mapped_column(DateTime)


class StudentFlag(Base):
    """Persistent flags set on a student (e.g. 'at_risk', 'crisis', 'watch')."""
    __tablename__ = "student_flags"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    flag_type: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged_at: Mapped[datetime] = mapped_column(DateTime)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="MCP Student DB Server", lifespan=lifespan)


class GetProfileRequest(BaseModel):
    student_id: int


class BehaviorLogData(BaseModel):
    session_gap_days: float = 0.0
    survey_skip_streak: int = 0
    avg_session_length: float = 0.0
    assignment_delay_hrs: float = 0.0
    chat_initiation_freq: float = 0.0
    mood_score_trend: float = 0.0
    login_hour_variance: float = 0.0


class UpdateBehaviorRequest(BaseModel):
    student_id: int
    signals: BehaviorLogData


class GetHistoryRequest(BaseModel):
    student_id: int
    days: int = 30


class SetFlagRequest(BaseModel):
    student_id: int
    flag_type: str
    is_active: bool = True
    notes: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-student-db"}


@app.post("/tools/get_profile")
async def get_profile(req: GetProfileRequest):
    async with async_session() as db:
        result = await db.execute(select(Student).where(Student.id == req.student_id))
        student = result.scalar_one_or_none()
        if not student:
            return {"error": "Student not found"}

        logs = await db.execute(
            select(BehaviorLog)
            .where(BehaviorLog.student_id == req.student_id)
            .order_by(desc(BehaviorLog.logged_at))
            .limit(1)
        )
        latest_log = logs.scalar_one_or_none()

        return {
            "id": student.id,
            "user_id": student.user_id,
            "name": student.name,
            "program": student.program,
            "year": student.year,
            "cgpa": student.cgpa,
            "latest_behavior": {
                "session_gap_days": latest_log.session_gap_days,
                "survey_skip_streak": latest_log.survey_skip_streak,
                "avg_session_length": latest_log.avg_session_length,
                "assignment_delay_hrs": latest_log.assignment_delay_hrs,
                "chat_initiation_freq": latest_log.chat_initiation_freq,
                "mood_score_trend": latest_log.mood_score_trend,
                "login_hour_variance": latest_log.login_hour_variance,
            } if latest_log else None,
        }


@app.post("/tools/update_behavior_log")
async def update_behavior_log(req: UpdateBehaviorRequest):
    from datetime import datetime, timezone
    async with async_session() as db:
        log = BehaviorLog(
            student_id=req.student_id,
            logged_at=datetime.now(timezone.utc).replace(tzinfo=None),
            **req.signals.model_dump(),
        )
        db.add(log)
        await db.commit()
        return {"status": "logged", "student_id": req.student_id}


@app.post("/tools/get_history")
async def get_history(req: GetHistoryRequest):
    async with async_session() as db:
        result = await db.execute(
            select(BehaviorLog)
            .where(BehaviorLog.student_id == req.student_id)
            .order_by(desc(BehaviorLog.logged_at))
            .limit(req.days)
        )
        logs = result.scalars().all()
        return [
            {
                "session_gap_days": l.session_gap_days,
                "survey_skip_streak": l.survey_skip_streak,
                "avg_session_length": l.avg_session_length,
                "assignment_delay_hrs": l.assignment_delay_hrs,
                "chat_initiation_freq": l.chat_initiation_freq,
                "mood_score_trend": l.mood_score_trend,
                "login_hour_variance": l.login_hour_variance,
                "logged_at": l.logged_at.isoformat(),
            }
            for l in logs
        ]


@app.post("/tools/set_flag")
async def set_flag(req: SetFlagRequest):
    """Create or update a student flag. Deactivating clears any active matching flag."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    async with async_session() as db:
        # Find any existing active flag of the same type for this student
        result = await db.execute(
            select(StudentFlag).where(
                StudentFlag.student_id == req.student_id,
                StudentFlag.flag_type == req.flag_type,
                StudentFlag.is_active == True,  # noqa: E712
            ).limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update in place
            existing.is_active = req.is_active
            existing.notes = req.notes
            if not req.is_active:
                existing.cleared_at = now
            flag_id = existing.id
        else:
            flag = StudentFlag(
                student_id=req.student_id,
                flag_type=req.flag_type,
                is_active=req.is_active,
                notes=req.notes,
                flagged_at=now,
            )
            db.add(flag)
            await db.flush()
            flag_id = flag.id

        await db.commit()

    return {
        "status": "flagged" if req.is_active else "cleared",
        "student_id": req.student_id,
        "flag_type": req.flag_type,
        "flag_id": flag_id,
    }

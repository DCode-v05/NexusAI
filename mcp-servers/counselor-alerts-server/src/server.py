"""MCP Counselor Alerts Server — port 9004.

Tools: create_alert, get_flagged_students, add_note, resolve_case
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Boolean, Text, Integer, ForeignKey, DateTime, select, desc


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


class CounselorAlert(Base):
    __tablename__ = "counselor_alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer)
    risk_score: Mapped[float] = mapped_column(Float)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    survey_score: Mapped[float] = mapped_column(Float, default=0.0)
    triggered_keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CaseNote(Base):
    __tablename__ = "case_notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("counselor_alerts.id"))
    counselor_user_id: Mapped[int] = mapped_column(Integer)
    note_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="MCP Counselor Alerts Server", lifespan=lifespan)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CreateAlertRequest(BaseModel):
    student_id: int
    risk_score: float
    anomaly_score: float = 0.0
    sentiment_score: float = 0.0
    survey_score: float = 0.0
    triggered_keywords: list[str] = []


class GetFlaggedRequest(BaseModel):
    threshold: float = 0.8
    limit: int = 50


class AddNoteRequest(BaseModel):
    alert_id: int
    counselor_user_id: int
    note_text: str


class ResolveCaseRequest(BaseModel):
    alert_id: int
    resolution_notes: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mcp-counselor-alerts"}


@app.post("/tools/create_alert")
async def create_alert(req: CreateAlertRequest):
    async with async_session() as db:
        alert = CounselorAlert(
            student_id=req.student_id,
            risk_score=req.risk_score,
            anomaly_score=req.anomaly_score,
            sentiment_score=req.sentiment_score,
            survey_score=req.survey_score,
            triggered_keywords=", ".join(req.triggered_keywords),
            created_at=_now(),
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        return {"alert_id": alert.id, "status": "created"}


@app.post("/tools/get_flagged_students")
async def get_flagged_students(req: GetFlaggedRequest):
    async with async_session() as db:
        result = await db.execute(
            select(CounselorAlert)
            .where(
                CounselorAlert.risk_score >= req.threshold,
                CounselorAlert.is_resolved.is_(False),
            )
            .order_by(desc(CounselorAlert.risk_score))
            .limit(req.limit)
        )
        alerts = result.scalars().all()
        return [
            {
                "alert_id": a.id,
                "student_id": a.student_id,
                "risk_score": a.risk_score,
                "anomaly_score": a.anomaly_score,
                "sentiment_score": a.sentiment_score,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]


@app.post("/tools/add_note")
async def add_note(req: AddNoteRequest):
    async with async_session() as db:
        note = CaseNote(
            alert_id=req.alert_id,
            counselor_user_id=req.counselor_user_id,
            note_text=req.note_text,
            created_at=_now(),
        )
        db.add(note)
        await db.commit()
        return {"status": "note added", "alert_id": req.alert_id}


@app.post("/tools/resolve_case")
async def resolve_case(req: ResolveCaseRequest):
    async with async_session() as db:
        result = await db.execute(select(CounselorAlert).where(CounselorAlert.id == req.alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return {"error": "Alert not found"}
        alert.is_resolved = True
        alert.resolved_at = _now()
        if req.resolution_notes:
            note = CaseNote(
                alert_id=alert.id,
                counselor_user_id=0,
                note_text=f"[RESOLUTION] {req.resolution_notes}",
                created_at=_now(),
            )
            db.add(note)
        await db.commit()
        return {"status": "resolved", "alert_id": req.alert_id}

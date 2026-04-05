from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import selectinload

from src.counselor import models, schemas
from src.students.models import Student
from src.shared.exceptions import NotFoundError
from src.shared.utils import utcnow


async def get_risk_feed(db: AsyncSession, threshold: float = 0.3) -> list[schemas.AlertCard]:
    result = await db.execute(
        select(models.CounselorAlert, Student.name)
        .join(Student, Student.id == models.CounselorAlert.student_id)
        .options(selectinload(models.CounselorAlert.notes))
        .where(models.CounselorAlert.risk_score >= threshold)
        .order_by(desc(models.CounselorAlert.risk_score))
        .limit(50)
    )
    rows = result.unique().all()

    def _tier(score: float) -> str:
        if score >= 0.8: return "crisis"
        if score >= 0.6: return "high"
        if score >= 0.4: return "moderate"
        return "low"

    return [
        schemas.AlertCard(
            id=alert.id,
            alert_id=alert.id,
            student_id=alert.student_id,
            student_name=name or "Unknown",
            risk_score=alert.risk_score,
            anomaly_score=alert.anomaly_score,
            sentiment_score=alert.sentiment_score,
            tier=_tier(alert.risk_score),
            trigger_message=alert.trigger_message,
            is_resolved=alert.is_resolved,
            created_at=alert.created_at,
            notes=[
                schemas.CaseNoteResponse(
                    id=n.id, alert_id=n.alert_id,
                    note_text=n.note_text, created_at=n.created_at,
                )
                for n in sorted(alert.notes, key=lambda x: x.created_at)
            ],
        )
        for alert, name in rows
    ]


async def add_case_note(db: AsyncSession, counselor_id: int, data: schemas.CaseNoteCreate) -> models.CaseNote:
    note = models.CaseNote(
        alert_id=data.alert_id,
        counselor_user_id=counselor_id,
        note_text=data.note_text,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def resolve_alert(db: AsyncSession, data: schemas.ResolveAlertRequest) -> models.CounselorAlert:
    result = await db.execute(select(models.CounselorAlert).where(models.CounselorAlert.id == data.alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert")
    alert.is_resolved = True
    alert.resolved_at = utcnow()
    await db.commit()
    await db.refresh(alert)

    # Send anonymous notification to the student
    # Look up the user_id from the student record
    from src.students.models import Student as StudentModel
    student_result = await db.execute(select(StudentModel).where(StudentModel.id == alert.student_id))
    student = student_result.scalar_one_or_none()
    if student:
        notification = models.Notification(
            user_id=student.user_id,
            message="Your wellbeing check-in has been reviewed by a counselor. They've noted your situation and support is available. Feel free to reach out to campus counseling services anytime. You're not alone.",
        )
        db.add(notification)
        await db.commit()

    return alert


async def get_notifications(db: AsyncSession, user_id: int) -> list[models.Notification]:
    result = await db.execute(
        select(models.Notification)
        .where(models.Notification.user_id == user_id)
        .order_by(desc(models.Notification.created_at))
        .limit(20)
    )
    return list(result.scalars().all())


async def mark_notifications_read(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(models.Notification)
        .where(models.Notification.user_id == user_id, models.Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()

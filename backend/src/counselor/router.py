from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.auth.dependencies import require_counselor, require_student
from src.auth.models import User
from src.counselor import schemas, service, models

router = APIRouter(prefix="/counselor", tags=["counselor"])


@router.get("/alerts", response_model=list[schemas.AlertCard])
async def get_alerts(
    threshold: float = 0.3,
    current_user: User = Depends(require_counselor),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_risk_feed(db, threshold)


@router.post("/notes", response_model=schemas.CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(
    data: schemas.CaseNoteCreate,
    current_user: User = Depends(require_counselor),
    db: AsyncSession = Depends(get_db),
):
    return await service.add_case_note(db, current_user.id, data)


@router.post("/resolve", response_model=schemas.AlertCard)
async def resolve_case(
    data: schemas.ResolveAlertRequest,
    current_user: User = Depends(require_counselor),
    db: AsyncSession = Depends(get_db),
):
    alert = await service.resolve_alert(db, data)
    from src.students.models import Student
    from sqlalchemy import select
    res = await db.execute(select(Student).where(Student.id == alert.student_id))
    student = res.scalar_one_or_none()
    return schemas.AlertCard(
        id=alert.id,
        student_id=alert.student_id,
        student_name=student.name if student else "Unknown",
        risk_score=alert.risk_score,
        anomaly_score=alert.anomaly_score,
        sentiment_score=alert.sentiment_score,
        is_resolved=alert.is_resolved,
        created_at=alert.created_at,
    )


# --- Student notification endpoints ---

@router.get("/notifications", response_model=list[schemas.NotificationResponse])
async def get_notifications(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_notifications(db, current_user.id)


@router.post("/notifications/read")
async def mark_read(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await service.mark_notifications_read(db, current_user.id)
    return {"status": "ok"}
